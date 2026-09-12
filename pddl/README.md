# PDDL → BT Expansion 适配器

把标准 **PDDL**（STRIPS 子集）直接喂给 [BT Expansion](../README.md) 算法，
自动生成**原生响应式**、且带 **Sound / Complete** 保证的行为树策略——**绕过传统规划器的解序列（plan）**。

> 这是 `feature/pddl-adapter` 分支新增的能力。**BT Expansion 算法内核一行未改**，
> 全部扩展都在一层「语义保持的编译」里：把 STRIPS 之上的若干构造编译回内核认识的
> grounded STRIPS，因此正确性保证是**继承**而非重新证明。

---

## 为什么要这一层

传统规划器（如 Fast Downward）输入 PDDL，输出一条 **grounded 动作序列** `a₁→a₂→…→aₙ`——
它只回答"从这个确定初始状态怎么一步步到目标"。而 BT Expansion 输出的是一棵
**策略树（policy）**：每个动作都带守卫条件，每次 tick 重新检查，环境变化能自动走另一分支。

本适配器走的是「转法 3」：**不要规划器的 plan，只借用它的输入（PDDL domain/problem）**，
直接调用 BT Expansion，得到原生响应式 + 带保证的策略树。

```
PDDL (domain + problem)
   │  parser.py          解析 S-表达式
   │  compat.py          兼容性判定：SUPPORTED / REWRITABLE / UNSUPPORTED
   │  grounding.py       lifted+typing grounding、负前提补谓词编码、静态谓词剪枝
   │  cond_effects.py    条件效果 (when C E) 编译为互斥动作分支
   ▼
grounded STRIPS: Action(pre, add, del_set, cost) 的集合
   │  run_algorithm_selTree   ← 原始 BT Expansion 内核（未改）
   ▼
响应式策略树（PTML）
```

---

## 快速开始

```bash
# 依赖：numpy tabulate py_trees antlr4-python3-runtime shortuuid
pip install -r ../requirements.txt

# 1. 先判定：这份 PDDL 能不能拿到 Sound/Complete 策略树
python ../scripts/pddl2bt.py --check movebtob/domain.pddl movebtob/problem.pddl
#   退出码 0 = 可转，1 = 有阻断项

# 2. 完整转换：grounding → 生成策略树 → 执行验证 → 导出 PTML
python ../scripts/pddl2bt.py robot_fetch/domain.pddl robot_fetch/problem.pddl \
       -o ../output --name robot_fetch
```

---

## 表达力：从「手写 STRIPS」扩展到了什么

| 构造 | PDDL 语法 | 处理方式 | 保 Sound/Complete？ |
| --- | --- | --- | --- |
| 基础 STRIPS | `:strips`，合取正文字 | 无需编译 | ✅ 原样保留 |
| 一阶提升 + 类型 | `:typing`，`(?x - T)` + `:types` | 按类型限定笛卡尔积后 grounding | ✅ 保留 |
| 动作代价 | `:action-costs`，`:cost n` | 写入 `Action.cost` | ✅ 保留 |
| 等词 | `:equality`，`(= ?x ?y)` | grounding 期静态求值 | ✅ 保留 |
| 静态谓词 | 从不出现在 `:effect` 的谓词 | grounding 期用 `:init` 求值并剪枝 | ✅ 保留 |
| 负前提 / 负目标 | `:negative-preconditions`，`(not (p …))` | 补谓词 `not-P` + 闭世界维护 | ✅ 改写后成立 |
| 条件效果（分支 add） | `:conditional-effects`，`(when C E)` | 拆成前提互斥且穷尽的动作分支 | ✅ 改写后成立 |
| 析取 / 量词 | `(or …)` / `forall` / `exists` | 理论可拆，**当前未自动实现** | ⚠️ 需人工改写 |
| 数值 / 时序 / 概率 | `:fluents` / `:durative-actions` / FOND | — | ❌ 模型层限制，拿不到 |

完整规则、每类构造的编译细节与代价、以及两条「合法 STRIPS 也会丢保证」的实现级陷阱
（`pre∩add≠∅`、`add∩del≠∅`），见 **[ADMISSIBILITY.md](ADMISSIBILITY.md)** 的总表（§0.5）。

---

## 亮点例子：条件效果 = 「分支 add」

`cond_effects/domain.pddl` 里的 `pick` 带两条条件效果：

```lisp
(:action pick
  :parameters (?i - item)
  :precondition (and (on-table ?i))
  :effect (and
    (holding ?i)
    (not (on-table ?i))
    (when (fragile ?i) (broken ?i))     ; 易碎 → 会摔坏
    (when (heavy ?i)   (tired))))       ; 太重 → 会累
```

适配器把它编译成 **4 个前提互斥、`add` 各不相同**的动作分支。当目标是
「拿到且不摔坏不累」时，算法会给出：

```
lighten(vase) → reinforce(vase) → pick(vase)[-fragile,-heavy]
```

**主动先消除 fragile 和 heavy，才走那个不产生副作用的分支**——这正是「看情况 add 不同东西」的正确语义。

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

---

## 验证（回归 13/13 PASS）

```bash
python ../scripts/verify_pddl_adapter.py    # 4/4  对拍 + lifted + 负前提 + 边界识别
python ../scripts/verify_reactivity.py      # 3/3  响应式：policy 而非 plan（抢走杯子会自愈）
python ../scripts/verify_cond_effects.py    # 3/3  条件效果编译的语义等价
python ../scripts/verify_static_pruning.py  # 3/3  静态剪枝规模收紧与解不变
```

最能体现价值的是响应式验证：同一棵树在 4 种不同初始状态下均达成目标
（目标已满足→0 步、已握杯→1 步、其他→3~4 步），执行中把杯子抢走会自动重做 `pick`。
这是「策略树」相对「plan 包 Sequence」的本质区别。

---

## 已知的上游问题（未改上游源码）

- `run_algorithm` 在 `len(goal) > 1` 时的多目标分支有缺陷（抛 `TypeError`，且语义上是析取而非合取）。
  适配器改为直接调 `run_algorithm_selTree(start, goal_set, actions)` 绕开。
- PTML 导出路径 `dfs_ptml_many_act` 会原地修改动作名（`r1`→`r`）。适配器统一走无副作用的导出方式。

两者均未改动 `src/bt_expansion/` 上游源码，以保持原实现可对照。
