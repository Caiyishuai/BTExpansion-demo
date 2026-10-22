"""批量验证：随机生成大量规划问题，逐个"规划 + py_trees 执行"并统计。

关心的三件事：

1. **正确性**：随机问题的目标按构造一定可达，所以成功率必须是 100%。
2. **规模**：树多大、动作多少、规划耗时多少。
3. **鲁棒性**：不可达问题是否明确报错（而不是静默返回一棵跑不动的树）。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from btplan.core.planner import Planner, PlanningFailure
from btplan.domains.random_problems import generate_problems
from btplan.env.runner import run
from btplan.env.symbolic import SymbolicEnv
from btplan.runtime.compiler import compile_tree
from btplan.runtime.tree import BehaviorTree


@dataclass
class BenchResult:
    total: int = 0
    solved: int = 0
    failures: List[str] = field(default_factory=list)
    planning_time: float = 0.0        # 总规划耗时（秒）
    expansions: int = 0               # 总扩展轮数
    tree_size: int = 0                # 树节点总数
    actions_used: int = 0             # 生成的问题里动作总数
    ticks: int = 0
    cost: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.solved / self.total if self.total else 0.0


def run_benchmark(
    problems: int = 100,
    literals_num: int = 10,
    depth: int = 10,
    iters: int = 10,
    seed: int = 1,
    max_ticks: int = 500,
    verbose: bool = False,
) -> BenchResult:
    """跑一批随机问题，返回统计结果。

    Args:
        problems: 问题个数。
        literals_num / depth / iters: 随机问题的规模参数（见
            `domains.random_problems.generate_problem`）。
        seed: 起始随机种子。
        max_ticks: 单个问题的 tick 上限。
        verbose: 打印每个问题的结果。
    """
    result = BenchResult(total=problems)

    for index, (goal, start, actions) in enumerate(
        generate_problems(problems, seed, literals_num, depth, iters)
    ):
        result.actions_used += len(actions)
        try:
            t0 = time.time()
            planner = Planner()
            plan = planner.plan(start, goal, actions)
            result.planning_time += time.time() - t0
            result.expansions += planner.expansions
            result.tree_size += plan.count_size()
        except PlanningFailure as exc:
            result.failures.append(f"#{index}(seed={seed + index}) 规划失败：{exc}")
            if verbose:
                print(result.failures[-1])
            continue

        env = SymbolicEnv(start, actions)
        bt = BehaviorTree(compile_tree(plan))
        bt.bind_env(env)
        run_result = run(bt, env, goal=goal, max_ticks=max_ticks)

        result.ticks += run_result.ticks
        result.cost += run_result.cost
        if run_result.success:
            result.solved += 1
        else:
            result.failures.append(
                f"#{index}(seed={seed + index}) 执行未达成目标：{run_result.summary()}"
            )
        if verbose:
            print(f"#{index}: {run_result.summary()}")

    return result


def format_report(result: BenchResult) -> str:
    """把统计结果排版成可直接读的报告。"""
    solved = result.solved
    avg = lambda x: x / solved if solved else 0.0
    lines = [
        "=========== benchmark ===========",
        f"问题数      : {result.total}",
        f"成功        : {result.solved}  (成功率 {result.success_rate:.1%})",
        f"规划耗时    : {result.planning_time:.3f}s  (平均 {avg(result.planning_time):.4f}s)",
        f"扩展轮数    : {result.expansions}  (平均 {avg(result.expansions):.1f})",
        f"树节点总数  : {result.tree_size}  (平均 {avg(result.tree_size):.1f})",
        f"动作总数    : {result.actions_used}  (平均 {avg(result.actions_used):.1f})",
        f"tick 总数   : {result.ticks}  (平均 {avg(result.ticks):.1f})",
        f"代价总数    : {result.cost:.1f}  (平均 {avg(result.cost):.1f})",
    ]
    if result.failures:
        lines.append(f"失败 {len(result.failures)} 例（前 5 条）：")
        lines += [f"  {msg}" for msg in result.failures[:5]]
    lines.append("=================================")
    return "\n".join(lines)
