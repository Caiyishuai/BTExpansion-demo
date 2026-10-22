"""tick 过程记录器：把每次 tick 后各节点的状态收集成可读文本。"""

from __future__ import annotations

import py_trees as pt


class StatusVisitor(pt.visitors.VisitorBase):
    """收集一次 tick 中每个节点的状态，用于打印调试。

    用法（BehaviorTree 已内置）：

        bt.tick()
        print(bt.visitor.output_str)
    """

    def __init__(self, skip_composites: bool = True) -> None:
        super().__init__(full=False)
        self.skip_composites = skip_composites
        self.output_str = ""

    def initialise(self) -> None:
        self.output_str = ""

    def run(self, behaviour: pt.behaviour.Behaviour) -> None:
        if self.skip_composites and isinstance(behaviour, pt.composites.Composite):
            return
        prefix = getattr(behaviour, "print_prefix", "")
        label = f"{prefix} {behaviour.name}" if prefix else behaviour.name
        status = behaviour.status.value if behaviour.status is not None else "INVALID"
        self.output_str += f"{label}: {status}\n"
