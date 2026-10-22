"""命令行入口 `btplan`。

    btplan plan  --domain MoveBtoB                 规划并打印 PTML
    btplan plan  --domain MakeCoffee --out output   同时写入 output/MakeCoffee.ptml
    btplan run   --domain MoveBtoB                  规划 + py_trees 执行
    btplan run   --pddl <domain.pddl> <problem.pddl>
    btplan draw  --domain MoveBtoB --out output     渲染成 Graphviz 图
    btplan bench --problems 50                      随机问题批量验证
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Tuple

from btplan.core.action import Action
from btplan.env.symbolic import SymbolicEnv
from btplan.ir.serialize import to_ptml
from btplan.runtime.compiler import compile_tree
from btplan.runtime.tree import BehaviorTree


def _load_problem(args) -> Tuple[frozenset, frozenset, List[Action], str]:
    """按 --domain 或 --pddl 载入问题，返回 (goal, start, actions, 名字)。"""
    if args.pddl:
        from btplan.pddl import load_pddl

        domain_path, problem_path = args.pddl
        goal, start, actions, report = load_pddl(
            domain_path, problem_path, strict=not args.force
        )
        print(report.format())
        name = os.path.splitext(os.path.basename(problem_path))[0]
        return goal, start, actions, name

    from btplan import domains

    factory = getattr(domains, args.domain, None)
    if factory is None:
        raise SystemExit(
            f"未知 --domain {args.domain!r}，可选："
            f"{', '.join(domains.__all__)}"
        )
    goal, start, actions = factory()
    return frozenset(goal), frozenset(start), list(actions), args.domain


def _plan(args):
    from btplan.core.planner import Planner

    goal, start, actions, _name = _load_problem(args)
    plan = Planner(verbose=args.verbose).plan(start, goal, actions)
    return goal, start, actions, _name, plan


def cmd_plan(args) -> int:
    goal, start, actions, name, plan = _plan(args)
    plan.print_tree()
    ptml = to_ptml(plan)
    print("\n=========== PTML ===========")
    print(ptml, end="")
    if args.out:
        _write_ptml(args.out, name, ptml)
    return 0


def cmd_run(args) -> int:
    from btplan.env.runner import run

    goal, start, actions, name, plan = _plan(args)
    env = SymbolicEnv(start, actions)
    bt = BehaviorTree(compile_tree(plan))
    bt.bind_env(env)

    print("=========== 运行 ===========")
    result = run(bt, env, goal=goal, verbose=args.verbose)
    print(result.summary())
    print("执行序列：", result.actions)
    if args.out:
        _write_ptml(args.out, name, to_ptml(plan))
    return 0 if result.success else 1


def cmd_draw(args) -> int:
    goal, start, actions, name, plan = _plan(args)
    bt = BehaviorTree(compile_tree(plan))
    try:
        paths = bt.draw(file_name=name, target_directory=args.out)
    except ImportError as exc:
        print(f"{exc}", file=sys.stderr)
        return 1
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


def cmd_bench(args) -> int:
    from btplan.tools.benchmark import format_report, run_benchmark

    result = run_benchmark(
        problems=args.problems,
        literals_num=args.literals,
        depth=args.depth,
        iters=args.iters,
        seed=args.seed,
        verbose=args.verbose,
    )
    print(format_report(result))
    return 0 if result.solved == result.total else 1


def _write_ptml(out_dir: str, name: str, ptml: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.ptml")
    with open(path, "w", encoding="utf-8") as file:
        file.write(ptml)
    print(f"\n已写入 {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="btplan", description="行为树扩展规划：规划 → 编译 → py_trees 执行"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        source = p.add_mutually_exclusive_group(required=True)
        source.add_argument("--domain", help="内置问题名，如 MoveBtoB")
        source.add_argument("--pddl", nargs=2, metavar=("DOMAIN", "PROBLEM"),
                            help="PDDL 文件路径")
        p.add_argument("--out", help="产物输出目录（PTML / 图）")
        p.add_argument("--force", action="store_true",
                       help="PDDL 含阻断项时仍强行尝试（失去 Sound/Complete 保证）")
        p.add_argument("-v", "--verbose", action="store_true")

    p = sub.add_parser("plan", help="规划并打印行为树（PTML）")
    add_common(p)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("run", help="规划并让 py_trees 执行到目标达成")
    add_common(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("draw", help="把行为树渲染成 Graphviz 图")
    add_common(p)
    p.set_defaults(func=cmd_draw)

    p = sub.add_parser("bench", help="随机问题批量验证（正确性 / 规模 / 耗时）")
    p.add_argument("--problems", type=int, default=100)
    p.add_argument("--literals", type=int, default=10)
    p.add_argument("--depth", type=int, default=10)
    p.add_argument("--iters", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_bench)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
