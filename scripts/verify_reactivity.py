"""验证生成的策略树确实是「响应式」的，而不只是一条包装过的 plan。

这是转法 3 相对转法 1/2 的核心价值主张，必须实证而非口头声称。

做三组扰动实验（都在执行中途篡改状态，模拟外界干扰）：
  A. 进度被回退：已完成的子目标被破坏，树应自动重做
  B. 进度被白送：目标提前达成，树应立即 success 而不做多余动作
  C. 初始状态变化：同一棵树换个初始状态仍能工作（策略 vs 单点解）
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import solve_pddl, load_domain, load_problem, ground
from bt_expansion.algorithm import BTExpAlgorithm
from bt_expansion.planning import state_transition

PDDL_DIR = os.path.join(PROJECT_ROOT, 'pddl')
FETCH = (os.path.join(PDDL_DIR, 'robot_fetch', 'domain.pddl'),
         os.path.join(PDDL_DIR, 'robot_fetch', 'problem.pddl'))


def rule(title):
    print()
    print('=' * 72)
    print(title)
    print('=' * 72)


def build_tree(domain_path, problem_path):
    """只做规划，拿到策略树与 (goal, start, actions)。"""
    dom, prob = load_domain(domain_path), load_problem(problem_path)
    g = ground(dom, prob)
    goal, start, actions = g.as_tuple()
    algo = BTExpAlgorithm(verbose=False)
    algo.clear()
    bt = algo.run_algorithm_selTree(start, goal, actions)
    return bt, goal, start, actions


def run_tree(bt, goal, state, max_steps=60, perturb=None, label=''):
    """执行策略树；perturb(step, state) 可在指定步篡改状态。"""
    state = set(state)
    plan, steps = [], 0
    val, obj = bt.tick(state)
    while val not in ('success', 'failure') and steps < max_steps:
        state = state_transition(state, obj)
        plan.append(obj.name)
        steps += 1
        if perturb is not None:
            new_state = perturb(steps, set(state))
            if new_state is not None and new_state != state:
                print(f'   [扰动@第{steps}步] {label}')
                state = new_state
        val, obj = bt.tick(state)
    return {'plan': plan, 'val': val, 'state': state, 'reached': goal <= state}


def test_a_regression():
    rule('实验 A · 进度被回退：已完成的子目标被外界破坏')
    bt, goal, start, actions = build_tree(*FETCH)

    base = run_tree(bt, goal, start)
    print('无扰动基线   : plan=%s reached=%s' % (base['plan'], base['reached']))

    # 在第 2 步（刚 pick 起杯子）之后，把杯子从手里"抢走"并丢回 kitchen
    def perturb(step, state):
        if step == 2 and 'holding(cup)' in state:
            state.discard('holding(cup)')
            state.add('hand-empty')
            state.add('item-at(cup,kitchen)')
            return state
        return None

    dis = run_tree(bt, goal, start, perturb=perturb,
                   label='杯子被抢走并丢回 kitchen（holding->hand-empty）')
    print('扰动后       : plan=%s' % dis['plan'])
    print('              reached=%s val=%s' % (dis['reached'], dis['val']))
    print()
    recovered = dis['reached'] and len(dis['plan']) > len(base['plan'])
    print('自动重做并最终达成目标 :', recovered)
    print('（plan 变长说明树重新执行了被破坏的步骤，这就是响应式）')
    return recovered


def test_b_free_progress():
    rule('实验 B · 进度被白送：目标被外界提前达成')
    bt, goal, start, actions = build_tree(*FETCH)

    base = run_tree(bt, goal, start)
    print('无扰动基线   : %d 步 plan=%s' % (len(base['plan']), base['plan']))

    # 第 1 步后直接把目标状态白送
    def perturb(step, state):
        if step == 1:
            state.add('item-at(cup,desk)')
            state.add('hand-empty')
            state.discard('holding(cup)')
            state.discard('item-at(cup,kitchen)')
            return state
        return None

    dis = run_tree(bt, goal, start, perturb=perturb,
                   label='目标 item-at(cup,desk) 与 hand-empty 被白送')
    print('扰动后       : %d 步 plan=%s' % (len(dis['plan']), dis['plan']))
    print('              reached=%s val=%s' % (dis['reached'], dis['val']))
    print()
    short_circuit = dis['reached'] and len(dis['plan']) < len(base['plan'])
    print('提前结束、未做多余动作 :', short_circuit)
    print('（步数变少说明树每次 tick 都重新检查条件，而非盲目按序执行）')
    return short_circuit


def test_c_other_initial_states():
    rule('实验 C · 同一棵树换初始状态（策略 vs 单点解）')
    bt, goal, start, actions = build_tree(*FETCH)
    print('树由 start = %s 生成' % sorted(start))
    print('目标 = %s' % sorted(goal))
    print()

    variants = {
        '机器人已在 kitchen': (start - {'robot-at(bar)'}) | {'robot-at(kitchen)'},
        '机器人已在 desk': (start - {'robot-at(bar)'}) | {'robot-at(desk)'},
        '杯子已在 desk 上(目标已满足)': (
            (start - {'item-at(cup,kitchen)'}) | {'item-at(cup,desk)'}),
        '已握着杯子在 desk': (
            (start - {'item-at(cup,kitchen)', 'hand-empty', 'robot-at(bar)'})
            | {'holding(cup)', 'robot-at(desk)'}),
    }

    all_ok = True
    for label, st in variants.items():
        r = run_tree(bt, goal, st)
        ok = r['reached']
        all_ok = all_ok and ok
        print('   %-28s -> %-6s %d 步 %s'
              % (label, 'OK' if ok else 'FAIL', len(r['plan']), r['plan']))

    print()
    print('同一棵树覆盖全部初始状态变体 :', all_ok)
    print('（一条 plan 做不到这点——它只对生成时那个初始状态有效）')
    return all_ok


def main():
    results = {
        'A 进度回退后自愈': test_a_regression(),
        'B 目标白送时短路': test_b_free_progress(),
        'C 跨初始状态复用': test_c_other_initial_states(),
    }
    rule('汇总')
    for name, ok in results.items():
        print('  %-20s %s' % (name, 'PASS' if ok else 'FAIL'))
    print()
    print('总体:', 'ALL PASS' if all(results.values()) else 'SOME FAILED')
    print()
    print('结论: 生成的树是真正的响应式策略（policy），而非包装过的动作序列（plan）。')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
