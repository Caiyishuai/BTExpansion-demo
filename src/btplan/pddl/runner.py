"""PDDL → 行为树：端到端驱动。

    PDDL 文件 → 解析 → 兼容性判定 → grounding → Planner → 编译 → py_trees 运行
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from btplan.core.action import Action
from btplan.core.planner import Planner, PlanningFailure
from btplan.env.runner import RunResult, run
from btplan.env.symbolic import SymbolicEnv
from btplan.ir.node import BTNode
from btplan.ir.serialize import to_ptml
from btplan.runtime.compiler import compile_tree
from btplan.runtime.tree import BehaviorTree

from .compat import UNSUPPORTED, check
from .grounding import ground
from .parser import load_domain, load_problem


@dataclass
class PddlResult:
    """一次 PDDL 求解的完整账本。"""

    report=None                       # CompatReport：兼容性诊断
    grounding=None                    # GroundingResult
    start: frozenset = frozenset()
    goal: frozenset = frozenset()
    actions: List[Action] = field(default_factory=list)
    plan: Optional[BTNode] = None     # 规划出的 IR 树
    ptml: str = ""
    result: Optional[RunResult] = None
    planning_time: float = 0.0
    aborted_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.result is not None and self.result.success

    def summary(self) -> str:
        if self.aborted_reason:
            return f"中止：{self.aborted_reason}"
        if self.result is None:
            return "未执行"
        return (
            f"{self.result.summary()}  "
            f"规划耗时={self.planning_time:.3f}s  动作数={len(self.actions)}"
        )


def load_pddl(domain_path: str, problem_path: str, strict: bool = True):
    """解析 + 兼容性判定 + grounding，返回 ``(goal, start, actions, report)``。

    只想自己控制规划/执行细节时用这个；否则直接用 :func:`solve_pddl`。
    """
    dom = load_domain(domain_path)
    prob = load_problem(problem_path)

    report = check(dom, prob)
    if strict and report.verdict == UNSUPPORTED:
        raise ValueError(
            "该 PDDL 含有阻断项，无法保证生成的策略树 Sound/Complete；"
            "如需强行尝试请传 strict=False。\n" + report.format()
        )

    grounding = ground(dom, prob)
    goal, start, actions = grounding.as_tuple()
    return frozenset(goal), frozenset(start), list(actions), report


def solve_pddl(
    domain_path: str,
    problem_path: str,
    *,
    verbose: bool = False,
    strict: bool = True,
    execute: bool = True,
    max_ticks: int = 500,
) -> PddlResult:
    """把一对 PDDL 文件变成一棵跑得起来的行为树。

    Args:
        domain_path / problem_path: PDDL 文件路径。
        verbose: 打印规划与执行的细节。
        strict: 遇到"无法保证 Sound/Complete"的阻断项时直接中止。
        execute: 是否真的用 py_trees 跑一遍（False 则只规划不执行）。
        max_ticks: 执行阶段的 tick 上限。

    Returns:
        PddlResult：诊断报告、IR 树、PTML、执行结果。
    """
    res = PddlResult()

    try:
        goal, start, actions, report = load_pddl(domain_path, problem_path, strict)
    except ValueError as exc:
        res.aborted_reason = str(exc)
        return res

    res.report = report
    res.start, res.goal, res.actions = start, goal, actions

    if not goal:
        res.aborted_reason = "目标为空，无需规划"
        return res

    # ---- 规划 ---- #
    t0 = time.time()
    try:
        res.plan = Planner(verbose=verbose).plan(start, goal, actions)
    except PlanningFailure as exc:
        res.aborted_reason = str(exc)
        return res
    res.planning_time = time.time() - t0
    res.ptml = to_ptml(res.plan)

    # ---- 执行 ---- #
    if execute:
        env = SymbolicEnv(start, actions)
        bt = BehaviorTree(compile_tree(res.plan))
        bt.bind_env(env)
        res.result = run(bt, env, goal=goal, max_ticks=max_ticks, verbose=verbose)

    return res


def default_sample(name: str = "movebtob"):
    """返回仓库自带的 PDDL 样例路径 ``(domain, problem)``。"""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    folder = os.path.join(root, "pddl", name)
    return os.path.join(folder, "domain.pddl"), os.path.join(folder, "problem.pddl")
