"""Strict, bounded input helpers for read-only specialist calculations."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import re
from typing import Any

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fields(value: Any, names: set[str]) -> dict:
    require(type(value) is dict and set(value) == names, 'INVALID_FIELDS:' + ','.join(sorted(names)))
    return value


def text(value: Any, maximum: int = 2000) -> str:
    require(type(value) is str and 0 < len(value) <= maximum and bool(value.strip()), 'INVALID_TEXT')
    require(not any(ord(ch) < 32 for ch in value), 'CONTROL_CHARACTER')
    return value


def identifier(value: Any) -> str:
    require(type(value) is str and _ID.fullmatch(value) is not None, 'INVALID_IDENTIFIER')
    return value


def integer(value: Any, minimum: int = 0, maximum: int = 10**12) -> int:
    require(type(value) is int and minimum <= value <= maximum, 'INTEGER_OUT_OF_BOUNDS')
    return value


def boolean(value: Any) -> bool:
    require(type(value) is bool, 'BOOLEAN_REQUIRED')
    return value


def rows(value: Any, maximum: int = 1000, minimum: int = 0) -> list:
    require(type(value) is list and minimum <= len(value) <= maximum, 'LIST_OUT_OF_BOUNDS')
    return value


def unique_ids(values: Any, maximum: int = 1000) -> list[str]:
    result = [identifier(v) for v in rows(values, maximum)]
    require(len(result) == len(set(result)), 'DUPLICATE_IDENTIFIER')
    return result


def decimal_value(value: Any, minimum: str = '0', maximum: str = '1000000000000', *,
                  lower_open: bool = False, upper_open: bool = False) -> Decimal:
    require(type(value) in (str, int), 'DECIMAL_STRING_OR_INTEGER_REQUIRED')
    raw = str(value)
    require(len(raw) <= 64 and re.fullmatch(r'-?\d+(?:\.\d{1,18})?', raw) is not None,
            'INVALID_FINITE_DECIMAL')
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError('INVALID_FINITE_DECIMAL') from exc
    low, high = Decimal(minimum), Decimal(maximum)
    require(number.is_finite() and (number > low if lower_open else number >= low)
            and (number < high if upper_open else number <= high), 'DECIMAL_OUT_OF_BOUNDS')
    return number


def decimal_text(value: Decimal) -> str:
    if value == 0:
        return '0'
    return format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')


def timestamp(value: Any) -> datetime:
    raw = text(value, 64)
    require('T' in raw, 'TIMESTAMP_REQUIRED')
    try:
        moment = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('INVALID_TIMESTAMP') from exc
    require(moment.tzinfo is not None and moment.utcoffset() is not None, 'TIMESTAMP_OFFSET_REQUIRED')
    return moment.astimezone(timezone.utc)


def bounded_json(value: Any) -> None:
    """Reject non-JSON types, cycles, oversized trees and nonfinite values."""
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        require(count <= 30000 and depth <= 32, 'INPUT_BUDGET_EXCEEDED')
        if type(item) is dict:
            require(len(item) <= 2000 and all(type(k) is str and len(k) <= 128 for k in item),
                    'INVALID_OBJECT_KEYS')
            stack.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            require(len(item) <= 10000, 'INPUT_LIST_TOO_LARGE')
            stack.extend((v, depth + 1) for v in item)
        elif type(item) is str:
            require(len(item) <= 20000 and '\x00' not in item, 'INPUT_TEXT_TOO_LARGE_OR_NUL')
        elif type(item) is float:
            require(math.isfinite(item), 'NONFINITE_NUMBER')
        elif type(item) is int:
            require(abs(item) <= 10**15, 'INTEGER_TOO_LARGE')
        else:
            require(item is None or type(item) is bool, 'NON_JSON_VALUE')


def canonical(value: Any) -> str:
    bounded_json(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def parse_json(raw: str) -> Any:
    require(type(raw) is str and len(raw.encode('utf-8')) <= 2_000_000, 'JSON_SIZE_LIMIT')
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = item
        return result
    def invalid(_):
        raise ValueError('NONFINITE_JSON_NUMBER')
    try:
        result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('INVALID_JSON') from exc
    bounded_json(result)
    return result
