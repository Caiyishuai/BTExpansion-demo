# 03 · 运行时层（py_trees）

> 对应代码：`src/btplan/runtime/`

## py_trees 速查

| 概念 | 含义 |
| --- | --- |
| `Status.SUCCESS / FAILURE / RUNNING` | 节点一次 tick 的返回值；`RUNNING` = "在做，还没完" |
| `Selector`（本项目叫 `Fallback`） | 从左到右，第一个非失败的孩子即为结果 |
| `Sequence` | 从左到右，遇到 `FAILURE`/`RUNNING` 就停，全过才 `SUCCESS` |
| `tick()` | 从根开始走一遍；控制节点决定走哪些孩子 |

**本项目的 `Fallback` / `Sequence` 固定 `memory=False`**：每个 tick 都从头重新评估。
这是 BT Expansion 响应式语义的前提，不要改成 `True`。

## IR → py_trees 对照

`runtime/compiler.py` 的 `compile_tree()`：

| IR 节点 | py_trees 节点 |
| --- | --- |
| `selector` | `Fallback(memory=False)` |
| `sequence` | `Sequence(memory=False)` |
| `condition`（1 个文字） | `ConditionNode` 子类，名字 = 文字 |
| `condition`（多个文字） | `CompositeCondition`（叶子，内部是 `Sequence` 子树） |
| `condition`（空集合） | `AlwaysTrue` |
| `action` | `ActionNode` 子类，名字 = 动作名 |

## 默认语义（零配置就能跑）

```python
class ConditionNode(BehaviorNode):
    def update(self):
        return SUCCESS if self.literal in self.env.observe() else FAILURE

class ActionNode(BehaviorNode):
    def update(self):
        if not self.env.is_applicable(self.literal):
            return FAILURE
        self.env.apply(self.literal)
        return SUCCESS
```

所以只要给 `Action` 列表，不写任何节点类也能跑完整个流程（见 `examples/02`）。

## 写自己的节点

继承 `ConditionNode` 或 `ActionNode`，实现 `update()`：

```python
from btplan import ConditionNode, ActionNode, Status

class At(ConditionNode):
    """接真实传感器：判断物体是否真的到位。"""
    def update(self) -> Status:
        obj, place = self.args            # At(b,ab) → args = ("b", "ab")
        return Status.SUCCESS if self.env.sensor.at(obj, place) else Status.FAILURE


class Move(ActionNode):
    """多拍才能完成的动作：第一拍启动，后面几拍推进。"""
    def initialise(self):                 # 每次从非 RUNNING 进入时重置
        self.path = None

    def update(self) -> Status:
        obj, place = self.args
        if self.path is None:
            self.path = self.env.plan_path(obj, place)
            if self.path is None:
                return Status.FAILURE
        if self.env.step_along(self.path):
            return Status.SUCCESS
        return Status.RUNNING
```

构造时的参数就是节点名括号里的参数：`Move("b", "ab").name == "Move(b,ab)"`。

## RUNNING 什么时候用

动作不是"一拍就做完"时（机械臂搬东西、导航）：

- 第一拍：校验前提、启动 → 返回 `RUNNING`
- 后续拍：继续推进；完成 → `SUCCESS`；出错 → `FAILURE`

`run()` 会一直 tick，直到根返回 `SUCCESS`/`FAILURE` 或超过 `max_ticks`。
最小示例见 `examples/01_hello_bt.py` 第二幕的 `MoveSlowly`。

## 行为库

把"文字 → 节点类"的映射集中管理（`runtime/library.py`）：

```python
from btplan import BehaviorLibrary, make_condition

lib = BehaviorLibrary()
lib.register(At)                       # 注册单个类
lib.load_from_directory("my_domain")   # 或从 my_domain/Condition、my_domain/Action 加载

node = make_condition("At(b,ab)", lib)  # 命中就用 At 类，否则退回默认语义
```

传给 `compile_tree(plan, lib)` 或 `solve(..., library=lib)` 即可生效。

目录约定：

```
my_domain/
├── Condition/At.py      class At(ConditionNode): ...
└── Action/Move.py       class Move(ActionNode): ...
```

## 常见坑

| 现象 | 原因 |
| --- | --- |
| 条件永远不成立 | 节点名与状态里的文字拼写不一致（文字统一用字符串！） |
| 卡在旧分支不换路 | 控制节点带了 `memory=True`（本项目已固定为 False） |
| `RuntimeError: 还没有绑定环境` | 忘了 `bt.bind_env(env)` |
| 动作没生效 | `env` 里没有同名动作，检查 `Action.name` 与节点名 |
| 一个 tick 把整串动作做完了 | 正常：默认动作是"一步到位"；要分步就返回 `RUNNING` |

完整可运行例子见 `examples/04_custom_domain.py`（自定义条件 + 两拍动作 + 行为库）。

## 下一步

- PDDL 接入 → [04-pddl.md](04-pddl.md)
- 术语 → [05-glossary.md](05-glossary.md)
