"""示例 04 —— 自定义节点 + 行为库（接真实机器人就是这一步）。

你会学到什么
------------
1. 怎么写自己的 ConditionNode / ActionNode（去读真实传感器、驱动真实动作）
2. 行为库怎么把"文字"接到"你的类"上（同名即命中，没写就退回默认语义）
3. 环境可以带自己的额外状态（本例的"咖啡豆余量"），树那边不用改
4. RUNNING 怎么用：一个动作分两拍完成

前置阅读：examples/02_plan_and_run.py、docs/03-runtime.md
运行命令：python examples/04_custom_domain.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btplan import (  # noqa: E402
    Action,
    ActionNode,
    BehaviorLibrary,
    BehaviorTree,
    ConditionNode,
    Planner,
    Status,
    SymbolicEnv,
    compile_tree,
    run,
)


# --------------------------------------------------------------------------- #
# ① 环境：符号状态 + 自己的额外状态
# --------------------------------------------------------------------------- #
class CoffeeShop(SymbolicEnv):
    """在文字状态之外，还维护一个"咖啡豆余量"。"""

    def __init__(self, state, actions, beans: int = 1) -> None:
        super().__init__(state, actions)
        self.beans = beans


# --------------------------------------------------------------------------- #
# ② 自定义节点
# --------------------------------------------------------------------------- #
class BeansLeft(ConditionNode):
    """条件：读环境的真实计数器，而不是查文字。

    类名 `BeansLeft` 会和文字 `BeansLeft` 自动对上（见 ③）。
    """

    def update(self) -> Status:
        return Status.SUCCESS if self.env.beans > 0 else Status.FAILURE


class Brew(ActionNode):
    """动作：分两拍完成——第一拍预热（RUNNING），第二拍出咖啡（SUCCESS）。"""

    def initialise(self) -> None:
        self.heating = False          # 每次从非 RUNNING 进入时重置

    def update(self) -> Status:
        if not self.heating:
            self.heating = True
            return Status.RUNNING
        if self.env.beans <= 0:
            return Status.FAILURE
        self.env.apply(self.literal)  # 改符号状态
        self.env.beans -= 1          # 改环境自己的状态
        return Status.SUCCESS


# --------------------------------------------------------------------------- #
# ③ 行为库：文字 -> 你的类
# --------------------------------------------------------------------------- #
def build_library() -> BehaviorLibrary:
    library = BehaviorLibrary()
    library.register(BeansLeft)   # 文字 "BeansLeft"    → BeansLeft 类
    library.register(Brew)        # 文字 "Brew(Coffee)" → Brew 类
    return library


# --------------------------------------------------------------------------- #
# ④ 跑起来
# --------------------------------------------------------------------------- #
def make_problem():
    actions = [
        Action("Brew(Coffee)", pre={"CupReady", "BeansLeft"},
               add={"HasCoffee"}, del_set=set()),
    ]
    start = {"CupReady", "BeansLeft"}
    goal = {"HasCoffee"}
    return goal, start, actions


def brew_once(beans: int, verbose: bool = False):
    goal, start, actions = make_problem()

    plan = Planner().plan(start, goal, actions)
    env = CoffeeShop(start, actions, beans=beans)

    # 注意这里把 library 传给 compile_tree：同名的文字会用你注册的类
    bt = BehaviorTree(compile_tree(plan, build_library()))
    bt.bind_env(env)
    return run(bt, env, goal=goal, verbose=verbose), env


if __name__ == "__main__":
    print("=========== 有咖啡豆（两拍完成）===========")
    result, env = brew_once(beans=1, verbose=True)
    print(result.summary())
    print("剩余咖啡豆：", env.beans)
    print("最终状态：", sorted(env.state))

    print("\n=========== 没有咖啡豆（自定义条件拦下）===========")
    result2, env2 = brew_once(beans=0)
    print(result2.summary())
    print("说明：条件 BeansLeft 走的是自定义类，读到 beans=0 直接 FAILURE，"
          "树根本不会去执行 Brew。")
