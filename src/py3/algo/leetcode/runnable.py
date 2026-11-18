"""Make every per-problem solution runnable through `algo generate / inputs / run / pipe`.

Each solved problem N becomes a target `lc-N`. Its input schema is derived from the solution's
signature: parameter names become fields and annotation strings map to shorthand types
(`list[int]` -> ints, `list[list[int]]` -> igrid, `ListNode | None` -> ll, ...). The sample input
is the first hand case in algo.leetcode.catalog. A few shapes need adapters:

    design classes (232, 359, 715)  fields ops, params      LeetCode's ["Cls", "op", ...] transcript
    528 Random Pick with Weight     fields w, picks, seed   returns `picks` seeded draws
    278 First Bad Version           fields n, bad           builds isBadVersion = v >= bad
    SQL (175, 181, 584, 1757)       field query             runs on the example tables in sqlite

The helpers below (`_invoke`, `_replay`, ...) are also copied verbatim into generated libraries,
so `algo r lc-N` and `python3 <lib>.py` execute the same code.
"""

from __future__ import annotations

import inspect
import types
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from algo.leetcode import solutions, structures
from algo.leetcode.catalog import SPECS, SQL_FIXTURES
from algo.leetcode.structures import from_list_node, to_list_node, to_tree

# Annotation string -> shorthand type (see algo.shorthand). Unknown annotations fall back to "any".
TYPE_MAP = {
    "int": "int",
    "str": "str",
    "float": "any",
    "bool": "any",
    "list[int]": "ints",
    "list[str]": "strs",
    "list[float]": "floats",
    "list[list[int]]": "igrid",
    "list[list[str]]": "cgrid",
    "ListNode | None": "ll",
    "list[ListNode | None]": "lls",
    "TreeNode | None": "tree",
}
DESIGN_SCHEMA = {"ops": "any", "params": "any"}


@dataclass(frozen=True)
class ProblemTarget:
    """One runnable per-problem solution."""

    pid: int
    title: str
    obj_name: str  # function / class name in algo.leetcode.solutions, or "SQL"
    kind: str  # function | design | weighted | badversion | sql
    schema: dict[str, str] = field(default_factory=dict)
    out: str = ""  # "ll" when the result is a linked list

    @property
    def key(self) -> str:
        """Target key used by the CLI: lc-<id>."""
        return f"lc-{self.pid}"

    @property
    def lib(self) -> str:
        """Library file stem for `algo g`, e.g. lc875_min_eating_speed."""
        return self.obj_name.lower() if self.kind != "sql" else f"lc{self.pid}_sql"


# ── adapters (copied into generated libraries; keep them self-contained) ────────────────────────


def _invoke(fn: Any, data: dict, kinds: dict[str, str], out: str) -> Any:
    """Call fn with data's fields in schema order, converting ll/lls/tree fields and the output.

    out "ll" turns a returned list node into a list; "arg0" (in-place problems such as 88)
    returns the first argument after the call instead of fn's None.
    """
    args = []
    for name, kind in kinds.items():
        value = data[name]
        if kind == "ll":
            value = to_list_node(value)
        elif kind == "lls":
            value = [to_list_node(v) for v in value]
        elif kind == "tree":
            value = to_tree(value)
        args.append(value)
    result = fn(*args)
    if out == "arg0":
        return args[0]
    return from_list_node(result) if out == "ll" else result


def _replay(cls: Any, ops: list[str], params: list[list[Any]]) -> list[Any]:
    """Run a LeetCode design transcript: construct with params[0], then call each op."""
    obj = cls(*params[0])
    return [None] + [getattr(obj, op)(*p) for op, p in zip(ops[1:], params[1:], strict=True)]


def _picks(cls: Any, w: list[int], picks: int, seed: int) -> list[int]:
    """Draw `picks` indices from a weighted picker seeded with `seed` (reproducible)."""
    import random

    picker = cls(w, random.Random(seed))  # noqa: S311 - reproducible demo draws
    return [picker.pickIndex() for _ in range(picks)]


def _bad_version(fn: Any, n: int, bad: int) -> int:
    """Call first-bad-version with an isBadVersion predicate whose first bad version is `bad`."""
    return fn(n, lambda v: v >= bad)


def _sql(query: str, fixture: str) -> list[list[Any]]:
    """Run query against the fixture tables in an in-memory sqlite database."""
    import sqlite3

    db = sqlite3.connect(":memory:")
    db.executescript(fixture)
    return [list(row) for row in db.execute(query).fetchall()]


ADAPTERS = [_invoke, _replay, _picks, _bad_version, _sql]


# ── target table ────────────────────────────────────────────────────────────────────────────────


def _titles() -> dict[int, str]:
    from algo.registry import load_problems

    return {p["id"]: p["title"] for p in load_problems()}


def _target(pid: int, obj: Any, title: str) -> ProblemTarget:
    if isinstance(obj, str):
        return ProblemTarget(pid, title, "SQL", "sql", {"query": "str"})
    if inspect.isclass(obj):
        if pid == 528:  # noqa: PLR2004
            return ProblemTarget(
                pid, title, obj.__name__, "weighted", {"w": "ints", "picks": "int", "seed": "int"}
            )
        return ProblemTarget(pid, title, obj.__name__, "design", dict(DESIGN_SCHEMA))
    sig = inspect.signature(obj)
    if any(str(p.annotation).startswith("Callable") for p in sig.parameters.values()):
        return ProblemTarget(pid, title, obj.__name__, "badversion", {"n": "int", "bad": "int"})
    schema = {name: TYPE_MAP.get(str(p.annotation), "any") for name, p in sig.parameters.items()}
    ret = str(sig.return_annotation)
    out = {"ListNode | None": "ll", "None": "arg0"}.get(ret, "")  # arg0: in place, show args[0]
    return ProblemTarget(pid, title, obj.__name__, "function", schema, out)


@lru_cache(maxsize=1)
def targets() -> dict[str, ProblemTarget]:
    """All runnable problem targets, keyed lc-<id>."""
    titles = _titles()
    out = {}
    for pid, obj in sorted(solutions.by_id().items()):
        t = _target(pid, obj, titles.get(pid, f"Problem {pid}"))
        out[t.key] = t
    return out


def get(key: str) -> ProblemTarget | None:
    """Target for lc-<id>, or None."""
    return targets().get(key)


def sample(key: str) -> dict[str, Any]:
    """Sample input dict: the first catalog hand case, mapped onto the schema's fields."""
    t = targets()[key]
    if t.kind == "sql":
        return {"query": solutions.SQL[t.pid]}
    if t.kind == "weighted":
        return {"w": SPECS[t.pid].cases[0][0], "picks": 10, "seed": 1}
    case = SPECS[t.pid].cases[0]
    return dict(zip(t.schema, case, strict=True))


def expected(key: str) -> Any:
    """Expected output for the sample, when the catalog has one (else None)."""
    t = targets()[key]
    if t.kind == "sql":
        return [list(r) for r in SQL_FIXTURES[t.pid][1]]
    spec = SPECS[t.pid]
    return spec.expect[0] if spec.expect and t.kind != "weighted" else None


def run(key: str, data: dict[str, Any]) -> Any:
    """Run a problem target in-process on an input dict."""
    t = targets()[key]
    if t.kind == "sql":
        return _sql(data["query"], SQL_FIXTURES[t.pid][0])
    obj = solutions.by_id()[t.pid]
    if t.kind == "design":
        return _replay(obj, data["ops"], data["params"])
    if t.kind == "weighted":
        return _picks(obj, data["w"], data["picks"], data["seed"])
    if t.kind == "badversion":
        return _bad_version(obj, data["n"], data["bad"])
    return _invoke(obj, data, t.schema, t.out)


def matches_expected(key: str, got: Any) -> bool:
    """Compare a sample result with the expected one using the problem's own comparator."""
    from algo.leetcode.verify import same

    t = targets()[key]
    want = expected(key)
    if want is None:
        return True
    if t.kind == "sql":
        return sorted(map(repr, got)) == sorted(map(repr, want))
    return same(SPECS[t.pid], SPECS[t.pid].cases[0], got, want)


# ── standalone library source ───────────────────────────────────────────────────────────────────

LIB_IMPORTS = (
    "from __future__ import annotations\n"
    "import bisect, heapq, json, random, sqlite3, sys\n"
    "from collections import Counter, defaultdict, deque\n"
    "from functools import cmp_to_key, lru_cache\n"
    "from typing import Any\n"
)
STRUCTURES = [
    structures.ListNode,
    structures.TreeNode,
    structures.to_list_node,
    structures.from_list_node,
    structures.to_tree,
]


def _code_names(code: types.CodeType) -> set[str]:
    names = set(code.co_names)
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            names |= _code_names(const)
    return names


def _referenced(obj: Any) -> set[str]:
    """Global names a function or class body refers to."""
    if inspect.isclass(obj):
        names: set[str] = set()
        for member in vars(obj).values():
            fn = getattr(member, "__func__", member)
            if inspect.isfunction(fn):
                names |= _code_names(fn.__code__)
        return names
    return _code_names(obj.__code__)


def _dependencies(obj: Any) -> list[Any]:
    """Helpers and constants from algo.leetcode.solutions that obj needs, dependencies first."""
    module = vars(solutions)
    seen: dict[str, Any] = {}

    def visit(o: Any) -> None:
        for name in sorted(_referenced(o)):
            if name in seen or name not in module:
                continue
            value = module[name]
            local = getattr(value, "__module__", None) == solutions.__name__
            if (inspect.isfunction(value) or inspect.isclass(value)) and local and value is not obj:
                seen[name] = value
                visit(value)
                seen[name] = seen.pop(name)  # move after its own dependencies
            elif name.isupper() and isinstance(value, (int, float, str)):
                seen[name] = value

    visit(obj)
    return list(seen.items())


def library_source(key: str, title_line: str, path: str) -> str:
    """Source of a standalone, importable library for a problem target (stdlib only)."""
    t = targets()[key]
    stem = path.rsplit("/", 1)[-1].removesuffix(".py")
    parts = [inspect.getsource(o) for o in STRUCTURES]
    if t.kind == "sql":
        fixture = SQL_FIXTURES[t.pid][0]
        parts.append(f"SQL = {solutions.SQL[t.pid]!r}\n\nFIXTURE = {fixture!r}")
        call = "_sql(data['query'], FIXTURE)"
    else:
        obj = solutions.by_id()[t.pid]
        for name, dep in _dependencies(obj):
            parts.append(f"{name} = {dep!r}" if not callable(dep) else inspect.getsource(dep))
        parts.append(inspect.getsource(obj))
        calls = {
            "design": f"_replay({t.obj_name}, data['ops'], data['params'])",
            "weighted": f"_picks({t.obj_name}, data['w'], data['picks'], data['seed'])",
            "badversion": f"_bad_version({t.obj_name}, data['n'], data['bad'])",
            "function": f"_invoke({t.obj_name}, data, KINDS, {t.out!r})",
        }
        call = calls[t.kind]
    parts += [inspect.getsource(a) for a in ADAPTERS]
    return (
        f'"""{title_line}\n'
        f"Import:  from {stem} import solve      solve({{...}}) -> result\n"
        f'Run:     python3 {path} [input.json]        (default: sample below)\n"""\n'
        + LIB_IMPORTS
        + "\n\n"
        + "\n\n".join(p.rstrip() + "\n" for p in parts)
        + f"\nKINDS = {t.schema!r}\n\n\n"
        "def solve(data: dict) -> Any:\n"
        f'    """Run {t.key} ({t.title}) on an input dict with fields {", ".join(t.schema)}."""\n'
        f"    return {call}\n\n\n"
        f"SAMPLE = {sample(key)!r}\n\n"  # a Python literal: samples may hold None
        'if __name__ == "__main__":\n'
        "    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else SAMPLE\n"
        "    print(json.dumps(solve(data), default=repr))\n"
    )


__all__ = ["ProblemTarget", "expected", "get", "library_source", "run", "sample", "targets"]
