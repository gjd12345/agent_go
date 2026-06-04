# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `bp_online`
- arm: `pure_eoh`
- pop_size: `2`
- generations: `1`
- operators: `i1`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/official_eoh_runs/bp_online/pure_eoh/run_20260604_101919`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `0`
- failure_reason: `-`
- runtime_seconds: `377.927`
- latest_generation: `1`
- population_size: `2`
- valid_candidates: `2`
- best_objective: `0.03984`

## 最优代码

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin.

    Args:
        item: size of the current item to assign
        bins: remaining capacities of feasible bins (all >= item size)
    Returns:
        scores: priority scores for each bin
    """
    # Remaining capacity if item is placed in each bin
    remaining_after_placement = bins - item
    # We want smaller remaining capacities to have higher scores.
    # Use negative remaining capacity so that max score picks smallest remainder.
    # Add 1/(bins+1) term to break ties in favor of larger original bin capacity,
    # which helps utilize partially filled bins more effectively.
    tie_breaker = 1.0 / (bins + 1)
    scores = -remaining_after_placement + tie_breaker
    return scores
```

## 最优算法描述

Assign the item to the bin whose remaining capacity after placement is closest to zero without going negative, prioritizing tighter fits to reduce wasted space and thus the total number of bins needed.
