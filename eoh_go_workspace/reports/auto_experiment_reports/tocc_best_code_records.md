# TOCC Best Code Records / TOCC 最优代码记录

本文件记录 TOCC / targeted Literature-RAG 当前最重要的最优代码。每条记录包含 best score、valid rate、selected cards、来源 summary 路径、中文/英文策略说明和完整 best code。

This file records the most important best-code artifacts from TOCC / targeted Literature-RAG runs. Each entry includes the best score, valid rate, selected cards, source summary path, bilingual strategy notes, and full best code.

## Summary Table / 汇总表

| record | problem | gen | pop | best score | valid | selected cards | source |
|---|---|---:|---:|---:|---:|---|---|
| TSP 历史最优 / TSP historical best | tsp_construct | 4 | 8 | 6.28736 | 8/8 | tsp_regret_insertion, tsp_farthest_insertion | `eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen4_pop8/official_eoh_run_summary.json` |
| CVRP 历史最优 / CVRP historical best | cvrp_construct | 4 | 8 | 12.82084 | 8/8 | cvrp_regret_insertion, cvrp_far_first | `eoh_go_workspace/local_runs/official_eoh_cvrp_gen_20260605/targeted_gen4_pop8/official_eoh_run_summary.json` |
| TSP Phase 4 冒烟最优 / TSP Phase 4 smoke best | tsp_construct | 0 | 4 | 6.47488 | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_tsp_targeted_tsp_g0_r1/official_eoh_run_summary.json` |
| CVRP Phase 4 冒烟最优 / CVRP Phase 4 smoke best | cvrp_construct | 0 | 4 | 13.07835 | 4/4 | cvrp_regret_insertion, cvrp_far_first | `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_cvrp_targeted_cvrp_g0_r1/official_eoh_run_summary.json` |
| **TSP V2 Agent 最优 / TSP V2 agent best** ⭐ | tsp_construct | 0 | 4 | **6.21694** | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | `eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/run_tsp_construct_v2_agent_targeted_tsp_g0_r1/official_eoh_run_summary.json` |

## 1. TSP 历史最优 / TSP historical best

### 中文记录

- 问题：`tsp_construct`
- 设置：arm=`literature_rag`, generations=`4`, pop_size=`8`
- 最优分数（best score）：`6.28736`
- 有效候选：`8/8`
- 选中卡片：`tsp_regret_insertion, tsp_farthest_insertion`
- 来源：`eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen4_pop8/official_eoh_run_summary.json`
- 策略说明：该代码将 regret lookahead 与 farthest/isolation 信号组合，用当前距离、未访问节点中心性和二跳 regret 共同选择下一个节点，是目前 TSP targeted RAG 的历史最优结果。

### English Record

- Problem: `tsp_construct`
- Setting: arm=`literature_rag`, generations=`4`, pop_size=`8`
- Best score: `6.28736`
- Valid candidates: `8/8`
- Selected cards: `tsp_regret_insertion, tsp_farthest_insertion`
- Source: `eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen4_pop8/official_eoh_run_summary.json`
- Strategy note: This code combines regret lookahead with farthest/isolation signals. It scores candidates using current distance, unvisited-node centrality, and two-hop regret, and is the current historical best TSP targeted-RAG result.

### Original Algorithm Description / 原始算法描述

A hybrid regret-farthest heuristic that balances immediate cost, future isolation risk, and lookahead regret by scoring each candidate based on its distance from current node, its distance from the centroid of unvisited nodes, and the regret of not visiting it now versus after an intermediate hop, then selecting the highest score while breaking ties toward smaller immediate distance.

### Full Best Code / 完整最优代码

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    # Fallback to nearest neighbor if very few candidates remain
    if len(unvisited_nodes) <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]

    # Compute centroid of unvisited nodes (including destination as part of context)
    relevant_nodes = np.append(unvisited_nodes, destination_node)
    centroid_x = np.mean(relevant_nodes)  # Using node indices as proxy positions; replace with real coords if available
    # Since we only have distance_matrix, we'll use average distance among unvisited as a spread measure
    # Compute mean distance between each unvisited node and all other unvisited+destination
    avg_distances = []
    for u in unvisited_nodes:
        others = np.setdiff1d(relevant_nodes, [u])
        avg_dist = np.mean([distance_matrix[u][o] for o in others])
        avg_distances.append(avg_dist)

    scores = []
    regrets = []

    # For each candidate, compute immediate cost and a simple 1‑step regret
    for i, cand in enumerate(unvisited_nodes):
        # Immediate cost
        d_current = distance_matrix[current_node][cand]

        # Isolation factor: higher avg distance means more isolated
        iso_factor = avg_distances[i]

        # Regret: difference between best direct link and best two‑hop via another unvisited
        # Best direct link from current to candidate is already d_current
        # Find best two‑hop: min over another unvisited k != cand of (dist[current][k] + dist[k][cand])
        two_hop_min = np.inf
        for j, k in enumerate(unvisited_nodes):
            if k == cand:
                continue
            two_hop = distance_matrix[current_node][k] + distance_matrix[k][cand]
            if two_hop < two_hop_min:
                two_hop_min = two_hop

        if two_hop_min == np.inf:  # only one candidate left
            regret_val = 0.0
        else:
            regret_val = max(0.0, two_hop_min - d_current)

        # Score combines inverse immediate cost, isolation, and regret
        # Weights tuned empirically: balance exploration vs exploitation
        w_iso = 0.4
        w_regret = 0.6
        # Normalize components relative to current best to keep scale stable
        scores.append((w_iso * iso_factor + w_regret * regret_val) / (d_current + 1e-9))
        regrets.append(regret_val)

    # If all regrets are zero (flat landscape), fall back to nearest neighbor with isolation tiebreak
    if np.max(regrets) == 0.0:
        best_idx = np.argmin(distance_matrix[current_node][unvisited_nodes])
        # Tiebreak toward more isolated node if equal distances occur
        min_dists = distance_matrix[current_node][unvisited_nodes]
        mask = min_dists == min_dists[best_idx]
        if np.sum(mask) > 1:
            tied_indices = np.where(mask)[0]
            best_tie_idx = tied_indices[np.argmax([avg_distances[t] for t in tied_indices])]
            return unvisited_nodes[best_tie_idx]
        return unvisited_nodes[best_idx]

    # Otherwise pick candidate with highest combined score
    best_score_idx = np.argmax(scores)
    return unvisited_nodes[best_score_idx]
```

## 2. CVRP 历史最优 / CVRP historical best

### 中文记录

- 问题：`cvrp_construct`
- 设置：arm=`literature_rag`, generations=`4`, pop_size=`8`
- 最优分数（best score）：`12.82084`
- 有效候选：`8/8`
- 选中卡片：`cvrp_regret_insertion, cvrp_far_first`
- 来源：`eoh_go_workspace/local_runs/official_eoh_cvrp_gen_20260605/targeted_gen4_pop8/official_eoh_run_summary.json`
- 策略说明：该代码先用 far-first 从 depot 方向建立远端簇，然后在路线推进中结合 nearest 与 regret foresight，兼顾容量可行性和未来绕行风险，是目前 CVRP targeted RAG 的历史最优结果。

### English Record

- Problem: `cvrp_construct`
- Setting: arm=`literature_rag`, generations=`4`, pop_size=`8`
- Best score: `12.82084`
- Valid candidates: `8/8`
- Selected cards: `cvrp_regret_insertion, cvrp_far_first`
- Source: `eoh_go_workspace/local_runs/official_eoh_cvrp_gen_20260605/targeted_gen4_pop8/official_eoh_run_summary.json`
- Strategy note: This code seeds distant clusters with far-first selection near the depot, then balances nearest-neighbor greediness and regret foresight while respecting capacity feasibility. It is the current historical best CVRP targeted-RAG result.

### Original Algorithm Description / 原始算法描述

Start new routes by selecting the farthest feasible customer from the depot to seed distant clusters; once away from the depot, switch to a weighted criterion that balances nearest-neighbor greediness and regret-based foresight to minimize future detours, always respecting capacity feasibility.

### Full Best Code / 完整最优代码

```python
import numpy as np

def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    # If no feasible customers remain, return to depot (should not happen per API guarantee).
    if len(unvisited_nodes) == 0:
        return depot

    # Phase 1: Starting a new route (current at depot) -> far‑first seeding.
    if current_node == depot:
        # Compute distances from depot to each unvisited candidate.
        depot_dists = distance_matrix[depot, unvisited_nodes]
        # Select the farthest feasible customer to seed a new route.
        return unvisited_nodes[np.argmax(depot_dists)]

    # Phase 2: Already on route -> blend nearest‑neighbor with regret lookahead.
    # Gather distances from current_node to each candidate.
    cur_dists = distance_matrix[current_node, unvisited_nodes]

    # --- Regret computation ---
    # For each candidate u, find best and second‑best insertion cost
    # measured as extra distance from *current_node* (not full tour regret).
    regrets = np.zeros(len(unvisited_nodes))
    for i, u in enumerate(unvisited_nodes):
        # Distances from current_node to all other candidates (excluding u itself).
        others_mask = np.ones(len(unvisited_nodes), dtype=bool)
        others_mask[i] = False
        other_candidates = unvisited_nodes[others_mask]
        if len(other_candidates) == 0:
            regrets[i] = 0.0
            continue
        # Best alternative after visiting u is simply the closest among the others?
        # But true regret should compare inserting u now vs later.
        # We approximate: best = dist(current, u); second_best = min(dist(current, v)) over v≠u.
        # However this is just the gap between the chosen and the next best choice from current.
        # Instead we follow strategy card: best = nearest neighbor (which is exactly cur_dists[i] relative ranking),
        # but we need the "second best" alternative cost when u is removed.
        # Simpler implementation: sort cur_dists and take second smallest as the baseline for others.
        pass  # We'll handle differently below.

    # Practical fast approximation:
    # Sort indices by cur_dists ascending.
    sorted_idx = np.argsort(cur_dists)
    best_dist = cur_dists[sorted_idx[0]]
    # If there is a second candidate, its distance is the second best.
    if len(sorted_idx) >= 2:
        second_best_dist = cur_dists[sorted_idx[1]]
    else:
        second_best_dist = best_dist + 1e-6  # small margin

    # Now compute regret per candidate: regret(u) = (cost if we do NOT pick u now) - (cost if we pick u now).
    # Approximation: cost if pick u now = cur_dists[u].
    # Cost if we skip u now and pick it later will increase because we'll have to come back from somewhere else.
    # A common proxy: assume skipping u means it will be served from the same current location but after serving another customer w first.
    # That detour ≈ dist(current,w) + dist(w,u) - dist(current,u). Hard to compute without knowing order.
    # Fallback to simpler rule from cards: regret = second_best - best for the *global* choice? No, that's per node.
    # Actually typical regret‑k: for each customer compute difference between best insertion place and second best insertion place *in the current partial route*.
    # Since we only decide next single move, we interpret: 
    #   best_cost = cur_dists[u]  (insert right after current)
    #   second_best_cost = min over v≠u of (dist(current,v) + dist(v,u) - dist(v, ?)) ... complex.
    # Given complexity bound, we adopt a hybrid:

    # Heuristic blend formula:
    #   score(u) = α * (cur_dists[u]) + β * (distance from depot to u) normalized? Not needed.
    # But strategy cards suggest: once away from depot, use nearest unless regrets are high.
    # We'll compute a simple regret proxy: 
    #   Let alt_cost = min_{v≠u} (dist(current,v) + dist(v,depot) + dist(depot,u) ) - (dist(current,u)+dist(u,depot))? Still heavy.
    # Compromise: use the difference between picking u now versus picking the nearest other and leaving u for next route from depot.
    # That is: penalty_skip_u = distance_matrix[depot, u]  (serving u later from depot directly approximates extra tour).
    # Then regret ≈ max(0, penalty_skip_u - cur_dists[u]).

    # Faster and more robust: combine nearest with farthest-from-depot among close ones.
    # Implementation: choose the candidate that maximizes (normalized_distance_from_depot - normalized_cur_distance),
    # i.e., far from depot but close to current → encourages finishing distant clusters.

    # Normalize components.
    max_depot_dist = np.max(distance_matrix[depot, unvisited_nodes])
    min_cur_dist = np.min(cur_dists)
    max_cur_dist = np.max(cur_dists)

    if max_cur_dist > min_cur_dist + 1e-9:
        norm_cur = (cur_dists - min_cur_dist) / (max_cur_dist - min_cur_dist)
    else:
        norm_cur = np.zeros_like(cur_dists)

    if max_depot_dist > 1e-9:
        norm_depot = distance_matrix[depot, unvisited_nodes] / max_depot_dist
    else:
        norm_depot = np.ones_like(cur_dists)

    # Trade‑off parameter: λ=0.5 balances both goals.
    scores = 0.5 * norm_cur - 0.5 * norm_depot  # lower score better (close & far from depot)
    # Actually we want close to current AND far from depot → minimize norm_cur, maximize norm_depot.
    # So score = norm_cur - norm_depot, pick argmin.

    # Check if we should voluntarily return to depot:
    # Only consider return if no candidate can be efficiently continued without forcing a later long trip.
    # Simple rule: if all remaining customers have very small demand and are far from current but near depot,
    # maybe return early. But API says unvisited_nodes already capacity‑feasible, so optional.
    # To avoid premature returns, only return if the best score is worse than a threshold
    # AND returning allows consolidating those leftover into a fresh efficient route.
    # Conservative: never return early unless forced by capacity (already handled upstream).

    best_idx = np.argmin(scores)
    selected = unvisited_nodes[best_idx]

    return selected
```

## 3. TSP Phase 4 冒烟最优 / TSP Phase 4 smoke best

### 中文记录

- 问题：`tsp_construct`
- 设置：arm=`literature_rag`, generations=`0`, pop_size=`4`
- 最优分数（best score）：`6.47488`
- 有效候选：`4/4`
- 选中卡片：`tsp_regret_insertion, tsp_farthest_insertion`
- 来源：`eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_tsp_targeted_tsp_g0_r1/official_eoh_run_summary.json`
- 策略说明：该代码是 TOCC Phase 4 端到端 smoke 中的 TSP 最优结果，验证 selected_card_ids 能通过 regret+farthest cards 进入 prompt 并产生正向 best-score 信号。

### English Record

- Problem: `tsp_construct`
- Setting: arm=`literature_rag`, generations=`0`, pop_size=`4`
- Best score: `6.47488`
- Valid candidates: `4/4`
- Selected cards: `tsp_regret_insertion, tsp_farthest_insertion`
- Source: `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_tsp_targeted_tsp_g0_r1/official_eoh_run_summary.json`
- Strategy note: This is the best TSP result from the TOCC Phase 4 end-to-end smoke. It verifies that selected_card_ids can route regret+farthest cards into the prompt and produce a positive best-score signal.

### Original Algorithm Description / 原始算法描述

A hybrid regret-farthest insertion algorithm that selects the next node by maximizing a weighted score combining immediate distance penalty, regret value, and isolation penalty relative to the destination and current cluster, while falling back to nearest neighbor when scores are tied.

### Full Best Code / 完整最优代码

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    # Compute direct distances from current node
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    
    # Fallback: nearest neighbor distances for normalization
    min_dist_idx = np.argmin(dist_from_current)
    nearest_neighbor = unvisited_nodes[min_dist_idx]
    
    # If few nodes remain, use nearest neighbor for stability
    if len(unvisited_nodes) <= 2:
        return nearest_neighbor
    
    # Step 1: Compute regret values for each candidate
    regrets = np.zeros(len(unvisited_nodes))
    for i, cand in enumerate(unvisited_nodes):
        # Distances from candidate to all other unvisited nodes
        mask = np.ones(len(unvisited_nodes), dtype=bool)
        mask[i] = False
        others = unvisited_nodes[mask]
        if len(others) > 0:
            # Best and second‑best connections from candidate into remaining unvisited set
            # Here we approximate by using distance to current node vs distance to destination
            d_to_curr = distance_matrix[cand][current_node]
            d_to_dest = distance_matrix[cand][destination_node]
            best = min(d_to_curr, d_to_dest)
            # For second‑best we consider the other endpoint plus the smallest connection among unvisited
            if len(others) >= 1:
                d_others = distance_matrix[cand][others]
                sorted_d = np.sort(d_others)
                candidates_second = [d_to_curr, d_to_dest, sorted_d[0] if len(sorted_d) > 0 else float('inf')]
                candidates_second.remove(best)
                second_best = min(candidates_second)
            else:
                second_best = max(d_to_curr, d_to_dest)
            regrets[i] = second_best - best
        else:
            regrets[i] = 0.0
    
    # Step 2: Isolation penalty – how far this node is from destination and from current cluster center
    # Cluster center approximated as the centroid of already visited region? Not available.
    # Instead use distance to destination as proxy for isolation.
    dist_to_dest = distance_matrix[destination_node][unvisited_nodes]
    # Normalize distances to comparable scales
    max_dist = np.max(dist_from_current)
    if max_dist == 0:
        max_dist = 1.0
    norm_current = dist_from_current / max_dist
    
    max_regret = np.max(regrets) if np.max(regrets) > 0 else 1.0
    norm_regret = regrets / max_regret
    
    max_isol = np.max(dist_to_dest) if np.max(dist_to_dest) > 0 else 1.0
    norm_isol = dist_to_dest / max_isol
    
    # Step 3: Weighted composite score
    # We want: low current distance, high regret, high isolation (to seed far regions early)
    # So invert current distance and invert isolation? Wait: farthest insertion wants large isolation early,
    # but large distance to destination means it's far away now, which is good to tackle early.
    # However we also need to penalize extremely long edges now.
    # Balance: alpha * (-norm_current) + beta * norm_regret + gamma * norm_isol
    alpha, beta, gamma = 1.0, 1.5, 0.8
    scores = -alpha * norm_current + beta * norm_regret + gamma * norm_isol
    
    # Step 4: Select highest score
    best_score_idx = np.argmax(scores)
    chosen = unvisited_nodes[best_score_idx]
    
    # Safety: ensure chosen is in unvisited_nodes (guaranteed by indexing)
    # Tie‑break: if score difference negligible, pick nearer one
    best_score = scores[best_score_idx]
    second_best_score = np.partition(scores.flatten(), -2)[-2]
    if abs(best_score - second_best_score) < 1e-9:
        return nearest_neighbor
    
    return chosen
```

## 4. CVRP Phase 4 冒烟最优 / CVRP Phase 4 smoke best

### 中文记录

- 问题：`cvrp_construct`
- 设置：arm=`literature_rag`, generations=`0`, pop_size=`4`
- 最优分数（best score）：`13.07835`
- 有效候选：`4/4`
- 选中卡片：`cvrp_regret_insertion, cvrp_far_first`
- 来源：`eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_cvrp_targeted_cvrp_g0_r1/official_eoh_run_summary.json`
- 策略说明：该代码是 TOCC Phase 4 端到端 smoke 中的 CVRP 最优结果，验证 cvrp_regret_insertion+cvrp_far_first 的显式选卡链路可跑通；稳定性仍需 repeat=3。

### English Record

- Problem: `cvrp_construct`
- Setting: arm=`literature_rag`, generations=`0`, pop_size=`4`
- Best score: `13.07835`
- Valid candidates: `4/4`
- Selected cards: `cvrp_regret_insertion, cvrp_far_first`
- Source: `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_cvrp_targeted_cvrp_g0_r1/official_eoh_run_summary.json`
- Strategy note: This is the best CVRP result from the TOCC Phase 4 end-to-end smoke. It verifies that the explicit cvrp_regret_insertion+cvrp_far_first card-selection path works; stability still requires repeat=3.

### Original Algorithm Description / 原始算法描述

The algorithm combines farthest-first seeding when near the depot with regret-based selection when away from the depot to balance clustering efficiency and avoid future large detours, always respecting capacity feasibility and switching to nearest-neighbor fallback when criteria tie.

### Full Best Code / 完整最优代码

```python
import numpy as np

def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a CVRP greedy construction."""
    # If no feasible customers remain, return to depot
    if len(unvisited_nodes) == 0:
        return depot
    
    # Compute distances from current node to all feasible unvisited customers
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    
    # Strategy choice based on proximity to depot
    if current_node == depot:
        # Far‑first seeding: prefer distant customers from depot
        dist_from_depot = distance_matrix[depot][unvisited_nodes]
        # Select the farthest feasible customer
        candidate_idx = np.argmax(dist_from_depot)
        return unvisited_nodes[candidate_idx]
    else:
        # Regret insertion: evaluate detour regret among top candidates
        # Limit lookahead to the k closest feasible candidates (bounded computation)
        k = min(5, len(unvisited_nodes))
        closest_indices = np.argsort(dist_from_current)[:k]
        candidates = unvisited_nodes[closest_indices]
        
        if len(candidates) <= 1:
            # Fallback: nearest feasible customer
            return unvisited_nodes[np.argmin(dist_from_current)]
        
        # For each candidate, compute best and second‑best insertion cost
        regrets = []
        for cand in candidates:
            # Best insertion cost is direct distance from current node
            best_cost = distance_matrix[current_node][cand]
            
            # Second‑best: minimum distance from any other candidate or back to depot?
            # Actually, second‑best means the cost if we do NOT insert now but later.
            # Approximate by distance from depot to candidate (simulating a fresh start).
            # More precise regret: compare inserting now vs inserting after visiting another customer.
            # We approximate: consider distances from other candidates to this candidate,
            # but simpler: use distance from depot as proxy for "harder to reach later".
            # However, strategy card defines regret = second_best_distance - best_distance.
            # We'll interpret second_best_distance as the distance from the *second* nearest
            # feasible node (excluding the best itself) to this candidate? That's costly.
            # Instead, follow the card's intent: compute for each candidate its own best and
            # second‑best attachment point. Here, attachment points are either current node
            # or the depot (returning later). So:
            # best = dist(current, cand)
            # second_best = dist(depot, cand)
            # This matches "regret if postponed" because postponing means going depot->cand later.
            second_best_cost = distance_matrix[depot][cand]
            regret = second_best_cost - best_cost
            regrets.append(regret)
        
        max_regret = max(regrets)
        if max_regret > 0:
            # Choose candidate with highest regret (largest penalty if delayed)
            winner_idx_in_candidates = np.argmax(regrets)
            return candidates[winner_idx_in_candidates]
        else:
            # All regrets zero or negative → fallback to nearest neighbor
            return unvisited_nodes[np.argmin(dist_from_current)]
```
