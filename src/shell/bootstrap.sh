#!/usr/bin/env bash
# 12-factor shell shim: behavior controlled by env vars, no hardcoded machine state.
# ALGO_HOME defaults to the checked-out repo root when sourced locally.
# Resolve the install root at source time (works in bash and zsh).
if [ -z "${ALGO_HOME:-}" ]; then
  if [ -n "${BASH_VERSION:-}" ]; then _algo_src="${BASH_SOURCE[0]}"; else _algo_src="${(%):-%x}"; fi
  ALGO_HOME="$(cd "$(dirname "$_algo_src")/.." && pwd)"; export ALGO_HOME
  unset _algo_src
fi
algo() {
  local root="$ALGO_HOME"
  local lang="${ALGO_LANG:-py3}"
  case "$lang" in
    go) (cd "$root/go" && go run ./cmd/algo "$@") ;;
    py3|python|python3) PYTHONPATH="$root/py3" python3 "$root/py3/algo/cli/main.py" "$@" ;;
    *) echo "Unsupported ALGO_LANG=$lang" >&2; return 2 ;;
  esac
}
# zsh would try to glob [a: [1, 2]] ("no matches found"); noglob passes it through.
if [ -n "${ZSH_VERSION:-}" ]; then alias .a='noglob algo'; else alias .a=algo; fi
# Tab completion (interactive bash only; fish loads its own in bootstrap.fish).
if [ -n "${BASH_VERSION:-}" ] && [ -n "${PS1:-}" ] && [ -f "$ALGO_HOME/shell/completions/algo.bash" ]; then
  . "$ALGO_HOME/shell/completions/algo.bash"
fi
