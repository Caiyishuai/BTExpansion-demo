"""符号求值：在不真正执行的前提下，判断一棵 IR 树能否从某个状态跑起来。

规划期每扩展一轮就要问一次"这棵树现在能从 start 跑起来了吗？"。
这里用轻量求值回答（纯集合运算），不去构造 py_trees、也不改状态：

    condition  文字 ⊆ 状态        -> success
    action     前提 ⊆ 状态        -> running（可以开始做）
    selector   任一孩子可行        -> 可行
    sequence   全部孩子可行        -> 可行

注意 action 返回 running 而不是 success：一次 tick 只是"开始做"这个动作，
所以只要前提满足，树就能运转起来。
"""

from __future__ import annotations

from btplan.ir.node import ACTION, CONDITION, SELECTOR, SEQUENCE, BTNode

SUCCESS = "success"
FAILURE = "failure"
RUNNING = "running"


def evaluate(node: BTNode, state) -> str:
    """返回 success / running / failure。"""
    if node.node_type == CONDITION:
        return SUCCESS if node.literals <= state else FAILURE

    if node.node_type == ACTION:
        return RUNNING if node.action.pre <= state else FAILURE

    if node.node_type == SELECTOR:
        for child in node.children:
            value = evaluate(child, state)
            if value in (SUCCESS, RUNNING):
                return value
        return FAILURE

    if node.node_type == SEQUENCE:
        for child in node.children:
            value = evaluate(child, state)
            if value == FAILURE:
                return FAILURE
            if value == RUNNING:
                return RUNNING
        return SUCCESS

    raise ValueError(f"未知节点类型：{node.node_type}")


def can_run(node: BTNode, state) -> bool:
    """这棵树能否从 `state` 开始运转（success 或 running 都算）。"""
    return evaluate(node, state) in (SUCCESS, RUNNING)
