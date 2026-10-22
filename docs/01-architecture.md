# 01 · 架构

> 一句话：**规划算结构，IR 存结构，编译换语言，py_trees 负责跑。**

## 四层

| 层 | 包 | 职责 | 依赖 py_trees |
| --- | --- | --- | --- |
| ① 规划内核 | `btplan.core` | 纯符号反向扩展，产出 IR 树 | 否 |
| ② 中间表示 | `btplan.ir` | 树形数据结构 + PTML 序列化 | 否 |
| ③ 运行时 | `btplan.runtime` | py_trees 节点、行为库、编译器 | 是 |
| ④ 环境 | `btplan.env` | 持有状态、执行动作、tick 循环 | 是（驱动） |

外加两个辅助包：`btplan.domains`（示例问题）、`btplan.pipeline`（`solve()` 一键流水线）。

## 数据流

```
start / goal / actions
        │
        │  Planner.plan()            纯集合运算，反向扩展
        ▼
   IR 树（BTNode）──► to_ptml()      打印 / 存档 / 测试快照
        │
        │  compile_tree()            查行为库，造 py_trees 节点
        ▼
   py_trees 树 ──► BehaviorTree.bind_env(env)
        │
        │  run() → bt.tick()         每个 tick 由 py_trees 决定走哪条分支
        ▼
   成功 / 失败 / 超时
```

## 各层入口

| 想做的事 | 入口 |
| --- | --- |
| 规划一棵树 | `Planner().plan(start, goal, actions) -> BTNode` |
| 导出/查看 | `to_ptml(tree)`、`tree.print_tree()` |
| 编译成可执行树 | `compile_tree(tree, library=None) -> py_trees.behaviour.Behaviour` |
| 绑定环境 | `BehaviorTree(root)` + `bt.bind_env(env)` |
| 跑起来 | `run(bt, env, goal=..., max_ticks=...)` |
| 一行搞定 | `solve(start, goal, actions)` |

## 五条关键约定

1. **规划期不碰 py_trees。**
   算法只在 `frozenset` 上做集合运算。py_trees 节点带父子指针、内存状态、visitor，
   在它上面做"复制结点 / 替换子树 / 求子集"既慢又脆。

2. **IR 是单向的。**
   只允许 `IR → py_trees`、`IR → PTML`。**不要**从 PTML 文本反解析回树
   （那会把文本格式变成隐式接口，一改就碎）。PTML 只是产物，不是真值来源。

3. **控制节点固定 `memory=False`。**
   BT Expansion 的 soundness / completeness 建立在"每个 tick 都从根重新评估"之上。
   带 memory 的选择节点会锁死在旧分支上，失去响应式能力。这个参数不对外开放。

4. **状态只在环境里。**
   节点通过 `bind_env` 持有环境引用，`update()` 读 `env.observe()`、写 `env.apply()`，
   自身**不缓存状态**。同一棵树换个环境就能复用。

5. **文字统一用字符串。**
   状态里的文字（`At(b,ab)`）就是条件节点的名字。用数字等非字符串会导致
   规划出的条件和运行时节点对不上。

## 我该改哪一层？

| 需求 | 改哪里 |
| --- | --- |
| 换搜索策略（最优 / 带启发） | `core/planner.py` |
| 加剪枝规则、冲突检测 | `core/expander.py`、`Planner(conflict_check=...)` |
| 换输出格式（新的序列化） | `ir/serialize.py` |
| 接真实机器人 / 模拟器 | 继承 `runtime/nodes.py` 里的 `ConditionNode` / `ActionNode`，写进行为库 |
| 改"状态怎么存 / 动作怎么生效" | `env/symbolic.py` |
| 改 tick 循环的终止判据 | `env/runner.py` |

## 测试怎么分层

| 测试文件 | 覆盖 |
| --- | --- |
| `tests/test_runtime.py` | 节点语义、tick 循环、RUNNING、失败分支 |
| `tests/test_planner.py` | 树结构、可执行性、不可达报错、PTML |
| `tests/test_pddl.py` | PDDL 样例端到端 |

## 下一步读什么

- 算法细节 → [02-planning.md](02-planning.md)
- 运行时细节 → [03-runtime.md](03-runtime.md)
- 术语 → [05-glossary.md](05-glossary.md)
