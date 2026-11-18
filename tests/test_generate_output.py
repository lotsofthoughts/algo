"""`algo g` / `algo i` output location (cwd by default) and `algo g -p` (print, write nothing)."""

from __future__ import annotations

import argparse
import pathlib

import pytest
from algo.cli.main import cmd_generate, cmd_inputs, tmp_dir


@pytest.fixture
def in_cwd(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Run in an empty directory with $ALGO_TMP unset."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ALGO_TMP", raising=False)
    return tmp_path


def generate(query: str, *, out_dir: str | None = None, print_: bool = False) -> None:
    cmd_generate(argparse.Namespace(query=query.split(), out_dir=out_dir, print=print_))


def test_default_output_dir_is_cwd(in_cwd: pathlib.Path) -> None:
    assert tmp_dir() == in_cwd.resolve()


def test_algo_tmp_and_flag_override_cwd(
    in_cwd: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ALGO_TMP", str(in_cwd / "env"))
    assert tmp_dir() == (in_cwd / "env").resolve()
    assert tmp_dir(str(in_cwd / "flag")) == (in_cwd / "flag").resolve()


def test_generate_writes_into_cwd(in_cwd: pathlib.Path, capsys: pytest.CaptureFixture) -> None:
    generate("lc-875")
    path = pathlib.Path(capsys.readouterr().out.strip())
    assert path.parent == in_cwd.resolve()
    assert path.is_file()


def test_inputs_writes_into_cwd(in_cwd: pathlib.Path) -> None:
    cmd_inputs(argparse.Namespace(tokens=["3,6,7,11", "8"], algo_opt="lc-875", out_opt=None))
    assert (in_cwd / "inputs.py").is_file()


@pytest.mark.parametrize("query", ["bfs", "lc-875"])
def test_print_writes_nothing(
    query: str, in_cwd: pathlib.Path, capsys: pytest.CaptureFixture
) -> None:
    generate(query, print_=True)
    code = capsys.readouterr().out
    assert list(in_cwd.iterdir()) == []
    compile(code, query, "exec")  # complete, valid Python
    assert 'if __name__ == "__main__":' in code


def test_print_matches_written_file(in_cwd: pathlib.Path, capsys: pytest.CaptureFixture) -> None:
    generate("bfs", print_=True)
    printed = capsys.readouterr().out
    generate("bfs")
    path = pathlib.Path(capsys.readouterr().out.strip())
    assert path.read_text() == printed
