"""符号环境（SymbolicEnv）：用一组文字表示世界状态。

它是"状态"的唯一持有者：条件节点从它读（`observe`），动作节点改它
（`apply`）。节点自身一律不缓存状态，这样同一棵树换个环境就能复用。
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from btplan.core.action import Action


class SymbolicEnv:
    """一个纯符号世界：状态 = 若干为真的文字组成的集合。"""

    def __init__(self, state: Iterable[str], actions: Iterable[Action] = ()) -> None:
        self.state = frozenset(state)
        self.actions: Dict[str, Action] = {a.name: a for a in actions}
        self.applied_actions: List[str] = []
        self.cost: float = 0.0

    # ------------------------------ 读 ------------------------------ #

    def observe(self):
        """返回当前为真的文字集合（条件节点的判据）。"""
        return self.state

    def satisfies(self, goal: Iterable[str]) -> bool:
        """目标是否已被满足。"""
        return set(goal) <= self.state

    def is_applicable(self, action_name: str) -> bool:
        """某个动作的前提在当前状态是否成立。"""
        return self._action(action_name).is_applicable(self.state)

    # ------------------------------ 写 ------------------------------ #

    def apply(self, action_name: str) -> None:
        """执行一步动作：删掉 del_set，加上 add，并累计代价。"""
        action = self._action(action_name)
        if not action.is_applicable(self.state):
            raise RuntimeError(f"动作 {action_name} 的前提不满足：缺 {action.pre - self.state}")
        self.state = (self.state - action.del_set) | action.add
        self.applied_actions.append(action_name)
        self.cost += action.cost

    # ------------------------------ 内部 ---------------------------- #

    def _action(self, action_name: str) -> Action:
        try:
            return self.actions[action_name]
        except KeyError:
            raise KeyError(
                f"环境里没有名为 {action_name!r} 的动作，"
                f"已知动作：{sorted(self.actions)}"
            ) from None

    def __repr__(self) -> str:
        return f"SymbolicEnv(state={sorted(self.state)})"
