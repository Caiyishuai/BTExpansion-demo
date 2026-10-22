# 05 · 术语表

新人最容易卡在术语上，这张表按"从问题到执行"的顺序排列。

| 术语 | 含义 | 例子 |
| --- | --- | --- |
| **文字（literal）** | 表示一个事实的字符串 | `At(b,ab)`、`Free(ab)` |
| **状态（state）** | 当前为真的文字集合 | `{"Free(ab)", "At(b,pb)"}` |
| **动作（Action）** | `name / pre / add / del_set / cost` 四元组模型 | `Move(b,ab)` |
| **前提（pre）** | 动作执行前必须成立的文字 | `{Free(ab), WayClear}` |
| **效果（add / del_set）** | 执行后新增 / 删除的文字 | add `At(b,ab)` |
| **grounded 动作** | 参数已绑定的具体动作（与"带变量的动作模板"相对） | `Move(b,ab)` 而非 `Move(?x,?y)` |
| **目标（goal）** | 要求全部成立的一组文字（合取） | `{At(b,ab)}` |
| **条件结点 / 条件 `c`** | 算法反向扩展时被处理的那组文字 | `{Free(ab), WayClear}` |
| **扩展（expansion）** | 对条件 `c` 找出"能产出它的动作"，长出分支的过程 | — |
| **前提回推 `c_attr`** | `(pre ∪ c) - add`，执行动作前必须先成立的条件 | — |
| **剪枝（pruning）** | 已有更宽条件覆盖时不再扩展（`has_no_subset`） | — |
| **IR（中间表示）** | 规划产出的纯数据行为树 `BTNode` | `selector / sequence / condition / action` |
| **PTML** | IR 的文本序列化格式（存档 / 人看 / 快照测试） | `selector{ cond A act B }` |
| **编译（compile）** | IR → py_trees 节点 | `compile_tree()` |
| **行为库（BehaviorLibrary）** | 文字 → 节点类的映射表 | `{"Condition": {"At": At}}` |
| **tick** | py_trees 从根走一遍；每个节点执行一次 `update()` | — |
| **RUNNING** | 节点状态："在做，还没完"，下一拍继续 tick 它 | 导航、搬东西 |
| **Selector / Fallback** | 控制节点：第一个可行分支即可 | 本项目 `Fallback` |
| **Sequence** | 控制节点：全部孩子可行才可行 | — |
| **memory=False** | 每个 tick 从头重新评估（响应式语义的前提） | — |
| **响应式（reactive）** | 每拍重新判断，外界改变条件也能继续跑 | BT 相对"动作序列"的优势 |
| **冲突检测（conflict_check）** | 剪掉符号上成立、物理上不可能的前提 | "同时拿着咖啡和饮料" |
| **互斥组** | 同一主体在同一谓词下只能有一个取值，用来做冲突检测 | `IsNear(a,x)` 与 `IsNear(a,y)` 互斥 |
| **sound / complete** | 生成的树能达成目标 / 目标可达成时一定能生成树 | BT Expansion 论文结论 |

## 符号速查

| 符号 | 含义 |
| --- | --- |
| `c` | 当前被扩展的条件（文字集合） |
| `c_attr` | 由 `c` 和动作推出的新前提 |
| `pre / add / del_set` | 动作的前提 / 新增 / 删除 |
| `⊆` | 文字集合之间的包含判断（成立性判断的本质） |
