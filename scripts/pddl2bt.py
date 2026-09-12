"""PDDL -> BT Expansion 命令行工具。

用法:
  # 只做兼容性判定（不规划），回答"这份 PDDL 能不能拿到 Sound/Complete 策略树"
  python scripts/pddl2bt.py --check domain.pddl problem.pddl

  # 完整转换：判定 -> grounding -> 生成策略树 -> 执行验证 -> 导出 PTML
  python scripts/pddl2bt.py domain.pddl problem.pddl -o output --name mytree

  # 对存在阻断项的输入强行尝试（不保证 Sound/Complete）
  python scripts/pddl2bt.py domain.pddl problem.pddl --no-strict

退出码: 0 成功 / 1 判定为不可转 / 2 规划失败或执行未达目标
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import load_domain, load_problem, check, solve_pddl, UNSUPPORTED


def main():
    ap = argparse.ArgumentParser(
        description='把 PDDL（STRIPS 子集）转成 BT Expansion 的响应式策略树')
    ap.add_argument('domain', help='domain.pddl 路径')
    ap.add_argument('problem', help='problem.pddl 路径')
    ap.add_argument('--check', action='store_true',
                    help='只做兼容性判定，不执行规划')
    ap.add_argument('--no-strict', action='store_true',
                    help='存在阻断项时仍尝试转换（不保证 Sound/Complete）')
    ap.add_argument('-o', '--output-dir', default=None, help='PTML 输出目录')
    ap.add_argument('--name', default=None, help='PTML 文件名（不含扩展名）')
    ap.add_argument('-v', '--verbose', action='store_true', help='打印扩展过程')
    args = ap.parse_args()

    for path in (args.domain, args.problem):
        if not os.path.isfile(path):
            print(f'错误: 找不到文件 {path}', file=sys.stderr)
            return 1

    dom = load_domain(args.domain)
    prob = load_problem(args.problem)

    print('=' * 68)
    print(f'domain : {dom.name}   ({len(dom.actions)} 个 lifted 算子, '
          f'{len(dom.predicates)} 个谓词)')
    print(f'problem: {prob.name}  ({len(prob.objects)} 个对象)')
    print('=' * 68)

    report = check(dom, prob)
    print()
    print(report.format())

    if args.check:
        return 0 if report.can_convert else 1

    if report.verdict == UNSUPPORTED and not args.no_strict:
        print()
        print('已停止。如需强行尝试（放弃 Sound/Complete 保证），加 --no-strict')
        return 1

    res = solve_pddl(args.domain, args.problem,
                     verbose=args.verbose,
                     strict=not args.no_strict,
                     ptml_name=args.name,
                     output_dir=args.output_dir)

    print()
    print('-' * 68)
    if res.grounding:
        print('grounding 统计:')
        for k, v in res.grounding.stats.items():
            print(f'   {k:<22} {v}')

    if res.bt is None:
        print()
        print('未能生成策略树:', res.aborted_reason)
        return 2

    print()
    print(f'策略树结点数 : {res.tree_size}')
    print(f'规划耗时     : {res.planning_time:.4f}s')
    print(f'执行动作序列 : {res.plan}')
    print(f'累计代价     : {res.cost}')
    print(f'tick 次数    : {res.ticks}')
    print(f'达成目标     : {res.reached_goal}')
    if res.aborted_reason:
        print(f'备注         : {res.aborted_reason}')

    print()
    print('--- 策略树 (PTML) ---')
    print(res.ptml.strip())

    if args.output_dir or args.name:
        out = args.output_dir or os.path.join(PROJECT_ROOT, 'output')
        name = args.name or os.path.splitext(os.path.basename(args.problem))[0]
        print()
        print(f'已写入: {os.path.join(out, name + ".ptml")}')

    return 0 if res.reached_goal else 2


if __name__ == '__main__':
    sys.exit(main())
