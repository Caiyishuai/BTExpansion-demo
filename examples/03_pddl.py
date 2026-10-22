"""示例 03 —— 直接吃 PDDL（domain + problem），生成并运行行为树。

你会学到什么
------------
1. 标准 PDDL 怎么变成一棵行为树（不需要写任何 Python 节点类）
2. 兼容性报告怎么看：这个 domain 能不能拿到 Sound/Complete 保证
3. grounding 之后发生了什么（谓词 → 文字、动作模板 → 具体动作）

前置阅读：examples/02_plan_and_run.py
运行命令：python examples/03_pddl.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btplan.pddl import default_sample, solve_pddl  # noqa: E402


def main() -> None:
    # 仓库自带样例：pddl/{minimal, movebtob, neg_precond, static_prune,
    #               cond_effects, robot_fetch, unsupported}
    domain_path, problem_path = default_sample("movebtob")
    print(f"domain : {domain_path}")
    print(f"problem: {problem_path}\n")

    # 换成自己的 PDDL：
    # res = solve_pddl("my/domain.pddl", "my/problem.pddl")
    res = solve_pddl(domain_path, problem_path)

    # ① 兼容性诊断：SUPPORTED 才保证生成的树 Sound + Complete
    print("=========== 兼容性报告 ===========")
    print(res.report.format())

    # ② 初始状态与目标（grounding 之后都是字符串文字）
    print("=========== grounding ===========")
    print("初始状态：", sorted(res.start))
    print("目标    ：", sorted(res.goal))
    print("可用动作：", len(res.actions), "个，例如",
          [a.name for a in res.actions[:3]])

    # ③ 生成的行为树
    print("\n=========== 行为树（PTML）===========")
    print(res.ptml, end="")

    # ④ 由 py_trees 驱动执行
    print("=========== 执行 ===========")
    print(res.summary())
    if res.result:
        print("执行序列：", res.result.actions)


if __name__ == "__main__":
    main()
