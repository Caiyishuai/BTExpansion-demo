# btplan

> 行为树扩展规划（BT Expansion）：给定初始状态、目标和可用动作，自动生成一棵**能达成目标的行为树**，并由 **py_trees** 驱动执行。

核心思路：**规划不碰 py_trees，执行才用 py_trees。**

---

## 30 秒跑通

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .                 # 依赖只有 py_trees（统一写在 pyproject.toml）
# 想画树图：pip install -e ".[draw]"（还需系统安装 graphviz）
# 想跑测试：pip install -e ".[dev]"

python examples/01_hello_bt.py   # 手写一棵树，看它怎么被 tick 驱动
python examples/02_plan_and_run.py  # 规划 → 编译 → 运行（最核心一集）
```

> 也可以用系统 Python 直接跑（示例会自动把 `src/` 加入模块路径），
> 但需要先 `pip install py_trees~=2.2.3`。

---

## 最小示例

```python
from btplan import Action, solve

actions = [
    Action("Move(b,ab)",
           pre={"Free(ab)"},                    # 前提：ab 位置空着
           add={"At(b,ab)"},                    # 做完：b 在 ab
           del_set={"Free(ab)", "At(b,pb)"}),   # 做完：ab 不空了、b 不在 pb
]

result = solve(start={"Free(ab)", "At(b,pb)"}, goal={"At(b,ab)"}, actions=actions)
print(result.summary())
# 成功=True  状态=SUCCESS  tick=1  代价=1.0  动作=['Move(b,ab)']
```

`solve()` 内部走完四步。想改其中任何一步，就自己拼：

```python
from btplan import Planner, SymbolicEnv, BehaviorTree, compile_tree, run, to_ptml

plan = Planner().plan(start, goal, actions)   # ① 规划：产出 IR 树（纯数据）
print(to_ptml(plan))                          #    顺手导出 PTML 文本

env  = SymbolicEnv(start, actions)            # ② 环境：状态的唯一持有者
bt   = BehaviorTree(compile_tree(plan))       # ③ 编译：IR → py_trees
bt.bind_env(env)

result = run(bt, env, goal=goal)              # ④ 运行：py_trees 驱动 tick
```

---

## 数据流

```
start / goal / actions
        │
        ▼
  ① 规划  btplan.core.Planner      纯符号反向扩展，产出 IR 树（不碰 py_trees）
        │
        ▼
  ② IR   btplan.ir.BTNode ──► to_ptml()  打印 / 存档 / 测试快照
        │
        ▼
  ③ 编译 btplan.runtime.compile_tree()   IR → py_trees 节点
        │
        ▼
  ④ 运行 btplan.env.run()           py_trees 驱动 tick，直到成功 / 失败
```

一句话概括每一层：**规划算结构，IR 存结构，编译换语言，py_trees 负责跑。**

---

## 目录地图

```
src/btplan/
├── core/        规划内核：动作模型、扩展规则、符号求值、搜索主循环（纯符号）
│   ├── action.py      Action：name / pre / add / del_set / cost
│   ├── expander.py    三条扩展判据（算法的核心）
│   ├── evaluate.py    不执行，只判断"树能否从 start 跑起来"
│   └── planner.py     Planner：BT Expansion 主循环
├── ir/          中间表示：BTNode（纯数据）+ PTML 序列化
├── runtime/     py_trees 运行时
│   ├── nodes.py        ConditionNode / ActionNode / Sequence / Fallback / CompositeCondition
│   ├── compiler.py     IR → py_trees
│   ├── library.py      行为库（文字 → 节点类的映射）
│   └── tree.py         BehaviorTree：bind_env / tick / print_tree / draw
├── env/         环境：状态怎么存、动作怎么生效、tick 循环怎么跑
├── domains/     内置示例问题，拿来就能跑
├── pddl/        PDDL 前端：解析 / 兼容性判定 / grounding（可选进阶）
├── tools/       benchmark：随机问题批量验证
├── cli.py       命令行入口 `btplan plan|run|draw|bench`
└── pipeline.py  solve() 一键流水线

examples/   按编号顺序学：01 运行时 → 02 全流程 → 03 PDDL → 04 自定义 → 05 新任务
tests/      与四层一一对应的测试
docs/       分主题文档 + tutorial.html（图文交互教程）
```

---

## 学习路径

> 想先"看图 + 点着玩"？打开 **[docs/tutorial.html](docs/tutorial.html)**：
> 图文教程，含两个可交互 demo（逐 tick 执行、扩展过程分步演示），单文件离线可用。

| 顺序 | 文件 | 你会学到 |
| --- | --- | --- |
| 0 | `docs/tutorial.html` | 图文教程 + 交互 demo（推荐先看） |
| 1 | `examples/01_hello_bt.py` | 行为树运行时长什么样、tick 怎么推进任务、RUNNING 是什么 |
| 2 | `examples/02_plan_and_run.py` | 完整闭环：规划 → PTML → 编译 → py_trees 驱动 |
| 3 | `examples/03_pddl.py` | 直接吃 PDDL（domain + problem）生成行为树 |
| 4 | `examples/04_custom_domain.py` | 自定义 Condition / Action 节点 + 行为库（接真实机器人） |
| 5 | `examples/05_new_task.py` | 从零写一个新任务：设计文字 → start/goal → 动作 → 运行 → 画图 |
| 6 | `docs/01-architecture.md` | 四层架构、"我该改哪一层" |
| 7 | `docs/02-planning.md` | 算法细节：三条扩展判据、剪枝、终止条件 |
| 8 | `docs/03-runtime.md` | 怎么写自己的 Condition / Action 节点 |
| 9 | `docs/04-pddl.md` | 直接用 PDDL（domain + problem）生成行为树 |

跑测试：

```bash
python tests/test_runtime.py              # 运行时层
python tests/test_planner.py              # 规划层
python tests/test_pddl.py                 # PDDL 前端（跑仓库自带 7 个样例）
python tests/test_tools.py                # 随机问题生成器 + benchmark
python scripts/benchmark.py               # 随机问题批量验证（鲁棒性 / 性能）
```

---

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [docs/tutorial.html](docs/tutorial.html) | **图文交互教程**（含可交互 demo，浏览器直接打开） |
| [docs/01-architecture.md](docs/01-architecture.md) | 四层架构、数据流、关键设计约定 |
| [docs/02-planning.md](docs/02-planning.md) | 规划算法：扩展判据、剪枝、终止、可扩展点 |
| [docs/03-runtime.md](docs/03-runtime.md) | py_trees 运行时：节点语义、自定义节点、行为库 |
| [docs/04-pddl.md](docs/04-pddl.md) | PDDL 前端：domain + problem → 行为树 |
| [docs/05-glossary.md](docs/05-glossary.md) | 术语表 |

---

## 命令行

```bash
btplan plan  --domain MoveBtoB                 # 规划并打印 PTML
btplan plan  --domain MakeCoffee --out output  # 同时写入 output/MakeCoffee.ptml
btplan run   --domain MoveBtoB                 # 规划 + py_trees 执行
btplan run   --pddl pddl/movebtob/domain.pddl pddl/movebtob/problem.pddl
btplan draw  --domain MoveBtoB --out output    # 渲染成 Graphviz 图
btplan bench --problems 50                     # 随机问题批量验证
```

`--domain` 可用值见 `btplan/domains/problems.py`（`MoveBtoB`、`ServeCoffee`、`MakeCoffee`、
`SoftdrinkCost`、`Cond2BelongsToCond3`、`MoveBtoB_num`、`MakeCoffeeCost`、`Test`）。

---

## 引用

本项目的算法源自以下论文，若对你的研究有帮助请引用：

> Cai, Z., Li, M., Huang, W., & Yang, W. (2021). **BT Expansion: a Sound and Complete Algorithm for Behavior Planning of Intelligent Robots with Behavior Trees**. *Proceedings of the AAAI Conference on Artificial Intelligence*, *35*(7), 6058–6065. https://doi.org/10.1609/aaai.v35i7.16755

```bibtex
@article{cai2021bt,
  title     = {BT Expansion: a Sound and Complete Algorithm for Behavior Planning of Intelligent Robots with Behavior Trees},
  author    = {Cai, Zhongxuan and Li, Minglong and Huang, Wanrong and Yang, Wenjing},
  journal   = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume    = {35},
  number    = {7},
  pages     = {6058--6065},
  year      = {2021},
  doi       = {10.1609/aaai.v35i7.16755}
}
```

相关项目：

- **LLM-OBTEA**（原作者团队将大模型与行为树扩展结合的官方扩展）：<https://github.com/DIDS-EI/LLM-OBTEA>
