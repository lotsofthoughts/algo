# Algorithm Workbench

Portable, declarative algorithm practice workbench for interview prep.

## Principles

- Shell functions are thin launchers.
- Runtime behavior is environment-driven: `ALGO_HOME`, `ALGO_LANG`.
- Shared YAML registries make algorithms searchable and declarative.
- Data structures are decoupled from problem adapters.
- Solvers read JSON and emit JSON.
- Judge/comparator logic is decoupled from algorithm implementations.

## Quick start

```bash
source shell/bootstrap.sh
algo targets
algo search --id "nested grid connected components"
algo search --disqualifier "negative weights"
algo judge leetcode-200
algo pipe leetcode-347 --input cases/leetcode-347/case-1.input.json \
  | algo assert --expected cases/leetcode-347/case-1.expected.json --comparator unordered-array
```

Fish:

```fish
source shell/bootstrap.fish
algo judge leetcode-322
```

Go backend:

```bash
ALGO_LANG=go algo pipe leetcode-743 --input cases/leetcode-743/case-1.input.json
```

## Generate code + inputs

```bash
.a p "two sum"            # problem -> algorithm(s)   (docs/API.md explains the whole system)
.a s graph                 # search: `id  name` list (-j for JSON)
.a g bfs                   # writes $TMPDIR/bfs.py (importable: `from bfs import solve`)
.a i 1 2 add               # writes $TMPDIR/inputs.py, generating add.py first if missing
python3 $TMPDIR/inputs.py  # -> 3
.a i [a: [1, 2, 3]] [b: [0], c: [2, 3]] -a deepmerge
.a i 212/110/011 bfs       # grid shorthand; see `.a sh` for each algorithm's fields
.a r topo 4 1-0,2-0,3-1,3-2 then binary-search _ target=2   # run + chain, no files
```

Values: `[1, 2]` lists, `[k: v]` dicts, bare scalars, plus per-shape sugar
(`a-b:w` edges, `11000/00100` grids, `rand:...`) — see `py3/algo/shorthand.py`.
In zsh, `.a` is an alias for `noglob algo` so brackets aren't glob-expanded.

## Study list (99 problems) + verification

Every problem in `request.md` is mapped to its LeetCode number, pattern(s) and other uses, with a solution
checked against [cnkyrpsgl/leetcode](https://github.com/cnkyrpsgl/leetcode) or a brute force. Full table:
[`docs/study99.md`](../docs/study99.md); how it works: [`docs/API.md` §5.1](../docs/API.md#51-per-problem-solutions-and-algo-verify).

```bash
.a p -l study99            # the list (* = verified solution)
.a p 875 -u                # pattern + other uses of the technique
.a p "rate limiter"        # search by use case
.a verify --fetch          # clone the reference once, then differential-test all 99
.a verify 3886 875 -v      # a few problems, every failure printed
```

## Shell completions

Tab completion for `algo` and `.a` (subcommands, flags, algorithm names, targets, comparators) ships in
`shell/completions/` and is loaded automatically by `bootstrap.sh` (interactive bash) and
`bootstrap.fish` (interactive fish) — so the pasted installer enables it too. Algorithm names are
read live from the registry via the hidden `algo complete <kind>` helper.

```fish
# optional, fish: make completions load without sourcing bootstrap
ln -s "$ALGO_HOME/shell/completions/algo.fish" ~/.config/fish/completions/algo.fish
```

```bash
# optional, bash: load from your ~/.bashrc without the full bootstrap
source "$ALGO_HOME/shell/completions/algo.bash"
```

zsh is not covered yet.

## V1 targets

| Target | Algorithm | Comparator |
|---|---|---|
| leetcode-200 | DFS | number |
| leetcode-994 | BFS | number |
| leetcode-33 | Binary Search | number |
| leetcode-3 | Sliding Window | number |
| leetcode-210 | Topological Sort | topo-order |
| leetcode-684 | Union Find | exact |
| leetcode-743 | Dijkstra | number |
| leetcode-347 | Heap Top-K | unordered-array |
| leetcode-79 | Backtracking | boolean |
| leetcode-322 | 1-D DP | number |

## Extension contract

Every new target should add:

1. Registry metadata in `registry/algorithms.yml`.
2. Problem target metadata in `registry/problem-targets.yml`.
3. One input case.
4. One expected output case.
5. A comparator name.
6. A solver adapter.

