"""PDDL 适配器端到端验证。

跑三件事：
  1. 对拍：PDDL 版 MoveBtoB 与 examples.py 手写版，生成的树与执行结果是否一致
  2. lifted 收益：带 typing 的 robot-fetch，一条模板 grounding 出多少动作，能否求解
  3. 边界识别：unsupported 样例是否被检查器精确拒绝并给出可操作诊断

运行:
  python scripts/verify_pddl_adapter.py
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import solve_pddl, load_domain, load_problem, check, ground
from bt_expansion.algorithm import BTExpAlgorithm
from bt_expansion.planning import state_transition
from bt_expansion.examples import MoveBtoB

PDDL_DIR = os.path.join(PROJECT_ROOT, 'pddl')


def rule(title):
    print()
    print('=' * 72)
    print(title)
    print('=' * 72)


def run_handwritten(goal, start, actions):
    """用与适配器相同的方式跑手写版，保证对拍公平。"""
    algo = BTExpAlgorithm(verbose=False)
    algo.clear()
    bt = algo.run_algorithm_selTree(start, goal, actions)
    if bt is False or bt is None:
        return None
    algo.bt = bt
    state, steps, plan = set(start), 0, []
    val, obj, cost, ticks = bt.cost_tick(state, 0, 0)
    total = cost
    while val not in ('success', 'failure') and steps < 500:
        state = state_transition(state, obj)
        plan.append(obj.name)
        val, obj, cost, ticks = bt.cost_tick(state, 0, ticks)
        total += cost
        steps += 1
    return {
        'plan': plan, 'cost': total, 'ticks': ticks,
        'size': bt.count_size() - 1, 'reached': goal <= state,
        'ptml': algo.get_ptml_many_act(),
    }


def test_movebtob_parity():
    rule('测试 1 · 对拍 MoveBtoB（PDDL 版 vs examples.py 手写版）')

    res = solve_pddl(os.path.join(PDDL_DIR, 'movebtob', 'domain.pddl'),
                     os.path.join(PDDL_DIR, 'movebtob', 'problem.pddl'))
    print('兼容性判定 :', res.report.verdict)
    if not res.report.can_convert:
        print(res.report.format())
        return False

    g = res.grounding
    print('grounding    :', g.stats)
    print('start        :', sorted(g.start))
    print('goal         :', sorted(g.goal))

    # --- 逐动作语义等价性检查（比只比树规模更有说服力）
    name_map = {
        'move-b-to-ab': 'Move(b,ab)',
        'move-s-to-ab': 'Move(s,ab)',
        'move-s-to-as': 'Move(s,as)',
    }
    lit_map = {
        'free-ab': 'Free(ab)', 'free-as': 'Free(as)', 'way-clear': 'WayClear',
        'at-b-ab': 'At(b,ab)', 'at-b-pb': 'At(b,pb)', 'at-s-ps': 'At(s,ps)',
    }
    h_goal, h_start, h_actions = MoveBtoB()
    h_by_name = {a.name: a for a in h_actions}

    def tr(s):
        return {lit_map.get(x, x) for x in s}

    print()
    print('--- 逐动作语义等价性（PDDL grounding 结果 vs 手写 Action）---')
    all_equiv = True
    for pa in g.actions:
        hname = name_map.get(pa.name)
        ha = h_by_name.get(hname)
        if ha is None:
            print('   %-14s 手写版无对应动作' % pa.name)
            all_equiv = False
            continue
        # 手写版 add 中被自己 del 抵消的项按 (state|add)-del 语义剔除
        h_add_eff = ha.add - ha.del_set
        same_pre = tr(pa.pre) == ha.pre
        same_add = tr(pa.add) == h_add_eff
        same_del = tr(pa.del_set) == ha.del_set
        same_cost = float(pa.cost) == float(ha.cost)
        ok = same_pre and same_add and same_del and same_cost
        all_equiv = all_equiv and ok
        print('   %-14s -> %-12s pre=%s add=%s del=%s cost=%s  %s'
              % (pa.name, hname, same_pre, same_add, same_del, same_cost,
                 'OK' if ok else 'MISMATCH'))
        if not ok:
            print('        PDDL pre=%s add=%s del=%s cost=%s'
                  % (sorted(tr(pa.pre)), sorted(tr(pa.add)),
                     sorted(tr(pa.del_set)), pa.cost))
            print('        手写 pre=%s add=%s del=%s cost=%s'
                  % (sorted(ha.pre), sorted(h_add_eff),
                     sorted(ha.del_set), ha.cost))

    same_start = tr(g.start) == h_start
    same_goal = tr(g.goal) == h_goal
    print('   start 等价: %s   goal 等价: %s' % (same_start, same_goal))

    print()
    print('PDDL 版结果  : plan=%s cost=%s ticks=%s size=%s reached=%s'
          % (res.plan, res.cost, res.ticks, res.tree_size, res.reached_goal))

    hand = run_handwritten(h_goal, h_start, h_actions)
    print('手写版结果   : plan=%s cost=%s ticks=%s size=%s reached=%s'
          % (hand['plan'], hand['cost'], hand['ticks'],
             hand['size'], hand['reached']))

    print()
    print('--- PDDL 版生成的策略树 (PTML) ---')
    print(res.ptml.strip())

    print()
    print('模型逐项等价 :', all_equiv and same_start and same_goal)
    print('两版均达成目标 :', res.reached_goal and hand['reached'])
    print('树规模 PDDL=%s 手写=%s（手写版 add/del 冲突使其动作更少，'
          '故树可小于 PDDL 版；等价性以逐动作检查为准）'
          % (res.tree_size, hand['size']))
    return (all_equiv and same_start and same_goal
            and res.reached_goal and hand['reached'])


def test_lifted_typing():
    rule('测试 2 · lifted + typing（robot-fetch，一条模板覆盖多对象）')

    dom_path = os.path.join(PDDL_DIR, 'robot_fetch', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'robot_fetch', 'problem.pddl')

    dom, prob = load_domain(dom_path), load_problem(prob_path)
    print('domain 中 lifted 算子数 :', len(dom.actions))
    for s in dom.actions:
        print('   %-8s params=%s' % (s.name, [p for p, _ in s.parameters]))

    rep = check(dom, prob)
    print()
    print('兼容性判定 :', rep.verdict)
    if rep.by_level('REWRITABLE'):
        print('需改写项（适配器自动处理）:')
        for f in rep.by_level('REWRITABLE'):
            print('   -', f.message)

    res = solve_pddl(dom_path, prob_path)
    g = res.grounding
    print()
    print('grounding 统计 :')
    for k, v in g.stats.items():
        print('   %-22s %s' % (k, v))
    print()
    print('3 条 lifted 模板  ->  %d 条 grounded 动作' % g.stats['grounded_actions'])
    print()
    print('规划结果 : reached=%s plan=%s' % (res.reached_goal, res.plan))
    print('           cost=%s ticks=%s tree_size=%s 规划耗时=%.4fs'
          % (res.cost, res.ticks, res.tree_size, res.planning_time))
    if res.aborted_reason:
        print('说明 :', res.aborted_reason)
    print()
    print('--- 生成的策略树 (PTML) ---')
    print(res.ptml.strip())
    return res.reached_goal


def test_negative_preconditions():
    rule('测试 3 · 负前提的补谓词编码（neg-precond）')

    dom_path = os.path.join(PDDL_DIR, 'neg_precond', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'neg_precond', 'problem.pddl')

    res = solve_pddl(dom_path, prob_path)
    print('兼容性判定 :', res.report.verdict, '(应为 REWRITABLE)')
    for f in res.report.by_level('REWRITABLE'):
        print('   需改写:', f.message)

    g = res.grounding
    print()
    print('自动引入的补谓词 :', g.stats['negated_predicates'])
    print('编码后 start     :', sorted(g.start))
    print('编码后 goal      :', sorted(g.goal))
    print()
    print('grounded 动作的前提/效果（注意 not-dirty 的同步维护）:')
    for a in g.actions:
        print('   %-12s pre=%-26s add=%-24s del=%s'
              % (a.name, sorted(a.pre), sorted(a.add), sorted(a.del_set)))

    print()
    print('规划结果 : reached=%s plan=%s cost=%s tree_size=%s'
          % (res.reached_goal, res.plan, res.cost, res.tree_size))
    if res.aborted_reason:
        print('说明 :', res.aborted_reason)
    print()
    print('--- 生成的策略树 (PTML) ---')
    print(res.ptml.strip())

    # 正确行为：cube 初始为 dirty，必须先 wash（消除 dirty）再 dry 再 paint
    expect_wash_before_paint = (
        'wash(cube)' in res.plan and 'paint(cube)' in res.plan
        and res.plan.index('wash(cube)') < res.plan.index('paint(cube)'))
    print()
    print('计划中 wash 先于 paint :', expect_wash_before_paint)
    return res.reached_goal and expect_wash_before_paint


def test_unsupported_detection():
    rule('测试 4 · 边界识别（unsupported 样例应被精确拒绝）')

    dom_path = os.path.join(PDDL_DIR, 'unsupported', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'unsupported', 'problem.pddl')

    dom, prob = load_domain(dom_path), load_problem(prob_path)
    rep = check(dom, prob)
    print(rep.format())

    res = solve_pddl(dom_path, prob_path, strict=True)
    print()
    print('strict 模式下是否停止转换 :', res.bt is None)
    print('停止原因 :', res.aborted_reason)

    codes = {f.code for f in rep.findings}
    # 注意：CONDITIONAL_EFFECT 现已降级为 REWRITABLE（适配器可编译为互斥分支），
    # 故不再属于阻断项。真正的阻断项只剩析取/数值/量词/pre∩add。
    expected = {'DISJUNCTION', 'NUMERIC', 'QUANTIFIER', 'PRE_ADD_OVERLAP'}
    hit = expected & codes
    print()
    print('期望识别的阻断类型 :', sorted(expected))
    print('实际识别到         :', sorted(hit))
    print('全部命中           :', hit == expected)

    cond_rewritable = any(f.code == 'CONDITIONAL_EFFECT'
                          and f.level == 'REWRITABLE' for f in rep.findings)
    print('条件效果被判为 REWRITABLE（而非阻断）:', cond_rewritable)
    return (rep.verdict == 'UNSUPPORTED' and hit == expected
            and cond_rewritable)


def main():
    results = {
        'MoveBtoB 对拍': test_movebtob_parity(),
        'lifted+typing': test_lifted_typing(),
        '负前提编码': test_negative_preconditions(),
        '边界识别': test_unsupported_detection(),
    }
    rule('汇总')
    for name, ok in results.items():
        print('  %-16s %s' % (name, 'PASS' if ok else 'FAIL'))
    print()
    print('总体:', 'ALL PASS' if all(results.values()) else 'SOME FAILED')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
