"""行为库（BehaviorLibrary）：把"符号文字 → py_trees 节点类"的映射集中管理。

两种用法，按需选择：

1. **零配置**（默认）：直接用默认语义造节点，新手不需要先写任何类。

       make_condition("At(b,ab)")   # 判断 At(b,ab) 是否在当前状态里
       make_action("Move(b,ab)")     # 前提满足则执行一步

2. **自定义**：写一个 ConditionNode / ActionNode 子类，注册进行为库后，
   同名的文字就会用你的类（比如去读真实机器人传感器）。

       lib = BehaviorLibrary()
       lib.register(MyAtCondition)          # 单个类
       lib.load_from_directory("domains/coffee")   # 整个文件夹
       make_condition("At(b,ab)", lib)
"""

from __future__ import annotations

import importlib.util
import inspect
import os
from typing import Optional

from btplan.core.predicate import parse_predicate
from btplan.runtime import nodes
from btplan.runtime.nodes import ActionNode, ConditionNode

CONDITION = "Condition"
ACTION = "Action"


class BehaviorLibrary(dict):
    """``{"Condition": {类名: 类}, "Action": {类名: 类}}``。"""

    def __init__(self) -> None:
        super().__init__({CONDITION: {}, ACTION: {}})

    # ------------------------------ 注册 ------------------------------ #

    def register(self, cls: type) -> type:
        """注册一个 ConditionNode / ActionNode 子类。"""
        if issubclass(cls, ConditionNode):
            self[CONDITION][cls.__name__] = cls
        elif issubclass(cls, ActionNode):
            self[ACTION][cls.__name__] = cls
        else:
            raise TypeError(
                f"{cls.__name__} 必须继承 ConditionNode 或 ActionNode"
            )
        return cls

    def load_from_directory(self, path: str) -> "BehaviorLibrary":
        """从 ``path/Condition/*.py`` 与 ``path/Action/*.py`` 加载所有节点类。"""
        for kind in (CONDITION, ACTION):
            folder = os.path.join(path, kind)
            if not os.path.isdir(folder):
                continue
            for filename in sorted(os.listdir(folder)):
                if not filename.endswith(".py") or filename.startswith("_"):
                    continue
                module = _load_module(os.path.join(folder, filename))
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ != module.__name__:
                        continue  # 跳过 import 进来的类
                    if issubclass(obj, (ConditionNode, ActionNode)) and obj not in (
                        ConditionNode,
                        ActionNode,
                    ):
                        self.register(obj)
        return self

    # ------------------------------ 造节点 ---------------------------- #

    def make_condition(self, literal: str) -> ConditionNode:
        cls_name, args = parse_predicate(literal)
        cls = self[CONDITION].get(cls_name)
        return cls(*args) if cls else nodes.make_condition(literal)

    def make_action(self, literal: str) -> ActionNode:
        cls_name, args = parse_predicate(literal)
        cls = self[ACTION].get(cls_name)
        return cls(*args) if cls else nodes.make_action(literal)

    def make_composite_condition(self, literals) -> nodes.CompositeCondition:
        return nodes.CompositeCondition(
            children=[self.make_condition(x) for x in literals]
        )


def _load_module(file_path: str):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_condition(literal: str, library: Optional[BehaviorLibrary] = None) -> ConditionNode:
    """按文字造条件节点；给了 library 就优先用库里注册的类。"""
    if library is None:
        return nodes.make_condition(literal)
    return library.make_condition(literal)


def make_action(literal: str, library: Optional[BehaviorLibrary] = None) -> ActionNode:
    """按文字造动作节点；给了 library 就优先用库里注册的类。"""
    if library is None:
        return nodes.make_action(literal)
    return library.make_action(literal)
