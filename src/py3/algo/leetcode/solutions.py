"""Reference solutions for the 99-problem study list (request.md).

Every function keeps LeetCode's argument order so it can be differential-tested against the
cnkyrpsgl/leetcode solutions (`algo verify`). The first line of each docstring names the pattern;
the registry entry in `registry/problems.yml` holds keywords, alternatives and other uses.
Design problems are classes; SQL problems are query strings run on sqlite by the verifier.
"""

from __future__ import annotations

import bisect
import heapq
import random
from collections import Counter, defaultdict, deque
from functools import cmp_to_key, lru_cache
from typing import TYPE_CHECKING, Any

from algo.leetcode.structures import ListNode, TreeNode

if TYPE_CHECKING:
    from collections.abc import Callable

MOD = 10**9 + 7


# ── arrays & hashing ────────────────────────────────────────────────────────────────────────────


def lc1_two_sum(nums: list[int], target: int) -> list[int]:
    """hash-map: remember value -> index, look up the complement. O(n)."""
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []


def lc128_longest_consecutive(nums: list[int]) -> int:
    """hash-map (set): only start counting at a run's first element. O(n)."""
    s, best = set(nums), 0
    for x in s:
        if x - 1 not in s:
            y = x
            while y + 1 in s:
                y += 1
            best = max(best, y - x + 1)
    return best


def lc242_is_anagram(s: str, t: str) -> bool:
    """hash-map: equal character counts. O(n)."""
    return Counter(s) == Counter(t)


def lc387_first_uniq_char(s: str) -> int:
    """hash-map: count characters, then the first index whose count is 1. O(n), O(1) space.

    `str.count` runs once per *distinct* character (at most 26), so this is O(26 n) = O(n) and
    the counting happens in C. Iterating `for c in s` instead would call it n times: O(n^2).
    """
    counts = {c: s.count(c) for c in set(s)}
    gen = (i for i, c in enumerate(s) if counts[c] == 1)
    return next(gen, -1)


def lc49_group_anagrams(strs: list[str]) -> list[list[str]]:
    """hash-map: group by sorted-letters key. O(n k log k)."""
    groups: dict[str, list[str]] = defaultdict(list)
    for w in strs:
        groups["".join(sorted(w))].append(w)
    return list(groups.values())


def lc349_intersection(nums1: list[int], nums2: list[int]) -> list[int]:
    """hash-map (set): set intersection. O(n + m)."""
    return list(set(nums1) & set(nums2))


def lc383_can_construct(ransom_note: str, magazine: str) -> bool:
    """hash-map: every needed letter count is available. O(n + m)."""
    return not (Counter(ransom_note) - Counter(magazine))


def lc217_contains_duplicate(nums: list[int]) -> bool:
    """hash-map (set): any value seen twice. O(n)."""
    return len(set(nums)) < len(nums)


def lc219_contains_nearby_duplicate(nums: list[int], k: int) -> bool:
    """hash-map: last index of each value; window of width k. O(n)."""
    last: dict[int, int] = {}
    for i, x in enumerate(nums):
        if x in last and i - last[x] <= k:
            return True
        last[x] = i
    return False


def lc1929_get_concatenation(nums: list[int]) -> list[int]:
    """simulation: ans = nums + nums. O(n)."""
    return nums + nums


def lc1480_running_sum(nums: list[int]) -> list[int]:
    """prefix-sum: cumulative totals. O(n)."""
    out, total = [], 0
    for x in nums:
        total += x
        out.append(total)
    return out


def lc560_subarray_sum(nums: list[int], k: int) -> int:
    """prefix-sum + hash-map: count earlier prefixes equal to prefix - k. O(n)."""
    count, prefix, seen = 0, 0, Counter({0: 1})
    for x in nums:
        prefix += x
        count += seen[prefix - k]
        seen[prefix] += 1
    return count


def lc3026_maximum_subarray_sum(nums: list[int], k: int) -> int:
    """prefix-sum + hash-map: min prefix before each value v, look up v±k. O(n)."""
    best_prefix: dict[int, int] = {}  # value -> smallest prefix sum ending just before it
    prefix, best = 0, None
    for x in nums:
        for v in (x - k, x + k):
            if v in best_prefix:
                cand = prefix + x - best_prefix[v]
                best = cand if best is None else max(best, cand)
        if x not in best_prefix or prefix < best_prefix[x]:
            best_prefix[x] = prefix
        prefix += x
    return best if best is not None else 0


def lc2913_sum_counts(nums: list[int]) -> int:
    """hash-map (set): extend each start, track distinct count. O(n^2)."""
    total = 0
    for i in range(len(nums)):
        seen: set[int] = set()
        for j in range(i, len(nums)):
            seen.add(nums[j])
            total += len(seen) ** 2
    return total


def lc41_first_missing_positive(nums: list[int]) -> int:
    """cyclic-sort: place v at index v-1, then scan. O(n) time, O(1) space."""
    nums = nums[:]
    n = len(nums)
    for i in range(n):
        while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
            j = nums[i] - 1
            nums[i], nums[j] = nums[j], nums[i]
    for i, v in enumerate(nums):
        if v != i + 1:
            return i + 1
    return n + 1


def lc2089_target_indices(nums: list[int], target: int) -> list[int]:
    """counting: indices are [#less, #less + #equal) after sorting; no sort needed. O(n)."""
    less = sum(1 for x in nums if x < target)
    equal = sum(1 for x in nums if x == target)
    return list(range(less, less + equal))


def lc347_top_k_frequent(nums: list[int], k: int) -> list[int]:
    """heap-topk: count, then k largest by frequency. O(n log k) (bucket sort gives O(n))."""
    counts = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, counts.items(), key=lambda kv: kv[1])]


# ── two pointers / sliding window ───────────────────────────────────────────────────────────────


def lc15_three_sum(nums: list[int]) -> list[list[int]]:
    """two-pointers: sort, fix i, converge j/k, skip duplicates. O(n^2)."""
    nums = sorted(nums)
    out: list[list[int]] = []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i - 1]:
            continue
        j, k = i + 1, len(nums) - 1
        while j < k:
            s = nums[i] + nums[j] + nums[k]
            if s < 0:
                j += 1
            elif s > 0:
                k -= 1
            else:
                out.append([nums[i], nums[j], nums[k]])
                j += 1
                while j < k and nums[j] == nums[j - 1]:
                    j += 1
                k -= 1
    return out


def lc11_max_area(height: list[int]) -> int:
    """two-pointers: move the shorter wall inward. O(n)."""
    i, j, best = 0, len(height) - 1, 0
    while i < j:
        best = max(best, (j - i) * min(height[i], height[j]))
        if height[i] < height[j]:
            i += 1
        else:
            j -= 1
    return best


def lc42_trap(height: list[int]) -> int:
    """two-pointers: water at the lower side is bounded by that side's running max. O(n)."""
    i, j, lmax, rmax, water = 0, len(height) - 1, 0, 0, 0
    while i < j:
        if height[i] < height[j]:
            lmax = max(lmax, height[i])
            water += lmax - height[i]
            i += 1
        else:
            rmax = max(rmax, height[j])
            water += rmax - height[j]
            j -= 1
    return water


def lc2337_can_change(start: str, target: str) -> bool:
    """two-pointers: same L/R order; L only moves left, R only moves right. O(n)."""
    n, i, j = len(start), 0, 0
    while True:
        while i < n and start[i] == "_":
            i += 1
        while j < n and target[j] == "_":
            j += 1
        if n in (i, j):
            return i == n and j == n
        if start[i] != target[j] or (start[i] == "L" and j > i) or (start[i] == "R" and j < i):
            return False
        i += 1
        j += 1


def lc3_length_of_longest_substring(s: str) -> int:
    """sliding-window: jump left past the last copy of the new char. O(n)."""
    left, best, last = 0, 0, {}
    for right, ch in enumerate(s):
        if last.get(ch, -1) >= left:
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best


def lc485_find_max_consecutive_ones(nums: list[int]) -> int:
    """sliding-window (run length): reset on 0. O(n)."""
    best = cur = 0
    for x in nums:
        cur = cur + 1 if x == 1 else 0
        best = max(best, cur)
    return best


def lc904_total_fruit(fruits: list[int]) -> int:
    """sliding-window: longest window with at most 2 distinct values. O(n)."""
    count: Counter[int] = Counter()
    left = best = 0
    for right, f in enumerate(fruits):
        count[f] += 1
        while len(count) > 2:  # noqa: PLR2004
            count[fruits[left]] -= 1
            if not count[fruits[left]]:
                del count[fruits[left]]
            left += 1
        best = max(best, right - left + 1)
    return best


def lc30_find_substring(s: str, words: list[str]) -> list[int]:
    """sliding-window: one word-sized window per offset, word counts in a map. O(n * w)."""
    if not words:
        return []
    w, k = len(words[0]), len(words)
    need, out = Counter(words), []
    for off in range(w):
        left, have, used = off, Counter(), 0
        for right in range(off, len(s) - w + 1, w):
            word = s[right : right + w]
            if word not in need:
                left, have, used = right + w, Counter(), 0
                continue
            have[word] += 1
            used += 1
            while have[word] > need[word]:
                have[s[left : left + w]] -= 1
                used -= 1
                left += w
            if used == k:
                out.append(left)
                have[s[left : left + w]] -= 1
                used -= 1
                left += w
    return sorted(out)


def lc2747_count_servers(n: int, logs: list[list[int]], x: int, queries: list[int]) -> list[int]:
    """sliding-window over time: sort logs and queries, keep per-server counts. O((L+Q) log)."""
    logs = sorted(logs, key=lambda e: e[1])
    order = sorted(range(len(queries)), key=lambda i: queries[i])
    cnt: Counter[int] = Counter()
    out, lo, hi = [0] * len(queries), 0, 0
    for qi in order:
        q = queries[qi]
        while hi < len(logs) and logs[hi][1] <= q:
            cnt[logs[hi][0]] += 1
            hi += 1
        while lo < hi and logs[lo][1] < q - x:
            cnt[logs[lo][0]] -= 1
            if not cnt[logs[lo][0]]:
                del cnt[logs[lo][0]]
            lo += 1
        out[qi] = n - len(cnt)
    return out


# ── binary search ───────────────────────────────────────────────────────────────────────────────


def lc4_find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    """binary-search: partition the shorter array so both left halves hold half. O(log min)."""
    a, b = (nums1, nums2) if len(nums1) <= len(nums2) else (nums2, nums1)
    m, n = len(a), len(b)
    half, lo, hi = (m + n + 1) // 2, 0, m
    inf = float("inf")
    while True:
        i = (lo + hi) // 2
        j = half - i
        a_left = a[i - 1] if i else -inf
        a_right = a[i] if i < m else inf
        b_left = b[j - 1] if j else -inf
        b_right = b[j] if j < n else inf
        if a_left <= b_right and b_left <= a_right:
            left = max(a_left, b_left)
            if (m + n) % 2:
                return float(left)
            return (left + min(a_right, b_right)) / 2
        if a_left > b_right:
            hi = i - 1
        else:
            lo = i + 1


def lc34_search_range(nums: list[int], target: int) -> list[int]:
    """binary-search: lower bound of target and of target + 1. O(log n)."""
    lo = bisect.bisect_left(nums, target)
    if lo == len(nums) or nums[lo] != target:
        return [-1, -1]
    return [lo, bisect.bisect_right(nums, target) - 1]


def lc69_my_sqrt(x: int) -> int:
    """binary-search on the answer: largest r with r*r <= x. O(log x)."""
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo


def lc278_first_bad_version(n: int, is_bad: Callable[[int], bool]) -> int:
    """binary-search on a monotone predicate. O(log n) API calls."""
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        if is_bad(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def lc875_min_eating_speed(piles: list[int], h: int) -> int:
    """binary-search on the answer: smallest speed whose total hours <= h. O(n log max)."""
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((p + mid - 1) // mid for p in piles) <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo


def lc410_split_array(nums: list[int], k: int) -> int:
    """binary-search on the answer + greedy check: min feasible largest part. O(n log sum)."""
    lo, hi = max(nums), sum(nums)
    while lo < hi:
        cap = (lo + hi) // 2
        parts, cur = 1, 0
        for x in nums:
            if cur + x > cap:
                parts, cur = parts + 1, 0
            cur += x
        if parts <= k:
            hi = cap
        else:
            lo = cap + 1
    return lo


def lc354_max_envelopes(envelopes: list[list[int]]) -> int:
    """binary-search (LIS / patience sort): sort w asc, h desc; LIS on h. O(n log n)."""
    tails: list[int] = []
    for _, h in sorted(envelopes, key=lambda e: (e[0], -e[1])):
        i = bisect.bisect_left(tails, h)
        tails[i : i + 1] = [h]
    return len(tails)


def lc302_min_area(image: list[list[str]], x: int, y: int) -> int:
    """binary-search: black pixels are connected, so row/col projections are contiguous."""
    rows, cols = len(image), len(image[0])

    def col_has(c: int) -> bool:
        return any(image[r][c] == "1" for r in range(rows))

    def row_has(r: int) -> bool:
        return "1" in image[r]

    def first(lo: int, hi: int, has: Callable[[int], bool], want: bool) -> int:
        while lo < hi:  # first index in [lo, hi) where has() == want
            mid = (lo + hi) // 2
            if has(mid) == want:
                hi = mid
            else:
                lo = mid + 1
        return lo

    left = first(0, y, col_has, True)
    right = first(y + 1, cols, col_has, False)
    top = first(0, x, row_has, True)
    bottom = first(x + 1, rows, row_has, False)
    return (right - left) * (bottom - top)


def lc1044_longest_dup_substring(s: str) -> str:
    """binary-search on length + rolling hash (Rabin-Karp), verified on collision. O(n log n)."""
    base, mod = 131, (1 << 61) - 1
    vals = [ord(c) for c in s]

    def find(length: int) -> int:
        h, power = 0, pow(base, length, mod)
        seen: dict[int, list[int]] = {}
        for i, v in enumerate(vals):
            h = (h * base + v) % mod
            if i >= length:
                h = (h - vals[i - length] * power) % mod
            if i >= length - 1:
                start = i - length + 1
                for j in seen.get(h, []):
                    if s[j : j + length] == s[start : start + length]:
                        return start
                seen.setdefault(h, []).append(start)
        return -1

    lo, hi, best = 1, len(s) - 1, ""
    while lo <= hi:
        mid = (lo + hi) // 2
        at = find(mid)
        if at >= 0:
            best, lo = s[at : at + mid], mid + 1
        else:
            hi = mid - 1
    return best


# ── stacks ──────────────────────────────────────────────────────────────────────────────────────


def lc20_is_valid(s: str) -> bool:
    """stack: push openers, pop on matching closer. O(n)."""
    pair, stack = {")": "(", "]": "[", "}": "{"}, []
    for ch in s:
        if ch in pair:
            if not stack or stack.pop() != pair[ch]:
                return False
        else:
            stack.append(ch)
    return not stack


def lc739_daily_temperatures(temperatures: list[int]) -> list[int]:
    """monotonic-stack (decreasing): pop colder days when a warmer one arrives. O(n)."""
    out, stack = [0] * len(temperatures), []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out


def lc84_largest_rectangle_area(heights: list[int]) -> int:
    """monotonic-stack (increasing): a popped bar's width spans to the next smaller bars. O(n)."""
    stack, best = [-1], 0
    for i, h in enumerate([*heights, 0]):
        while stack[-1] != -1 and heights[stack[-1]] >= h:
            top = heights[stack.pop()]
            best = max(best, top * (i - stack[-1] - 1))
        stack.append(i)
    return best


def lc1944_can_see_persons_count(heights: list[int]) -> list[int]:
    """monotonic-stack (decreasing, right to left): count the shorter people you pop. O(n)."""
    out, stack = [0] * len(heights), []
    for i in range(len(heights) - 1, -1, -1):
        seen = 0
        while stack and stack[-1] < heights[i]:
            stack.pop()
            seen += 1
        out[i] = seen + (1 if stack else 0)
        stack.append(heights[i])
    return out


def lc772_calculate(s: str) -> int:
    """Stack (recursive descent): + - * / and parentheses, division truncates toward 0. O(n)."""
    pos = 0

    def parse() -> int:
        nonlocal pos
        stack, num, op = [], 0, "+"
        while pos < len(s):
            ch = s[pos]
            pos += 1
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == "(":
                num = parse()
            if ch in "+-*/)" or pos == len(s):
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                else:
                    stack.append(int(stack.pop() / num))
                op, num = ch, 0
                if ch == ")":
                    break
        return sum(stack)

    return parse()


def lc3749_evaluate_expression(expression: str) -> int:
    """stack: push a frame at `op(`, apply it at `)`. Division is exact by contract. O(n)."""
    ops: dict[str, Callable[[int, int], int]] = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: abs(a) // abs(b) * (1 if (a >= 0) == (b > 0) else -1),
    }
    frames: list[tuple[Callable[[int, int], int], list[int]]] = []
    i, n = 0, len(expression)
    while i < n:
        c = expression[i]
        if c == ",":
            i += 1
        elif c == ")":
            fn, args = frames.pop()
            val = fn(args[0], args[1])
            if not frames:
                return val
            frames[-1][1].append(val)
            i += 1
        elif c.isalpha():
            j = expression.index("(", i)
            frames.append((ops[expression[i:j]], []))
            i = j + 1
        else:
            j = i + 1
            while j < n and expression[j].isdigit():
                j += 1
            val = int(expression[i:j])
            if not frames:
                return val
            frames[-1][1].append(val)
            i = j
    return 0


class MyQueue:
    """stack (two stacks): 232 Implement Queue using Stacks, amortised O(1) per op."""

    def __init__(self) -> None:
        """Create an empty queue."""
        self.inbox: list[int] = []
        self.outbox: list[int] = []

    def push(self, x: int) -> None:
        """Enqueue x."""
        self.inbox.append(x)

    def _shift(self) -> None:
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self) -> int:
        """Dequeue the front element."""
        self._shift()
        return self.outbox.pop()

    def peek(self) -> int:
        """Return the front element."""
        self._shift()
        return self.outbox[-1]

    def empty(self) -> bool:
        """Return True when the queue holds nothing."""
        return not self.inbox and not self.outbox


# ── linked lists ────────────────────────────────────────────────────────────────────────────────


def lc2_add_two_numbers(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
    """linked-list: walk both with a carry onto a dummy head. O(n)."""
    dummy = tail = ListNode()
    carry = 0
    while l1 or l2 or carry:
        total = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
        l1 = l1.next if l1 else None
        l2 = l2.next if l2 else None
    return dummy.next


def lc21_merge_two_lists(list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
    """linked-list: splice the smaller head onto a dummy tail. O(n + m)."""
    dummy = tail = ListNode()
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next, list1 = list1, list1.next
        else:
            tail.next, list2 = list2, list2.next
        tail = tail.next
    tail.next = list1 or list2
    return dummy.next


def lc876_middle_node(head: ListNode | None) -> ListNode | None:
    """fast-slow-pointers: slow is at the (second) middle when fast falls off. O(n)."""
    slow = fast = head
    while slow is not None and fast is not None and fast.next is not None:
        slow, fast = slow.next, fast.next.next
    return slow


def lc287_find_duplicate(nums: list[int]) -> int:
    """fast-slow-pointers: i -> nums[i] is a functional graph; the cycle entry is the dup. O(n)."""
    slow = fast = nums[0]
    while True:
        slow, fast = nums[slow], nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow, fast = nums[slow], nums[fast]
    return slow


def lc202_is_happy(n: int) -> bool:
    """fast-slow-pointers: digit-square map either reaches 1 or cycles. O(log n) per step."""

    def step(x: int) -> int:
        return sum(int(d) ** 2 for d in str(x))

    slow, fast = n, step(n)
    while fast not in (1, slow):
        slow, fast = step(slow), step(step(fast))
    return fast == 1


# ── trees ───────────────────────────────────────────────────────────────────────────────────────


def lc100_is_same_tree(p: TreeNode | None, q: TreeNode | None) -> bool:
    """tree-dfs: same value and both subtrees equal. O(n)."""
    if not p or not q:
        return p is q
    return (
        p.val == q.val
        and lc100_is_same_tree(p.left, q.left)
        and lc100_is_same_tree(p.right, q.right)
    )


def lc112_has_path_sum(root: TreeNode | None, target_sum: int) -> bool:
    """tree-dfs: subtract on the way down; check at leaves. O(n)."""
    if not root:
        return False
    rest = target_sum - root.val
    if not root.left and not root.right:
        return rest == 0
    return lc112_has_path_sum(root.left, rest) or lc112_has_path_sum(root.right, rest)


def lc1448_good_nodes(root: TreeNode | None) -> int:
    """tree-dfs: carry the max on the root-to-node path. O(n)."""
    count, stack = 0, [(root, float("-inf"))]
    while stack:
        node, best = stack.pop()
        if node:
            if node.val >= best:
                count += 1
            best = max(best, node.val)
            stack += [(node.left, best), (node.right, best)]
    return count


# ── graphs ──────────────────────────────────────────────────────────────────────────────────────


def lc200_num_islands(grid: list[list[str]]) -> int:
    """dfs: flood-fill each unseen '1' cell. O(rows * cols)."""
    rows, cols = len(grid), len(grid[0])
    seen, count = set(), 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    x, y = stack.pop()
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if (
                            0 <= nx < rows
                            and 0 <= ny < cols
                            and grid[nx][ny] == "1"
                            and (nx, ny) not in seen
                        ):
                            seen.add((nx, ny))
                            stack.append((nx, ny))
    return count


def lc419_count_battleships(board: list[list[str]]) -> int:
    """matrix: count each ship once at its top-left cell; one pass, O(1) space."""
    return sum(
        1
        for r, row in enumerate(board)
        for c, v in enumerate(row)
        if v == "X" and (r == 0 or board[r - 1][c] != "X") and (c == 0 or row[c - 1] != "X")
    )


def lc547_find_circle_num(is_connected: list[list[int]]) -> int:
    """union-find: union every connected pair; count roots. O(n^2 alpha(n))."""
    parent = list(range(len(is_connected)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, row in enumerate(is_connected):
        for j in range(i + 1, len(row)):
            if row[j]:
                parent[find(i)] = find(j)
    return sum(1 for i in range(len(parent)) if find(i) == i)


def lc261_valid_tree(n: int, edges: list[list[int]]) -> bool:
    """union-find: exactly n-1 edges and no edge closes a cycle. O(n alpha(n))."""
    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True


def lc207_can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    """topological-sort (Kahn): all courses get processed iff the graph is acyclic. O(V + E)."""
    graph: dict[int, list[int]] = defaultdict(list)
    indeg = [0] * num_courses
    for course, pre in prerequisites:
        graph[pre].append(course)
        indeg[course] += 1
    q = deque(i for i, d in enumerate(indeg) if d == 0)
    done = 0
    while q:
        node = q.popleft()
        done += 1
        for nxt in graph[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return done == num_courses


def lc1514_max_probability(
    n: int, edges: list[list[int]], succ_prob: list[float], start_node: int, end_node: int
) -> float:
    """Dijkstra (max-product): probabilities <= 1 never grow along a path, so greedy holds."""
    graph: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for (a, b), p in zip(edges, succ_prob, strict=True):
        graph[a].append((b, p))
        graph[b].append((a, p))
    best = [0.0] * n
    best[start_node] = 1.0
    heap = [(-1.0, start_node)]
    while heap:
        neg, node = heapq.heappop(heap)
        if node == end_node:
            return -neg
        if -neg < best[node]:
            continue
        for nxt, p in graph[node]:
            cand = -neg * p
            if cand > best[nxt]:
                best[nxt] = cand
                heapq.heappush(heap, (-cand, nxt))
    return 0.0


def lc3970_shortest_path(n: int, edges: list[list[int]], labels: str, k: int) -> int:
    """Dijkstra on expanded state (node, current run length). O(k (V+E) log(kV))."""
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in edges:
        graph[u].append((v, w))
    dist: dict[tuple[int, int], int] = {(0, 1): 0}
    heap = [(0, 0, 1)]
    while heap:
        d, u, run = heapq.heappop(heap)
        if u == n - 1:
            return d
        if d > dist[(u, run)]:
            continue
        for v, w in graph[u]:
            nxt = run + 1 if labels[v] == labels[u] else 1
            if nxt <= k and d + w < dist.get((v, nxt), float("inf")):
                dist[(v, nxt)] = d + w
                heapq.heappush(heap, (d + w, v, nxt))
    return -1


def _grid_steps(n: int, r: int, c: int) -> list[tuple[int, int]]:
    """In-bounds 4-neighbours of (r, c) in an n x n grid."""
    steps = ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
    return [(a, b) for a, b in steps if 0 <= a < n and 0 <= b < n]


def lc2812_maximum_safeness_factor(grid: list[list[int]]) -> int:
    """Bfs (multi-source distance to thieves) + dijkstra (maximise the path minimum)."""
    n = len(grid)
    dist = [[-1] * n for _ in range(n)]
    q = deque((r, c) for r in range(n) for c in range(n) if grid[r][c] == 1)
    for r, c in q:
        dist[r][c] = 0
    while q:
        r, c = q.popleft()
        for nr, nc in _grid_steps(n, r, c):
            if dist[nr][nc] < 0:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    best = [[-1] * n for _ in range(n)]
    heap = [(-dist[0][0], 0, 0)]
    best[0][0] = dist[0][0]
    while heap:
        neg, r, c = heapq.heappop(heap)
        if (r, c) == (n - 1, n - 1):
            return -neg
        for nr, nc in _grid_steps(n, r, c):
            cand = min(-neg, dist[nr][nc])
            if cand > best[nr][nc]:
                best[nr][nc] = cand
                heapq.heappush(heap, (-cand, nr, nc))
    return 0


# ── intervals / design ──────────────────────────────────────────────────────────────────────────


def lc56_merge(intervals: list[list[int]]) -> list[list[int]]:
    """intervals: sort by start, extend or append. O(n log n)."""
    out: list[list[int]] = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def lc759_employee_free_time(schedule: list[list[list[int]]]) -> list[list[int]]:
    """Intervals (+ heap k-way merge): merge everyone's busy time; gaps are free. O(n log n)."""
    out: list[list[int]] = []
    end = None
    for s, e in sorted(iv for emp in schedule for iv in emp):
        if end is not None and s > end:
            out.append([end, s])
        end = e if end is None else max(end, e)
    return out


class RangeModule:
    """intervals (sorted boundary list + bisect): 715 Range Module, O(log n + k) per op."""

    def __init__(self) -> None:
        """Track no ranges; `bounds` alternates start, end, start, end ... (half-open)."""
        self.bounds: list[int] = []

    def addRange(self, left: int, right: int) -> None:  # noqa: N802
        """Track every number in [left, right)."""
        i, j = bisect.bisect_left(self.bounds, left), bisect.bisect_right(self.bounds, right)
        self.bounds[i:j] = [left] * (i % 2 == 0) + [right] * (j % 2 == 0)

    def queryRange(self, left: int, right: int) -> bool:  # noqa: N802
        """Return True if every number in [left, right) is tracked."""
        i, j = bisect.bisect_right(self.bounds, left), bisect.bisect_left(self.bounds, right)
        return i == j and i % 2 == 1

    def removeRange(self, left: int, right: int) -> None:  # noqa: N802
        """Stop tracking every number in [left, right)."""
        i, j = bisect.bisect_left(self.bounds, left), bisect.bisect_right(self.bounds, right)
        self.bounds[i:j] = [left] * (i % 2 == 1) + [right] * (j % 2 == 1)


class Logger:
    """hash-map: 359 Logger Rate Limiter — next allowed timestamp per message."""

    def __init__(self) -> None:
        """Start with no messages seen."""
        self.next_ok: dict[str, int] = {}

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:  # noqa: N802
        """Allow a message at most once every 10 seconds."""
        if timestamp < self.next_ok.get(message, 0):
            return False
        self.next_ok[message] = timestamp + 10
        return True


class WeightedPicker:
    """prefix-sum + binary-search: 528 Random Pick with Weight. O(n) build, O(log n) pick."""

    def __init__(self, w: list[int], rng: random.Random | None = None) -> None:
        """Precompute cumulative weights."""
        self.prefix = lc1480_running_sum(w)
        self.rng = rng or random.Random()  # noqa: S311

    def pickIndex(self) -> int:  # noqa: N802
        """Return index i with probability w[i] / sum(w)."""
        return bisect.bisect_left(self.prefix, self.rng.randint(1, self.prefix[-1]))


# ── greedy / heap ───────────────────────────────────────────────────────────────────────────────


def lc121_max_profit(prices: list[int]) -> int:
    """greedy: best sell today minus the cheapest buy so far. O(n)."""
    low, best = float("inf"), 0
    for p in prices:
        low = min(low, p)
        best = max(best, p - low)
    return int(best)


def lc53_max_sub_array(nums: list[int]) -> int:
    """kadane: best subarray ending here = max(x, best_ending_prev + x). O(n)."""
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def lc621_least_interval(tasks: list[str], n: int) -> int:
    """Greedy (counting): frames of the most frequent task, n+1 slots each. O(T)."""
    counts = Counter(tasks).values()
    top = max(counts)
    ties = sum(1 for c in counts if c == top)
    return max(len(tasks), (top - 1) * (n + 1) + ties)


def lc1046_last_stone_weight(stones: list[int]) -> int:
    """heap: smash the two heaviest repeatedly. O(n log n)."""
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        a, b = -heapq.heappop(heap), -heapq.heappop(heap)
        if a != b:
            heapq.heappush(heap, b - a)
    return -heap[0] if heap else 0


def lc1405_longest_diverse_string(a: int, b: int, c: int) -> str:
    """Greedy + heap: take the most plentiful letter unless it would make three in a row."""
    heap = [(-cnt, ch) for cnt, ch in ((a, "a"), (b, "b"), (c, "c")) if cnt]
    heapq.heapify(heap)
    out: list[str] = []
    while heap:
        cnt, ch = heapq.heappop(heap)
        if len(out) >= 2 and out[-1] == out[-2] == ch:  # noqa: PLR2004
            if heap:
                cnt2, ch2 = heapq.heappop(heap)
                out.append(ch2)
                if cnt2 + 1:
                    heapq.heappush(heap, (cnt2 + 1, ch2))
                heapq.heappush(heap, (cnt, ch))
        else:
            out.append(ch)
            if cnt + 1:
                heapq.heappush(heap, (cnt + 1, ch))
    return "".join(out)


def lc3863_min_operations(s: str) -> int:
    """Greedy (case analysis): answer is always 0, 1, 2, 3 or -1. O(n)."""
    if all(s[i] <= s[i + 1] for i in range(len(s) - 1)):
        return 0
    if len(s) == 2:  # noqa: PLR2004 - the only allowed substrings are single letters
        return -1
    lo, hi = min(s), max(s)
    if s[0] == lo or s[-1] == hi:
        return 1
    if lo in s[1:-1] or hi in s[1:-1]:
        return 2
    return 3


def lc179_largest_number(nums: list[int]) -> str:
    """Sorting (custom comparator): a before b iff a+b > b+a as strings. O(n log n)."""
    words = sorted(map(str, nums), key=cmp_to_key(lambda a, b: (b + a > a + b) - (b + a < a + b)))
    return "0" if words[0] == "0" else "".join(words)


def lc912_sort_array(nums: list[int]) -> list[int]:
    """Sorting (bottom-up merge sort): guaranteed O(n log n), stable."""
    arr, width = nums[:], 1
    while width < len(arr):
        merged: list[int] = []
        for lo in range(0, len(arr), 2 * width):
            left, right = arr[lo : lo + width], arr[lo + width : lo + 2 * width]
            i = j = 0
            while i < len(left) and j < len(right):
                if left[i] <= right[j]:
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
            merged += left[i:] + right[j:]
        arr, width = merged, width * 2
    return arr


def lc462_min_moves2(nums: list[int]) -> int:
    """Sorting (median): the median minimises total absolute distance. O(n log n)."""
    nums = sorted(nums)
    med = nums[len(nums) // 2]
    return sum(abs(x - med) for x in nums)


def lc3886_sum_of_sortable(nums: list[int]) -> int:
    """Sorting check per divisor k: each block is a rotated run, blocks don't overlap in value."""
    n, total = len(nums), 0
    for k in range(1, n + 1):
        if n % k:
            continue
        ok, prev_max = True, float("-inf")
        for lo in range(0, n, k):
            block = nums[lo : lo + k]
            drops = sum(1 for i in range(k) if block[i] > block[(i + 1) % k])
            if drops > 1 or min(block) < prev_max:
                ok = False
                break
            prev_max = max(block)
        if ok:
            total += k
    return total


def lc3644_sort_permutation(nums: list[int]) -> int:
    """bit-manipulation: every misplaced value must keep all bits of k → AND of them. O(n)."""
    mask, misplaced = -1, False
    for i, v in enumerate(nums):
        if v != i:
            mask &= v
            misplaced = True
    return mask if misplaced else 0


def lc136_single_number(nums: list[int]) -> int:
    """bit-manipulation: XOR cancels pairs. O(n), O(1) space.

    The hash-map version, `next(x for x, c in Counter(nums).items() if c == 1)`, is also O(n) but
    needs O(n) space; XOR is optimal because the other values appear exactly twice.
    """
    out = 0
    for x in nums:
        out ^= x
    return out


# ── dynamic programming ─────────────────────────────────────────────────────────────────────────


def lc70_climb_stairs(n: int) -> int:
    """dp-1d: ways(n) = ways(n-1) + ways(n-2). O(n), O(1) space."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def lc509_fib(n: int) -> int:
    """dp-1d: rolling pair. O(n)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def lc416_can_partition(nums: list[int]) -> bool:
    """dp-knapsack: bitset of reachable subset sums. O(n * sum / wordsize)."""
    total = sum(nums)
    if total % 2:
        return False
    reach = 1
    for x in nums:
        reach |= reach << x
    return bool(reach >> (total // 2) & 1)


def lc1218_longest_subsequence(arr: list[int], difference: int) -> int:
    """dp-1d + hash-map: best[v] = best[v - difference] + 1. O(n)."""
    best: dict[int, int] = {}
    for x in arr:
        best[x] = best.get(x - difference, 0) + 1
    return max(best.values())


def lc1048_longest_str_chain(words: list[str]) -> int:
    """dp-1d + hash-map: by length, chain[w] = 1 + max chain[w minus one letter]. O(n L^2)."""
    chain: dict[str, int] = {}
    for w in sorted(set(words), key=len):
        chain[w] = 1 + max((chain.get(w[:i] + w[i + 1 :], 0) for i in range(len(w))), default=0)
    return max(chain.values())


def lc1911_max_alternating_sum(nums: list[int]) -> int:
    """dp-1d (state machine): best sum ending on an even (+) or odd (-) pick. O(n)."""
    even, odd = 0, 0
    for x in nums:
        even, odd = max(even, odd + x), max(odd, even - x)
    return even


def lc1143_longest_common_subsequence(text1: str, text2: str) -> int:
    """dp-2d: match → diag + 1, else max(up, left); one rolling row. O(n m)."""
    prev = [0] * (len(text2) + 1)
    for a in text1:
        cur = [0]
        for j, b in enumerate(text2):
            cur.append(prev[j] + 1 if a == b else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def lc72_min_distance(word1: str, word2: str) -> int:
    """dp-2d (Levenshtein): insert/delete/replace from the three neighbours. O(n m)."""
    prev = list(range(len(word2) + 1))
    for i, a in enumerate(word1, 1):
        cur = [i]
        for j, b in enumerate(word2, 1):
            cur.append(prev[j - 1] if a == b else 1 + min(prev[j - 1], prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def lc5_longest_palindrome(s: str) -> str:
    """two-pointers (expand around centre): 2n-1 centres. O(n^2), O(1) space."""
    best = (0, 0)
    for c in range(2 * len(s) - 1):
        lo, hi = c // 2, c // 2 + c % 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo, hi = lo - 1, hi + 1
        if hi - lo - 1 > best[1] - best[0]:
            best = (lo + 1, hi)
    return s[best[0] : best[1]]


def lc118_generate(num_rows: int) -> list[list[int]]:
    """dp-1d: each row from the previous one. O(n^2)."""
    rows = [[1]]
    for _ in range(num_rows - 1):
        prev = rows[-1]
        rows.append([1] + [prev[i] + prev[i + 1] for i in range(len(prev) - 1)] + [1])
    return rows[:num_rows]


def lc22_generate_parenthesis(n: int) -> list[str]:
    """backtracking: add '(' while opens < n, ')' while closes < opens. O(Catalan(n))."""
    out: list[str] = []

    def go(cur: str, opens: int, closes: int) -> None:
        if len(cur) == 2 * n:
            out.append(cur)
            return
        if opens < n:
            go(cur + "(", opens + 1, closes)
        if closes < opens:
            go(cur + ")", opens, closes + 1)

    go("", 0, 0)
    return out


# ── math / strings / simulation ─────────────────────────────────────────────────────────────────


def lc9_is_palindrome(x: int) -> bool:
    """math: reverse the lower half of the digits. O(log x)."""
    if x < 0 or (x % 10 == 0 and x):
        return False
    rev = 0
    while x > rev:
        x, d = divmod(x, 10)
        rev = rev * 10 + d
    return x in (rev, rev // 10)


def lc2235_sum(num1: int, num2: int) -> int:
    """math: num1 + num2."""
    return num1 + num2


def lc50_my_pow(x: float, n: int) -> float:
    """Math (fast exponentiation): square-and-multiply. O(log n)."""
    if n < 0:
        x, n = 1 / x, -n
    out = 1.0
    while n:
        if n & 1:
            out *= x
        x *= x
        n >>= 1
    return out


def lc1922_count_good_numbers(n: int) -> int:
    """Math (fast modular power): 5 choices at even indices, 4 at odd. O(log n)."""
    return pow(5, (n + 1) // 2, MOD) * pow(4, n // 2, MOD) % MOD


def lc3736_min_moves(nums: list[int]) -> int:
    """math: raise everything to the max. O(n)."""
    top = max(nums)
    return sum(top - x for x in nums)


def lc13_roman_to_int(s: str) -> int:
    """hash-map: subtract a numeral when a larger one follows it. O(n)."""
    val = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, ch in enumerate(s):
        v = val[ch]
        total += -v if i + 1 < len(s) and val[s[i + 1]] > v else v
    return total


def lc14_longest_common_prefix(strs: list[str]) -> str:
    """strings: the min and max strings bound every prefix. O(n L)."""
    if not strs:
        return ""
    lo, hi = min(strs), max(strs)
    i = 0
    while i < len(lo) and lo[i] == hi[i]:
        i += 1
    return lo[:i]


def lc6_convert(s: str, num_rows: int) -> str:
    """simulation: walk rows down and up, appending each char to its row. O(n)."""
    if num_rows == 1:
        return s
    rows, r, step = [""] * num_rows, 0, 1
    for ch in s:
        rows[r] += ch
        if r == 0:
            step = 1
        elif r == num_rows - 1:
            step = -1
        r += step
    return "".join(rows)


def lc8_my_atoi(s: str) -> int:
    """Simulation (state machine): spaces, sign, digits, clamp to int32. O(n)."""
    i, n = 0, len(s)
    while i < n and s[i] == " ":
        i += 1
    sign = 1
    if i < n and s[i] in "+-":
        sign = -1 if s[i] == "-" else 1
        i += 1
    num = 0
    while i < n and s[i].isdigit() and s[i].isascii():
        num = num * 10 + int(s[i])
        i += 1
    return max(-(2**31), min(2**31 - 1, sign * num))


def lc54_spiral_order(matrix: list[list[int]]) -> list[int]:
    """matrix: peel the first row, rotate the rest counter-clockwise. O(rows * cols)."""
    out: list[int] = []
    m = [row[:] for row in matrix]
    while m:
        out += m.pop(0)
        m = [list(row) for row in zip(*m, strict=True)][::-1]
    return out


# ── SQL (run on sqlite by the verifier) ─────────────────────────────────────────────────────────

SQL: dict[int, str] = {
    175: "SELECT p.firstName, p.lastName, a.city, a.state "
    "FROM Person p LEFT JOIN Address a ON p.personId = a.personId",
    181: "SELECT e.name AS Employee FROM Employee e "
    "JOIN Employee m ON e.managerId = m.id WHERE e.salary > m.salary",
    584: "SELECT name FROM Customer WHERE referee_id IS NULL OR referee_id != 2",
    1757: "SELECT product_id FROM Products WHERE low_fats = 'Y' AND recyclable = 'Y'",
}


@lru_cache(maxsize=1)
def by_id() -> dict[int, Any]:
    """Map LeetCode id -> solution function, class, or SQL string."""
    out: dict[int, Any] = dict(SQL)
    for name, obj in globals().items():
        if name.startswith("lc") and callable(obj):
            out[int(name[2:].split("_", 1)[0])] = obj
    out.update({232: MyQueue, 715: RangeModule, 359: Logger, 528: WeightedPicker})
    return out
