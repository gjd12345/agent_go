# 官方 EoH bp_online 最小对比实验

本文记录官方 EoH `bp_online` 上的最小 LLM evolution 对比。实验使用官方 EoH core 和官方 `bp_online` evaluator；不提交 raw run 目录。

## 结果概览

| Arm | Status | Latest gen | Best objective | Valid | Samples | Context | 结论 |
|---|---|---:|---:|---:|---:|---|---|
| `pure_eoh` | completed | 1 | 0.03984 | 2/2 | 6 | - | 官方 pure EOH 闭环跑通，生成 best-fit/tight-fit。 |
| `api_only` | completed | 1 | 0.03984 | 2/2 | 6 | - | 未优于 pure EOH，仍生成同类 best-fit 公式。 |
| `literature_rag_default` | completed | 1 | 0.03984 | 1/1 | 6 | 1800 chars; obp_best_fit, obp_first_fit | 检索偏向 best_fit/first_fit，未带来新行为；objective 去重后 pop=1。 |
| `literature_rag_targeted_residual` | timeout_after_init | 0 | 0.03984 | 2/2 | 4 | 1800 chars; obp_eoh_util_sqrt_exp, obp_funsearch_residual_poly | 成功选中 residual/eoh 卡，但 context 截断且 Gen 1 超时；init best 仍未提升。 |

## 初步判断

- 官方 `bp_online` benchmark 已确认可通过本项目 wrapper 调用官方 EoH core 完成 LLM evolution。
- 这组最小预算下，`api_only` 和 `literature_rag` 都没有优于 pure EOH；所有有效最优解本质上都回到 best-fit/tight-fit。
- 默认 RAG 的检索问题很清楚：`obp_best_fit`/`obp_first_fit` 分数最高，给出的知识和 pure EOH 自发生成的策略重复。
- targeted residual RAG 能选中 `obp_eoh_util_sqrt_exp` 和 `obp_funsearch_residual_poly`，但 context 仍有截断，且完整 Gen 1 超时。下一步应改为 top_k=1 或更短卡片，再跑一组。
- 如果目标是展示正向收益，`bp_online` 可能不是最适合的第一正例：官方评价上 best-fit 已经很强，建议同步推进 `tsp_construct` / `cvrp_construct` 的官方小闭环。

## pure_eoh 最优算法

Assign the item to the bin whose remaining capacity after placement is closest to zero without going negative, prioritizing tighter fits to reduce wasted space and thus the total number of bins needed.

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

## api_only 最优算法

Maximize utilization by scoring bins based on how close their remaining capacity is to the item size after placement, preferring bins where the leftover space is minimized but still non-negative, while also prioritizing tighter fits to reduce fragmentation and thus total bins used.

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

## literature_rag_default 最优算法

New algorithm: Hybrid Residual-Aware Gap Minimization (HRAGM) — prioritize bins whose post-assignment residual creates the smallest potential future waste relative to both their absolute residual and their contribution to lowering the global lower-bound gap, while strongly favoring tighter fits on larger items to delay new-bin openings.

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

## literature_rag_targeted_residual 最优算法

Score bins by combining a strong preference for minimizing leftover space after placement with a secondary preference for using already highly-utilized bins, implemented via a normalized best-fit term and a utilization bonus that avoids extreme penalties to keep all scores finite.

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    residuals = bins - item
    min_r = np.min(residuals)
    max_r = np.max(residuals)
    
    # Primary term: best-fit preference (normalized, higher when residual is smaller)
    if max_r > min_r:
        primary = 1.0 - (residuals - min_r) / (max_r - min_r + 1e-12)
    else:
        primary = np.ones_like(residuals, dtype=float)
    
    # Secondary term: utilization bonus based on original remaining capacity before placing item
    # We want to slightly favor bins that are more filled, but avoid extreme values.
    # Use a gentle linear scaling from empty (bonus ~0) to full (bonus ~1).
    capacity_approx = bins.max() + item  # rough estimate of bin capacity, works if at least one bin can hold item+something
    util_bonus = 1.0 - bins / (capacity_approx + 1e-12)
    
    # Combine: primary dominates, secondary adds tie-breaking towards higher utilization.
    scores = primary * 10.0 + util_bonus
    
    return scores.astype(float)
```
