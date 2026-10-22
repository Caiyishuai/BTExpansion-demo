"""一键流水线：solve(start, goal, actions) 走完"规划 → 编译 → 运行"。

想省事就用它；想改中间任何一步，就按同样的四步自己拼（见 examples/02）。
"""

from __future__ import annotations

from typing import Iterable, Optional

from btplan.core.action import Action
from btplan.core.planner import Planner
from btplan.env.runner import RunResult, run
from btplan.env.symbolic import SymbolicEnv
from btplan.ir.node import BTNode
from btplan.runtime.compiler import compile_tree
from btplan.runtime.library import BehaviorLibrary
from btplan.runtime.tree import BehaviorTree


def plan_and_compile(
    start: Iterable[str],
    goal: Iterable[str],
    actions: Iterable[Action],
    library: Optional[BehaviorLibrary] = None,
    verbose: bool = False,
):
    """规划 + 编译，返回 ``(IR 树, 可 tick 的 BehaviorTree, 环境)``。"""
    start, goal = frozenset(start), frozenset(goal)
    ir_tree: BTNode = Planner(verbose=verbose).plan(start, goal, actions)
    env = SymbolicEnv(start, actions)
    bt = BehaviorTree(compile_tree(ir_tree, library))
    bt.bind_env(env)
    return ir_tree, bt, env


def solve(
    start: Iterable[str],
    goal: Iterable[str],
    actions: Iterable[Action],
    *,
    library: Optional[BehaviorLibrary] = None,
    max_ticks: int = 1000,
    verbose: bool = False,
) -> RunResult:
    """规划一棵行为树并让 py_trees 把它跑到目标达成。

    Args:
        start: 初始状态（文字集合）。
        goal: 目标（文字集合）。
        actions: 可用动作。
        library: 可选行为库（自定义 Condition/Action 节点时用）。
        max_ticks: tick 上限，防止死循环。
        verbose: 打印每拍细节。

    Returns:
        RunResult：成功与否、tick 数、代价、执行过的动作、规划出的 IR 树。
    """
    ir_tree, bt, env = plan_and_compile(start, goal, actions, library, verbose)
    result = run(bt, env, goal=goal, max_ticks=max_ticks, verbose=verbose)
    result.plan = ir_tree
    return result
