"""示例 01 —— 手写一棵行为树，交给 py_trees 驱动。

你会学到什么
------------
1. 行为树在运行时长什么样：Fallback / Sequence / 条件节点 / 动作节点
2. 状态放在 env 里；节点只读状态、改状态，不自己保存状态
3. tick 循环怎么把任务一步步推进（以及 RUNNING 是什么）

前置阅读：无，这是第一个示例
运行命令：python examples/01_hello_bt.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan import (  # noqa: E402
    Action,
    ActionNode,
    BehaviorTree,
    CompositeCondition,
    Fallback,
    RunResult,
    Sequence,
    Status,
    SymbolicEnv,
    make_action,
    make_condition,
    run,
)


# --------------------------------------------------------------------------- #
# 第一幕：一步到位的动作
# --------------------------------------------------------------------------- #
#
# 任务：把物体 b 从 pb 搬到 ab。
# 状态里只有文字（字符串），比如 Free(ab) 表示 ab 位置是空的。
#
def act_one_shot() -> RunResult:
    actions = [
        Action(
            name="Move(b,ab)",
            pre={"Free(ab)"},                 # 前提：ab 位置空着
            add={"At(b,ab)"},                 # 做完：b 在 ab
            del_set={"Free(ab)", "At(b,pb)"},  # 做完：ab 不空了，b 不在 pb 了
        )
    ]
    start = {"Free(ab)", "At(b,pb)"}
    goal = {"At(b,ab)"}

    env = SymbolicEnv(start, actions)

    # 手写一棵树：
    #   Fallback                      先试左分支，不行再试右分支
    #   ├── At(b,ab)                  目标已经达成了？那就什么都不用做
    #   └── Sequence                  否则：先看条件，再执行动作
    #       ├── Free(ab)              条件成立？
    #       └── Move(b,ab)            搬！
    root = Fallback(
        "bt",
        children=[
            make_condition("At(b,ab)"),
            Sequence(
                "move-b-to-ab",
                children=[
                    make_condition("Free(ab)"),
                    make_action("Move(b,ab)"),
                ],
            ),
        ],
    )

    bt = BehaviorTree(root)
    bt.bind_env(env)
    return run(bt, env, goal=goal)


# --------------------------------------------------------------------------- #
# 第二幕：多拍才能完成的动作（RUNNING）
# --------------------------------------------------------------------------- #
#
# 真实机器人很少"一拍就做完"。动作可以返回 RUNNING 表示"我在做，还没完"，
# py_trees 会在这一拍停在它身上，下一拍继续 tick 它。
#
class MoveSlowly(ActionNode):
    """两拍完成的动作：第一拍启动（RUNNING），第二拍落地效果（SUCCESS）。"""

    def initialise(self) -> None:
        # py_trees 会在节点从非 RUNNING 转入时调用它，用来重置内部状态
        self.started = False

    def update(self) -> Status:
        if not self.started:
            self.started = True
            return Status.RUNNING          # 启动，还没做完
        if not self.env.is_applicable(self.literal):
            return Status.FAILURE
        self.env.apply(self.literal)
        return Status.SUCCESS


def act_multi_tick() -> RunResult:
    actions = [
        Action(
            name="MoveSlowly(b,ab)",
            pre={"Free(ab)"},
            add={"At(b,ab)"},
            del_set={"Free(ab)", "At(b,pb)"},
        )
    ]
    env = SymbolicEnv({"Free(ab)", "At(b,pb)"}, actions)

    root = Fallback(
        "bt",
        children=[
            make_condition("At(b,ab)"),
            Sequence(
                "move-slowly",
                children=[
                    CompositeCondition({"Free(ab)"}),   # 多文字条件（这里只有一个）
                    MoveSlowly("b", "ab"),              # 自定义节点
                ],
            ),
        ],
    )

    bt = BehaviorTree(root)
    bt.bind_env(env)
    return run(bt, env, goal={"At(b,ab)"}, verbose=True)


if __name__ == "__main__":
    print("=========== 第一幕：一步到位 ===========")
    result = act_one_shot()
    print(result.summary())

    print("\n=========== 第二幕：RUNNING ===========")
    result2 = act_multi_tick()
    print(result2.summary())
