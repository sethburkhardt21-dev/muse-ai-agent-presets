"""Bounded, genuine synthetic linear-model learning; no LLM or provider runtime.

This additive engine does not change the original R33 model_eval.py contract.
Decimal strings and an explicit context make the arithmetic reproducible without
BLAS, GPUs, pickle, executables or platform-dependent floating-point reductions.
The protected final partition contains identifiers only and is never scored.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from typing import Any

MAX_JSON_BYTES = 65536
MAX_ROWS = 128
MAX_STEPS = 128
MAX_DIMENSIONS = 4
SCHEMA = "r60/toy-linear-dataset-v1"
CHECKPOINT_SCHEMA = "r60/toy-linear-checkpoint-v1"
SCOPE = "SYNTHETIC_OFFLINE_LINEAR_MODEL_ONLY"
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z", re.ASCII)
SHA = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)
INPUT_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,12})?\Z", re.ASCII)
RESULT_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,30})?\Z", re.ASCII)
MATH_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN, Emin=-999, Emax=999)
QUANTUM = Decimal("0.000000000000000000000000000001")
ZERO = Decimal(0)
ONE = Decimal(1)


class Refused(ValueError):
    """The bounded source/input contract was not met; no authority is granted."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise Refused("NONCANONICAL_JSON") from exc


def _unique(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise Refused("DUPLICATE_JSON_KEY")
        result[name] = value
    return result


def _integer(text: str) -> int:
    if len(text) > 6:
        raise Refused("JSON_INTEGER_BUDGET")
    return int(text)


def _non_integer(text: str):
    raise Refused("JSON_NUMBERS_REQUIRE_DECIMAL_STRINGS")


def strict_json(raw: bytes, *, limit: int = MAX_JSON_BYTES) -> dict:
    if type(raw) is not bytes or not 1 <= len(raw) <= limit:
        raise Refused("JSON_SIZE_BUDGET")
    # Bound nesting before parsing. Brackets within quoted strings do not count.
    depth = 0
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 16:
                raise Refused("JSON_DEPTH_BUDGET")
        elif byte in (93, 125):
            depth -= 1
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                            parse_int=_integer, parse_float=_non_integer,
                            parse_constant=_non_integer)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Refused("MALFORMED_JSON") from exc
    if type(result) is not dict:
        raise Refused("JSON_OBJECT_REQUIRED")
    return result


def _slug(value: object) -> bool:
    return type(value) is str and len(value) <= 64 and SLUG.fullmatch(value) is not None


def _sha(value: object) -> bool:
    return type(value) is str and SHA.fullmatch(value) is not None


def _number(value: object, *, result: bool = False, bound: str = "1000") -> Decimal:
    expression = RESULT_DECIMAL if result else INPUT_DECIMAL
    if type(value) is not str or len(value) > 48 or expression.fullmatch(value) is None:
        raise Refused("INVALID_DECIMAL_STRING")
    number = Decimal(value)
    if not number.is_finite() or number.copy_abs() > Decimal(bound):
        raise Refused("DECIMAL_RANGE")
    return number


def _text(value: Decimal) -> str:
    number = value.quantize(QUANTUM)
    # Squared-error metrics have squared units and can exceed parameter limits.
    # Parameter validation and optimizer bounds remain independently constrained.
    if not number.is_finite() or number.copy_abs() > Decimal("1000000000000"):
        raise Refused("NUMERIC_RESULT_BUDGET")
    if number == ZERO:
        return "0"
    return format(number, "f").rstrip("0").rstrip(".")


def validate_dataset(data: object) -> dict:
    expected = {"schema", "dataset_id", "data_kind", "dimensions", "rows"}
    if type(data) is not dict or set(data) != expected:
        raise Refused("DATASET_FIELDS")
    if data["schema"] != SCHEMA or data["data_kind"] != "synthetic":
        raise Refused("SYNTHETIC_DATASET_SCHEMA_REQUIRED")
    if not _slug(data["dataset_id"]):
        raise Refused("INVALID_DATASET_ID")
    dimensions = data["dimensions"]
    if type(dimensions) is not int or not 1 <= dimensions <= MAX_DIMENSIONS:
        raise Refused("DIMENSION_BUDGET")
    rows = data["rows"]
    if type(rows) is not list or not 1 <= len(rows) <= MAX_ROWS:
        raise Refused("ROWS_BUDGET")
    partitions: dict[str, list] = {"train": [], "dev": [], "final": []}
    seen: set[str] = set()
    families: dict[str, str] = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"id", "family", "split", "features", "target"}:
            raise Refused("ROW_FIELDS")
        name, family, split = row["id"], row["family"], row["split"]
        if not _slug(name) or name in seen or not _slug(family):
            raise Refused("INVALID_OR_DUPLICATE_ID")
        if type(split) is not str or split not in partitions:
            raise Refused("PARTITION_INVALID")
        seen.add(name)
        if family in families and families[family] != split:
            raise Refused("CROSS_PARTITION_FAMILY_LEAKAGE")
        families[family] = split
        if split == "final":
            if row["features"] is not None or row["target"] is not None:
                raise Refused("PROTECTED_FINAL_EXPOSED")
            partitions[split].append(name)
            continue
        vector = row["features"]
        if type(vector) is not list or len(vector) != dimensions:
            raise Refused("FEATURE_DIMENSION")
        features = tuple(_number(v, bound="1") for v in vector)
        target = _number(row["target"])
        partitions[split].append((features, target))
    if not (2 <= len(partitions["train"]) <= 64 and
            2 <= len(partitions["dev"]) <= 48 and
            1 <= len(partitions["final"]) <= 16):
        raise Refused("PARTITION_COUNT_BUDGET")
    return {"dimensions": dimensions, **partitions}


def training_config(dimensions: int, steps: object, learning_rate: object) -> dict:
    if type(steps) is not int or not 1 <= steps <= MAX_STEPS:
        raise Refused("OPTIMIZER_STEPS_BUDGET")
    with localcontext(MATH_CONTEXT):
        rate = _number(learning_rate, bound="1")
        # Conservative rate bound for normalized features and squared loss.
        if not ZERO < rate <= ONE / (4 * (dimensions + 1)):
            raise Refused("LEARNING_RATE_BUDGET")
    return {"schema": "r60/toy-training-config-v1", "steps": steps,
            "learning_rate": learning_rate}


def _prediction(weights: list[Decimal], bias: Decimal, vector: tuple[Decimal, ...]) -> Decimal:
    return bias + sum((w*x for w, x in zip(weights, vector)), ZERO)


def _mse(weights: list[Decimal], bias: Decimal, rows: list) -> Decimal:
    return sum(((_prediction(weights, bias, x)-y)**2 for x, y in rows), ZERO) / len(rows)


def _checkpoint(data_pin: str, config_pin: str, weights: list[Decimal], bias: Decimal,
                steps: int, parent: str | None) -> dict:
    return {"schema": CHECKPOINT_SCHEMA, "scope": SCOPE,
            "dataset_sha256": data_pin, "training_config_sha256": config_pin,
            "kind": "baseline" if steps == 0 else "candidate",
            "dimensions": len(weights), "weights": [_text(w) for w in weights],
            "bias": _text(bias), "optimizer_steps": steps, "parent_sha256": parent}


def validate_checkpoint(checkpoint: object) -> tuple[list[Decimal], Decimal]:
    keys = {"schema", "scope", "dataset_sha256", "training_config_sha256", "kind",
            "dimensions", "weights", "bias", "optimizer_steps", "parent_sha256"}
    if type(checkpoint) is not dict or set(checkpoint) != keys:
        raise Refused("CHECKPOINT_FIELDS")
    c = checkpoint
    if c["schema"] != CHECKPOINT_SCHEMA or c["scope"] != SCOPE:
        raise Refused("CHECKPOINT_SCHEMA")
    if not _sha(c["dataset_sha256"]) or not _sha(c["training_config_sha256"]):
        raise Refused("CHECKPOINT_SOURCE_PIN")
    if type(c["dimensions"]) is not int or not 1 <= c["dimensions"] <= MAX_DIMENSIONS:
        raise Refused("CHECKPOINT_DIMENSIONS")
    if type(c["optimizer_steps"]) is not int or not 0 <= c["optimizer_steps"] <= MAX_STEPS:
        raise Refused("CHECKPOINT_STEPS")
    if c["optimizer_steps"] == 0:
        if c["kind"] != "baseline" or c["parent_sha256"] is not None:
            raise Refused("BASELINE_LINEAGE")
    elif c["kind"] != "candidate" or not _sha(c["parent_sha256"]):
        raise Refused("CANDIDATE_LINEAGE")
    if type(c["weights"]) is not list or len(c["weights"]) != c["dimensions"]:
        raise Refused("CHECKPOINT_WEIGHTS")
    weights = [_number(w, result=True, bound="1000000") for w in c["weights"]]
    bias = _number(c["bias"], result=True, bound="1000000")
    return weights, bias


def predict(checkpoint: object, features: object) -> str:
    with localcontext(MATH_CONTEXT):
        weights, bias = validate_checkpoint(checkpoint)
        if type(features) is not list or len(features) != len(weights):
            raise Refused("PREDICTION_FEATURES")
        vector = tuple(_number(x, bound="1") for x in features)
        return _text(_prediction(weights, bias, vector))


def fit_experiment(data: object, *, steps: int = 64, learning_rate: str = "0.05") -> dict:
    """Run actual batch-gradient updates on train only; compare dev, hold final.

    Returned values carry no native deployment, dataset-authority or external
    reviewer proof. This engine only learns a small linear toy model.
    """
    try:
        with localcontext(MATH_CONTEXT):
            partition = validate_dataset(data)
            dimensions = partition["dimensions"]
            config = training_config(dimensions, steps, learning_rate)
            rate = Decimal(learning_rate)
            train = partition["train"]
            weights = [ZERO] * dimensions
            bias = (sum((y for _, y in train), ZERO) / len(train)).quantize(QUANTUM)
            data_pin = digest(canonical_json(data))
            config_pin = digest(canonical_json(config))
            baseline = _checkpoint(data_pin, config_pin, weights, bias, 0, None)
            baseline_mse = _mse(weights, bias, partition["dev"])
            train_before = _mse(weights, bias, train)
            for _ in range(steps):
                errors = [(_prediction(weights, bias, x)-y, x) for x, y in train]
                gradients = [2*sum((e*x[j] for e, x in errors), ZERO)/len(train)
                             for j in range(dimensions)]
                bias_gradient = 2*sum((e for e, _ in errors), ZERO)/len(train)
                weights = [(w-rate*g).quantize(QUANTUM) for w, g in zip(weights, gradients)]
                bias = (bias-rate*bias_gradient).quantize(QUANTUM)
                if any(not w.is_finite() or abs(w) > 1000000 for w in weights+[bias]):
                    raise Refused("OPTIMIZER_NUMERIC_BUDGET")
            candidate = _checkpoint(data_pin, config_pin, weights, bias, steps,
                                    digest(canonical_json(baseline)))
            candidate_mse = _mse(weights, bias, partition["dev"])
            # Compare quantized, reproducible metrics; no external promotion.
            baseline_mse = baseline_mse.quantize(QUANTUM)
            candidate_mse = candidate_mse.quantize(QUANTUM)
            improved = candidate_mse < baseline_mse
            evaluation = {
                "schema": "r60/toy-dev-evaluation-v1", "scope": SCOPE,
                "dataset_sha256": data_pin, "optimizer_steps": steps,
                "train_count": len(train), "dev_count": len(partition["dev"]),
                "final_count": len(partition["final"]),
                "baseline_mse": _text(baseline_mse), "candidate_mse": _text(candidate_mse),
                "delta_mse": _text(candidate_mse-baseline_mse),
                "train_mse_before": _text(train_before),
                "train_mse_after": _text(_mse(weights, bias, train)),
                "selected_checkpoint": "candidate" if improved else "baseline",
                "fallback_to_baseline": not improved, "final_status": "HELD_UNEVALUATED",
                "promotion_authorized": False, "native_muse_invoked": False,
                "external_effect_authorized": False,
                "dataset_source_independently_verified": False,
                "llm_training_performed": False,
            }
            return {"baseline": baseline, "candidate": candidate,
                    "evaluation": evaluation, "config": config}
    except DecimalException as exc:
        raise Refused("BOUNDED_DECIMAL_ARITHMETIC_FAILED") from exc
