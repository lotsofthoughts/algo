# Study list → LeetCode map (99 problems)

Every problem from `request.md`, matched to its LeetCode number, the pattern that solves it optimally
(first = primary, the rest are valid alternatives), and **other places the same technique shows up**.
Each one has a solution in [`src/py3/algo/leetcode/solutions.py`](../src/py3/algo/leetcode/solutions.py)
checked by `algo verify` (`mise run verify:leetcode`).

**Verification:** 99/99 pass · 70 vs [cnkyrpsgl/leetcode](https://github.com/cnkyrpsgl/leetcode) (examples + 300 random cases each) · 24 vs brute-force oracles · 4 SQL on sqlite · 1 statistical. Re-run any time with `algo verify [ids…]`.

| Check | Meaning |
|---|---|
| ref | Differential test against the cnkyrpsgl solution (LeetCode examples + 300 random inputs). |
| brute | Reference repo lacks it (mostly ids > 1263); compared to a slow, obviously-correct brute force. |
| brute† | Reference repo **has a wrong solution** (see below); brute force used instead. |
| sqlite | SQL run on the LeetCode example tables in in-memory sqlite. |
| stats | Randomised (528): 20k picks per case must match the weights within 2%. |

| # | LC | Problem | Diff | Pattern(s) | Check | Other uses of the technique |
|---:|---:|---|:-:|---|:-:|---|
| 1 | 1 | [Two Sum](https://leetcode.com/problems/two-sum/) | E | `hash-map` | ref | deduplicate records by key; join two datasets on a key; detect matching transactions; cache lookups |
| 2 | 9 | [Palindrome Number](https://leetcode.com/problems/palindrome-number/) | E | `math` | ref | digit manipulation; checksum digits; number base conversion |
| 3 | 4 | [Median of Two Sorted Arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/) | H | `binary-search` | ref | k-th smallest across shards; percentiles over merged sorted datasets; database merge-join statistics |
| 4 | 3 | [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) | M | `sliding-window`, `hash-map` | ref | longest session without repeat events; network packet dedupe windows; unique-token spans in logs |
| 5 | 15 | [3Sum](https://leetcode.com/problems/3sum/) | M | `two-pointers`, `sorting` | ref | k-sum feature search; finding balanced trades; closest-sum budgeting |
| 6 | 2 | [Add Two Numbers](https://leetcode.com/problems/add-two-numbers/) | M | `linked-list` | ref | big integer arithmetic; streaming digit addition; merging sorted streams with a dummy head |
| 7 | 121 | [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) | E | `greedy`, `kadane` | ref | max drawup and drawdown; best single trade; max difference with order constraint |
| 8 | 13 | [Roman to Integer](https://leetcode.com/problems/roman-to-integer/) | E | `hash-map` | ref | parsing numeral systems; lookup-table decoding; lexical token translation |
| 9 | 1929 | [Concatenation of Array](https://leetcode.com/problems/concatenation-of-array/) | E | `simulation` | brute | circular buffer unrolling; wrap-around problems; doubling arrays for rotations |
| 10 | 128 | [Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) | M | `hash-map`, `union-find` | ref | streak detection; finding id runs; union-find of adjacent values |
| 11 | 410 | [Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/) | H | `binary-search-answer`, `greedy`, `dp-2d` | ref | load balancing across workers; book allocation; partitioning jobs fairly |
| 12 | 242 | [Valid Anagram](https://leetcode.com/problems/valid-anagram/) | E | `hash-map` | ref | frequency comparison; checksum-like equality; plagiarism signatures |
| 13 | 49 | [Group Anagrams](https://leetcode.com/problems/group-anagrams/) | M | `hash-map` | ref | canonical-form grouping; clustering equivalent records; dedupe by signature |
| 14 | 14 | [Longest Common Prefix](https://leetcode.com/problems/longest-common-prefix/) | E | `simulation`, `trie`, `sorting` | ref | autocomplete; ip routing prefix match; grouping file paths |
| 15 | 42 | [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) | H | `two-pointers`, `monotonic-stack`, `prefix-sum` | ref | terrain and flood modelling; capacity between peaks; elevation map analysis |
| 16 | 11 | [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) | M | `two-pointers` | ref | maximize pairwise score on sorted data; pair selection under a min constraint; best window between two boundaries |
| 17 | 20 | [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) | E | `stack` | ref | html and xml tag validation; compiler syntax checks; undo stacks |
| 18 | 175 | [Combine Two Tables](https://leetcode.com/problems/combine-two-tables/) | E | `sql` | sqlite | reporting with optional data; outer joins in etl; enriching records |
| 19 | 200 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) | M | `dfs`, `bfs`, `union-find` | ref | image segmentation; counting clusters; network partitions |
| 20 | 2235 | [Add Two Integers](https://leetcode.com/problems/add-two-integers/) | E | `math` | brute | warmup; arithmetic utilities; overflow awareness |
| 21 | 347 | [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) | M | `heap-topk`, `hash-map` | ref | trending topics; top talkers in networks; leaderboards |
| 22 | 875 | [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) | M | `binary-search-answer` | brute† | capacity planning; minimum throughput for a deadline; shipping capacity |
| 23 | 53 | [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) | M | `kadane`, `dp-1d` | ref | best profit period; signal burst detection; max-gain segment in time series |
| 24 | 485 | [Max Consecutive Ones](https://leetcode.com/problems/max-consecutive-ones/) | E | `sliding-window` | ref | uptime streaks; longest success run; run-length encoding |
| 25 | 6 | [Zigzag Conversion](https://leetcode.com/problems/zigzag-conversion/) | M | `simulation` | ref | text layout and rendering; interleaving data into lanes; rail-fence cipher |
| 26 | 349 | [Intersection of Two Arrays](https://leetcode.com/problems/intersection-of-two-arrays/) | E | `hash-map`, `two-pointers`, `sorting` | ref | finding shared users; tag overlap; joining id sets |
| 27 | 34 | [Find First and Last Position of Element in Sorted Array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/) | M | `binary-search` | ref | range queries on sorted indexes; counting occurrences in sorted data; time-range lookup in logs |
| 28 | 22 | [Generate Parentheses](https://leetcode.com/problems/generate-parentheses/) | M | `backtracking` | ref | generating valid test inputs; grammar enumeration; catalan structure enumeration |
| 29 | 56 | [Merge Intervals](https://leetcode.com/problems/merge-intervals/) | M | `intervals`, `sorting` | ref | calendar merging; coalescing ip ranges; genomic region merging |
| 30 | 278 | [First Bad Version](https://leetcode.com/problems/first-bad-version/) | E | `binary-search` | ref | git bisect; finding regression commits; threshold search |
| 31 | 354 | [Russian Doll Envelopes](https://leetcode.com/problems/russian-doll-envelopes/) | H | `binary-search`, `dp-1d`, `sorting` | ref | box stacking; chain scheduling; 2d longest increasing subsequence |
| 32 | 118 | [Pascal's Triangle](https://leetcode.com/problems/pascals-triangle/) | E | `dp-1d` | ref | combinatorics nCk; probability distributions; polynomial expansion |
| 33 | 84 | [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) | H | `monotonic-stack` | ref | maximal rectangle in binary matrix; skyline problems; span and range queries |
| 34 | 5 | [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) | M | `two-pointers`, `dp-2d` | ref | dna palindromic site detection; symmetry detection in sequences; manacher for linear-time palindromes |
| 35 | 136 | [Single Number](https://leetcode.com/problems/single-number/) | E | `bit-manipulation` | ref | parity checks; error detection; find the odd one out in pairs |
| 36 | 181 | [Employees Earning More Than Their Managers](https://leetcode.com/problems/employees-earning-more-than-their-managers/) | E | `sql` | sqlite | hierarchy queries; self-joins for parent-child data; org chart reports |
| 37 | 287 | [Find the Duplicate Number](https://leetcode.com/problems/find-the-duplicate-number/) | M | `fast-slow-pointers`, `binary-search`, `cyclic-sort` | ref | cycle detection in functional graphs; memory-light duplicate finding; pointer-chasing bugs |
| 38 | 2337 | [Move Pieces to Obtain a String](https://leetcode.com/problems/move-pieces-to-obtain-a-string/) | M | `two-pointers` | brute | token movement puzzles; sliding-piece feasibility; relative-order invariants |
| 39 | 179 | [Largest Number](https://leetcode.com/problems/largest-number/) | M | `sorting` | ref | custom ordering rules; smallest number by concatenation; key-ordering tricks |
| 40 | 2913 | [Subarrays Distinct Element Sum of Squares I](https://leetcode.com/problems/subarrays-distinct-element-sum-of-squares-i/) | E | `hash-map` | brute | distinct-count analytics; window diversity metrics; brute-force baselines |
| 41 | 715 | [Range Module](https://leetcode.com/problems/range-module/) | H | `intervals`, `binary-search`, `design` | ref | memory allocators; ip range tracking; calendar availability |
| 42 | 1218 | [Longest Arithmetic Subsequence of Given Difference](https://leetcode.com/problems/longest-arithmetic-subsequence-of-given-difference/) | M | `dp-1d`, `hash-map` | ref | trend detection; sequence pattern mining; dp keyed by value |
| 43 | 383 | [Ransom Note](https://leetcode.com/problems/ransom-note/) | E | `hash-map` | ref | inventory sufficiency checks; resource allocation feasibility; multiset containment |
| 44 | 1757 | [Recyclable and Low Fat Products](https://leetcode.com/problems/recyclable-and-low-fat-products/) | E | `sql` | sqlite | simple filtering; product catalog queries; feature flags |
| 45 | 69 | [Sqrt(x)](https://leetcode.com/problems/sqrtx/) | E | `binary-search-answer`, `math` | ref | integer roots without floats; newton method; binary search on monotone functions |
| 46 | 2089 | [Find Target Indices After Sorting Array](https://leetcode.com/problems/find-target-indices-after-sorting-array/) | E | `sorting`, `binary-search` | brute | rank queries; counting sort; positional statistics |
| 47 | 739 | [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/) | M | `monotonic-stack` | ref | stock span; next price increase; event lookahead |
| 48 | 1048 | [Longest String Chain](https://leetcode.com/problems/longest-string-chain/) | M | `dp-1d`, `hash-map`, `sorting` | ref | edit-step chains; version lineage; longest path in dag |
| 49 | 1944 | [Number of Visible People in a Queue](https://leetcode.com/problems/number-of-visible-people-in-a-queue/) | H | `monotonic-stack` | brute | line-of-sight problems; skyline visibility; next greater with counts |
| 50 | 3886 | [Sum of Sortable Integers](https://leetcode.com/problems/sum-of-sortable-integers/) | H | `sorting`, `prefix-sum` | brute | block-wise sortedness checks; rotation detection; divisor enumeration |
| 51 | 3863 | [Minimum Operations to Sort a String](https://leetcode.com/problems/minimum-operations-to-sort-a-string/) | M | `greedy` | brute | answer bounded by a small constant; invariant-based reasoning; operation counting puzzles |
| 52 | 416 | [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) | M | `dp-knapsack` | ref | fair division; load balancing two machines; budget allocation |
| 53 | 100 | [Same Tree](https://leetcode.com/problems/same-tree/) | E | `tree-dfs` | ref | dom diffing; ast comparison; merkle-style tree equality |
| 54 | 50 | [Pow(x, n)](https://leetcode.com/problems/powx-n/) | M | `math` | ref | modular exponentiation in rsa; matrix power for recurrences; repeated squaring of transforms |
| 55 | 21 | [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/) | E | `linked-list` | ref | merge step of merge sort; merging sorted log files; k-way merge of streams |
| 56 | 3026 | [Maximum Good Subarray Sum](https://leetcode.com/problems/maximum-good-subarray-sum/) | M | `prefix-sum`, `hash-map` | brute | best segment between matching events; pair-anchored range sums; prefix-min lookups |
| 57 | 1143 | [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) | M | `dp-2d` | ref | diff and patch; dna comparison; version-control merges |
| 58 | 8 | [String to Integer (atoi)](https://leetcode.com/problems/string-to-integer-atoi/) | M | `simulation` | brute† | config and protocol parsers; input validation; tokenizers and lexers |
| 59 | 3644 | [Maximum K to Sort a Permutation](https://leetcode.com/problems/maximum-k-to-sort-a-permutation/) | M | `bit-manipulation` | brute | bitmask invariants; permission masks; feasibility via common bits |
| 60 | 54 | [Spiral Matrix](https://leetcode.com/problems/spiral-matrix/) | M | `matrix` | ref | image and matrix traversal orders; printing layouts; peeling layers of grids |
| 61 | 904 | [Fruit Into Baskets](https://leetcode.com/problems/fruit-into-baskets/) | M | `sliding-window`, `hash-map` | ref | longest window with k distinct values; session analysis; cache with k types |
| 62 | 1046 | [Last Stone Weight](https://leetcode.com/problems/last-stone-weight/) | E | `heap` | ref | priority scheduling; event simulation; huffman-style merges |
| 63 | 1922 | [Count Good Numbers](https://leetcode.com/problems/count-good-numbers/) | M | `math` | brute | counting with independent choices; modular arithmetic; combinatorics mod p |
| 64 | 876 | [Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/) | E | `fast-slow-pointers` | ref | splitting lists for merge sort; palindrome list checks; single-pass midpoint |
| 65 | 219 | [Contains Duplicate II](https://leetcode.com/problems/contains-duplicate-ii/) | E | `hash-map`, `sliding-window` | ref | rate limiting; recent-duplicate suppression; dedupe in time windows |
| 66 | 912 | [Sort an Array](https://leetcode.com/problems/sort-an-array/) | M | `sorting` | ref | external sorting; stable multi-key sorting; preprocessing for binary search |
| 67 | 3970 | [Shortest Path With At Most K Consecutive Identical Characters](https://leetcode.com/problems/shortest-path-with-at-most-k-consecutive-identical-characters/) | M | `dijkstra`, `bfs` | brute | routing with constraints; fuel or streak limited paths; state-space search |
| 68 | 560 | [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) | M | `prefix-sum`, `hash-map` | ref | counting time windows with target totals; anomaly windows; range-sum analytics |
| 69 | 217 | [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) | E | `hash-map` | ref | duplicate detection in uploads; unique constraint checks; bloom filter prefilters |
| 70 | 759 | [Employee Free Time](https://leetcode.com/problems/employee-free-time/) | H | `intervals`, `heap`, `sorting` | ref | meeting scheduling; resource availability; maintenance windows |
| 71 | 419 | [Battleships in a Board](https://leetcode.com/problems/battleships-in-a-board/) | M | `matrix`, `dfs` | ref | counting objects in grids; connected component shortcuts; image blob counting |
| 72 | 584 | [Find Customer Referee](https://leetcode.com/problems/find-customer-referee/) | E | `sql` | sqlite | three-valued logic pitfalls; filtering nullable columns; data quality checks |
| 73 | 462 | [Minimum Moves to Equal Array Elements II](https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/) | M | `sorting`, `math` | ref | facility location on a line; minimizing absolute deviation; meeting point problems |
| 74 | 1405 | [Longest Happy String](https://leetcode.com/problems/longest-happy-string/) | M | `greedy`, `heap` | brute | task interleaving without repeats; reorganize string; playlist shuffling |
| 75 | 1044 | [Longest Duplicate Substring](https://leetcode.com/problems/longest-duplicate-substring/) | H | `rolling-hash`, `binary-search` | ref | plagiarism detection; dna repeat finding; data deduplication |
| 76 | 1911 | [Maximum Alternating Subsequence Sum](https://leetcode.com/problems/maximum-alternating-subsequence-sum/) | M | `dp-1d`, `greedy` | brute | stock trading with unlimited trades; state-machine dp; signal peaks and troughs |
| 77 | 72 | [Edit Distance](https://leetcode.com/problems/edit-distance/) | M | `dp-2d` | ref | spell checking; dna alignment; diff tools and fuzzy search |
| 78 | 3749 | [Evaluate Valid Expressions](https://leetcode.com/problems/evaluate-valid-expressions/) | H | `stack` | brute | s-expression interpreters; ast evaluation; function-call parsers |
| 79 | 1514 | [Path with Maximum Probability](https://leetcode.com/problems/path-with-maximum-probability/) | M | `dijkstra` | brute | most reliable network route; risk-minimizing paths; log-transform to shortest path |
| 80 | 3736 | [Minimum Moves to Equal Array Elements III](https://leetcode.com/problems/minimum-moves-to-equal-array-elements-iii/) | E | `math` | brute | levelling resources; equalizing inventory; budget top-ups |
| 81 | 232 | [Implement Queue using Stacks](https://leetcode.com/problems/implement-queue-using-stacks/) | E | `stack`, `design` | ref | amortized analysis; functional queues; undo and redo buffers |
| 82 | 261 | [Graph Valid Tree](https://leetcode.com/problems/graph-valid-tree/) | M | `union-find`, `dfs`, `bfs` | ref | network topology validation; spanning tree checks; detecting redundant links |
| 83 | 202 | [Happy Number](https://leetcode.com/problems/happy-number/) | E | `fast-slow-pointers`, `hash-map` | ref | cycle detection in iterated functions; prng period finding; detecting loops in state machines |
| 84 | 207 | [Course Schedule](https://leetcode.com/problems/course-schedule/) | M | `topological-sort`, `dfs` | ref | build systems; package dependency resolution; deadlock detection |
| 85 | 112 | [Path Sum](https://leetcode.com/problems/path-sum/) | E | `tree-dfs` | ref | decision tree evaluation; budget along hierarchy paths; config inheritance checks |
| 86 | 772 | [Basic Calculator III](https://leetcode.com/problems/basic-calculator-iii/) | H | `stack` | brute† | formula engines; interpreters; config expression evaluation |
| 87 | 509 | [Fibonacci Number](https://leetcode.com/problems/fibonacci-number/) | E | `dp-1d`, `math` | ref | dp warmup; matrix exponentiation; recurrence modelling |
| 88 | 2747 | [Count Zero Request Servers](https://leetcode.com/problems/count-zero-request-servers/) | M | `sliding-window`, `sorting` | brute | monitoring idle hosts; offline query processing; time-window aggregation |
| 89 | 547 | [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) | M | `union-find`, `dfs`, `bfs` | ref | social graph clusters; network segmentation; grouping related accounts |
| 90 | 621 | [Task Scheduler](https://leetcode.com/problems/task-scheduler/) | M | `greedy`, `heap` | ref | cpu scheduling with cooldowns; rate-limited job queues; round-robin planning |
| 91 | 528 | [Random Pick with Weight](https://leetcode.com/problems/random-pick-with-weight/) | M | `prefix-sum`, `binary-search`, `design` | stats | load balancer weighting; a/b test traffic splits; weighted sampling in games |
| 92 | 30 | [Substring with Concatenation of All Words](https://leetcode.com/problems/substring-with-concatenation-of-all-words/) | H | `sliding-window`, `hash-map` | ref | multi-keyword search in text; bag-of-words matching; detecting anagram-like token windows |
| 93 | 2812 | [Find the Safest Path in a Grid](https://leetcode.com/problems/find-the-safest-path-in-a-grid/) | M | `bfs`, `dijkstra`, `binary-search-answer` | brute | robot path planning away from hazards; evacuation routing; bottleneck paths |
| 94 | 70 | [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) | E | `dp-1d` | ref | counting tilings; step-combination counting; linear recurrences |
| 95 | 359 | [Logger Rate Limiter](https://leetcode.com/problems/logger-rate-limiter/) | E | `hash-map`, `design` | ref | api throttling; alert dedupe; log spam suppression |
| 96 | 41 | [First Missing Positive](https://leetcode.com/problems/first-missing-positive/) | H | `cyclic-sort` | ref | allocating the smallest free id; finding gaps in sequences; in-place bucket placement |
| 97 | 302 | [Smallest Rectangle Enclosing Black Pixels](https://leetcode.com/problems/smallest-rectangle-enclosing-black-pixels/) | H | `binary-search`, `dfs`, `bfs` | ref | image bounding boxes; object detection crops; sparse region bounds |
| 98 | 1448 | [Count Good Nodes in Binary Tree](https://leetcode.com/problems/count-good-nodes-in-binary-tree/) | M | `tree-dfs` | brute | path maxima in hierarchies; permission inheritance; record-breaking along paths |
| 99 | 1480 | [Running Sum of 1d Array](https://leetcode.com/problems/running-sum-of-1d-array/) | E | `prefix-sum` | brute | range-sum queries; cumulative metrics; weighted sampling tables |

## Reference-repo bugs found while verifying

- **8 String to Integer (atoi)** — regex r'\u005Cd+' matches a literal backslash + d, so it returns 0 for every input.
- **772 Basic Calculator III** — floors negative division (-1/9 -> -1); the problem truncates toward zero.
- **875 Koko Eating Bananas** — returns the first speed whose hours == h, not the smallest ([20,13], h=3 -> 15, answer 13).
- **56 Merge Intervals** and **759 Employee Free Time** use LeetCode's old `Interval` objects; the verifier converts `[s, e]` pairs for them.

## Problems added for this list

Six titles are recent contest problems (2025–26) that were looked up by title, pinned from their published statements, and verified against brute force: 3644, 3736, 3749, 3863, 3886, 3970. The four SQL problems
(175, 181, 584, 1757) map to the new `sql` pattern.

## Patterns by count (this list)

`hash-map` 11 · `dp-1d` 6 · `math` 5 · `binary-search` 5 · `sliding-window` 5 · `two-pointers` 5 · `sorting` 5 · `greedy` 4 · `simulation` 4 · `stack` 4 · `sql` 4 · `prefix-sum` 4 · `binary-search-answer` 3 · `intervals` 3 · `monotonic-stack` 3 · `fast-slow-pointers` 3 · `tree-dfs` 3 · `linked-list` 2 · `bit-manipulation` 2 · `dp-2d` 2 · `matrix` 2 · `dijkstra` 2 · `union-find` 2 · `dfs` 1 · `heap-topk` 1 · `kadane` 1 · `backtracking` 1 · `dp-knapsack` 1 · `heap` 1 · `rolling-hash` 1 · `topological-sort` 1 · `bfs` 1 · `cyclic-sort` 1

## Reading a row

```bash
algo p 875 -u        # pattern + other uses   (875* = verified solution exists)
algo p -l study99    # just this list
algo p "rate limiter" # search by a use, not just a title
algo verify 875 4 3886 -v
```
