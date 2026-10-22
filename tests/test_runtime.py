"""运行时层的最小回归测试。

运行：python tests/test_runtime.py   （或 pytest tests/）
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan import (  # noqa: E402
    Action,
    BehaviorTree,
    CompositeCondition,
    Fallback,
    Sequence,
    Status,
    SymbolicEnv,
    make_action,
    make_condition,
    run,
)


def _env_and_tree():
    actions = [
        Action("Move(b,ab)", pre={"Free(ab)"}, add={"At(b,ab)"},
               del_set={"Free(ab)", "At(b,pb)"}),
    ]
    env = SymbolicEnv({"Free(ab)", "At(b,pb)"}, actions)
    root = Fallback("bt", children=[
        make_condition("At(b,ab)"),
        Sequence("move", children=[
            make_condition("Free(ab)"),
            make_action("Move(b,ab)"),
        ]),
    ])
    bt = BehaviorTree(root)
    bt.bind_env(env)
    return env, bt


def test_goal_already_satisfied() -> None:
    """目标已达成时，第一拍就该成功且不执行任何动作。"""
    env, bt = _env_and_tree()
    env.state = frozenset({"At(b,ab)"})
    result = run(bt, env, goal={"At(b,ab)"})
    assert result.success is True
    assert result.actions == []
    assert result.ticks == 1


def test_one_shot_action_reaches_goal() -> None:
    """一步动作：两拍达成目标（第一拍搬，第二拍确认目标成立）。"""
    env, bt = _env_and_tree()
    result = run(bt, env, goal={"At(b,ab)"})
    assert result.success is True
    assert result.actions == ["Move(b,ab)"]
    assert result.cost == 1.0
    assert "At(b,ab)" in env.state


def test_failure_when_no_branch_applies() -> None:
    """没有可用分支时，根节点返回 FAILURE，运行判定为失败。"""
    actions = [Action("Move(b,ab)", pre={"Free(ab)"}, add={"At(b,ab)"})]
    env = SymbolicEnv({"At(b,pb)"}, actions)        # Free(ab) 不成立
    root = Fallback("bt", children=[
        Sequence("move", children=[
            make_condition("Free(ab)"),
            make_action("Move(b,ab)"),
        ]),
    ])
    bt = BehaviorTree(root)
    bt.bind_env(env)
    result = run(bt, env, goal={"At(b,ab)"})
    assert result.success is False
    assert result.status == "FAILURE"
    assert result.actions == []


def test_composite_condition_requires_all_literals() -> None:
    """多文字条件：缺任意一个文字就算 FAILURE。"""
    env = SymbolicEnv({"Free(ab)"})                 # 缺 WayClear
    node = CompositeCondition({"Free(ab)", "WayClear"})
    node.bind_env(env)
    assert node.update() is Status.FAILURE

    env.state = frozenset({"Free(ab)", "WayClear"})
    assert node.update() is Status.SUCCESS


def test_max_ticks_guard() -> None:
    """永远 RUNNING 的动作不会把循环卡死。"""

    from btplan import ActionNode

    class NeverDone(ActionNode):
        def update(self) -> Status:
            return Status.RUNNING

    env = SymbolicEnv(set(), [Action("NeverDone")])
    root = Sequence("s", children=[NeverDone()])
    bt = BehaviorTree(root)
    bt.bind_env(env)
    result = run(bt, env, goal={"At(b,ab)"}, max_ticks=5)
    assert result.success is False
    assert result.ticks == 5


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} 个测试全部通过")
