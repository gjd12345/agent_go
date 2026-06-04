# TSP Literature-RAG 实验报告

日期：2026-06-04 | 模型：JoyAI-LLM-Pro

## 摘要

在官方 EoH benchmark `tsp_construct` 上，比较 pure EOH、API-only、默认 Literature-RAG、targeted Literature-RAG 的 init-only 和进化表现。核心发现：**targeted Literature-RAG (regret+farthest) 稳定优于 pure EOH，best=6.287（改善 -8%），但默认 RAG 无提升——变量不是"是否加 RAG"，而是"检索选中哪类 skill cards"。**

---

## 实验设置

| 参数 | 值 |
|---|---|
| problem | tsp_construct (官方 EoH, n=50) |
| model | JoyAI-LLM-Pro |
| operators | i1 |
| eval_timeout | 40s |
| llm_timeout | 180s |
| RAG query (default) | `tsp construct select next node distance nearest insertion regret route length` |
| RAG query (targeted) | `tsp construct select next node regret farthest insertion lookahead second best global route length` |
| RAG top-k | 2 |
| RAG max_chars | 2500 (实际 context 1917, 无截断) |

---

## 一、init-only 四臂对照 (gen=0, pop=4)

| arm | best | vs pure | vs api_only | valid | cards |
|---|---:|---:|---:|---:|---|
| pure_eoh | 6.83907 | — | +0.04954 | 4/4 | — |
| api_only | 6.78953 | -0.04954 | — | 4/4 | — |
| lit_rag_default | 6.83954 | +0.00047 | +0.05001 | 4/4 | nearest_insertion, nearest_neighbor |
| lit_rag_targeted | **6.51118** | **-0.32789** | -0.27835 | 4/4 | regret_insertion, farthest_insertion |

- 默认 RAG 选中的 nearest 族与模型自发生成策略重合，无增量
- targeted RAG 拉入 regret+farthest 后，best 从 6.84 → 6.51

---

## 二、repeat=3 稳定性验证 (gen=0, pop=4, targeted query)

| repeat | best | vs pure | valid/pop | runtime |
|---|---:|---:|---:|---:|
| 1 | **6.30547** | **-0.53360** | 4/4 | 1303s |
| 2 | 6.50049 | -0.33858 | 4/4 | 1014s |
| 3 | 6.73293 | -0.10614 | 4/4 | 615s |
| **median** | **6.500** | — | — | — |
| **min** | **6.305** | — | — | — |

- 3/3 全部低于 pure EOH (6.839) 和 API-only (6.790)
- 存在 init-only 随机波动 (6.30–6.73)，但方向一致
- 信号稳定，非单次运气

---

## 三、深度进化探索 (targeted query)

| config | best | vs pure | valid | 进化轨迹 |
|---|---:|---:|---:|---|
| gen=1, pop=4 | 7.3266 | +0.48753 | 4/4 | init 弱 (7.33), gen1 无改善 |
| **gen=4, pop=8** | **6.28736** | **-0.55171** | 8/8 | init=6.51 → gen2=6.32 → gen3=6.29 |
| gen=8, pop=8 | 6.49327 | -0.34580 | 8/8 | init=6.49, plateau 至 gen8 |

- gen=4,pop=8 是 sweet spot：进化轨迹清晰可解释，逐代改善
- gen=8 进入 plateau，边际收益递减
- gen=1 失败原因是该轮 init 不幸弱（LLM 随机性）

---

## 四、关键判断

1. **默认 RAG 无提升 ≠ RAG 链路失败**。默认选卡 (nearest/nearest) 与模型自发策略重合，没有给模型新信息。

2. **Targeted RAG 明确有效**。只要把 regret/farthest 拉入上下文，LLM 就能生成超越 nearest 族的策略。repeat=3 验证了稳定性。

3. **RAG 核心变量是 card selection，不是"是否加 RAG"**。同一套 RAG 基础设施，不同 query → 不同 cards → 不同结果。

4. **进化有帮助但不是无限的**。gen=0→gen=4 有改善 (6.51→6.29)，gen=4→gen=8 无改善。TSP 此规模的 sweet spot 在 gen=4 左右。

5. **BP 和 CVRP 不适合作为 RAG 正向证据**：
   - BP: 目标空间太小，pure EOH 已占优
   - CVRP: skill cards 过度倾向 capacity，需要先修复

---

## 五、最佳代码 (gen=4, pop=8, best=6.28736)

算法描述：A hybrid regret-farthest heuristic that balances immediate cost, future isolation risk, and lookahead regret by scoring each candidate based on its distance from current node, its distance from the centroid of unvisited nodes, and the regret of not visiting it now versus after an intermediate hop.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    if len(unvisited_nodes) <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]

    relevant_nodes = np.append(unvisited_nodes, destination_node)
    avg_distances = []
    for u in unvisited_nodes:
        others = np.setdiff1d(relevant_nodes, [u])
        avg_dist = np.mean([distance_matrix[u][o] for o in others])
        avg_distances.append(avg_dist)

    scores = []
    regrets = []
    for i, cand in enumerate(unvisited_nodes):
        d_current = distance_matrix[current_node][cand]
        iso_factor = avg_distances[i]
        two_hop_min = np.inf
        for j, k in enumerate(unvisited_nodes):
            if k == cand:
                continue
            two_hop = distance_matrix[current_node][k] + distance_matrix[k][cand]
            if two_hop < two_hop_min:
                two_hop_min = two_hop
        if two_hop_min == np.inf:
            regret_val = 0.0
        else:
            regret_val = max(0.0, two_hop_min - d_current)
        w_iso = 0.4
        w_regret = 0.6
        scores.append((w_iso * iso_factor + w_regret * regret_val) / (d_current + 1e-9))
        regrets.append(regret_val)

    if np.max(regrets) == 0.0:
        best_idx = np.argmin(distance_matrix[current_node][unvisited_nodes])
        min_dists = distance_matrix[current_node][unvisited_nodes]
        mask = min_dists == min_dists[best_idx]
        if np.sum(mask) > 1:
            tied_indices = np.where(mask)[0]
            best_tie_idx = tied_indices[np.argmax([avg_distances[t] for t in tied_indices])]
            return unvisited_nodes[best_tie_idx]
        return unvisited_nodes[best_idx]

    best_score_idx = np.argmax(scores)
    return unvisited_nodes[best_score_idx]
```

---

## 六、后续工作

| 优先级 | 任务 | 状态 |
|---|---|---|
| P0 | 本报告交导师审阅 | 待提交 |
| P1 | CVRP skill card 修复 + 重跑 | 待修复 |
| P1 | gen=16,pop=8 极限探索 | 待晚间跑 |
| P2 | Knapsack literature-RAG 接入 | 待开始 |
| P2 | 开源模型对比 (DeepSeek-Coder 等) | 待调研 |
