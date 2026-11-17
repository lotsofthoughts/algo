# Case 1: Course Schedule II → topological sort

> *There are `numCourses` courses labelled `0..n-1`. `prerequisites[i] = [a, b]` means take `b` before `a`.
> Return an order that finishes every course, or `[]` if that's impossible.*

## 1. Identification

Search with the words the statement uses:

```console
$ .a p "course order prerequisites" --top 3
 207* Course Schedule                    medium  -> topological-sort, dfs
 210  Course Schedule II                 medium  -> topological-sort
 102  Binary Tree Level Order Traversal  medium  -> bfs
```

210 is this problem; its only pattern is `topological-sort`. (207 asks the yes/no version and also lists
`dfs`, for cycle detection by colouring.)

## 2. Judging

Describe the symptoms and see what matches:

```console
$ .a s -j --id "dependencies ordering" --top 2
[ { "id": "topological-sort", "score": 4, "matched": ["dependencies", "ordering"], ... },
  { "id": "bfs",              "score": 1, "matched": ["level order"], ... } ]
```

A 4-to-1 gap: topological sort is clearly the fit. Now check what could rule it out:

```console
$ .a s --disqualifier "cyclic graph"
topological-sort  Topological Sort
...
```

Topological sort is listed because a **cyclic** graph has no complete order. That doesn't disqualify it
here: the problem *expects* cycles and asks for `[]` when one exists, and Kahn's algorithm reports one for
free (fewer than `n` nodes get processed). Keep it.

**Why not plain BFS or DFS?** BFS gives level order, not dependency order. DFS can produce a topological order
(reverse post-order), but needs explicit three-colour cycle detection. Kahn's queue gets both properties in
one O(V + E) pass.

## 3. Solving

Check the input fields, then pass values in that order (`1-0` is the edge `[1, 0]`):

```console
$ .a sh | grep topological
topological-sort numCourses:int prerequisites:edges

$ .a i 4 1-0,2-0,3-1,3-2 topo
generated /tmp/algo-demo/topological_sort.py
/tmp/algo-demo/inputs.py
```

`.a i` generated the library first, then an `inputs.py` that imports it:

```python
"""Inputs for topological-sort.  Run: python3 /tmp/algo-demo/inputs.py"""
import json, sys
sys.path.insert(0, '/tmp/algo-demo')
from topological_sort import solve

numCourses = 4
prerequisites = [[1, 0], [2, 0], [3, 1], [3, 2]]

if __name__ == "__main__":
    print(json.dumps(solve({'numCourses': numCourses, 'prerequisites': prerequisites}), default=repr))
```

```console
$ python3 $TMPDIR/inputs.py
[0, 1, 2, 3]
```

Edit the values in `inputs.py` and re-run to try more cases. The cycle case doesn't need a file:

```console
$ .a r topo 2 0-1,1-0
[]
```

## 4. Chaining

*Where in the plan does course 3 land?* The order is a list of ints, which fits binary search's `nums` field:

```console
$ .a r topo 4 1-0,2-0,3-1,3-2 then binary-search _ target=3
topological-sort in={"numCourses":4,"prerequisites":[[1,0],[2,0],[3,1],[3,2]]}  out=[0, 1, 2, 3]
binary-search    in={"nums":[0,1,2,3],"target":3}  out=3
3
```

Course 3 is fourth (index 3). Binary search is only valid here because this particular order happens to
be sorted. In general, look positions up with a `{course: index}` map, which is what Kahn's order is
usually turned into for "is A scheduled before B?" queries.

**Other places topological sort applies** (`.a p 207 -u`): build systems, package dependency resolution,
deadlock detection.
