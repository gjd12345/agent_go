# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `bp_online`
- arm: `literature_rag`
- pop_size: `2`
- generations: `1`
- operators: `i1`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/official_eoh_runs/bp_online/literature_rag/run_20260604_105012`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `0`
- failure_reason: `-`
- runtime_seconds: `424.002`
- latest_generation: `1`
- population_size: `1`
- valid_candidates: `1`
- best_objective: `0.03984`

## 最优代码

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin."""
    # Post-assignment residual for each feasible bin
    residuals = bins - item
    
    # Absolute tightness: smaller residual is better → invert for scoring
    tightness = 1.0 / (residuals + 1e-9)
    
    # Global incentive: penalize bins whose residual is far from zero but also far from being useless
    # Use normalized residual to avoid scale bias
    max_residual = np.max(residuals) if len(residuals) > 0 else 1
    norm_residuals = residuals / (max_residual + 1e-9)
    # Prefer small normalized residuals (tighter fit)
    fit_quality = 1.0 - norm_residuals
    
    # Item-size awareness: for larger items, prioritize even more aggressive tightness
    # because wasting space on big items is costly
    item_factor = 1.0 + (item / (np.mean(bins) + 1e-9)) * 0.5
    
    # Combine: primary weight on tightness, secondary on fit_quality, modulated by item factor
    scores = tightness * (1.0 + fit_quality * 0.3) * item_factor
    
    # Fallback deterministic tie-break via tiny index-based perturbation
    indices = np.arange(len(bins))
    epsilon = 1e-12
    scores += indices * epsilon
    
    return scores.astype(np.float64)
```

## 最优算法描述

New algorithm: Hybrid Residual-Aware Gap Minimization (HRAGM) — prioritize bins whose post-assignment residual creates the smallest potential future waste relative to both their absolute residual and their contribution to lowering the global lower-bound gap, while strongly favoring tighter fits on larger items to delay new-bin openings.
