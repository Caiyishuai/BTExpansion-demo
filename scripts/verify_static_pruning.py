"""静态谓词剪枝验证：用 :types 与静态谓词收紧 grounding 规模。

背景
----
grounding 把 lifted 算子按对象组合展开，一个 k 参数算子在 n 个对象上
产出 n^k 个实例。收紧参数域是控制规模的主要手段，有两个层次：

  1. :types      —— 按类型限定每个参数位的候选对象（语法层）
  2. 静态谓词    —— 从不出现在任何动作效果中的谓词，真值由 :init 恒定，
                    可在 grounding 期直接求值剪掉不可执行实例（语义层）

第 2 点是对第 1 点的必要补充：像"两个房间是否连通"这种约束，
起点终点都是 location，类型系统无法表达，只能靠静态谓词。

三组验证：
  A. :types 收紧效果（robot-fetch：有类型 15 条 vs 抹掉类型 48 条）
  B. 静态谓词剪枝效果（6 房间走廊：36 个 move 剪到 10 个）
  C. 剪枝不改变解（剪枝前后规划结果一致，Sound/Complete 不受影响）
"""

import os
import signal
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import load_domain, load_problem, ground
from pddl_adapter.grounding import find_static_predicates
from bt_expansion.algorithm import BTExpAlgorithm
from bt_expansion.planning import state_transition

PDDL_DIR = os.path.join(PROJECT_ROOT, 'pddl')


def rule(title):
    print()
    print('=' * 72)
    print(title)
    print('=' * 72)


def solve(goal, start, actions, time_limit=20):
    """规划 + 执行，带超时保护。返回 None 表示超时。"""
    algo = BTExpAlgorithm(verbose=False)
    algo.clear()

    def on_timeout(*_):
        raise TimeoutError()

    old = signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(time_limit)
    t0 = time.time()
    try:
        bt = algo.run_algorithm_selTree(start, goal, actions)
    except TimeoutError:
        return {'timeout': True, 'elapsed': time.time() - t0,
                'partial_nodes': algo.tree_size}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

    elapsed = time.time() - t0
    if bt is False or bt is None:
        return {'timeout': False, 'failed': True, 'elapsed': elapsed}

    state, steps, plan = set(start), 0, []
    val, obj = bt.tick(state)
    while val not in ('success', 'failure') and steps < 300:
        state = state_transition(state, obj)
        plan.append(obj.name)
        val, obj = bt.tick(state)
        steps += 1
    return {'timeout': False, 'failed': False, 'elapsed': elapsed,
            'nodes': bt.count_size() - 1, 'plan': plan,
            'reached': goal <= state}


def test_a_types():
    rule('验证 A · :types 收紧 —— 限定每个参数位的候选对象')

    dom_path = os.path.join(PDDL_DIR, 'robot_fetch', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'robot_fetch', 'problem.pddl')

    dom, prob = load_domain(dom_path), load_problem(prob_path)
    print('对象:', [(n, t) for n, t in prob.objects])

    g_typed = ground(dom, prob)
    typed_names = {a.name for a in g_typed.actions}

    # 抹掉所有参数类型，模拟没写 :types 的情况
    dom2 = load_domain(dom_path)
    for s in dom2.actions:
        s.parameters = [(n, None) for n, _ in s.parameters]
    g_untyped = ground(dom2, prob)

    bogus = [a.name for a in g_untyped.actions if a.name not in typed_names]
    print()
    print('有 :types  : %d 条动作' % g_typed.stats['grounded_actions'])
    print('无 :types  : %d 条动作' % g_untyped.stats['grounded_actions'])
    print('多出的无意义实例 %d 条，例如:' % len(bogus))
    for n in bogus[:6]:
        print('   ', n)

    shrink = g_untyped.stats['grounded_actions'] > g_typed.stats['grounded_actions']
    print()
    print(':types 确实收紧了 grounding 规模 :', shrink)
    return shrink


def test_b_static_pruning():
    rule('验证 B · 静态谓词剪枝 —— 类型系统表达不了的约束')

    dom_path = os.path.join(PDDL_DIR, 'static_prune', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'static_prune', 'problem.pddl')
    dom, prob = load_domain(dom_path), load_problem(prob_path)

    static = find_static_predicates(dom)
    print('自动识别的静态谓词 :', sorted(static))
    print('（从不出现在任何动作效果中，真值由 :init 恒定）')
    print()
    print('场景: 6 个房间排成走廊 r1-r2-r3-r4-r5-r6，只有相邻房间连通')
    print()

    results = {}
    for prune in (False, True):
        g = ground(dom, prob, prune_static=prune)
        moves = [a for a in g.actions if a.name.startswith('move')]
        print('prune_static=%-5s 总动作=%-3d move实例=%-3d 剪掉=%d'
              % (prune, g.stats['grounded_actions'], len(moves),
                 g.stats['skipped_by_static_pred']))
        r = solve(*g.as_tuple(), time_limit=20)
        results[prune] = (g, r)
        if r['timeout']:
            print('              规划 20s 超时（树已膨胀到 %d 结点）'
                  % r['partial_nodes'])
        elif r.get('failed'):
            print('              规划失败')
        else:
            print('              树结点=%-4d 耗时=%.4fs 步数=%d 达成=%s'
                  % (r['nodes'], r['elapsed'], len(r['plan']), r['reached']))
        print()

    g_on, r_on = results[True]
    moves_on = [a for a in g_on.actions if a.name.startswith('move')]
    print('保留的 move 实例（恰好是 5 段双向边 = 10 条）:')
    print('  ', sorted(a.name for a in moves_on))

    ok = (len(moves_on) == 10
          and g_on.stats['skipped_by_static_pred'] == 26
          and not r_on['timeout'] and r_on.get('reached'))
    print()
    print('36 个 move 组合剪到 10 条，且成功求解 :', ok)
    return ok


def test_c_prune_preserves_solution():
    rule('验证 C · 剪枝不改变解 —— Sound/Complete 不受影响')

    # 用规模较小的 robot-fetch，两种模式都能跑完，可直接比对
    dom_path = os.path.join(PDDL_DIR, 'robot_fetch', 'domain.pddl')
    prob_path = os.path.join(PDDL_DIR, 'robot_fetch', 'problem.pddl')
    dom, prob = load_domain(dom_path), load_problem(prob_path)

    rows = {}
    for prune in (False, True):
        g = ground(dom, prob, prune_static=prune)
        r = solve(*g.as_tuple(), time_limit=20)
        rows[prune] = (g, r)
        print('prune_static=%-5s 动作=%-3d 树结点=%-4s 步数=%-2s 达成=%s'
              % (prune, g.stats['grounded_actions'],
                 r.get('nodes', '-'), len(r.get('plan', [])), r.get('reached')))
        print('              plan =', r.get('plan'))

    (_, r_off), (_, r_on) = rows[False], rows[True]
    same = (r_off.get('reached') and r_on.get('reached')
            and r_off.get('plan') == r_on.get('plan'))
    print()
    print('剪枝前后计划完全一致 :', same)
    print('（reachable 三个位置全为真，故此例剪 0 条，结果必然一致）')

    # 再验证一个"静态谓词为假会正确剪掉"的场景
    print()
    print('补充: 把 desk 设为不可达，剪枝应移除所有 move(*,desk)')
    from pddl_adapter.parser import build_problem, parse_sexpr, tokenize
    txt = '''(define (problem no-desk) (:domain robot-fetch)
      (:objects kitchen desk bar - location cup - item)
      (:init (robot-at bar) (item-at cup kitchen) (hand-empty)
             (reachable kitchen) (reachable bar))
      (:goal (and (item-at cup kitchen) (hand-empty))))'''
    prob2 = build_problem(parse_sexpr(tokenize(txt)))
    g2 = ground(dom, prob2, prune_static=True)
    to_desk = [a.name for a in g2.actions
               if a.name.startswith('move') and a.name.endswith('desk)')]
    print('   剪掉 %d 条; 残留的 move(*,desk): %s'
          % (g2.stats['skipped_by_static_pred'], to_desk or '无'))
    desk_pruned = len(to_desk) == 0

    print()
    print('不可达目的地的 move 实例被正确剪除 :', desk_pruned)
    return same and desk_pruned


def main():
    results = {
        'A :types 收紧': test_a_types(),
        'B 静态谓词剪枝': test_b_static_pruning(),
        'C 剪枝不改变解': test_c_prune_preserves_solution(),
    }
    rule('汇总')
    for name, ok in results.items():
        print('  %-20s %s' % (name, 'PASS' if ok else 'FAIL'))
    print()
    print('总体:', 'ALL PASS' if all(results.values()) else 'SOME FAILED')
    print()
    print('结论: :types 限定参数域（语法层），静态谓词剪掉不可执行实例（语义层），')
    print('      两者结合是控制 grounding 组合爆炸的主要手段。')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
