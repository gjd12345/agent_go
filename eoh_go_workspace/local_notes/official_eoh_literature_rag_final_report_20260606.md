# Literature-RAG 阶段性实验报告：TSP / CVRP / BP

日期：2026-06-04 ~ 2026-06-06  
模型：JoyAI-LLM-Pro  
报告性质：exploratory report / 阶段性实验记录，不作为确认性最终结论。

---

## 0. 结论先行

当前实验支持一个阶段性判断：

> Literature-RAG 的关键变量不是“是否注入 RAG”，而是“检索/选择到了什么 operator cards”。默认检索可能无效甚至有害；targeted card selection 在 TSP 和 CVRP 上都观察到正向 best-score 信号。

但需要注意：

- 当前多数 deep run 仍是单次运行，不能直接推断统计稳定性。
- `gen=4,pop=8` 是当前单次实验中的最佳配置，不是已验证的全局 sweet spot。
- `TSP gen=16,pop=8` 是 partial run：运行到 Gen 6 后 API 失败严重，未完成到 Gen 16。
- BP 当前没有给出 RAG 增益证据，但不能证明 BP 本身“不适合 RAG”。

---

## 1. 汇总表

| problem | pure EOH | default RAG | targeted RAG init | deep best | 当前观察 | 谨慎结论 |
|---|---:|---:|---:|---:|---|---|
| `tsp_construct` | 6.839 | 6.840 | 6.511 | **6.287** | targeted regret+farthest 明显优于 pure/default | 正向信号较强，但 deep best 仍需多 seed 复核 |
| `cvrp_construct` | 13.207 | 14.494 | 13.033 | **12.821** | old capacity cards 有害，targeted regret+far_first 转正 | 正向信号成立，需重复验证 |
| `bp_online` | 0.03984 | 0.03984 | 0.03984 | — | 当前 budget 下 pure 已覆盖 tight/best-fit 族 | 暂无 RAG 增益证据 |

指标方向：越低越好。

---

## 2. TSP Construct

### 2.1 实验表

| config | gen | pop | best | valid | init best | final/latest best | plateau / status | cards |
|---|---:|---:|---:|:---:|---:|---:|---|---|
| pure_eoh | 0 | 4 | 6.839 | 4/4 | 6.839 | 6.839 | baseline | — |
| api_only | 0 | 4 | 6.790 | 4/4 | 6.790 | 6.790 | API 规则有小幅改善 | — |
| lit_rag_default | 0 | 4 | 6.840 | 4/4 | 6.840 | 6.840 | 无改善 | nearest_insertion, nearest_neighbor |
| lit_rag_targeted | 0 | 4 | 6.511 | 4/4 | 6.511 | 6.511 | targeted init 转正 | regret, farthest |
| targeted repeat 1 | 0 | 4 | 6.305 | 4/4 | 6.305 | 6.305 | repeat 低于 pure | regret, farthest |
| targeted repeat 2 | 0 | 4 | 6.500 | 4/4 | 6.500 | 6.500 | repeat 低于 pure | regret, farthest |
| targeted repeat 3 | 0 | 4 | 6.733 | 4/4 | 6.733 | 6.733 | repeat 低于 pure | regret, farthest |
| targeted gen=1 | 1 | 4 | 7.327 | 4/4 | 7.327 | 7.327 | bad init，无改善 | regret, farthest |
| targeted gen=4 | 4 | 8 | **6.287** | 8/8 | 6.512 | 6.287 | 当前最佳；Gen 3 后稳定 | regret, farthest |
| targeted gen=8 | 8 | 8 | 6.493 | 8/8 | 6.493 | 6.493 | 独立 run；未超过 gen4 | regret, farthest |
| targeted gen=16 | partial | 8 | 6.461 | 8/8 until Gen6 | 6.830 | 6.461 | partial run；Gen2 找到 best，Gen4 后 API 大量失败 | regret, farthest |

### 2.2 TSP gen4 / gen8 / gen16 口径说明

`gen=4,pop=8` 和 `gen=8,pop=8` 是两个独立 run，不是同一个 run 的截断对比。因此不能从单次结果直接推出 “gen=4 一定优于 gen=8”。当前只能说：

> 在本轮独立运行中，`gen=4,pop=8` 给出当前最低 best objective；`gen=8,pop=8` 没有观察到进一步收益。

`gen=16,pop=8` 没有完整跑完：

- init best = 6.83008
- Gen 2 找到 best = 6.46057
- Gen 4 后 API 大量失败
- Gen 5 / Gen 6 offspring 基本 generation failed
- 运行未完成到 Gen 16

所以 `gen=16` 只能作为 partial evidence，不应和完整 gen=4/gen=8 run 并列比较。

### 2.3 TSP 代码演化

**Pure EOH / Gen 0, best=6.839**：progress score + nearest bias。

```python
# balance proximity to current and alignment toward destination
alpha = 0.6
combined_score = alpha * norm_dist - (1 - alpha) * norm_prog
best_idx = np.argmin(combined_score)
```

**Targeted RAG / Init, best=6.511**：regret + farthest cluster。

```python
# regret_u = second_min_connection_cost(u) - min_connection_cost(u)
# cluster_penalty_u = distance(u, farthest_rep)
w_r, w_c, w_i = 1.0, 1.0, 1.0
scores = w_r * norm_regret + w_c * norm_cluster + w_i * (1 - norm_curdist)
```

**Targeted RAG / Gen 4, best=6.287**：regret + isolation + two-hop lookahead。

```python
# two_hop_min = min_k(dist[current][k] + dist[k][cand])
regret_val = max(0.0, two_hop_min - d_current)
w_iso = 0.4
w_regret = 0.6
scores.append((w_iso * iso_factor + w_regret * regret_val) / (d_current + 1e-9))
```

### 2.4 TSP 小结

TSP 是当前最强正向证据：

- default RAG 选中 nearest 族，与模型自发策略重合，几乎无改善。
- targeted query 选中 regret + farthest 后，init-only repeat=3 全部低于 pure EOH。
- gen=4,pop=8 单次 deep run 给出当前最低 best=6.287。

谨慎表述：

> TSP 上 targeted card selection 带来了清晰正向信号，但 deep run 的最优配置仍需多 seed / 同预算复核。

---

## 3. CVRP Construct

### 3.1 实验表

| config | gen | pop | best | valid | init best | final/latest best | status | cards |
|---|---:|---:|---:|:---:|---:|---:|---|---|
| pure_eoh | 0 | 4 | 13.207 | — | 13.207 | 13.207 | baseline | — |
| lit_rag_old (capacity) | 0 | 4 | 14.494 | — | 14.494 | 14.494 | 有害 | nearest_capacity, capacity_slack |
| lit_rag_fixed (far_first) | 0 | 4 | 13.283 | 2/2 | 13.283 | 13.283 | 接近 pure，但未超过 | far_first, nearest_capacity |
| lit_rag_fixed gen=4 | 4 | 8 | 13.283 | 1/1 | 13.283 | 13.283 | 48 samples 退化到 recipe | far_first, nearest_capacity |
| targeted init | 0 | 4 | 13.033 | 4/4 | 13.033 | 13.033 | targeted 转正 | regret, far_first |
| targeted gen=4 | 4 | 8 | **12.821** | 8/8 | 12.821 | 12.821 | 当前 CVRP 最佳；从 init 即强 | regret, far_first |
| targeted gen=8 | 8 | 8 | 12.918 | 8/8 | 13.033 | 12.918 | 独立 run；Gen 5/8 有改善 | regret, far_first |

### 3.2 Card 修复前 vs 后

| query / card policy | top cards | best | vs pure | 策略特征 |
|---|---|---:|---:|---|
| old default | nearest_capacity, capacity_slack | 14.494 | +1.287 | 容量优先，方向错误 |
| fixed default | far_first, nearest_capacity | 13.283 | +0.076 | far-first + nearest recipe |
| targeted | regret_insertion, far_first | **12.821** | **-0.386** | regret + far cluster，LLM 合成 |

CVRP 的结果说明：不是“有 RAG 就有用”，而是要选到能改变搜索偏好的 cards。capacity-first cards 会把模型带偏；regret + far-first cards 才带来正向信号。

### 3.3 CVRP 代码演化

**Old RAG / capacity, best=14.494**：容量加权评分，方向错误。

```python
# weighted combination of normalized distance and normalized capacity slack
scores = alpha * norm_dist + beta * norm_slack  # capacity-first bias
```

**Fixed RAG / recipe, best=13.283**：从 depot far-first，否则 nearest。48 samples 退化到同一 recipe，缺少多样性。

```python
if current_node == depot:
    return unvisited_nodes[np.argmax(distance_matrix[depot][unvisited_nodes])]

return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
```

**Targeted RAG / regret + far_first, best=12.821**：保留 far-first，同时加入 regret 选择。

```python
if current_node == depot:
    return unvisited_nodes[np.argmax(distance_matrix[depot][unvisited_nodes])]

# regret-based: alt_costs = distance_matrix[depot][unvisited_nodes]
# regrets = alt_costs - direct_costs
# pick highest regret within 1.5x nearest distance
mask = direct_costs <= nearest_dist * 1.5
```

### 3.4 CVRP 小结

CVRP 支持与 TSP 相同的机制解释：

- 默认/旧 RAG 选卡方向错，结果变差。
- 修卡后 default 接近 pure，但没有明显超过。
- targeted query 选中 regret + far_first 后，best 低于 pure EOH。

谨慎表述：

> CVRP 上 targeted card selection 观察到正向 best-score 信号；但 gen4/gen8 仍是独立单次 run，需重复实验确认稳定性。

---

## 4. BP Online

### 4.1 实验表

| config | best | vs pure | cards | 诊断 |
|---|---:|---:|---|---|
| pure_eoh | 0.03984 | baseline | — | 自发生成 best-fit / tight-fit 族 |
| api_only | 0.03984 | 0 | — | 策略族未改变 |
| lit_rag_default | 0.03984 | 0 | best_fit, first_fit | 与 pure 策略重合 |
| lit_rag_targeted_residual | 0.03984 | 0 | util_sqrt_exp, residual_poly | Gen1 超时，init-only 未突破 |

### 4.2 BP 失败代码

```python
# pure EOH 自发生成:
tightness = np.exp(-remaining_after / max(bins.max(), item))
fill_ratio = item / (bins + eps)
raw_scores = tightness * 0.7 + fill_ratio * 0.3 + exact_fit_bonus
```

### 4.3 BP 小结

当前 BP 只能说明：

> 在当前 instances、cards 和 budget 下，RAG 没有提供增益证据；可能原因是 pure EOH 已经生成了较强的 tight-fit / best-fit 类公式。

不能写成：

> BP 不适合 RAG。

后续如果要把 BP 纳入论文主证据，需要补：

- 更多 instances
- 更长 budget
- residual / utilization cards 的 oracle 注入
- pure / default / targeted 同预算 repeat
- 检查生成失败和 timeout 的根因

---

## 5. 关键观察

### 5.1 Default RAG 失败主要是 card selection 问题

TSP default RAG 选 nearest 族，和模型自发策略高度重合；CVRP old RAG 选 capacity 族，反而把搜索方向带偏。因此 default RAG 失败不能解释为 “RAG 链路失败”，更合理的解释是：

> lexical retrieval 只保证关键词相关，不保证 operator 有区分度。

### 5.2 Targeted cards 改变了生成代码结构

TSP 和 CVRP 的 targeted cards 都不是简单给模型“更多信息”，而是改变了启发式程序的结构：

- TSP: progress / nearest → regret + farthest + isolation
- CVRP: capacity-first / recipe → regret + far cluster

这支持一个后续方法方向：

> 把 RAG 从被动检索升级为 operator-card selection controller。

### 5.3 当前证据仍是 best-score oriented

当前报告主要使用 best objective，而不是 mean/std 或 paired statistical test。因此结论应保持探索性：

- 可以说 “观察到正向信号”
- 不宜说 “已证明稳定有效”

---

## 6. 后续实验建议

为了把当前阶段性信号提升为论文级证据，建议补以下消融：

1. **多 seed 重复**
   - pure EOH
   - api_only
   - default RAG
   - targeted RAG
   - 每组至少 repeat=3/5
   - 报告 mean / std / min / median / best

2. **预算对齐**
   - 固定 pop、gen、LLM 调用数
   - 避免把 RAG 效果和搜索预算混在一起

3. **Card selection 消融**
   - default query + default cards
   - targeted query + targeted cards
   - random cards
   - oracle/manual cards
   - no-RAG but explicit operator names

4. **检索质量评估**
   - 记录 top-k selected cards
   - 标注 card relevance / diversity / baseline overlap
   - 分析 default 为什么选错

5. **Operator-Card Agent 离线验证**
   - 输入 trace
   - 输出 diagnosis + card set + query
   - 看它能否复现人工 targeted selection

---

## 7. 当前可汇报版本

建议对外汇报时使用以下口径：

> 我们已经完成了从 passive Literature-RAG 到 targeted operator-card selection 的初步验证。TSP 和 CVRP 两个 official EoH benchmark 都显示：默认检索容易选到同质或错误算子，而 targeted regret/farthest 类 cards 能改变生成启发式代码结构，并在当前 best-score 实验中优于 pure EOH。下一步将把人工 targeted 选卡升级为 Operator-Card Agent，并用多 seed、同预算消融验证稳定性。

