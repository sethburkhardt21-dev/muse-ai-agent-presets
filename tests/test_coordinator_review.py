"""R33 Coordinator: test bounded offline graph review and refusal boundaries."""
import copy
import hashlib
import json
import unittest

from muse_presets.coordinator_review import review_workgraph, review_assertions


def toy_graph():
    return {
        "schema": "r33/coordinator-workgraph-v1",
        "workspace": "fictional-demo",
        "budget_units": 5,
        "tasks": [
            {
                "id": "diagnose-1",
                "role": "software-engineer",
                "reviewer": "adversarial-verifier",
                "requires": [],
                "estimated_units": 2,
                "effect_class": "none",
                "source_sha256": "a" * 64,
                "acceptance": ["Reproduced exact source and expected result"],
            },
            {
                "id": "analyze-2",
                "role": "claims-adjudicator",
                "reviewer": "research-evaluator",
                "requires": ["diagnose-1"],
                "estimated_units": 3,
                "effect_class": "external",
                "source_sha256": "b" * 64,
                "acceptance": ["Independent recipient readback verified"],
            },
        ],
    }


def assertions():
    return {
        "schema": "r33/coordinator-assertions-v1",
        "workgraph_sha256": review_workgraph(toy_graph())["workgraph_sha256"],
        "items": [
            {"task_id": "diagnose-1", "actor_role": "software-engineer",
             "reviewer_role": "adversarial-verifier", "source_sha256": "a" * 64,
             "actor_claim": "completed", "reviewer_claim": "pass"},
            {"task_id": "analyze-2", "actor_role": "claims-adjudicator",
             "reviewer_role": "research-evaluator", "source_sha256": "b" * 64,
             "actor_claim": "unknown_effect", "reviewer_claim": "hold"},
        ],
    }


class CoordinatorReviewTests(unittest.TestCase):
    def test_valid_graph_is_deterministic_topological_and_plan_only(self):
        graph = toy_graph()
        report = review_workgraph(graph)
        self.assertEqual(report["status"], "LOCAL_PLAN_REVIEW_ONLY")
        self.assertEqual(report["execution_order"], ["diagnose-1", "analyze-2"])
        self.assertEqual(report["budget_units"], 5)
        self.assertEqual(report["held_effect_tasks"], ["analyze-2"])
        self.assertEqual(len(report["workgraph_sha256"]), 64)
        self.assertFalse(report["provider_authenticated"])
        self.assertFalse(report["effect_authorized"])
        self.assertEqual(report, review_workgraph(copy.deepcopy(graph)))
        self.assertEqual(graph, toy_graph())

    def test_invalid_budget_denied(self):
        for amount in (0, -1, 4, 999, "5", True):
            graph=toy_graph()
            graph["budget_units"]=amount
            with self.subTest(amount=amount):
                self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")

    def test_cycle_and_unknown_dependency_denied(self):
        graph=toy_graph()
        graph["tasks"][0]["requires"]=["analyze-2"]
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][1]["requires"]=["phantom-3"]
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")

    def test_invalid_unhashable_role_is_refused_without_crash(self):
        graph=toy_graph()
        graph["tasks"][0]["role"]=["software-engineer"]
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")

    def test_self_review_and_wrong_role_are_refused(self):
        graph=toy_graph()
        graph["tasks"][0]["reviewer"]="software-engineer"
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][0]["role"]="some-private-agent"
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")

    def test_unknown_fields_and_duplicate_task_ids_rejected(self):
        graph=toy_graph()
        graph["host_authenticated"]=True
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][1]["id"]="diagnose-1"
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][0]["grant"]="granted"
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")

    def test_effect_annotation_never_becomes_an_grant(self):
        graph=toy_graph()
        graph["tasks"][1]["effect_class"]="none"
        self.assertEqual(review_workgraph(graph)["status"], "LOCAL_PLAN_REVIEW_ONLY")
        self.assertFalse(review_workgraph(graph)["effect_authorized"])

    def test_assertions_consistent_but_not_native_authentication(self):
        graph=toy_graph()
        out=review_assertions(graph, assertions())
        self.assertEqual(out["status"], "UNATTESTED_ASSERTIONS_ONLY")
        self.assertEqual(out["held_task_ids"], ["analyze-2"])
        self.assertFalse(out["recipient_readback_verified"])
        self.assertFalse(out["external_effect_authorized"])
        self.assertFalse(out["native_execution_verified"])

    def test_forged_review_or_original_recipient_claim_refused(self):
        graph=toy_graph()
        reports=assertions()
        reports["items"][0]["reviewer_role"]="software-engineer"
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")
        reports=assertions()
        reports["recipient_readback_verified"]=True
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")

    def test_unknown_effect_is_never_reclassified_to_pass(self):
        graph=toy_graph()
        reports=assertions()
        reports["items"][1]["reviewer_claim"]="pass"
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")

    def test_source_drift_or_mismatched_graph_digest_refused(self):
        graph=toy_graph()
        reports=assertions()
        reports["workgraph_sha256"]="0" * 64
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")
        reports=assertions()
        reports["items"][0]["source_sha256"]="f" * 64
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")

    def test_duplicate_or_missing_assertion_refused(self):
        graph=toy_graph()
        reports=assertions()
        reports["items"].append(copy.deepcopy(reports["items"][0]))
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")
        reports=assertions()
        reports["items"].pop()
        self.assertEqual(review_assertions(graph,reports)["status"], "REVIEW_REQUIRED")

    def test_empty_unbounded_or_nonfinite_inputs_refused(self):
        graph=toy_graph()
        graph["tasks"]=[]
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][0]["acceptance"]=[]
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")
        graph=toy_graph()
        graph["tasks"][0]["estimated_units"]=float("nan")
        self.assertEqual(review_workgraph(graph)["status"], "REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
