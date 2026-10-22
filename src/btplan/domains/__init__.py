"""示例问题集：每个函数返回 (goal, start, actions)，拿来就能跑。

    from btplan.domains import MoveBtoB
    goal, start, actions = MoveBtoB()
"""

from btplan.domains.problems import (
    Cond2BelongsToCond3,
    MakeCoffee,
    MakeCoffeeCost,
    MoveBtoB,
    MoveBtoB_num,
    ServeCoffee,
    SoftdrinkCost,
    Test,
)
from btplan.domains.random_problems import (
    generate_problem,
    generate_problems,
    random_action,
    random_state,
    state_transition,
)

__all__ = [
    # 内置示例问题
    "MoveBtoB",
    "MoveBtoB_num",
    "ServeCoffee",
    "MakeCoffee",
    "MakeCoffeeCost",
    "SoftdrinkCost",
    "Cond2BelongsToCond3",
    "Test",
    # 随机问题生成（benchmark 用）
    "generate_problem",
    "generate_problems",
    "random_state",
    "random_action",
    "state_transition",
]
