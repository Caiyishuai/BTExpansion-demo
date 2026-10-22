"""IR → py_trees 编译器。

这是"规划"和"执行"之间唯一的一座桥：

    IR 节点          py_trees 节点
    selector     ->  Fallback（memory=False）
    sequence     ->  Sequence（memory=False）
    condition    ->  单个文字：ConditionNode
                     多个文字：CompositeCondition（内部是 Sequence 子树）
                     空集合  ：AlwaysTrue
    action       ->  ActionNode（名字相同的那个类）
"""

from __future__ import annotations

from typing import Optional

import py_trees as pt

from btplan.ir.node import ACTION, CONDITION, SELECTOR, SEQUENCE, BTNode
from btplan.runtime.library import BehaviorLibrary, make_action, make_condition
from btplan.runtime.nodes import CompositeCondition, ConditionNode, Fallback, Sequence


class AlwaysTrue(ConditionNode):
    """永远成立的条件（空文字集合，即"什么都不要求"）。"""

    def _build_name(self) -> str:
        return "true"

    def update(self) -> pt.common.Status:
        return pt.common.Status.SUCCESS


def compile_tree(
    node: BTNode,
    library: Optional[BehaviorLibrary] = None,
) -> pt.behaviour.Behaviour:
    """把 IR 树编译成可以直接 tick 的 py_trees 树。"""
    if node.node_type == SELECTOR:
        return Fallback(
            name=node.info.get("name", "Fallback"),
            children=[compile_tree(c, library) for c in node.children],
        )
    if node.node_type == SEQUENCE:
        return Sequence(
            name=node.info.get("name", "Sequence"),
            children=[compile_tree(c, library) for c in node.children],
        )
    if node.node_type == ACTION:
        return make_action(node.action.name, library)
    if node.node_type == CONDITION:
        return _compile_condition(node, library)
    raise ValueError(f"未知节点类型：{node.node_type}")


def _compile_condition(node: BTNode, library: Optional[BehaviorLibrary]):
    literals = sorted(map(str, node.literals))
    if not literals:
        return AlwaysTrue()
    if len(literals) == 1:
        return make_condition(literals[0], library)
    return CompositeCondition(children=[make_condition(x, library) for x in literals])
