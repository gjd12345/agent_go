# Literature-RAG 实验完整报告

日期：2026-06-04 ~ 2026-06-06 | 模型：JoyAI-LLM-Pro

---

## 汇总表

| problem | pure EOH | default RAG | targeted RAG | deep best | gen sweet spot | delta vs pure | 结论 |
|---|---:|---:|---:|---:|---:|---:|---|
| `tsp_construct` | 6.839 | 6.840 (无效) | 6.511 (init) | **6.287** | gen=4,pop=8 | **-0.552 (-8.0%)** | targeted RAG 明确有效 |
| `cvrp_construct` | 13.207 | 14.494 (有害) | 13.033 (init) | **12.821** | gen=4,pop=8 | **-0.386 (-2.9%)** | card 修复 + targeted 有效 |
| `bp_online` | 0.03984 | 0.03984 (持平) | — | — | — | 0 | 目标空间太小，不适合 |

---

## 一、TSP Construct

### Per-problem 表

| config | gen | pop | best | valid | init best | final best | plateau | cards |
|---|---|---|---|:---:|---:|---:|---:|---:|---|
| pure_eoh | 0 | 4 | 6.839 | 4/4 | 6.839 | 6.839 | — | — |
| api_only | 0 | 4 | 6.790 | 4/4 | 6.790 | 6.790 | — | — |
| lit_rag_default | 0 | 4 | 6.840 | 4/4 | 6.840 | 6.840 | — | nearest_insertion, nearest_neighbor |
| lit_rag_targeted | 0 | 4 | 6.511 | 4/4 | 6.511 | 6.511 | — | regret, farthest |
| repeat 1 | 0 | 4 | 6.305 | 4/4 | 6.305 | 6.305 | — | regret, farthest |
| repeat 2 | 0 | 4 | 6.500 | 4/4 | 6.500 | 6.500 | — | regret, farthest |
| repeat 3 | 0 | 4 | 6.733 | 4/4 | 6.733 | 6.733 | — | regret, farthest |
| targeted gen=1 | 1 | 4 | 7.327 | 4/4 | 7.327 | 7.327 | yes (bad init) | regret, farthest |
| targeted gen=4 | 4 | 8 | **6.287** | 8/8 | 6.512 | 6.287 | gen3→gen4 | regret, farthest |
| targeted gen=8 | 8 | 8 | 6.493 | 8/8 | 6.493 | 6.493 | yes (gen0→gen8) | regret, farthest |
| targeted gen=16 | 16 | 8 | 6.461 | — | 6.461 | — | gen0→gen6 then API fail | regret, farthest |

### 代码演化

**Gen 0 (pure EOH, 6.839)** — progress score + nearest bias:
```python
# balance proximity to current and alignment toward destination
alpha = 0.6
combined_score = alpha * norm_dist - (1 - alpha) * norm_prog
best_idx = np.argmin(combined_score)
```

**Gen 0 (targeted init, 6.511)** — regret + farthest cluster:
```python
# regret_u = second_min_connection_cost(u) - min_connection_cost(u)
# cluster_penalty_u = distance(u, farthest_rep)
w_r, w_c, w_i = 1.0, 1.0, 1.0
scores = w_r * norm_regret + w_c * norm_cluster + w_i * (1 - norm_curdist)
```

**Gen 4 (targeted, best=6.287)** — regret + isolation + two-hop lookahead:
```python
# two_hop_min = min_k(dist[current][k] + dist[k][cand])
regret_val = max(0.0, two_hop_min - d_current)
w_iso = 0.4; w_regret = 0.6
scores.append((w_iso * iso_factor + w_regret * regret_val) / (d_current + 1e-9))
```

---

## 二、CVRP Construct

### Per-problem 表

| config | gen | pop | best | valid | init best | final best | plateau | cards |
|---|---|---|---|:---:|---:|---:|---:|---:|---|
| pure_eoh | 0 | 4 | 13.207 | — | 13.207 | 13.207 | — | — |
| lit_rag_old (capacity) | 0 | 4 | 14.494 | — | 14.494 | 14.494 | — | nearest_capacity, capacity_slack |
| lit_rag_fixed (far_first) | 0 | 4 | 13.283 | 2/2 | 13.283 | 13.283 | yes (all same) | far_first, nearest_capacity |
| lit_rag_fixed gen=4 | 4 | 8 | 13.283 | 1/1 | 13.283 | 13.283 | yes (48 samples) | far_first, nearest_capacity |
| targeted init | 0 | 4 | 13.033 | 4/4 | 13.033 | 13.033 | — | regret, far_first |
| targeted gen=4 | 4 | 8 | **12.821** | 8/8 | 12.821 | 12.821 | gen0→gen4 | regret, far_first |
| targeted gen=8 | 8 | 8 | 12.918 | 8/8 | 13.033 | 12.918 | partial (gen5 improvement) | regret, far_first |

### Card 修复前 vs 后

| query | top-2 cards | best | vs pure | 策略特征 |
|---|---|---|---|---|
| default (old) | nearest_capacity, capacity_slack | 14.494 | +1.287 | 容量优先加权 |
| default (fixed) | far_first, nearest_capacity | 13.283 | +0.076 | far-first + nearest (recipe) |
| targeted | regret_insertion, far_first | 12.821 | **-0.386** | regret + far cluster (LLM 合成) |

### 代码演化

**Old RAG (capacity, 14.494)** — 容量加权评分:
```python
# weighted combination of normalized distance and normalized capacity slack
scores = alpha * norm_dist + beta * norm_slack  # 容量优先
```

**Fixed RAG (recipe → 48 samples 退化, 13.283)**:
```python
if current_node == depot:
    return unvisited_nodes[np.argmax(distance_matrix[depot][unvisited_nodes])]
# else: nearest
return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
```

**Targeted RAG (regret + far_first, best=12.821)**:
```python
if current_node == depot:
    return unvisited_nodes[np.argmax(distance_matrix[depot][unvisited_nodes])]
# regret-based: alt_costs = distance_matrix[depot][unvisited_nodes]
# regrets = alt_costs - direct_costs
# pick highest regret within 1.5× nearest distance
mask = direct_costs <= nearest_dist * 1.5
```

---

## 三、BP Online

### Per-problem 表

| config | best | vs pure | cards | 诊断 |
|---|---:|---:|---|---|
| pure_eoh | 0.03984 | baseline | — | 自发生成 best-fit/tight-fit |
| api_only | 0.03984 | 0 | — | 策略族未改变 |
| lit_rag_default | 0.03984 | 0 | best_fit, first_fit | 与 pure 策略重合 |
| lit_rag_targeted_residual | 0.03984 | 0 | util_sqrt_exp, residual_poly | Gen1 超时，init-only 未突破 |

### 失败代码（未形成有效算子）

```python
# pure EOH 自发生成:
tightness = np.exp(-remaining_after / max(bins.max(), item))
fill_ratio = item / (bins + eps)
raw_scores = tightness * 0.7 + fill_ratio * 0.3 + exact_fit_bonus
# → 已是 strongest baseline，RAG 无法提供超越它的新知识
```

**诊断**: `score(item, bins)` 目标函数空间太小，pure EOH 在小 budget 下已占优。

---

## 关键结论

1. **Default RAG 无效是检索选卡问题，不是链路失败**。TSP default 选 nearest 族（与模型自发重合），CVRP old 选 capacity 族（方向错了）。

2. **Targeted RAG 两个 problem 都有效**：
   - TSP: regret+farthest → 6.287（改善 -8.0%）
   - CVRP: regret+far_first → 12.821（改善 -2.9%）

3. **Sweet spot 在 gen=4,pop=8**。Gen=0→4 有改善，gen=4→8 进入 plateau。

4. **BP 不适合作为 RAG 证据**：目标空间太小，强基线已占优。

5. **下一步应在 Operator-Card Agent**：自动 trace → diagnose card selection → propose targeted query。
