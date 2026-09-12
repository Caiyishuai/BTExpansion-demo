# PDDL → BT Expansion 适配器（使用指南）

把标准 **PDDL**（STRIPS 子集）直接喂给 BT Expansion 算法，自动生成**原生响应式**、
且带 **Sound / Complete** 保证的行为树策略——**绕过传统规划器的解序列（plan）**。

> **BT Expansion 算法内核一行未改**，全部扩展都在一层「语义保持的编译」里：
> 把 STRIPS 之上的若干构造（类型、负前提、条件效果…）编译回内核认识的 grounded STRIPS，
> 因此正确性保证是**继承**而非重新证明。

**给谁用**：你已经有一个 PDDL 领域模型（或愿意写一个），想要的不只是一条动作序列，
而是一棵能在环境变化时自愈的行为树。

---

## 目录

- [快速开始](#快速开始)
- [一、如何写动作模型](#一如何写动作模型)
- [二、语法注意事项（务必过一遍）](#二语法注意事项务必过一遍)
- [三、必须避免的写法](#三必须避免的写法)
- [四、如何生成并使用行为树](#四如何生成并使用行为树)
- [五、排错](#五排错)
- [表达力边界总表](#表达力边界总表)

---

## 快速开始

```bash
# 依赖
pip install -r ../requirements.txt   # numpy tabulate py_trees antlr4-python3-runtime shortuuid

# 1. 判定：这份 PDDL 能不能拿到 Sound/Complete 策略树（退出码 0=可转，1=有阻断项）
python ../scripts/pddl2bt.py --check robot_fetch/domain.pddl robot_fetch/problem.pddl

# 2. 完整转换：grounding → 生成策略树 → 执行验证 → 导出 PTML
python ../scripts/pddl2bt.py robot_fetch/domain.pddl robot_fetch/problem.pddl \
       -o ../output --name robot_fetch
```

---

## 一、如何写动作模型

### 1.1 最小可运行模板

下面这份 domain + problem **可以直接复制运行**（已实测通过，判定 `SUPPORTED`）。

**domain.pddl**

```lisp
(define (domain pick-and-place)
  (:requirements :strips :typing)

  (:types item location)                 ; 类型：用于收紧 grounding

  (:predicates
    (robot-at ?l - location)
    (item-at ?i - item ?l - location)
    (holding  ?i - item)
    (hand-empty)                         ; 0 元谓词直接写名字
  )

  (:action move
    :parameters (?from - location ?to - location)
    :precondition (and (robot-at ?from))
    :effect (and (robot-at ?to) (not (robot-at ?from)))
    :cost 2                              ; 自定义代价字段，见 1.2 节
  )

  (:action pick
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (item-at ?i ?l) (hand-empty))
    :effect (and (holding ?i) (not (item-at ?i ?l)) (not (hand-empty)))
    :cost 1
  )

  (:action place
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (holding ?i))
    :effect (and (item-at ?i ?l) (hand-empty) (not (holding ?i)))
    :cost 1
  )
)
```

**problem.pddl**

```lisp
(define (problem p1)
  (:domain pick-and-place)
  (:objects cup - item  kitchen desk - location)
  (:init (robot-at kitchen) (item-at cup kitchen) (hand-empty))
  (:goal (and (item-at cup desk)))       ; 合取目标
)
```

运行后得到：

```
判定: SUPPORTED
执行动作序列 : ['pick(cup,kitchen)', 'move(kitchen,desk)', 'place(cup,desk)']
累计代价     : 4.0        达成目标 : True
```

### 1.2 表达力扩展的写法

在基础 STRIPS 之上，本适配器额外支持以下写法。**每类都有对应的样例目录可对照。**

#### 类型与一阶提升 —— `:typing`

用带变量的参数模板代替逐条手写动作。类型会把每个参数位的候选对象限定为该类型，
显著减少 grounding 规模。

```lisp
(:types
  graspable fixed - object      ; 继承：graspable / fixed 都是 object 的子类型
  room surface - location)

(:action pick
  :parameters (?i - graspable ?l - location)   ; 只有 graspable 能代入
  ...)
```

实测：3 条 lifted 模板在 4 个对象上 grounding 出 15 条动作；若不标类型则 44 条
（多出 `move(cup,kitchen)` 这类无意义实例）。样例见 `robot_fetch/`。

#### 代价 —— 用 `:cost`（⚠️ 非标准字段）

```lisp
(:action move ... :cost 2)      ; ✅ 本适配器认这个
```

**注意**：这是本项目的**自定义扩展**，不是 PDDL 标准。省略 `:cost` 时默认为 1。

如果你照搬标准 PDDL 的 `:action-costs` 写法会被拒绝：

```lisp
:effect (and ... (increase (total-cost) 2))   ; ❌ 判为 UNSUPPORTED（数值流）
```

原因：状态是命题集合，没有数值维度。**代价只影响代价统计，不影响可达性**，
所以直接省略 `:cost` 也完全可以正常工作。

#### 负前提 / 负目标 —— `:negative-preconditions`

```lisp
(:action paint
  :parameters (?i - item)
  :precondition (and (not (dirty ?i)) (dry ?i))   ; 只能给"不脏"的物体上漆
  :effect (and (painted ?i)))
```

适配器**自动**为 `dirty` 引入补谓词 `not-dirty`：按闭世界假设初始化
（`:init` 里没出现的 `dirty(X)`，其 `not-dirty(X)` 为真），并在所有增删 `dirty`
的动作里同步维护。你不需要手工写补谓词。

> 只有**前提或目标**里的 `(not ...)` 需要编码。效果里的 `(not p)` 就是标准删除，无额外开销。

样例见 `neg_precond/`，实测生成 `wash → dry-it → paint`。

#### 条件效果「分支 add」 —— `:conditional-effects`

表达"在什么情况下 add 什么"：

```lisp
(:action pick
  :parameters (?i - item)
  :precondition (and (on-table ?i))
  :effect (and
    (holding ?i)
    (not (on-table ?i))
    (when (fragile ?i) (broken ?i))    ; 易碎 → 会摔坏
    (when (heavy ?i)   (tired))        ; 太重 → 会累
  ))
```

适配器把它编译成 **4 个前提互斥、`add` 各不相同的动作分支**：

| 分支 | pre 追加 | add |
| --- | --- | --- |
| `pick(vase)[+fragile,+heavy]` | `fragile`, `heavy` | `holding`, `broken`, `tired` |
| `pick(vase)[+fragile,-heavy]` | `fragile`, `not-heavy` | `holding`, `broken` |
| `pick(vase)[-fragile,+heavy]` | `not-fragile`, `heavy` | `holding`, `tired` |
| `pick(vase)[-fragile,-heavy]` | `not-fragile`, `not-heavy` | `holding` |

目标若是「拿到且不摔坏不累」，算法会给出 `lighten → reinforce → pick(vase)[-fragile,-heavy]`
——**主动先消除 fragile 和 heavy，才走那个不产生副作用的分支**。

`when` 的条件 `C` 可以是合取，其中的文字也可以是负的（会自动补谓词编码）。
**嵌套 `when` 不支持**。样例见 `cond_effects/`。

#### 静态谓词 —— 表达类型系统管不了的约束

"两个房间是否连通"这类约束，起点终点类型相同，`:types` 管不了。解决办法是写一个
**从不出现在任何 `:effect` 中的谓词**，适配器会自动识别它、并在 grounding 期用 `:init` 求值：

```lisp
(:action move
  :parameters (?from ?to - location)
  :precondition (and (robot-at ?from) (connected ?from ?to))  ; connected 是静态的
  ...)
```

- `(connected r1 r2)` 在 `:init` 里为假 → 该 `move` 实例**永远不可执行，直接丢弃**
- 为真 → 从 `pre` 中**移除**（恒真的守卫不必进入运行时判定，树更精简）

实测（6 房间走廊，只有相邻连通）：`move` 实例 36 → 10，规划从 **20 秒超时**变为 **0.02 秒**。
样例见 `static_prune/`。

#### 其他

| 构造 | 写法 | 说明 |
| --- | --- | --- |
| 等词 | `(:requirements :equality)` + `(= ?x ?y)` | grounding 期静态求值，不进 `pre` |
| 常量 | `(:constants red blue - color)` | 与 `:objects` 一样参与 grounding |
| 注释 | `; 这是行注释` | 支持 |

---

## 二、语法注意事项（务必过一遍）

| # | 注意点 | 说明 |
| --- | --- | --- |
| 1 | **标识符统一转小写** | 解析器把原子全部 lowercase，`(holding Cup)` 会变成 `holding(cup)`。命名请保持小写风格，避免与大写混用 |
| 2 | **变量必须以 `?` 开头** | `?i`、`?from`；对象名不要带 `?` |
| 3 | **`:cost` 是自定义字段** | 别用标准 `(increase (total-cost) ...)`，会被判为数值流 |
| 4 | **前提必须是合取** | `(and (p) (q))`。不能有 `or` / `imply` / `forall` / `exists` / 数值比较 |
| 5 | **目标必须是合取** | `(and (g1) (g2))`。析取目标不支持 |
| 6 | **效果是文字合取** | `(and (p) (not (q)))`。可以有 `when`，不能有 `forall`、数值赋值 |
| 7 | **`:predicates` 用 typed list** | `(item-at ?i - item ?l - location)` 的 arity 是 **2**（`- item` 不算参数） |
| 8 | **`(either a b)` 联合类型不支持** | 会被标记为 unsupported |
| 9 | **嵌套 `when` 不支持** | `(when C (when ...))` 无效 |
| 10 | **闭世界假设** | 与 PDDL 一致：`:init` 里没写的就是假 |
| 11 | **`?` 变量作用域** | 只在所属 `:action` 内有效；动作间不共享 |

---

## 三、必须避免的写法

这些**不是 PDDL 语法错误，但会让生成的树丢掉保证**，检查器会拦截并报出具体动作名。

| 问题 | 反例 | 后果 | 修法 |
| --- | --- | --- | --- |
| `pre ∩ add ≠ ∅` | `pre={X,Y}`, `add={Y,G}` | 回归公式会把 `Y` 减掉 → **丢解**（Completeness 被破坏） | 把"执行前后都成立"的前提从 `add` 中移除 |
| `add ∩ del ≠ ∅` | 同一原子同时出现在正负效果 | 语义取决于实现（del 覆盖 add） | 明确只保留其一 |
| 效果含 `or` / 量词 / 数值 | `(increase ...)`, `(forall ...)` | 判 `UNSUPPORTED` | 见 `ADMISSIBILITY.md` |
| 条件效果过多 | 6 条 `when`（每条 2 文字） | 分支数 `3^6=729`，超 `max_cases=64` 抛错 | 减少 `when`，或放宽上限 |
| 对象过多、类型过宽 | 20 对象 × 3 参数算子 | grounding `20³=8000` 条，可能超时/OOM | 用 `:types` 收紧 + 静态谓词剪枝 |

> 分支数超限时**抛错而非静默截断**——静默截断会破坏穷尽性，从而破坏 Completeness。

---

## 四、如何生成并使用行为树

### 4.1 命令行

```bash
# 只判定，不规划（退出码 0=可转 / 1=有阻断项）
python ../scripts/pddl2bt.py --check domain.pddl problem.pddl

# 完整转换，导出 PTML
python ../scripts/pddl2bt.py domain.pddl problem.pddl -o ../output --name mytree

# 打印算法扩展过程（调试用）
python ../scripts/pddl2bt.py domain.pddl problem.pddl -v

# 存在阻断项时仍强行尝试（放弃 Sound/Complete 保证）
python ../scripts/pddl2bt.py domain.pddl problem.pddl --no-strict
```

退出码：`0` 成功 / `1` 判定为不可转 / `2` 规划失败或执行未达目标。

### 4.2 Python API

```python
import sys, os
# PROJECT_ROOT 换成你本地的仓库根目录
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
from pddl_adapter import solve_pddl

res = solve_pddl('domain.pddl', 'problem.pddl', output_dir='output')

print(res.report.verdict)      # 'SUPPORTED' / 'REWRITABLE' / 'UNSUPPORTED'
print(res.grounding.stats)     # 对象数、grounded 动作数、剪枝数…
print(res.plan)                # 实际执行序列 ['pick(cup,kitchen)', ...]
print(res.cost, res.ticks)     # 累计代价、tick 次数
print(res.reached_goal)        # 是否达成目标
print(res.ptml)                # 策略树（PTML 文本）
```

也可以用更底层的方式，自己控制每一层：

```python
from pddl_adapter import load_domain, load_problem, ground, check
from bt_expansion.algorithm import BTExpAlgorithm

dom, prob = load_domain('domain.pddl'), load_problem('problem.pddl')
print(check(dom, prob).format())                    # 先看判定报告

g = ground(dom, prob)                               # 可传 prune_static=False 关闭剪枝
goal, start, actions = g.as_tuple()

algo = BTExpAlgorithm(verbose=False)
algo.clear()
bt = algo.run_algorithm_selTree(start, goal, actions)   # 返回 False 表示无解
```

### 4.3 接到真实机器人（关键：这是响应式策略，不是一次性 plan）

生成的是一棵**策略树**，每次 tick 都重新检查条件。因此执行循环里
**必须用真实感知更新 state，而不是用模型推演**：

```python
from bt_expansion.planning import state_transition

state = observe_state()          # 你的感知模块，返回一组命题字符串
val, obj = bt.tick(state)

while val not in ('success', 'failure'):
    execute(obj)                 # 在真实世界执行该动作（obj.name 即动作名）
    state = observe_state()      # 重新感知 —— 不要沿用状态转移
    val, obj = bt.tick(state)

if val == 'success':
    ...  # 目标达成
```

这样做的好处已被实证（`scripts/verify_reactivity.py`）：

- **进度回退可自愈**：执行中把杯子"抢走"，树会自动重做 `pick`
- **目标白送会短路**：目标被提前满足时立即返回 success，不做多余动作
- **跨初始状态复用**：同一棵树在 4 种不同初始状态下均达成目标（0/1/3/4 步）

若只是离线规划（无真实感知），用 `state_transition(state, obj)` 推演即可。

---

## 五、排错

| 现象 | 原因与处理 |
| --- | --- |
| 判定 `UNSUPPORTED` | 看输出里的「阻断项」，每条都给出了位置和修法建议。常见是数值流、时序、析取、量词 |
| 判定 `REWRITABLE` 但有告警 | 可以转换，保证仍成立；但注意状态空间放大（`negated_predicates`）或分支膨胀（`cond_effect_instances`） |
| 算法返回 `Failure` | 在完备性保证下即为**真无解**。通常是动作集建模不足（缺动作或前提写错），而不是算法问题 |
| 规划很慢 / 卡住 | grounding 爆炸。加 `:types`、把拓扑/能力约束写成静态谓词；`--check` 会打印 grounded 动作数 |
| 动作名变成 `move(r,r)` | 已修复（上游 PTML 导出的副作用），若遇到请更新到本分支 |
| 合取目标报错 | 上游 `run_algorithm` 多目标分支有缺陷，适配器已绕开；请走 `solve_pddl` 或 `run_algorithm_selTree` |

---

## 表达力边界总表

每类构造的**语法 / 编译方式 / 是否保 Sound+Complete / 代价 / 样例**，
见 **[ADMISSIBILITY.md](ADMISSIBILITY.md) §0.5 表达力扩展总表**。

要点速记：

- ✅ **原样保留**：`:strips`、`:typing`、`:action-costs`（仅声明）、`:equality`、静态谓词
- ✅ **自动改写后成立**：负前提 / 负目标、条件效果 `(when C E)`
- ⚠️ **理论可、适配器未自动实现**：析取前提/目标、量词（需人工改写）
- ❌ **模型层限制，拿不到**：数值流、时序动作、推导谓词、偏好/约束、非确定/概率效果

---

## 例子目录

| 目录 | 演示的能力 |
| --- | --- |
| `movebtob/` | 与 `src/bt_expansion/examples.py` 手写版**逐动作语义等价**的对拍基准 |
| `robot_fetch/` | lifted + `:types`：3 条算子模板 grounding 出多条动作 |
| `neg_precond/` | 负前提的补谓词编码：生成 `wash → dry-it → paint` |
| `cond_effects/` | 条件效果（分支 add）编译 |
| `static_prune/` | 静态谓词剪枝：6 房间走廊，`move` 实例 36→10，超时→0.02s |
| `unsupported/` | 反例集：析取 / 数值 / 量词等阻断项，验证检查器能精确拒绝 |

## 验证（回归 13/13 PASS）

```bash
python ../scripts/verify_pddl_adapter.py    # 4/4  对拍 + lifted + 负前提 + 边界识别
python ../scripts/verify_reactivity.py      # 3/3  响应式：policy 而非 plan
python ../scripts/verify_cond_effects.py    # 3/3  条件效果编译的语义等价
python ../scripts/verify_static_pruning.py  # 3/3  静态剪枝规模收紧与解不变
```

## 已知的上游问题（未改上游源码）

- `run_algorithm` 在 `len(goal) > 1` 时的多目标分支有缺陷（抛 `TypeError`，且语义上是析取而非合取）。
  适配器直接调 `run_algorithm_selTree(start, goal_set, actions)` 绕开。
- PTML 导出路径 `dfs_ptml_many_act` 会原地修改动作名（`r1`→`r`）。适配器统一走无副作用的导出方式。

两者均未改动 `src/bt_expansion/` 上游源码，以保持原实现可对照。
