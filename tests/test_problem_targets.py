"""Per-problem targets (lc-N): every study-list solution runs via the CLI layer and as a library."""

from __future__ import annotations

import json
import pathlib
import random
import subprocess
import sys

import pytest
from algo.cli.main import resolve_target
from algo.leetcode import runnable
from algo.shorthand import ShorthandError, build_input, parse_value


def rng() -> random.Random:
    """Seeded generator for shorthand parsing (reproducible test inputs, not crypto)."""
    return random.Random(0)  # noqa: S311


KEYS = sorted(runnable.targets(), key=lambda k: int(k.removeprefix("lc-")))


def test_every_solution_is_a_target() -> None:
    assert len(KEYS) == 99


@pytest.mark.parametrize("key", KEYS)
def test_sample_reproduces_catalog_example(key: str) -> None:
    got = runnable.run(key, runnable.sample(key))
    assert runnable.matches_expected(key, got), (got, runnable.expected(key))


@pytest.mark.parametrize("key", KEYS)
def test_generated_library_is_standalone(key: str, tmp_path: pathlib.Path) -> None:
    t = runnable.targets()[key]
    path = tmp_path / f"{t.lib}.py"
    path.write_text(runnable.library_source(key, f"{t.title} — {key}", str(path)))
    # -I: isolated mode, so only the generated file (not the repo) is importable.
    proc = subprocess.run(  # noqa: S603 - runs a file this test just generated
        [sys.executable, "-I", str(path)], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr
    expected = json.loads(json.dumps(runnable.run(key, runnable.sample(key)), default=repr))
    assert json.loads(proc.stdout) == expected


@pytest.mark.parametrize(
    ("query", "target"),
    [
        ("875", "lc-875"),
        ("lc-875", "lc-875"),
        ("lc875", "lc-875"),
        ("koko", "lc-875"),  # unique title prefix
        ("trapping rain water", "lc-42"),
        ("binary-search-answer", "lc-875"),  # algorithm without a solver -> its problem
        ("two sum", "leetcode-1"),  # existing per-algorithm solver wins
        ("200", "leetcode-200"),  # bare number prefers the existing solver
        ("lc-200", "lc-200"),  # lc- always means the per-problem solution
        ("bfs", "leetcode-994"),
        ("tree-dfs", "lc-100"),  # representative (104) unsolved -> first problem it's primary for
    ],
)
def test_resolve_target(query: str, target: str) -> None:
    found = resolve_target(query)
    assert found is not None
    assert found[1] == target


def test_resolve_unknown_problem() -> None:
    assert resolve_target("99999") is None


@pytest.mark.parametrize(
    ("kind", "token", "value"),
    [
        ("strs", "eat,tea,tan", ["eat", "tea", "tan"]),
        ("floats", "0.5,0.25", [0.5, 0.25]),
        ("ll", "2,4,3", [2, 4, 3]),
        ("tree", "3,9,null,7", [3, 9, None, 7]),
    ],
)
def test_new_shorthand_types(kind: str, token: str, value: object) -> None:
    assert parse_value(kind, token, rng()) == value


def test_build_input_with_derived_schema() -> None:
    schema = runnable.targets()["lc-2"].schema
    data = build_input("lc-2", ["2,4,3", "5,6,4"], {}, None, rng(), schema=schema)
    assert runnable.run("lc-2", data) == [7, 0, 8]


def test_build_input_rejects_extra_values() -> None:
    schema = runnable.targets()["lc-69"].schema
    with pytest.raises(ShorthandError):
        build_input("lc-69", ["4", "5"], {}, None, rng(), schema=schema)
