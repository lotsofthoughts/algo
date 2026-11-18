# Algo Workbench

> Find the pattern, judge it, generate the code, feed it your inputs, chain it into the next algorithm —
> from one shell command. Stdlib-only Python, offline, YAML-driven.

An interview-prep workbench that maps problems to algorithms and turns any algorithm into a runnable,
importable Python file in seconds. 38 algorithm patterns, 173 indexed LeetCode problems, and a
99-problem study list where every problem has a solution verified against an independent reference.

- **Full CLI spec:** [docs/API.md](docs/API.md)
- **Worked examples (identify → judge → solve → chain):** [docs/cases/](docs/cases/README.md)
- **The 99-problem study list, with other uses of each technique:** [docs/study99.md](docs/study99.md)

---

## Install

**From the repo** (bash, zsh or fish):

```bash
source src/shell/bootstrap.sh      # or: source src/shell/bootstrap.fish
algo check                         # 38 algorithms, 173 problems (102 with verified solutions) ... OK
```

This defines `algo` and its alias `.a` (in zsh `.a` is `noglob algo`, so `[a: [1, 2]]` isn't globbed) and
loads tab completion for bash and fish.

**Anywhere, no clone, no network:** `mise run pack` writes a single paste-able installer to `dist/`
(`algo.install.sh` / `.fish`, plus snipkey, iTerm2 and VS Code bindings). Pasting it unpacks the workbench into
`$ALGO_HOME` (default `/tmp/algo`) and sources it. `python3 scripts/algopack.py selftest` proves the round trip.

Requirements: `python3` (3.12+). Nothing else at runtime.

| Env var | Default | Meaning |
| --- | --- | --- |
| `ALGO_HOME` | the repo's `src/` | Install root |
| `ALGO_TMP` | the current directory | Where `generate` / `inputs` write files (`-o DIR` overrides) |
| `ALGO_LANG` | `py3` | `go` runs the experimental Go backend (10 solvers, `solve` only) |

---

## The solving process

Every problem goes through the same four steps. Each has one command.

| Step | Question | Command |
| --- | --- | --- |
| **1. Identify** | Which problem is this, and what pattern does it use? | `.a p "<title, number, keywords or use case>"` |
| **2. Judge** | Is that pattern right *here*? What signals it, what rules it out? | `.a s -j --id "<symptoms>"` · `.a s --disqualifier "<constraint>"` |
| **3. Solve** | Give me the code, run on my inputs. | `.a i <values...> <algo>` → `python3 inputs.py` |
| **4. Chain** | Feed the answer into the next algorithm. | `.a r <algo> <values> then <algo> _ ...` |

```console
$ .a p "course order prerequisites" --top 2
 207* Course Schedule                    medium  -> topological-sort, dfs
 210  Course Schedule II                 medium  -> topological-sort

$ .a s -j --id "dependencies ordering" --top 1        # matched: ["dependencies", "ordering"]

$ .a i 4 1-0,2-0,3-1,3-2 topo                         # writes the library + inputs.py
generated /tmp/algo-demo/topological_sort.py
/tmp/algo-demo/inputs.py
$ python3 $ALGO_TMP/inputs.py
[0, 1, 2, 3]

$ .a r topo 4 1-0,2-0,3-1,3-2 then binary-search _ target=3
topological-sort in={"numCourses":4,"prerequisites":[[1,0],[2,0],[3,1],[3,2]]}  out=[0, 1, 2, 3]
binary-search    in={"nums":[0,1,2,3],"target":3}  out=3
3
```

Five complete walkthroughs (topological sort, Dijkstra, top-k, flood fill, coin-change DP), each ending in a chain:
**[docs/cases/](docs/cases/README.md)**.

---

## Command cheat-sheet

| Command | Does | Example |
| --- | --- | --- |
| `p` | Problem → algorithms. `*` = verified solution. `-u` other uses, `-l study99`, `-a ALGO`, `-j` | `.a p 875 -u` |
| `s` | Find algorithms. `--id` symptoms, `--disqualifier` constraints, `-p` example problems, `-j` | `.a s bfs -p` |
| `g` | Write the importable library `<id>.py` (to the cwd); `-p` prints it instead, writing nothing | `.a g dijkstra` · `.a g 2812 -p` |
| `i` | Write `inputs.py` (to the cwd) that calls the library on your values | `.a i 1,2,5 11 coin-change` |
| `r` | Run in-process, no files; `then` chains, `_` = previous output | `.a r top-k 5,5,1 1 then coin-change _ 11` |
| `sh` | Input fields and types for every algorithm; a word filters, a problem shows one target | `.a sh` · `.a sh sort` · `.a sh 875` |
| `u` | Real-world uses per algorithm; describe a need to get the algorithm and its problems | `.a u` · `.a u shortest distance between two zip codes` |
| `pipe` / `assert` / `judge` | JSON in → JSON out, compare, judge a sample | `.a judge leetcode-322` |
| `verify` | Differential-test the 99 study-list solutions | `.a verify --fetch` |
| `check` | Validate registry ↔ problems ↔ solvers ↔ schemas ↔ cases | `.a check` |

**Targets** are algorithms (`dijkstra`), solver keys (`leetcode-743`), or any of the 99 solved problems by number,
`lc-N` or title (`875`, `lc-875`, `koko`, `"trapping rain water"`). 36 of 38 algorithms and 109 of 173 indexed problems run.

```console
$ .a r 875 3,6,7,11 8                          # Koko Eating Bananas
4
$ .a r lc-2 2,4,3 5,6,4                        # linked lists in, linked list out
[7, 0, 8]
$ .a r 112 5,4,8,11,null,13,4,7,2,null,null,null,1 22   # a tree in level order
true
```

**Input shorthand** (full table in [API.md §6](docs/API.md#6-schemas-and-input-shorthand)):
`1,2,5` and `1..5` lists · `eat,tea` word lists · `abcabcbb` strings · `11000/00100` grids · `1-0,2-0` edges ·
`2-1:1` weighted edges · `3,9,null,7` trees · `rand:8:0-9`, `rand:4x5` random inputs · `[1, 2]`, `[k: v]` literals ·
`name=value` by field · `_` previous stage.

---

## Study list and verification

All 99 problems on the study list are mapped to LeetCode ids, patterns and **other uses of each
technique** ([docs/study99.md](docs/study99.md)). Each has a LeetCode-signature solution in
[src/py3/algo/leetcode/](src/py3/algo/leetcode/), differential-tested by `algo verify`:

| Compared against | Problems |
| --- | --- |
| [cnkyrpsgl/leetcode](https://github.com/cnkyrpsgl/leetcode) solutions (examples + 300 random inputs each) | 70 |
| Slow brute-force oracles (reference lacks the problem, or its solution is wrong) | 24 |
| SQL on sqlite with the example tables | 4 |
| Statistical check (randomised problem) | 1 |

```bash
.a verify --fetch            # clone the reference once (~/.cache/algo/leetcode-ref), then test all 99
.a verify 875 3886 -v        # a few problems, every failure printed
```

Three reference solutions turned out to be wrong (8, 772, 875); see [docs/study99.md](docs/study99.md).

---

## How it fits together

```text
registry/algorithms.yml   pattern: identification phrases, disqualifiers, representative problem
registry/problems.yml     problem → patterns (+ keywords, uses, list)          ← algo p
        │                                                                      ← algo s
        ▼
py3/algo/solutions.py     one solver per pattern: f(dict) -> JSON              ← algo g / i / r / pipe
py3/algo/shorthand.py     input schema per solver + shorthand parser
cases/<target>/           sample input + expected output                       ← algo judge
py3/algo/leetcode/        per-problem solutions (runnable as lc-N), specs, verifier  ← algo verify / r 875
```

Adding an algorithm, problem, solver or schema is a few lines each:
[API.md §7](docs/API.md#7-end-to-end-checklist-worked-example) walks through one end to end.

## Repository layout

```text
src/
  py3/algo/          Python package: cli/ (the `algo` command), solutions, shorthand, judge/, leetcode/
  registry/          algorithms.yml, problems.yml (problem-targets.yml is documentation only)
  cases/             judged sample inputs and expected outputs
  shell/             bootstrap.sh / .fish and tab completions
  go/                experimental Go backend
  python_template/   project-template CLI kept for the packaging, CI and release scaffolding
docs/                API.md (CLI spec), cases/ (walkthroughs), study99.md
scripts/algopack.py  builds the offline installer (`mise run pack`)
tests/               pytest suite for the template package
```

---

## Development

Tooling: UV, Ruff, Ty, pytest and Mise; every task is a script in `.mise/tasks/`.

```bash
mise run install           # uv sync
mise run lint:fix          # ruff check --fix (src/ tests/ scripts/)
mise run fmt               # ruff format
mise run typecheck         # ty check src/
mise run test              # pytest
mise run verify:leetcode   # algo verify --fetch
mise run pack              # build dist/ installers
mise run ci:all            # full pipeline
```

**Git flow is rebase-only:** `feature → develop → main → tag`. `mise run vcs:rebase` keeps a branch current,
`vcs:integrate` lands it on `develop`, `vcs:release` rebases `main` onto `develop`, then `bump:patch` and
`tag:push` cut a release. Hooks in `config/githooks/hooks` run ruff, a complexity check (lizard) and the tests.
Contributor and agent rules: [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md).

> **macOS note:** Homebrew's `lizard` is a file compressor, not the complexity analyzer the pre-commit hook
> needs; install the analyzer with `uv tool install lizard`. If `python -m python_template` stops importing
> after `uv sync`, macOS has flagged `.venv/*.pth` hidden (Python 3.13+ skips those):
> `chflags nohidden .venv/lib/python3.*/site-packages/*.pth`.

## License

MIT
