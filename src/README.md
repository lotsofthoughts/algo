# `src/`: the workbench runtime tree

This directory is what `ALGO_HOME` points at, and what `mise run pack` bundles into the offline installer
(`py3/`, `registry/`, `cases/`, `shell/`). Project overview, install and the solving process:
[../README.md](../README.md). Full CLI spec: [../docs/API.md](../docs/API.md).

| Path | Holds | Docs |
| --- | --- | --- |
| `py3/algo/cli/main.py` | The `algo` command (search, problems, generate, inputs, run, verify, check, …) | [API §2](../docs/API.md#2-command-reference) |
| `py3/algo/solutions.py` | One solver per algorithm: `f(dict) -> JSON`, registered in `SOLVERS` | [API §5](../docs/API.md#5-solvers) |
| `py3/algo/shorthand.py` | Input schema per solver and the shorthand parser (`1,2`, `11/00`, `1-2:3`, `rand:`) | [API §6](../docs/API.md#6-schemas-and-input-shorthand) |
| `py3/algo/judge/` | Comparators for `judge` / `assert` | [API §5](../docs/API.md#5-solvers) |
| `py3/algo/leetcode/` | Per-problem solutions for the 99-problem study list, test specs, `verify` | [API §5.1](../docs/API.md#51-per-problem-solutions-and-algo-verify) |
| `registry/algorithms.yml` | Patterns: identification phrases, disqualifiers, representative problem | [API §3](../docs/API.md#3-the-algorithm-registry) |
| `registry/problems.yml` | Problem → patterns, keywords, uses, list | [API §4](../docs/API.md#4-the-problem-index) |
| `cases/<target>/` | Judged sample input and expected output | [API §5](../docs/API.md#5-solvers) |
| `shell/` | `bootstrap.sh` / `.fish` (define `algo` and `.a`) and tab completions | below |
| `go/` | Experimental Go backend (`ALGO_LANG=go`, `solve` only) | |
| `python_template/` | Template CLI kept for packaging, CI and release scaffolding (not part of the runtime) | |

## Principles

- Shell functions are thin launchers; behaviour comes from `ALGO_HOME`, `ALGO_LANG`, `ALGO_TMP`.
- Registries are declarative YAML, parsed by small stdlib loaders (no PyYAML), so it runs anywhere.
- Solvers read JSON and emit JSON; judging and comparators are separate from the algorithms.
- Data structures are decoupled from problem adapters.

## Shell completions

Tab completion for `algo` and `.a` (subcommands, flags, algorithm names, targets, comparators) lives in
`shell/completions/` and loads automatically from `bootstrap.sh` (interactive bash) and `bootstrap.fish`.
Algorithm names come live from the registry via the hidden `algo complete <kind>` helper. zsh is not covered yet.

```fish
# optional, fish: load completions without sourcing bootstrap
ln -s "$ALGO_HOME/shell/completions/algo.fish" ~/.config/fish/completions/algo.fish
```

```bash
# optional, bash: load from ~/.bashrc without the full bootstrap
source "$ALGO_HOME/shell/completions/algo.bash"
```

When you add a subcommand or flag in `main.py`, add it to **both** `algo.bash` and `algo.fish`.
