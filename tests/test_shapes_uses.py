"""`algo shapes` (all algorithms, word filter) and `algo uses` (need -> algorithm + problems)."""

from __future__ import annotations

import argparse

import pytest
from algo.cli import uses
from algo.cli.main import cmd_shapes, cmd_uses, load_problems, load_registry

REG = load_registry()
PROBLEMS = load_problems()


def shapes(capsys: pytest.CaptureFixture, *query: str) -> list[str]:
    cmd_shapes(argparse.Namespace(query=list(query)))
    return capsys.readouterr().out.splitlines()


def test_shapes_lists_every_algorithm(capsys: pytest.CaptureFixture) -> None:
    ids = [line.split()[0] for line in shapes(capsys) if not line.startswith("(")]
    assert ids == [i["id"] for i in REG]


def test_shapes_word_filters(capsys: pytest.CaptureFixture) -> None:
    ids = [line.split()[0] for line in shapes(capsys, "sort")]
    assert ids == ["topological-sort", "cyclic-sort", "sorting"]


@pytest.mark.parametrize(("query", "first"), [("875", "lc-875"), ("koko", "lc-875")])
def test_shapes_single_target_detail(capsys: pytest.CaptureFixture, query: str, first: str) -> None:
    out = shapes(capsys, query)
    assert out[0].split()[0] == first
    assert any("sample:" in line for line in out)


def test_every_algorithm_has_uses() -> None:
    assert all(i.get("uses") for i in REG), [i["id"] for i in REG if not i.get("uses")]


def test_tokens_fold_synonyms_stems_and_stopwords() -> None:
    assert uses.tokens("Finding the smallest integers") == {"min", "number"}
    assert uses.tokens("zip codes") == uses.tokens("zip code") == {"location", "code"}
    assert uses.tokens("chessboard") == {"chess", "board"}


@pytest.mark.parametrize(
    ("need", "algo", "problem"),
    [
        ("shortest distance between two zip codes", "dijkstra", 743),
        ("place queens on a chess board", "backtracking", 51),
        ("searching a tree", "tree-dfs", None),
        ("smallest missing positive integer", "cyclic-sort", 41),
        ("autocomplete", "trie", 208),
        ("running median of a stream", "two-heaps", 295),
        ("fewest coins to make change", "dp-1d", 322),
        ("course prerequisites order", "topological-sort", None),
        ("merge overlapping meetings", "intervals", 56),
    ],
)
def test_need_finds_optimal_algorithm(need: str, algo: str, problem: int | None) -> None:
    best = uses.search(need, REG, PROBLEMS)[0]
    assert best.algo["id"] == algo
    assert len(best.problems) >= 1
    assert all(p["algorithms"][0] == algo for p in best.problems)  # it is their primary pattern
    if problem is not None:
        assert problem in [p["id"] for p in best.problems]


def test_empty_query_lists_every_algorithm_with_problems() -> None:
    found = uses.search("", REG, PROBLEMS)
    assert [m.algo["id"] for m in found] == [i["id"] for i in REG]
    with_problems = [m for m in found if m.algo["id"] not in {"add", "deepmerge"}]
    assert all(m.problems for m in with_problems)


def test_nonsense_finds_nothing(capsys: pytest.CaptureFixture) -> None:
    assert uses.search("qwertyuiop zxcvb", REG, PROBLEMS) == []
    with pytest.raises(SystemExit):
        cmd_uses(argparse.Namespace(query=["qwertyuiop"], top=5, problems_top=3, json=False))


def test_uses_cli_text(capsys: pytest.CaptureFixture) -> None:
    cmd_uses(
        argparse.Namespace(
            query=["shortest", "distance", "between", "two", "zip", "codes"],
            top=5,
            problems_top=3,
            json=False,
        )
    )
    out = capsys.readouterr().out
    assert out.startswith("dijkstra")
    assert "zip codes" in out
    assert "743" in out
