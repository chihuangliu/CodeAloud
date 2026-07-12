import re

PREAMBLE = """
from collections import deque as _deque
import json as _json
null = None

def _to_linked_list(arr):
    if not arr:
        return None
    dummy = ListNode(0)
    curr = dummy
    for v in arr:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next

def _to_cycled_linked_list(arr, pos):
    if not arr:
        return None
    nodes = []
    dummy = ListNode(0)
    curr = dummy
    for v in arr:
        curr.next = ListNode(v)
        curr = curr.next
        nodes.append(curr)
    if pos >= 0:
        curr.next = nodes[pos]
    return dummy.next

def _from_linked_list(head):
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result

def _to_tree(arr):
    if not arr:
        return None
    root = TreeNode(arr[0])
    queue = _deque([root])
    i = 1
    while queue and i < len(arr):
        node = queue.popleft()
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root

def _from_tree(root):
    if not root:
        return []
    result = []
    queue = _deque([root])
    while queue:
        node = queue.popleft()
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result
"""

INPUT_CONVERTERS = {
    "ListNode": "_to_linked_list({name})",
    "CycledListNode": "_to_cycled_linked_list({name}, pos)",
    "TreeNode": "_to_tree({name})",
    "List[ListNode]": "[_to_linked_list(_x) for _x in {name}]",
}

OUTPUT_SERIALIZERS = {
    "ListNode": "_from_linked_list({result})",
    "TreeNode": "_from_tree({result})",
}


def build_test_code(
    user_code: str,
    test_input: str,
    function_name: str,
    params: list,
    return_type: str,
) -> str:
    parts = [PREAMBLE, user_code, ""]

    assignments = re.split(r",\s+(?=\w+\s*=)", test_input)
    parts.extend(assignments)

    func_args = []
    for p in params:
        converter = INPUT_CONVERTERS.get(p.type)
        if converter:
            parts.append(f"{p.name} = {converter.format(name=p.name)}")
        func_args.append(p.name)

    func_args = [
        a
        for a in func_args
        if not (any(p.type == "CycledListNode" for p in params) and a == "pos")
    ]

    args_str = ", ".join(func_args)
    parts.append(f"_result = {function_name}({args_str})")

    serializer = OUTPUT_SERIALIZERS.get(return_type)
    if serializer:
        parts.append(f"_result = {serializer.format(result='_result')}")

    parts.append("print(_json.dumps(_result))")
    return "\n".join(parts)


def build_class_test_code(user_code: str, test_input: str) -> str:
    if ";" in test_input:
        return _build_ops_test_code(user_code, test_input)
    return _build_roundtrip_test_code(user_code, test_input)


def _build_ops_test_code(user_code: str, test_input: str) -> str:
    ops = [op.strip() for op in test_input.split(";")]
    lines = [PREAMBLE, user_code, "", f"_obj = {ops[0]}", "_results = []"]
    for op in ops[1:]:
        lines.append(f"_r = _obj.{op}")
        lines.append("if _r is not None: _results.append(str(_r))")
    lines.append('print("; ".join(_results))')
    return "\n".join(lines)


def _build_roundtrip_test_code(user_code: str, test_input: str) -> str:
    assignments = re.split(r",\s+(?=\w+\s*=)", test_input)
    lines = [PREAMBLE, user_code, ""]
    lines.extend(assignments)
    lines.append("root = _to_tree(root)")
    lines.append("_codec = Codec()")
    lines.append("_result = _codec.deserialize(_codec.serialize(root))")
    lines.append("_result = _from_tree(_result)")
    lines.append("print(_json.dumps(_result))")
    return "\n".join(lines)


def outputs_match(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    return _normalize(actual) == _normalize(expected)


def _normalize(s: str) -> str:
    s = s.replace(" ", "").replace("'", '"')
    for old, new in [("True", "true"), ("False", "false"), ("None", "null")]:
        s = s.replace(old, new)
    return s
