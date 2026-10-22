"""行为树节点（py_trees）。

节点只有三类，记住它们的语义就够了：

    Fallback（回退/选择）  从左到右试，第一个成功的分支即为成功
    Sequence（顺序）       从左到右做，全部成功才算成功
    ConditionNode          条件叶节点：读环境，返回 SUCCESS / FAILURE
    ActionNode             动作叶节点：改环境，返回 SUCCESS / FAILURE / RUNNING

重要：所有控制节点固定 ``memory=False``。BT Expansion 的正确性建立在
"每个 tick 都从根重新评估"之上，带 memory 的选择节点会锁死在旧分支上。

想写自己的节点，继承 ``ConditionNode`` 或 ``ActionNode`` 并实现 ``update()``
即可，参见 examples/01_hello_bt.py 的第二幕。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Optional

import py_trees as pt
from py_trees.common import Status

from btplan.core.predicate import format_predicate, parse_predicate

if TYPE_CHECKING:
    from btplan.env.protocol import Environment

__all__ = [
    "Status",
    "BehaviorNode",
    "ConditionNode",
    "ActionNode",
    "Sequence",
    "Fallback",
    "CompositeCondition",
    "make_condition",
    "make_action",
]


class BehaviorNode(pt.behaviour.Behaviour):
    """所有叶子节点的基类。

    负责两件小事：把参数拼成规范名字（``At(b,ab)``），以及持有环境引用。
    名字刻意与符号状态的文字拼写完全一致，这样"规划里的文字"和"运行时的
    节点"天然对得上。
    """

    print_prefix = ""

    def __init__(self, *args: str) -> None:
        self.args: tuple = tuple(str(a) for a in args)
        self.env: Optional["Environment"] = None
        super().__init__(name=self._build_name())

    def _build_name(self) -> str:
        return format_predicate(type(self).__name__, self.args)

    @property
    def literal(self) -> str:
        """该节点对应的符号文字，例如 ``At(b,ab)``。"""
        return self.name

    def bind_env(self, env: "Environment") -> None:
        """把环境注入节点（由 BehaviorTree.bind_env 递归调用）。"""
        self.env = env

    def _require_env(self) -> None:
        if self.env is None:
            raise RuntimeError(
                f"{self.name} 还没有绑定环境，请先调用 BehaviorTree.bind_env(env)"
            )

    def update(self) -> Status:  # pragma: no cover - 由子类实现
        raise NotImplementedError(
            f"{type(self).__name__} 需要实现 update() -> Status"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({','.join(self.args)})"


class ConditionNode(BehaviorNode):
    """条件叶节点：判断一个文字在当前状态里是否成立。

    默认语义（零配置即可用）：``literal in env.observe()``。
    要接真实传感器/模拟器时，继承它并重写 ``update()``。
    """

    print_prefix = "condition"

    def update(self) -> Status:
        self._require_env()
        return Status.SUCCESS if self.literal in self.env.observe() else Status.FAILURE


class ActionNode(BehaviorNode):
    """动作叶节点：前提满足时执行一步动作。

    默认语义（一步到位的符号动作）：

        * 前提不满足 -> FAILURE，不执行
        * 前提满足   -> env.apply(...) 并 SUCCESS

    需要多拍才能完成的动作（机械臂搬东西），返回 RUNNING，见
    examples/01_hello_bt.py 的 ``MoveSlowly``。
    """

    print_prefix = "action"

    def update(self) -> Status:
        self._require_env()
        if not self.env.is_applicable(self.literal):
            return Status.FAILURE
        self.env.apply(self.literal)
        return Status.SUCCESS


class Sequence(pt.composites.Sequence):
    """顺序节点：全部孩子成功才算成功。

    ``memory`` 固定为 False —— 每个 tick 从头重新评估。
    """

    def __init__(
        self,
        name: str = "Sequence",
        children: Optional[List[pt.behaviour.Behaviour]] = None,
    ) -> None:
        super().__init__(name=name, memory=False, children=list(children or []))

    def bind_env(self, env) -> None:
        for child in self.children:
            child.bind_env(env)


class Fallback(pt.composites.Selector):
    """回退（选择）节点：第一个成功的分支即为成功。

    ``memory`` 固定为 False —— 每个 tick 从头重新评估。
    """

    def __init__(
        self,
        name: str = "Fallback",
        children: Optional[List[pt.behaviour.Behaviour]] = None,
    ) -> None:
        super().__init__(name=name, memory=False, children=list(children or []))

    def bind_env(self, env) -> None:
        for child in self.children:
            child.bind_env(env)


class CompositeCondition(ConditionNode):
    """多文字条件：一组文字**全部**成立才算 SUCCESS。

    BT Expansion 里一个"条件结点"携带的是文字集合（如 ``{Free(ab), WayClear}``），
    py_trees 没有原生对应物，所以用一个叶子节点包住一棵 ``Sequence`` 子树：
    对外它仍然是一个节点（返回 SUCCESS/FAILURE），对内是若干个条件节点。
    """

    def __init__(
        self,
        literals: Iterable[str] = (),
        children: Optional[List[BehaviorNode]] = None,
    ) -> None:
        if children is None:
            children = [make_condition(x) for x in literals]
        self.literals: tuple = tuple(sorted(c.name for c in children))
        self.subtree_root = Sequence(name=self._join(children), children=children)
        self.subtree = pt.trees.BehaviourTree(self.subtree_root)
        super().__init__()

    @staticmethod
    def _join(children) -> str:
        return " & ".join(c.name for c in children) or "true"

    def _build_name(self) -> str:
        return self._join(self.subtree_root.children)

    def bind_env(self, env) -> None:
        super().bind_env(env)
        self.subtree_root.bind_env(env)

    def update(self) -> Status:
        self._require_env()
        self.subtree.tick()
        return self.subtree_root.status


def make_condition(literal: str) -> ConditionNode:
    """按文字造一个**默认语义**的条件节点。

    >>> make_condition("At(b,ab)").name
    'At(b,ab)'
    """
    cls_name, args = parse_predicate(literal)
    return type(cls_name, (ConditionNode,), {})(*args)


def make_action(literal: str) -> ActionNode:
    """按文字造一个**默认语义**的动作节点。

    >>> make_action("Move(b,ab)").name
    'Move(b,ab)'
    """
    cls_name, args = parse_predicate(literal)
    return type(cls_name, (ActionNode,), {})(*args)
