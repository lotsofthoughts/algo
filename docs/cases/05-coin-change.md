# Case 5: Coin Change → 1-D dynamic programming

> *Given coin denominations and an `amount`, return the fewest coins that make the amount, or `-1`. Unlimited
> coins of each kind.*

## 1. Identification

```console
$ .a p "fewest coins amount" --top 3
 322  Coin Change      medium  -> dp-1d
 279  Perfect Squares  medium  -> dp-1d, bfs
```

322 → `dp-1d`. 279 is the same recurrence with squares as the coins.

## 2. Judging

```console
$ .a s -j --id "minimum coins target amount" --top 2
[ { "id": "dp-1d",                "score": 4, "matched": ["minimum coins", "target amount"], ... },
  { "id": "binary-search-answer", "score": 3, "matched": ["maximize the minimum", "minimum speed", "minimum capacity"], ... } ]
```

The runner-up only matched the word "minimum" in other phrases. Nothing here is monotone in a way
binary search could use. The real competitor is **greedy** (always take the largest coin), and its
disqualifier makes the call:

```console
$ .a s --disqualifier "greedy canonical coin system guaranteed"
dp-1d           One Dimensional Dynamic Programming
...
```

DP is overkill only if the coin system is guaranteed canonical (like 1/5/10/25, where greedy is optimal).
The problem allows **any** coins: with `[1, 3, 4]` and amount 6, greedy picks 4+1+1 (3 coins) but 3+3 (2 coins)
is optimal. So DP: `dp[a] = min(dp[a - c] + 1)` over coins `c`, O(amount × coins).

## 3. Solving

```console
$ .a i 1,2,5 11 coin-change
generated /tmp/algo-demo/dp_1d.py
/tmp/algo-demo/inputs.py
$ python3 $TMPDIR/inputs.py
3
```

The generated library stands alone. Run it on its sample, on a JSON file, or import it:

```console
$ python3 $TMPDIR/dp_1d.py
3
$ echo '{"coins":[1,5,10,25],"amount":63}' > c.json && python3 $TMPDIR/dp_1d.py c.json
6
$ python3 -c "import sys; sys.path.insert(0, '$TMPDIR'); from dp_1d import solve; print(solve({'coins':[2],'amount':3}))"
-1
```

The unreachable case also works without files: `.a r coin-change 2 3` prints `-1`. Confirm against the judged sample
with `.a judge leetcode-322` (`"status": "PASS"`).

## 4. Chaining (this time *into* DP)

*The amount is computed upstream: the longest run of distinct characters in a log line. Make it from 2s and 3s.*

```console
$ .a r sliding-window abcabcbb then coin-change 2,3 _
sliding-window   in={"s":"abcabcbb"}  out=3
dp-1d            in={"coins":[2,3],"amount":3}  out=1
1
```

Any stage that outputs an int can feed `amount`. Swap in `dfs` (island count) or `dijkstra` (delay) and the
chain still type-checks, because `_` binds by type.

**Other places this DP applies:** making change, minimum-cost step counting, resource bundling,
perfect squares (279), knapsack variants (`.a s dp-knapsack -p`).
