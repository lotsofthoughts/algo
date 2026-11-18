# Cases: from problem statement to chained solution

Each case takes one problem through the same four steps. Every command and output below was run
against the workbench as shipped (`ALGO_TMP=/tmp/algo-demo`); your paths will differ.

| Step | What you do | Command |
| --- | --- | --- |
| **1. Identification** | Search for the problem by title, number, keywords or a use case. The first algorithm listed is the primary pattern. | `.a p "<query>"` |
| **2. Judging** | Check the pattern against the problem: which identification phrases match, and which disqualifiers would rule it out. | `.a s -j --id "<symptoms>"` · `.a s --disqualifier "<constraint>"` |
| **3. Solving** | Generate the library and an `inputs.py` wired to your values, then run it. `.a sh` shows each algorithm's fields. | `.a i <values...> <algo>` · `python3 inputs.py` |
| **4. Chaining** | Feed the output into another algorithm. `_` is the previous output; with no `_`, it binds to the first empty field it fits. | `.a r <algo> <values> then <algo> _ ...` |

| # | Case | Pattern | Chained into |
| --- | --- | --- | --- |
| 1 | [Course Schedule II](01-course-schedule.md) | `topological-sort` | `binary-search`: where does a course land in the plan? |
| 2 | [Network Delay Time](02-network-delay.md) | `dijkstra` | `dp-1d`: fewest timer ticks that cover the delay |
| 3 | [Top K Frequent Elements](03-top-k-frequent.md) | `heap-topk` | `dp-1d`: make change from the most common coins |
| 4 | [Number of Islands](04-number-of-islands.md) | `dfs` | `add`: total islands across two map tiles |
| 5 | [Coin Change](05-coin-change.md) | `dp-1d` | fed *by* `sliding-window`: an amount computed upstream |

## Reading the output

- `.a p` rows: `id* title difficulty -> algorithms`. `*` means a verified per-problem solution exists
  (`algo verify`).
- `.a s -j`: `score` counts phrase hits (2 for a whole phrase, 1 per shared word); `matched` lists the phrases
  that hit. A big gap between the top two scores means the choice is clear-cut.
- `.a s --disqualifier "X"` lists the algorithms that **X rules out**. If your problem has constraint X, drop
  those candidates.
- `.a i` prints `generated <lib>.py` the first time (it never overwrites), then the path of `inputs.py`.
  The library is standalone: `from <lib> import solve`, or `python3 <lib>.py [input.json]`.
- In a chain, each stage's input and output go to stderr; only the final answer goes to stdout, so
  `.a r ... | jq` works.

Full flag reference: [../API.md §2](../API.md#2-command-reference).
