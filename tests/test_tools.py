"""工具层测试：随机问题生成器 + benchmark。

运行：python tests/test_tools.py   （或 pytest tests/）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan import solve  # noqa: E402
from btplan.domains import generate_problem, generate_problems  # noqa: E402
from btplan.domains.random_problems import state_transition  # noqa: E402
from btplan.tools.benchmark import format_report, run_benchmark  # noqa: E402


def test_generate_problem_is_reproducible() -> None:
    """同一个种子必须得到同一个问题。"""
    a = generate_problem(seed=7)
    b = generate_problem(seed=7)
    assert a[0] == b[0] and a[1] == b[1]
    assert [x.name for x in a[2]] == [x.name for x in b[2]]


def test_generated_problem_is_solvable() -> None:
    """随机问题的目标按构造可达，所以一定能解出来。"""
    for seed in range(10):
        goal, start, actions = generate_problem(seed=seed)
        result = solve(start, goal, actions)
        assert result.success is True, f"seed={seed} 未达成：{result.summary()}"


def test_generate_problems_batch() -> None:
    problems = generate_problems(5, seed=100)
    assert len(problems) == 5
    for goal, start, actions in problems:
        assert goal and actions


def test_state_transition_respects_precondition() -> None:
    from btplan import Action

    action = Action("a", pre={"x"}, add={"y"}, del_set={"x"})
    assert state_transition({"x"}, action) == frozenset({"y"})
    assert state_transition({"z"}, action) == frozenset({"z"})   # 前提不满足，原样返回


def test_benchmark_all_solved() -> None:
    """小规模 benchmark：成功率必须是 100%。"""
    result = run_benchmark(problems=20, seed=1)
    assert result.total == 20
    assert result.solved == 20, format_report(result)
    assert result.failures == []


def test_benchmark_report_is_readable() -> None:
    report = format_report(run_benchmark(problems=3, seed=2))
    assert "成功率" in report


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} 个测试全部通过")
