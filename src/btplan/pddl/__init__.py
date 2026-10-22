"""PDDL 前端：直接吃标准 PDDL（domain + problem），吐出一棵行为树。

    from btplan.pddl import solve_pddl

    res = solve_pddl("domain.pddl", "problem.pddl")
    print(res.report.format())     # 兼容性诊断（能不能拿到 Sound/Complete 保证）
    print(res.ptml)                # 行为树文本
    print(res.result.summary())    # 执行结果

流程：解析 → 兼容性判定 → grounding → Planner → 编译 → py_trees 驱动。
准入规则（什么 PDDL 能拿保证）见 pddl/ADMISSIBILITY.md。
"""

from btplan.pddl.parser import load_domain, load_problem
from btplan.pddl.grounding import ground, GroundingResult
from btplan.pddl.compat import (
    UNSUPPORTED,
    check,
    collect_atoms,
    CompatReport,
    Finding,
)
from btplan.pddl.runner import PddlResult, default_sample, load_pddl, solve_pddl

__all__ = [
    # 解析
    "load_domain",
    "load_problem",
    # 兼容性判定
    "check",
    "CompatReport",
    "Finding",
    "UNSUPPORTED",
    "collect_atoms",
    # grounding
    "ground",
    "GroundingResult",
    # 端到端
    "load_pddl",
    "solve_pddl",
    "default_sample",
    "PddlResult",
]
