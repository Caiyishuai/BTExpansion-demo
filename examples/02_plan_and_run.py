"""示例 02 —— 规划 → 编译 → py_trees 驱动执行（最核心的一集）。

你会学到什么
------------
1. Planner 怎么把 goal 反向扩展成一棵 IR 树
2. IR 树怎么导出成 PTML 文本（存档/人看）
3. IR 树怎么编译成 py_trees，再由 py_trees tick 到达成目标

前置阅读：examples/01_hello_bt.py（先知道运行时长什么样）
运行命令：python examples/02_plan_and_run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan import (  # noqa: E402
    BehaviorTree,
    Planner,
    SymbolicEnv,
    compile_tree,
    run,
    solve,
    to_ptml,
)
from btplan.domains import MoveBtoB  # noqa: E402


def main() -> None:
    goal, start, actions = MoveBtoB()

    # ---------------- ① 规划：产出 IR 树（纯数据） ---------------- #
    plan = Planner(verbose=True).plan(start, goal, actions)
    print("\n=========== IR 树 ===========")
    plan.print_tree()

    print("\n=========== PTML ===========")
    print(to_ptml(plan), end="")

    # ---------------- ② 编译：IR → py_trees ---------------- #
    env = SymbolicEnv(start, actions)
    bt = BehaviorTree(compile_tree(plan))
    bt.bind_env(env)

    # ---------------- ③ 运行：py_trees 驱动 ---------------- #
    print("=========== 运行 ===========")
    result = run(bt, env, goal=goal, verbose=True)
    print(result.summary())
    print("最终状态：", sorted(map(str, env.state)))

    # ---------------- 一行版：solve() ---------------- #
    print("\n=========== solve() 一行版 ===========")
    print(solve(start, goal, actions).summary())


if __name__ == "__main__":
    main()
