# Case 2: Network Delay Time → Dijkstra

> *`times[i] = [u, v, w]` is a directed edge taking `w` time. A signal starts at node `k`. How long until all
> `n` nodes receive it? Return `-1` if some node never does.*

## 1. Identification

```console
$ .a p "network delay signal" --top 3
 743  Network Delay Time           medium  -> dijkstra
   1* Two Sum                      easy    -> hash-map
   4* Median of Two Sorted Arrays  hard    -> binary-search
```

One clear hit, 743 → `dijkstra`. The rows after it are weak matches.

## 2. Judging

The key symptom is *weighted* edges:

```console
$ .a s -j --id "weighted shortest path" --top 2
[ { "id": "dijkstra", "score": 3, "matched": ["weighted shortest path", "weighted graph"], ... },
  { "id": "bfs",      "score": 2, "matched": ["shortest path unweighted"], ... } ]
```

BFS comes close because "shortest path" matches, so let the constraint decide:

```console
$ .a s --disqualifier "weighted edges" -p --problems-top 2
bfs  Breadth-First Search
        102  Binary Tree Level Order Traversal
        199  Binary Tree Right Side View
       ... +8 more (algo p -a bfs)
dfs  Depth-First Search
...
```

Weighted edges **rule out BFS**: it minimises hop count, not total weight. Dijkstra's own disqualifiers are
`negative weights` and `all pairs shortest path`; travel times are non-negative and there is one source, so
Dijkstra stands. The answer is the **largest** shortest-path distance, since everyone has to have heard.

## 3. Solving

```console
$ .a sh | grep dijkstra
dijkstra         times:wedges n:int k:int

$ .a i 2-1:1,2-3:1,3-4:1 4 2 dijkstra
generated /tmp/algo-demo/dijkstra.py
/tmp/algo-demo/inputs.py
$ python3 $TMPDIR/inputs.py
2
```

`2-1:1` is the edge 2→1 with weight 1 (`wedges` shorthand). From node 2: node 1 and node 3 at time 1,
node 4 at time 2, so the answer is 2.

## 4. Chaining

*The scheduler fires on 1, 2 and 5 ms ticks. What's the fewest ticks that add up to the delay?* That's Coin
Change, with the delay as the amount:

```console
$ .a r dijkstra 2-1:1,2-3:1,3-4:1 4 2 then coin-change 1,2,5 _
dijkstra         in={"times":[[2,1,1],[2,3,1],[3,4,1]],"n":4,"k":2}  out=2
dp-1d            in={"coins":[1,2,5],"amount":2}  out=1
1
```

`_` filled `amount`; the coin list was given positionally. For a random graph, start from the highest
node, because `rand:` edges always point from higher to lower node numbers:
`.a r dijkstra rand:5:9 5 4 --seed 1 -v` (prints 8).

**Other places Dijkstra applies:** routing, most-reliable path (multiply probabilities: 1514), constrained
paths with expanded state (3970), map navigation.
