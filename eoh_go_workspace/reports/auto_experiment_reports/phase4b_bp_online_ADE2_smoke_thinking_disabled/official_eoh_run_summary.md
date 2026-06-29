# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `bp_online`
- arm: `pure_eoh`
- pop_size: `1`
- generations: `0`
- operators: `i1`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/auto_experiment_reports/phase4b_bp_online_ADE2_smoke_thinking_disabled/bp_online/pure_eoh/run_20260629_150818`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `0`
- failure_reason: `-`
- runtime_seconds: `22.39`
- latest_generation: `0`
- population_size: `1`
- valid_candidates: `1`
- best_objective: `0.86427`

## 最优代码

```python
def score(item: int, bins: np.ndarray) -> np.ndarray:
    waste = bins - item
    penalty = np.exp(-waste / (bins + 1e-9))
    reward = 1.0 / (waste + 1e-9)
    return reward - penalty
```

## 最优算法描述

Use a score that combines remaining capacity inversely with a penalty for near-full bins, plus a reward for bins that leave minimal leftover waste after insertion, to encourage dense packing and reduce bin count.
