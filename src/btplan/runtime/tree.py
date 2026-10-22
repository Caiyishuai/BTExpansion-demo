"""BehaviorTree：把一棵 py_trees 树包装成"可驱动、可打印、可画图"的对象。

典型用法（三步）：

    bt = BehaviorTree(root)   # 1. 包装
    bt.bind_env(env)          # 2. 把环境注入所有节点
    bt.tick()                 # 3. 由 py_trees 决定这一拍做什么
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import py_trees as pt

from btplan.runtime.visitor import StatusVisitor

if TYPE_CHECKING:
    from btplan.env.protocol import Environment


class BehaviorTree(pt.trees.BehaviourTree):
    """一棵可运行的行为树。"""

    def __init__(self, root: pt.behaviour.Behaviour) -> None:
        super().__init__(root)
        self.visitor = StatusVisitor()
        self.visitors.append(self.visitor)
        self.setup(timeout=15)

    @property
    def tick_count(self) -> int:
        """已经 tick 了多少拍。"""
        return self.count

    def bind_env(self, env: "Environment") -> None:
        """把环境递归注入所有节点（条件/动作节点靠它读状态、改状态）。"""
        self.root.bind_env(env)

    def tick(self, *args, **kwargs) -> pt.common.Status:
        """tick 一拍，返回根节点状态（SUCCESS / FAILURE / RUNNING）。"""
        super().tick(*args, **kwargs)
        return self.root.status

    @property
    def status(self) -> pt.common.Status:
        return self.root.status

    def print_tree(self, show_status: bool = True) -> None:
        """把树结构打印出来（`show_status=True` 时附带各节点当前状态）。"""
        print(pt.display.unicode_tree(self.root, show_status=show_status))

    def draw(
        self,
        file_name: str = "behavior_tree",
        target_directory: Optional[str] = None,
    ):
        """渲染成 Graphviz 图（需要 `pip install 'btplan[draw]'` 与系统 graphviz）。"""
        try:
            import pydot  # noqa: F401
        except ImportError:  # pragma: no cover
            raise ImportError(
                "画图需要 pydot，请执行：pip install 'btplan[draw]'"
            ) from None
        return pt.display.render_dot_tree(
            self.root, name=file_name, target_directory=target_directory
        )

    def __repr__(self) -> str:
        return f"BehaviorTree(root={self.root.name!r}, ticks={self.tick_count})"
