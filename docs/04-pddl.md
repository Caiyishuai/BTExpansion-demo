# 04 · PDDL 前端

> 对应代码：`src/btplan/pddl/`
> 示例：`examples/03_pddl.py`

## 用法

```python
from btplan.pddl import solve_pddl, default_sample

domain, problem = default_sample("movebtob")   # 仓库自带样例
res = solve_pddl(domain, problem)

print(res.report.format())   # 兼容性诊断
print(res.ptml)              # 行为树（PTML 文本）
print(res.summary())         # 执行结果
```

用自己的 PDDL：

```python
res = solve_pddl("my/domain.pddl", "my/problem.pddl")
```

只想自己控制规划细节（比如换 Planner 参数）：

```python
from btplan.pddl import load_pddl
goal, start, actions, report = load_pddl("domain.pddl", "problem.pddl")
# 之后就是普通流程：Planner().plan(start, goal, actions) → compile_tree → run
```

## 流程

```
domain.pddl + problem.pddl
        │
        │  parser.py      解析成 Domain / Problem（s-expression）
        ▼
   兼容性判定  compat.py    这个 domain 能不能保证 Sound/Complete？
        │
        │  grounding.py   grounding：谓词 → 文字、动作模板 → 具体动作，
        │                 同时做负前提编码、静态谓词剪枝、条件效果编译
        ▼
   goal / start / actions（都是字符串文字 + btplan.Action）
        │
        │  Planner → compile_tree → run
        ▼
   行为树 + 执行结果
```

## 兼容性报告

`res.report.format()` 会给出三种判定之一：

| 判定 | 含义 | 默认行为 |
| --- | --- | --- |
| `SUPPORTED` | 可直接转换，保持 Sound + Complete | 正常求解 |
| `REWRITABLE` | 需要改写（如条件效果），改写后仍有保证 | 正常求解（已自动改写） |
| `UNSUPPORTED` | 有阻断项（如量化、函数、数值），无法保证 | `strict=True` 时中止 |

要强行尝试 `UNSUPPORTED`（结果**没有** Sound/Complete 保证）：

```python
res = solve_pddl(domain, problem, strict=False)
```

准入规则与具体例子见仓库的 [`pddl/ADMISSIBILITY.md`](../pddl/ADMISSIBILITY.md)。

## grounding 做了什么

1. **实例化**：按类型闭包把动作模板展开成具体动作
   （`move(?x,?y)` → `move-b-to-ab`）。
2. **负前提编码**：PDDL 的 `(not (at b ab))` 在 STRIPS 里没法直接表示，
   用补谓词编码成 `not-at-b-ab` 这样的文字。
3. **静态谓词剪枝**：从不出现在任何效果里的谓词（如 `(connected a b)`）
   在 grounding 期直接求值，剪掉永不可执行的动作实例——这是大问题上的关键优化。
4. **条件效果编译**：`(when C (p))` 展开成无条件效果（配合前提拆分）。

输出统一为**字符串文字**（`at-b-ab`、`free-ab`），正好是运行时条件节点的名字，
所以 PDDL 场景**不需要手写任何节点类**——默认语义（"文字是否在状态里"）即可。

## 仓库自带的样例

| 目录 | 演示什么 |
| --- | --- |
| `pddl/minimal` | 最小可用 domain |
| `pddl/movebtob` | 经典搬运问题（与 `domains.MoveBtoB` 同构） |
| `pddl/neg_precond` | 负前提 |
| `pddl/static_prune` | 静态谓词剪枝 |
| `pddl/cond_effects` | 条件效果 |
| `pddl/robot_fetch` | 较完整的机器人取物 |
| `pddl/unsupported` | 含阻断项（用于看诊断长什么样） |

跑全部样例的测试：`python tests/test_pddl.py`。

## 已知限制

- 量化目标（`:exists` / `:forall`）会被丢弃，可能导致 grounding 后目标为空
  （`unsupported` 样例就是这样，会返回"目标为空，无需规划"）。
- 不支持数值/函数（`:functions`）、时序、偏好等扩展。
- grounding 是**全量**展开，动作数随对象数爆炸；大 domain 要靠静态剪枝 + 类型约束控制规模。

## 排错

| 现象 | 处理 |
| --- | --- |
| "该 PDDL 含有阻断项…" | 看 `res.report.format()` 的具体条目；确认无误后 `strict=False` |
| "目标为空，无需规划" | 检查 `:goal` 是否用了量化 |
| 动作数巨大、规划很慢 | 用类型约束收紧参数；确认静态谓词被正确识别 |
| 生成的树跑不通 | 用 `verbose=True` 看规划过程；检查 `del_set` 是否漏了文字 |

## 下一步

- 术语 → [05-glossary.md](05-glossary.md)
- 架构总览 → [01-architecture.md](01-architecture.md)
