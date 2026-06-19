"""
End-to-end tests: run a correct solution for every question through the
code harness and verify the output matches each test case's expected value.
"""

import json
from pathlib import Path
import pytest
from app.services.judge0_service import _execute_local
from app.services.code_harness import (
    build_test_code,
    build_class_test_code,
    outputs_match,
)
from app.models.question import Question

QUESTIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "questions.json"

with open(QUESTIONS_PATH) as f:
    ALL_QUESTIONS: list[Question] = [Question(**q) for q in json.load(f)]

QUESTIONS_BY_ID = {q.id: q for q in ALL_QUESTIONS}

# ---------------------------------------------------------------------------
# Reference solutions — one per question
# ---------------------------------------------------------------------------
SOLUTIONS: dict[str, str] = {
    # ---- Easy ----
    "lc-1": """
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in seen:
            return [seen[diff], i]
        seen[n] = i
""",
    "lc-20": """
def isValid(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in pairs:
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:
            stack.append(c)
    return not stack
""",
    "lc-70": """
def climbStairs(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
""",
    "lc-121": """
def maxProfit(prices):
    min_price = float('inf')
    max_profit = 0
    for p in prices:
        min_price = min(min_price, p)
        max_profit = max(max_profit, p - min_price)
    return max_profit
""",
    "lc-141": """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def hasCycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
""",
    "lc-206": """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverseList(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
""",
    "lc-226": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def invertTree(root):
    if not root:
        return None
    root.left, root.right = invertTree(root.right), invertTree(root.left)
    return root
""",
    "lc-242": """
def isAnagram(s, t):
    if len(s) != len(t):
        return False
    counts = {}
    for c in s:
        counts[c] = counts.get(c, 0) + 1
    for c in t:
        counts[c] = counts.get(c, 0) - 1
        if counts[c] < 0:
            return False
    return True
""",
    "lc-704": """
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
    "lc-733": """
def floodFill(image, sr, sc, color):
    orig = image[sr][sc]
    if orig == color:
        return image
    rows, cols = len(image), len(image[0])
    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        if image[r][c] != orig:
            return
        image[r][c] = color
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    dfs(sr, sc)
    return image
""",
    # ---- Medium ----
    "lc-146": """
class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.cache = {}
        self.order = []

    def get(self, key):
        if key not in self.cache:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.cap:
            lru = self.order.pop(0)
            del self.cache[lru]
        self.cache[key] = value
        self.order.append(key)
""",
    "lc-3": """
def lengthOfLongestSubstring(s):
    seen = {}
    left = 0
    result = 0
    for right, c in enumerate(s):
        if c in seen and seen[c] >= left:
            left = seen[c] + 1
        seen[c] = right
        result = max(result, right - left + 1)
    return result
""",
    "lc-56": """
def merge(intervals):
    intervals.sort()
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""",
    "lc-200": """
def numIslands(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0
    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '0'
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    return count
""",
    "lc-322": """
def coinChange(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] != float('inf') else -1
""",
    "lc-102": """
from collections import deque

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def levelOrder(root):
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
""",
    "lc-153": """
def findMin(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]
""",
    "lc-238": """
def productExceptSelf(nums):
    n = len(nums)
    result = [1] * n
    prefix = 1
    for i in range(n):
        result[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in range(n - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]
    return result
""",
    "lc-739": """
def dailyTemperatures(temperatures):
    n = len(temperatures)
    result = [0] * n
    stack = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)
    return result
""",
    "lc-79": """
def exist(board, word):
    rows, cols = len(board), len(board[0])
    def dfs(r, c, k):
        if k == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[k]:
            return False
        tmp = board[r][c]
        board[r][c] = '#'
        found = (dfs(r+1,c,k+1) or dfs(r-1,c,k+1) or
                 dfs(r,c+1,k+1) or dfs(r,c-1,k+1))
        board[r][c] = tmp
        return found
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False
""",
    "lc-98": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def isValidBST(root):
    def check(node, lo, hi):
        if not node:
            return True
        if node.val <= lo or node.val >= hi:
            return False
        return check(node.left, lo, node.val) and check(node.right, node.val, hi)
    return check(root, float('-inf'), float('inf'))
""",
    "lc-417": """
from collections import deque

def pacificAtlantic(heights):
    if not heights:
        return []
    rows, cols = len(heights), len(heights[0])
    def bfs(starts):
        visited = set(starts)
        queue = deque(starts)
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and heights[nr][nc] >= heights[r][c]:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return visited
    pacific = [(r, 0) for r in range(rows)] + [(0, c) for c in range(1, cols)]
    atlantic = [(r, cols-1) for r in range(rows)] + [(rows-1, c) for c in range(cols-1)]
    p = bfs(pacific)
    a = bfs(atlantic)
    return sorted([list(x) for x in p & a])
""",
    "lc-435": """
def eraseOverlapIntervals(intervals):
    intervals.sort(key=lambda x: x[1])
    count = 0
    end = float('-inf')
    for s, e in intervals:
        if s >= end:
            end = e
        else:
            count += 1
    return count
""",
    "lc-128": """
def longestConsecutive(nums):
    s = set(nums)
    best = 0
    for n in s:
        if n - 1 not in s:
            cur = n
            length = 1
            while cur + 1 in s:
                cur += 1
                length += 1
            best = max(best, length)
    return best
""",
    "lc-49": """
from collections import defaultdict

def groupAnagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = ''.join(sorted(s))
        groups[key].append(s)
    result = []
    for g in groups.values():
        result.append(sorted(g))
    return sorted(result)
""",
    # ---- Hard ----
    "lc-297": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    def serialize(self, root):
        if not root:
            return 'N'
        return str(root.val) + ',' + self.serialize(root.left) + ',' + self.serialize(root.right)

    def deserialize(self, data):
        vals = iter(data.split(','))
        def build():
            v = next(vals)
            if v == 'N':
                return None
            node = TreeNode(int(v))
            node.left = build()
            node.right = build()
            return node
        return build()
""",
    "lc-239": """
from collections import deque

def maxSlidingWindow(nums, k):
    dq = deque()
    result = []
    for i, n in enumerate(nums):
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        while dq and nums[dq[-1]] <= n:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
""",
    "lc-23": """
import heapq

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def mergeKLists(lists):
    heap = []
    for idx, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, idx, head))
    dummy = ListNode(0)
    curr = dummy
    while heap:
        val, idx, node = heapq.heappop(heap)
        curr.next = node
        curr = curr.next
        if node.next:
            heapq.heappush(heap, (node.next.val, idx, node.next))
    return dummy.next
""",
    "lc-42": """
def trap(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water
""",
    "lc-76": """
from collections import Counter

def minWindow(s, t):
    need = Counter(t)
    missing = len(t)
    left = 0
    best = (0, float('inf'))
    for right, c in enumerate(s):
        if need[c] > 0:
            missing -= 1
        need[c] -= 1
        while missing == 0:
            if right - left < best[1] - best[0]:
                best = (left, right)
            need[s[left]] += 1
            if need[s[left]] > 0:
                missing += 1
            left += 1
    return '' if best[1] == float('inf') else s[best[0]:best[1]+1]
""",
}

# ---------------------------------------------------------------------------
# Build parametrize list: (question_id, test_case_index)
# ---------------------------------------------------------------------------
_PARAMS = []
for q in ALL_QUESTIONS:
    for i in range(len(q.test_cases)):
        _PARAMS.append(pytest.param(q.id, i, id=f"{q.id}-tc{i}"))


@pytest.mark.parametrize("question_id,tc_index", _PARAMS)
async def test_solution(question_id: str, tc_index: int):
    question = QUESTIONS_BY_ID[question_id]
    tc = question.test_cases[tc_index]
    solution = SOLUTIONS[question_id]

    if question.function_name:
        code = build_test_code(
            solution,
            tc.input,
            question.function_name,
            question.params,
            question.return_type,
        )
    else:
        code = build_class_test_code(solution, tc.input)

    result = await _execute_local(code, "python")

    assert result.status == "Accepted", (
        f"[{question_id}] Execution failed:\n{result.stderr}"
    )

    actual = result.stdout.strip()
    expected = tc.output.strip()
    assert outputs_match(actual, expected), (
        f"[{question_id}] Output mismatch:\n"
        f"  input:    {tc.input}\n"
        f"  expected: {expected}\n"
        f"  actual:   {actual}"
    )
