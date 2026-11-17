from __future__ import annotations

from collections import Counter
from typing import Any


def _freeze(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    return value


def exact(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when actual == expected."""
    return actual == expected


def unordered_array(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when both hold the same multiset of elements."""
    return Counter(actual) == Counter(expected)


def unordered_nested_array(
    actual: Any, expected: Any, context: dict[str, Any] | None = None
) -> bool:
    """Pass when both hold the same multiset of inner lists/dicts."""
    return Counter(_freeze(x) for x in actual) == Counter(_freeze(x) for x in expected)


def number(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when equal and numeric."""
    return actual == expected and isinstance(actual, (int, float))


def boolean(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when actual is expected (True/False identity)."""
    return actual is expected


def string(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when equal and a string."""
    return actual == expected and isinstance(actual, str)


def topo_order(actual: Any, expected: Any, context: dict[str, Any] | None = None) -> bool:
    """Pass when actual is a valid topological order.

    `expected` is either an exact accepted order or the course-schedule input
    (`numCourses` + `prerequisites`), in which case any valid order passes.
    """
    if isinstance(expected, list):
        return actual == expected
    if not isinstance(expected, dict):
        return False
    n = expected.get("numCourses")
    prereqs = expected.get("prerequisites", [])
    if not isinstance(actual, list) or len(actual) != n or set(actual) != set(range(n)):
        return False
    pos = {course: i for i, course in enumerate(actual)}
    return all(pos[pre] < pos[course] for course, pre in prereqs)


COMPARATORS = {
    "exact": exact,
    "unordered-array": unordered_array,
    "unordered-nested-array": unordered_nested_array,
    "number": number,
    "boolean": boolean,
    "string": string,
    "topo-order": topo_order,
}
