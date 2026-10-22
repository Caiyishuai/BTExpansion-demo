"""扩展规则（BT Expansion 的三条核心判据）。

算法从目标出发**反向**扩展：不断问"要让条件 c 成立，可以先做什么？"
下面三个函数就是这个问题的答案。
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Tuple

from btplan.core.action import Action


def is_consequence(condition, action: Action) -> bool:
    """动作 `action` 能否"产出"条件 `condition`？

    两条判据（与原论文一致）：

    1. 动作的前提或效果确实**碰到**了这个条件：
       ``c & ((pre ∪ add) - del_set)`` 非空
    2. 动作**不会删掉**条件里已经成立的文字：``c - del_set == c``
    """
    if condition & ((action.pre | action.add) - action.del_set) <= set():
        return False
    if (condition - action.del_set) != condition:
        return False
    return True


def premise_of(condition, action: Action):
    """为了让 `condition` 成立而执行 `action`，之前必须先成立什么？

        c_attr = (action.pre ∪ c) - action.add

    也就是"动作的前提 + 还没达成目标的部分"。
    """
    return (action.pre | condition) - action.add


def has_no_subset(candidate, expanded: Iterable) -> bool:
    """剪枝判据：已扩展过的条件里，是否已有 `candidate` 的子集？

    若某个已扩展条件 e ⊆ candidate，说明 candidate 这条路已经被更宽的
    条件覆盖过了，再扩展只会长出冗余分支。
    """
    return all(not (e <= candidate) for e in expanded)


def expandable_actions(
    condition,
    actions: Iterable[Action],
    expanded: Iterable = (),
    conflict_check: Optional[Callable[[frozenset], bool]] = None,
) -> List[Tuple[Action, frozenset]]:
    """列出所有能把 `condition` 往前推一步的 (动作, 新前提) 组合。

    Args:
        condition: 待扩展的条件（文字集合）。
        actions: 可用动作。
        expanded: 已扩展过的条件，用于剪枝。
        conflict_check: 可选的自相矛盾检测（例如"同时拿着两样东西"），
            返回 True 表示这个前提不成立，应当跳过。
    """
    result: List[Tuple[Action, frozenset]] = []
    for action in actions:
        if not is_consequence(condition, action):
            continue
        premise = premise_of(condition, action)
        if not has_no_subset(premise, expanded):
            continue
        if conflict_check is not None and conflict_check(premise):
            continue
        result.append((action, frozenset(premise)))
    return result
