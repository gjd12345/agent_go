# TOCC RAG 子系统升级方案 — 交叉验证用

> 请审查此方案的技术合理性、优先级排序、潜在风险，并给出你的修改建议。

---

## 1. 项目背景

**TOCC**（Trace-Conditioned Operator-Card Controller）是我们在 EoH（Evolution of Heuristics, ICML 2024）之上构建的知识注入层。EoH 用 LLM 进化组合优化启发式代码，TOCC 的核心贡献是：在每次 LLM 生成前，根据执行轨迹（trace）选择策略卡（strategy cards）注入 prompt，改变 LLM 的生成分布。

**RAG 子系统**是 TOCC 的检索层，负责：
- 从策略语料库（35 张卡：21 文献卡 + 14 历史合成卡）中选择 top-k 卡
- 将选中的卡格式化为结构化 context 追加到 EoH 的 task_description
- EoH 的 5 个算子（i1 初始化、e1/e2 交叉、m1/m2 变异）共享同一段 context

**当前实现**：
- 检索器：纯关键词 TF-IDF，只索引 title/tags/summary/constraints，不索引 content
- 卡片格式：Skill/When/Do/Fallback/Safety 文本模板，无代码
- 负反馈：存在于 TOCC controller/gatekeeper 层，但不参与检索排序
- 注入方式：所有算子共享同一 context，task-level 单点注入
- 种群感知：无。推荐的策略可能已在当前种群中实现

**目标**：升级 RAG 使 TOCC 在广度（策略覆盖面）和深度（单策略进化质量）上超越原始 EoH。

---

## 2. 已验证的问题

| # | 问题 | 证据 |
|---|------|------|
| P1 | 检索器语义盲区 | `second_best - best` 与 `regret` 无法匹配；TSP top-3 永远是词频最高的 3 张 |
| P2 | Trace 不完整 | trace 记录 `rag_selected_items`，但不记录实际注入了哪些卡、是否被截断 |
| P3 | 负反馈不入检索 | gatekeeper 可以拦卡，但 retriever 的 scoring 不知道某卡曾导致 valid collapse |
| P4 | History card 过粗 | 只保存特征组合标签（regret+destination+adaptive），不保存代码片段或公式 |
| P5 | 种群无感知 | 不知道当前种群已经实现了哪些策略，重复推荐 |
| P6 | 单一注入点 | 初始化(i1)需要广度探索、变异(m1)需要深度优化，但看到相同 context |

---

## 3. 学术参考

| 系统 | 相关机制 | 我们借鉴什么 |
|------|----------|-------------|
| **HeurAgenix** (Microsoft 2025) | LLM 作为 hyper-heuristic selector，tool calling 选函数；每次选择前后记录 observation delta | LLM 做 card selection + outcome 记录 |
| **A2DEPT** (2026) | SA + Boltzmann 自适应算子调度 | Score-proportional selection 替代固定 top-k |
| **CoEvo-AHD** (2026) | 双种群协进化，工具增强环境库 | 种群多样性管理 |
| **HeuriGym** (2025) | 逐轮 verifier feedback → repair cycle | 结构化负反馈 |
| **ReEvo** (2024) | 反思式进化 + 文本梯度 | History card 带 code snippet |
| **Harness Engineering Survey** (TMLR 2026) | Progressive disclosure，按阶段注入不同粒度 context | Operator-aware injection |
| **EoH-S** (2025) | 互补 heuristic set design | 种群覆盖感知 |

---

## 4. 方案设计（按执行顺序）

### Step 1：Trace 审计补全（~30min，风险极低）

**动机**：后续所有模块都需要 A/B 验证。当前 trace 连"哪张卡被截断"都不知道。

**变更**：
- `prompt_context.py` 的 `format_prompt_context()` 返回 `(context_str, injection_report)`
- `injection_report` 结构：`{injected_items: [{id, chars_used, truncated: bool}], total_chars, truncated_at_item: str|null}`
- `official_eoh_run.py` 的 trace dict 新增 `rag_injected_items`, `rag_context_truncated`, `rag_truncated_item_id`

**验证**：运行一次 smoke run，检查 trace JSON 中有新字段。

---

### Step 2：Card Outcome Memory（~2h，风险低）

**动机**：让 retriever 和 controller 都能用结构化的卡片历史表现数据，替代当前散落在 gatekeeper/prior_decisions 中的碎片信息。

**设计**：

```
card_outcomes.jsonl — 每行一条记录
{
  "card_id": "regret_insertion",
  "run_id": "tsp_20260625_001",
  "generation": 3,
  "injected": true,
  "valid_rate": 0.75,
  "best_delta": -12.3,      # 负 = 改善
  "mean_delta": -5.1,
  "collapse": false,
  "timeout_rate": 0.1,
  "timestamp": "2026-06-25T10:30:00"
}
```

**聚合视图**（运行时计算）：
```python
@dataclass
class CardOutcomeSummary:
    card_id: str
    total_runs: int
    avg_valid_rate: float
    avg_best_delta: float
    collapse_count: int
    confidence: float  # beta分布置信度，runs越多越高
    recommendation: str  # "boost" | "neutral" | "suppress"
```

**集成点**：
- 记录端：`official_eoh_run.py` 每 generation 结束后写入
- 读取端：retriever scoring 时作为 multiplier；controller 做 card selection 时参考 confidence

**与现有 gatekeeper 的关系**：gatekeeper 的硬规则（content 为空、id 重复）保留不变。outcome memory 是软信号，不会硬删卡。

---

### Step 3：代码片段注入（~1.5h，风险低）

**动机**：LLM 看到 "Do: maximize regret = second_best - best" 不如看到具体 5-15 行公式代码有效。ReEvo 的反思式进化也是基于具体代码做 reflection。

**变更**：
- `card_synthesis.py` 的 `synthesize_card()` 接受 `code` 参数
- 新增 `_extract_scoring_core(code, max_lines=15)` — 提取评分公式核心代码
- `_build_content()` 在 Skill/When/Do 之后追加 `\nCode:\n```python\n{snippet}\n```\n`
- `schemas.py` 的 `CorpusItem` 新增可选字段 `code_snippet: str = ""`（向后兼容）

**提取策略**：
1. 找含 `score`/`weight`/`priority`/`cost` 的代码块
2. 向上扩展到变量定义，向下扩展到 return
3. 限制 15 行；超过则取 scoring formula 核心

**字符预算**：snippet ~600 chars + 现有 content ~300 chars = 单卡 <1000 chars。3 卡 <3000 chars，在 max_chars=6000 限内。

**验证**：对已有 best code 运行 synthesize_card()，检查生成的 card 是否包含有意义的代码片段。

---

### Step 4：Retriever Hybrid 升级（~2h，风险中）

**动机**：关键词检索无法理解语义等价性。但此步骤在 Step 2 之后做，因为 LLM rerank prompt 可以利用 outcome data。

**设计**：2-stage pipeline

```
Stage 1: Keyword coarse retrieval (现有 retrieve(), top_k=10)
    ↓
Stage 2: LLM reranking (新增, 输出 top_k=3)
```

**LLM Rerank Prompt**：
```
你是策略卡选择器。当前任务：{task_description}
当前种群特征：{population_features_summary}
候选策略卡（按初步相关性排序）：
1. [{card_id}] {title} — {summary} | 历史表现：{outcome_summary}
2. ...
10. ...

请选择最能改变搜索方向的 3 张卡（避免与种群已有策略重复）。
输出 JSON: {"selected": ["id1", "id2", "id3"], "reasoning": "..."}
```

**种群感知去重**（融入此步骤）：
- 从 population code 提取 feature set
- 在 rerank prompt 中提供 `population_features_summary`
- LLM 自然会避免推荐已覆盖策略

**Fallback**：LLM 超时/失败 → 退化为 Stage 1 的 keyword top-3。

**成本控制**：
- 输入 ~1500 tokens（10 张卡的 id+title+summary+outcome）
- 输出 ~100 tokens
- 使用 DeepSeek（已有 client），单次 ~0.001 USD
- 每 generation 调用 1 次（不是每个 offspring 调用）

---

### Step 5：Operator-Aware Injection（Phase 2，~2h，风险中）

**动机**：初始化(i1)需要广度探索，变异(m1/m2)需要与 parent 相似但有增量的卡。

**设计**：

| 算子 | 注入策略 |
|------|----------|
| i1 | 全量 top-3 + code snippet（最大广度） |
| e1/e2 | 种群缺失特征卡 + diversity bonus |
| m1/m2 | 与 parent 特征最相似但有增量的 1 张卡 |
| m3 | 无卡注入（m3 是泛化简化，不需要新策略） |

**前置条件**：Step 1-4 验证有效后再做。当前 task-level 统一注入已经能验证 TOCC 主线论点。

---

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|------|------|------|
| LLM reranker 延迟增加 evolution 时间 | 中 | 每 gen 只调 1 次（不是每 offspring），fallback 到 keyword |
| LLM reranker 选卡不稳定 | 中 | 保留 trace 审计 + outcome memory 做 post-hoc 验证 |
| Code snippet 撑爆 context | 低 | 硬限 15 行/卡，max_chars 总控仍为 6000 |
| Outcome memory 冷启动 | 低 | 前几次 run 用 keyword-only，积累 outcome 后切换 |
| 向后兼容 | 低 | CorpusItem 新字段可选、retrieve() 保留、fallback 路径完整 |

---

## 6. 验证方式

| 验证项 | 方法 |
|--------|------|
| Trace 完整性 | Smoke run → 检查 trace JSON 新字段 |
| Outcome 记录正确 | 2-gen run → 检查 card_outcomes.jsonl 行数 = gen × injected_cards |
| Code snippet 质量 | 对 5 个已知 best code 运行 synthesize → 人工检查 snippet 是否包含 scoring core |
| Retriever 改善 | 固定 seed 对比：keyword top-3 vs LLM-rerank top-3 的覆盖差异 |
| 端到端效果 | 3-problem × 3-seed 实验：RAG-off / keyword-RAG / hybrid-RAG 的 best objective 对比 |

---

## 7. 不做的事

| 不做 | 原因 |
|------|------|
| Embedding 向量库 | 35 张卡，不需要 FAISS/向量检索的复杂度 |
| 微调 LLM 做选卡（GRPO） | 数据量不够，当前阶段用 prompt-based selection 足够 |
| 多轮对话式 retrieval | 增加延迟，且 EoH 单次 prompt 模式不支持 |
| 改 EoH _build_prompt() 源码 | 侵入性太大，用 task_description 注入已经够用 |
| 实时 population embedding | 35 张卡 vs population 的 feature overlap 用集合运算即可 |

---

## 8. 时间线

| 阶段 | 工时 | 产出 |
|------|------|------|
| Step 1 Trace | 30min | trace 审计字段上线 |
| Step 2 Outcome Memory | 2h | card_outcomes.jsonl + CardOutcomeSummary |
| Step 3 Code Snippet | 1.5h | history card 带代码片段 |
| Step 4 Hybrid Retriever | 2h | LLM reranker + population-aware |
| Step 5 Operator-Aware | 2h | 按算子类型差异化注入 |
| **总计** | **~8h** | |

Step 1-3 可独立上线验证，Step 4 依赖 Step 2 的 outcome data。

---

## 请 GPT 回答

1. 这个优先级排序合理吗？有没有更优的依赖顺序？
2. Card Outcome Memory 的 schema 设计是否缺少关键字段？
3. LLM reranker 的 2-stage 设计是否过度？35 张卡直接全量送 LLM 一次性选 3 是否更简单？
4. 代码片段提取策略（找 score/weight 关键词）是否可靠？有没有更好的 heuristic？
5. 有没有我遗漏的关键风险或 failure mode？
6. 从论文贡献角度，这 5 个模块中哪些最能支撑 "TOCC 超越 EoH" 的论点？
