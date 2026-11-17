"""Per-algorithm solvers: each takes the input dict and returns a JSON-serialisable result.

`algo g` copies a solver (plus its HELPERS) into a standalone file whose header imports only
json, sys, Counter, defaultdict, deque, heapq and Any, so solvers must stick to those.
"""

from __future__ import annotations

import heapq
from collections import Counter, defaultdict, deque
from typing import Any


def leetcode_200(data: dict[str, Any]) -> int:
    """DFS flood fill: count islands of '1' (or 1) cells."""
    grid = data["grid"]
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()

    def is_land(v: Any) -> bool:
        return v in {"1", 1}

    def dfs(r: int, c: int) -> None:
        stack = [(r, c)]
        while stack:
            x, y = stack.pop()
            if (
                (x, y) in seen
                or x < 0
                or y < 0
                or x >= rows
                or y >= cols
                or not is_land(grid[x][y])
            ):
                continue
            seen.add((x, y))
            stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    count = 0
    for r in range(rows):
        for c in range(cols):
            if is_land(grid[r][c]) and (r, c) not in seen:
                count += 1
                dfs(r, c)
    return count


def leetcode_994(data: dict[str, Any]) -> int:
    """Multi-source BFS: minutes until every fresh orange rots, or -1."""
    grid = data["grid"]
    rows, cols = len(grid), len(grid[0])
    rotten, fresh_cell = 2, 1
    q, fresh = deque(), 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == rotten:
                q.append((r, c, 0))
            elif grid[r][c] == fresh_cell:
                fresh += 1
    minutes = 0
    while q:
        r, c, minutes = q.popleft()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                q.append((nr, nc, minutes + 1))
    return minutes if fresh == 0 else -1


def leetcode_33(data: dict[str, Any]) -> int:
    """Binary search in a rotated sorted array: index of target, or -1."""
    nums, target = data["nums"], data["target"]
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        elif nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def leetcode_3(data: dict[str, Any]) -> int:
    """Sliding window: length of the longest substring without repeats."""
    s = data["s"]
    left, best, seen = 0, 0, {}
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best


def leetcode_210(data: dict[str, Any]) -> list[int]:
    """Kahn topological sort: a valid course order, or [] if there is a cycle."""
    n, prereqs = data["numCourses"], data["prerequisites"]
    graph = defaultdict(list)
    indeg = [0] * n
    for course, prereq in prereqs:
        graph[prereq].append(course)
        indeg[course] += 1
    q = deque([i for i, d in enumerate(indeg) if d == 0])
    order = []
    while q:
        node = q.popleft()
        order.append(node)
        for nxt in graph[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return order if len(order) == n else []


class DSU:
    """Disjoint-set union with path compression and union by rank."""

    def __init__(self) -> None:
        """Start with no elements; they are added on first use."""
        self.parent: dict[Any, Any] = {}
        self.rank: dict[Any, int] = {}

    def find(self, x: Any) -> Any:
        """Return the root of x's set."""
        self.parent.setdefault(x, x)
        self.rank.setdefault(x, 0)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: Any, b: Any) -> bool:
        """Merge the sets of a and b; False if they were already joined."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def leetcode_684(data: dict[str, Any]) -> list[int]:
    """Union-find: the first edge that closes a cycle."""
    dsu = DSU()
    for a, b in data["edges"]:
        if not dsu.union(a, b):
            return [a, b]
    return []


def leetcode_743(data: dict[str, Any]) -> int:
    """Dijkstra: time for a signal from k to reach all n nodes, or -1."""
    graph = defaultdict(list)
    for u, v, w in data["times"]:
        graph[u].append((v, w))
    n, start = data["n"], data["k"]
    dist = {}
    heap = [(0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if node in dist:
            continue
        dist[node] = d
        for nxt, w in graph[node]:
            if nxt not in dist:
                heapq.heappush(heap, (d + w, nxt))
    return max(dist.values()) if len(dist) == n else -1


def leetcode_347(data: dict[str, Any]) -> list[int]:
    """Count + heap: the k most frequent values."""
    counts = Counter(data["nums"])
    return [item for item, _ in heapq.nlargest(data["k"], counts.items(), key=lambda kv: kv[1])]


def leetcode_79(data: dict[str, Any]) -> bool:
    """Backtracking: does the word exist as a path in the board."""
    board, word = data["board"], data["word"]
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, i: int) -> bool:
        if i == len(word):
            return True
        if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != word[i]:
            return False
        tmp, board[r][c] = board[r][c], "#"
        ok = (
            dfs(r + 1, c, i + 1)
            or dfs(r - 1, c, i + 1)
            or dfs(r, c + 1, i + 1)
            or dfs(r, c - 1, i + 1)
        )
        board[r][c] = tmp
        return ok

    return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))


def leetcode_322(data: dict[str, Any]) -> int:
    """1-D DP: fewest coins that make amount, or -1."""
    coins, amount = data["coins"], data["amount"]
    inf = amount + 1
    dp = [0] + [inf] * amount
    for a in range(1, amount + 1):
        for coin in coins:
            if a - coin >= 0:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return dp[amount] if dp[amount] != inf else -1


def leetcode_1(data: dict[str, Any]) -> list[int]:
    """Hash map: indices of the two numbers that add to target."""
    seen: dict[int, int] = {}
    for i, x in enumerate(data["nums"]):
        if data["target"] - x in seen:
            return [seen[data["target"] - x], i]
        seen[x] = i
    return []


def solve_add(data: dict[str, Any]) -> Any:
    """Return a + b."""
    return data["a"] + data["b"]


def _merge(a: Any, b: Any) -> Any:
    """Recursively merge: dicts merge key-wise, lists concatenate, otherwise b wins."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _merge(out[k], v) if k in out else v
        return out
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    return b


def solve_deepmerge(data: dict[str, Any]) -> Any:
    """Deep-merge b into a (dicts key-wise, lists concatenated)."""
    return _merge(data["a"], data["b"])


SOLVERS = {
    "leetcode-1": leetcode_1,
    "leetcode-200": leetcode_200,
    "leetcode-994": leetcode_994,
    "leetcode-33": leetcode_33,
    "leetcode-3": leetcode_3,
    "leetcode-210": leetcode_210,
    "leetcode-684": leetcode_684,
    "leetcode-743": leetcode_743,
    "leetcode-347": leetcode_347,
    "leetcode-79": leetcode_79,
    "leetcode-322": leetcode_322,
    "add": solve_add,
    "deepmerge": solve_deepmerge,
}
