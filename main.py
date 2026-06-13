# from OptimalBTExpansionAlgorithm import Action,OptBTExpAlgorithm # 调用最优行为树扩展算法
from BTExpansionAlgorithm import BTExpAlgorithm,state_transition
from tools import print_action_data_table
from Examples import *
from utils.bt.draw import render_dot_tree
from utils.bt.load import load_bt_from_ptml
# find_node_by_name,print_tree_from_root
import os
output_path = os.path.join(os.path.dirname(__file__), "outputs")



if __name__ == '__main__' :

    ptml_file_name = "MoveBtoB"  # MakeCoffee

    # 从已定义好的例子中直接导入
    goal, start, actions = MoveBtoB()  # Examples里的例子: MoveBtoB_num,MoveBtoB,Cond2BelongsToCond3,SoftdrinkCost,MakeCoffeeCost,Test
    print_action_data_table(goal,start,actions) # 打印所有变量


    # todo: 运行算法得到行为树为 algo.bt
    algo = BTExpAlgorithm(verbose=True)
    algo.clear()
    algo.run_algorithm(start, goal, actions)
    algo.print_solution() # 打印行为树
    # todo: 输出 MakeCoffee.ptml
    print("=========== PTML ============")
    ptml_string = algo.save_ptml_file(ptml_file_name)
    print(ptml_string)
    print("========= End PTML ==========\n")

    # 把树画出来 下面的有错误
    # ptml_path = os.path.join(f'{ptml_file_name}.ptml')
    # bt = load_bt_from_ptml(None, ptml_path,behavior_lib_path="")
    # render_dot_tree(algo.bt, target_directory="", name="bt", png_only=False)




    
    algo2 = BTExpAlgorithm(verbose=False)
    algo2.clear()
    algo2.run_algorithm(start, goal, actions)
    # algo2.print_solution() # 打印行为树
    print("=========== Run BT-Expansion ============")
    state = start
    steps = 0
    cost_tatol2 = 0
    val, obj,cost,ticks = algo2.bt.cost_tick(state,0,0)
    cost_tatol2+=cost
    while val != 'success' and val != 'failure':
        state = state_transition(state, obj)
        print (obj.name)
        val, obj,cost,ticks = algo2.bt.cost_tick(state,0,ticks)
        cost_tatol2 += cost
        if (val == 'failure'):
            print("bt fails at step", steps)
        steps += 1
    if not goal <= state:
        print ("wrong solution steps",steps)
    else:
        print ("right solution steps",steps)
    print("The number of nodes in BT:", algo.bt.count_size() - 1)
    algo2.clear()
    print("BT-Expansion cost:", cost_tatol2)
    print("BT-Expansion ticks:", ticks)
    print("============ End Run BT-Expansion ===========\n")



