# Case 4: Number of Islands → DFS flood fill

> *Given a grid of `'1'` (land) and `'0'` (water), count the islands: groups of land connected
> horizontally or vertically.*

## 1. Identification

```console
$ .a p islands --top 3
 200* Number of Islands      medium  -> dfs, bfs, union-find
  14* Longest Common Prefix  easy    -> simulation, trie, sorting
  50* Pow(x, n)              medium  -> math
```

Three valid patterns: `dfs` (primary), `bfs`, `union-find`. Judging picks one.

## 2. Judging

```console
$ .a s -j --id "connected components flood fill" --top 3
[ { "id": "dfs", "score": 4, "matched": ["connected components", "flood fill"], ... } ]
```

Only DFS matches both phrases. Now check whether a constraint rules it out:

```console
$ .a s --disqualifier "shortest path required"
dfs               Depth-First Search
union-find        Union Find
...
```

DFS and union-find **would** drop out if the question asked for a shortest path (use BFS then: 994 Rotting
Oranges, 2812 Safest Path). It only asks for a count, so:

| Option | Fits when | Here |
| --- | --- | --- |
| DFS (iterative stack) | one-off count, simplest code | **chosen** |
| BFS | you also need distances or levels | works, no benefit |
| Union-find | the grid changes (land added over time), or connectivity queries repeat | overkill |

## 3. Solving

`cgrid` shorthand: rows separated by `/`.

```console
$ .a i 11000/11000/00100/00011 dfs
generated /tmp/algo-demo/dfs.py
/tmp/algo-demo/inputs.py
$ python3 $TMPDIR/inputs.py
3
```

Stress it with a random grid (`-v` echoes the generated input):

```console
$ .a r dfs rand:5x8 --seed 7 -v
dfs              in={"grid":[["1","0","1","0","0","0","1","0"], ...]}  out=9
9
```

## 4. Chaining

*Two map tiles: count islands on the first and add the second tile's count (2).*

```console
$ .a r dfs 11000/11000/00100/00011 then add _ 2
dfs              in={"grid":[["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]}  out=3
add              in={"a":3,"b":2}  out=5
5
```

(Islands touching across the tile border would be double-counted. Handling that needs union-find over the
edge cells, which is the "grid changes" row above.)

**Other places flood fill applies:** image segmentation and paint-bucket fill, counting clusters,
network partitions, battleship counting (419 does it in one pass without a visited set).
