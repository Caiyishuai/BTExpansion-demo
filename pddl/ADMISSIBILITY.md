# PDDL → BT Expansion 准入规则

本文回答一个问题：**什么样的 PDDL 输入能得到"原生响应式 + Sound/Complete 保证"的策略树，什么样的不能。**

结论均由 `src/pddl_adapter/compat.py` 实现为可执行检查，并由
`scripts/verify_pddl_adapter.py` 与 `scripts/verify_reactivity.py` 实证验证。

---

## 0. 判定速查

| 档位 | 含义 | 保证 |
| --- | --- | --- |
| `SUPPORTED` | 直接可转 | Sound + Complete 完整保留 |
| `REWRITABLE` | 需等价改写（适配器自动完成） | 改写后 Sound + Complete 仍成立，代价是状态空间放大 |
| `UNSUPPORTED` | 超出命题 STRIPS 模型 | **无法保证**，`strict` 模式下拒绝转换 |

命令行判定：

```bash
python scripts/pddl2bt.py --check domain.pddl problem.pddl
```

---

## 0.5 表达力扩展总表（一张表看全）

从原始 BT Expansion 只吃「手写 grounded STRIPS 动作」，本适配器把**输入建模语言**
扩展到下表所列的 PDDL 子集。核心思想：**内核一行未改，扩展全部通过「语义保持的
编译」还原回内核认识的 grounded STRIPS**，因此 Sound/Complete 是**继承**而非重证。

| 构造 | PDDL 语法 | 编译 / 处理方式 | 落到内核后的形态 | 保 Sound/Complete？ | 代价 | 样例 |
| --- | --- | --- | --- | --- | --- | --- |
| **基础 STRIPS** | `:strips`；`(and ...)` 正文字前提/效果/目标 | 无需编译 | 原生 `Action(pre,add,del)` | ✅ 原样保留 | 无 | `movebtob` |
| **一阶提升 + 类型** | `:typing`；`:parameters (?x - T)` + `:types` | 按类型继承链限定笛卡尔积后 grounding | 多条 grounded `Action` | ✅ 保留（命题空间不变） | grounding 组合数（受类型收紧） | `robot_fetch` |
| **动作代价** | `:action-costs`；`:cost n` | 直接写入 `Action.cost` | `Action.cost` | ✅（只影响代价统计，不影响可达） | 无 | `robot_fetch` |
| **等词** | `:equality`；`(= ?x ?y)` | grounding 期**静态求值**，决定实例去留，不进 `pre` | 更少的 grounded `Action` | ✅ 保留 | 无（反而减规模） | — |
| **静态谓词** | 从不出现在任何 `:effect` 的谓词，如 `(connected ?a ?b)` | grounding 期用 `:init` 求值：假则丢弃实例、真则移出 `pre` | 更少 `Action`、更精简守卫 | ✅ 保留（恒定真值，求值=运行时判定） | 无（大幅减规模） | `static_prune` |
| **负前提 / 负目标** | `:negative-preconditions`；`(not (p ...))` 出现在**前提或目标** | 引入补谓词 `not-P`，闭世界初始化，在所有增删 `P` 的动作里同步维护 | 全正文字的 `Action`（多出 `not-P`） | ✅ 改写后成立 | 状态空间放大（多出补谓词实例） | `neg_precond` |
| **条件效果（分支 add）** | `:conditional-effects`；`(when C E)` | 拆成前提**互斥且穷尽**的多个动作分支，`then` 加 `C`+`E`、`else` 加 `¬C` | 多条普通 `Action`，`add` 各不相同 | ✅ 改写后成立（穷举验证后继逐位一致） | 分支数 `∏(1+\|Cᵢ\|)` 指数增长；上限 `max_cases` 超限**抛错**不截断 | `cond_effects` |
| **析取前提** | `:disjunctive-preconditions`；`(or ...)` | 理论上可拆成多动作实例 | — | ⚠️ **理论可、适配器未实现** | 需人工改写 | `unsupported`(反例) |
| **析取目标** | `(or ...)` 目标 | 理论上每分支一棵树 + 顶层 Selector | — | ⚠️ **理论可、适配器未实现** | 需人工改写 | — |
| **量词前提** | `:universal-/:existential-preconditions`；`forall`/`exists` | 有限对象下可 grounding 期展开（∀→合取、∃→析取） | — | ⚠️ **理论可、适配器未实现** | 展开后仍受析取限制 | `unsupported`(反例) |
| **数值流** | `:fluents` / `:numeric-fluents`；数值比较/赋值 | — | ✗ 状态是命题集合，无数值维度 | ❌ 拿不到 | 需离散化或换数值规划器 | — |
| **时序动作** | `:durative-actions` / 连续效果 / 定时初值 | — | ✗ tick 是离散瞬时，无时间维度 | ❌ **无法改写** | 需时序规划器 | — |
| **推导谓词** | `:derived-predicates` | — | ✗ 无公理闭包机制 | ❌ 拿不到 | 层次有限时可手工展开 | — |
| **偏好 / 约束** | `:preferences` / `:constraints` | — | ✗ 算法只做可达性 | ❌ 拿不到 | 无 | — |
| **非确定 / 概率** | FOND / PPDDL | — | ✗ `state_transition` 确定性单后继 | ❌ 拿不到（目标语义不同，FOND 要强循环解） | 需 FOND/概率规划器 | — |

> 图例：✅ = `SUPPORTED`（直接保留）｜✅改写 = `REWRITABLE`（适配器自动改写，保证仍成立）｜
> ⚠️ = 理论上可编译但**当前适配器未自动实现**，需人工改写｜❌ = `UNSUPPORTED`（模型层限制，编译绕不开）。
>
> 另有两条**合法 STRIPS 也会丢保证**的实现级陷阱（不是语法问题），见 §3：
> `pre ∩ add ≠ ∅` 破坏 Completeness、`add ∩ del ≠ ∅` 语义歧义。检查器均会拦截。

---

## 1. 保证成立的充分条件（PDDL 白名单）

同时满足以下全部条件时，判定为 `SUPPORTED`，论文的 Sound + Complete 保证完整保留：

1. **requirements 只用** `:strips`、`:typing`、`:action-costs`
2. **前提是合取的正文字**：`:precondition` 形如 `(and (p ...) (q ...))`，不含 `or` / `not` / `imply` / 量词 / 数值比较
3. **效果是无条件的正负文字合取**：`:effect` 形如 `(and (p ...) (not (q ...)))`，不含 `when` / `forall` / 数值赋值
4. **目标是合取的正文字**：`:goal` 形如 `(and (g1) (g2))`
5. **每个动作 `pre ∩ add = ∅`**（见 §3.1，这是本项目实现的硬约束）
6. **每个动作 `add ∩ del = ∅`**（见 §3.2）
7. 有限对象集，grounding 规模可接受

对应样例：`pddl/movebtob/`、`pddl/robot_fetch/`

---

## 2. 需改写但保证仍成立（REWRITABLE）

### 2.1 负前提 / 负目标 —— `:negative-preconditions`

**为什么需要改写**：BT Expansion 的状态是「正文字字符串集合」，条件判定是
`c <= state`（集合包含）。集合里没有"某文字为假"的表示，因此 `(not (p))`
这种前提无法直接判定。

**改写方式（适配器自动完成）**：为谓词 `P` 引入补谓词 `not-P`，并且

- `:init` 中按闭世界假设初始化：所有未在 `:init` 出现的 `P` 实例，其 `not-P` 为真
- 所有 `add P` 的动作同时 `del not-P`
- 所有 `del P` 的动作同时 `add not-P`

改写后模型回到全正文字，集合包含判定正确，Sound/Complete 成立。

**代价**：状态空间放大。补谓词实例数 = 谓词的全部类型合法实例数，对象多时膨胀明显。

对应样例：`pddl/neg_precond/`，实测生成 `wash → dry-it → paint` 的正确计划。

> 注意：只有**前提或目标**里的负文字才需要编码。仅出现在效果里的 `(not ...)`
> 就是标准 `del_set`，无需任何改写。适配器已按此区分，避免无意义膨胀。

### 2.2 条件效果 —— `:conditional-effects`（即「分支 add」）

**问题本质**：`Action` 的 `add` / `del_set` 是**扁平的固定集合**，
执行语义 `new_state = (state | add) - del_set` 无条件并入 `add`，
因此无法直接表达「在 C1 成立时 add E1，在 C2 成立时 add E2」。

**改写方式（适配器自动完成）**：把一个带条件效果的动作
**拆成多个前提互斥的普通动作**。对含 n 条 `(when Ci Ei)` 的动作，
为每种"哪些条件成立"的组合生成一个实例：

```
a_case:  pre    = pre(a) ∪ {选中分支的 Ci} ∪ {未选中分支的 ¬Ci}
         effect = 无条件效果 ∪ {选中分支的 Ei}
```

这些实例的前提**两两互斥且穷尽所有情况**，因此与原动作语义等价。
BT Expansion 扩展时会自动挑选能达成目标的分支，并在必要时先把状态
引导到该分支的前提上（实测会主动规避有害分支）。

实例（`pddl/cond_effects/`）：`pick` 有两条条件效果
`(when (fragile ?i) (broken ?i))` 与 `(when (heavy ?i) (tired))`，编译出 4 个分支：

| 分支 | pre 追加 | add |
| --- | --- | --- |
| `pick(vase)[+fragile,+heavy]` | `fragile`, `heavy` | `holding`, `broken`, `tired` |
| `pick(vase)[+fragile,-heavy]` | `fragile`, `not-heavy` | `holding`, `broken` |
| `pick(vase)[-fragile,+heavy]` | `not-fragile`, `heavy` | `holding`, `tired` |
| `pick(vase)[-fragile,-heavy]` | `not-fragile`, `not-heavy` | `holding` |

目标为 `(and (holding vase) (not (broken vase)) (not (tired)))` 时，
算法给出 `lighten → reinforce → pick(vase)[-fragile,-heavy]` ——
**主动先消除 fragile 与 heavy，才走那个不产生副作用的分支**。

**两个注意点**：

1. **`¬C` 是析取**。`C` 通常是合取 `(and c1 c2)`，其否定
   `¬C = (or ¬c1 ¬c2)` 是析取，而 `pre` 必须是合取文字集合。
   处理方式：对 `C` 中每个文字各生成一个 else 实例，
   穷尽性由"每个析取子句一个实例"共同保证。
2. **条件 `C` 中的谓词一律需要补谓词编码**，因为 else 分支要表达 `¬C`。
   适配器自动处理。

**代价**：分支数 = `∏(1 + |Ci|)`，随条件效果个数**指数增长**，
再乘以参数 grounding 的组合数。`compile_conditional_effects` 设有
`max_cases=64` 上限，超限时**抛错而非静默截断**——
静默截断会破坏穷尽性，从而破坏 Completeness。

**额外风险**：编译后 then 分支的前提含 `C`，若 `C` 中原子同时出现在
效果的 `add` 里，就会触发 §3.1 的 `pre ∩ add` 丢解问题。
`compat.py` 对此有专门检查（`PRE_ADD_OVERLAP` on `when`）。

### 2.3 等词 —— `:equality`

`(= ?x ?y)` 不是状态里的可变命题。适配器在 **grounding 期静态求值**：
参数相等/不等直接决定该动作实例保留与否，不进入 `pre`。语义等价，无额外代价。

### 2.4 空效果动作

没有任何效果的动作永远不会被算法选中（不贡献目标文字），可安全删除。

---

## 3. 本项目实现特有的硬约束（易被忽略，但会破坏保证）

这两条不是 PDDL 语法问题，而是 BT Expansion **实现层面**的约束。
即便你的 PDDL 完全是合法 STRIPS，违反这两条也会丢掉保证。

### 3.1 `pre ∩ add ≠ ∅` → **破坏 Completeness（丢解）**

算法的回归公式（`src/bt_expansion/algorithm.py:91`）是

```python
c_attr = (actions[i].pre | c) - actions[i].add
```

若某原子**既是前提又是正效果**，它会被自己的 `add` 从 `c_attr` 中减掉，
导致生成的子树缺少这条必要守卫。

实测反例：

```
a:   pre={X,Y}  add={Y,G}    ->  c_attr = ({X,Y} ∪ {G}) - {Y,G} = {X}   ← Y 丢了
mkY: pre={}     add={Y}

start={X}, goal={G}
真实有解: mkY -> a   (｛X｝-mkY->｛X,Y｝-a->｛X,Y,G｝)
算法结果: 声称有解，但执行时 tick 返回 failure  ← 完备性被破坏
```

**改写建议**：把"执行前后都保持成立的前提"从 `add` 中移除——它本来就成立，无需再 `add`。

### 3.2 `add ∩ del ≠ ∅` → 语义歧义

`state_transition` 定义为 `(state | add) - del_set`，`del` 会覆盖 `add`。
同一原子同时出现在正负效果时，实际生效的是"删除"，这取决于实现细节而非 PDDL 语义。

`src/bt_expansion/examples.py` 的 `MoveBtoB()` 就存在这种写法，
`pddl/movebtob/domain.pddl` 按实际生效语义做了消歧还原（并在注释中说明）。

---

## 4. 无法保证的情形（UNSUPPORTED）

| PDDL 构造 | requirement | 为什么不行 | 可否绕过 |
| --- | --- | --- | --- |
| 析取前提 `(or ...)` | `:disjunctive-preconditions` | 前提必须是一个合取文字集合 | 可把每个析取分支拆成独立动作实例 |
| 析取目标 `(or ...)` | — | 目标必须是合取条件集合 | 可对每个分支各生成一棵树，再用顶层 Selector 合并 |
| 蕴含 `(imply a b)` | — | 同析取 | 先化为 `(or (not a) b)` 再拆 |
| 全称前提 `(forall ...)` | `:universal-preconditions` | 无量词展开机制 | 有限对象集下可 grounding 期展开为合取 |
| 存在前提 `(exists ...)` | `:existential-preconditions` | 展开后是析取 | 展开为析取后再拆动作 |
| 数值流 | `:fluents` / `:numeric-fluents` | 状态是命题集合，无数值维度；集合包含无法表达数值比较 | 离散化成命题，或改用数值规划器 |
| 时序动作 | `:durative-actions` | 模型无时间维度，tick 是离散瞬时的 | **无法改写**，需时序规划器 |
| 推导谓词 | `:derived-predicates` | 无公理闭包求解机制 | 推导层次有限时可手工展开 |
| 时间初值 | `:timed-initial-literals` | 同上无时间维度 | 无 |
| 偏好 / 约束 | `:preferences` / `:constraints` | 算法只做可达性，不做软约束优化 | 无 |
| ADL 全集 | `:adl` | 蕴含上述多项 | 逐项处理 |

此外，**非确定性 / 概率效果**（PPDDL、FOND）也不支持：`tick` 基于集合包含，
`state_transition` 是确定性单后继。FOND 需要的是"强循环解"，
这与 BT Expansion 的 Sound/Complete 定义不同。

---

## 5. 一个容易误解的点：Completeness 的适用范围

论文的 Complete 是指：**在给定的 grounded 动作集与命题状态空间内**，
若存在解则算法必能找到。它**不**意味着：

- 能补齐建模缺陷（动作集本身不足时仍然无解，此时返回 `Failure` 是正确行为）
- 能处理 grounding 期被类型约束排除掉的动作实例
- 最优性 —— BT Expansion 保证可达，不保证代价最优（最优版本见 OBTEA 系列）

---

## 5.5 控制 grounding 规模：两层「收紧」

**实践中最常见的瓶颈不是理论边界，而是 grounding 组合爆炸。**
一个 k 参数算子在 n 个对象上产出 `n^k` 个实例，收紧参数域的收益是指数级的。

### 第一层：`:types`（语法层，限定参数位候选对象）

grounding 时每个参数位只枚举该类型（及其子类型）的对象，
而不是全部对象。代码在 `grounding.py` 的
`objects_of_type(all_objects, t, closure)` 做这件事。

实测（`pddl/robot_fetch/`，3 个 location + 1 个 item）：

| | 动作数 | 说明 |
| --- | --- | --- |
| 有 `:types` | 15 | 参数位按类型限定 |
| 抹掉类型 | 44 | 多出 29 条垃圾，如 `move(cup,kitchen)`、`pick(kitchen,desk)` |

**做法**：给参数标类型；并把类型层次切细，别都塞进一个宽类型。

```lisp
(:types
  graspable fixed - object     ; 只有 graspable 能被 pick
  room surface - location)     ; 区分房间与台面
```

### 第二层：静态谓词（语义层，剪掉不可执行实例）

有些约束类型系统表达不了 —— 比如"两个房间是否连通"，
起点终点都是 `location`。这时用**静态谓词**：
从不出现在任何动作效果中的谓词，其真值由 `:init` 恒定。

适配器自动识别（`find_static_predicates`）并在 grounding 期求值：

- 前提中该静态原子在 `:init` 里为假 → **该动作实例永远不可执行，直接丢弃**
- 为真 → **从 `pre` 中移除**（恒真的守卫无需进入运行时判定，树更精简）

实测（`pddl/static_prune/`，6 个房间排成走廊，只有相邻连通）：

| | move 实例 | 规划结果 |
| --- | --- | --- |
| `prune_static=False` | 36（6×6 全展开） | **20s 超时**，树膨胀到 25000+ 结点 |
| `prune_static=True` | 10（恰为 5 段双向边） | **0.02s** 完成，树 488 结点，12 步达成 |

附带收益：`robot-fetch` 的树结点从 101 降到 71，
因为恒真的 `reachable(...)` 守卫被移出了 `pre`。

**用法**：把类型系统表达不了的约束写成静态谓词，放进前提即可：

```lisp
(:action move :parameters (?from ?to - location)
  :precondition (and (robot-at ?from) (connected ?from ?to)) ...)
```

只要 `connected` 不出现在任何 `:effect` 中，适配器就会自动识别并剪枝。

### 正确性

静态谓词真值恒定，因此"在 grounding 期求值"与"在运行时判定"等价：
被剪掉的实例在任何可达状态下都不可执行，保留的实例其静态前提恒真。
Sound/Complete 不受影响（`scripts/verify_static_pruning.py` 验证 C 已确认
剪枝前后计划完全一致）。

关闭剪枝：`ground(dom, prob, prune_static=False)`。

---

## 6. 实践工作流

```bash
# 1. 先判定，看清阻断项与改写项
python scripts/pddl2bt.py --check domain.pddl problem.pddl

# 2. 按诊断建议改写 PDDL（负前提等 REWRITABLE 项适配器会自动处理）

# 3. 完整转换并导出 PTML
python scripts/pddl2bt.py domain.pddl problem.pddl -o output --name mytree

# 4. 回归验证（对拍 + 边界识别 + 响应式 + 条件效果 + 规模收紧）
python scripts/verify_pddl_adapter.py
python scripts/verify_reactivity.py
python scripts/verify_cond_effects.py
python scripts/verify_static_pruning.py
```

---

## 7. 已验证的结论

`scripts/verify_pddl_adapter.py`（4/4 PASS）：

- PDDL 版 `MoveBtoB` 与 `examples.py` 手写版**逐动作语义等价**，
  且 plan / cost=4 / ticks=26 / tree_size=9 完全一致
- `robot-fetch`：3 条 lifted 模板 grounding 出 15 条动作，正确求解 4 步计划
- `neg_precond`：补谓词编码正确，生成 `wash → dry-it → paint`
- `unsupported` 样例的阻断项（析取 / 数值 / 量词 / pre∩add）**全部精确命中**

`scripts/verify_reactivity.py`（3/3 PASS）：

- **进度回退可自愈**：执行中把杯子抢走，树自动重做 `pick`，最终仍达成目标
- **目标白送会短路**：目标被提前满足时 1 步结束，不做多余动作
- **跨初始状态复用**：同一棵树在 4 种不同初始状态下均达成目标
  （目标已满足→0 步，已握杯→1 步，其他→3~4 步）

最后一条是转法 3 相对"plan 包 Sequence"的核心价值：得到的是 **policy 而非 plan**。

`scripts/verify_cond_effects.py`（3/3 PASS）—— 条件效果（分支 add）：

- **编译结构**：2 条 `(when ...)` 编译出 4 个分支，前提两两互斥、`add` 各不相同
- **规划规避有害分支**：目标要求"不摔坏不累"时，
  算法给出 `lighten → reinforce → pick(vase)[-fragile,-heavy]`
- **语义等价**：穷举所有 `pick` 可执行的初始状态，
  每个状态**恰好匹配 1 个分支**，且后继状态与 PDDL 原始 `(when C E)` 语义完全一致

`scripts/verify_static_pruning.py`（3/3 PASS）—— grounding 规模收紧：

- **`:types` 收紧**：`robot-fetch` 有类型 15 条 vs 抹掉类型 44 条（29 条垃圾实例）
- **静态谓词剪枝**：6 房间走廊，36 个 `move` 剪到 10 个；
  不剪枝时规划 20s 超时（树膨胀到 25000+ 结点），剪枝后 0.02s 完成
- **剪枝不改变解**：剪枝前后计划完全一致；不可达目的地的 `move` 实例被正确剪除

---

## 8. 已知的上游实现问题

`BTExpAlgorithm.run_algorithm` 在 `len(goal) > 1` 时的多目标分支存在缺陷：

1. 把 `for g in goal` 得到的**单个字符串**传给 `run_algorithm_selTree`，
   内部做 `c <= start` 集合运算时抛 `TypeError: '<=' not supported between
   instances of 'str' and 'set'`
2. 即使类型可用，"每个子目标各一棵树 + 顶层 Selector 合并"语义上是**析取**，
   对合取目标是错的

因此本适配器**直接调用 `run_algorithm_selTree(start, goal_set, actions)`**，
把整个目标集合作为一个合取条件传入——这与论文中"目标是一个条件集合 c"的设定一致，
实测可正确处理多文字合取目标（`robot-fetch` 的 `(and (item-at cup desk) (hand-empty))`
与双对象 `(and (painted cube) (painted ball))` 均正确求解）。

未修改上游源码，以保持原实现可对照。
