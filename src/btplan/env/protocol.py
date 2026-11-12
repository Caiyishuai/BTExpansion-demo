"""环境契约：想换掉 SymbolicEnv，实现这四个方法就行。

运行时节点只依赖这个接口，不依赖具体实现类：

    observe()              返回当前为真的文字集合（条件节点读它）
    satisfies(goal)        目标是否已达成
    is_applicable(name)    某个动作的前提是否成立
    apply(name)            执行一步动作（改状态）

接真实机器人/模拟器时，写一个类实现这四条，传给 `bt.bind_env(env)` 即可，
行为树那边一个字都不用改。
"""

from __future__ import annotations

from typing import Iterable, Protocol


class Environment(Protocol):
    """运行时需要的最小环境接口（结构化类型，无需显式继承）。"""

    def observe(self) -> Iterable[str]:
        """当前为真的文字集合。"""

    def satisfies(self, goal: Iterable[str]) -> bool:
        """目标是否已被满足。"""

    def is_applicable(self, action_name: str) -> bool:
        """动作前提是否成立。"""

    def apply(self, action_name: str) -> None:
        """执行一步动作。"""
