"""随机规划问题生成器（benchmark / 鲁棒性测试用）。

生成思路保证**目标一定可达**：

    随机初始状态 ──随机动作──> 状态1 ──> 状态2 ──> … ──> 状态N
                                                        └─ 拿它当目标

这样"规划失败"就一定是算法/实现的问题，而不是问题本身无解。
"""

from __future__ import annotations

import random
from typing import List, Tuple

from btplan.core.action import Action


def random_state(literals_num: int, rng: random.Random):
    """随机挑一部分文字作为初始状态。"""
    return {str(i) for i in range(literals_num) if rng.random() > 0.5}


def random_action(state, literals_num: int, rng: random.Random) -> Action:
    """从当前状态随机造一个动作：状态里有的文字多半进前提，没有的多半进效果。"""
    pre, add, del_set = set(), set(), set()
    for i in range(literals_num):
        literal = str(i)
        if literal in state:
            if rng.random() > 0.5:
                pre.add(literal)
                if rng.random() > 0.5:
                    del_set.add(literal)
            continue
        if rng.random() > 0.5:
            add.add(literal)
            continue
        if rng.random() > 0.5:
            del_set.add(literal)
    return Action(name="?", pre=pre, add=add, del_set=del_set, cost=rng.randint(1, 100))


def state_transition(state, action: Action):
    """在符号世界里执行一步（前提不满足时原样返回）。"""
    if not action.pre <= state:
        return frozenset(state)
    return frozenset((state | action.add) - action.del_set)


def generate_problem(
    seed: int = 1,
    literals_num: int = 10,
    depth: int = 10,
    iters: int = 10,
):
    """生成一个随机问题，返回 ``(goal, start, actions)``。

    Args:
        seed: 随机种子（相同种子得到相同问题）。
        literals_num: 文字总数（决定状态空间大小）。
        depth: 从初始状态往前走多少步。
        iters: 生成多少条动作链（越大动作越多）。
    """
    rng = random.Random(seed)
    start = random_state(literals_num, rng)
    states: List[frozenset] = [frozenset(start)]
    actions: List[Action] = []

    for _ in range(max(1, iters // 5)):
        state = frozenset(start)
        for _ in range(depth):
            action = random_action(state, literals_num, rng)
            action.name = f"a{len(actions) + 1}"
            actions.append(action)
            state = state_transition(state, action)
            if state not in states:
                states.append(state)

    # 目标取"走得最远的那个非空状态"
    goal = states[-1]
    if not goal:
        non_empty = [s for s in states if s]
        goal = non_empty[-1] if non_empty else frozenset(random_state(literals_num, rng))

    return frozenset(goal), frozenset(start), actions


def generate_problems(
    count: int = 100,
    seed: int = 1,
    literals_num: int = 10,
    depth: int = 10,
    iters: int = 10,
) -> List[Tuple[frozenset, frozenset, List[Action]]]:
    """批量生成：第 k 个问题用种子 ``seed + k``。"""
    return [
        generate_problem(seed + k, literals_num, depth, iters)
        for k in range(count)
    ]
