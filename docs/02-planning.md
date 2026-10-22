# 02 · 规划层（算法）

> 对应代码：`src/btplan/core/`

## 问题是什么

- **状态**：一组为真的**文字**（字符串）组成的集合，如 `{"Free(ab)", "At(b,pb)"}`。
- **动作**：`Action(name, pre, add, del_set, cost)`。执行后状态变成
  `(state - del_set) | add`，前提是 `pre ⊆ state`。
- **目标**：一组文字，要求全部成立。
- **要什么**：一棵行为树，从 `start` 反复 tick 后能让 `goal` 成立，
  而且**中途条件被外界改变也能继续跑**（响应式）。

## 反向扩展：三条判据

算法从目标出发往回问："要让条件 `c` 成立，可以先做什么？" 答案在
`core/expander.py`：

**① 这个动作能产出 `c` 吗？**（`is_consequence`）

```python
c & ((action.pre | action.add) - action.del_set) != 空    # 确实碰到了 c
(c - action.del_set) == c                                 # 不会把 c 里的文字删掉
```

**② 做了它之后，之前必须先成立什么？**（`premise_of`）

```python
c_attr = (action.pre | c) - action.add
```

即"动作的前提 + 还没达成的那部分目标"。例如目标是 `At(b,ab)`，
动作 `Move(b,ab)` 的前提是 `{Free(ab), WayClear}`，那新前提就是
`{Free(ab), WayClear}`（`At(b,ab)` 被 `add` 减掉了）。

**③ 这条路要不要剪掉？**（`has_no_subset`）

若已扩展过的条件里有 `c_attr` 的子集，说明更宽的条件已经覆盖过这条路，
再扩展只会长出冗余分支。

## 主循环

`core/planner.py` 的 `Planner.plan()`，伪代码：

```
树 = 条件结点(goal)
while 树还不能从 start 跑起来:                 # core/evaluate.py: can_run()
    挑一个还没扩展过的条件结点 c               # 按长出顺序，广度优先
    if c != goal 且 c ⊆ start: break           # 已被初始状态满足，不用再扩展
    for 每个"能产出 c"的动作 a:                # expandable_actions()
        挂一条分支：sequence{ cond c_attr, act a }
    把 c 这个结点原地"长成"：selector{ cond c, 上面那些分支 }
    （新长出的 c_attr 结点留着以后继续扩展）
```

关键点：**每个 selector 都保留了"原条件已经成立"这一分支**。这就是树能响应
外界变化的原因——它不是一个固定动作序列，而是"每拍都重新判断该走哪条路"。

`MoveBtoB` 的结果（`python examples/02_plan_and_run.py` 可看到）：

```
selector
    cond At(b,ab)                      目标已达成？那就什么都不做
    sequence
        selector
            cond Free(ab) & WayClear   条件已满足？直接搬
            sequence
                cond Free(ab) & Free(as)
                act Move(s,as)         否则先把 s 挪开
        act Move(b,ab)
```

## 终止条件

| 情况 | 行为 |
| --- | --- |
| 树能从 `start` 跑起来 | 正常返回 |
| 目标本来就被 `start` 满足 | 不做任何扩展，返回单点树 |
| 所有条件都扩展完仍跑不起来 | 抛 `PlanningFailure`（目标不可达） |

`can_run()`（`core/evaluate.py`）是**纯符号求值**，不构造 py_trees、也不改状态：

| 节点 | 求值 |
| --- | --- |
| condition | 文字 ⊆ 状态 → `success` |
| action | 前提 ⊆ 状态 → `running`（一次 tick 只是"开始做"） |
| selector | 任一孩子可行 → 可行 |
| sequence | 全部孩子可行 → 可行 |

## 代价（cost）

当前实现**在规划期不看代价**：扩展顺序就是动作列表的顺序（FIFO），
`cost` 只在运行时累计（`RunResult.cost`）。

想要"优先扩展便宜动作"，改 `core/planner.py`：把待扩展条件改成按累计代价排序的
优先队列（MRBTP 论文里的 MAOBTP 就是这么做的），`Action.cost` 已经就绪。

## 冲突检测

有些前提符号上成立、物理上不可能（比如"同时拿着咖啡和饮料"、"同一物体在两个房间"）。
用 `conflict_check` 注入：

```python
def conflict(premise) -> bool:      # 返回 True 表示这个前提不成立
    return "Holding(Coffee)" in premise and "Holding(Softdrink)" in premise

Planner(conflict_check=conflict).plan(start, goal, actions)
```

规则怎么写取决于领域：常见做法是维护"互斥组"（同一主体在同一谓词下只能有一个值），
见 [05-glossary.md](05-glossary.md) 的"冲突检测"。

## 规模提示

- 每轮扩展会遍历**全部动作**，动作数 × 条件数增长很快；grounding 后的动作集合通常很大。
- 规划期每轮都跑一次 `can_run()`（对整棵树求值），树越大越慢。
- 真要上规模，优先做：`has_no_subset` 之外的更强剪枝、按代价排序的扩展顺序、超时上限。

## 下一步

- 运行时怎么跑起来 → [03-runtime.md](03-runtime.md)
