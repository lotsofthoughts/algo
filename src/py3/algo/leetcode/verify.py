"""Differential tester: our solutions vs cnkyrpsgl/leetcode, brute-force oracles, and examples.

    python3 -m algo.leetcode.verify --ref ~/.cache/algo/leetcode-ref [--n 300] [--seed 7] [ids...]
    algo verify [ids...] [--fetch]   # same, via the CLI; --fetch clones the reference if missing

For each problem: the LeetCode examples are checked against `expect`; then hand cases plus `--n`
random cases are run through our solution and through the reference solution (when the repo has
it) or the brute-force `oracle` (when it doesn't). Exit status 1 if anything disagrees.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import copy
import functools
import heapq
import itertools
import json
import math
import pathlib
import random
import re
import sqlite3
import string
import sys
import typing
from typing import TYPE_CHECKING, Any

from algo.leetcode import solutions
from algo.leetcode.catalog import SPECS, SQL_FIXTURES, Args, Spec

if TYPE_CHECKING:
    from collections.abc import Callable

from algo.leetcode.structures import (
    Interval,
    ListNode,
    TreeNode,
    from_list_node,
    to_list_node,
    to_tree,
)

REF_URL = "https://github.com/cnkyrpsgl/leetcode"
DEFAULT_REF = pathlib.Path.home() / ".cache" / "algo" / "leetcode-ref"


# ── loading reference solutions ─────────────────────────────────────────────────────────────────


def ref_namespace() -> dict[str, Any]:
    """Names LeetCode pre-imports for Python solutions."""
    ns: dict[str, Any] = {
        name: getattr(typing, name) for name in ("List", "Optional", "Dict", "Tuple", "Set")
    }
    for mod in (bisect, collections, heapq, itertools, functools, math, random, re, string):
        ns[mod.__name__] = mod
    ns.update(
        defaultdict=collections.defaultdict,
        Counter=collections.Counter,
        deque=collections.deque,
        heappush=heapq.heappush,
        heappop=heapq.heappop,
        heapify=heapq.heapify,
        ListNode=ListNode,
        TreeNode=TreeNode,
        Interval=Interval,
        lru_cache=functools.lru_cache,
        inf=math.inf,
    )
    return ns


def load_ref(ref_dir: pathlib.Path, pid: int) -> dict[str, Any] | None:
    """Exec the reference file for `pid` into a fresh namespace (None if the repo lacks it)."""
    path = ref_dir / "solutions" / "python3" / f"{pid}.py"
    if not path.is_file():
        return None
    ns = ref_namespace()
    # Running the user-chosen reference repo's solutions is the point of this tool.
    exec(compile(path.read_text(), str(path), "exec"), ns)  # noqa: S102  # nosec B102
    return ns


def ref_method(ns: dict[str, Any]) -> Callable[..., Any]:
    """The public entry method of `class Solution` (first non-underscore def)."""
    cls = ns["Solution"]
    name = next(k for k, v in vars(cls).items() if callable(v) and not k.startswith("_"))
    return getattr(cls(), name)


# ── calling and comparing ───────────────────────────────────────────────────────────────────────


def prepare(args: Args, spec: Spec, for_ref: bool) -> Args:
    """Deep-copy args and convert list/tree/interval arguments."""
    out = []
    for i, a in enumerate(copy.deepcopy(args)):
        kind = spec.kinds[i] if i < len(spec.kinds) else ""
        if kind == "ll":
            a = to_list_node(a)  # noqa: PLW2901
        elif kind == "lls":
            a = [to_list_node(x) for x in a]  # noqa: PLW2901
        elif kind == "tree":
            a = to_tree(a)  # noqa: PLW2901
        elif kind == "intervals" and for_ref:
            a = [[Interval(s, e) for s, e in emp] for emp in a]  # noqa: PLW2901
        elif kind == "interval-list" and for_ref:
            a = [Interval(s, e) for s, e in a]  # noqa: PLW2901
        out.append(a)
    return tuple(out)


def run_design(
    cls_by_name: Callable[[str], type], ops: list[str], params: list[list[Any]]
) -> list[Any]:
    """Replay a LeetCode design-problem transcript."""
    obj = cls_by_name(ops[0])(*params[0])
    return [None] + [getattr(obj, op)(*p) for op, p in zip(ops[1:], params[1:], strict=True)]


def _result(spec: Spec, fn: Callable[..., Any], args: Args) -> Any:
    """Call fn; normalise linked-list output, or return args[0] for in-place problems (88)."""
    out = fn(*args)
    if spec.out == "arg0":
        return args[0]
    return from_list_node(out) if spec.out == "ll" else out


def call_ours(pid: int, spec: Spec, args: Args) -> Any:
    """Run our solution on args, normalising linked-list output."""
    fn = solutions.by_id()[pid]
    if spec.design:
        return run_design(lambda _name: fn, *copy.deepcopy(args))
    if spec.kinds[:1] == ("badversion",):
        n, bad = args
        return fn(n, lambda v: v >= bad)
    return _result(spec, fn, prepare(args, spec, for_ref=False))


def call_ref(ns: dict[str, Any], spec: Spec, args: Args) -> Any:
    """Run the reference solution on args."""
    if spec.design:
        return run_design(lambda name: ns[name], *copy.deepcopy(args))
    if spec.kinds[:1] == ("badversion",):
        n, bad = args
        ns["isBadVersion"] = lambda v: v >= bad
        return ref_method(ns)(n)
    return _result(spec, ref_method(ns), prepare(args, spec, for_ref=True))


def same(spec: Spec, args: Args, a: Any, b: Any) -> bool:
    """Compare two outputs under the spec's comparator."""
    if not isinstance(spec.out, str):
        return bool(spec.out(args, a, b))
    if spec.out == "float":
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5)
    if spec.out == "unordered":
        return sorted(map(repr, a)) == sorted(map(repr, b))
    if spec.out == "nested":
        return sorted(sorted(map(repr, x)) for x in a) == sorted(sorted(map(repr, x)) for x in b)
    return a == b


# ── per-problem drivers ─────────────────────────────────────────────────────────────────────────


def verify_sql(pid: int) -> tuple[str, int, list[str]]:
    """Run the SQL answer against the LeetCode example tables on sqlite."""
    schema, want = SQL_FIXTURES[pid]
    db = sqlite3.connect(":memory:")
    db.executescript(schema)
    got = sorted(db.execute(solutions.SQL[pid]).fetchall(), key=repr)
    return "sqlite", 1, [] if got == sorted(want, key=repr) else [f"got {got}, want {want}"]


def verify_weighted(pid: int) -> tuple[str, int, list[str]]:
    """528 is random: check the empirical distribution of 20k picks per case."""
    fails = []
    for (w,) in SPECS[pid].cases:
        picker = solutions.WeightedPicker(w, random.Random(1))  # noqa: S311
        hits = collections.Counter(picker.pickIndex() for _ in range(20000))
        for i, wi in enumerate(w):
            if abs(hits[i] / 20000 - wi / sum(w)) > 0.02:  # noqa: PLR2004
                fails.append(
                    f"w={w}: index {i} picked {hits[i] / 20000:.3f}, want {wi / sum(w):.3f}"
                )
    return "distribution", len(SPECS[pid].cases), fails


def check_examples(pid: int, spec: Spec) -> list[str]:
    """Compare our answers with the expected outputs of the LeetCode examples."""
    fails = []
    for args, want in zip(spec.cases, spec.expect, strict=False):
        got = call_ours(pid, spec, args)
        if not same(spec, args, got, want):
            fails.append(f"example {args!r}: got {got!r}, want {want!r}")
    return fails


def pick_other(spec: Spec, ns: dict[str, Any] | None) -> tuple[str, Callable[[Args], Any] | None]:
    """What to compare against: the reference solution, else the brute-force oracle."""
    if ns is not None:
        return "reference", lambda a: call_ref(ns, spec, a)
    oracle = spec.oracle
    if oracle is None:
        return "examples", None
    source = "brute force*" if spec.bad_ref else "brute force"
    return source, lambda a: oracle(*copy.deepcopy(a))


def verify_one(pid: int, ref_dir: pathlib.Path, n: int, seed: int) -> tuple[str, int, list[str]]:
    """Return (compared-against, cases run, failure messages)."""
    if pid in solutions.SQL:
        return verify_sql(pid)
    if pid == 528:  # noqa: PLR2004
        return verify_weighted(pid)
    spec = SPECS[pid]
    fails = check_examples(pid, spec)
    ns = None if spec.bad_ref else load_ref(ref_dir, pid)
    source, other = pick_other(spec, ns)
    if other is None:
        return source, len(spec.expect), fails
    rng = random.Random(f"{seed}-{pid}")  # noqa: S311
    # Hand cases go to the reference too; a brute force only sees the small random ones.
    hand = list(spec.cases) if ns is not None else list(spec.cases[len(spec.expect) :])
    batch = hand + ([spec.gen(rng) for _ in range(n)] if spec.gen else [])
    for args in batch:
        ours = call_ours(pid, spec, args)
        try:
            theirs = other(args)
        except Exception as e:
            fails.append(f"{source} raised {type(e).__name__}: {e} on {args!r}")
            continue
        if not same(spec, args, ours, theirs):
            fails.append(f"{args!r}: ours {ours!r}, {source} {theirs!r}")
    return source, len(spec.expect) + len(batch), fails


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("ids", nargs="*", type=int, help="problem ids (default: all 99)")
    ap.add_argument(
        "--ref", type=pathlib.Path, default=DEFAULT_REF, help="clone of cnkyrpsgl/leetcode"
    )
    ap.add_argument("-n", "--n", type=int, default=300, help="random cases per problem")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("-j", "--json", action="store_true")
    ap.add_argument(
        "-v", "--verbose", action="store_true", help="print every failure, not just the first 3"
    )
    a = ap.parse_args(argv)
    if not (a.ref / "solutions" / "python3").is_dir():
        print(
            f"reference repo not found at {a.ref}: "
            f"run `algo verify --fetch` or git clone {REF_URL} {a.ref}",
            file=sys.stderr,
        )
        return 2
    rows, bad = [], 0
    for pid in a.ids or sorted(SPECS):
        try:
            source, count, fails = verify_one(pid, a.ref, a.n, a.seed)
        except Exception as e:
            source, count, fails = "error", 0, [f"{type(e).__name__}: {e}"]
        bad += bool(fails)
        rows.append(
            {"id": pid, "against": source, "cases": count, "ok": not fails, "failures": fails}
        )
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            mark = "ok  " if r["ok"] else "FAIL"
            print(f"{mark} {r['id']:>5}  {r['against']:<12} {r['cases']:>4} cases")
            if SPECS.get(r["id"]) and SPECS[r["id"]].bad_ref:
                print(f"        * reference repo is wrong here: {SPECS[r['id']].bad_ref}")
            for f in r["failures"][: None if a.verbose else 3]:
                print(f"        {f[:300]}")
        by = collections.Counter(r["against"] for r in rows)
        print(
            f"{len(rows) - bad}/{len(rows)} passed  ("
            + ", ".join(f"{v} vs {k}" for k, v in sorted(by.items()))
            + ")"
        )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
