# 神经符号 × 机器人大模型：近年论文速查（2022–2026）

整理时间：2026-11-02。按「符号 ↔ 神经信息流方向」分类：

- **A 符号→神经**：用形式结构约束生成（约束解码、LTL 引导、SMT 校验）
- **B 神经→符号**：让大模型当建模者（写 PDDL、生成行为树、归纳动作语义）
- **C 双向闭环**：生成—验证—修复
- **D 架构内嵌**：符号层做进模型内部
- **E 评估与反证**：基准、消融、能耗

> 主结论：2025–2026 年范式已收敛为「LLM 做建模者与提议者，正确性交给确定性求解器，失败交给符号层做可解释修复」。

---

## A｜符号 → 神经

| 工作 | 出处 / 编号 | 要点 |
|---|---|---|
| SELP: Generating Safe and Efficient Task Plans for Robot Agents with LLMs | ICRA 2025 · arXiv:2409.19471 | 等价投票（多条 LTL 分组取多数）+ 约束解码 + 领域微调。无人机安全率 +10.8%、效率 +19.8%；操作任务安全率 +20.4% |
| SCLPlan: Constrained Natural Language Action Planning | arXiv:2510.06357 | LLM 生成 PDDL 目标态 → 求解器 → 失败转 ReAct → **前置条件验证 PV**。ALFWorld 99%，Spot 真机 100%（纯 LLM 50%、纯符号 30%）；PV 单项消融 +40%；每任务省约 2 万 token。结论「部分域就够了」 |
| Code-as-Symbolic-Planner | IROS 2025 · arXiv:2503.01700 | 让 LLM 现写 solver/planner/checker，而不是调 API。7 任务 × 3 LLM 平均 +24.1% |
| 视觉探索 + 约束符号规划的神经符号智能体 | 2026，VirtualHome / ALFWorld | VLM 获取目标相关谓词与实例绑定 → PDDL 转移模型限解码 + MCTS。4B–27B 模型成功率 >90%，token 更少（编号待核） |

## B｜神经 → 符号

| 工作 | 出处 / 编号 | 要点 |
|---|---|---|
| SayPlan | CoRL 2023 | 3D 场景图接地：层次语义搜索（expand/contract）+ Dijkstra 接管导航 + 场景图模拟器迭代重规划。3 层楼 / 36 房间 / 140 物体 |
| EmbodiedRAG | 2025 (JHU/ARL) | 把 RAG 搬到 3DSG，检索任务相关子图并随执行动态更新 |
| LLM-as-BT-Planner | arXiv:2409.10444 | 一步 / 迭代（模拟器反馈）/ 人机协作 / 递归（MakePlan→MakeTree→PredictState）四种生成策略；对小模型做 SFT |
| BT-ACTION | arXiv:2504.02779 | 测试驱动的 BT 生成，45 人用户研究：犯错更少、信任更高 |
| Interpretable Robot Control via Structured BTs and LLMs | arXiv:2508.09621 | 可解释 HRI，认知→执行准确率约 94% |
| **MRBTP** | **AAAI 2025 · arXiv:2502.18072** | 多机器人 BT 规划，可靠性与完备性理论保证；跨树扩展协调异质动作；LLM 插件预规划长程子树 |
| LLM-Constructed Hierarchical Trees（异构团队） | ICRA 2025 (Honda Research) | 受约束 API 构建 TAEMS 式层级树（AND/XOR/Precedence）+ 自底向上启发式 MRTA，带剪枝 ρ |
| LaMMA-P | ICRA 2025 · arXiv:2409.20560 | 六模块流水线（Precondition Identifier → Task Allocator → Problem Generator → Validator → Fast Downward/LLM → Sub-Plan Combiner）。MAT-THOR 基准；相对 SMART-LLM 成功率 +105%、效率 +36% |
| FLEET | arXiv:2510.07417 | LLM 出任务图 + 能力适配矩阵，MILP 解 makespan。消融：MILP 改善时序、LLM 适配度对能力耦合任务是决定性的 |
| PSALM-V | arXiv:2506.20097 | 不假设预定义问题文件/全可观/显式报错，从执行结果与错误解释中归纳 PDDL 语义，维护树状信念。ALFRED 37%→74% |
| Gideon | IAS 2025 · arXiv:2505.08492 | 本地 Qwen-2.5 1.5B（比基线小 120×）+ 通用数据生成器。单域 66.1%、多域 70.6% 合法计划率 |
| OntoAct | arXiv:2610.21983 (2026) | 本体抽象 → 公理；LLM 提假设、符号验证器核对证据。基准 Tacit-FLE（Factorio 隐藏故障诊断） |

## C｜双向闭环（2025–2026 最活跃）

| 工作 | 出处 / 编号 | 要点 |
|---|---|---|
| **VIRF** | **ICLR 2026 · arXiv:2602.08373** | 批评「LLM 监督 LLM」的自指循环。确定性 Logic Tutor 给 LLM Apprentice 因果式教学反馈，使其修复而非回避。HAR **0%**、GCR **77.3%**、平均 1.1 轮修正 |
| LogicGuard | arXiv:2507.03293 | LLM critic 用 LTL 约束屏蔽 actor 的未来不安全行为。Behavior-100: 47%→72%，失败动作 23%→4.5% |
| VerifyLLM | arXiv:2507.05118 | 执行前校验三类不一致：位置错误、遗漏前置条件、冗余动作。附 ALFRED-LTL / VirtualHome-LTL |
| SENTINEL | arXiv:2510.12985 | 三层：语义（NL→TL，92% 等价翻译）、计划（LTL，判定 35% 不安全）、轨迹（CTL，检出 87% 违规） |
| Kinodynamic TAMP (VLM 回溯) | arXiv:2510.26139 | 混合状态树统一符号态与数值态；运动规划器 + 物理仿真验证；失败时 VLM 看渲染图预测回溯节点。成功率 +32%~+1167%，双 UR5e 真机 n=3/4 → 100% |
| Meta-Optimization & Program Search for TAMP | CoRL 2025 · arXiv:2505.03725 | 把「轨迹优化问题的程序搜索」作为基础模型与控制的接口，零阶法优化数值参数 |

## D｜架构内嵌

| 工作 | 出处 / 编号 | 要点 |
|---|---|---|
| NS-VLA | arXiv:2603.09542 (2026) | 诊断 VLA 三病：结构盲、泛化被 backbone 绑定、扁平目标。Encoder（计划约束的 primitive 推理）+ Solver（骨干无关，以 primitive 为条件）+ 分层联合优化。**单调指针**跟踪 primitive 进度 |
| CoRAL | RSS 2026 | LLM 当「代价设计师」给 MPPI 生成目标函数；VLM 预估质量/摩擦，失败时外层 LLM 在线系统辨识。零样本复杂接触任务比 OpenVLA 平均 +50%；真机 Franka 零样本 |
| NeuroStrata | FSE 2025 IVR · arXiv:2502.12267 | 三层分层（纯符号 / 神经符号 / 神经符号）；LLM 做 Specification Mining。LASER 案例 Recall@10 53.98%（+30.55%），分布外仅掉 0.52% |
| NEUROSYMLAND | 2025 | 概率场景图 + Scallop 规则执行，UAV 着陆，强调可解释可验证 |
| 传统可微符号栈 | — | DeepProbLog、NSCL、∂ILP、LTN、Neural Logic Machines：仍有生命力，但增长点在于与基础模型结合 |

## E｜评估与反证（最值得读）

| 工作 | 出处 / 编号 | 要点 |
|---|---|---|
| **Can LLM-Reasoning Models Replace Classical Planning?** | arXiv:2507.23589 | **执行保真度**：Fast Downward 100%；GPT o1 80%、Claude 3.7 Thinking 60%、o3-mini 50%、Claude 3.7 45%、Gemini 2 Flash Thinking 35%、DeepSeek R1 30%、Llama 405B 15%。「计划看起来对」≠「能跑通」 |
| Systematic Study of LLMs for TAMP with PDDLStream | arXiv:2510.00182 | 16 种集成方式、4,950 问题、3 域。LLM 版成功率更低、更慢；**喂几何细节反而增加任务规划错误**；非推理型（更快）优于推理型，因为系统会纠错 |
| The Price Is Not Right | ICRA 2026 · arXiv:2602.19260 | 汉诺塔（起始位抖动 1cm）：3 块 NSM 95% vs E2E-VLA 34% vs PG-VLA 0%；**4 块（未训练）NSM 78% vs VLA 0%**；训练能耗 0.85 MJ/34min vs 68.5 MJ/1d16h（~80×）；示教 50 vs 300。**注意：任务高度结构化，是符号方法的舒适区** |
| PlanBench | NeurIPS 2023 D&B；o1 评估 TMLR 2025 | DeepSeek-R1：NL Blocksworld 99.1%，Mystery 43.3%，Randomized Mystery 25.8% —— 换名即崩 |

## 综述与基准

- **LLMs as Planning Formalizers**（ACL 2025 Findings, arXiv:2503.18971）—— 最契合当前范式：LLM 是规划建模者，不是规划器。
- **Neuro-Symbolic AI: Towards Improving the Reasoning Abilities of LLMs**（IJCAI 2025 Survey, arXiv:2508.13678）—— 三分法 taxonomy，附 GitHub 论文库。
- **Neuro-symbolic agentic AI**（Information Fusion, 2026）—— PRISMA 178 篇；元认知仅占 5%，被严重低估；机器人任务完成度 +23%。
- **多机器人任务规划：从符号分解到神经符号具身智能**（中文, DOI 10.13976/j.cnki.xk.2025.3873）—— LLM 规划需经 RL 值函数做物理可供性过滤；指出离散-连续「可行性鸿沟」。
- 基准：MAT-THOR（多机器人长程）、SafeAgentBench（安全）、ALFRED-LTL / VirtualHome-LTL、Tacit-FLE（隐藏故障诊断）。

## 六条趋势

1. LLM 从规划器 → 建模者/提议者（「直接吐动作序列」已被执行保真度、几何反噬、能耗三重证据证伪）。
2. 符号层从「拒绝」升级为「解释 + 修复」。
3. 纵向下探：任务层 → 运动/控制层（TAMP、动力学验证、代价函数、VLA 内部符号接口）。
4. 横向扩展：多机器人/异构团队成为主战场，LLM 的增量在「能力↔任务」语义匹配。
5. 小模型 + 合成数据 + 本地部署是工程落地线（Gideon、SCLPlan token 节省、能耗论证指向同一结论）。
6. 评估换轴：执行保真度、HAR、GCR、修正轮数、能耗、token、OOD 鲁棒性。只报成功率越来越难站住。

## 开放问题

Symbol Grounding（最大脆弱点）· 开放世界的域归纳 · 高维连续空间形式验证的可扩展性 · 可复现性 · 元认知（仅占 5%）。

## 对 BT + PDDL 方向的选题缺口

1. **LLM 生成 BT 的形式化保证** —— BT 有成熟语义与可靠性/完备性理论，可转 TL 公式或 SMT 约束做前置校验；「BT 比线性计划更适合形式化验证（反应式、带 fallback、可组合）」这个差异化卖点目前没人讲。
2. **失败驱动的 BT 局部修复** —— VIRF 的因果反馈搬到树结构，定位到具体条件节点，局部修复而非整体重规划。
3. **多机器人 + BT + 能力感知分配** —— MRBTP 的 LLM 插件 × FLEET 的适配矩阵 × MILP 时序；缺公开的长程 BT 基准。
4. **把执行保真度/能耗这套评估轴引进 BT 文献** —— 目前 BT+LLM 论文基本只报成功率。
5. **开放世界的 BT 条件归纳** —— BT 执行轨迹天然带 Success/Failure/Running 三值信号，比线性计划提供更丰富监督（PSALM-V 思路迁移）。

---

*注：arXiv 编号以检索来源标注为准；2026 年少数条目（CoRAL、OntoAct、The Price Is Not Right）来自会议/媒体与索引站点，正式引用前建议核对原文。*
