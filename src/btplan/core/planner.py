"""规划器（Planner）：BT Expansion 主循环，产出 IR 树。

算法一句话：**从目标出发反向扩展，直到这棵树能从初始状态跑起来。**

    while 树还不能从 start 跑起来:
        挑一个还没扩展过的条件结点 c
        for 每个"能产出 c"的动作 a:
            算出新前提 c_attr = (a.pre ∪ c) - a.add
            挂上一条分支：sequence{cond c_attr, act a}
        把 c 这个结点原地替换成 selector{cond c, 上面那些分支}
        （新长出来的 c_attr 结点留着以后继续扩展）

产出的树天然是"响应式"的：每个 selector 都保留了"目标已达成"这一分支，
所以运行时条件被外界改变也能继续跑，而不是照着一条固定序列执行到底。
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from btplan.core.action import Action
from btplan.core.evaluate import can_run
from btplan.core.expander import expandable_actions
from btplan.ir.node import CONDITION, SELECTOR, BTNode


class PlanningFailure(RuntimeError):
    """所有条件都扩展完了，树仍然跑不起来（该目标不可达）。"""


class Planner:
    """行为树扩展规划器。"""

    def __init__(
        self,
        verbose: bool = False,
        conflict_check: Optional[Callable[[frozenset], bool]] = None,
    ) -> None:
        """
        Args:
            verbose: 打印每一步扩展了什么。
            conflict_check: 可选的自相矛盾检测，用于剪掉物理上不可能的前提
                （比如"同时拿着咖啡和饮料"）。
        """
        self.verbose = verbose
        self.conflict_check = conflict_check
        self.expansions = 0          # 扩展了多少轮（搜索代价的粗略指标）

    # ------------------------------ 对外 ------------------------------ #

    def plan(
        self,
        start: Iterable[str],
        goal: Iterable[str],
        actions: Iterable[Action],
    ) -> BTNode:
        """规划一棵能从 `start` 达成 `goal` 的行为树（IR）。

        Args:
            start: 初始状态（文字集合）。
            goal: 目标（文字集合）。**整个目标作为一个条件一起回溯**——
                目标是"合取"的，必须全部成立才算达成。
                （早期实现会把多目标拆成每文字一棵子树再用 selector 拼，
                  那样只要达成其中一个就会返回成功，语义是错的。）
            actions: 可用动作。

        Returns:
            IR 树的根结点（一个 selector）。
        """
        self.expansions = 0
        return self._plan_single(frozenset(start), frozenset(goal), actions)

    # ------------------------------ 内部 ------------------------------ #

    def _plan_single(
        self,
        start: frozenset,
        goal: frozenset,
        actions: Iterable[Action],
    ) -> BTNode:
        # 树一开始只有一个目标条件结点，它会随着扩展"原地长大"
        root = BTNode.condition(goal)

        pending: List[BTNode] = [root]        # 待扩展的条件结点（按长出顺序）
        expanded: List[frozenset] = []        # 已扩展过的条件（用于剪枝）

        while not can_run(root, start):
            self.expansions += 1

            node = next(
                (n for n in pending if n.node_type == CONDITION and n.literals not in expanded),
                None,
            )
            if node is None:
                raise PlanningFailure(
                    f"目标 {set(goal)} 不可达：所有条件都扩展完了，"
                    f"树仍无法从初始状态运行"
                )

            condition = node.literals
            if self.verbose:
                print(f"[扩展] 条件 {set(condition)}")

            # 这个条件本来就被初始状态满足了，没有继续扩展的必要
            if condition != goal and condition <= start:
                return root

            branches: List[BTNode] = []
            for action, premise in expandable_actions(
                condition, actions, expanded, self.conflict_check
            ):
                branch = BTNode.sequence(children=[
                    BTNode.condition(premise),
                    BTNode.action(action),
                ])
                pending.append(branch.children[0])   # 新条件结点待以后扩展
                branches.append(branch)
                if self.verbose:
                    print(f"        + {action.name} -> 前提 {set(premise)}")

            # 这个条件结点原地"长成"一个 selector：
            #   selector{ 原条件（已经达成就不用动了）, 各条分支 }
            node.node_type = SELECTOR
            node.literals = frozenset()
            node.children = [BTNode.condition(condition)] + branches
            expanded.append(condition)

        # 目标一开始就已达成、完全没扩展过的情况：包一层 selector，
        # 保证 plan() 返回的根始终是 selector。
        if root.node_type == CONDITION:
            root = BTNode.selector(children=[root])
        return root
