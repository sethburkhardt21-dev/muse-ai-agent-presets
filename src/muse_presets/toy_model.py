"""Bounded standard-library perceptron training and actual JSON checkpoint inference.

A deliberately small local model, not an LLM trainer or GPU adapter. No network,
subprocess, dynamic imports, pickle, filesystem writes or provider grants. All
numbers are bounded integers, so checkpoint bytes are cross-platform stable.
Caller data and self-hashes do not establish rights, a publisher or provenance.
"""
from __future__ import annotations

import hashlib
import json
import re

EXPERIMENT_SCHEMA = "r61/toy-perceptron-experiment-v1"
CHECKPOINT_SCHEMA = "r61/toy-perceptron-checkpoint-v1"
MODEL_TYPE = "binary-integer-perceptron"
MAX_ROWS = 96
MAX_PARTITION_ROWS = 64
MAX_FEATURES = 8
MAX_EPOCHS = 32
MAX_CHECKPOINT_BYTES = 16384
MAX_COEFFICIENT = 32768
ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[0-9a-f]{64}$")
ROW_KEYS = {"sample_id", "family_id", "split", "features", "label"}
MODEL_KEYS = {"schema", "model_type", "feature_count", "weights", "bias",
              "training_dataset_sha256", "training_steps", "update_count",
              "training_provenance_verified", "training_family_ids", "training_feature_sha256"}


def _refuse(reason: str) -> dict:
    return {"status": "REVIEW_REQUIRED", "reason": reason,
            "trained_this_call": False, "promotion_authorized": False,
            "external_effect_authorized": False, "native_tool_invoked": False,
            "training_provenance_verified": False}


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _slug(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 64 and ID.fullmatch(value) is not None


def _integer(value: object, lower: int, upper: int) -> bool:
    return type(value) is int and lower <= value <= upper


def _vector(value: object, dimensions: int, lower: int, upper: int) -> bool:
    return (type(value) is list and len(value) == dimensions
            and all(_integer(v, lower, upper) for v in value))


def _canonical(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _unique(pairs):
    out = {}
    for name, value in pairs:
        _need(name not in out, "DUPLICATE_CHECKPOINT_KEY")
        out[name] = value
    return out


def _nonfinite(value):
    raise ValueError("NONFINITE_CHECKPOINT_NUMBER")


def _validate_rows(rows: object, dimensions: int, *, development_only: bool) -> dict:
    _need(type(rows) is list and 1 <= len(rows) <= MAX_ROWS, "ROW_COUNT_REFUSED")
    groups = {"train": [], "dev": [], "final": []}
    ids, families, content_splits = set(), {}, {}
    for row in rows:
        _need(type(row) is dict and set(row) == ROW_KEYS, "ROW_FIELDS_REFUSED")
        sid, family, split = row["sample_id"], row["family_id"], row["split"]
        _need(_slug(sid) and _slug(family) and sid not in ids, "DUPLICATE_OR_INVALID_ID")
        _need(type(split) is str and split in groups, "UNKNOWN_PARTITION")
        _need(not development_only or split == "dev", "NON_DEVELOPMENT_EVALUATION_REFUSED")
        _need(family not in families or families[family] == split, "SOURCE_FAMILY_CONTAMINATION")
        ids.add(sid)
        families[family] = split
        features, label = row["features"], row["label"]
        if split == "final":
            _need(features is None and label is None, "PROTECTED_FINAL_EXPOSED")
        else:
            _need(_vector(features, dimensions, -1, 1), "BOUNDED_INTEGER_FEATURES_REQUIRED")
            _need(_integer(label, 0, 1), "BINARY_INTEGER_LABEL_REQUIRED")
            feature_key = tuple(features)
            _need(feature_key not in content_splits or content_splits[feature_key] == split,
                  "CROSS_PARTITION_FEATURE_DUPLICATE")
            content_splits[feature_key] = split
        groups[split].append(row)
        _need(len(groups[split]) <= MAX_PARTITION_ROWS, "PARTITION_BUDGET_EXCEEDED")
    if not development_only:
        _need(len(groups["train"]) >= 2 and len(groups["dev"]) >= 1
              and len(groups["final"]) >= 1, "REQUIRED_PARTITION_MISSING")
        _need({r["label"] for r in groups["train"]} == {0, 1}, "TWO_TRAINING_CLASSES_REQUIRED")
    return groups


def _decode_checkpoint(raw: object, expected_sha256: object) -> dict:
    _need(type(raw) is bytes and 1 <= len(raw) <= MAX_CHECKPOINT_BYTES,
          "CHECKPOINT_BYTE_BUDGET_REFUSED")
    _need(type(expected_sha256) is str and SHA.fullmatch(expected_sha256) is not None
          and _sha(raw) == expected_sha256, "CHECKPOINT_PIN_MISMATCH")
    doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite)
    _need(type(doc) is dict and set(doc) == MODEL_KEYS, "CHECKPOINT_SCHEMA_FIELDS_REFUSED")
    _need(doc["schema"] == CHECKPOINT_SCHEMA and doc["model_type"] == MODEL_TYPE,
          "CHECKPOINT_MODEL_TYPE_REFUSED")
    n = doc["feature_count"]
    _need(_integer(n, 1, MAX_FEATURES), "CHECKPOINT_DIMENSIONS_REFUSED")
    _need(_vector(doc["weights"], n, -MAX_COEFFICIENT, MAX_COEFFICIENT)
          and _integer(doc["bias"], -MAX_COEFFICIENT, MAX_COEFFICIENT),
          "CHECKPOINT_INTEGER_COEFFICIENTS_REQUIRED")
    _need(type(doc["training_dataset_sha256"]) is str
          and SHA.fullmatch(doc["training_dataset_sha256"]) is not None,
          "CHECKPOINT_DATASET_PIN_INVALID")
    _need(_integer(doc["training_steps"], 0, MAX_EPOCHS * MAX_PARTITION_ROWS)
          and _integer(doc["update_count"], 0, doc["training_steps"]),
          "CHECKPOINT_WORK_COUNTERS_REFUSED")
    _need(doc["training_provenance_verified"] is False, "CHECKPOINT_PROVENANCE_NOT_AUTHENTICATED")
    families, features = doc["training_family_ids"], doc["training_feature_sha256"]
    _need(type(families) is list and 1 <= len(families) <= MAX_PARTITION_ROWS
          and all(_slug(v) for v in families) and len(set(families)) == len(families),
          "CHECKPOINT_TRAINING_FAMILY_LINEAGE_REQUIRED")
    _need(type(features) is list and 1 <= len(features) <= MAX_PARTITION_ROWS
          and all(type(v) is str and SHA.fullmatch(v) is not None for v in features)
          and len(set(features)) == len(features), "CHECKPOINT_TRAINING_FEATURE_LINEAGE_REQUIRED")
    return doc


def _predict(weights: list[int], bias: int, features: list[int]) -> tuple[int, int]:
    score = sum(w * x for w, x in zip(weights, features)) + bias
    return int(score >= 0), score


def _checkpoint(weights, bias, dataset_sha, steps, updates, train) -> bytes:
    return _canonical({"schema": CHECKPOINT_SCHEMA, "model_type": MODEL_TYPE,
                       "feature_count": len(weights), "weights": list(weights),
                       "bias": bias, "training_dataset_sha256": dataset_sha,
                       "training_steps": steps, "update_count": updates,
                       "training_family_ids": sorted({r["family_id"] for r in train}),
                       "training_feature_sha256": sorted({_sha(_canonical(r["features"])) for r in train}),
                       "training_provenance_verified": False})


def score_toy_checkpoint(raw: object, expected_sha256: object, rows: object) -> dict:
    """Infer labels from numeric weights, never from supplied prediction fields.

    The digest must be obtained separately from the checkpoint; matching it
    still does not authenticate its training history. Only development rows
    are accepted. No protected-final inference or automatic deployment.
    """
    try:
        doc = _decode_checkpoint(raw, expected_sha256)
        groups = _validate_rows(rows, doc["feature_count"], development_only=True)
        predictions, correct = [], 0
        for row in groups["dev"]:
            _need(row["family_id"] not in doc["training_family_ids"]
                  and _sha(_canonical(row["features"])) not in doc["training_feature_sha256"],
                  "RELOADED_CHECKPOINT_TRAIN_DEV_CONTAMINATION")
            label, score = _predict(doc["weights"], doc["bias"], row["features"])
            correct += int(label == row["label"])
            predictions.append({"sample_id": row["sample_id"], "prediction": label,
                                "decision_score": score, "expected_label": row["label"]})
        return {"status": "LOCAL_TOY_CHECKPOINT_EVALUATED", "checkpoint_sha256": expected_sha256,
                "model_type": MODEL_TYPE, "sample_count": len(predictions),
                "correct": correct, "accuracy": correct / len(predictions),
                "predictions": predictions, "inference_executed": True,
                "trained_this_call": False, "training_provenance_verified": False,
                "promotion_authorized": False, "external_effect_authorized": False,
                "native_tool_invoked": False, "final_status": "HELD_UNEVALUATED"}
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return _refuse("CHECKPOINT_OR_DEVELOPMENT_INPUT_REFUSED")


def run_toy_experiment(request: object, *, allow_training: bool = False) -> dict:
    """Execute a finite integer perceptron experiment after explicit local opt-in."""
    if allow_training is not True:
        return _refuse("EXPLICIT_LOCAL_TRAINING_OPT_IN_REQUIRED")
    try:
        _need(type(request) is dict and set(request) == {
            "schema", "experiment_id", "feature_count", "epochs", "rows"},
            "EXPERIMENT_FIELDS_REFUSED")
        _need(request["schema"] == EXPERIMENT_SCHEMA and _slug(request["experiment_id"]),
              "EXPERIMENT_SCHEMA_OR_ID_REFUSED")
        n, epochs = request["feature_count"], request["epochs"]
        _need(_integer(n, 1, MAX_FEATURES) and _integer(epochs, 1, MAX_EPOCHS),
              "TRAINING_WORK_BUDGET_REFUSED")
        groups = _validate_rows(request["rows"], n, development_only=False)
        train = sorted(groups["train"], key=lambda r: r["sample_id"])
        dataset_sha = _sha(_canonical(train))
        weights, bias, steps, updates = [0] * n, 0, 0, 0
        epoch_mistakes = []
        for _ in range(epochs):
            mistakes = 0
            for row in train:
                predicted, _ = _predict(weights, bias, row["features"])
                error = row["label"] - predicted
                steps += 1
                if error:
                    weights = [w + error * x for w, x in zip(weights, row["features"])]
                    bias += error
                    updates += 1
                    mistakes += 1
            epoch_mistakes.append(mistakes)
        model = _checkpoint(weights, bias, dataset_sha, steps, updates, train)
        # Majority baseline is learned only from TRAIN; ties select class zero.
        majority = int(sum(r["label"] for r in train) > len(train) / 2)
        baseline = _checkpoint([0] * n, 1 if majority else -1, dataset_sha, 0, 0, train)
        candidate = score_toy_checkpoint(model, _sha(model), groups["dev"])
        reference = score_toy_checkpoint(baseline, _sha(baseline), groups["dev"])
        _need(candidate["status"] == reference["status"] == "LOCAL_TOY_CHECKPOINT_EVALUATED",
              "INTERNAL_CHECKPOINT_REPLAY_FAILED")
        improved = candidate["correct"] > reference["correct"]
        return {"status": "LOCAL_TOY_TRAIN_EVAL_COMPLETE", "model_type": MODEL_TYPE,
                "experiment_id": request["experiment_id"], "trained_this_call": True,
                "inference_executed": True, "training_steps": steps, "update_count": updates,
                "epoch_mistakes": epoch_mistakes, "training_dataset_sha256": dataset_sha,
                "train_n": len(train), "dev_n": len(groups["dev"]),
                "final_n": len(groups["final"]), "final_status": "HELD_UNEVALUATED",
                "candidate_correct": candidate["correct"], "baseline_correct": reference["correct"],
                "candidate_accuracy": candidate["accuracy"], "baseline_accuracy": reference["accuracy"],
                "checkpoint_utf8": model.decode("utf-8"), "checkpoint_sha256": _sha(model),
                "baseline_checkpoint_utf8": baseline.decode("utf-8"),
                "baseline_checkpoint_sha256": _sha(baseline),
                "selected_checkpoint_sha256": _sha(model if improved else baseline),
                "selection_reason": "CANDIDATE_DEV_IMPROVEMENT" if improved else "KEEP_BASELINE_NO_DEV_IMPROVEMENT",
                "promotion_authorized": False, "independent_examiner_verified": False,
                "training_provenance_verified": False, "native_tool_invoked": False,
                "external_effect_authorized": False, "gpu_used": False, "network_used": False}
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return _refuse("EXPERIMENT_INPUT_OR_BUDGET_REFUSED")


def restore_toy_baseline(candidate: object, candidate_sha: object,
                         baseline: object, baseline_sha: object) -> dict:
    """Recover exact baseline JSON bytes after verifying both pins and dimensions.

    This is local artifact recovery, NOT mutation of a deployed model or any
    host. Callers must separately authorize writing the returned bytes.
    """
    try:
        current = _decode_checkpoint(candidate, candidate_sha)
        previous = _decode_checkpoint(baseline, baseline_sha)
        _need(current["feature_count"] == previous["feature_count"]
              and current["training_dataset_sha256"] == previous["training_dataset_sha256"],
              "BASELINE_EXPERIMENT_MISMATCH")
        return {"status": "LOCAL_BASELINE_BYTES_RECOVERED", "checkpoint_utf8": baseline.decode("utf-8"),
                "checkpoint_sha256": baseline_sha, "deployment_changed": False,
                "promotion_authorized": False, "external_effect_authorized": False,
                "training_provenance_verified": False, "native_tool_invoked": False}
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return _refuse("BASELINE_RECOVERY_REFUSED")


def example_toy_experiment() -> dict:
    """Fictional, deterministic train/dev/final fixture; no external data."""
    rows = []
    records = (
        ("train-a", "a", "train", [-1, 0], 0),
        ("train-b", "b", "train", [1, 0], 1),
        ("dev-a", "c", "dev", [-1, -1], 0),
        ("dev-b", "d", "dev", [1, 1], 1),
        ("dev-c", "e", "dev", [-1, 1], 0),
        ("dev-d", "f", "dev", [1, -1], 1),
        ("final-a", "g", "final", None, None),
    )
    for sample, family, split, features, label in records:
        rows.append({"sample_id": sample, "family_id": "family-" + family,
                     "split": split, "features": features, "label": label})
    return {"schema": EXPERIMENT_SCHEMA, "experiment_id": "fictional-toy-model",
            "feature_count": 2, "epochs": 4, "rows": rows}
