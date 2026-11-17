#!/usr/bin/env python3
"""algopack — bundle the algo workbench into a single zero-dependency, offline self-installer.

The installer is suitable for pasting through a browser snippet expander (snipkey).

The runtime of the workbench is stdlib-only Python plus a few data files:

    <ALGO_HOME>/
      py3/        the Python package (algo.cli.main + solvers + comparators)
      registry/   algorithms.yml (+ problem-targets.yml)
      cases/      leetcode-*/case-1.{input,expected}.json
      shell/      bootstrap.sh / bootstrap.fish  (define the `algo` function)

`build` tars those four trees deterministically, gzips, base64-encodes, and
renders two paste-safe installer payloads (bash/zsh and fish). Each payload,
when evaluated at a shell prompt, decodes the embedded bundle into ALGO_HOME
(default /tmp/algo), extracts it, and sources the bootstrap so `algo` and the
`.a` alias are live in the current shell. No network, no pip, no deps beyond
python3 + base64 + tar + gzip (all standard on macOS and Linux).

`selftest` proves the round trip in a throwaway directory.

Everything here is Python stdlib only — in keeping with the workbench itself.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
SRC_ROOT = REPO_ROOT / "src"
DIST = REPO_ROOT / "dist"

# Trees that make up the runtime, relative to src/. Order is irrelevant; the
# tar is sorted deterministically below.
RUNTIME_TREES = ["py3", "registry", "cases", "shell"]

DEFAULT_TARGET = "/tmp/algo"  # noqa: S108 - user-overridable install dir, not a temp file
DEFAULT_CHORD_BASH = "Alt+Shift+KeyA"
DEFAULT_CHORD_FISH = "Alt+Shift+KeyF"

# Pure-ANSI clear (no dependency on `clear`/terminfo or $TERM): erase screen (2J),
# erase scrollback (3J), home the cursor (H). Hides the pasted bundle after it runs.
CLEAR_SUFFIX = "; printf '\\033[2J\\033[3J\\033[H'"


# ---------------------------------------------------------------------------
# Bundle construction
# ---------------------------------------------------------------------------


def _iter_runtime_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for tree in RUNTIME_TREES:
        base = SRC_ROOT / tree
        if not base.exists():
            raise SystemExit(f"error: expected runtime tree missing: {base}")
        files += [
            p
            for p in base.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")
        ]
    return sorted(files)


def build_bundle() -> bytes:
    """Return a reproducible .tar.gz of the runtime trees (arcnames relative to src/)."""
    files = _iter_runtime_files()
    raw = io.BytesIO()
    # mtime=0 + sorted members + normalized ownership => byte-identical output
    # for identical inputs.
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for f in files:
            arcname = str(f.relative_to(SRC_ROOT))
            info = tarfile.TarInfo(arcname)
            data = f.read_bytes()
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o755 if os.access(f, os.X_OK) else 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    gz = io.BytesIO()
    # mtime=0 in the gzip header too, for reproducibility.
    with gzip.GzipFile(fileobj=gz, mode="wb", compresslevel=9, mtime=0) as g:
        g.write(raw.getvalue())
    return gz.getvalue()


# ---------------------------------------------------------------------------
# Payload rendering
# ---------------------------------------------------------------------------


def _wrap(b64: str, width: int = 76) -> str:
    """Wrap base64 onto short lines.

    base64 -d ignores the embedded newlines, and interactive shells keep reading inside the
    open single quote, so every physical line stays well under the terminal canonical-input
    limit (~4096 B) that would otherwise truncate one giant pasted line.
    """
    return "\n".join(b64[i : i + width] for i in range(0, len(b64), width))


def render_bash(b64: str, target: str, *, clear: bool = False) -> str:
    """Render the bash/zsh installer payload.

    One logical line, no heredocs (survives WYSIWYG / rich-text insertion). The decoder
    flag is probed once so stdin is never half-consumed, and both GNU (`base64 -d`) and
    BSD/macOS (`base64 -D`) work.
    """
    return (
        f'ALGO_HOME="${{ALGO_HOME:-{target}}}"; mkdir -p "$ALGO_HOME"; '
        'if printf "" | base64 -d >/dev/null 2>&1; '
        'then _bd="base64 -d"; else _bd="base64 -D"; fi; '
        f"printf %s '{_wrap(b64)}' | $_bd | tar -xzf - -C \"$ALGO_HOME\"; unset _bd; "
        f'export ALGO_HOME; . "$ALGO_HOME/shell/bootstrap.sh"' + (CLEAR_SUFFIX if clear else "")
    )


def render_fish(b64: str, target: str, *, clear: bool = False) -> str:
    """Render the fish installer payload (same steps as render_bash)."""
    return (
        f"set -q ALGO_HOME; or set -gx ALGO_HOME {target}; mkdir -p $ALGO_HOME; "
        f'if printf "" | base64 -d >/dev/null 2>&1; set _bd -d; else; set _bd -D; end; '
        f"printf %s '{_wrap(b64)}' | base64 $_bd | tar -xzf - -C $ALGO_HOME; set -e _bd; "
        f"source $ALGO_HOME/shell/bootstrap.fish; function .a; algo $argv; end"
        + (CLEAR_SUFFIX if clear else "")
    )


_VSCODE_MODS = {"Ctrl": "ctrl", "Alt": "alt", "Shift": "shift", "Meta": "cmd"}


def _chord_to_vscode(combo: str) -> str:
    """Map a SnipKey combo (e.g. 'Ctrl+Shift+Digit1') to a VS Code key (e.g. 'ctrl+shift+1')."""
    parts = combo.split("+")
    key = parts[-1]
    if key.startswith("Digit"):
        key = key[len("Digit") :]
    elif key.startswith("Key"):
        key = key[len("Key") :].lower()
    else:
        key = key.lower()
    mods = [_VSCODE_MODS.get(p, p.lower()) for p in parts[:-1]]
    return "+".join([*mods, key])


def render_vscode_keybinding(bash_payload: str, combo: str) -> str:
    r"""Return a keybindings.json entry that types the installer into the focused terminal.

    Uses the built-in sendSequence command. The trailing newline is stripped so it drops
    the text at the prompt without auto-running (append a \r to args.text to run on trigger).
    """
    entry = {
        "key": _chord_to_vscode(combo),
        "command": "workbench.action.terminal.sendSequence",
        "args": {"text": bash_payload.rstrip("\n")},
        "when": "terminalFocus",
    }
    return json.dumps([entry], indent=2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_build(args: argparse.Namespace) -> None:
    """Build the bundle and every installer payload into dist/."""
    target = args.target
    bundle = build_bundle()
    b64 = base64.b64encode(bundle).decode("ascii")  # unwrapped single line

    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "algo-bundle.tar.gz").write_bytes(bundle)

    bash = render_bash(b64, target, clear=args.clear)
    fish = render_fish(b64, target, clear=args.clear)
    (DIST / "algo.install.sh").write_text(bash + "\n")
    (DIST / "algo.install.fish").write_text(fish + "\n")

    # Native (non-browser) targets that reuse the same bash payload:
    # iTerm2 snippet body == the bash payload; VS Code keybindings entry.
    iterm_body = bash + ("\n" if args.autorun else "")
    (DIST / "algo.iterm2-snippet.txt").write_text(iterm_body + "\n")
    vscode_payload = bash + ("\r" if args.autorun else "")
    (DIST / "algo.vscode-keybinding.json").write_text(
        render_vscode_keybinding(vscode_payload, args.chord_bash) + "\n"
    )

    # snipkey import file: combo -> {label, body}, matching storage.local shape.
    snippets = {
        args.chord_bash: {"label": "algo install (bash/zsh)", "body": bash, "submit": args.autorun},
        args.chord_fish: {"label": "algo install (fish)", "body": fish, "submit": args.autorun},
    }
    (DIST / "snipkey-snippets.json").write_text(json.dumps({"snippets": snippets}, indent=2) + "\n")

    manifest = {
        "target": target,
        "bundle_bytes": len(bundle),
        "base64_chars": len(b64),
        "bash_payload_chars": len(bash),
        "fish_payload_chars": len(fish),
        "files": [str(p.relative_to(SRC_ROOT)) for p in _iter_runtime_files()],
        "chords": {"bash": args.chord_bash, "fish": args.chord_fish},
    }
    (DIST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"bundle:        {len(bundle):>6} bytes  -> dist/algo-bundle.tar.gz")
    print(f"base64:        {len(b64):>6} chars")
    print(f"bash payload:  {len(bash):>6} chars  -> dist/algo.install.sh")
    print(f"fish payload:  {len(fish):>6} chars  -> dist/algo.install.fish")
    print(
        f"snipkey import:        -> dist/snipkey-snippets.json "
        f"({args.chord_bash} / {args.chord_fish})"
    )
    print("iterm2 snippet:        -> dist/algo.iterm2-snippet.txt")
    print(
        f"vscode keybinding:     -> dist/algo.vscode-keybinding.json "
        f"(key: {_chord_to_vscode(args.chord_bash)})"
    )
    print(f"target ALGO_HOME: {target}")


Check = tuple[str, bool, str]


def _run(argv: list[str], **kw: object) -> subprocess.CompletedProcess:
    """Run argv (argv[0] resolved on PATH) and capture text output; never raises on failure."""
    exe = shutil.which(argv[0]) or argv[0]
    return subprocess.run(  # noqa: S603 - fixed argv built by this script, no shell
        [exe, *argv[1:]], capture_output=True, text=True, check=False, **kw
    )


def _cli_checks(tmp: pathlib.Path, env: dict[str, str]) -> list[Check]:
    """Exercise the extracted CLI: targets, judge, search, p, check, pipe, complete, inputs."""
    cli = str(tmp / "py3" / "algo" / "cli" / "main.py")

    def run(*cli_args: str) -> subprocess.CompletedProcess:
        return _run([sys.executable, cli, *cli_args], env=env, stdin=subprocess.DEVNULL)

    checks: list[Check] = []
    r = run("targets")
    ok = r.returncode == 0 and "leetcode-347" in r.stdout
    checks.append(("algo targets", ok, r.stdout.strip().replace("\n", " ")[:60] + " ..."))
    r = run("judge", "leetcode-347")
    ok = r.returncode == 0 and '"status": "PASS"' in r.stdout
    checks.append(("algo judge leetcode-347", ok, "PASS" if ok else r.stderr.strip()[:80]))
    r = run("s", "-j", "--id", "connected components", "--top", "1")
    ok = r.returncode == 0 and '"id"' in r.stdout
    checks.append(("algo search --id 'connected components'", ok, r.stderr.strip()[:80]))
    r = run("p", "two sum")
    ok = r.returncode == 0 and "hash-map" in r.stdout.splitlines()[0]
    checks.append(("algo p 'two sum' -> hash-map", ok, r.stdout.strip()[:60] or r.stderr[:80]))
    r = run("check")
    checks.append(("algo check", r.returncode == 0, r.stdout.strip() or r.stderr.strip()[:200]))
    r = run("pipe", "leetcode-200")
    ok = r.returncode == 0 and r.stdout.strip() == "3"
    checks.append(("algo pipe leetcode-200 (no stdin -> sample)", ok, r.stderr.strip()[:80]))
    r = run("complete", "algos")
    ok = r.returncode == 0 and "bfs\tBreadth-First Search" in r.stdout
    checks.append(("algo complete algos", ok, r.stderr.strip()[:80]))
    gen = tmp / "gen"
    r = run("i", "[a: [1, 2]]", "[b: [3]]", "-a", "deepmerge", "-o", str(gen))
    r2 = _run([sys.executable, str(gen / "inputs.py")]) if r.returncode == 0 else r
    ok = r.returncode == 0 and json.loads(r2.stdout) == {"a": [1, 2], "b": [3]}
    detail = r2.stdout.strip() or r.stderr.strip()[:80]
    checks.append(("algo i [a:..] [b:..] -a deepmerge -> py inputs.py", ok, detail))
    return checks


def _shell_checks(tmp: pathlib.Path, env: dict[str, str]) -> list[Check]:
    """Source the bootstraps and completions the way the pasted installer does."""
    checks: list[Check] = []
    r = _run(
        [
            "bash",
            "-c",
            f'ALGO_HOME="{tmp}"; PS1=x; . "{tmp}/shell/bootstrap.sh"; '
            'COMP_WORDS=(.a g bf); COMP_CWORD=2; _algo_complete; echo "${COMPREPLY[*]}"',
        ],
        env=env,
    )
    detail = r.stdout.strip() or r.stderr.strip()[:80]
    checks.append(("bash completion: .a g bf<TAB> -> bfs", r.stdout.strip() == "bfs", detail))
    if shutil.which("fish"):
        comp = tmp / "shell" / "completions"
        script = (
            f'set -x ALGO_HOME "{tmp}"; source "{tmp}/shell/bootstrap.fish"; '
            f'source "{comp}/algo.fish"; complete -C ".a g bf"'
        )
        r = _run(["fish", "-c", script], env=env, stdin=subprocess.DEVNULL)
        detail = r.stdout.strip() or r.stderr.strip()[:80]
        checks.append(("fish completion: .a g bf<TAB> -> bfs", r.stdout.startswith("bfs"), detail))
    # Verify the bootstrap really defines a working `algo` function when sourced.
    boot = tmp / "shell" / "bootstrap.sh"
    script = (
        f'set -e; ALGO_HOME="{tmp}"; . "{boot}"; alias .a=algo 2>/dev/null; '
        "algo targets >/dev/null; type -t algo"
    )
    r = _run(["bash", "-c", script], env=env)
    ok = r.returncode == 0 and "function" in r.stdout
    detail = r.stdout.strip() or r.stderr.strip()[:80]
    checks.append(("source bootstrap.sh -> algo() defined + runs", ok, detail))
    return checks


def cmd_selftest(args: argparse.Namespace) -> None:
    """Extract the freshly-built bundle into a temp dir and exercise the CLI.

    Runs exactly as the pasted installer would — no network, no deps.
    """
    bundle = build_bundle()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="algopack-selftest-"))
    try:
        with tarfile.open(fileobj=io.BytesIO(gzip.decompress(bundle))) as tar:
            tar.extractall(tmp, filter="data")  # we just built it from our own src
        env = dict(os.environ, PYTHONPATH=str(tmp / "py3"))
        checks = _cli_checks(tmp, env) + _shell_checks(tmp, env)
        print(f"selftest sandbox: {tmp}\n")
        all_ok = True
        for name, ok, detail in checks:
            all_ok = all_ok and ok
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
            if not ok:
                print(f"         {detail}")
        print()
        if not all_ok:
            raise SystemExit("selftest: one or more checks FAILED")
        print("selftest: all checks PASSED")
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"(kept sandbox at {tmp})")


def main() -> None:
    """Entry point: `algopack build` or `algopack selftest`."""
    p = argparse.ArgumentParser(
        prog="algopack", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(required=True)

    b = sub.add_parser("build", help="build bundle + installer payloads into dist/")
    b.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"default ALGO_HOME baked into the payload (default: {DEFAULT_TARGET})",
    )
    b.add_argument(
        "--chord-bash",
        default=DEFAULT_CHORD_BASH,
        help=f"snipkey chord for the bash payload (default: {DEFAULT_CHORD_BASH})",
    )
    b.add_argument(
        "--chord-fish",
        default=DEFAULT_CHORD_FISH,
        help=f"snipkey chord for the fish payload (default: {DEFAULT_CHORD_FISH})",
    )
    b.add_argument(
        "--autorun",
        action="store_true",
        help="auto-run after paste: submit:true in snipkey import, trailing CR in the "
        "VS Code binding, trailing newline in the iTerm2 snippet",
    )
    b.add_argument(
        "--clear",
        action="store_true",
        help="append a terminal clear (screen + scrollback) to the payload so the pasted "
        "bundle is wiped after it runs",
    )
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("selftest", help="extract into a temp dir and exercise the CLI")
    s.add_argument("--keep", action="store_true", help="keep the sandbox dir for inspection")
    s.set_defaults(func=cmd_selftest)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
