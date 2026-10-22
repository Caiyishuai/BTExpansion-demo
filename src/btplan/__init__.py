"""btplan —— 行为树扩展规划（BT Expansion）。

数据流只有一条，记住它就看懂了整个项目：

    start / goal / actions
        │
        ▼
    ① 规划  Planner           纯符号反向扩展，产出 IR 树（不碰 py_trees）
        │
        ▼
    ② IR    BTNode ──► to_ptml() / 打印 / 测试快照
        │
        ▼
    ③ 编译  compile_tree()    IR → py_trees 节点
        │
        ▼
    ④ 运行  run()             py_trees 驱动 tick，直到成功/失败

四层对应四个子包：

    btplan.core      规划内核：动作模型、扩展规则、符号求值、搜索主循环
    btplan.ir        中间表示：BTNode + PTML 序列化
    btplan.runtime   py_trees 运行时：节点、行为库、编译器、BehaviorTree
    btplan.env       环境：状态怎么存、动作怎么生效、tick 循环怎么跑

最快上手：examples/01_hello_bt.py（运行时）→ examples/02_plan_and_run.py（全流程）
架构说明：docs/01-architecture.md
"""

from btplan.core.action import Action
from btplan.core.evaluate import can_run, evaluate
from btplan.core.expander import expandable_actions, is_consequence, premise_of
from btplan.core.planner import Planner, PlanningFailure
from btplan.env.runner import RunResult, run
from btplan.env.symbolic import SymbolicEnv
from btplan.ir.node import BTNode
from btplan.ir.serialize import to_ptml
from btplan.pddl import solve_pddl
from btplan.pipeline import plan_and_compile, solve
from btplan.runtime.compiler import AlwaysTrue, compile_tree
from btplan.runtime.library import BehaviorLibrary, make_action, make_condition
from btplan.runtime.nodes import (
    ActionNode,
    BehaviorNode,
    CompositeCondition,
    ConditionNode,
    Fallback,
    Sequence,
    Status,
)
from btplan.runtime.tree import BehaviorTree

__version__ = "0.1.0"

__all__ = [
    # 数据
    "Action",
    "Status",
    # 规划
    "Planner",
    "PlanningFailure",
    "is_consequence",
    "premise_of",
    "expandable_actions",
    "evaluate",
    "can_run",
    # 中间表示
    "BTNode",
    "to_ptml",
    # 运行时
    "BehaviorTree",
    "BehaviorLibrary",
    "BehaviorNode",
    "ConditionNode",
    "ActionNode",
    "CompositeCondition",
    "AlwaysTrue",
    "Sequence",
    "Fallback",
    "make_condition",
    "make_action",
    "compile_tree",
    # 环境与驱动
    "SymbolicEnv",
    "RunResult",
    "run",
    # 一键流水线
    "solve",
    "plan_and_compile",
    # PDDL 前端
    "solve_pddl",
]
