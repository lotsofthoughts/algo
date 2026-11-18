#!/usr/bin/env python3
"""The `algo` command: find, judge, generate, run and verify algorithms.

Subcommands (full spec in docs/API.md §2):

    problems (p)   problem title / number / keywords / use case -> algorithms
    search   (s)   algorithms by name, identification phrase or disqualifier
    generate (g)   write the importable library <id>.py (`-p` prints it instead)
    inputs   (i)   write inputs.py that calls the library on shorthand values
                   (files go to -o DIR, else $ALGO_TMP, else the current directory)
    run      (r)   run in-process; chain stages with `then`, `_` = previous output
                   (targets: an algorithm, a solver key, or a problem: 875 / lc-875 / "koko")
    shapes   (sh)  input fields per algorithm; `algo sh sort` filters, `algo sh 875` = one target
    uses     (u)   common real-world uses per algorithm; `algo u <need>` -> algorithm + problems
    pipe / assert / judge / targets   JSON in -> JSON out, compare, judge samples
    verify         differential-test the per-problem solutions (algo.leetcode.verify)
    check          cross-validate registry, problems, solvers, schemas and cases

Data lives in registry/*.yml (parsed with small regex loaders, no PyYAML) and solvers in
algo.solutions. Stdlib only, so it runs from the offline installer (scripts/algopack.py).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import TYPE_CHECKING, Any, NoReturn

from algo.judge.comparators import COMPARATORS
from algo.solutions import SOLVERS

if TYPE_CHECKING:
    from collections.abc import Callable

    from algo.leetcode.runnable import ProblemTarget

Item = dict[str, Any]  # a registry entry or a problem row

ROOT = pathlib.Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "registry" / "algorithms.yml"
PROBLEMS = ROOT / "registry" / "problems.yml"
TARGETS = {
    "leetcode-1": (
        "unordered-array",
        ROOT / "cases/leetcode-1/case-1.input.json",
        ROOT / "cases/leetcode-1/case-1.expected.json",
    ),
    "leetcode-200": (
        "number",
        ROOT / "cases/leetcode-200/case-1.input.json",
        ROOT / "cases/leetcode-200/case-1.expected.json",
    ),
    "leetcode-994": (
        "number",
        ROOT / "cases/leetcode-994/case-1.input.json",
        ROOT / "cases/leetcode-994/case-1.expected.json",
    ),
    "leetcode-33": (
        "number",
        ROOT / "cases/leetcode-33/case-1.input.json",
        ROOT / "cases/leetcode-33/case-1.expected.json",
    ),
    "leetcode-3": (
        "number",
        ROOT / "cases/leetcode-3/case-1.input.json",
        ROOT / "cases/leetcode-3/case-1.expected.json",
    ),
    "leetcode-210": (
        "topo-order",
        ROOT / "cases/leetcode-210/case-1.input.json",
        ROOT / "cases/leetcode-210/case-1.expected.json",
    ),
    "leetcode-684": (
        "exact",
        ROOT / "cases/leetcode-684/case-1.input.json",
        ROOT / "cases/leetcode-684/case-1.expected.json",
    ),
    "leetcode-743": (
        "number",
        ROOT / "cases/leetcode-743/case-1.input.json",
        ROOT / "cases/leetcode-743/case-1.expected.json",
    ),
    "leetcode-347": (
        "unordered-array",
        ROOT / "cases/leetcode-347/case-1.input.json",
        ROOT / "cases/leetcode-347/case-1.expected.json",
    ),
    "leetcode-79": (
        "boolean",
        ROOT / "cases/leetcode-79/case-1.input.json",
        ROOT / "cases/leetcode-79/case-1.expected.json",
    ),
    "leetcode-322": (
        "number",
        ROOT / "cases/leetcode-322/case-1.input.json",
        ROOT / "cases/leetcode-322/case-1.expected.json",
    ),
}


def load_registry() -> list[Item]:
    """Parse algorithms.yml with a tiny regex parser (stdlib only, so it ships in the installer)."""
    import re

    text = REGISTRY.read_text()
    blocks = re.split(r"\n  - id: ", text)
    items = []
    for block in blocks[1:]:
        lines = block.splitlines()
        item = {"id": lines[0].strip()}
        for line in lines[1:]:
            s = line.strip()
            if s.startswith("name:"):
                item["name"] = s[5:].strip()
            elif s.startswith("leetcode:"):
                m = re.search(r"id:\s*(\d+),\s*title:\s*(.*?)\s*}", s)
                if m:
                    item["leetcode_id"] = int(m.group(1))
                    item["leetcode_title"] = m.group(2)
            elif s.startswith("category:"):
                item["category"] = s[9:].strip()
            elif s.startswith("data_structures:"):
                item["data_structures"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("identification:"):
                item["identification"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("disqualifiers:"):
                item["disqualifiers"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("uses:"):
                item["uses"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
        for k in ("data_structures", "identification", "disqualifiers", "uses"):
            if k in item:
                item[k] = [x for x in item[k] if x]
        items.append(item)
    return items


def read_json(path: str | None) -> Any:
    """Load JSON from `path`, or from stdin when no path is given."""
    if path:
        with open(path) as f:
            return json.load(f)
    return json.load(sys.stdin)


def cmd_pipe(args: argparse.Namespace) -> None:
    """JSON in (--input, stdin, or the sample case) -> solver -> JSON out, for `| algo assert`."""
    item, target = pick(args.target)
    if args.input:
        data = read_json(args.input)
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
        else:
            data = sample_for(target)
            print("(no --input and no piped stdin: using the sample case)", file=sys.stderr)
    print(json.dumps(run_solver(item, target, data), default=repr))


def load_problems() -> list[Item]:
    """Parse problems.yml (one flow mapping per line) into dicts."""
    import re

    pat = re.compile(
        r"id:\s*(\d+),\s*title:\s*(.*?),\s*difficulty:\s*(\w+),"
        r"\s*algorithms:\s*\[(.*?)\],\s*keywords:\s*\[(.*?)\]"
    )
    out = []
    for line in PROBLEMS.read_text().splitlines():
        m = pat.search(line)
        if m:
            out.append(
                {
                    "id": int(m[1]),
                    "title": m[2],
                    "difficulty": m[3],
                    "algorithms": [x.strip() for x in m[4].split(",") if x.strip()],
                    "keywords": [x.strip() for x in m[5].split(",") if x.strip()],
                }
            )
            u = re.search(r"uses:\s*\[(.*?)\]", line)
            tag = re.search(r"list:\s*([\w-]+)", line)
            out[-1]["uses"] = [x.strip() for x in u[1].split(",") if x.strip()] if u else []
            out[-1]["list"] = tag[1] if tag else None
    return out


def solved_ids() -> set[int]:
    """LeetCode ids with a verified per-problem solution in algo.leetcode (see `algo verify`)."""
    from algo.leetcode.solutions import by_id

    return set(by_id())


MIN_WORD = 2  # words this short are ignored when scoring phrases


def score(query: str, phrases: list[str]) -> tuple[int, list[str]]:
    """Score `query` against phrases: 2 per whole-phrase hit, else 1 per shared word."""
    q = query.lower()
    total = 0
    hits = []
    for p in phrases:
        pp = p.lower()
        words = [w for w in pp.replace("-", " ").split() if len(w) > MIN_WORD]
        val = 2 if pp in q else sum(1 for w in words if w in q)
        if val:
            total += val
            hits.append(p)
    return total, hits


def _norm(t: str) -> str:
    return t.lower().replace("-", " ").replace("_", " ")


def match_name(query: str, item: Item) -> tuple[int, list[str]]:
    """Score a free-text query against id/name/category/title (strong) and tags (weak)."""
    q = _norm(query).strip()
    if not q:
        return 0, []
    strong = [
        item["id"],
        item.get("name", ""),
        item.get("category", ""),
        item.get("leetcode_title", ""),
    ]
    total, hits = 0, []
    for f in strong:
        nf = _norm(f)
        if not nf:
            continue
        if nf == q:
            val = 100
        elif nf.startswith(q):
            val = 50
        elif q in nf:
            val = 20
        else:
            val = 0
        if val:
            total += val
            hits.append(f)
    s, h = score(q, item.get("identification", []) + item.get("data_structures", []))
    return total + s, hits + h


def _search_score(args: argparse.Namespace, item: Item) -> tuple[int, list[str]]:
    """Score one registry entry for `algo s` according to which flag was given."""
    if args.id:
        return score(args.id, item.get("identification", []) + item.get("data_structures", []))
    if args.disqualifier:
        return score(args.disqualifier, item.get("disqualifiers", []))
    if args.query:
        return match_name(" ".join(args.query), item)
    return 1, []


def _print_search(rows: list[tuple[int, Item, list[str]]], args: argparse.Namespace) -> None:
    """Text output for `algo s`: `id  name`, plus example problems with -p."""
    w = max(len(i["id"]) for _, i, _ in rows)
    probs = load_problems() if args.problems else []
    for _, i, _ in rows:
        print(f"{i['id']:<{w}}  {i.get('name', '')}")
        if not args.problems:
            continue
        mine = sorted(
            (p for p in probs if i["id"] in p["algorithms"]),
            key=lambda p: (p["algorithms"].index(i["id"]), p["id"]),
        )
        for p in mine[: args.problems_top]:
            print(f"{'':<{w}}    {p['id']:>4}  {p['title']}")
        if len(mine) > args.problems_top:
            more = len(mine) - args.problems_top
            print(f"{'':<{w}}    ... +{more} more (algo p -a {i['id']})")


def cmd_search(args: argparse.Namespace) -> None:
    """Find algorithms by name, identification phrase or disqualifier."""
    rows = []
    for item in load_registry():
        s, h = _search_score(args, item)
        if s > 0:
            rows.append((s, item, h))
    rows.sort(key=lambda x: x[0], reverse=True)
    rows = rows[: args.top]
    if args.json:
        out = [
            {
                "id": i["id"],
                "name": i.get("name"),
                "score": s,
                "matched": h,
                "data_structures": i.get("data_structures", []),
            }
            for s, i, h in rows
        ]
        print(json.dumps(out, indent=2))
        return
    if not rows:
        print("no matches (looking for a problem by name? try: algo p <title>)", file=sys.stderr)
        raise SystemExit(1)
    _print_search(rows, args)


def resolve_algorithm(query: str) -> Item | None:
    """Exact id match first, then the best fuzzy match on id/name/category/title."""
    items = load_registry()
    q = _norm(query).strip()
    for i in items:
        if _norm(i["id"]) == q:
            return i
    ranked = sorted(((match_name(query, i)[0], i) for i in items), key=lambda x: -x[0])
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return None


# Helper definitions a solver depends on, beyond its own function body.
HELPERS = {"leetcode-684": ["DSU"], "deepmerge": ["_merge"]}


def target_of(item: Item) -> str:
    """Solver key for a registry entry: leetcode-<id> or the entry's own id."""
    return f"leetcode-{item['leetcode_id']}" if item.get("leetcode_id") else item["id"]


def sample_for(target: str) -> Any:
    """Sample input for a solver: its case-1 file if judged, else SAMPLES."""
    from algo.shorthand import SAMPLES

    if target in TARGETS:
        return json.loads(TARGETS[target][1].read_text())
    if target.startswith("lc-"):
        from algo.leetcode import runnable

        return runnable.sample(target)
    return SAMPLES[target]


def solver_for(target: str) -> Callable[[dict], Any]:
    """The callable behind a target: a SOLVERS entry, or a per-problem solution (lc-N)."""
    if target in SOLVERS:
        return SOLVERS[target]
    from algo.leetcode import runnable

    return lambda data: runnable.run(target, data)


def run_solver(item: Item, target: str, data: dict) -> Any:
    """Call a target's solver; report a crash on bad input as one line instead of a traceback."""
    try:
        return solver_for(target)(data)
    except Exception as e:
        shown = json.dumps(data, default=repr)[:200]
        print(f"{item['id']}: {type(e).__name__}: {e}\n  input: {shown}", file=sys.stderr)
        raise SystemExit(1) from e


def schema_for(target: str) -> dict[str, str]:
    """Ordered field -> shorthand type map for a target."""
    from algo.shorthand import SCHEMAS

    if target in SCHEMAS:
        return SCHEMAS[target]
    from algo.leetcode import runnable

    return runnable.targets()[target].schema


def tmp_dir(arg: str | None = None) -> pathlib.Path:
    """Output directory: arg, $ALGO_TMP, or the current directory (created if needed).

    Args:
        arg: An explicit `-o DIR`, or None.

    Returns:
        The absolute output directory.
    """
    d = pathlib.Path(arg or os.environ.get("ALGO_TMP") or pathlib.Path.cwd()).resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _problem_id(query: str) -> int | None:
    """875, lc-875, lc875, leetcode-875 or problem-875 -> 875; anything else -> None."""
    import re

    m = re.fullmatch(r"(?:lc-?|leetcode-|problem-)?(\d+)", query.strip().lower())
    return int(m[1]) if m else None


def _problem_item(t: ProblemTarget) -> Item:
    """A registry-shaped item describing a per-problem target, for naming and display."""
    return {
        "id": t.key,
        "name": t.title,
        "leetcode_id": t.pid,
        "leetcode_title": t.title,
        "lib": t.lib,
    }


def _title_match(query: str) -> ProblemTarget | None:
    """A runnable problem whose title equals the query, or is the only title it prefixes."""
    from algo.leetcode import runnable

    q = _norm(query).strip()
    if len(q) < 3:  # noqa: PLR2004 - too short to name a problem
        return None
    exact = [t for t in runnable.targets().values() if _norm(t.title) == q]
    prefix = [t for t in runnable.targets().values() if _norm(t.title).startswith(q)]
    if exact:
        return exact[0]
    return prefix[0] if len(prefix) == 1 else None


def _exact_algorithm(query: str) -> Item | None:
    """Registry entry whose id equals the query (ignoring case and -/_)."""
    q = _norm(query).strip()
    return next((i for i in load_registry() if _norm(i["id"]) == q), None)


def _resolve_number(query: str, pid: int) -> tuple[Item, str | None] | None:
    """lc-N is always the per-problem solution; a bare N prefers an existing leetcode-N solver."""
    from algo.leetcode import runnable

    if not query.strip().lower().startswith("lc") and f"leetcode-{pid}" in SOLVERS:
        return resolve_target(f"leetcode-{pid}")
    t = runnable.get(f"lc-{pid}")
    return (_problem_item(t), t.key) if t else None


def _resolve_name(query: str) -> tuple[Item, str | None] | None:
    """Exact algorithm id -> problem title -> fuzzy algorithm (falling back to its problem)."""
    from algo.leetcode import runnable

    item = _exact_algorithm(query)
    if item is None and (t := _title_match(query)):
        legacy = f"leetcode-{t.pid}"
        return resolve_target(legacy) if legacy in SOLVERS else (_problem_item(t), t.key)
    item = item or resolve_algorithm(query)
    if item is None:
        return None
    if target_of(item) in SOLVERS:
        return item, target_of(item)
    t = runnable.get(f"lc-{item['leetcode_id']}") if item.get("leetcode_id") else None
    t = t or _primary_problem_target(item["id"])
    return item, (t.key if t else None)


def _primary_problem_target(algo_id: str) -> ProblemTarget | None:
    """Lowest-numbered solved problem whose primary pattern is algo_id (fallback runner)."""
    from algo.leetcode import runnable

    for p in sorted(load_problems(), key=lambda p: p["id"]):
        if p["algorithms"][:1] == [algo_id] and (t := runnable.get(f"lc-{p['id']}")):
            return t
    return None


def resolve_target(query: str) -> tuple[Item, str | None] | None:
    """Resolve a query to (item, solver target); target None = known but not runnable.

    Order: solver key -> problem number (875, lc-875) -> exact algorithm id -> problem title ->
    fuzzy algorithm. An algorithm without a solver runs its representative problem's solution,
    else the lowest-numbered solved problem whose primary pattern it is.
    """
    if query in SOLVERS:
        return next((i for i in load_registry() if target_of(i) == query), {"id": query}), query
    pid = _problem_id(query)
    return _resolve_number(query, pid) if pid is not None else _resolve_name(query)


def pick(query: str) -> tuple[Item, str]:
    """Resolve a query to (item, solver target), or exit with a hint."""
    found = resolve_target(query)
    item, target = found if found else (None, None)
    if not item:
        print(
            f"no algorithm matches {query!r}  (try: algo s {query}  or  algo p {query})",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if target is None:
        print(
            f"{item['id']} is in the registry but has no solver yet"
            " — see docs/API.md ('Adding a solver')",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return item, target


def lib_path(item: Item, outdir: pathlib.Path) -> pathlib.Path:
    """Where `algo g` writes an algorithm's library file."""
    return outdir / f"{(item.get('lib') or item['id']).replace('-', '_')}.py"


def generate_lib(item: Item, target: str, outdir: pathlib.Path) -> pathlib.Path:
    """Write the importable algorithm library <id>.py into outdir; return its path."""
    path = lib_path(item, outdir)
    path.write_text(library_text(item, target, path))
    return path


def library_text(item: Item, target: str, path: pathlib.Path) -> str:
    """Source of the standalone library for target, as it would be written to path.

    Args:
        item: The registry item the target was resolved from.
        target: A solver key (leetcode-N) or a per-problem target (lc-N).
        path: Where the file lives (or would live); quoted in its docstring.

    Returns:
        The complete, runnable Python source.
    """
    import inspect

    from algo import solutions

    if target.startswith("lc-"):
        return _problem_library_text(item, target, path)
    fn = SOLVERS[target]
    parts = [inspect.getsource(getattr(solutions, h)) for h in HELPERS.get(target, [])] + [
        inspect.getsource(fn)
    ]
    lc = (
        f" (LeetCode {item['leetcode_id']}: {item.get('leetcode_title')})"
        if item.get("leetcode_id")
        else ""
    )
    return (
        f'"""{item.get("name")} — {item["id"]}{lc}\n'
        f"Import:  from {path.stem} import solve      solve({{...}}) -> result\n"
        f'Run:     python3 {path} [input.json]        (default: sample below)\n"""\n'
        "from __future__ import annotations\nimport json, sys\n"
        "from collections import Counter, defaultdict, deque\nimport heapq\n"
        "from typing import Any\n\n\n"
        + "\n\n".join(parts)
        + f"\n\nsolve = {fn.__name__}\n\nSAMPLE = {json.dumps(sample_for(target))}\n\n"
        'if __name__ == "__main__":\n'
        "    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else SAMPLE\n"
        "    print(json.dumps(solve(data), default=repr))\n"
    )


def _problem_library_text(item: Item, target: str, path: pathlib.Path) -> str:
    """Standalone library source for a per-problem target (helpers and node types inlined)."""
    from algo.leetcode import runnable

    t = runnable.targets()[target]
    title = f"{t.title} — {t.key} (LeetCode {t.pid})"
    if item["id"] != t.key:
        title = f"{item.get('name')} — {item['id']} (LeetCode {t.pid}: {t.title})"
    return runnable.library_source(target, title, str(path))


def cmd_generate(args: argparse.Namespace) -> None:
    """Write an algorithm's importable library file and print its path (`-p`: print the code)."""
    item, target = pick(" ".join(args.query))
    if args.print:  # nothing is written; the docstring names where `algo g` would put it
        outdir = pathlib.Path(args.out_dir or os.environ.get("ALGO_TMP") or pathlib.Path.cwd())
        sys.stdout.write(library_text(item, target, lib_path(item, outdir.resolve())))
        return
    print(generate_lib(item, target, tmp_dir(args.out_dir)))


def pull(toks: list[str], *names: str) -> str | None:
    """Remove `name value` from toks (first match) and return value, else None."""
    for n in names:
        if n in toks:
            i = toks.index(n)
            if i + 1 >= len(toks):
                print(f"{n} needs a value", file=sys.stderr)
                raise SystemExit(2)
            v = toks[i + 1]
            del toks[i : i + 2]
            return v
    return None


def _names_target(word: str) -> bool:
    """Is a trailing `algo i` word a target? Bare numbers stay values; use lc-N or -a for those."""
    if _problem_id(word) is not None and not word.lower().startswith(("lc", "leetcode")):
        return False
    found = resolve_target(word)
    return bool(found and found[1])


def cmd_inputs(args: argparse.Namespace) -> None:
    """Write inputs.py: `algo i <value> [<value> ...] [<algo>] [-a algo] [-o dir]`."""
    import pprint

    from algo.shorthand import ShorthandError, build_input, split_values

    toks = list(args.tokens)
    algo = pull(toks, "-a", "--algo") or args.algo_opt
    outdir = tmp_dir(pull(toks, "-o", "--out-dir") or args.out_opt)
    try:
        vals = split_values(toks)
    except ShorthandError as e:
        print(f"bad input: {e}", file=sys.stderr)
        raise SystemExit(2) from e
    if algo is None:  # trailing bare word that names an algorithm
        if vals and vals[-1][:1] not in "[{'\"" and _names_target(vals[-1]):
            algo = vals.pop()
        else:
            print(
                "which algorithm? add one as the last word or with -a, e.g.  algo i 1 2 add",
                file=sys.stderr,
            )
            raise SystemExit(2)
    item, target = pick(algo)
    schema = schema_for(target)
    try:
        data = build_input(
            target,
            vals,
            sample_for(target),
            None,
            __import__("random").Random(),
            strict=True,
            schema=schema,
        )
    except (ShorthandError, ValueError) as e:
        print(
            f"{item['id']}: bad input: {e}\n  fields: "
            + " ".join(f"{k}:{v}" for k, v in schema.items()),
            file=sys.stderr,
        )
        raise SystemExit(2) from e
    lib = lib_path(item, outdir)
    if not lib.exists():  # make the dependency, then build on it
        generate_lib(item, target, outdir)
        print(f"generated {lib}", file=sys.stderr)
    body = "\n".join(f"{k} = {pprint.pformat(v, width=88)}" for k, v in data.items())
    call = ", ".join(f"{k!r}: {k}" for k in data)
    out = outdir / "inputs.py"
    out.write_text(
        f'"""Inputs for {item["id"]}.  Run: python3 {out}"""\n'
        f"import json, sys\nsys.path.insert(0, {str(outdir)!r})\nfrom {lib.stem} import solve\n\n"
        f'{body}\n\nif __name__ == "__main__":\n'
        f"    print(json.dumps(solve({{{call}}}), default=repr))\n"
    )
    print(out)


def cmd_run(args: argparse.Namespace) -> None:
    """Run in-process: `algo run <algo> [values...] [then <algo> [values...]] ...`."""
    import random

    from algo.shorthand import ShorthandError, build_input, split_values

    toks = list(args.tokens)
    seed = args.seed
    verbose = args.verbose
    if "-v" in toks:
        toks.remove("-v")
        verbose = True
    if "--seed" in toks:
        i = toks.index("--seed")
        seed = int(toks[i + 1])
        del toks[i : i + 2]
    rng = random.Random(seed)  # noqa: S311 - reproducible test inputs, not crypto
    stages: list[list[str]] = [[]]
    for t in toks:
        if t == "then":
            stages.append([])
        else:
            stages[-1].append(t)
    prev = None
    for st in stages:
        if not st:
            print("empty stage around 'then'", file=sys.stderr)
            raise SystemExit(2)
        item, target = pick(st[0])
        try:
            data = build_input(
                target,
                split_values(st[1:]),
                sample_for(target),
                prev,
                rng,
                schema=schema_for(target),
            )
        except (ShorthandError, ValueError) as e:
            print(
                f"{item['id']}: bad input: {e}\n  fields: "
                + " ".join(f"{k}:{v}" for k, v in schema_for(target).items()),
                file=sys.stderr,
            )
            raise SystemExit(2) from e
        prev = run_solver(item, target, data)
        if verbose or len(stages) > 1:
            shown = json.dumps(data, separators=(",", ":"))
            print(f"{item['id']:<16} in={shown}  out={json.dumps(prev)}", file=sys.stderr)
    print(json.dumps(prev))


def _title_score(q: str, t: str) -> int:
    """Exact/prefix/substring title match, then whole and prefix word hits (`k` -> `kth`)."""
    s = 100 if t == q else 50 if t.startswith(q) else 30 if q in t else 0
    tw = set(t.split())
    qw = q.split()
    s += 5 * sum(1 for w in qw if len(w) > 1 and w in tw)
    s += 3 * sum(1 for w in qw if w not in tw and any(x.startswith(w) for x in tw))
    return s


def _tag_score(q: str, p: Item) -> int:
    """Keyword phrase/word hits, algorithm names, and uses ("rate limiter" -> 359)."""
    s = 12 * any(q in _norm(k) for k in p["keywords"])
    s += 3 * score(q, p["keywords"])[0]
    s += 10 * sum(1 for a in p["algorithms"] if q in _norm(a))
    s += 6 * any(q in _norm(u) for u in p.get("uses", []))
    return s


def score_problem(query: str, p: Item) -> int:
    """Rank a problem for `algo p`: title, number, keywords, algorithms, uses."""
    q = _norm(query).strip()
    if q.isdigit():
        return 100 if int(q) == p["id"] else 0
    if not q:
        return 1
    return _title_score(q, _norm(p["title"])) + _tag_score(q, p)


def _filter_problems(args: argparse.Namespace) -> list[Item]:
    """Apply `-a ALGO` and `-l LIST` to the problem index."""
    probs = load_problems()
    if args.algo:
        algo = resolve_algorithm(args.algo)
        if not algo:
            print(f"no algorithm matches {args.algo!r}", file=sys.stderr)
            raise SystemExit(1)
        probs = [p for p in probs if algo["id"] in p["algorithms"]]
    if args.list:
        probs = [p for p in probs if p.get("list") == args.list]
    return probs


def _print_problems(rows: list[tuple[int, Item]], solved: set[int], *, uses: bool) -> None:
    """Text output for `algo p`; `*` marks a verified per-problem solution."""
    w = max(len(p["title"]) for _, p in rows)
    for _, p in rows:
        mark = "*" if p["id"] in solved else " "
        algos = ", ".join(p["algorithms"])
        print(f"{p['id']:>4}{mark} {p['title']:<{w}}  {p['difficulty']:<6}  -> {algos}")
        if uses and p.get("uses"):
            print(f"{'':>6} {'':<{w}}  also: {'; '.join(p['uses'])}")


def cmd_problems(args: argparse.Namespace) -> None:
    """Map a problem (title, number, or keywords) to the algorithm(s) that solve it."""
    q = " ".join(args.query)
    rows = [(score_problem(q, p), p) for p in _filter_problems(args)]
    rows = [r for r in rows if r[0] > 0]
    rows.sort(key=lambda r: (-r[0], r[1]["id"]))
    top = args.top if args.top is not None else (8 if q else 0)
    solved = solved_ids()
    if top > 0:
        rows = rows[:top]
    if args.json:
        out = [
            {
                **p,
                "score": s,
                "has_solver": f"leetcode-{p['id']}" in SOLVERS,
                "has_solution": p["id"] in solved,
                "target": f"lc-{p['id']}" if p["id"] in solved else None,
            }
            for s, p in rows
        ]
        print(json.dumps(out, indent=2))
        return
    if not rows:
        print("no matching problems (try keywords, e.g. algo p 'shortest path')", file=sys.stderr)
        raise SystemExit(1)
    _print_problems(rows, solved, uses=args.uses)


def _check_problems(reg: list[Item], solved: set[int]) -> list[str]:
    """Registry ids are unique; problems use known algorithms; study99 problems are solved."""
    from algo.leetcode.catalog import SPECS

    errs: list[str] = []
    ids = [i["id"] for i in reg]
    idset = set(ids)
    errs += [f"duplicate algorithm id: {x}" for x in sorted({x for x in ids if ids.count(x) > 1})]
    for p in load_problems():
        errs += [
            f"problem {p['id']} ({p['title']}): unknown algorithm {a!r}"
            for a in p["algorithms"]
            if a not in idset
        ]
    for p in load_problems():
        if p.get("list") == "study99" and p["id"] not in solved:
            errs.append(
                f"problem {p['id']}: on study99 but no solution in algo/leetcode/solutions.py"
            )
        if p["id"] in solved and p["id"] not in SPECS:
            errs.append(f"problem {p['id']}: solution has no test Spec in algo/leetcode/catalog.py")
    return errs


def _check_solvers(reg: list[Item]) -> list[str]:
    """Solvers have schemas, registry entries, working samples, helpers and case files."""
    from algo import solutions
    from algo.shorthand import SCHEMAS

    errs: list[str] = []
    by_target = {target_of(i): i for i in reg}
    for t in SOLVERS:
        if t not in SCHEMAS:
            errs.append(f"solver {t}: no entry in SCHEMAS (shorthand.py)")
        if t not in by_target:
            errs.append(f"solver {t}: no registry entry maps to it (leetcode id or algorithm id)")
        try:
            SOLVERS[t](sample_for(t))
        except Exception as e:
            errs.append(f"solver {t}: failed on its sample: {type(e).__name__}: {e}")
        errs += [
            f"solver {t}: HELPERS names missing {h!r}"
            for h in HELPERS.get(t, [])
            if not hasattr(solutions, h)
        ]
    errs += [f"SCHEMAS {t}: no solver" for t in SCHEMAS if t not in SOLVERS]
    for t, (comp, inp, exp) in TARGETS.items():
        if t not in SOLVERS:
            errs.append(f"TARGETS {t}: no solver")
        if comp not in COMPARATORS:
            errs.append(f"TARGETS {t}: unknown comparator {comp!r}")
        errs += [f"TARGETS {t}: missing file {f}" for f in (inp, exp) if not f.exists()]
    return errs


def _check_problem_targets() -> list[str]:
    """Every per-problem target has known field types and reproduces its catalog example."""
    from algo.leetcode import runnable
    from algo.shorthand import SCHEMAS

    known = {k for sc in SCHEMAS.values() for k in sc.values()} | set(runnable.TYPE_MAP.values())
    errs = []
    for key, t in runnable.targets().items():
        errs += [f"{key}: unknown field type {v!r}" for v in t.schema.values() if v not in known]
        try:
            got = runnable.run(key, runnable.sample(key))
        except Exception as e:
            errs.append(f"{key}: failed on its sample: {type(e).__name__}: {e}")
            continue
        if not runnable.matches_expected(key, got):
            errs.append(f"{key}: sample gave {got!r}, expected {runnable.expected(key)!r}")
    return errs


def cmd_check(_args: argparse.Namespace) -> NoReturn:
    """Cross-check registry, problem index, solvers, schemas, cases. Exit 1 on any error."""
    reg = load_registry()
    solved = solved_ids()
    errs = _check_problems(reg, solved) + _check_solvers(reg) + _check_problem_targets()
    errs += [f"algorithm {i['id']}: no `uses` (algo uses)" for i in reg if not i.get("uses")]
    for e in errs:
        print("ERROR", e, file=sys.stderr)
    print(
        f"{len(reg)} algorithms, {len(load_problems())} problems "
        f"({len(solved)} with verified solutions), {len(SOLVERS)} solvers "
        f"+ {len(solved)} problem targets, "
        f"{len(TARGETS)} judged targets: " + ("OK" if not errs else f"{len(errs)} error(s)")
    )
    raise SystemExit(1 if errs else 0)


def cmd_verify(args: argparse.Namespace) -> NoReturn:
    """Run algo.leetcode.verify; --fetch shallow-clones the reference repo when it is missing."""
    import subprocess

    from algo.leetcode import verify

    rest = list(args.rest)
    ref = (
        pathlib.Path(rest[rest.index("--ref") + 1]).expanduser()
        if "--ref" in rest
        else verify.DEFAULT_REF
    )
    if "--fetch" in rest:
        rest.remove("--fetch")
        if not ref.exists():
            ref.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(  # noqa: S603 - fixed argv, no shell
                ["git", "clone", "--depth", "1", "-q", verify.REF_URL, str(ref)],  # noqa: S607
                check=True,
            )
    raise SystemExit(verify.main(rest))


def cmd_complete(args: argparse.Namespace) -> None:
    """Hidden helper for shell completions: print `value<TAB>description` candidates."""
    if args.kind == "algos":
        for i in load_registry():
            print(f"{i['id']}\t{i.get('name', '')}")
    elif args.kind == "runnable":  # what `pipe` accepts: algorithms with a solver + solver keys
        for i in load_registry():
            if target_of(i) in SOLVERS:
                print(f"{i['id']}\t{i.get('name', '')}")
        for t in SOLVERS:
            if t.startswith("leetcode-"):
                print(f"{t}\tsolver target")
        from algo.leetcode import runnable

        for key, pt in runnable.targets().items():
            print(f"{key}\t{pt.title}")
    elif args.kind == "judged":
        for t in sorted(TARGETS):
            print(t)
    elif args.kind == "comparators":
        for c in COMPARATORS:
            print(c)


def _shape_detail(item: Item, target: str) -> None:
    """One target's fields, the problem it runs (if any) and its sample."""
    fields = " ".join(f"{k}:{v}" for k, v in schema_for(target).items())
    print(f"{item['id']:<16} {fields}")
    if target.startswith("lc-") and item["id"] != target:
        from algo.leetcode import runnable

        t = runnable.targets()[target]
        print(f"{'':<16} runs: {t.key} {t.title}")
    print(f"{'':<16} sample: {json.dumps(sample_for(target), default=repr)}")


def filter_algorithms(query: str, items: list[Item]) -> list[Item]:
    """Algorithms whose id, name or category contain query; else whose tags mention it."""
    q = _norm(query).strip()
    strong = [i for i in items if any(q in _norm(i.get(f, "")) for f in ("id", "name", "category"))]
    if strong:
        return strong
    tags = ("identification", "data_structures")
    return [i for i in items if score(q, [t for f in tags for t in i.get(f, [])])[0] > 0]


def _shape_rows(items: list[Item]) -> None:
    """`id  fields  (runs lc-N ...)` for each algorithm; `(no solver yet)` when not runnable."""
    w = max(len(i["id"]) for i in items)
    for i in items:
        found = resolve_target(i["id"])
        target = found[1] if found else None
        if target is None:
            print(f"{i['id']:<{w}}  (no solver yet)")
            continue
        fields = " ".join(f"{k}:{v}" for k, v in schema_for(target).items())
        runs = f"   (runs {target})" if target.startswith("lc-") else ""
        print(f"{i['id']:<{w}}  {fields}{runs}")


def cmd_shapes(args: argparse.Namespace) -> None:
    """Input fields per algorithm: all, those matching a word (`sort`), or one target (`875`)."""
    reg = load_registry()
    if not args.query:
        _shape_rows(reg)
        print(f"(+ {len(solved_ids())} problem targets lc-N: algo sh <problem>, e.g. algo sh 875)")
        return
    q = " ".join(args.query)
    if q in SOLVERS or _problem_id(q) is not None:
        _shape_detail(*pick(q))
        return
    matches = filter_algorithms(q, reg)
    if len(matches) == 1:
        _shape_detail(*pick(matches[0]["id"]))
    elif matches:
        _shape_rows(matches)
    else:  # a problem title such as "koko"
        _shape_detail(*pick(q))


def _wrap(label: str, text: str, indent: int) -> str:
    import shutil
    import textwrap

    width = max(60, min(shutil.get_terminal_size((100, 20)).columns, 120))
    pad = " " * indent
    return textwrap.fill(
        text, width, initial_indent=pad + label, subsequent_indent=pad + " " * len(label)
    )


def cmd_uses(args: argparse.Namespace) -> None:
    """Common uses per algorithm, or the algorithms (and problems) that fit a described need."""
    from algo.cli import uses

    q = " ".join(args.query)
    found = uses.search(
        q, load_registry(), load_problems(), top=args.top, per_algo=args.problems_top
    )
    solved = solved_ids()
    if args.json:
        out = [
            {
                "id": m.algo["id"],
                "name": m.algo.get("name"),
                "score": round(m.score, 2),
                "uses": m.matched,
                "problems": [
                    {"id": p["id"], "title": p["title"], "solved": p["id"] in solved}
                    for p in m.problems
                ],
            }
            for m in found
        ]
        print(json.dumps(out, indent=2))
        return
    if not found:
        print(f"no algorithm matches {q!r}  (try other words, or: algo s {q})", file=sys.stderr)
        raise SystemExit(1)
    for m in found:
        print(f"{m.algo['id']}  {m.algo.get('name', '')}")
        if m.matched:
            print(_wrap("uses:     ", "; ".join(m.matched), 2))
        if m.problems:
            probs = " · ".join(
                f"{p['id']}{'*' if p['id'] in solved else ''} {p['title']}" for p in m.problems
            )
            print(_wrap("problems: ", probs, 2))


def cmd_assert(args: argparse.Namespace) -> NoReturn:
    """Compare actual JSON (file or stdin) with an expected file; exit 1 on mismatch."""
    actual = read_json(args.actual)
    expected = read_json(args.expected)
    comp = COMPARATORS[args.comparator]
    ok = comp(actual, expected)
    print(
        json.dumps(
            {
                "status": "PASS" if ok else "FAIL",
                "comparator": args.comparator,
                "actual": actual,
                "expected": expected,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if ok else 1)


def cmd_judge(args: argparse.Namespace) -> NoReturn:
    """Run a judged target's sample and compare it with the expected output."""
    comparator, input_path, expected_path = TARGETS[args.target]
    actual = SOLVERS[args.target](json.loads(input_path.read_text()))
    expected = json.loads(expected_path.read_text())
    ok = COMPARATORS[comparator](actual, expected)
    print(
        json.dumps(
            {
                "target": args.target,
                "status": "PASS" if ok else "FAIL",
                "comparator": comparator,
                "actual": actual,
                "expected": expected,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if ok else 1)


def cmd_targets(_args: argparse.Namespace) -> None:
    """List judged targets as JSON."""
    print(json.dumps(sorted(TARGETS.keys()), indent=2))


def _add_judge_commands(sub: Any) -> None:
    """Register pipe, judge and assert."""
    s = sub.add_parser("pipe", help="JSON in -> solver -> JSON out (for `| algo assert`)")
    s.add_argument("target", help="algorithm name/id or leetcode-N")
    s.add_argument("--input", "-i")
    s.set_defaults(func=cmd_pipe)
    j = sub.add_parser("judge")
    j.add_argument("target", choices=TARGETS.keys())
    j.set_defaults(func=cmd_judge)
    a = sub.add_parser("assert")
    a.add_argument("--expected", required=True)
    a.add_argument("--actual")
    a.add_argument("--comparator", default="exact", choices=COMPARATORS.keys())
    a.set_defaults(func=cmd_assert)


def _add_find_commands(sub: Any) -> None:
    """Register search, problems and verify."""
    search = sub.add_parser("search", aliases=["s"])
    search.add_argument("query", nargs="*", help="name/id/category/keyword, e.g. bfs or graph")
    search.add_argument("--id")
    search.add_argument("--disqualifier")
    search.add_argument("--top", type=int, default=5)
    search.add_argument(
        "-p",
        "--problems",
        action="store_true",
        help="also list LeetCode problems solved by each match",
    )
    search.add_argument("--problems-top", type=int, default=5)
    search.add_argument("-j", "--json", action="store_true", help="full JSON output")
    search.set_defaults(func=cmd_search)
    pr = sub.add_parser(
        "problems", aliases=["p"], help="problem title/number/keywords -> algorithms"
    )
    pr.add_argument("query", nargs="*")
    pr.add_argument("-a", "--algo", help="only problems solved by this algorithm")
    pr.add_argument("--top", type=int)
    pr.add_argument(
        "-u",
        "--uses",
        action="store_true",
        help="also print other uses of each problem's technique",
    )
    pr.add_argument("-l", "--list", help="only problems on this list, e.g. study99")
    pr.add_argument("-j", "--json", action="store_true")
    pr.set_defaults(func=cmd_problems)
    vf = sub.add_parser(
        "verify",
        add_help=False,
        help="differential-test the per-problem solutions against cnkyrpsgl/leetcode + brute force",
    )
    vf.add_argument(
        "rest",
        nargs=argparse.REMAINDER,
        help="[ids...] [--ref DIR] [-n N] [--seed S] [-j] [-v] [--fetch]",
    )
    vf.set_defaults(func=cmd_verify)


def _add_build_commands(sub: Any) -> None:
    """Register generate, run, inputs, check, complete, shapes and targets."""
    g = sub.add_parser("generate", aliases=["g"])
    g.add_argument("query", nargs="+", help="algorithm id or name, e.g. bfs")
    g.add_argument("-o", "--out-dir", help="output dir (default: $ALGO_TMP, else the cwd)")
    g.add_argument(
        "-p", "--print", action="store_true", help="print the library to stdout; write nothing"
    )
    g.set_defaults(func=cmd_generate)
    r = sub.add_parser("run", aliases=["r"])
    r.add_argument("tokens", nargs=argparse.REMAINDER, help="<algo> [values...] [then <algo> ...]")
    r.add_argument("--seed", type=int, default=None)
    r.add_argument("-v", "--verbose", action="store_true")
    r.set_defaults(func=cmd_run)
    inp = sub.add_parser(
        "inputs",
        aliases=["i"],
        help="write inputs.py for an algorithm (generates its library if missing)",
    )
    # -a/-o are declared so they also work as the first token (REMAINDER can't start with a flag);
    # later in the line they are pulled out of `tokens` by cmd_inputs.
    inp.add_argument("-a", "--algo", dest="algo_opt", help="algorithm or problem (875, lc-875)")
    inp.add_argument(
        "-o", "--out-dir", dest="out_opt", help="output dir (default: $ALGO_TMP, else the cwd)"
    )
    inp.add_argument(
        "tokens", nargs=argparse.REMAINDER, help="<values...> [<algo>] [-a algo] [-o dir]"
    )
    inp.set_defaults(func=cmd_inputs)
    ck = sub.add_parser(
        "check", help="validate registry/problems/solvers/schemas against each other"
    )
    ck.set_defaults(func=cmd_check)
    co = sub.add_parser("complete", help=argparse.SUPPRESS)
    co.add_argument("kind", choices=["algos", "runnable", "judged", "comparators"])
    co.set_defaults(func=cmd_complete)
    sh = sub.add_parser(
        "shapes", aliases=["sh"], help="input fields per algorithm (filter: sort, graph)"
    )
    sh.add_argument(
        "query", nargs="*", help="filter word (sort), or one algorithm / problem (875, koko)"
    )
    sh.set_defaults(func=cmd_shapes)
    u = sub.add_parser(
        "uses", aliases=["u"], help="real-world uses per algorithm; describe a need to search"
    )
    u.add_argument("query", nargs="*", help="a need, e.g. shortest distance between two zip codes")
    u.add_argument("--top", type=int, default=5, help="algorithms to show for a query (default 5)")
    u.add_argument(
        "-p", dest="problems_top", type=int, default=3, help="problems per algorithm (default 3)"
    )
    u.add_argument("-j", "--json", action="store_true")
    u.set_defaults(func=cmd_uses)
    t = sub.add_parser("targets")
    t.set_defaults(func=cmd_targets)


def main() -> None:
    """Entry point for the `algo` command."""
    if sys.argv[1:2] == ["verify"]:  # pass every flag straight through to algo.leetcode.verify
        cmd_verify(argparse.Namespace(rest=sys.argv[2:]))
    p = argparse.ArgumentParser(prog="algo")
    sub = p.add_subparsers(required=True)
    _add_judge_commands(sub)
    _add_find_commands(sub)
    _add_build_commands(sub)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
