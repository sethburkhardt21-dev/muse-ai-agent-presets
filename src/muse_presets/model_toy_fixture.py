"""Reviewed fictional input for the bounded local toy optimizer; no owner data."""
from __future__ import annotations
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext


def example_dataset() -> dict:
    with localcontext(Context(prec=64, rounding=ROUND_HALF_EVEN)):
        rows = []
        for i, value in enumerate(("-1", "-0.5", "0", "0.5", "1")):
            rows.append({"id": f"train-{i}", "family": f"train-family-{i}",
                         "split": "train", "features": [value],
                         "target": str(Decimal(value)*2+1)})
        for i, value in enumerate(("-0.75", "0.25", "0.75")):
            rows.append({"id": f"dev-{i}", "family": f"dev-family-{i}",
                         "split": "dev", "features": [value],
                         "target": str(Decimal(value)*2+1)})
        rows.append({"id": "final-0", "family": "final-family", "split": "final",
                     "features": None, "target": None})
        return {"schema": "r60/toy-linear-dataset-v1", "dataset_id": "linear-fixture",
                "data_kind": "synthetic", "dimensions": 1, "rows": rows}
