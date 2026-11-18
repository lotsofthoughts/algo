# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- LeetCode 88 (Merge Sorted Array, two-pointers: fill from the back in place, O(1) extra) and 23 (Merge k
  Sorted Lists, heap-topk: `heapq.merge` over a `walk()` generator per list, O(N log k)), each with test spec,
  `uses`, and a runnable `lc-N` target. Both verified against cnkyrpsgl/leetcode.
- Shorthand type `lls` (list of linked lists: `1,4,5/1,3,4/2,6`), and in-place targets: a solution annotated
  `-> None` returns its mutated first argument (`algo r 88 1,2,3,0,0,0 3 2,5,6 3` -> `[1, 2, 2, 3, 5, 6]`).
- LeetCode 387 (First Unique Character in a String, hash-map): verified solution, test spec, `uses`, and a
  runnable `lc-387` target for `run`, `generate`, `inputs`, `shapes` and `uses`. 136 (Single Number) is now
  also indexed under hash-map, with counting keywords ("value whose count is 1"); XOR stays the solution.
- `algo sh <problem title>` (e.g. `algo sh single number`) shows that problem instead of loose tag matches.
- `algo uses` (`u`): common real-world uses for every algorithm; `algo u <need>` (e.g. "shortest distance
  between two zip codes") ranks the algorithms that fit and lists the problems each is the optimal pattern
  for. Backed by a new required `uses` field on all 38 registry entries (`algo check` enforces it).
- `algo g -p` / `--print`: print the generated library to stdout instead of writing a file.
- **Every solved problem is runnable:** `lc-N` targets for all 99 study-list solutions in `generate`, `inputs`,
  `run`, `pipe` and `shapes` (`algo r 875 3,6,7,11 8`, `algo g 2812`). Schemas are derived from each solution's
  signature; design, SQL, 278 and 528 have adapters. Problems resolve by number, `lc-N` or title.
- Algorithms without a solver run their representative problem's solution (or the first solved problem they are
  primary for): 36 of 38 algorithms and 106 of 171 indexed problems are now runnable (was 13 and 11).
- Shorthand types `strs`, `floats`, `ll` (linked list) and `tree` (level order with `null`).
- `algo sh <name>` shows one target's fields, sample, and which problem it runs.
- `tests/test_problem_targets.py`: every target's sample and every generated library (run with `python -I`).

### Changed

- `algo shapes` lists all 38 algorithms (was only the 13 with dedicated solvers), noting which problem
  each runs; `algo sh <word>` filters (`algo sh sort` → topological-sort, cyclic-sort, sorting).
- `algo g` and `algo i` write to the current directory by default (was the system temp dir);
  `$ALGO_TMP` and `-o DIR` still override it.

### Fixed

- `mise run test` (and `test:cov`, `test:watch`) use `uv run`, so pytest comes from the project venv.
- `algo i -a X ...` and `-o DIR` now work as the first argument.
- A solver error in `algo r` / `algo pipe` prints one line and exits 1 instead of a traceback.
- `ci:all` lints `scripts/` like the lint tasks do.

- README rewritten as the **Algo Workbench** project README (install, the four-step solving process,
  command cheat-sheet, verification, layout, development), linking `docs/API.md` for the full spec.
- `docs/cases/`: five worked examples (topological sort, Dijkstra, top-k, flood fill, coin-change DP), each
  going identification → judging → solving with `.a i` → chaining, using real CLI output.
- Module docstrings for the `algo` CLI, comparators and every `algo.*` package (placeholders say what they are
  reserved for); header comments on the Go backend, `algorithms.yml`, `problem-targets.yml` and `bootstrap.fish`.
- `src/README.md` reduced to a map of the runtime tree.

- `study99` list: all 99 problems from `request.md` mapped to LeetCode ids in `registry/problems.yml`, each with
  primary/alternative patterns and a new `uses` field (other places the technique applies). Table: `docs/study99.md`.
- Per-problem solutions for all 99 (`src/py3/algo/leetcode/`), with test specs, brute-force oracles and SQL fixtures.
- `algo verify` / `mise run verify:leetcode`: differential testing against cnkyrpsgl/leetcode (70 problems),
  brute force (24), sqlite (4) and a distribution check (1). Found 3 wrong reference solutions (8, 772, 875).
- New registry patterns: `binary-search-answer`, `heap`, `sorting`, `rolling-hash`, `math`, `simulation`, `design`, `sql`.
- `algo p -u` (print other uses), `algo p -l study99` (filter by list), `*` marker for problems with a verified
  solution, and search over `uses`. `algo check` now requires every `study99` problem to have a solution and spec.

## [0.1.0] - 2026-04-12

### Added

- `algo g -p` / `--print`: print the generated library to stdout instead of writing a file.
- Initial template release
- UV package management with `uv sync`
- Ruff linting and formatting configuration
- Ty type checking integration
- pytest test suite with coverage reporting
- Mise task runner with all tasks as executable file tasks in `.mise/tasks/`
- PyInstaller binary compilation (`mise run compile`)
- Cross-platform release workflow (Linux AMD64/ARM64, macOS ARM64/AMD64, Windows AMD64)
- GitHub Advanced Security (GHAS) with CodeQL scanning
- Dependabot configuration for Python deps and GitHub Actions
- Branch protection ruleset automation via `mise run vcs:protect`
- Required status checks: lint, typecheck, test, security
- Git hooks: pre-commit (ruff), pre-push (tests + main protection), commit-msg (Conventional Commits)
- Hooks sync from orchestras/git-hooks (`mise run hooks:sync`)
- Semver bump tasks with git tag creation
- Rebase-only workflow enforcement
- Dev Container configuration
- AGENTS.md for AI coding assistant instructions

[Unreleased]: https://github.com/orchestras/python3/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/orchestras/python3/releases/tag/v0.1.0
