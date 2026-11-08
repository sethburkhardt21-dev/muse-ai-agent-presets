"""Bounded offline Model Builder development scoring and synthetic byte checkpoint checks.

This code neither trains a model nor evaluates a protected final set.
Hash matches and self-supplied predictions do not prove real weights, data
rights, optimizer steps, independent examination or native Muse authority.
"""
from __future__ import annotations

import hashlib
import re

SLUG = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[a-f0-9]{64}$")
ROW_KEYS = frozenset({"sample_id", "family_id", "split", "label", "baseline", "candidate"})
EVAL_KEYS = frozenset({"schema", "model_source_sha256", "dataset_source_sha256",
                       "rights_status", "rows"})
CHECKPOINT_KEYS = frozenset({"schema", "artifact_kind", "artifact_sha256",
                             "parent_model_sha256", "dataset_source_sha256",
                             "optimizer_steps", "weights_trained", "rights_status"})
MAX_ROWS = 64
MAX_CHECKPOINT_BYTES = 4096


def _refused(reason: str) -> dict:
    return {
        "status": "REVIEW_REQUIRED",
        "reason": reason,
        "trained": False,
        "weights_proven": False,
        "promotion_authorized": False,
        "native_tool_invoked": False,
        "external_effect_authorized": False,
        "independent_examiner_verified": False,
    }


def _binary(x: object) -> bool:
    return type(x) is int and x in (0, 1)


def evaluate_development(data: object) -> dict:
    """Compute actual local accuracy over DEVELOPMENT rows only.

    The supplied rows/predictions are untrusted local data. Protected final
    examples must not include ground truth or predictions in this interface.
    """
    if type(data) is not dict or set(data) != EVAL_KEYS:
        return _refused("EVALUATION_SCHEMA_FIELDS")
    if data["schema"] != "r33/model-builder-development-v1":
        return _refused("EVALUATION_SCHEMA")
    if data["rights_status"] != "UNVERIFIED":
        return _refused("UNVERIFIED_RIGHTS_MUST_NOT_BE_PROMOTED")
    for name in ("model_source_sha256", "dataset_source_sha256"):
        value = data[name]
        if type(value) is not str or SHA.fullmatch(value) is None:
            return _refused("INVALID_SOURCE_DIGEST")
    rows = data["rows"]
    if type(rows) is not list or not 3 <= len(rows) <= MAX_ROWS:
        return _refused("INVALID_ROW_COUNT")
    ids: set[str] = set()
    families: dict[str, str] = {}
    counts = {"train": 0, "dev": 0, "final": 0}
    baseline_correct = 0
    candidate_correct = 0
    for row in rows:
        if type(row) is not dict or set(row) != ROW_KEYS:
            return _refused("INVALID_ROW_FIELDS")
        sample_id, family_id, split = row["sample_id"], row["family_id"], row["split"]
        if (type(sample_id) is not str or SLUG.fullmatch(sample_id) is None
            or sample_id in ids or type(family_id) is not str
            or SLUG.fullmatch(family_id) is None
            or type(split) is not str or split not in counts):
            return _refused("INVALID_ID_OR_SPLIT")
        ids.add(sample_id)
        if family_id in families and families[family_id] != split:
            return _refused("CROSS_PARTITION_SOURCE_FAMILY_CONTAMINATION")
        families[family_id] = split
        counts[split] += 1
        label, baseline, candidate = row["label"], row["baseline"], row["candidate"]
        if split == "train":
            if not _binary(label) or baseline is not None or candidate is not None:
                return _refused("TRAIN_SPLIT_OUTPUTS_NOT_ALLOWED")
        elif split == "final":
            if label is not None or baseline is not None or candidate is not None:
                return _refused("PROTECTED_FINAL_EXPOSED")
        else:
            if not (_binary(label) and _binary(baseline) and _binary(candidate)):
                return _refused("NON_BINARY_DEV_VALUE")
            baseline_correct += int(baseline == label)
            candidate_correct += int(candidate == label)
    if any(n == 0 for n in counts.values()):
        return _refused("MISSING_REQUIRED_DISJOINT_SPLIT")
    n = counts["dev"]
    # Exact integer counts first; numeric summaries are for display only.
    baseline_accuracy = baseline_correct / n
    candidate_accuracy = candidate_correct / n
    return {
        "status": "LOCAL_DEV_METRICS_ONLY",
        "dev_n": n,
        "train_n": counts["train"],
        "final_n": counts["final"],
        "baseline_correct": baseline_correct,
        "candidate_correct": candidate_correct,
        "baseline_accuracy": baseline_accuracy,
        "candidate_accuracy": candidate_accuracy,
        "delta_accuracy": (candidate_correct - baseline_correct) / n,
        "final_status": "HELD_UNEVALUATED",
        "rights_status": "UNVERIFIED",
        "trained": False,
        "weights_proven": False,
        "promotion_authorized": False,
        "native_tool_invoked": False,
        "external_effect_authorized": False,
        "independent_examiner_verified": False,
        "evidence_grade": "UNATTESTED_CALLER_PROVIDED_DEV_PREDICTIONS",
    }


def verify_checkpoint_bytes(manifest: object, content: object) -> dict:
    """Verify actual bounded bytes against a claimed SHA, not model provenance."""
    if type(manifest) is not dict or set(manifest) != CHECKPOINT_KEYS:
        return _refused("INVALID_CHECKPOINT_FIELDS")
    if (manifest["schema"] != "r33/model-builder-checkpoint-v1" or
        manifest["artifact_kind"] != "synthetic-checkpoint-bytes" or
        manifest["rights_status"] != "UNVERIFIED" or
        type(manifest["optimizer_steps"]) is not int or
        manifest["optimizer_steps"] != 0 or
        manifest["weights_trained"] is not False):
        return _refused("CHECKPOINT_TRAINING_OR_RIGHTS_CLAIM_UNVERIFIED")
    for name in ("artifact_sha256", "parent_model_sha256", "dataset_source_sha256"):
        value = manifest[name]
        if type(value) is not str or SHA.fullmatch(value) is None:
            return _refused("CHECKPOINT_DIGEST_INVALID")
    if type(content) is not bytes or not 1 <= len(content) <= MAX_CHECKPOINT_BYTES:
        return _refused("CHECKPOINT_BYTES_NOT_ADMITTED")
    observed = hashlib.sha256(content).hexdigest()
    if observed != manifest["artifact_sha256"]:
        return _refused("CHECKPOINT_BYTES_DRIFT")
    return {
        "status": "LOCAL_CHECKPOINT_DIGEST_MATCH",
        "observed_sha256": observed,
        "artifact_bytes": len(content),
        "artifact_kind": "synthetic-checkpoint-bytes",
        "trained": False,
        "weights_proven": False,
        "promotion_authorized": False,
        "native_tool_invoked": False,
        "external_effect_authorized": False,
        "independent_examiner_verified": False,
        "evidence_grade": "LOCAL_HASH_MATCH_NOT_TRAINING_RECEIPT",
    }
