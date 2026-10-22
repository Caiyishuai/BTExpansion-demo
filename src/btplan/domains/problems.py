"""内置规划问题。每个函数返回 ``(goal, start, actions)``。"""

from btplan.core.action import Action


def MoveBtoB():
    """经典例子：把物体 b 搬到 ab，路上要先把挡路的 s 挪开。"""
    actions = [
        Action("Move(b,ab)", pre={"Free(ab)", "WayClear"},
               add={"At(b,ab)"}, del_set={"Free(ab)", "At(b,pb)"}, cost=1),
        Action("Move(s,ab)", pre={"Free(ab)"},
               add={"Free(ab)", "WayClear"}, del_set={"Free(ab)", "At(s,ps)"}, cost=2),
        Action("Move(s,as)", pre={"Free(as)"},
               add={"At(s,ps)", "WayClear"}, del_set={"Free(as)", "At(s,ps)"}, cost=3),
    ]
    start = {"Free(ab)", "Free(as)", "At(b,pb)", "At(s,ps)"}
    goal = {"At(b,ab)"}
    return goal, start, actions


def MakeCoffee():
    """做咖啡：先操作咖啡机做出咖啡，再抓起来放到桌上。"""
    actions = [
        Action("Put(Table,Coffee)", pre={"Holding(Coffee)", "At(Table)"},
               add={"At(Table,Coffee)", "NotHolding"}, del_set={"Holding(Coffee)"}),
        Action("Put(Table,VacuumCup)", pre={"Holding(VacuumCup)", "At(Table)"},
               add={"At(Table,VacuumCup)", "NotHolding"}, del_set={"Holding(VacuumCup)"}),
        Action("Grasp(Coffee)", pre={"NotHolding", "At(Coffee)"},
               add={"Holding(Coffee)"}, del_set={"NotHolding"}),
        Action("MoveTo(Table)", pre={"Exist(Table)"},
               add={"At(Table)"}, del_set={"At(FrontDesk)", "At(Coffee)", "At(CoffeeMachine)"}),
        Action("MoveTo(Coffee)", pre={"Exist(Coffee)"},
               add={"At(Coffee)"}, del_set={"At(FrontDesk)", "At(Table)", "At(CoffeeMachine)"}),
        Action("MoveTo(CoffeeMachine)", pre={"Exist(CoffeeMachine)"},
               add={"At(CoffeeMachine)"}, del_set={"At(FrontDesk)", "At(Coffee)", "At(Table)"}),
        Action("OpCoffeeMachine", pre={"At(CoffeeMachine)", "NotHolding"},
               add={"Exist(Coffee)", "At(Coffee)"}, del_set=set()),
    ]
    start = {"At(FrontDesk)", "Holding(VacuumCup)", "Exist(Table)",
             "Exist(CoffeeMachine)", "Exist(FrontDesk)"}
    goal = {"At(Table,Coffee)"}
    return goal, start, actions


def MakeCoffeeCost():
    """MakeCoffee 的带代价版本（不同动作 cost 不同）。"""
    actions = [
        Action("PutDown(Table,Coffee)", pre={"Holding(Coffee)", "At(Robot,Table)"},
               add={"At(Table,Coffee)", "NotHolding"}, del_set={"Holding(Coffee)"}, cost=1),
        Action("PutDown(Table,VacuumCup)", pre={"Holding(VacuumCup)", "At(Robot,Table)"},
               add={"At(Table,VacuumCup)", "NotHolding"}, del_set={"Holding(VacuumCup)"}, cost=1),
        Action("PickUp(Coffee)", pre={"NotHolding", "At(Robot,Coffee)"},
               add={"Holding(Coffee)"}, del_set={"NotHolding"}, cost=1),
        Action("MoveTo(Table)", pre={"Available(Table)"},
               add={"At(Robot,Table)"},
               del_set={"At(Robot,FrontDesk)", "At(Robot,Coffee)", "At(Robot,CoffeeMachine)"}, cost=1),
        Action("MoveTo(Coffee)", pre={"Available(Coffee)"},
               add={"At(Robot,Coffee)"},
               del_set={"At(Robot,FrontDesk)", "At(Robot,Table)", "At(Robot,CoffeeMachine)"}, cost=1),
        Action("MoveTo(CoffeeMachine)", pre={"Available(CoffeeMachine)"},
               add={"At(Robot,CoffeeMachine)"},
               del_set={"At(Robot,FrontDesk)", "At(Robot,Coffee)", "At(Robot,Table)"}, cost=1),
        Action("OpCoffeeMachine", pre={"At(Robot,CoffeeMachine)", "NotHolding"},
               add={"Available(Coffee)", "At(Robot,Coffee)"}, del_set=set(), cost=1),
    ]
    start = {"At(Robot,Bar)", "Holding(VacuumCup)", "Available(Table)",
             "Available(CoffeeMachine)", "Available(FrontDesk)"}
    goal = {"At(Table,Coffee)"}
    return goal, start, actions


def ServeCoffee():
    """送咖啡：机器人先开门，去咖啡机做一杯，再送到餐桌上。

    依赖关系（正是它让生成的树有分叉）：
        放到餐桌  ←  人在餐桌 且 手里有咖啡
        人在餐桌  ←  门开着
        手里有咖啡 ←  人在咖啡机 且 手是空的
        门开着    ←  手是空的（初始就成立）
    """
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
    start = {"At(Robot,Bar)", "HandEmpty"}
    goal = {"On(Coffee,Table)"}
    return goal, start, actions


def SoftdrinkCost():
    """放饮料：演示带代价的动作选择。"""
    actions = [
        Action("PutDown(Softdrink,WaterTable)",
               pre={"Holding(Softdrink)", "At(Robot,WaterTable)"},
               add={"Holding(Nothing)", "On(Softdrink,WaterTable)"},
               del_set={"Holding(Softdrink)"}, cost=3),
        Action("PickUp(Softdrink)", pre={"At(Robot,Softdrink)", "Holding(Nothing)"},
               add={"Holding(Softdrink)"}, del_set={"Holding(Nothing)"}, cost=2),
        Action("MoveTo(WaterTable)", pre=set(), add={"At(Robot,WaterTable)"},
               del_set={"At(Robot,Softdrink)", "At(Robot,Bar)", "At(Robot,Coffee)"}, cost=5),
        Action("MoveTo(Softdrink)", pre={"Exist(Softdrink)"}, add={"At(Robot,Softdrink)"},
               del_set={"At(Robot,WaterTable)", "At(Robot,Bar)", "At(Robot,Coffee)"}, cost=5),
        Action("PutDown(Coffee,WaterTable)", pre={"Holding(Coffee)"}, add={"Holding(Nothing)"},
               del_set={"Holding(Softdrink)", "Holding(Coffee)"}, cost=10),
        Action("PutDown(Anything,Anywhere)", pre=set(), add={"Holding(Nothing)"},
               del_set={"Holding(Softdrink)", "Holding(Coffee)"}, cost=0),
    ]
    start = {"At(Robot,Bar)", "Holding(Coffee)", "Exist(Softdrink)"}
    goal = {"On(Softdrink,WaterTable)"}
    return goal, start, actions


def MoveBtoB_num():
    """MoveBtoB 的抽象版本：文字用抽象符号表示，用来做随机 benchmark。

    注意：文字统一用**字符串**（"1"、"c_goal" 等），这样规划出的条件和
    运行时节点的名字才能对得上。
    """
    actions = [
        Action("a1", pre={"1", "4"}, add={"c_goal"}, del_set={"1", "4"}),
        Action("a2", pre={"1", "2", "3"}, add={"c_goal"}, del_set={"1", "2", "3"}),
        Action("a3", pre={"1", "2"}, add={"4"}, del_set={"2"}),
        Action("a4", pre={"c_start"}, add={"1", "2", "3"}, del_set={"c_start", "4"}),
    ]
    start = {"c_start"}
    goal = {"c_goal"}
    return goal, start, actions


def Cond2BelongsToCond3():
    """论文里的例子：条件 2 从属于条件 3，用来检验剪枝。"""
    actions = [
        Action("a1", pre={"1", "4"}, add={"c_goal"}, del_set={"1", "4"}),
        Action("a2", pre={"1", "2", "3"}, add={"c_goal"}, del_set={"1", "2", "3"}),
        Action("a3", pre={"1", "2"}, add={"4"}, del_set={"2"}),
        Action("a4", pre={"c_start"}, add={"1", "2", "3"}, del_set={"c_start", "4"}),
    ]
    start = {"c_start"}
    goal = {"c_goal"}
    return goal, start, actions


def Test():
    """多目标例子：目标有 5 个文字，需要多个动作配合。"""
    actions = [
        Action("a1", pre={"6"}, add={"0", "2", "4"}, del_set={"1", "5"}),
        Action("a2", pre=set(), add={"0", "1"}, del_set=set()),
        Action("a3", pre={"1", "6"}, add={"0", "2", "3", "5"}, del_set={"1", "6"}),
        Action("a4", pre={"0", "2", "3"}, add={"4", "5"}, del_set={"0", "6"}),
        Action("a5", pre={"0", "1", "4"}, add={"2", "3", "6"}, del_set={"0"}),
    ]
    start = {"1", "2", "6"}
    goal = {"0", "1", "2", "4", "6"}
    return goal, start, actions
