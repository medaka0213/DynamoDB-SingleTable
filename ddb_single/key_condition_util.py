"""Utilities for DynamoDB KeyConditionExpression validation."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from ddb_single.error import InvalidParameterError

_LEAF_TYPES = frozenset(
    {
        "Equals",
        "LessThan",
        "LessThanEquals",
        "LessThanOrEqualTo",
        "GreaterThan",
        "GreaterThanEquals",
        "GreaterThanOrEqualTo",
        "BeginsWith",
        "Between",
    }
)


def _condition_subnodes(condition) -> tuple:
    """Return boto3 condition children tuple; fail fast if the shape is unexpected."""
    values = getattr(condition, "_values", None)
    if values is None:
        raise InvalidParameterError(
            "Unsupported KeyConditionExpression node (missing _values): %s"
            % type(condition).__name__
        )
    if not isinstance(values, tuple):
        raise InvalidParameterError(
            "Unsupported KeyConditionExpression node (_values is not a tuple): %s"
            % type(condition).__name__
        )
    return values


def iter_key_attributes_used_in_key_condition(condition) -> Iterable[str]:
    """Yield key attribute names referenced in a boto3 KeyConditionExpression tree."""
    if condition is None:
        return
    cls_name = condition.__class__.__name__
    if cls_name in ("And", "Or"):
        for sub in _condition_subnodes(condition):
            yield from iter_key_attributes_used_in_key_condition(sub)
        return
    if cls_name == "Not":
        inner = _condition_subnodes(condition)
        if inner:
            yield from iter_key_attributes_used_in_key_condition(inner[0])
        return
    if cls_name in _LEAF_TYPES:
        values = getattr(condition, "_values", None)
        if values is None or len(values) == 0:
            raise InvalidParameterError(
                "Unsupported KeyConditionExpression leaf (missing _values): %s"
                % cls_name
            )
        key_or_attr = values[0]
        name = getattr(key_or_attr, "name", None)
        if name is not None:
            yield name
        return
    raise InvalidParameterError(
        "Unsupported KeyConditionExpression node type: %s" % cls_name
    )


def validate_single_condition_per_key(condition) -> None:
    """Raise when the same key attribute is constrained more than once."""
    names = list(iter_key_attributes_used_in_key_condition(condition))
    counts = Counter(names)
    dups = sorted(k for k, v in counts.items() if v > 1)
    if dups:
        raise InvalidParameterError(
            "KeyConditionExpression uses multiple conditions for the same key attribute(s): %s"
            % ", ".join(dups)
        )
