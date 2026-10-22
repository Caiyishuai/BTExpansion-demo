"""BTNode —— IR 树节点。

只有四种节点，和运行时一一对应：

    selector    回退/选择：从左到右试，第一个可行分支即可
    sequence    顺序：从左到右做，全部可行才可行
    condition   条件：一组文字（literals）全部成立才成立
    action      动作：执行一个 Action

用工厂方法建节点，读起来就是树本身：

    BTNode.selector(children=[
        BTNode.condition({"At(b,ab)"}),
        BTNode.sequence(children=[
            BTNode.condition({"Free(ab)", "WayClear"}),
            BTNode.action(move_action),
        ]),
    ])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from btplan.core.action import Action

SELECTOR = "selector"
SEQUENCE = "sequence"
CONDITION = "condition"
ACTION = "action"

_LEAF_TYPES = (CONDITION, ACTION)


@dataclass
class BTNode:
    """IR 树节点（纯数据）。"""

    node_type: str
    children: List["BTNode"] = field(default_factory=list)
    literals: Iterable[str] = field(default_factory=frozenset)  # condition 用
    action: Optional[Action] = None                             # action 用
    info: dict = field(default_factory=dict)                    # 名字、代价等元数据

    def __post_init__(self) -> None:
        self.literals = frozenset(self.literals)

    # ---------------------------- 工厂方法 ---------------------------- #

    @classmethod
    def selector(cls, children: Iterable["BTNode"] = (), **info) -> "BTNode":
        return cls(SELECTOR, children=list(children), info=info)

    @classmethod
    def sequence(cls, children: Iterable["BTNode"] = (), **info) -> "BTNode":
        return cls(SEQUENCE, children=list(children), info=info)

    @classmethod
    def condition(cls, literals: Iterable[str], **info) -> "BTNode":
        return cls(CONDITION, literals=frozenset(literals), info=info)

    @classmethod
    def action(cls, action: Action, **info) -> "BTNode":
        return cls(ACTION, action=action, info=info)

    # ---------------------------- 常用属性 ---------------------------- #

    @property
    def name(self) -> str:
        """可读名字：动作用动作名，条件用"文字 & 文字"。"""
        if self.node_type == ACTION:
            return self.action.name if self.action else "<action>"
        if self.node_type == CONDITION:
            return " & ".join(sorted(map(str, self.literals))) or "true"
        return self.node_type

    @property
    def is_leaf(self) -> bool:
        return self.node_type in _LEAF_TYPES

    def add_child(self, child: "BTNode") -> "BTNode":
        self.children.append(child)
        return child

    def count_size(self) -> int:
        """树中节点总数（含自己）。"""
        return 1 + sum(child.count_size() for child in self.children)

    def to_text(self, indent: int = 0) -> str:
        """把树打印成缩进文本（调试用）。"""
        pad = "    " * indent
        header = f"{'cond' if self.node_type == CONDITION else 'act'} {self.name}" \
            if self.is_leaf else self.node_type
        lines = [pad + header]
        for child in self.children:
            lines.append(child.to_text(indent + 1))
        return "\n".join(lines)

    def print_tree(self) -> None:
        print(self.to_text())
