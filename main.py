"""BT_Expansion 演示入口。

流程：定义规划问题 -> 运行行为树扩展算法 -> 打印 / 保存行为树 -> 执行行为树。
生成的 .ptml 文件统一输出到项目根目录下的 output/ 文件夹。
"""

import os
import sys

# 将 src 目录加入模块搜索路径，使核心包与库代码可被导入
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from bt_expansion.algorithm import BTExpAlgorithm, state_transition
from bt_expansion.planning import print_action_data_table
from bt_expansion.examples import (
    MoveBtoB, MoveBtoB_num, Cond2BelongsToCond3,
    SoftdrinkCost, MakeCoffee, MakeCoffeeCost, Test,
)

# 所有生成产物（.ptml 等）统一输出到此目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def main():
    ptml_file_name = "MoveBtoB"  # 可替换为 MakeCoffee 等

    # 从已定义好的例子中直接导入规划问题
    goal, start, actions = MoveBtoB()
    print_action_data_table(goal, start, actions)  # 打印所有变量

    # 运行算法，得到的行为树保存在 algo.bt
    algo = BTExpAlgorithm(verbose=True)
    algo.clear()
    algo.run_algorithm(start, goal, actions)
    algo.print_solution()  # 打印行为树

    # 输出 PTML 文件到 output/ 目录
    print("=========== PTML ============")
    ptml_string = algo.save_ptml_file(ptml_file_name, OUTPUT_DIR)
    print(ptml_string)
    print("========= End PTML ==========\n")

    # 重新运行算法并执行行为树，统计代价与 tick 次数
    algo2 = BTExpAlgorithm(verbose=False)
    algo2.clear()
    algo2.run_algorithm(start, goal, actions)

    print("=========== Run BT-Expansion ============")
    state = start
    steps = 0
    cost_total = 0
    val, obj, cost, ticks = algo2.bt.cost_tick(state, 0, 0)
    cost_total += cost
    while val != 'success' and val != 'failure':
        state = state_transition(state, obj)
        print(obj.name)
        val, obj, cost, ticks = algo2.bt.cost_tick(state, 0, ticks)
        cost_total += cost
        if val == 'failure':
            print("bt fails at step", steps)
        steps += 1

    if not goal <= state:
        print("wrong solution steps", steps)
    else:
        print("right solution steps", steps)
    print("The number of nodes in BT:", algo.bt.count_size() - 1)
    algo2.clear()
    print("BT-Expansion cost:", cost_total)
    print("BT-Expansion ticks:", ticks)
    print("============ End Run BT-Expansion ===========\n")


if __name__ == '__main__':
    main()
