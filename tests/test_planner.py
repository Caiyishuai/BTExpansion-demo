"""规划层的测试：结构、可执行性、失败路径。

运行：python tests/test_planner.py   （或 pytest tests/）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan import Planner, PlanningFailure, compile_tree, solve, to_ptml  # noqa: E402
from btplan.core.evaluate import can_run  # noqa: E402
from btplan.domains import (  # noqa: E402
    Cond2BelongsToCond3,
    MakeCoffee,
    MakeCoffeeCost,
    MoveBtoB,
    MoveBtoB_num,
    ServeCoffee,
    SoftdrinkCost,
    Test,
)

ALL_DOMAINS = [
    MoveBtoB,
    MoveBtoB_num,
    ServeCoffee,
    MakeCoffee,
    MakeCoffeeCost,
    SoftdrinkCost,
    Cond2BelongsToCond3,
    Test,
]


def test_move_b_to_b_tree_shape() -> None:
    """MoveBtoB：目标分支 + 一条"先挪开 s 再搬 b"的分支。"""
    goal, start, actions = MoveBtoB()
    plan = Planner().plan(start, goal, actions)

    assert plan.node_type == "selector"
    assert plan.children[0].literals == frozenset({"At(b,ab)"})

    branch = plan.children[1]
    assert branch.node_type == "sequence"
    assert branch.children[-1].action.name == "Move(b,ab)"

    # 前置条件结点被继续扩展成了一个 selector（含"已达成"分支 + 挪开 s 的分支）
    expanded = branch.children[0]
    assert expanded.node_type == "selector"
    assert expanded.children[0].literals == frozenset({"Free(ab)", "WayClear"})
    sub_branch = expanded.children[1]
    assert sub_branch.children[-1].action.name == "Move(s,as)"


def test_plan_can_run_from_start() -> None:
    """规划出的树必须能从初始状态跑起来。"""
    for domain in ALL_DOMAINS:
        goal, start, actions = domain()
        plan = Planner().plan(start, goal, actions)
        assert can_run(plan, start), f"{domain.__name__} 规划出的树跑不起来"


def test_solve_reaches_goal_on_every_domain() -> None:
    """端到端：规划的树经 py_trees 驱动后必须真正达成目标。"""
    for domain in ALL_DOMAINS:
        goal, start, actions = domain()
        result = solve(start, goal, actions)
        assert result.success is True, f"{domain.__name__} 未达成目标：{result.summary()}"
        assert result.plan is not None


def test_ptml_roundtrip_contains_all_actions() -> None:
    """PTML 里应出现树中所有动作节点。"""
    goal, start, actions = MakeCoffee()
    plan = Planner().plan(start, goal, actions)

    def collect_actions(node, found):
        if node.node_type == "action":
            found.add(node.action.name)
        for child in node.children:
            collect_actions(child, found)
        return found

    used = collect_actions(plan, set())
    ptml = to_ptml(plan)
    for name in used:
        assert f"act {name}" in ptml


def test_unreachable_goal_raises() -> None:
    """目标不可达时应明确报错，而不是静默返回一棵跑不动的树。"""
    from btplan import Action

    actions = [Action("DoNothing", pre={"Impossible"}, add=set(), del_set=set())]
    try:
        Planner().plan(set(), {"Goal"}, actions)
    except PlanningFailure:
        return
    raise AssertionError("目标不可达时应当抛出 PlanningFailure")


def test_goal_already_satisfied() -> None:
    """目标已经达成时，不扩展，直接返回单点树。"""
    from btplan import Action

    goal, start, actions = MoveBtoB()
    satisfied_start = start | goal
    plan = Planner().plan(satisfied_start, goal, actions)
    assert len(plan.children) == 1
    assert plan.children[0].literals == frozenset(goal)


def test_compile_tree_produces_tickable_root() -> None:
    """编译结果必须是一棵能被 py_trees tick 的树。"""
    goal, start, actions = MoveBtoB()
    plan = Planner().plan(start, goal, actions)
    root = compile_tree(plan)
    assert root.children, "编译出的树不应为空"
    assert hasattr(root, "bind_env")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} 个测试全部通过")
