# API.md — extending the workbench

How the registry, problem index, solvers and schemas fit together, how to add each, and what exists
today. The inventory tables in §8 were generated from the live registry on 2026-11-17; run
`algo check` after any change to keep everything consistent.

New here? Start with the [README](../README.md) for install and the four-step solving process, and
[cases/](cases/README.md) for five worked examples. This file is the reference.

Contents: [1 Mental model](#1-mental-model) · [2 Commands](#2-command-reference) ·
[3 Registry](#3-the-algorithm-registry) · [4 Problem index](#4-the-problem-index) ·
[5 Solvers](#5-solvers) · [5.1 Per-problem solutions](#51-per-problem-solutions-and-algo-verify) · [6 Schemas](#6-schemas-and-input-shorthand) ·
[7 Checklist](#7-end-to-end-checklist-worked-example) · [8 Inventory](#8-current-inventory) · [9 Gaps](#9-gaps)

---

## 1. Mental model

| Concept | Lives in | What it is |
|---|---|---|
| **Algorithm** (a.k.a. pattern) | `src/registry/algorithms.yml` | A technique: `bfs`, `two-pointers`, `dp-knapsack`. Searchable by the symptoms in a problem statement. |
| **Problem** | `src/registry/problems.yml` | A LeetCode problem mapped to one or more algorithms (first = primary), plus other `uses` of the technique. |
| **Per-problem solution** | `src/py3/algo/leetcode/` | LeetCode-signature solution + test `Spec`, differential-tested by `algo verify` (§5.1). |
| **Solver** | `src/py3/algo/solutions.py` | A Python function `f(data: dict) -> result`. Registered in `SOLVERS`. |
| **Schema** | `src/py3/algo/shorthand.py` (`SCHEMAS`) | Ordered `field: type` list for a solver's input; powers `algo i` / `algo r` shorthand. |
| **Sample / case** | `src/cases/<target>/` (or `SAMPLES`) | Known-good input and expected output, used by `judge`, `generate` and defaults. |
| **Target** | key such as `leetcode-200` or `add` | The string that ties solver + schema + case together. |

The path from "I have a problem" to a running solution:

```
algo p "two sum"        # problem -> algorithm(s):   1  Two Sum  easy  -> hash-map
algo s hash-map -p      # algorithm -> its identifying phrases and example problems
algo g hash-map         # writes ./hash_map.py   (importable: from hash_map import solve)
algo g hash-map -p      # prints that code instead; writes nothing
algo i 2,7,11,15 9 hash-map && python3 inputs.py     # -> [0, 1]
```

**How an algorithm finds its solver.** The registry entry's `leetcode: { id: N, ... }` field decides it:
the solver key is `leetcode-N`. An entry with no `leetcode` field uses its own id (`add`, `deepmerge`).
One algorithm therefore maps to exactly one solver — the solver for its *representative* problem.
(`bfs` → `leetcode-994`, even though 5 problems use BFS.)

**Problems are targets too.** Every solved study-list problem N is runnable as `lc-N` (§5.1), so
`.a r 875 3,6,7,11 8`, `.a g "trapping rain water"` and `.a i -a lc-2 2,4,3 5,6,4` all work. An algorithm with no
`SOLVERS` entry runs its representative problem's solution, else the lowest-numbered solved problem whose primary
pattern it is (`.a sh tree-dfs` → `runs: lc-100 Same Tree`). Only `two-heaps` and `trie` still report
"in the registry but has no solver yet".

Name resolution order: solver key (`leetcode-200`) → problem number (`lc-875` is always the per-problem
solution; a bare `200` prefers an existing `leetcode-200` solver) → exact algorithm id → problem title (exact, or
a unique prefix such as `koko`) → fuzzy algorithm match. Multi-word names need quotes in `run`/`inputs`.

---

## 2. Command reference

`algo` is the shell function from `shell/bootstrap.sh`; `.a` is its alias (in zsh, `.a` is
`noglob algo`, so `[a: [1, 2]]` is not glob-expanded). Env: `ALGO_HOME` (install root),
`ALGO_LANG` (`py3` default), `ALGO_TMP` (output dir; default the current directory).

| Command (alias) | Purpose | Example |
|---|---|---|
| `search` (`s`) | Find **algorithms**. Plain `id  name` list; `-j` full JSON; `-p` also list example problems; `--top N`. | `.a s graph` · `.a s bfs -p` |
| | Search only by symptoms / only by disqualifiers. | `.a s --id "shortest path"` · `.a s --disqualifier "negative weights"` |
| `problems` (`p`) | Find **problems** by title, number, keywords or uses → algorithms. `-a ALGO` filters; `-l study99` limits to a list; `-u` prints other uses; `-j` JSON; no query lists all. `*` after the id = verified solution exists. | `.a p "two sum"` · `.a p 200` · `.a p -a dijkstra` · `.a p 875 -u` |
| `generate` (`g`) | Write the algorithm library `<id>.py` (importable; also runnable on its sample). A problem target writes a standalone `lc<N>_<name>.py` with its helpers and node types inlined. `-o DIR` (default `$ALGO_TMP`, else the cwd); `-p` prints the code to stdout and writes nothing. | `.a g bfs` · `.a g 2812` · `.a g bfs -p \| less` |
| `inputs` (`i`) | Write `inputs.py` (same output dir as `generate`) that imports the library and calls `solve(...)`. Generates the library first if missing (never overwrites). Target = last bare word or `-a` (a bare number at the end is a value: use `lc-N` or `-a N`). | `.a i 1 2 add` · `.a i -a 875 3,6,7,11 8` |
| `run` (`r`) | Run in-process with shorthand input, no files. Chain stages with `then`; `_` = previous output. A solver error prints one line and exits 1. | `.a r topo 4 1-0,2-0 then binary-search _ target=2` · `.a r 22 3 then 14 _` |
| `shapes` (`sh`) | Input fields and types for **every algorithm** (`(runs lc-N)` when it runs a problem's solution; `(no solver yet)` otherwise). A word filters by id/name/category (`sort` → topological-sort, cyclic-sort, sorting), falling back to identification tags; a problem number, solver key or a single match shows that target's fields, sample and the problem it runs. | `.a sh` · `.a sh sort` · `.a sh 875` |
| `uses` (`u`) | **Real-world uses → algorithm + problems.** No query: every algorithm with its `uses` and its top problems. With a described need, ranks algorithms (default top 5, weak matches dropped) and shows the matching uses and the problems that algorithm is the primary (optimal) pattern for. Words are stemmed, a few synonyms fold together (zip code/city/address → location; distance/route/path → route; smallest/minimum → min) and rare words weigh more. `--top N`, `-p N` problems each, `-j` JSON. | `.a u` · `.a u shortest distance between two zip codes` · `.a u chess board` |
| `pipe` | JSON in → solver → JSON out, for pipelines. Input from `--input FILE`, piped stdin, or the sample case when stdin is a terminal. | `.a pipe leetcode-347 -i in.json \| .a assert --expected out.json --comparator unordered-array` |
| `judge` | Run a target's sample through its solver and compare to the expected file. | `.a judge leetcode-200` |
| `assert` | Compare JSON from stdin/`--actual` against `--expected` with a comparator. | see `pipe` |
| `targets` | List judged targets. | `.a targets` |
| `check` | Validate registry ↔ problems ↔ solvers ↔ schemas ↔ cases, and that every `study99` problem has a solution + test spec. Exit 1 on errors. | `.a check` |
| `verify` | Differential-test the per-problem solutions against [cnkyrpsgl/leetcode](https://github.com/cnkyrpsgl/leetcode), brute-force oracles and the LeetCode examples (§5.1). `--fetch` clones the reference to `~/.cache/algo/leetcode-ref`; `-n` random cases (300); `--seed`; `-v`; `-j`. | `.a verify --fetch` · `.a verify 875 3886 -v` |

> **`solve` was renamed `pipe`.** `solve` collided conceptually with the `s` shortcut, and — worse — it
> hung when run without `--input` because it waited on an empty terminal stdin. `pipe` falls back to the
> sample case instead. (The experimental Go backend, `ALGO_LANG=go`, still exposes only `solve`.)

Tab completion for bash and fish lives in `src/shell/completions/` (see `src/README.md`). When you add a
subcommand or flag in `main.py`, add it to **both** `algo.bash` and `algo.fish`; algorithm/target names
need no change — they come from the hidden `algo complete {algos|runnable|judged|comparators}` command.

Algorithm names are resolved leniently: exact id → fuzzy match on id/name/category/problem title. So
`.a g topo`, `.a g "two sum"` and `.a g leetcode-200` all work.

---

## 3. The algorithm registry

File: `src/registry/algorithms.yml`. One entry per algorithm/pattern.

```yaml
algorithms:
  - id: hash-map
    name: Hash Map Lookup
    category: arrays-hashing
    leetcode: { id: 1, title: Two Sum }
    data_structures: [hash map, set, array]
    identification: [pair sum, complement lookup, frequency count, group by key, duplicates, membership check]
    uses: [find two numbers that add up to a target, deduplicate records by key, count word frequencies]
    disqualifiers: [need sorted order, memory constrained, need range queries]
    comparator: exact
```

| Field | Required | Used for |
|---|---|---|
| `id` | yes | Unique kebab-case slug. Becomes the library filename (`hash_map.py`) and the key everywhere else. |
| `name` | yes | Human name; searched and displayed. |
| `category` | yes | Grouping; searched (strong match). |
| `leetcode` | no | Representative problem. **Determines the solver key** (`leetcode-<id>`). Omit for non-LeetCode utilities. |
| `data_structures` | yes | Weak search signal (`s --id`). |
| `identification` | yes | **The most important field.** Phrases that appear in problem statements / constraints that signal this algorithm. Drives `s --id "..."`. |
| `uses` | yes | Everyday tasks and real-world problems it solves ("driving directions between two zip codes", "place n queens on a chess board"). Drives `algo uses`; `algo check` fails on an entry without it. |
| `disqualifiers` | yes | Phrases that rule it out. Drives `s --disqualifier "..."`. |
| `comparator` | yes | Documentation of the expected comparator. *Not read by code today* — the judged comparator lives in `TARGETS` (§5). |

**Parser rules** (the loader is a deliberately tiny regex parser, not PyYAML — it is stdlib-only so it
can ship in the offline installer):

- Each entry starts with a line exactly `  - id: <id>` (two spaces, dash). Fields are indented further, one per line.
- Lists are **inline**: `[a, b, c]`, separated by `", "`. No nested brackets, and **no commas inside an item**. Empty `[]` is allowed.
- `leetcode:` must be exactly `{ id: <int>, title: <text> }`.
- No multi-line values; unknown fields are ignored.

**Writing good `identification` phrases.** Search scores lowercase words longer than 2 characters, and a
whole-phrase hit counts double. Write 4–8 phrases in the words a problem statement would use ("minimum
minutes", "no adjacent", "k-th largest"), not abstract descriptions. Put the things that make you
reject it in `disqualifiers`.

**Writing good `uses`.** Describe the task the way someone would ask for it, not the technique: "find the
smallest missing positive integer", "rate limit requests per minute". 5–8 concrete phrases; the
problems the algorithm is primary for (§4) add their titles, keywords and `uses` automatically.

**To add an algorithm:** append an entry → add the problems that use it to `problems.yml` (§4) → `algo check`.
It is now searchable (`.a s`, `.a p`). It becomes *runnable* only once it has a solver (§5) and a schema (§6).

---

## 4. The problem index

File: `src/registry/problems.yml`. One problem per line:

```yaml
  - { id: 1, title: Two Sum, difficulty: easy, algorithms: [hash-map], keywords: [pair sum, complement lookup, two numbers add to target] }
```

- `algorithms`: registry ids. **The first is the primary pattern**; the rest are valid alternatives
  (e.g. 200 Number of Islands → `dfs, bfs, union-find`). `algo check` fails on unknown ids.
- `keywords`: what you'd type when you half-remember the problem. Searched with the title.
  Titles and keywords must not contain commas.
- `difficulty`: `easy | medium | hard`.
- `uses` *(optional)*: other places the same technique applies ("api throttling", "git bisect"). Searched by `algo p`, printed by `-u`.
- `list` *(optional)*: a study-list tag. `study99` = the 99 problems in `request.md`; `algo check` requires each to have a
  per-problem solution (§5.1). The full map with verification status is [`docs/study99.md`](study99.md).
- Titles may contain commas (`Pow(x, n)`); `keywords` and `uses` items may not.
- `algo p` ranks: exact/prefix/substring title match, title-word and prefix-word hits (`k` matches `Kth`),
  whole-phrase keyword hits, then algorithm names. A bare number matches the problem id.

**To add a problem:** append one line, then `algo check`.

---

## 5. Solvers

File: `src/py3/algo/solutions.py`.

**Contract:** a pure function taking one `dict` (keys = schema field names) and returning a
JSON-serialisable result. Register it in `SOLVERS`:

```python
def leetcode_1(data: dict[str, Any]) -> list[int]:        # naming: leetcode_<N>, or solve_<id> for utilities
    seen: dict[int, int] = {}
    for i, x in enumerate(data["nums"]):
        if data["target"] - x in seen:
            return [seen[data["target"] - x], i]
        seen[x] = i
    return []

SOLVERS = { ..., "leetcode-1": leetcode_1 }                # key = the solver key from §1
```

**`algo g` copies your solver into a standalone file.** It writes the source of the function, plus any
helpers named in `HELPERS` (in `main.py`), under a fixed header that imports only
`json, sys, Counter, defaultdict, deque, heapq, Any`. Therefore:

- A solver may only use those imports, the standard library it imports itself *inside* the function, and its listed helpers.
- Helper functions/classes must live in `solutions.py` and be listed: `HELPERS = {"leetcode-684": ["DSU"], "deepmerge": ["_merge"]}`.
  A helper that itself needs another helper must list both, in dependency order.
- The generated file exposes `solve = <your function>` and a `SAMPLE`, which is why `inputs.py` can `from <id> import solve`.

**Judging (optional but recommended for LeetCode targets):** add the case files and a `TARGETS` entry in
`src/py3/algo/cli/main.py`:

```python
"leetcode-1": ("unordered-array", ROOT/"cases/leetcode-1/case-1.input.json", ROOT/"cases/leetcode-1/case-1.expected.json"),
```

`cases/leetcode-1/case-1.input.json` = `{"nums":[2,7,11,15],"target":9}`, `case-1.expected.json` = `[0,1]`.
(`registry/problem-targets.yml` mirrors this table but is **not read by code** — see §9.)

| Comparator | Passes when |
|---|---|
| `exact` | `actual == expected` |
| `number` | equal and numeric |
| `boolean` | `actual is expected` |
| `string` | equal and a string |
| `unordered-array` | same multiset of elements (order ignored) |
| `unordered-nested-array` | same multiset of inner lists |
| `topo-order` | `actual` is a valid topological order; `expected` may be the problem input (`numCourses` + `prerequisites`) or an exact order |

Add a comparator in `src/py3/algo/judge/comparators.py` and register it in `COMPARATORS`.

### 5.1 Per-problem solutions and `algo verify`

`SOLVERS` holds one solver per *algorithm* (its representative problem). Separately, every problem on the
`study99` list has its own solution, kept in LeetCode's own argument order so it can be run side by side
with someone else's code:

| File | Holds |
|---|---|
| `src/py3/algo/leetcode/solutions.py` | `lc<N>_<name>(...)` functions; design problems as classes (`MyQueue`, `RangeModule`, `Logger`, `WeightedPicker`); SQL answers in `SQL`. Docstring line 1 = pattern + complexity. `by_id()` maps id → object. |
| `src/py3/algo/leetcode/structures.py` | `ListNode`, `TreeNode`, `Interval` and list/level-order converters. |
| `src/py3/algo/leetcode/catalog.py` | `SPECS[id] = Spec(...)`: hand `cases` + `expect`ed outputs, a random `gen`, an `out` comparator, an optional brute-force `oracle`, `kinds` for argument conversion, `bad_ref` when the reference is wrong. `SQL_FIXTURES` for the SQL problems. |
| `src/py3/algo/leetcode/verify.py` | The harness (`python3 -m algo.leetcode.verify`, `algo verify`, `mise run verify:leetcode`). |

For each problem `verify` (1) checks the LeetCode examples against `expect`, then (2) runs hand cases plus
`-n` random cases through our solution **and** through the cnkyrpsgl solution if the repo has it, otherwise
through `oracle`. SQL runs on sqlite against the example tables; 528 (random) is checked statistically.
Comparators: `exact`, `unordered`, `nested` (list of unordered groups), `float`, `ll` (linked-list output),
or a function for problems with several valid answers (e.g. Two Sum indices, longest palindrome, top-k ties).

Reference solutions are `exec`'d with LeetCode's implicit imports (`List`, `collections`, `heapq`, …) and
our `ListNode`/`TreeNode`/`Interval`. Three are wrong and are bypassed with `bad_ref` (8, 772, 875 —
listed in `docs/study99.md`); a mutated solution is caught within the first few cases, so a pass is meaningful.

**Running them (`lc-N` targets).** `algo/leetcode/runnable.py` turns each solution into a target. Its schema comes
from the signature: parameter names are the fields, and annotation strings map to shorthand types (`list[int]` →
`ints`, `list[str]` → `strs`, `list[float]` → `floats`, `list[list[int]]` → `igrid`, `list[list[str]]` → `cgrid`,
`ListNode | None` → `ll`, `list[ListNode | None]` → `lls`, `TreeNode | None` → `tree`, anything else → `any`). A
solution annotated `-> None` modifies its input in place (LeetCode's contract, e.g. 88), so the target returns its
first argument after the call (spec `out="arg0"`). The sample is the first catalog hand case.
Adapters cover the other shapes: design classes take `ops params` (LeetCode's transcript format), 528 takes
`w picks seed`, 278 takes `n bad`, and SQL problems take `query` and run on the example tables in sqlite. The same
adapter code is copied into generated libraries, so `algo r lc-N` and `python3 lc<N>_*.py` behave the same.
`algo check` and `tests/test_problem_targets.py` run every target's sample and every generated library.

**To add a problem:** solution in `solutions.py` → `Spec` in `catalog.py` (examples + `gen`; an `oracle` if
the reference repo lacks the id, i.e. most ids > 1263) → line in `problems.yml` → `algo check` → `algo verify <id>`.

---

## 6. Schemas and input shorthand

File: `src/py3/algo/shorthand.py`. `SCHEMAS[target]` is an ordered `field -> type` map. **Field names must be
exactly the keys the solver reads from `data`.** Tokens fill fields positionally, or `field=value` by name.

```python
SCHEMAS = { ..., "leetcode-1": {"nums": "ints", "target": "int"} }
```

| Type | Shorthand | Random (`rand:`) |
|---|---|---|
| `int` | `5` | — |
| `ints` | `1,2,5` · `1..5` | `rand:8:0-9` (count, range) |
| `str` | `abcabcbb` | `rand:10:abc` (length, alphabet) |
| `cgrid` / `igrid` | `11000/11000/00100` (chars) · `2,1,1/1,1,0` (ints) | `rand:4x5[:alphabet]` |
| `edges` | `1-2,1-3,2-3` · path `1-2-3-4` | `rand:6:8` (nodes, edges; acyclic) |
| `wedges` | `2-1:1,2-3:1` (`u-v:weight`) | `rand:6:8` |
| `strs` | `eat,tea,tan` | — |
| `floats` | `0.5,0.5,0.2` | — |
| `ll` | `2,4,3` (passed to the solution as a linked list) | as `ints` |
| `lls` | `1,4,5/1,3,4/2,6` (list of linked lists; an empty row is an empty list) | — |
| `tree` | `3,9,20,null,null,15,7` (level order, `null` = no node) | — |
| `any` | `5` · `abc` · `[1, 2]` · `[a: [1, 2], b: [3]]` | — |

**Literal syntax** works for any type: `[...]` is a list, `[k: v, ...]` or `{k: v}` a dict, quotes force a
string, bare words are int/float/true/false/null else string. Brackets may contain spaces.

**Samples.** `leetcode-*` targets take their sample from `cases/<target>/case-1.input.json` (via `TARGETS`).
Utilities with no case files use `SAMPLES["<id>"]` in `shorthand.py`. `GRID_ALPHA` sets default random-grid
alphabets (e.g. `01` for islands). A new type = a new branch in `parse_value()`.

---

## 7. End-to-end checklist (worked example)

Adding *Two Sum* took exactly these steps (all of it is in the repo):

1. **Registry** — the pattern entry `hash-map` already carried `leetcode: { id: 1, ... }` (§3). New pattern? add an entry.
2. **Problem index** — `1 Two Sum` → `[hash-map]` in `problems.yml` (§4).
3. **Solver** — `leetcode_1` in `solutions.py`, registered as `"leetcode-1"` in `SOLVERS` (§5).
4. **Schema** — `"leetcode-1": {"nums": "ints", "target": "int"}` in `SCHEMAS` (§6).
5. **Case** — `cases/leetcode-1/case-1.{input,expected}.json`, plus the `TARGETS` entry and, for the record, a line in `problem-targets.yml`.
6. **Verify** — `algo check`, then `algo judge leetcode-1`, then `algo i 2,7,11,15 9 hash-map && python3 inputs.py`.
7. **Reinstall** — `mise run pack` rebuilds `dist/` (the bundle includes `registry/`, `py3/`, `cases/`, `shell/`).

A non-LeetCode utility (`add`) is the same minus the case files: registry entry with no `leetcode:` field,
`solve_add` registered under `"add"`, `SCHEMAS["add"] = {"a": "any", "b": "any"}`, `SAMPLES["add"]`.

If a solver needs a helper, add it to `solutions.py` **and** to `HELPERS` — `algo check` verifies the name exists,
but only `algo g <id>` followed by running the generated file proves the file is self-contained.

---

## 8. Current inventory

### 8.1 Algorithms (38)

| id | Name | Category | Representative problem | Has solver | Problems |
|---|---|---|---|---|---|
| `dfs` | Depth-First Search | graph-traversal | 200 Number of Islands | yes (`leetcode-200`) | 6 |
| `bfs` | Breadth-First Search | graph-traversal | 994 Rotting Oranges | yes (`leetcode-994`) | 10 |
| `binary-search` | Binary Search | search | 33 Search in Rotated Sorted Array | yes (`leetcode-33`) | 14 |
| `sliding-window` | Sliding Window | arrays-strings | 3 Longest Substring Without Repeating Characters | yes (`leetcode-3`) | 9 |
| `topological-sort` | Topological Sort | graph | 210 Course Schedule II | yes (`leetcode-210`) | 2 |
| `union-find` | Union Find | graph | 684 Redundant Connection | yes (`leetcode-684`) | 5 |
| `dijkstra` | Dijkstra Shortest Path | graph | 743 Network Delay Time | yes (`leetcode-743`) | 4 |
| `heap-topk` | Top K Frequent | heap | 347 Top K Frequent Elements | yes (`leetcode-347`) | 3 |
| `backtracking` | Backtracking | search | 79 Word Search | yes (`leetcode-79`) | 8 |
| `dp-1d` | One Dimensional Dynamic Programming | dynamic-programming | 322 Coin Change | yes (`leetcode-322`) | 17 |
| `add` | Add | utility | — | yes (`add`) | 0 |
| `deepmerge` | Deep Merge | utility | — | yes (`deepmerge`) | 0 |
| `hash-map` | Hash Map Lookup | arrays-hashing | 1 Two Sum | yes (`leetcode-1`) | 26 |
| `two-pointers` | Two Pointers | arrays-strings | 15 3Sum | no | 12 |
| `fast-slow-pointers` | Fast and Slow Pointers | linked-list | 141 Linked List Cycle | no | 6 |
| `prefix-sum` | Prefix Sum | arrays-hashing | 560 Subarray Sum Equals K | no | 8 |
| `kadane` | Kadane Running Best | dynamic-programming | 53 Maximum Subarray | no | 3 |
| `greedy` | Greedy Choice | greedy | 55 Jump Game | no | 10 |
| `monotonic-stack` | Monotonic Stack | stack | 739 Daily Temperatures | no | 6 |
| `stack` | Stack | stack | 20 Valid Parentheses | no | 7 |
| `linked-list` | Linked List Manipulation | linked-list | 206 Reverse Linked List | no | 9 |
| `intervals` | Interval Merging | intervals | 56 Merge Intervals | no | 3 |
| `tree-dfs` | Tree Recursion | trees | 104 Maximum Depth of Binary Tree | no | 17 |
| `dp-2d` | Two Dimensional Dynamic Programming | dynamic-programming | 62 Unique Paths | no | 10 |
| `dp-knapsack` | Knapsack Subset DP | dynamic-programming | 416 Partition Equal Subset Sum | no | 2 |
| `two-heaps` | Two Heaps | heap | 295 Find Median from Data Stream | no | 1 |
| `trie` | Trie | strings | 208 Implement Trie (Prefix Tree) | no | 2 |
| `bit-manipulation` | Bit Manipulation | bits | 136 Single Number | no | 3 |
| `matrix` | Matrix Traversal | arrays-matrix | 48 Rotate Image | no | 5 |
| `cyclic-sort` | Cyclic Sort | arrays | 41 First Missing Positive | no | 3 |
| `binary-search-answer` | Binary Search on the Answer | search | 875 Koko Eating Bananas | no | 4 |
| `heap` | Heap Priority Queue | heap | 1046 Last Stone Weight | no | 4 |
| `sorting` | Sorting and Order Statistics | sorting | 912 Sort an Array | no | 13 |
| `rolling-hash` | Rolling Hash (Rabin-Karp) | strings | 1044 Longest Duplicate Substring | no | 1 |
| `math` | Math and Number Theory | math | 50 Pow(x n) | no | 8 |
| `simulation` | Simulation and Parsing | strings | 6 Zigzag Conversion | no | 4 |
| `design` | Data Structure Design | design | 232 Implement Queue using Stacks | no | 4 |
| `sql` | SQL Query | database | 175 Combine Two Tables | no | 4 |

### 8.2 Solvers (13)

| Target | Function | Algorithm | Schema (field:type) | Judged with |
|---|---|---|---|---|
| `leetcode-1` | `leetcode_1` | `hash-map` | `nums:ints` `target:int` | unordered-array |
| `leetcode-200` | `leetcode_200` | `dfs` | `grid:cgrid` | number |
| `leetcode-994` | `leetcode_994` | `bfs` | `grid:igrid` | number |
| `leetcode-33` | `leetcode_33` | `binary-search` | `nums:ints` `target:int` | number |
| `leetcode-3` | `leetcode_3` | `sliding-window` | `s:str` | number |
| `leetcode-210` | `leetcode_210` | `topological-sort` | `numCourses:int` `prerequisites:edges` | topo-order |
| `leetcode-684` | `leetcode_684` | `union-find` | `edges:edges` | exact |
| `leetcode-743` | `leetcode_743` | `dijkstra` | `times:wedges` `n:int` `k:int` | number |
| `leetcode-347` | `leetcode_347` | `heap-topk` | `nums:ints` `k:int` | unordered-array |
| `leetcode-79` | `leetcode_79` | `backtracking` | `board:cgrid` `word:str` | boolean |
| `leetcode-322` | `leetcode_322` | `dp-1d` | `coins:ints` `amount:int` | number |
| `add` | `solve_add` | `add` | `a:any` `b:any` | — (not judged) |
| `deepmerge` | `solve_deepmerge` | `deepmerge` | `a:any` `b:any` | — (not judged) |

### 8.3 Problem → algorithm index (173 problems)

51 easy · 98 medium · 24 hard · 99 on the `study99` list (all solved and verified — see [`docs/study99.md`](study99.md) for the per-problem table with other uses), plus 23, 88 and 387 solved and verified outside the list. An asterisk (`*`) marks an algorithm that is an
*alternative* rather than the primary pattern. The non-study99 entries are curated from memory of the commonly cited
"Top 100 Liked" / Blind 75 / NeetCode sets — **not a snapshot of LeetCode's live ranking**.

- **`dfs`** (6) — 200 Number of Islands, 207 Course Schedule*, 261 Graph Valid Tree*, 302 Smallest Rectangle Enclosing Black Pixels*, 419 Battleships in a Board*, 547 Number of Provinces*
- **`bfs`** (10) — 102 Binary Tree Level Order Traversal, 199 Binary Tree Right Side View, 994 Rotting Oranges, 2812 Find the Safest Path in a Grid, 200 Number of Islands*, 261 Graph Valid Tree*, 279 Perfect Squares*, 302 Smallest Rectangle Enclosing Black Pixels*, 547 Number of Provinces*, 3970 Shortest Path With At Most K Consecutive Identical Characters*
- **`binary-search`** (14) — 4 Median of Two Sorted Arrays, 33 Search in Rotated Sorted Array, 34 Find First and Last Position of Element in Sorted Array, 153 Find Minimum in Rotated Sorted Array, 278 First Bad Version, 302 Smallest Rectangle Enclosing Black Pixels, 354 Russian Doll Envelopes, 240 Search a 2D Matrix II*, 287 Find the Duplicate Number*, 300 Longest Increasing Subsequence*, 528 Random Pick with Weight*, 715 Range Module*, 1044 Longest Duplicate Substring*, 2089 Find Target Indices After Sorting Array*
- **`sliding-window`** (9) — 3 Longest Substring Without Repeating Characters, 30 Substring with Concatenation of All Words, 76 Minimum Window Substring, 438 Find All Anagrams in a String, 485 Max Consecutive Ones, 904 Fruit Into Baskets, 2747 Count Zero Request Servers, 219 Contains Duplicate II*, 239 Sliding Window Maximum*
- **`topological-sort`** (2) — 207 Course Schedule, 210 Course Schedule II
- **`union-find`** (5) — 261 Graph Valid Tree, 547 Number of Provinces, 684 Redundant Connection, 128 Longest Consecutive Sequence*, 200 Number of Islands*
- **`dijkstra`** (4) — 743 Network Delay Time, 1514 Path with Maximum Probability, 3970 Shortest Path With At Most K Consecutive Identical Characters, 2812 Find the Safest Path in a Grid*
- **`heap-topk`** (3) — 23 Merge k Sorted Lists, 215 Kth Largest Element in an Array, 347 Top K Frequent Elements
- **`backtracking`** (8) — 17 Letter Combinations of a Phone Number, 22 Generate Parentheses, 39 Combination Sum, 46 Permutations, 51 N-Queens, 78 Subsets, 79 Word Search, 494 Target Sum*
- **`dp-1d`** (17) — 70 Climbing Stairs, 96 Unique Binary Search Trees, 118 Pascal's Triangle, 139 Word Break, 198 House Robber, 279 Perfect Squares, 300 Longest Increasing Subsequence, 322 Coin Change, 509 Fibonacci Number, 1048 Longest String Chain, 1218 Longest Arithmetic Subsequence of Given Difference, 1911 Maximum Alternating Subsequence Sum, 32 Longest Valid Parentheses*, 53 Maximum Subarray*, 337 House Robber III*, 338 Counting Bits*, 354 Russian Doll Envelopes*
- **`hash-map`** (28) — 1 Two Sum, 13 Roman to Integer, 49 Group Anagrams, 128 Longest Consecutive Sequence, 146 LRU Cache, 217 Contains Duplicate, 219 Contains Duplicate II, 242 Valid Anagram, 349 Intersection of Two Arrays, 359 Logger Rate Limiter, 383 Ransom Note, 387 First Unique Character in a String, 2913 Subarrays Distinct Element Sum of Squares I, 3 Longest Substring Without Repeating Characters*, 30 Substring with Concatenation of All Words*, 76 Minimum Window Substring*, 105 Construct Binary Tree from Preorder and Inorder Traversal*, 136 Single Number*, 138 Copy List with Random Pointer*, 169 Majority Element*, 202 Happy Number*, 347 Top K Frequent Elements*, 438 Find All Anagrams in a String*, 560 Subarray Sum Equals K*, 904 Fruit Into Baskets*, 1048 Longest String Chain*, 1218 Longest Arithmetic Subsequence of Given Difference*, 3026 Maximum Good Subarray Sum*
- **`two-pointers`** (13) — 5 Longest Palindromic Substring, 11 Container With Most Water, 15 3Sum, 31 Next Permutation, 42 Trapping Rain Water, 75 Sort Colors, 88 Merge Sorted Array, 283 Move Zeroes, 2337 Move Pieces to Obtain a String, 19 Remove Nth Node From End of List*, 160 Intersection of Two Linked Lists*, 349 Intersection of Two Arrays*, 647 Palindromic Substrings*
- **`fast-slow-pointers`** (6) — 141 Linked List Cycle, 142 Linked List Cycle II, 202 Happy Number, 234 Palindrome Linked List, 287 Find the Duplicate Number, 876 Middle of the Linked List
- **`prefix-sum`** (8) — 238 Product of Array Except Self, 528 Random Pick with Weight, 560 Subarray Sum Equals K, 1480 Running Sum of 1d Array, 3026 Maximum Good Subarray Sum, 42 Trapping Rain Water*, 437 Path Sum III*, 3886 Sum of Sortable Integers*
- **`kadane`** (3) — 53 Maximum Subarray, 152 Maximum Product Subarray, 121 Best Time to Buy and Sell Stock*
- **`greedy`** (10) — 45 Jump Game II, 55 Jump Game, 121 Best Time to Buy and Sell Stock, 169 Majority Element, 621 Task Scheduler, 763 Partition Labels, 1405 Longest Happy String, 3863 Minimum Operations to Sort a String, 410 Split Array Largest Sum*, 1911 Maximum Alternating Subsequence Sum*
- **`monotonic-stack`** (6) — 84 Largest Rectangle in Histogram, 85 Maximal Rectangle, 239 Sliding Window Maximum, 739 Daily Temperatures, 1944 Number of Visible People in a Queue, 42 Trapping Rain Water*
- **`stack`** (7) — 20 Valid Parentheses, 32 Longest Valid Parentheses, 155 Min Stack, 232 Implement Queue using Stacks, 394 Decode String, 772 Basic Calculator III, 3749 Evaluate Valid Expressions
- **`linked-list`** (9) — 2 Add Two Numbers, 19 Remove Nth Node From End of List, 21 Merge Two Sorted Lists, 138 Copy List with Random Pointer, 160 Intersection of Two Linked Lists, 206 Reverse Linked List, 23 Merge k Sorted Lists*, 146 LRU Cache*, 234 Palindrome Linked List*
- **`intervals`** (3) — 56 Merge Intervals, 715 Range Module, 759 Employee Free Time
- **`tree-dfs`** (17) — 94 Binary Tree Inorder Traversal, 98 Validate Binary Search Tree, 100 Same Tree, 101 Symmetric Tree, 104 Maximum Depth of Binary Tree, 105 Construct Binary Tree from Preorder and Inorder Traversal, 112 Path Sum, 114 Flatten Binary Tree to Linked List, 124 Binary Tree Maximum Path Sum, 226 Invert Binary Tree, 230 Kth Smallest Element in a BST, 236 Lowest Common Ancestor of a Binary Tree, 337 House Robber III, 437 Path Sum III, 543 Diameter of Binary Tree, 1448 Count Good Nodes in Binary Tree, 199 Binary Tree Right Side View*
- **`dp-2d`** (10) — 10 Regular Expression Matching, 62 Unique Paths, 64 Minimum Path Sum, 72 Edit Distance, 221 Maximal Square, 647 Palindromic Substrings, 1143 Longest Common Subsequence, 5 Longest Palindromic Substring*, 85 Maximal Rectangle*, 410 Split Array Largest Sum*
- **`dp-knapsack`** (2) — 416 Partition Equal Subset Sum, 494 Target Sum
- **`two-heaps`** (1) — 295 Find Median from Data Stream
- **`trie`** (2) — 208 Implement Trie (Prefix Tree), 14 Longest Common Prefix*
- **`bit-manipulation`** (3) — 136 Single Number, 338 Counting Bits, 3644 Maximum K to Sort a Permutation
- **`matrix`** (5) — 48 Rotate Image, 54 Spiral Matrix, 73 Set Matrix Zeroes, 240 Search a 2D Matrix II, 419 Battleships in a Board
- **`cyclic-sort`** (3) — 41 First Missing Positive, 448 Find All Numbers Disappeared in an Array, 287 Find the Duplicate Number*
- **`binary-search-answer`** (4) — 69 Sqrt(x), 410 Split Array Largest Sum, 875 Koko Eating Bananas, 2812 Find the Safest Path in a Grid*
- **`heap`** (4) — 1046 Last Stone Weight, 621 Task Scheduler*, 759 Employee Free Time*, 1405 Longest Happy String*
- **`sorting`** (13) — 179 Largest Number, 462 Minimum Moves to Equal Array Elements II, 912 Sort an Array, 2089 Find Target Indices After Sorting Array, 3886 Sum of Sortable Integers, 14 Longest Common Prefix*, 15 3Sum*, 56 Merge Intervals*, 349 Intersection of Two Arrays*, 354 Russian Doll Envelopes*, 759 Employee Free Time*, 1048 Longest String Chain*, 2747 Count Zero Request Servers*
- **`rolling-hash`** (1) — 1044 Longest Duplicate Substring
- **`math`** (8) — 9 Palindrome Number, 50 Pow(x, n), 1922 Count Good Numbers, 2235 Add Two Integers, 3736 Minimum Moves to Equal Array Elements III, 69 Sqrt(x)*, 462 Minimum Moves to Equal Array Elements II*, 509 Fibonacci Number*
- **`simulation`** (4) — 6 Zigzag Conversion, 8 String to Integer (atoi), 14 Longest Common Prefix, 1929 Concatenation of Array
- **`design`** (4) — 232 Implement Queue using Stacks*, 359 Logger Rate Limiter*, 528 Random Pick with Weight*, 715 Range Module*
- **`sql`** (4) — 175 Combine Two Tables, 181 Employees Earning More Than Their Managers, 584 Find Customer Referee, 1757 Recyclable and Low Fat Products

---

## 9. Gaps

**Solver coverage.** 36 of 38 algorithms are runnable: 13 through a per-algorithm solver, the rest through a
per-problem target (§1, §5.1). 109 of the 173 indexed problems are runnable by number: the 99 study-list problems,
23, 88, 387, plus 33, 79, 210, 684, 743 and 994 via `SOLVERS`. Everything else is *findable* (`.a p`, `.a s`) but not runnable.
Algorithms with **no runner**: `two-heaps`, `trie` (no solved problem uses either as its primary pattern).
Solving one more problem in `algo/leetcode/solutions.py` makes it, and any pattern it is primary for, runnable.

**Problem-target limits.** Field types come from annotation strings, so a new solution needs a mapped annotation
(or gets `any`, which takes literal syntax). 759's `list[list[list[int]]]` input is `any`. Random (`rand:`) input
exists only for the types that had it before (`ints`/`ll`, `str`, grids, edges).

**Mapping is coarse in places.**
- `tree-dfs` bundles 14 problems with different shapes (traversal, BST validation, path sums,
  construction, LCA). Candidates to split: `bst`, `tree-construction`, `tree-path-sum`.
- `linked-list` (9) and `hash-map` (12) are broad; `dp-1d` (10) mixes
  counting DP, string segmentation and subsequence DP.
- Design problems now have a `design` pattern (232, 359, 528, 715); older entries (146 LRU Cache, 155 Min Stack, 208 Trie)
  are still mapped only to their underlying structure.
- Binary search on the *answer space* has its own entry, `binary-search-answer` (69, 410, 875, 2812); 287 still sits under `binary-search`.

**Patterns absent from the registry** (common in interviews, not needed by the 171 indexed problems):
Bellman-Ford, Floyd–Warshall, minimum spanning tree (Kruskal/Prim), segment tree / Fenwick tree,
KMP / Manacher (Rabin-Karp is now `rolling-hash`), quickselect as its own entry (only referenced under `heap-topk`), sweep line,
bitmask DP, interval DP, bipartite check / graph colouring, Kahn's-algorithm variant of topological sort,
Morris traversal, reservoir sampling, meet-in-the-middle.

**Index limits.**
- Only the problems listed. Premium problems appear only where a study list includes them (261, 302, 359, 759, 772).
- Titles/difficulty/pattern assignments were written from memory — spot-check before trusting a specific entry.
- Search is substring + keyword scoring (no stemming/synonyms): `.a p "k largest"` works via prefix matching,
  but a paraphrase with none of the title words or keywords will miss. Fix by adding `keywords` to the problem.

**Plumbing.**
- `registry/problem-targets.yml` duplicates the `TARGETS` dict in `main.py` and is **not read**; two sources of truth.
- Registry `comparator:` is documentation only (the judged comparator comes from `TARGETS`).
- Only one case per judged target (`case-1`); edge cases (empty input, duplicates, negatives) are untested.
- The Go backend implements only the original 10 solvers via `solve`; it has none of `search/problems/generate/inputs/run/pipe/check`.
- Negative numbers conflict with `-` in edge shorthand (`1-2`); use the literal syntax (`[[1, 2]]`) instead.
