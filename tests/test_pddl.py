"""PDDL 前端测试：仓库自带的每个样例都要能跑通（unsupported 除外）。

运行：python tests/test_pddl.py   （或 pytest tests/）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan.pddl import default_sample, load_pddl, solve_pddl  # noqa: E402

SOLVABLE = ["minimal", "movebtob", "neg_precond", "static_prune",
            "cond_effects", "robot_fetch"]


def test_every_sample_solves() -> None:
    """每个可解样例：规划 + 执行都要真的达成目标。"""
    for name in SOLVABLE:
        domain, problem = default_sample(name)
        res = solve_pddl(domain, problem)
        assert res.aborted_reason == "", f"{name} 被中止：{res.aborted_reason}"
        assert res.ok is True, f"{name} 未达成目标：{res.summary()}"
        assert res.ptml.startswith("selector{")


def test_goal_is_really_satisfied() -> None:
    """执行完之后，目标文字必须真的都在状态里。"""
    domain, problem = default_sample("robot_fetch")
    res = solve_pddl(domain, problem)
    assert res.result is not None
    executed = res.result.actions
    assert executed, "应当至少执行一个动作"

    # 用环境回放一遍，确认目标成立
    from btplan import SymbolicEnv

    env = SymbolicEnv(res.start, res.actions)
    for name in executed:
        env.apply(name)
    assert res.goal <= env.state, "回放后目标仍未成立"


def test_grounding_produces_plain_str_literals() -> None:
    """grounding 的产物必须是字符串文字，才能和运行时节点名对上。"""
    domain, problem = default_sample("movebtob")
    goal, start, actions, _report = load_pddl(domain, problem)

    assert all(isinstance(x, str) for x in goal | start)
    for action in actions:
        assert isinstance(action.name, str)
        assert all(isinstance(x, str) for x in action.pre | action.add | action.del_set)


def test_unsupported_domain_is_blocked() -> None:
    """含阻断项的 domain 在 strict=True 时应被拦下，而不是给出没保证的树。"""
    domain, problem = default_sample("unsupported")
    res = solve_pddl(domain, problem)
    assert res.plan is None
    assert "阻断项" in res.aborted_reason


def test_unsupported_domain_can_be_forced() -> None:
    """strict=False 时不再因"阻断项"被拦下（但结果没有 Sound/Complete 保证）。"""
    domain, problem = default_sample("unsupported")
    res = solve_pddl(domain, problem, strict=False)
    assert "阻断项" not in res.aborted_reason
    # 本样例的 goal 在 grounding 后为空，因此走到"无需规划"分支
    assert res.plan is None


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} 个测试全部通过")
