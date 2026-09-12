"""条件效果（分支 add）编译验证。

回答的问题：BT Expansion 的 add 是扁平集合，无法表达
「在 C1 时 add E1，在 C2 时 add E2」。本脚本验证适配器的编译方案确实能表达它。

三组验证：
  A. 编译正确性：2 条 (when ...) 编译出 4 个互斥分支，前提互斥、add 各异
  B. 规划正确性：目标要求"拿到且不摔坏不累"时，算法主动规避有害分支
  C. 语义等价性：穷举所有初始状态，逐一比对"编译后动作集"与"原始条件效果语义"
"""

import itertools
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import load_domain, load_problem, ground, solve_pddl
from pddl_adapter.cond_effects import split_effect, compile_conditional_effects

PDDL_DIR = os.path.join(PROJECT_ROOT, 'pddl')
COND = (os.path.join(PDDL_DIR, 'cond_effects', 'domain.pddl'),
        os.path.join(PDDL_DIR, 'cond_effects', 'problem.pddl'))


def rule(title):
    print()
    print('=' * 72)
    print(title)
    print('=' * 72)


def test_a_compile_shape():
    rule('验证 A · 编译结构：2 条 when -> 4 个互斥分支，add 各不相同')

    dom, prob = load_domain(COND[0]), load_problem(COND[1])
    pick = next(s for s in dom.actions if s.name == 'pick')
    uncond, conds = split_effect(pick.effect)
    print('pick 的效果拆解:')
    print('   无条件部分 :', [('not ' if n else '') + a.to_literal()
                              for a, n in uncond])
    for ce in conds:
        print('   条件效果   :', ce)

    g = ground(dom, prob)
    picks = [a for a in g.actions if a.name.startswith('pick')]
    print()
    print('编译出的分支 (%d 个):' % len(picks))
    for a in picks:
        print('   %-34s add=%s' % (a.name, sorted(a.add)))

    # 前提两两互斥：任取两个分支，必存在某原子被一个要求真、另一个要求假
    pre_sets = [a.pre for a in picks]
    mutually_exclusive = True
    for i, j in itertools.combinations(range(len(picks)), 2):
        pi, pj = pre_sets[i], pre_sets[j]
        conflict = any(lit.startswith('not-') and lit[4:] in pj for lit in pi) or \
                   any(lit.startswith('not-') and lit[4:] in pi for lit in pj)
        if not conflict:
            mutually_exclusive = False
            print('   [!] 分支 %d 与 %d 前提不互斥' % (i, j))

    add_sets = {frozenset(a.add) for a in picks}
    print()
    print('分支数 = 4                :', len(picks) == 4)
    print('前提两两互斥              :', mutually_exclusive)
    print('add 集合各不相同          :', len(add_sets) == len(picks))
    return len(picks) == 4 and mutually_exclusive and len(add_sets) == len(picks)


def test_b_planning():
    rule('验证 B · 规划：目标要求不摔坏不累时，应主动规避有害分支')

    res = solve_pddl(*COND)
    print('兼容性判定 :', res.report.verdict, '(应为 REWRITABLE)')
    print('条件效果统计 : schemas=%s instances=%s'
          % (res.grounding.stats['schemas_with_cond_effects'],
             res.grounding.stats['cond_effect_instances']))
    print()
    print('执行序列 :', res.plan)
    print('累计代价 :', res.cost)
    print('达成目标 :', res.reached_goal)

    # 必须先消除 fragile / heavy，最后才 pick，且走的是 [-fragile,-heavy] 分支
    picked = [p for p in res.plan if p.startswith('pick')]
    safe_branch = bool(picked) and '[-fragile,-heavy]' in picked[-1]
    order_ok = ('reinforce(vase)' in res.plan and 'lighten(vase)' in res.plan
                and res.plan.index('reinforce(vase)') < res.plan.index(picked[-1])
                and res.plan.index('lighten(vase)') < res.plan.index(picked[-1]))
    print()
    print('走的是安全分支 [-fragile,-heavy] :', safe_branch)
    print('reinforce/lighten 均在 pick 之前 :', order_ok)
    return res.reached_goal and safe_branch and order_ok


def _apply_original_semantics(state, uncond, conds, binding_free=True):
    """按 PDDL 原始条件效果语义算后继状态（作为 ground truth）。"""
    add, dele = set(), set()
    for atom, neg in uncond:
        (dele if neg else add).add(atom.to_literal())
    for ce in conds:
        holds = True
        for atom, neg in ce.cond:
            lit = atom.to_literal()
            present = lit in state
            if neg == present:                 # 要求为假却存在，或要求为真却不存在
                holds = False
                break
        if holds:
            for atom, neg in ce.eff:
                (dele if neg else add).add(atom.to_literal())
    return (state | add) - dele


def test_c_semantic_equivalence():
    rule('验证 C · 语义等价：穷举初始状态，比对编译前后的后继状态')

    dom, prob = load_domain(COND[0]), load_problem(COND[1])
    pick = next(s for s in dom.actions if s.name == 'pick')
    uncond, conds = split_effect(pick.effect)

    # 把 schema 里的 ?i 绑定到 vase
    binding = {'?i': 'vase'}
    uncond_g = [(a.substitute(binding), n) for a, n in uncond]
    conds_g = []
    for ce in conds:
        from pddl_adapter.cond_effects import CondEffect
        conds_g.append(CondEffect(
            [(a.substitute(binding), n) for a, n in ce.cond],
            [(a.substitute(binding), n) for a, n in ce.eff]))

    g = ground(dom, prob)
    picks = [a for a in g.actions if a.name.startswith('pick')]

    # 穷举 fragile / heavy / on-table 的真假组合（8 种）
    base_lits = ['fragile(vase)', 'heavy(vase)', 'on-table(vase)']
    mismatches = 0
    checked = 0
    print('逐状态比对（只看 pick 可执行的状态）:')
    for bits in itertools.product([False, True], repeat=len(base_lits)):
        state = {lit for lit, on in zip(base_lits, bits) if on}
        # 补齐编码后的 not-* 文字，使编译版动作的前提可判定
        enc = set(state)
        for lit in base_lits:
            pred = lit.split('(')[0]
            if pred in ('fragile', 'heavy') and lit not in state:
                enc.add('not-' + lit)
        if 'broken(vase)' not in enc:
            enc.add('not-broken(vase)')
        if 'tired' not in enc:
            enc.add('not-tired')

        # 原始语义
        truth = _apply_original_semantics(state, uncond_g, conds_g)

        # 编译版：找到唯一前提满足的分支
        applicable = [a for a in picks if a.pre <= enc]
        if not applicable:
            continue                            # pick 在该状态不可执行
        checked += 1
        if len(applicable) != 1:
            print('   state=%-38s [!] %d 个分支同时可执行（应恰好 1 个）'
                  % (sorted(state), len(applicable)))
            mismatches += 1
            continue
        got = (enc | applicable[0].add) - applicable[0].del_set

        # 只比对原始谓词（忽略补谓词），因为 truth 不含编码
        real_preds = {'fragile(vase)', 'heavy(vase)', 'on-table(vase)',
                      'holding(vase)', 'broken(vase)', 'tired'}
        got_real = got & real_preds
        truth_real = truth & real_preds
        ok = got_real == truth_real
        if not ok:
            mismatches += 1
        print('   state=%-38s 分支=%-22s %s'
              % (sorted(state), applicable[0].name.replace('pick(vase)', ''),
                 'OK' if ok else 'MISMATCH got=%s want=%s'
                 % (sorted(got_real), sorted(truth_real))))

    print()
    print('比对状态数 : %d   不一致 : %d' % (checked, mismatches))
    print('每个可执行状态恰好匹配 1 个分支且语义一致 :', mismatches == 0)
    return mismatches == 0 and checked > 0


def main():
    results = {
        'A 编译结构': test_a_compile_shape(),
        'B 规划规避有害分支': test_b_planning(),
        'C 语义等价': test_c_semantic_equivalence(),
    }
    rule('汇总')
    for name, ok in results.items():
        print('  %-22s %s' % (name, 'PASS' if ok else 'FAIL'))
    print()
    print('总体:', 'ALL PASS' if all(results.values()) else 'SOME FAILED')
    print()
    print('结论: 通过「动作拆分」编译，扁平的 add 可以表达条件分支效果，')
    print('      且保持与 PDDL 原始 (when C E) 语义等价。')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
