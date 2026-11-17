"""LeetCode's node types plus list/level-order converters, so cases stay plain JSON."""

from __future__ import annotations

from collections import deque
from typing import Any


class ListNode:
    """Singly linked list node (LeetCode's `ListNode`, also accepts `ListNode(x)`)."""

    def __init__(self, val: int = 0, next: ListNode | None = None) -> None:
        """Create a node holding `val` that points at `next`."""
        self.val = val
        self.next = next


class TreeNode:
    """Binary tree node (LeetCode's `TreeNode`)."""

    def __init__(
        self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None
    ) -> None:
        """Create a node holding `val` with optional children."""
        self.val = val
        self.left = left
        self.right = right


class Interval:
    """Interval object used by premium problems such as 759 Employee Free Time."""

    def __init__(self, start: int = 0, end: int = 0) -> None:
        """Create the closed interval [start, end]."""
        self.start = start
        self.end = end


def to_list_node(values: list[int]) -> ListNode | None:
    """Build a linked list from a Python list; `[]` becomes `None`."""
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def from_list_node(node: Any) -> list[int]:
    """Flatten any object with `.val`/`.next` back into a Python list."""
    out: list[int] = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out


def to_tree(values: list[int | None]) -> TreeNode | None:
    """Build a binary tree from LeetCode level-order form, e.g. `[3, 9, 20, None, None, 15, 7]`."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    q, i = deque([root]), 1
    while q and i < len(values):
        node = q.popleft()
        for side in ("left", "right"):
            if i < len(values) and values[i] is not None:
                child = TreeNode(values[i])  # type: ignore[arg-type]
                setattr(node, side, child)
                q.append(child)
            i += 1
    return root
