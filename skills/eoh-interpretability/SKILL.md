# EOH Interpretability Skill

> 可解释性分析 skill — 帮助 AI 分析精英代码的策略、特征和行为差异。

## 触发条件

用户要：分析 best code 策略、比较不同 run 的行为差异、提取可解释特征、写论文 case study

## 核心操作

### 分析精英代码策略
```python
from eoh_rag.experiments.pool_api import PoolAPI
from eoh_rag.rag.problem_vocab import get_feature_vocab

pool = PoolAPI("eoh_rag_workspace/shared_pool")
codes = pool.best_codes("bp_online", top_k=5)

# 提取每份代码的策略特征
for c in codes:
    code = c["code"]
    obj = c["objective"]
    features = _identify_features(code, "bp_online")
    print(f"obj={obj:.5f} features={features}")
```

### 比较进化轨迹
```python
# 读取 pool_index 中同 problem 的 run 按时间排序
runs = pool.list_runs("bp_online")
runs.sort(key=lambda r: r.get("ts", 0))
for r in runs[-10:]:
    print(f"  ts={r['ts']:.0f} obj={r['objective']:.5f} dir={r['run_dir']}")
```

### 使用 problem-specific 词表
```python
from eoh_rag.rag.problem_vocab import get_feature_vocab, BP_FEATURE_DO

# BP 专用词表
do_dict, when_dict = get_feature_vocab("bp_online")
print("BP strategies:")
for k, v in do_dict.items():
    print(f"  {k}: {v}")
```

### 分析 card 合成质量
```python
from eoh_rag.rag.card_synthesis import synthesize_card, _build_content

# 用最佳代码生成 card
best = pool.best_codes("bp_online", top_k=1)[0]
card = synthesize_card("bp_online", best["code"], run_info={"objective": best["objective"]})
print(f"Card title: {card.title}")
print(f"Card content:\n{card.content}")
```

## 可解释性要点

### BP Online (Bin Packing)
- 核心策略：residual-based scoring（剩余容量惩罚）
- 关键特征：tight_fit, exponential penalty, dead_gap_avoidance
- 最佳结果 0.00674 的策略：multi-factor exponential scoring
- evidence 在 `evidence/final_batch_20260630/best_codes/bp_online_best.py`

### TSP Construct
- 核心策略：regret + distance-to-destination + adaptive weights
- 关键特征：destination, normalize, adaptive_weights
- 最佳结果 6.00393

### CVRP Construct
- 核心策略：capacity-aware + farthest-first + regret
- 关键特征：capacity, far_first, regret
- 最佳结果 12.35639

## 输出格式

为论文 case study 准备时，输出应包含：
1. 策略标签（来自 problem_vocab）
2. 关键代码片段（< 10 行核心逻辑）
3. 与 baseline 的 improvement 百分比
4. 进化路径简述（从哪个 seed 进化来的）

## 相关文档

- `docs/project_context/00_PRD_EOH_RAG.md` — 论文主线
- `eoh_rag/rag/problem_vocab.py` — 词表定义
- `eoh_rag/rag/card_synthesis.py` — card 合成逻辑
- `evidence/final_batch_20260630/` — 冻结 evidence
