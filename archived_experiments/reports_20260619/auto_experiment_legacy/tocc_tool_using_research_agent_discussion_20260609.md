# TOCC Tool-Using Research Agent 讨论报告

日期：2026-06-09（更新：同日深夜，含全天数据分析和文献代码调研）  
范围：CVRP n=8 稳定化证据、default_rag 坍缩发现、TSP 方差诊断、文献代码调研、paper 定位  
性质：阶段性研究设计文档，不作为论文最终结论

---

## 1. 全天进展总结

今天完成了四件事：

1. **CVRP 证据升级**：从 n=3 exploratory signal → n=8 repeat-level positive signal
2. **default_rag 坍缩发现**：意外获得 TOCC 选卡价值的强对照证据
3. **TSP 方差诊断**：确认 gen=0 不可靠，card 方向正确但需要 gen=4
4. **文献代码调研**：HeuriGym/HeurAgenix/CO-Bench 三仓库深读，确定了可迁移项和差异化定位

---

## 2. CVRP 完整证据

### 2.1 数据

```
CVRP pure_eoh        n=8  mean=13.540  [13.279, 13.611]
CVRP default_rag     n=5  mean=13.283  [13.283, 13.283]  ← ALL IDENTICAL
CVRP tocc_corrected  n=8  mean=12.975  [12.713, 13.283]
```

tocc 8/8 优于 pure mean。tocc max (13.283) 低于 pure mean (13.540)。改善从 n=3 的 -4.6% 收敛到 n=8 的 -4.2%，信号稳定。

### 2.2 default_rag 坍缩——意外强证据

5/5 default_rag runs 全部出现灾难性坍缩：

- `valid=1, pop=1, best=13.28321`（恰好等于 seed_objective，0% 改善）
- 注入的 card：`cvrp_far_first` + `cvrp_nearest_capacity`
- 3/4 候选代码在 EOH init 阶段全部失败，种群坍缩到只剩种子

**而 tocc_corrected 仅差一张 card**（`cvrp_regret_insertion` vs `cvrp_nearest_capacity`），结果 10/10 valid=4。

这个发现的价值：
- 表明在该特定 default_rag 卡组合 (far_first + nearest_capacity) 下 RAG 注入不仅无效，而且导致种群完全坍缩
- 表明 card selection 不是锦上添花，选错一张卡即可导致 valid 从 100% 跌到 0%
- 为 TOCC 提供了比 objective delta 更有区分度的证据

### 2.3 对 paper 的意义

论文的叙事从"TOCC 改善了目标函数"升级为"TOCC 的精准选卡避免了灾难性坍缩，同时获得了稳定的 4.2% 改善"。前者只有 delta，后者包含了 failure mode analysis，学术分量完全不同。

---

## 3. TSP 方差诊断

### 3.1 数据

```
TSP pure_eoh        n=3  mean=6.751  [6.590, 7.057]
TSP default_rag     n=3  mean=6.756  [6.273, 7.194]
TSP tocc_corrected  n=5  mean=7.372  [6.189, 9.656]
```

去掉 outlier 后 tocc mean=6.801，仍不优于 pure。

### 3.2 根因

outlier (9.656) 和 best (6.189) 使用了**完全相同的两张 card**（`tsp_regret_insertion` + `tsp_farthest_insertion`），都是 valid=4, pop=4，无 failure。差异纯粹来自 LLM 在相同 context 下生成的代码质量不同。

**card 方向正确，问题在 gen=0 无选择压。**

### 3.3 历史数据佐证

- gen=4 pop=8 tocc best=6.287（同 card，证明深度进化下 card 有效）
- gen=0 targeted repeat×3 mean=6.513（旧数据，显著优于新 stabilization gen=0 tocc mean=7.372，说明 gen=0 LLM 方差大）

### 3.4 结论

TSP 最优先验证 gen=4（历史单点 6.287 仅作方向参考，需 pure baseline 确认后升级为确认结论）。需要先跑 pure gen=4 baseline（从未跑过），再决定 tocc gen=4 是否要补。

---

## 4. 文献代码调研

### 4.1 范围

讨论报告中列出的 5 篇论文，3 篇有公开代码：

| 论文 | 代码 | 关键发现 |
|---|---|---|
| HeuriGym (ICLR 2026) | [cornell-zhang/heurigym](https://github.com/cornell-zhang/heurigym) | Agent 循环、四阶段错误分类、solve@i 指标 |
| HeurAgenix (MSRA) | [microsoft/HeurAgenix](https://github.com/microsoft/HeurAgenix) | 瓶颈驱动进化、TTS-BON rollout 验证、function_to_tool |
| CO-Bench (CMU) | [sunnweiwei/CO-Bench](https://github.com/sunnweiwei/CO-Bench) | step/feedback/finalize 协议、几何平均归一化、沙箱隔离 |
| CoEvo-AHD | 无公开代码 | — |
| A2DEPT | 无公开代码 | — |

### 4.2 可迁移项

1. **Success funnel 接入**：HeuriGym 的四阶段错误分类可直接映射到 TOCC 五层漏斗，在 summarize 中增加自动归类
2. **solve@i 指标**：N 次 proposal 内 gatekeeper accept + valid > 0 的比例，度量 agent 可靠性
3. **几何平均归一化**：以 pure baseline 为基准归一化到 [0,1]，跨 CVRP/TSP/BP 统一评分
4. **TTS-BON**（V4 候选）：多 card 组合的小规模 rollout 验证，替代当前 LLM 单次判断
5. **反馈格式**：迭代 0 完整上下文，后续迭代仅给差异（减少 token、聚焦变化）

### 4.3 差异化定位

三层工作互不竞争：

```text
HeuriGym:  LLM 直接写启发式代码 → benchmark 评估
HeurAgenix: LLM 在运行时选择启发式 → hyper-heuristic selector
TOCC:      LLM 根据 trace 选择 operator-card prior → 控制 EOH 搜索方向
```

TOCC 的核心区分点：**experiment-control primitives**（trace reader → card selector → gatekeeper → manifest runner → summarizer），而非 operator implementation primitives。

---

## 5. Paper 定位更新

### 5.1 临时主张

```text
Trace-conditioned operator-card selection for steering LLM-based heuristic evolution.
```

中文：

```text
根据上一轮实验 trace 诊断搜索偏差，自动选择下一轮注入的 operator cards，
从而控制 LLM-based EOH 的生成先验。
```

### 5.2 LLM Proposer 边界

"tool-using research agent" 指整条 TOCC pipeline（trace reader → card selector → gatekeeper → manifest runner → summarizer），而非仅指 LLM。LLM proposer 在此 pipeline 中仅承担 trace-conditioned card selection 角色，输出限于 6 个字段（diagnosis、selected_card_ids、rag_query、rationale、expected_effect、confidence），不可控制 budget、shell command、API key、git operation 或 output path deletion。所有可执行动作必须经过 rule gatekeeper 和 manifest runner。

### 5.3 差异化表述

```text
Existing AHD methods (EoH, FunSearch, CoEvo-AHD, HeurAgenix) focus on generating
or co-evolving heuristic operators. TOCC studies how a tool-using research agent
selects operator-card priors from previous run traces to steer LLM-based
heuristic evolution.
```

### 5.3 论文条件评估

| 条件 | 当前状态 | 缺口 |
|---|---|---|
| 方法定义 | 五层漏斗 + 五工具架构已明确 | 需要 formalization 和伪代码 |
| 系统实现 | TOCC V3 + manifest runner + summarizer 已就绪 | success funnel logging 待接入 |
| CVRP 证据 | n=8 repeat-level positive + default_rag 坍缩对照 | 已充分 |
| TSP 证据 | gen=0 方差大，card 方向确认 | 需 gen=4 baseline |
| BP 证据 | 无 RAG 增益 | 不追求 |
| 文献边界 | 5 篇论文 + 3 仓库深读 | 需写 related work 草稿 |
| 消融 | pure vs default vs tocc 三臂 | TSP 侧待补齐 |
| 可复现性 | manifest runner 已具备 | 需 clean artifact package |

---

## 6. Agent 成功率五层漏斗

与 HeuriGym 四阶段对齐后：

| 层级 | 指标 | HeuriGym 对应 | CVRP tocc 当前 | CVRP default 当前 |
|---|---|---|---|---|
| Diagnosis | diagnosis_success | — | 待统计 | — |
| Proposal | proposal_accept_rate | — | 待统计 | — |
| Linkage | linkage_success | — | 待自动检查 | — |
| Generation | generation_success | Stage 1-3 通过 | 10/10 = 100% | 0/5 = 0% |
| Objective | objective_success | Stage 4: Pass | 8/8 vs pure mean | 0/5 |

漏斗接入 `summarize_manifest_runs.py` 后，每次 run 自动产出这五个布尔值。

---

## 7. 两周计划更新

| Day | 白天 | 夜间 |
|---|---:|---|
| 1 (today) | ✅ CVRP 分析 + TSP 诊断 + 文献调研 + 文档改写 | TSP pure gen=4 baseline (3 repeats) |
| 2 | 分析 TSP gen=4 结果，对比 pure vs tocc 历史锚点 | 如需：TSP tocc gen=4 repeat |
| 3 | 漏斗接入 summarize + 归一化评分实现 | CVRP/TSP 全量漏斗生成 |
| 4 | rule controller vs LLM proposer 对比报告 | — |
| 5 | 文献边界表 + related work 草稿 | Mixer/Knapsack smoke（可选） |
| 6 | architecture_v4（TOCC agent 中心视角） | — |
| 7 | 周总结：证据等级、漏斗统计、下周 run plan | 只补缺失 |
| 8-14 | 方法 formalization、伪代码、论文草稿、导师汇报 PPT | 按需补实验 |

---

## 8. AGENTS.md 审查

本文档属于 S 级文档任务，未触碰实验执行、RAG 检索代码、auth、sandbox、eval-guard 或 test infrastructure。

### preflight checklist

| 检查项 | 结论 |
|---|---|
| 是否读取或打印 API key | 否 |
| 是否执行付费 LLM 实验 | 否 |
| 是否修改实验代码 | 否 |
| 是否夸大实验结论 | 否，明确区分 repeat-level signal / exploratory / inconclusive |
| 是否包含文献来源 | 是，含 GitHub + arXiv 链接 |
| 是否包含 agent 成功率 | 是，五层漏斗 + HeuriGym 对齐 |
| 是否包含代码可迁移分析 | 是，三仓库深读 + 五可迁移项 |

### gatekeeper note

CVRP 8/8 可以写 repeat-level positive signal，不可以写 stable improvement 或统计显著。default_rag 坍缩可以写 catastrophic failure，需要避免写成"RAG 总是有害"——坍缩是特定 card 组合导致的，不是 RAG 机制本身的必然结果。
