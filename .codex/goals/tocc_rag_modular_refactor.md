/goal: TOCC-RAG Modular Refactor - candidate pool -> rerank -> final injected cards

目标：暂停继续扩展 Phase 4b / embedding / operator-aware injection，先把 TOCC-RAG 从“selected cards 直接注入”重构成分层清晰、可解释、可 ablation、可复现、可继续扩展的实验系统。

本文件是长期执行 goal，不代表创建本文件时立即执行 Commit 1-4。创建本 goal 的 PR 只允许新增 goal 文档；后续每个 commit/PR 单独执行对应阶段。

报告一律写中文。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。raw run、population、samples、run log 不入 git。允许入 git 的只有 manifest、summary、整理后的报告、card decision、card memory、best-code records、literature notes、goal 文档。

---

## 0. 当前判断

当前系统已经出现字段语义和模块职责混合：

- `retriever.py` 同时承担 keyword retrieve、outcome/population rerank、rerank debug score、population code feature extraction。
- `build_official_rag_context()` 已支持 `outcome_summaries`，但 `eoh_single_runner` 当前只接入 `prev_run_dir -> population_features`，没有正式接入 outcome memory。
- TOCC agent/gatekeeper/loop 仍把 `cards` / `selected_card_ids` 当最终注入卡使用。
- `batch_runner` 对 `tocc_*` arm 仍要求 `selected_card_ids`，manifest 语义尚未升级到 candidate pool。
- population dedup、outcome memory、selected_card_ids 精确注入正在同一条链路上互相影响，继续加能力会降低实验可解释性。

因此本 goal 的优先级高于继续扩展深度/广度功能。

---

## 1. 术语与层级

统一术语：

```text
candidate_card_ids = TOCC agent/controller 推荐的候选池，必须放在 arm 层
rag_selected_items = RAG/reranker 最终注入 prompt 的卡
selected_card_ids = legacy alias，只做兼容，不作为新字段继续扩展
cards = legacy agent proposal alias，只做兼容
```

Manifest 层级规则：

```text
arm.candidate_card_ids          # 每个 arm 自己的候选池
manifest.rag.top_k              # 全局 RAG 配置
manifest.rag.max_chars          # 全局 RAG 配置
manifest.rag.prev_run_dir       # 全局或批次级 population signal 来源
manifest.rag.outcome_file       # 全局或批次级 outcome memory 来源
```

禁止把 `candidate_card_ids` 放到 `manifest.rag` 全局层。一个 manifest 可以包含多个 arm，每个 arm 必须能拥有不同候选池。

短期 CLI 兼容规则：

```text
--selected-card-ids 暂时作为 legacy allowlist 参数继续使用。
它在新语义下表示 candidate allowlist，不表示最终注入卡。
最终注入卡以 rag_trace.rag_selected_items / rag_injected_items 为准。
```

---

## 2. Candidate Pool 规则

`candidate_card_ids` 只过滤 strategy cards，不影响 problem API/global constraint cards 注入。API skeleton、problem constraints、global warnings 等必须继续由 RAG context builder 根据 problem/mode 注入。

候选池必须按输入顺序做 order-preserving dedupe，并且去重后再执行 min/max 数量检查。

本轮新增硬约束：

- `candidate_card_ids` 只过滤 strategy cards，不影响 problem API/global constraint cards 注入。
- `candidate_card_ids` 必须 order-preserving dedupe；去重后再执行 min/max 数量检查。
- unknown `candidate_card_ids` 必须在 gatekeeper 阶段 reject。
- 被 history gate block 的候选卡必须在 builder 阶段 fail fast。
- candidate allowlist 过滤后为空不得静默回退到全量 pool。
- trace 额外记录 `rag_candidate_card_source: candidate_card_ids | selected_card_ids | cards | none`。
- trace 额外记录 `rag_candidate_pool_size_before_filter`。
- 候选池建议 4-8 张；若可用候选不足 4 张，允许少于 4，但必须写入 warning/trace。
- 若本 PR 只新增 goal 文档，不要求 pytest；若同 PR 包含任何 Python/Go 代码改动，必须按代码改动验收标准运行测试。

候选池来源优先级：

```text
candidate_card_ids -> selected_card_ids -> cards -> none
```

trace 必须记录候选来源：

```text
rag_candidate_card_source: candidate_card_ids | selected_card_ids | cards | none
```

过滤边界：

- unknown `candidate_card_ids` 必须在 gatekeeper 阶段 reject。
- 被 history gate block 的候选卡必须在 builder 阶段 fail fast。
- candidate allowlist 过滤后为空不得静默回退到全量 pool。
- `candidate_card_ids` 只约束 strategy pool，不约束 global/API constraints。

候选池数量：

- 正常建议 4-8 张候选卡。
- `MAX_CANDIDATE_CARDS = 10`。
- 若可用候选不足 4 张，允许少于 4，但必须写入 warning/trace。
- 去重后再检查 min/max；重复项只产生 warning，不应导致误判数量超限。

trace 必须额外记录：

```text
rag_candidate_card_ids
rag_candidate_card_source
rag_candidate_pool_size_before_filter
rag_candidate_pool_size_after_filter
rag_selection_space_warning
```

当 `candidate_count <= top_k` 时，trace 写入 warning：rerank 没有替换空间。

---

## 3. 目标调用链

```text
TOCC agent/controller
  -> output arm.candidate_card_ids + rag_query

gatekeeper
  -> normalize and order-preserving dedupe candidate_card_ids
  -> reject unknown candidate ids
  -> validate candidate count after dedupe
  -> safe_arm.candidate_card_ids

loop / batch_runner
  -> arm.candidate_card_ids
  -> legacy --selected-card-ids allowlist
  -> manifest.rag.prev_run_dir
  -> manifest.rag.outcome_file

single_runner
  -> load rerank signals
  -> RagContextRequest

rag_context_builder
  -> load corpus
  -> keep problem API/global constraint cards independent
  -> apply candidate allowlist only to strategy cards
  -> fail fast on blocked history candidates
  -> keyword retrieve
  -> rerank with outcome/population signals
  -> format prompt context
  -> write trace

official EOH
  -> run
  -> summary
  -> outcome memory update
```

---

## 4. 执行顺序

### Commit 1a：字段兼容，不改 agent 策略

目标：底层先接受新字段，保持旧 agent prompt 可用。

必须完成：

- `gatekeeper` 支持 `candidate_card_ids` / `cards` / `selected_card_ids` fallback。
- `gatekeeper` 对候选卡做 order-preserving dedupe。
- `gatekeeper` 对 unknown candidate ids reject。
- `safe_arm` 输出 `candidate_card_ids`。
- `batch_runner` 读取 `arm.candidate_card_ids` fallback `arm.selected_card_ids`。
- `loop.py` 读取 `candidate_card_ids` fallback `selected_card_ids`。
- `build_official_rag_context` 只用 candidate allowlist 过滤 strategy cards，不影响 API/global constraint cards。
- `build_official_rag_context` trace 增加：
  - `rag_candidate_card_ids`
  - `rag_candidate_card_source`
  - `rag_candidate_pool_size_before_filter`
  - `rag_candidate_pool_size_after_filter`
  - `rag_selection_space_warning`
- candidate allowlist 过滤后为空必须 fail fast，不得静默回退全量 pool。
- history gate block 的候选卡必须 fail fast。
- 不改 `agent.py` prompt，不扩大候选池数量。

### Commit 1b：agent/gatekeeper 正式切 candidate pool

目标：统一 candidate pool 语义并保持 CLI 兼容。该阶段可能改变最终注入卡，因为 rerank 获得了更大的候选池；所有变化必须通过 trace 可解释。

必须完成：

- `agent.py` prompt 改成输出 `candidate_card_ids`。
- 候选池建议 4-8 张。
- 若 available candidate cards 少于 4 张，允许输出少于 4 张，但必须写入 warning/trace。
- `gatekeeper` 使用候选池限制：
  - `MIN_CANDIDATE_CARDS = 2`
  - `MAX_CANDIDATE_CARDS = 10`
- `selected_card_ids` / `cards` 继续作为 legacy fallback。
- 不删除 `--selected-card-ids` CLI。

### Commit 2：P0 接通 outcome memory

目标：让 Phase 4a 的 outcome + population-aware rerank 完整生效。未完成前，不允许声称 Phase 4a 已完整接通。

必须完成：

- `eoh_single_runner` 增加 `--outcome-file`。
- `batch_runner` 支持 `manifest.rag.outcome_file`。
- 外层 loader 执行：
  - `outcome_file -> load_outcomes() -> summarize_all_cards() -> outcome_summaries`
  - `prev_run_dir -> population_features`
- `build_official_rag_context` 接收真实 `outcome_summaries`。
- trace 记录：
  - `rag_outcome_file`
  - `rag_outcome_summary_count`
  - `rag_rerank_enabled`

### Commit 3：拆 retriever/reranker/features

目标：降低 `retriever.py` 复杂度，保持外部 import 兼容。

拆分：

```text
eoh_go/rag/retriever.py   -> keyword retrieve
eoh_go/rag/reranker.py    -> RerankConfig + outcome/population rerank
eoh_go/rag/features.py    -> code/card/population feature extraction
```

必须保留兼容 wrapper：

```python
# eoh_go/rag/retriever.py
from eoh_go.rag.reranker import RerankConfig, retrieve_with_rerank, score_corpus_with_rerank
from eoh_go.rag.features import load_population_features
```

### Commit 4：拆 rag_context_builder

目标：让 `eoh_single_runner.py` 回到单次执行职责。

新增：

```text
eoh_go/experiments/rag_context_builder.py
```

核心请求对象不直接承担文件 I/O：

```python
@dataclass
class RagContextRequest:
    problem: str
    mode: str
    query: str | None
    top_k: int
    max_chars: int
    candidate_card_ids: list[str] | None = None
    outcome_summaries: dict[str, object] | None = None
    population_features: set[str] | None = None
    rerank_config: RerankConfig | None = None
```

`single_runner` 或独立 signal loader 负责把 `outcome_file` / `prev_run_dir` 转成已加载信号。

---

## 5. 验收标准

创建本 goal 文件本身：

```text
只检查 Markdown 文件存在、UTF-8 可读、没有 API key/raw log/raw run 内容。
不运行实验，不执行 Commit 1-4 代码改动。
若本 PR 只新增 goal 文档，不要求 pytest。
```

后续同 PR 如果包含任何 Python/Go 代码改动，必须按代码改动验收标准运行测试。

Python/RAG/TOCC 代码改动默认必跑：

```powershell
python -m pytest tests -q
python -m compileall -q eoh_go
```

仅当改动 Go executor、Go candidate、根目录 Go 文件时，额外跑：

```powershell
go build -o mainbin_sa.exe .
```

定向测试优先覆盖：

```text
tests/test_tocc_gatekeeper.py
tests/test_experiment_manifest_runner.py 或现有 batch runner 测试
tests/test_rag_retriever.py
tests/test_rag_context.py 或现有 eoh_single_runner/RAG context 测试
```

如果预期测试文件不存在，不允许静默跳过；阶段报告必须说明“未找到测试文件，需要补测试”。

---

## 6. 禁止事项

```text
1. 不要一开始就做 embedding / hybrid / LLM rerank。
2. 不要把 candidate_card_ids 写成最终注入卡。
3. 不要把 candidate_card_ids 放到 manifest.rag 全局层。
4. 不要删除 selected_card_ids/cards 兼容逻辑。
5. 不要在同一个 commit 同时改字段语义、拆文件、接 outcome。
6. 不要用单次 smoke 结果声称稳定提升。
7. 不要打印 API key、endpoint token 或 raw LLM log。
8. 不要让 candidate allowlist 影响 problem API/global constraint cards 注入。
9. 不要在 candidate allowlist 过滤为空时静默回退全量 pool。
```

---

## 7. 完成时填报清单

每次阶段完成后补充：

- files changed:
- commands run:
- test results:
- subagent verdicts:
- unresolved risks:
- merge recommendation:
