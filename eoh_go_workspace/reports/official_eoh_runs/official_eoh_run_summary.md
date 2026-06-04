# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `bp_online`
- arm: `api_only`
- pop_size: `2`
- generations: `1`
- operators: `i1`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/official_eoh_runs/bp_online/api_only/run_20260604_102757`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `0`
- failure_reason: `-`
- runtime_seconds: `1133.805`
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
    # After placing the item, the leftover space is (bins - item).
    # We want to maximize the negative of leftover space (i.e., minimize leftover),
    # so we can use (bins - item) directly but invert sign because higher leftover means lower preference.
    # However, to strictly prefer smaller leftovers, we take negative of leftover.
    # To handle exact fits best (leftover = 0), we add a small bonus for exact fits.
    # But simpler: score = -(bins - item) = item - bins? Wait, that's negative if bins > item.
    # Actually, we want larger score when leftover is smaller, so score = - (bins - item) = item - bins.
    # That gives highest score when bins == item (score = 0?), let's check:
    # If bins == item: leftover = 0, score = item - bins = 0.
    # If bins > item: leftover positive, score negative → worse than exact fit.
    # But all bins have bins >= item, so smallest leftover gives least negative (or zero).
    # So we can just use negative leftover: score = - (bins - item) = item - bins.
    # Since item is constant across bins, this is equivalent to using -bins.
    # But using -bins alone would rank same as minimizing bins, which isn't exactly our goal.
    # Better: score = 1 / (bins - item + epsilon) to heavily favor smaller leftover.
    # This gives huge scores for near-exact fits.
    
    # Add tiny epsilon to avoid division by zero when bins == item.
    eps = 1e-9
    leftover = bins - item
    # Use reciprocal to strongly prioritize smaller leftover.
    scores = 1.0 / (leftover + eps)
    return scores
```

## 最优算法描述

Maximize utilization by scoring bins based on how close their remaining capacity is to the item size after placement, preferring bins where the leftover space is minimized but still non-negative, while also prioritizing tighter fits to reduce fragmentation and thus total bins used.
