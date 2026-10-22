"""示例 05 —— 从零写一个新任务（完整流程）。

这一集演示"我自己有个新任务，该怎么交给 btplan"：

    ① 设计文字（世界里有哪几类事实）
    ② 写 start（一开始什么是真的）
    ③ 写 goal（想让什么变成真的）
    ④ 写 actions（每个动作的前提 / 新增 / 删除）
    ⑤ 规划 + 运行
    ⑥ 导出 PTML
    ⑦ 画出树图（需要 pip install ".[draw]" 与系统 graphviz）

前置阅读：examples/02_plan_and_run.py
运行命令：python examples/05_new_task.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btplan import (  # noqa: E402
    Action,
    BehaviorTree,
    Planner,
    SymbolicEnv,
    compile_tree,
    run,
    to_ptml,
)


# --------------------------------------------------------------------------- #
# ① 设计文字
# --------------------------------------------------------------------------- #
# 我们的世界里有这几类事实：
#   At(Robot,X)        机器人在 X 处          X ∈ {Bar, Machine, Table}
#   HandEmpty          手是空的
#   Holding(Coffee)    手里拿着咖啡
#   DoorOpen           门是开着的
#   On(Coffee,Table)   咖啡在餐桌上
#
# 规则很简单：文字就是字符串，条件判断就是"集合包含"。

# --------------------------------------------------------------------------- #
# ② 写 start：一开始什么是真的
# --------------------------------------------------------------------------- #
start = {"At(Robot,Bar)", "HandEmpty"}

# --------------------------------------------------------------------------- #
# ③ 写 goal：想让什么变成真的
# --------------------------------------------------------------------------- #
goal = {"On(Coffee,Table)"}

# --------------------------------------------------------------------------- #
# ④ 写 actions：每个动作的 pre / add / del_set
# --------------------------------------------------------------------------- #
# 写动作的要点：
#   pre      做之前必须成立
#   add      做完之后变成真的
#   del_set  做完之后不再为真的（同一谓词的其他取值一定要删掉！）
actions = [
    Action("Move(Robot,Machine)", pre={"DoorOpen"},
           add={"At(Robot,Machine)"}, del_set={"At(Robot,Bar)", "At(Robot,Table)"}, cost=1),
    Action("Move(Robot,Table)", pre={"DoorOpen"},
           add={"At(Robot,Table)"}, del_set={"At(Robot,Bar)", "At(Robot,Machine)"}, cost=1),
    Action("OpenDoor", pre={"HandEmpty"}, add={"DoorOpen"}, del_set=set(), cost=1),
    Action("BrewCoffee", pre={"At(Robot,Machine)", "HandEmpty"},
           add={"Holding(Coffee)"}, del_set={"HandEmpty"}, cost=2),
    Action("PlaceOnTable", pre={"At(Robot,Table)", "Holding(Coffee)"},
           add={"On(Coffee,Table)", "HandEmpty"}, del_set={"Holding(Coffee)"}, cost=1),
]


def main() -> None:
    # ----------------------------------------------------------------- #
    # ⑤ 规划 + 运行
    # ----------------------------------------------------------------- #
    plan = Planner(verbose=True).plan(start, goal, actions)

    print("\n=========== 行为树（IR）===========")
    plan.print_tree()

    env = SymbolicEnv(start, actions)
    bt = BehaviorTree(compile_tree(plan))
    bt.bind_env(env)

    result = run(bt, env, goal=goal, verbose=True)
    print("\n=========== 结果 ===========")
    print(result.summary())
    print("执行序列：", result.actions)
    print("最终状态：", sorted(env.state))

    # ----------------------------------------------------------------- #
    # ⑥ 导出 PTML
    # ----------------------------------------------------------------- #
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    ptml = to_ptml(plan)
    (out_dir / "ServeCoffee.ptml").write_text(ptml, encoding="utf-8")
    print(f"\n=========== PTML（已写入 output/ServeCoffee.ptml）===========")
    print(ptml, end="")

    # ----------------------------------------------------------------- #
    # ⑦ 画出树图
    # ----------------------------------------------------------------- #
    try:
        paths = bt.draw(file_name="ServeCoffee", target_directory=str(out_dir))
        print("\n=========== 树图 ===========")
        for kind, path in paths.items():
            print(f"{kind}: {path}")
    except ImportError as exc:
        print(f"\n（跳过画图：{exc}）")


if __name__ == "__main__":
    main()
