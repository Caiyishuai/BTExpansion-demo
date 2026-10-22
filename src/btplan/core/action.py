"""动作模型（Action）：规划层与执行层共用的符号动作描述。

一个 Action 只描述"做什么、需要什么、改变什么"，本身不含可执行代码：

    Action(
        name="Move(b,ab)",                  # 名字，同时是它在状态里的唯一标识
        pre={"Free(ab)"},                   # 前提：执行前必须成立的文字
        add={"At(b,ab)"},                   # 执行后变为真的文字
        del_set={"Free(ab)", "At(b,pb)"},   # 执行后不再为真的文字
        cost=1.0,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Set


@dataclass
class Action:
    """一个 grounded（参数已绑定）的符号动作。"""

    name: str
    pre: Iterable[str] = ()
    add: Iterable[str] = ()
    del_set: Iterable[str] = ()
    cost: float = 1.0

    def __post_init__(self) -> None:
        # 统一转成 frozenset：后续全靠集合运算，避免可变集合被意外修改
        self.pre: Set[str] = frozenset(self.pre)
        self.add: Set[str] = frozenset(self.add)
        self.del_set: Set[str] = frozenset(self.del_set)

    def is_applicable(self, state) -> bool:
        """`state` 是否满足该动作的前提。"""
        return self.pre <= state

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"Action({self.name!r}, pre={set(self.pre)}, "
            f"add={set(self.add)}, del_set={set(self.del_set)}, cost={self.cost})"
        )
