"""Shorthand input language for `algo run`.

Each target declares a schema (ordered field -> type). Tokens fill fields
positionally, or by name with ``key=value``. Value sugar by type:

  int      5
  ints     1,2,5   | 1..5 | rand:8:0-9            (n, lo-hi)
  str      abcabcbb | rand:10:abc                 (n, alphabet)
  cgrid    11000/11000/00100   (chars)  | rand:4x5[:01]
  igrid    2,1,1/1,1,0/0,1,1   (ints)   | rand:4x5[:012]
  strs     eat,tea,tan                            (list of strings)
  floats   0.5,0.5,0.2                            (list of numbers)
  ll       2,4,3   | 1..5 | rand:...              (ints, passed as a linked list)
  tree     3,9,20,null,null,15,7                  (level order; null = no node)
  any      5 | abc | [1, 2] | [a: [1, 2], b: [3]]   (literal syntax, see below)
  edges    1-2 1-3 2-3 | 1-2-3-4 (path) | rand:6:8 (nodes, edges; acyclic u>v)
  wedges   2-1:1 2-3:1 3-4:1    (u-v:weight) | rand:6:8

Literal syntax works for ANY type: ``[1, 2, 3]`` is a list, ``[k: v, ...]`` (or
``{k: v}``) is a dict, quotes force strings, bare scalars are int/float/bool/null/str.
Bracketed values may contain spaces; split_values() re-joins shell-split args.

``@`` or no tokens = built-in sample. ``_`` = previous stage's output.
Stages chain with the bare word ``then``.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import random

SCHEMAS: dict[str, dict[str, str]] = {
    "leetcode-1": {"nums": "ints", "target": "int"},
    "leetcode-200": {"grid": "cgrid"},
    "leetcode-994": {"grid": "igrid"},
    "leetcode-33": {"nums": "ints", "target": "int"},
    "leetcode-3": {"s": "str"},
    "leetcode-210": {"numCourses": "int", "prerequisites": "edges"},
    "leetcode-684": {"edges": "edges"},
    "leetcode-743": {"times": "wedges", "n": "int", "k": "int"},
    "leetcode-347": {"nums": "ints", "k": "int"},
    "leetcode-79": {"board": "cgrid", "word": "str"},
    "leetcode-322": {"coins": "ints", "amount": "int"},
    "add": {"a": "any", "b": "any"},
    "deepmerge": {"a": "any", "b": "any"},
}
SAMPLES: dict[str, dict] = {
    "add": {"a": 1, "b": 2},
    "deepmerge": {"a": {"x": [1], "y": {"z": 1}}, "b": {"x": [2], "y": {"w": 2}}},
}
GRID_ALPHA = {"leetcode-200": "01", "leetcode-994": "012", "leetcode-79": "ABCDE"}


class ShorthandError(ValueError):
    """A shorthand token could not be parsed or does not fit the schema."""


def _range(spec: str) -> tuple[int, int]:
    lo, _, hi = spec.partition("-")
    return int(lo), int(hi or lo)


def _rand_edges(n: int, m: int, rng: random.Random, weighted: bool) -> list[list[int]]:
    seen: set[tuple[int, int]] = set()
    out: list[list[int]] = []
    for _ in range(m * 4):
        if len(out) >= m or n < 2:  # noqa: PLR2004 - an edge needs two nodes
            break
        u, v = sorted(rng.sample(range(n), 2), reverse=True)  # u>v keeps it a DAG
        if (u, v) in seen:
            continue
        seen.add((u, v))
        out.append([u, v] + ([rng.randint(1, 9)] if weighted else []))
    return out


def split_values(toks: list[str]) -> list[str]:
    """Re-join shell-split args so each bracketed literal is one value."""
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    for t in toks:
        buf.append(t)
        depth += t.count("[") + t.count("{") - t.count("]") - t.count("}")
        if depth <= 0:
            out.append(" ".join(buf))
            buf = []
            depth = 0
    if buf:
        raise ShorthandError("unbalanced brackets: " + " ".join(buf))
    return out


def _scalar(w: str) -> object:
    for conv in (int, float):
        try:
            return conv(w)
        except ValueError:
            pass
    return {"true": True, "false": False, "null": None, "none": None}.get(w.lower(), w)


class _Lit:
    """Tiny recursive-descent parser for the relaxed literal syntax."""

    def __init__(self, s: str) -> None:
        self.s, self.i = s, 0

    def peek(self) -> str:
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
        return self.s[self.i] if self.i < len(self.s) else ""

    def quoted(self) -> str:
        q = self.s[self.i]
        j = self.s.find(q, self.i + 1)
        if j < 0:
            raise ShorthandError("unterminated string")
        w = self.s[self.i + 1 : j]
        self.i = j + 1
        return w

    def bare(self) -> str:
        j = self.i
        while j < len(self.s) and self.s[j] not in ",]}:[{":
            j += 1
        w = self.s[self.i : j].strip()
        self.i = j
        if not w:
            raise ShorthandError(f"unexpected {self.s[j : j + 1]!r} at {j} in {self.s!r}")
        return w

    def value(self) -> object:
        c = self.peek()
        if c in ("[", "{"):
            return self.container()
        if c in ("'", '"'):
            return self.quoted()
        return _scalar(self.bare())

    def container(self) -> object:
        close = "]" if self.s[self.i] == "[" else "}"
        self.i += 1
        items: list[tuple[str | None, object]] = []
        while True:
            c = self.peek()
            if c == close:
                self.i += 1
                break
            if c == "":
                raise ShorthandError(f"missing {close!r} in {self.s!r}")
            items.append(self.item(c))
            c = self.peek()
            if c == ",":
                self.i += 1
            elif c != close:
                raise ShorthandError(f"expected ',' or {close!r} at {self.i} in {self.s!r}")
        return self.collect(items, close)

    def item(self, c: str) -> tuple[str | None, object]:
        """One container element: a nested container, `key: value`, or a bare/quoted value."""
        if c in ("[", "{"):
            return None, self.container()
        quoted = c in ("'", '"')
        w = self.quoted() if quoted else self.bare()
        if self.peek() == ":":
            self.i += 1
            return w, self.value()
        return None, w if quoted else _scalar(w)

    def collect(self, items: list[tuple[str | None, object]], close: str) -> object:
        """All keyed -> dict; none keyed -> list (or {} for an empty brace)."""
        keyed = [k is not None for k, _ in items]
        if any(keyed):
            if not all(keyed):
                raise ShorthandError(f"mixed keyed/unkeyed items in {self.s!r}")
            return dict(items)
        return [v for _, v in items] if close == "]" else {}


def parse_literal(tok: str) -> object:
    """Parse literal syntax: `[1, 2]`, `[k: v]`, `{k: v}`, quoted strings, bare scalars."""
    p = _Lit(tok.strip())
    v = p.value()
    if p.peek():
        raise ShorthandError(f"trailing text in {tok!r}")
    return v


def _arg(parts: list[str], i: int, default: str) -> str:
    """parts[i] if present, else default (for optional `rand:` fields)."""
    return parts[i] if len(parts) > i else default


def _parse_ints(tok: str, parts: list[str], rng: random.Random, _alpha: str) -> object:
    if parts[0] == "rand":
        lo, hi = _range(_arg(parts, 2, "0-9"))
        return [rng.randint(lo, hi) for _ in range(int(parts[1]))]
    if ".." in tok:
        a, b = tok.split("..")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in tok.split(",") if x]


def _parse_str(tok: str, parts: list[str], rng: random.Random, _alpha: str) -> object:
    if parts[0] == "rand":
        chars = _arg(parts, 2, "abc")
        return "".join(rng.choice(chars) for _ in range(int(parts[1])))
    return tok


def _parse_grid(tok: str, parts: list[str], rng: random.Random, alpha: str) -> list[list[str]]:
    if parts[0] == "rand":
        r, c = parts[1].split("x")
        chars = _arg(parts, 2, alpha)
        return [[rng.choice(chars) for _ in range(int(c))] for _ in range(int(r))]
    return [row.split(",") if "," in row else list(row) for row in tok.split("/")]


def _parse_edges(tok: str, parts: list[str], rng: random.Random, weighted: bool) -> object:
    if parts[0] == "rand":
        return _rand_edges(int(parts[1]), int(parts[2]), rng, weighted)
    out: list[list[int]] = []
    for e in tok.split(","):
        body, _, wt = e.partition(":")
        nodes = [int(x) for x in body.split("-")]
        out += [[a, b, *([int(wt or 1)] if weighted else [])] for a, b in itertools.pairwise(nodes)]
    return out  # 1-2-3 => [1,2],[2,3]


def _parse_strs(tok: str, _parts: list[str], _rng: random.Random, _alpha: str) -> object:
    return [w for w in tok.split(",") if w]


def _parse_floats(tok: str, _parts: list[str], _rng: random.Random, _alpha: str) -> object:
    return [_scalar(x) for x in tok.split(",") if x]


def _parse_tree(tok: str, _parts: list[str], _rng: random.Random, _alpha: str) -> object:
    return [_scalar(x) for x in tok.split(",") if x]


def parse_value(kind: str, tok: str, rng: random.Random, alpha: str = "01") -> object:
    """Parse one token as `kind` (see the module docstring for each type's sugar)."""
    if kind == "any" or tok[:1] in ("[", "{", "'", '"'):
        return parse_literal(tok)
    parts = tok.split(":")
    if kind == "int":
        return int(tok)
    if kind in ("cgrid", "igrid"):
        rows = _parse_grid(tok, parts, rng, alpha)
        return [[int(x) for x in r] for r in rows] if kind == "igrid" else rows
    if kind in ("edges", "wedges"):
        return _parse_edges(tok, parts, rng, weighted=kind == "wedges")
    parsers = {
        "ints": _parse_ints,
        "ll": _parse_ints,
        "str": _parse_str,
        "strs": _parse_strs,
        "floats": _parse_floats,
        "tree": _parse_tree,
    }
    if kind not in parsers:
        raise ShorthandError(f"unknown type {kind}")
    return parsers[kind](tok, parts, rng, alpha)


def _fits(kind: str, val: object) -> bool:
    """Can a previous stage's output fill a field of this kind without an explicit `_`?"""
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return kind == "int"
    if isinstance(val, str):
        return kind == "str"
    if not isinstance(val, list):
        return False
    if all(isinstance(x, int) and not isinstance(x, bool) for x in val):
        return kind in ("ints", "ll", "floats")
    return kind == "strs" and all(isinstance(x, str) for x in val)


def _field_for(
    target: str, schema: dict[str, str], tok: str, pos: list[str], data: dict
) -> tuple[str, str]:
    """Which field a token fills: `name=value`, else the next unfilled positional field."""
    key, eq, val = tok.partition("=")
    if eq and key in schema:
        return key, val
    free = [f for f in pos if f not in data]
    if not free:
        raise ShorthandError(f"too many values for {target}: {tok!r}")
    return free[0], tok


def _bind_prev(schema: dict[str, str], data: dict, prev: object) -> None:
    """Auto-bind a chained stage's output to the first empty field it fits."""
    for f, kind in schema.items():
        if f not in data and _fits(kind, prev):
            data[f] = prev
            return


def build_input(  # noqa: PLR0913 - one value per pipeline input; all are needed
    target: str,
    tokens: list[str],
    sample: dict,
    prev: object | None,
    rng: random.Random,
    *,
    strict: bool = False,
    schema: dict[str, str] | None = None,
) -> dict:
    """Turn shorthand tokens into the solver's input dict.

    `schema` overrides SCHEMAS[target]; per-problem targets (lc-N) pass their derived schema.
    """
    schema = schema if schema is not None else SCHEMAS[target]
    data = dict(sample) if (not tokens or tokens == ["@"]) else {}
    alpha = GRID_ALPHA.get(target, "01")
    pos = list(schema)
    used_prev = False
    for tok in tokens:
        if tok == "@":
            data = {**sample, **data}
            continue
        field, raw = _field_for(target, schema, tok, pos, data)
        if raw == "_":
            if prev is None:
                raise ShorthandError("'_' used with no previous stage")
            data[field] = prev
            used_prev = True
        else:
            data[field] = parse_value(schema[field], raw, rng, alpha)
        if field in pos:
            pos.remove(field)
    if prev is not None and not used_prev:
        _bind_prev(schema, data, prev)
    _fill_missing(schema, data, sample, strict=strict and bool(tokens))
    return data


def _fill_missing(schema: dict[str, str], data: dict, sample: dict, *, strict: bool) -> None:
    """Fall back to the sample for unfilled fields (or fail when strict)."""
    missing = [f for f in schema if f not in data]
    if missing and strict:
        raise ShorthandError("missing value for: " + ", ".join(missing))
    for f in missing:
        data[f] = sample[f]
