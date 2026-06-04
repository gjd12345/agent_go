# 官方 EoH bp_online 最小对比实验

本文记录官方 EoH `bp_online` 上的最小 LLM evolution 对比。两组均为 `pop_size=2`, `generations=1`, `operators=i1`，不提交 raw run 目录。

## 结果概览

| Arm | Best objective | Valid | Samples | 结论 |
|---|---:|---:|---:|---|
| `pure_eoh` | 0.03984 | 2/2 | 6 | 最小 pure EOH 闭环跑通 |
| `api_only` | 0.03984 | 2/2 | 6 | 未优于 pure EOH，主要生成同类 best-fit 公式 |

## 初步判断

- 官方 `bp_online` benchmark 已经能通过本项目 wrapper 调用官方 EoH core 完成 LLM evolution。
- `api_only` 约束没有在这一组最小预算中带来提升；两个 arm 都收敛到 best-fit/tight-fit 风格。
- 下一步不要扩大全矩阵，先在同等预算下跑 `literature_rag`/`history_rag`，并加入更有区分度的 bin packing strategy cards。

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
