# Case 3: Top K Frequent Elements → heap top-k

> *Given `nums` and `k`, return the `k` most frequent elements, in any order.*

## 1. Identification

Phrasing matters. Paraphrases with few title words rank lower:

```console
$ .a p "k most frequent" --top 3
 621* Task Scheduler             medium  -> greedy, heap
  11* Container With Most Water  medium  -> two-pointers
 347* Top K Frequent Elements    medium  -> heap-topk, hash-map

$ .a p "top k frequent" --top 3
 347* Top K Frequent Elements          medium  -> heap-topk, hash-map
 215  Kth Largest Element in an Array  medium  -> heap-topk
 230  Kth Smallest Element in a BST    medium  -> tree-dfs
```

Use the statement's own nouns. 347 → `heap-topk` (primary), with `hash-map` for the counting step.

## 2. Judging

```console
$ .a s -j --id "top k most frequent" --top 2
[ { "id": "heap-topk", "score": 4, "matched": ["top k", "most frequent"], ... },
  { "id": "heap",      "score": 1, "matched": ["greedy with most remaining"], ... } ]
```

```console
$ .a s --disqualifier "need fully sorted result"
heap-topk     Top K Frequent
...
```

If the problem needed **every** element ranked, a full sort (O(n log n)) would be simpler and the heap gains
nothing. Here only `k` are needed and order doesn't matter, so a size-k heap over the counts
(O(n log k)) is right. Bucket sort by frequency gets O(n) when you need it.

## 3. Solving

```console
$ .a i 1,1,1,2,2,3 2 heap-topk
generated /tmp/algo-demo/heap_topk.py
/tmp/algo-demo/inputs.py
$ python3 $ALGO_TMP/inputs.py
[1, 2]
```

The judged target compares with `unordered-array`, since any order is accepted:
`.a pipe leetcode-347 | .a assert --expected src/cases/leetcode-347/case-1.expected.json --comparator unordered-array`.

## 4. Chaining

*A till holds mostly 5s and 2s. Using only the two most common denominations, what's the fewest coins
for 11?*

```console
$ .a r top-k 5,5,5,1,1,2,2,2,2,10 2 then coin-change _ 11
heap-topk        in={"nums":[5,5,5,1,1,2,2,2,2,10],"k":2}  out=[2, 5]
dp-1d            in={"coins":[2,5],"amount":11}  out=4
4
```

The list output fit `coins`, the first `ints` field, so `_` went there and `11` filled `amount`.
11 = 5 + 2 + 2 + 2, four coins.

**Other places top-k applies:** trending topics, top talkers in network traffic, leaderboards, k nearest points.
