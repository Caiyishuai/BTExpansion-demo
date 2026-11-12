"""运行驱动：反复调用 py_trees 的 tick，直到任务成功/失败/超限。

**这里是"py_trees 驱动"的落点**：循环里只有一句 `bt.tick()`，
走哪个分支、执行哪个动作，全部由 py_trees 的 Selector/Sequence 语义决定。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, List, Optional

from py_trees.common import Status

from btplan.ir.node import BTNode
from btplan.runtime.tree import BehaviorTree

if TYPE_CHECKING:  # 只在类型检查时导入，避免运行时循环依赖
    from btplan.env.protocol import Environment


@dataclass
class RunResult:
    """一次运行的账本。"""

    success: bool
    status: str
    ticks: int
    cost: float
    actions: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    plan: Optional[BTNode] = None      # solve() 会顺带把规划出的 IR 树带回来

    def summary(self) -> str:
        return (
            f"成功={self.success}  状态={self.status}  "
            f"tick={self.ticks}  代价={self.cost}  动作={self.actions}"
        )

    def __str__(self) -> str:
        return self.summary()


def run(
    bt: BehaviorTree,
    env: "Environment",
    goal: Optional[Iterable[str]] = None,
    max_ticks: int = 1000,
    verbose: bool = False,
) -> RunResult:
    """驱动一棵行为树，直到目标达成 / 失败 / 超过 max_ticks。

    Args:
        bt: 已 `bind_env` 的行为树。
        env: 环境（提供 `observe` / `apply` / `satisfies`）。
        goal: 目标文字集合；给了就以"目标是否被满足"为最终判据。
        max_ticks: 死循环保护。
        verbose: 打印每一拍的节点状态。

    Returns:
        RunResult：成功与否、tick 数、代价、执行过的动作。
    """
    goal = frozenset(goal or ())
    trace: List[str] = []
    success = False

    while bt.tick_count < max_ticks:
        status = bt.tick()
        trace.append(bt.visitor.output_str)

        if verbose:
            print(f"--- tick {bt.tick_count} --- root={status.value}")
            print(bt.visitor.output_str, end="")

        if status is Status.FAILURE:
            success = False
            break
        if status is Status.SUCCESS:
            success = env.satisfies(goal) if goal else True
            break
        if goal and env.satisfies(goal):
            success = True
            break
    else:
        status = Status.FAILURE
        success = False

    return RunResult(
        success=success,
        status=status.value if status is not None else "INVALID",
        ticks=bt.tick_count,
        cost=getattr(env, "cost", 0.0),
        actions=list(getattr(env, "applied_actions", [])),
        trace=trace,
    )
