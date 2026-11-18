"""Test specs for every solution: hand cases, random generators, comparators, brute-force oracles.

A `Spec` tells the verifier how to call a solution, how to build random inputs, and what to compare
against: the cnkyrpsgl/leetcode reference when it has the problem, otherwise `oracle` (a slow,
obviously-correct brute force) and/or the `expect` values from the LeetCode examples.
"""

from __future__ import annotations

import ast
import itertools
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import random

Args = tuple[Any, ...]
Check = Callable[[Args, Any, Any], bool]


@dataclass
class Spec:
    """How to exercise one problem."""

    kinds: tuple[str, ...] = ()  # per-arg conversion: ll, lls, tree, intervals ("" = as is)
    # exact | unordered | nested | float | ll | arg0 (in place: compare args[0]) | callable
    out: str | Check = "exact"
    cases: list[Args] = field(default_factory=list)
    expect: list[Any] = field(default_factory=list)  # expected outputs for the first cases
    gen: Callable[[random.Random], Args] | None = None
    oracle: Callable[..., Any] | None = None
    design: bool = False  # args = (ops, params) like LeetCode's design-problem format
    bad_ref: str = ""  # why the cnkyrpsgl solution is wrong; the oracle is used instead


# ── random input helpers ────────────────────────────────────────────────────────────────────────


def ints(r: random.Random, n: tuple[int, int] = (1, 9), v: tuple[int, int] = (-9, 9)) -> list[int]:
    """Random int list with length in n and values in v."""
    return [r.randint(*v) for _ in range(r.randint(*n))]


def word(r: random.Random, n: tuple[int, int] = (0, 8), alpha: str = "abc") -> str:
    """Random string."""
    return "".join(r.choice(alpha) for _ in range(r.randint(*n)))


def tree(r: random.Random, n: int = 8, v: tuple[int, int] = (-5, 5)) -> list[int | None]:
    """Random level-order tree list."""
    size = r.randint(0, n)
    return [r.randint(*v)] + [r.randint(*v) if r.random() < 0.7 else None for _ in range(size)]  # noqa: PLR2004


def sorted_ints(r: random.Random, n: tuple[int, int] = (0, 8)) -> list[int]:
    """Random sorted int list."""
    return sorted(ints(r, n, (-5, 5)))


def roman(x: int) -> str:
    """Integer -> Roman numeral (for generating 13's inputs)."""
    table = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    out = ""
    for v, s in table:
        while x >= v:
            out, x = out + s, x - v
    return out


def expr(r: random.Random, depth: int = 3) -> str:
    """Random calculator expression with + - * / and parentheses (for 772)."""
    if depth == 0 or r.random() < 0.3:  # noqa: PLR2004
        return str(r.randint(0, 20))
    a, op = expr(r, depth - 1), r.choice("+-*/")
    b = str(r.randint(1, 9)) if op == "/" else expr(r, depth - 1)
    e = f"{a}{op}{b}"
    return f"({e})" if r.random() < 0.5 else e  # noqa: PLR2004


def fexpr(r: random.Random, depth: int = 4) -> tuple[str, int]:
    """Random op(a,b) expression and its value, with exact divisions (for 3749)."""
    if depth == 0 or r.random() < 0.3:  # noqa: PLR2004
        v = r.randint(-30, 30)
        return str(v), v
    (sa, a), (sb, b) = fexpr(r, depth - 1), fexpr(r, depth - 1)
    op = r.choice(["add", "sub", "mul", "div"])
    if op == "div":
        if b == 0:
            op = "add"
        else:
            sa, a = f"mul({sa},{sb})", a * b  # make it divide exactly
    val = {"add": a + b, "sub": a - b, "mul": a * b, "div": a // b if b and a % b == 0 else 0}[op]
    return f"{op}({sa},{sb})", val


# ── checks for problems with several valid answers ──────────────────────────────────────────────


def check_two_sum(args: Args, a: Any, _b: Any) -> bool:
    """Indices are distinct and add to target."""
    nums, target = args
    return len(a) == 2 and a[0] != a[1] and nums[a[0]] + nums[a[1]] == target  # noqa: PLR2004


def check_palindrome(args: Args, a: str, b: str) -> bool:
    """Same length as the other answer, a palindrome, and a substring."""
    return len(a) == len(b) and a == a[::-1] and a in args[0]


def check_top_k(args: Args, a: list[int], b: list[int]) -> bool:
    """Same multiset of frequencies (ties may pick different values)."""
    from collections import Counter

    c = Counter(args[0])
    return len(set(a)) == len(a) == args[1] and sorted(c[x] for x in a) == sorted(c[x] for x in b)


def check_dup_substring(args: Args, a: str, b: str) -> bool:
    """Same length and actually occurs twice."""
    s = args[0]
    return len(a) == len(b) and (not a or s.find(a) != s.rfind(a) or s.find(a, s.find(a) + 1) >= 0)


def check_happy(args: Args, a: str, b: Any) -> bool:
    """Valid diverse string of the oracle's (maximum) length."""
    counts = dict(zip("abc", args, strict=True))
    ok = all(a.count(ch) <= counts[ch] for ch in "abc") and not any(
        t in a for t in ("aaa", "bbb", "ccc")
    )
    return ok and len(a) == (b if isinstance(b, int) else len(b))


# ── brute-force oracles (for problems the reference repo lacks) ─────────────────────────────────


def brute_atoi(s: str) -> int:
    """Regex reading of the spec: spaces, optional sign, ASCII digits, clamp to int32."""
    import re

    m = re.match(r" *([+-]?[0-9]+)", s)
    return max(-(2**31), min(2**31 - 1, int(m.group(1)))) if m else 0


def _trunc_div(a: int, b: int) -> int:
    """Integer division truncating toward zero (C/Java semantics)."""
    return abs(a) // abs(b) * (1 if (a >= 0) == (b > 0) else -1)


_ARITH: dict[str, Callable[[int, int], int]] = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": _trunc_div,
}
_AST_OPS: dict[type[ast.operator], str] = {
    ast.Add: "add",
    ast.Sub: "sub",
    ast.Mult: "mul",
    ast.Div: "div",
}


def _ast_int(node: ast.AST) -> int:
    """Evaluate integer literals, unary minus, + - * / and add/sub/mul/div(a,b) calls.

    A whitelist walk over Python's parse tree — no eval — used by the 772 and 3749 oracles.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_ast_int(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _AST_OPS:
        return _ARITH[_AST_OPS[type(node.op)]](_ast_int(node.left), _ast_int(node.right))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _ARITH:
        a, b = (_ast_int(x) for x in node.args)
        return _ARITH[node.func.id](a, b)
    raise ValueError(f"unsupported expression node: {ast.dump(node)}")


def brute_calc(s: str) -> int:
    """Walk Python's own parse tree, dividing with truncation toward zero."""
    return _ast_int(ast.parse(s, mode="eval").body)


def brute_koko(piles: list[int], h: int) -> int:
    """Smallest speed by linear scan."""
    return next(k for k in range(1, max(piles) + 1) if sum(-(-p // k) for p in piles) <= h)


def brute_can_change(start: str, target: str) -> bool:
    """BFS over every reachable string."""
    seen, q = {start}, deque([start])
    while q:
        s = q.popleft()
        if s == target:
            return True
        for i, ch in enumerate(s):
            j = i - 1 if ch == "L" else i + 1 if ch == "R" else None
            if j is not None and 0 <= j < len(s) and s[j] == "_":
                t = list(s)
                t[i], t[j] = "_", ch
                u = "".join(t)
                if u not in seen:
                    seen.add(u)
                    q.append(u)
    return False


def brute_sum_counts(nums: list[int]) -> int:
    """O(n^3): every subarray, count distinct directly."""
    return sum(
        len(set(nums[i:j])) ** 2 for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)
    )


def brute_visible(heights: list[int]) -> list[int]:
    """O(n^2): j is visible from i if everyone between is shorter than both."""
    n = len(heights)
    return [
        sum(
            1
            for j in range(i + 1, n)
            if all(heights[m] < min(heights[i], heights[j]) for m in range(i + 1, j))
        )
        for i in range(n)
    ]


def brute_sortable(nums: list[int]) -> int:
    """Try every rotation of every block."""
    n, total = len(nums), 0
    for k in range(1, n + 1):
        if n % k:
            continue
        out: list[int] = []
        for lo in range(0, n, k):
            b = nums[lo : lo + k]
            rots = [b[i:] + b[:i] for i in range(k)]
            good = [x for x in rots if x == sorted(x)]
            if not good:
                break
            out += good[0]
        else:
            if out == sorted(nums):
                total += k
    return total


def brute_min_ops_sort(s: str) -> int:
    """BFS: sort any proper substring per move."""
    goal = "".join(sorted(s))
    dist, q = {s: 0}, deque([s])
    while q:
        cur = q.popleft()
        if cur == goal:
            return dist[cur]
        n = len(cur)
        for i in range(n):
            for j in range(i + 1, n + 1):
                if j - i == n:
                    continue
                nxt = cur[:i] + "".join(sorted(cur[i:j])) + cur[j:]
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)
    return -1


def brute_good_subarray(nums: list[int], k: int) -> int:
    """O(n^2) over all (i, j) with |nums[i] - nums[j]| == k."""
    best = None
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if abs(nums[i] - nums[j]) == k:
                s = sum(nums[i : j + 1])
                best = s if best is None else max(best, s)
    return best if best is not None else 0


def brute_sort_permutation(nums: list[int]) -> int:
    """Largest k for which swap components (a&b==k) can each sort themselves."""
    n = len(nums)
    if nums == sorted(nums):
        return 0

    def find(parent: list[int], x: int) -> int:
        while parent[x] != x:
            x = parent[x]
        return x

    for k in range(n, -1, -1):
        parent = list(range(n))
        for a in range(n):
            for b in range(a + 1, n):
                if a & b == k:
                    parent[find(parent, a)] = find(parent, b)
        if all(find(parent, v) == find(parent, i) for i, v in enumerate(nums)):  # v must reach v
            return k
    return 0


def brute_good_numbers(n: int) -> int:
    """Enumerate every digit string of length n."""
    return sum(
        1
        for digits in itertools.product(range(10), repeat=n)
        if all((d % 2 == 0) if i % 2 == 0 else d in (2, 3, 5, 7) for i, d in enumerate(digits))
    )


def brute_shortest_path(n: int, edges: list[list[int]], labels: str, k: int) -> int:
    """Bellman-Ford relaxation over (node, run) states."""
    inf = float("inf")
    dist = {(0, 1): 0}
    for _ in range(n * (k + 1) + 1):
        changed = False
        for (u, run), d in list(dist.items()):
            for a, b, w in edges:
                if a == u:
                    nxt = run + 1 if labels[b] == labels[u] else 1
                    if nxt <= k and d + w < dist.get((b, nxt), inf):
                        dist[(b, nxt)] = d + w
                        changed = True
        if not changed:
            break
    best = min((d for (u, _), d in dist.items() if u == n - 1), default=inf)
    return -1 if best == inf else int(best)


def brute_happy_len(a: int, b: int, c: int) -> int:
    """DFS for the maximum diverse-string length."""
    best = 0

    def go(cnt: list[int], last: str, run: int, length: int) -> None:
        nonlocal best
        best = max(best, length)
        for i, ch in enumerate("abc"):
            if cnt[i] and not (ch == last and run == 2):  # noqa: PLR2004
                cnt[i] -= 1
                go(cnt, ch, run + 1 if ch == last else 1, length + 1)
                cnt[i] += 1

    go([a, b, c], "", 0, 0)
    return best


def brute_alternating(nums: list[int]) -> int:
    """Every subsequence."""
    best = 0
    for mask in range(1, 1 << len(nums)):
        picked = [x for i, x in enumerate(nums) if mask >> i & 1]
        best = max(best, sum(x if i % 2 == 0 else -x for i, x in enumerate(picked)))
    return best


def brute_eval(expression: str) -> int:
    """Evaluate op(a,b): it is valid Python call syntax, so walk its parse tree (no eval)."""
    return _ast_int(ast.parse(expression, mode="eval").body)


def brute_max_probability(
    n: int, edges: list[list[int]], probs: list[float], s: int, e: int
) -> float:
    """Bellman-Ford on products."""
    best = [0.0] * n
    best[s] = 1.0
    for _ in range(n):
        for (a, b), p in zip(edges, probs, strict=True):
            best[b] = max(best[b], best[a] * p)
            best[a] = max(best[a], best[b] * p)
    return best[e]


def brute_count_servers(n: int, logs: list[list[int]], x: int, queries: list[int]) -> list[int]:
    """Per query, scan every log."""
    return [n - len({s for s, t in logs if q - x <= t <= q}) for q in queries]


def brute_safeness(grid: list[list[int]]) -> int:
    """Try every threshold d from high to low; BFS through cells at distance >= d."""
    n = len(grid)
    thieves = [(r, c) for r in range(n) for c in range(n) if grid[r][c]]
    dist = [[min(abs(r - a) + abs(c - b) for a, b in thieves) for c in range(n)] for r in range(n)]
    for d in range(2 * n, -1, -1):
        if dist[0][0] >= d and (n - 1, n - 1) in _reachable(dist, d):
            return d
    return 0


def _reachable(dist: list[list[int]], d: int) -> set[tuple[int, int]]:
    """Cells reachable from (0, 0) through cells whose distance is at least d."""
    n = len(dist)
    seen, q = {(0, 0)}, deque([(0, 0)])
    while q:
        r, c = q.popleft()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            inside = 0 <= nr < n and 0 <= nc < n
            if inside and (nr, nc) not in seen and dist[nr][nc] >= d:
                seen.add((nr, nc))
                q.append((nr, nc))
    return seen


def brute_good_nodes(values: list[int | None]) -> int:
    """Rebuild root-to-node paths by index arithmetic on a materialised tree."""
    from algo.leetcode.structures import to_tree

    count = 0

    def walk(node: Any, path: list[int]) -> None:
        nonlocal count
        if node:
            count += all(node.val >= p for p in path)
            walk(node.left, [*path, node.val])
            walk(node.right, [*path, node.val])

    walk(to_tree(values), [])
    return count


# ── random generators that need structure ───────────────────────────────────────────────────────


def gen_islands_grid(r: random.Random) -> Args:
    """Grid of '0'/'1'."""
    rows, cols = r.randint(1, 6), r.randint(1, 6)
    return ([[r.choice("01") for _ in range(cols)] for _ in range(rows)],)


def gen_battleships(r: random.Random) -> Args:
    """Valid board: non-adjacent straight ships."""
    rows, cols = r.randint(1, 6), r.randint(1, 6)
    b = [["."] * cols for _ in range(rows)]
    for _ in range(r.randint(0, 5)):
        horiz, length = r.random() < 0.5, r.randint(1, 3)  # noqa: PLR2004
        x, y = r.randrange(rows), r.randrange(cols)
        cells = [(x, y + i) if horiz else (x + i, y) for i in range(length)]
        if all(0 <= a < rows and 0 <= c < cols for a, c in cells) and all(
            b[a + da][c + dc] == "."
            for a, c in cells
            for da in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if 0 <= a + da < rows and 0 <= c + dc < cols
        ):
            for a, c in cells:
                b[a][c] = "X"
    return (b,)


def gen_black_pixels(r: random.Random) -> Args:
    """One connected black region (random walk) plus a pixel inside it."""
    rows, cols = r.randint(1, 6), r.randint(1, 6)
    img = [["0"] * cols for _ in range(rows)]
    x, y = r.randrange(rows), r.randrange(cols)
    sx, sy = x, y
    for _ in range(r.randint(1, 12)):
        img[x][y] = "1"
        dx, dy = r.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        if 0 <= x + dx < rows and 0 <= y + dy < cols:
            x, y = x + dx, y + dy
    return (img, sx, sy)


def gen_circle(r: random.Random) -> Args:
    """Symmetric adjacency matrix."""
    n = r.randint(1, 7)
    m = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if r.random() < 0.25:  # noqa: PLR2004
                m[i][j] = m[j][i] = 1
    return (m,)


def gen_edges(r: random.Random, n: int, m: int, directed: bool = False) -> list[list[int]]:
    """Random distinct edges without self-loops."""
    pairs = [(a, b) for a in range(n) for b in range(n) if a != b and (directed or a < b)]
    return [list(p) for p in r.sample(pairs, min(m, len(pairs)))]


def gen_valid_tree(r: random.Random) -> Args:
    """Half real trees, half random graphs."""
    n = r.randint(1, 7)
    if r.random() < 0.5:  # noqa: PLR2004
        return (n, [[r.randrange(i), i] for i in range(1, n)])
    return (n, gen_edges(r, n, r.randint(0, n)))


def gen_courses(r: random.Random) -> Args:
    """Random prerequisites (cycles possible)."""
    n = r.randint(1, 6)
    return (n, gen_edges(r, n, r.randint(0, 7), directed=True))


def gen_probability(r: random.Random) -> Args:
    """Random undirected weighted graph with probabilities."""
    n = r.randint(2, 6)
    edges = gen_edges(r, n, r.randint(0, 8))
    return (n, edges, [round(r.random(), 2) for _ in edges], 0, n - 1)


def gen_label_graph(r: random.Random) -> Args:
    """Random directed graph with node labels."""
    n = r.randint(1, 6)
    edges = [[a, b, r.randint(1, 9)] for a, b in gen_edges(r, n, r.randint(0, 10), directed=True)]
    return (n, edges, word(r, (n, n), "ab"), r.randint(1, 3))


def gen_safeness(r: random.Random) -> Args:
    """Square grid with at least one thief."""
    n = r.randint(1, 6)
    g = [[1 if r.random() < 0.2 else 0 for _ in range(n)] for _ in range(n)]  # noqa: PLR2004
    g[r.randrange(n)][r.randrange(n)] = 1
    return (g,)


def gen_schedule(r: random.Random) -> Args:
    """Each employee: sorted, non-overlapping busy intervals."""
    out = []
    for _ in range(r.randint(1, 4)):
        pts = sorted(r.sample(range(0, 30), 2 * r.randint(1, 3)))
        out.append([[pts[i], pts[i + 1]] for i in range(0, len(pts), 2)])
    return (out,)


def gen_range_module(r: random.Random) -> Args:
    """Random add/remove/query sequence."""
    ops, params = ["RangeModule"], [[]]
    for _ in range(r.randint(1, 15)):
        a = r.randint(1, 20)
        ops.append(r.choice(["addRange", "removeRange", "queryRange"]))
        params.append([a, a + r.randint(1, 8)])
    return (ops, params)


def gen_queue(r: random.Random) -> Args:
    """Random push/pop/peek/empty sequence that never pops an empty queue."""
    ops, params, size = ["MyQueue"], [[]], 0
    for _ in range(r.randint(1, 15)):
        op = (
            r.choice(["push", "push", "pop", "peek", "empty"])
            if size
            else r.choice(["push", "empty"])
        )
        ops.append(op)
        params.append([r.randint(1, 9)] if op == "push" else [])
        size += 1 if op == "push" else -1 if op == "pop" else 0
    return (ops, params)


def gen_logger(r: random.Random) -> Args:
    """Non-decreasing timestamps."""
    ops, params, t = ["Logger"], [[]], 0
    for _ in range(r.randint(1, 15)):
        t += r.randint(0, 6)
        ops.append("shouldPrintMessage")
        params.append([t, r.choice(["foo", "bar", "baz"])])
    return (ops, params)


def gen_perm(r: random.Random) -> Args:
    """Random permutation of 0..n-1."""
    p = list(range(r.randint(1, 8)))
    r.shuffle(p)
    return (p,)


def gen_str_chain(r: random.Random) -> Args:
    """Words over a tiny alphabet so chains exist."""
    return ([word(r, (1, 5), "ab") for _ in range(r.randint(1, 8))],)


def gen_rotated_blocks(r: random.Random) -> Args:
    """Sorted array, rotate random blocks, sometimes scramble."""
    n = r.choice([1, 2, 3, 4, 6, 8, 9, 12])
    a = sorted(r.randint(1, 6) for _ in range(n))
    k = r.choice([d for d in range(1, n + 1) if n % d == 0])
    for lo in range(0, n, k):
        s = r.randrange(k)
        a[lo : lo + k] = a[lo + s : lo + k] + a[lo : lo + s]
    if r.random() < 0.3:  # noqa: PLR2004
        r.shuffle(a)
    return (a,)


def gen_servers(r: random.Random) -> Args:
    """Random logs and queries (x < q)."""
    n, x = r.randint(1, 5), r.randint(1, 5)
    logs = [[r.randint(1, n), r.randint(1, 15)] for _ in range(r.randint(1, 8))]
    return (n, logs, x, [r.randint(x + 1, 18) for _ in range(r.randint(1, 5))])


def gen_same_tree(r: random.Random) -> Args:
    """Identical trees half the time."""
    t = tree(r, 3, (0, 1))
    return (t, t if r.random() < 0.5 else tree(r, 3, (0, 1)))  # noqa: PLR2004


def gen_merge_sorted_array(r: random.Random) -> Args:
    """nums1 = m sorted values + n zero slots; nums2 = n sorted values."""
    a, b = sorted_ints(r), sorted_ints(r)
    return (a + [0] * len(b), len(a), b, len(b))


def gen_single_number(r: random.Random) -> Args:
    """Every value twice except the first."""
    xs = r.sample(range(-20, 20), r.randint(1, 5))
    return (r.sample(xs + xs[1:], 2 * len(xs) - 1),)


def gen_bad_version(r: random.Random) -> Args:
    """Return n versions and a first bad one somewhere in 1..n."""
    n = r.randint(1, 100)
    return (n, r.randint(1, n))


def gen_find_duplicate(r: random.Random) -> Args:
    """1..n plus one repeated value, shuffled."""
    n = r.randint(1, 8)
    return (r.sample([*range(1, n + 1), r.randint(1, n)], n + 1),)


def gen_top_k(r: random.Random) -> Args:
    """Pick k no larger than the number of distinct values."""
    xs = ints(r, (1, 10), (0, 4))
    return (xs, r.randint(1, len(set(xs))))


def gen_split_array(r: random.Random) -> Args:
    """Pick k between 1 and len(nums)."""
    xs = ints(r, (1, 8), (0, 10))
    return (xs, r.randint(1, len(xs)))


def gen_koko(r: random.Random) -> Args:
    """Pick h at least the number of piles."""
    xs = ints(r, (1, 6), (1, 30))
    return (xs, r.randint(len(xs), 3 * len(xs)))


def gen_two_sum(r: random.Random) -> Args:
    """Plant exactly one answer."""
    nums = ints(r, (2, 8), (-20, 20))
    i, j = r.sample(range(len(nums)), 2)
    return (nums, nums[i] + nums[j])


def gen_can_change(r: random.Random) -> Args:
    """Two strings with the same pieces: target is a shuffle of start."""
    s = word(r, (1, 7), "LR__")
    t = list(s)
    r.shuffle(t)
    return (s, "".join(t) if r.random() < 0.7 else s)  # noqa: PLR2004


# ── the catalog ─────────────────────────────────────────────────────────────────────────────────

SPECS: dict[int, Spec] = {
    1: Spec(
        out=check_two_sum,
        cases=[([2, 7, 11, 15], 9), ([3, 2, 4], 6)],
        expect=[[0, 1], [1, 2]],
        gen=gen_two_sum,
    ),
    2: Spec(
        kinds=("ll", "ll"),
        out="ll",
        cases=[([2, 4, 3], [5, 6, 4]), ([9, 9, 9, 9], [9])],
        expect=[[7, 0, 8], [8, 0, 0, 0, 1]],
        gen=lambda r: (ints(r, (1, 6), (0, 9)), ints(r, (1, 6), (0, 9))),
    ),
    3: Spec(
        cases=[("abcabcbb",), ("bbbbb",), ("pwwkew",)],
        expect=[3, 1, 3],
        gen=lambda r: (word(r, (0, 12), "abcd"),),
    ),
    4: Spec(
        out="float",
        cases=[([1, 3], [2]), ([1, 2], [3, 4])],
        expect=[2.0, 2.5],
        gen=lambda r: (sorted_ints(r, (1, 6)), sorted_ints(r, (0, 6))),
    ),
    5: Spec(
        out=check_palindrome, cases=[("babad",), ("cbbd",)], gen=lambda r: (word(r, (1, 12), "ab"),)
    ),
    6: Spec(
        cases=[("PAYPALISHIRING", 3), ("PAYPALISHIRING", 4), ("A", 1)],
        expect=["PAHNAPLSIIGYIR", "PINALSIGYAHRPI", "A"],
        gen=lambda r: (word(r, (1, 15), "abcdef"), r.randint(1, 5)),
    ),
    8: Spec(
        cases=[
            ("42",),
            ("   -042",),
            ("1337c0d3",),
            ("0-1",),
            ("words and 987",),
            ("-91283472332",),
        ],
        expect=[42, -42, 1337, 0, 0, -2147483648],
        gen=lambda r: (word(r, (0, 12), " +-0129a"),),
        oracle=brute_atoi,
        bad_ref=(
            "regex r'\\u005Cd+' matches a literal backslash + d, so it returns 0 for every input"
        ),
    ),
    9: Spec(
        cases=[(121,), (-121,), (10,)],
        expect=[True, False, False],
        gen=lambda r: (
            r.choice([r.randint(-50, 50), r.randint(0, 10**6), int(str(r.randint(1, 999)) * 2)]),
        ),
    ),
    11: Spec(
        cases=[([1, 8, 6, 2, 5, 4, 8, 3, 7],)],
        expect=[49],
        gen=lambda r: (ints(r, (2, 10), (0, 10)),),
    ),
    13: Spec(
        cases=[("III",), ("LVIII",), ("MCMXCIV",)],
        expect=[3, 58, 1994],
        gen=lambda r: (roman(r.randint(1, 3999)),),
    ),
    14: Spec(
        cases=[(["flower", "flow", "flight"],), (["dog", "racecar", "car"],)],
        expect=["fl", ""],
        gen=lambda r: ([word(r, (0, 5), "ab") for _ in range(r.randint(1, 5))],),
    ),
    15: Spec(
        out="nested",
        cases=[([-1, 0, 1, 2, -1, -4],), ([0, 0, 0],)],
        expect=[[[-1, -1, 2], [-1, 0, 1]], [[0, 0, 0]]],
        gen=lambda r: (ints(r, (3, 10), (-5, 5)),),
    ),
    20: Spec(
        cases=[("()",), ("()[]{}",), ("(]",), ("([])",)],
        expect=[True, True, False, True],
        gen=lambda r: (word(r, (0, 8), "()[]{}"),),
    ),
    21: Spec(
        kinds=("ll", "ll"),
        out="ll",
        cases=[([1, 2, 4], [1, 3, 4])],
        expect=[[1, 1, 2, 3, 4, 4]],
        gen=lambda r: (sorted_ints(r), sorted_ints(r)),
    ),
    22: Spec(
        out="unordered",
        cases=[(3,), (1,)],
        expect=[["((()))", "(()())", "(())()", "()(())", "()()()"], ["()"]],
        gen=lambda r: (r.randint(1, 6),),
    ),
    23: Spec(
        kinds=("lls",),
        out="ll",
        cases=[([[1, 4, 5], [1, 3, 4], [2, 6]],), ([],), ([[]],)],
        expect=[[1, 1, 2, 3, 4, 4, 5, 6], [], []],
        gen=lambda r: ([sorted_ints(r) for _ in range(r.randint(0, 5))],),
        oracle=lambda lists: sorted(v for lst in lists for v in lst),
    ),
    30: Spec(
        out="unordered",
        cases=[
            ("barfoothefoobarman", ["foo", "bar"]),
            ("barfoofoobarthefoobarman", ["bar", "foo", "the"]),
        ],
        expect=[[0, 9], [6, 9, 12]],
        gen=lambda r: (
            word(r, (0, 14), "ab"),
            [word(r, (2, 2), "ab") for _ in range(r.randint(1, 3))],
        ),
    ),
    34: Spec(
        cases=[([5, 7, 7, 8, 8, 10], 8), ([5, 7, 7, 8, 8, 10], 6), ([], 0)],
        expect=[[3, 4], [-1, -1], [-1, -1]],
        gen=lambda r: (sorted_ints(r), r.randint(-5, 5)),
    ),
    41: Spec(
        cases=[([1, 2, 0],), ([3, 4, -1, 1],), ([7, 8, 9, 11, 12],)],
        expect=[3, 2, 1],
        gen=lambda r: (ints(r, (1, 9), (-2, 9)),),
    ),
    42: Spec(
        cases=[([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],)],
        expect=[6],
        gen=lambda r: (ints(r, (1, 12), (0, 6)),),
    ),
    49: Spec(
        out="nested",
        cases=[(["eat", "tea", "tan", "ate", "nat", "bat"],)],
        expect=[[["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]],
        gen=lambda r: ([word(r, (0, 3), "abc") for _ in range(r.randint(1, 8))],),
    ),
    50: Spec(
        out="float",
        cases=[(2.0, 10), (2.1, 3), (2.0, -2)],
        expect=[1024.0, 9.261, 0.25],
        gen=lambda r: (round(r.uniform(-2, 2), 2) or 1.5, r.randint(-8, 8)),
    ),
    53: Spec(
        cases=[([-2, 1, -3, 4, -1, 2, 1, -5, 4],), ([5, 4, -1, 7, 8],)],
        expect=[6, 23],
        gen=lambda r: (ints(r),),
    ),
    54: Spec(
        cases=[([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)],
        expect=[[1, 2, 3, 6, 9, 8, 7, 4, 5]],
        gen=lambda r: (
            [
                [r.randint(0, 9) for _ in range(c)]
                for c in [r.randint(1, 5)]
                for _ in range(r.randint(1, 5))
            ],
        ),
    ),
    56: Spec(
        kinds=("interval-list",),
        out="unordered",
        cases=[([[1, 3], [2, 6], [8, 10], [15, 18]],), ([[1, 4], [4, 5]],)],
        expect=[[[1, 6], [8, 10], [15, 18]], [[1, 5]]],
        gen=lambda r: ([[a, a + r.randint(0, 4)] for a in ints(r, (1, 7), (0, 15))],),
    ),
    69: Spec(cases=[(4,), (8,), (0,)], expect=[2, 2, 0], gen=lambda r: (r.randint(0, 10**6),)),
    70: Spec(cases=[(2,), (3,)], expect=[2, 3], gen=lambda r: (r.randint(1, 30),)),
    72: Spec(
        cases=[("horse", "ros"), ("intention", "execution")],
        expect=[3, 5],
        gen=lambda r: (word(r), word(r)),
    ),
    84: Spec(
        cases=[([2, 1, 5, 6, 2, 3],), ([2, 4],)],
        expect=[10, 4],
        gen=lambda r: (ints(r, (1, 10), (0, 8)),),
    ),
    88: Spec(
        out="arg0",
        cases=[([1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3), ([1], 1, [], 0), ([0], 0, [1], 1)],
        expect=[[1, 2, 2, 3, 5, 6], [1], [1]],
        gen=gen_merge_sorted_array,
        oracle=lambda nums1, m, nums2, n: sorted(nums1[:m] + nums2[:n]),
    ),
    100: Spec(
        kinds=("tree", "tree"),
        cases=[([1, 2, 3], [1, 2, 3]), ([1, 2], [1, None, 2])],
        expect=[True, False],
        gen=gen_same_tree,
    ),
    112: Spec(
        kinds=("tree", ""),
        cases=[([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22), ([1, 2, 3], 5)],
        expect=[True, False],
        gen=lambda r: (tree(r), r.randint(-6, 6)),
    ),
    118: Spec(
        cases=[(5,), (1,)],
        expect=[[[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]], [[1]]],
        gen=lambda r: (r.randint(1, 12),),
    ),
    121: Spec(
        cases=[([7, 1, 5, 3, 6, 4],), ([7, 6, 4, 3, 1],)],
        expect=[5, 0],
        gen=lambda r: (ints(r, (1, 10), (0, 20)),),
    ),
    128: Spec(
        cases=[([100, 4, 200, 1, 3, 2],), ([0, 3, 7, 2, 5, 8, 4, 6, 0, 1],)],
        expect=[4, 9],
        gen=lambda r: (ints(r, (0, 10)),),
    ),
    136: Spec(
        cases=[([2, 2, 1],), ([4, 1, 2, 1, 2],)],
        expect=[1, 4],
        gen=gen_single_number,
    ),
    175: Spec(cases=[("sql",)]),
    179: Spec(
        cases=[([10, 2],), ([3, 30, 34, 5, 9],), ([0, 0],)],
        expect=["210", "9534330", "0"],
        gen=lambda r: (ints(r, (1, 6), (0, 120)),),
    ),
    181: Spec(cases=[("sql",)]),
    200: Spec(
        cases=[([["1", "1", "0"], ["0", "1", "0"], ["1", "0", "1"]],)],
        expect=[3],
        gen=gen_islands_grid,
    ),
    202: Spec(cases=[(19,), (2,)], expect=[True, False], gen=lambda r: (r.randint(1, 10**5),)),
    207: Spec(cases=[(2, [[1, 0]]), (2, [[1, 0], [0, 1]])], expect=[True, False], gen=gen_courses),
    217: Spec(
        cases=[([1, 2, 3, 1],), ([1, 2, 3, 4],)],
        expect=[True, False],
        gen=lambda r: (ints(r, (1, 8), (0, 12)),),
    ),
    219: Spec(
        cases=[([1, 2, 3, 1], 3), ([1, 2, 3, 1, 2, 3], 2)],
        expect=[True, False],
        gen=lambda r: (ints(r, (1, 8), (0, 5)), r.randint(0, 4)),
    ),
    232: Spec(
        design=True,
        cases=[(["MyQueue", "push", "push", "peek", "pop", "empty"], [[], [1], [2], [], [], []])],
        expect=[[None, None, None, 1, 1, False]],
        gen=gen_queue,
    ),
    242: Spec(
        cases=[("anagram", "nagaram"), ("rat", "car")],
        expect=[True, False],
        gen=lambda r: (word(r, (0, 5)), word(r, (0, 5))),
    ),
    261: Spec(
        cases=[
            (5, [[0, 1], [0, 2], [0, 3], [1, 4]]),
            (5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]),
        ],
        expect=[True, False],
        gen=gen_valid_tree,
    ),
    278: Spec(
        kinds=("badversion",),
        cases=[(5, 4), (1, 1)],
        expect=[4, 1],
        gen=gen_bad_version,
    ),
    287: Spec(
        cases=[([1, 3, 4, 2, 2],), ([3, 1, 3, 4, 2],)],
        expect=[2, 3],
        gen=gen_find_duplicate,
    ),
    302: Spec(
        cases=[([["0", "0", "1", "0"], ["0", "1", "1", "0"], ["0", "1", "0", "0"]], 0, 2)],
        expect=[6],
        gen=gen_black_pixels,
    ),
    347: Spec(
        out=check_top_k,
        cases=[([1, 1, 1, 2, 2, 3], 2)],
        expect=[[1, 2]],
        gen=gen_top_k,
    ),
    349: Spec(
        out="unordered",
        cases=[([1, 2, 2, 1], [2, 2])],
        expect=[[2]],
        gen=lambda r: (ints(r, (0, 6), (0, 6)), ints(r, (0, 6), (0, 6))),
    ),
    354: Spec(
        cases=[([[5, 4], [6, 4], [6, 7], [2, 3]],)],
        expect=[3],
        gen=lambda r: ([[r.randint(1, 6), r.randint(1, 6)] for _ in range(r.randint(1, 8))],),
    ),
    359: Spec(
        design=True,
        cases=[
            (
                ["Logger"] + ["shouldPrintMessage"] * 6,
                [[], [1, "foo"], [2, "bar"], [3, "foo"], [8, "bar"], [10, "foo"], [11, "foo"]],
            )
        ],
        expect=[[None, True, True, False, False, False, True]],
        gen=gen_logger,
    ),
    383: Spec(
        cases=[("a", "b"), ("aa", "ab"), ("aa", "aab")],
        expect=[False, False, True],
        gen=lambda r: (word(r, (0, 4)), word(r, (0, 6))),
    ),
    387: Spec(
        cases=[("leetcode",), ("loveleetcode",), ("aabb",), ("z",), ("",)],
        expect=[0, 2, -1, 0, -1],
        gen=lambda r: (word(r, (0, 10), "abcd"),),
        oracle=lambda s: next((i for i, c in enumerate(s) if s.count(c) == 1), -1),
    ),
    410: Spec(
        cases=[([7, 2, 5, 10, 8], 2), ([1, 2, 3, 4, 5], 2)],
        expect=[18, 9],
        gen=gen_split_array,
    ),
    416: Spec(
        cases=[([1, 5, 11, 5],), ([1, 2, 3, 5],)],
        expect=[True, False],
        gen=lambda r: (ints(r, (1, 8), (1, 10)),),
    ),
    419: Spec(
        cases=[([["X", ".", ".", "X"], [".", ".", ".", "X"], [".", ".", ".", "X"]],)],
        expect=[2],
        gen=gen_battleships,
    ),
    462: Spec(
        cases=[([1, 2, 3],), ([1, 10, 2, 9],)],
        expect=[2, 16],
        gen=lambda r: (ints(r, (1, 9), (-10, 10)),),
    ),
    485: Spec(cases=[([1, 1, 0, 1, 1, 1],)], expect=[3], gen=lambda r: (ints(r, (1, 12), (0, 1)),)),
    509: Spec(cases=[(2,), (4,)], expect=[1, 3], gen=lambda r: (r.randint(0, 30),)),
    528: Spec(cases=[([1, 3],), ([1, 2, 3, 4],)]),
    547: Spec(cases=[([[1, 1, 0], [1, 1, 0], [0, 0, 1]],)], expect=[2], gen=gen_circle),
    560: Spec(
        cases=[([1, 1, 1], 2), ([1, 2, 3], 3)],
        expect=[2, 2],
        gen=lambda r: (ints(r, (1, 10), (-3, 3)), r.randint(-3, 3)),
    ),
    584: Spec(cases=[("sql",)]),
    621: Spec(
        cases=[(list("AAABBB"), 2), (list("ACABDB"), 1), (list("AAABBB"), 3)],
        expect=[8, 6, 10],
        gen=lambda r: (list(word(r, (1, 10), "ABCD")), r.randint(0, 4)),
    ),
    715: Spec(
        design=True,
        cases=[
            (
                [
                    "RangeModule",
                    "addRange",
                    "removeRange",
                    "queryRange",
                    "queryRange",
                    "queryRange",
                ],
                [[], [10, 20], [14, 16], [10, 14], [13, 15], [16, 17]],
            )
        ],
        expect=[[None, None, None, True, False, True]],
        gen=gen_range_module,
    ),
    739: Spec(
        cases=[([73, 74, 75, 71, 69, 72, 76, 73],)],
        expect=[[1, 1, 4, 2, 1, 1, 0, 0]],
        gen=lambda r: (ints(r, (1, 10), (30, 40)),),
    ),
    759: Spec(
        kinds=("intervals",),
        cases=[([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]],)],
        expect=[[[3, 4]]],
        gen=gen_schedule,
    ),
    772: Spec(
        cases=[("1+1",), ("6-4/2",), ("2*(5+5*2)/3+(6/2+8)",)],
        expect=[2, 4, 21],
        gen=lambda r: (expr(r),),
        oracle=brute_calc,
        bad_ref="floors negative division (-1/9 -> -1); the problem truncates toward zero",
    ),
    875: Spec(
        cases=[([3, 6, 7, 11], 8), ([30, 11, 23, 4, 20], 5)],
        expect=[4, 30],
        gen=gen_koko,
        oracle=brute_koko,
        bad_ref=(
            "returns the first speed whose hours == h, not the smallest"
            " ([20,13], h=3 -> 15, answer 13)"
        ),
    ),
    876: Spec(
        kinds=("ll",),
        out="ll",
        cases=[([1, 2, 3, 4, 5],), ([1, 2, 3, 4, 5, 6],)],
        expect=[[3, 4, 5], [4, 5, 6]],
        gen=lambda r: (ints(r, (1, 8)),),
    ),
    904: Spec(
        cases=[([1, 2, 1],), ([0, 1, 2, 2],), ([1, 2, 3, 2, 2],)],
        expect=[3, 3, 4],
        gen=lambda r: (ints(r, (1, 12), (0, 3)),),
    ),
    912: Spec(cases=[([5, 2, 3, 1],)], expect=[[1, 2, 3, 5]], gen=lambda r: (ints(r, (1, 12)),)),
    1044: Spec(
        out=check_dup_substring,
        cases=[("banana",), ("abcd",)],
        expect=["ana", ""],
        gen=lambda r: (word(r, (2, 14), "ab"),),
    ),
    1046: Spec(
        cases=[([2, 7, 4, 1, 8, 1],)], expect=[1], gen=lambda r: (ints(r, (1, 8), (1, 10)),)
    ),
    1048: Spec(
        cases=[(["a", "b", "ba", "bca", "bda", "bdca"],), (["abcd", "dbqca"],)],
        expect=[4, 1],
        gen=gen_str_chain,
    ),
    1143: Spec(
        cases=[("abcde", "ace"), ("abc", "def")],
        expect=[3, 0],
        gen=lambda r: (word(r, (1, 8)), word(r, (1, 8))),
    ),
    1218: Spec(
        cases=[([1, 2, 3, 4], 1), ([1, 5, 7, 8, 5, 3, 4, 2, 1], -2)],
        expect=[4, 4],
        gen=lambda r: (ints(r, (1, 10), (0, 6)), r.randint(-2, 2)),
    ),
    1405: Spec(
        out=check_happy,
        cases=[(1, 1, 7), (7, 1, 0)],
        gen=lambda r: (r.randint(0, 5), r.randint(0, 5), r.randint(0, 5)),
        oracle=brute_happy_len,
    ),
    1448: Spec(
        kinds=("tree",),
        cases=[([3, 1, 4, 3, None, 1, 5],), ([3, 3, None, 4, 2],)],
        expect=[4, 3],
        gen=lambda r: (tree(r),),
        oracle=brute_good_nodes,
    ),
    1480: Spec(
        cases=[([1, 2, 3, 4],), ([3, 1, 2, 10, 1],)],
        expect=[[1, 3, 6, 10], [3, 4, 6, 16, 17]],
        gen=lambda r: (ints(r),),
        oracle=lambda nums: list(itertools.accumulate(nums)),
    ),
    1514: Spec(
        out="float",
        cases=[(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2), (3, [[0, 1]], [0.5], 0, 2)],
        expect=[0.25, 0.0],
        gen=gen_probability,
        oracle=brute_max_probability,
    ),
    1757: Spec(cases=[("sql",)]),
    1911: Spec(
        cases=[([4, 2, 5, 3],), ([5, 6, 7, 8],), ([6, 2, 1, 2, 4, 5],)],
        expect=[7, 8, 10],
        gen=lambda r: (ints(r, (1, 9), (1, 9)),),
        oracle=brute_alternating,
    ),
    1922: Spec(
        cases=[(1,), (4,), (50,)],
        expect=[5, 400, 564908303],
        gen=lambda r: (r.randint(1, 4),),
        oracle=brute_good_numbers,
    ),
    1929: Spec(
        cases=[([1, 2, 1],)],
        expect=[[1, 2, 1, 1, 2, 1]],
        gen=lambda r: (ints(r),),
        oracle=lambda nums: [nums[i % len(nums)] for i in range(2 * len(nums))],
    ),
    1944: Spec(
        cases=[([10, 6, 8, 5, 11, 9],), ([5, 1, 2, 3, 10],)],
        expect=[[3, 1, 2, 1, 1, 0], [4, 1, 1, 1, 0]],
        gen=lambda r: (r.sample(range(1, 30), r.randint(1, 9)),),
        oracle=brute_visible,
    ),
    2089: Spec(
        cases=[([1, 2, 5, 2, 3], 2), ([1, 2, 5, 2, 3], 5), ([1, 2, 5, 2, 3], 4)],
        expect=[[1, 2], [4], []],
        gen=lambda r: (ints(r, (1, 9), (0, 5)), r.randint(0, 5)),
        oracle=lambda nums, t: [i for i, x in enumerate(sorted(nums)) if x == t],
    ),
    2235: Spec(
        cases=[(12, 5), (-10, 4)],
        expect=[17, -6],
        gen=lambda r: (r.randint(-100, 100), r.randint(-100, 100)),
        oracle=lambda a, b: a + b,
    ),
    2337: Spec(
        cases=[("_L__R__R_", "L______RR"), ("R_L_", "__LR"), ("_R", "R_")],
        expect=[True, False, False],
        gen=gen_can_change,
        oracle=brute_can_change,
    ),
    2747: Spec(
        cases=[
            (3, [[1, 3], [2, 6], [1, 5]], 5, [10, 11]),
            (3, [[2, 4], [2, 1], [1, 2], [3, 1]], 2, [3, 4]),
        ],
        expect=[[1, 2], [0, 1]],
        gen=gen_servers,
        oracle=brute_count_servers,
    ),
    2812: Spec(
        cases=[
            ([[1, 0, 0], [0, 0, 0], [0, 0, 1]],),
            ([[0, 0, 1], [0, 0, 0], [0, 0, 0]],),
            ([[0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0]],),
        ],
        expect=[0, 2, 2],
        gen=gen_safeness,
        oracle=brute_safeness,
    ),
    2913: Spec(
        cases=[([1, 2, 1],), ([1, 1],)],
        expect=[15, 3],
        gen=lambda r: (ints(r, (1, 8), (1, 4)),),
        oracle=brute_sum_counts,
    ),
    3026: Spec(
        cases=[([1, 2, 3, 4, 5, 6], 1), ([-1, 3, 2, 4, 5], 3), ([-1, -2, -3, -4], 2)],
        expect=[11, 11, -6],
        gen=lambda r: (ints(r, (2, 9), (-6, 6)), r.randint(1, 4)),
        oracle=brute_good_subarray,
    ),
    3644: Spec(
        cases=[([0, 3, 2, 1],), ([0, 1, 3, 2],), ([3, 2, 1, 0],)],
        expect=[1, 2, 0],
        gen=gen_perm,
        oracle=brute_sort_permutation,
    ),
    3736: Spec(
        cases=[([2, 1, 3],), ([4, 4, 5],)],
        expect=[3, 2],
        gen=lambda r: (ints(r, (1, 8), (1, 20)),),
        oracle=lambda nums: len(nums) * max(nums) - sum(nums),
    ),
    3749: Spec(
        cases=[("add(2,3)",), ("-42",), ("div(mul(4,sub(9,5)),add(1,1))",)],
        expect=[5, -42, 8],
        gen=lambda r: (fexpr(r)[0],),
        oracle=brute_eval,
    ),
    3863: Spec(
        cases=[("dog",), ("card",), ("gf",)],
        expect=[1, 2, -1],
        gen=lambda r: (word(r, (1, 6), "abc"),),
        oracle=brute_min_ops_sort,
    ),
    3886: Spec(
        cases=[([3, 1, 2],), ([7, 6, 5],), ([5, 8],)],
        expect=[3, 0, 3],
        gen=gen_rotated_blocks,
        oracle=brute_sortable,
    ),
    3970: Spec(
        cases=[
            (3, [[0, 1, 1], [1, 2, 1], [0, 2, 3]], "aab", 1),
            (3, [[0, 1, 1], [1, 2, 1], [0, 2, 3]], "aab", 2),
            (3, [[0, 1, 1], [1, 2, 1]], "aaa", 2),
        ],
        expect=[3, 2, -1],
        gen=gen_label_graph,
        oracle=brute_shortest_path,
    ),
}


# SQL fixtures: (schema + rows, expected rows as a sorted list of tuples)
SQL_FIXTURES: dict[int, tuple[str, list[tuple[Any, ...]]]] = {
    175: (
        """CREATE TABLE Person (personId INT, lastName TEXT, firstName TEXT);
             CREATE TABLE Address (addressId INT, personId INT, city TEXT, state TEXT);
             INSERT INTO Person VALUES (1,'Wang','Allen'),(2,'Alice','Bob');
             INSERT INTO Address VALUES (1,2,'New York City','New York'),
                                        (2,3,'Leetcode','California');""",
        [("Allen", "Wang", None, None), ("Bob", "Alice", "New York City", "New York")],
    ),
    181: (
        """CREATE TABLE Employee (id INT, name TEXT, salary INT, managerId INT);
             INSERT INTO Employee VALUES (1,'Joe',70000,3),(2,'Henry',80000,4),
                                         (3,'Sam',60000,NULL),(4,'Max',90000,NULL);""",
        [("Joe",)],
    ),
    584: (
        """CREATE TABLE Customer (id INT, name TEXT, referee_id INT);
             INSERT INTO Customer VALUES (1,'Will',NULL),(2,'Jane',NULL),(3,'Alex',2),
                                         (4,'Bill',NULL),(5,'Zack',1),(6,'Mark',2);""",
        [("Bill",), ("Jane",), ("Will",), ("Zack",)],
    ),
    1757: (
        """CREATE TABLE Products (product_id INT, low_fats TEXT, recyclable TEXT);
              INSERT INTO Products VALUES (0,'Y','N'),(1,'Y','Y'),(2,'N','Y'),
                                          (3,'Y','Y'),(4,'N','N');""",
        [(1,), (3,)],
    ),
}
