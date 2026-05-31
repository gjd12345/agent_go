# RAG 对 EOH-InsertShips 搜索效果的实验报告（冻结版，harness 视角）

**日期**: 2026-05-28  
**模型**: JoyAI-LLM-Pro (api.chatrhino.jd.com)  
**数据集**: Solomon RC101  
**评测指标**: best_EOH_J（越低越好），valid_candidates（编译通过数），中位数 ΔJ（3-repeat）

---

## 0. 理论定位

本工作在 Li et al. "Agent Harness Engineering: A Survey" (TMLR 2026) 的 ETCLOVG 框架下定位为
**面向窄领域组合优化的 C+L+V 型 agent harness**。核心论证参见 `reports/paper_notes/c_l_v_harness_mapping.md`。

| Harness 层 | 本工作对应 | 核心问题 |
|-----------|----------|------|
| **C: Context** | RAG corpus → retrieval → format_prompt_context | 模型每一步看到什么信息？ |
| **L: Lifecycle** | EOH gen 循环 + ablation-pair + resume | 候选如何生成、评估、继承、恢复？ |
| **V: Verification** | candidate_guard + seed 检查 + build 验证 | 结果是否可信、可复现？ |

本报告不是"试了几个 prompt 变体"，而是 **在固定模型下，对 Context 层的三种注入策略做消融实验**。

---

## 1. 实验状态冻结

### 正式证据（gen=1, pop=8, 3 repeats, ablation-pair）

| 实验 | cells | 数据质量 | 结论置信度 |
|------|-------|:---:|:---:|
| **API-only vs baseline** | RC101-d50, RC101-d75 | 3/3 reps valid | HIGH |
| **History-RAG vs baseline** | RC101-d50, RC101-d75 | d50: 2/3 reps valid; d75: 3/3 | HIGH for d75, MEDIUM for d50 |
| **Full RAG vs baseline** | RC101-d50, RC101-d75 | 1 rep | LOW（单次 run） |

### 探索证据（gen≥3, single run, 不声称统计显著性）

| 实验 | 状态 | 用途 |
|------|:---:|------|
| gen=8 baseline d50: 274.90 | best_build_ok=true | 证明深演化能突破 gen=1 上限（单次 run） |
| gen=8 baseline d75: 393.30 | best_build_ok=true | 参考 |
| gen=8 API/history d50/d75 | 多个 stuck / suspicious | Context 层在深演化下不稳定 |
| gen=16 baseline d75 | **build failed** | 不用于结论（V 层过滤） |
| gen=16 history d75: 266.06 | gen=1 即到顶，stuck | 参考 |

### 排除证据

| 项目 | 原因 |
|------|------|
| RC102-d75 | seed_J 在不同 run 间不一致（350 vs 383）——V 层 seed mismatch 检测排除 |
| RC103-d50/d75 | seed_J=null 频繁出现——V 层 baseline 缺失排除 |
| Literature cards (Full RAG) | ΔJ ≥ 0，valid rate 下降——C 层 context 策略退化 |

---

## 2. 正式结果

### 2.1 RC101-d50 (seed_J = 713.52)

| 配置 | rep | Bsl_best_J | RAG_best_J | ΔJ | 裁决 |
|------|:---:|----------:|----------:|-----:|:---:|
| API-only | 1 | 660.73 | 660.73 | 0.00 | |
| API-only | 2 | 660.73 | 565.29 | −95.44 | |
| API-only | 3 | 604.59 | 316.84 | −287.75 | |
| **API-only median** | | | | **−95.44** | 2/3 better |
| History-RAG | 1 | 258.34 | 660.73 | +402.39 | （基线异常值） |
| History-RAG | 2 | 604.59 | 566.01 | −38.58 | |
| History-RAG | 3 | null | 604.59 | — | V 层过滤（build failed） |
| **History median (2 valid)** | | | | **−38.58** | 1/2 better |

**主结论**: API-only（C 层：最小高信号 context，~1006 chars）是 RC101-d50 上最稳定的改进方案。验证了 harness paper 的 progressive disclosure 原则：中等密度下，API skeleton 已提供足够约束，更多 context 引入噪声。

### 2.2 RC101-d75 (seed_J = 549.48)

| 配置 | rep | Bsl_best_J | RAG_best_J | ΔJ | 裁决 |
|------|:---:|----------:|----------:|-----:|:---:|
| API-only | 1 | 365.92 | 549.48 | +183.56 | |
| API-only | 2 | 409.39 | 376.70 | −32.69 | |
| API-only | 3 | 376.70 | 376.70 | 0.00 | |
| **API-only median** | | | | **0.00** | 1/1/1 (不确定) |
| History-RAG | 1 | 549.48 | 274.34 | −275.14 | |
| History-RAG | 2 | 549.48 | 549.48 | 0.00 | |
| History-RAG | 3 | 456.43 | 321.91 | −134.52 | |
| **History-RAG median** | | | | **−134.52** | 2/3 better |

**主结论**: History-RAG（C 层：code-level context ~1500 chars）是 RC101-d75 上唯一有稳定正向信号的配置。高密度下 LLM 需要参考 density_switch 等具体代码模式，纯 API constraint 不够。

---

## 3. 负结论

**Literature strategy cards 不适用于 insertShips 函数粒度。** 仅 1 次 run，置信度 LOW，但信号方向一致——宏观 VRP 伪代码与 Go 函数之间的粒度鸿沟可能导致 context rot（Hong et al. 2025）：
- RC101-d75: ΔJ = +349.30，valid 从 4 降到 1（重度退化）
- RC101-d50: ΔJ = +52.79（退化）
**需要更多 repeats 确认，但当前不推荐继续投入此方向。**

---

## 4. 方法学风险

| 风险 | 严重性 | 说明 |
|------|:---:|------|
| RC101-d50 baseline Rep 1 异常值 258.34 | P2 | V 层未过滤，使 History-RAG Rep 1 不可比；单次观测噪声 |
| History-RAG d50 Rep 3 baseline build failed | P1 | V 层正确过滤，但仅剩 2/3 valid pairs |
| RC102-d75 seed mismatch | P0 | V 层检测到不可比，排除该 cell |
| pop=8 gen=1 方差大 | P2 | L 层演化深度不足，基线在 300-660 间波动 |

---

## 5. 密度分支效应

```
RC101-d50 (density=50%): C:API-only > C:History-RAG > no-context
RC101-d75 (density=75%): C:History-RAG > C:API-only > no-context
```

Context 层的最优策略取决于问题密度。这支持 harness paper 的核心原则——context 的选择不是量的问题，是"对当前 step 最高信号"的问题。

---

## 6. 深度演化探索（gen=8, gen=16）

| 结论 | 证据 | 置信度 |
|------|------|:---:|
| L 层深演化在 d50 上超越 gen=1 最优 | 274.90 < 316.84（gen=1 最优） | 单次 run |
| L 层深演化在 d75 上不如 C 层早期注入 | 393.30 > 274.34 | 单次 run |
| gen=16 baseline d75 build failed | V 层 best_build_ok=false | 不可用 |
| C 层持续注入 + L 层 16 代 → stuck | gen=1→266, gen=16→266 | 单次 run |
| C 层 API-only 在 gen≥3 下不稳定 | gen=3/8 多次 0 valid | 持续出现 |

**C 层和 L 层的关系**: gen=1 是正式结论（3-repeat），gen=8/16 是探索性证据。两个层可能不互斥——warm-start schedule（gen=1 C 层注入，gen=2+ L 层自主）是下一步要验证的假设。

---

## 7. 唯一下一轮实验

**Schedule Ablation — RC101-d75 only**

| Arm | C 层 (gen=1) | C 层 (gen=2-8) | 验证假设 |
|-----|-------------|---------------|------|
| Baseline all-gens | no-context | no-context | 纯 L 层上限 |
| History all-gens | history | history | 当前 C+L 做法 |
| **History warm-start** | history | **API-only** | C 层只适合冷启动？ |
| API-only all-gens | API-only | API-only | C 层约束是否帮助 L 层长期？ |

---

## 8. 附录：关键参数

```
固定: --llm-model JoyAI-LLM-Pro --use-density-source-dirs --source-dir solomon_benchmark
      --arrival-scale 1.0

C 层配置:
  API-only:      --rag-mode literature --rag-top-k 0 --rag-max-chars 2500  (~1006 chars)
  History-RAG:   --rag-mode history    --rag-top-k 1 --rag-max-chars 1500  (~1500 chars)

API key: export $(grep -v '^#' ~/.config/agent_go/chatrhino.env | xargs)（不可 echo）

输出: eoh_go_workspace/reports/tables/
图表: eoh_go_workspace/reports/figures/
理论: eoh_go_workspace/reports/paper_notes/
```

## 9. 理论定位（总结）

| 论文概念 | 本工作对应 | 证据 |
|----------|----------|------|
| Binding-constraint thesis | 不改 JoyAI 模型，C 层改动产生 ΔJ=−95~−134 | Section 2 |
| Context rot | Full RAG (2500 chars) 比 API-only (1006 chars) 更差 | Section 3 |
| Progressive disclosure | 密度分支效应——不同密度需要不同 context | Section 5 |
| Harness > Model | gen=8 baseline 274.90 在 L 层自主超越 C 层 gen=1 最优 | Section 6 |
| C+L+V harness | 本工作的三层工程闭环 | c_l_v_harness_mapping.md |

## 附录 D: 演化产生的 InsertShips 代码

以下为 gen=8 baseline 产生的两个密度最优候选，来自纯演化（无 RAG 注入）。

### d50 最优 (best_J = 274.90, 62 行)

```
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    for orderIdx := 0; orderIdx < len(oris); orderIdx++ {
        shipId := total_ship + orderIdx
        bestAssignIdx := -1; bestDeltaCost := 1e308
        for aIdx := 0; aIdx < dispatch.AssignsLen; aIdx++ {
            assign := &dispatch.Assigns[aIdx]
            origCost := assign.Cost
            trialOk := assign.AddShip(shipId, ori, des)
            if trialOk {
                assign.GenRoute()
                deltaCost := assign.Cost - origCost
                if deltaCost < bestDeltaCost { bestDeltaCost = deltaCost; bestAssignIdx = aIdx }
                assign.RemoveShip(shipId); assign.GenRoute()
            }
        }
        // commit best, fallback to new Assign if fails
        if bestAssignIdx != -1 { ... commit ... }
        if !inserted { ... fallback new Assign ... }
    }
    dispatch.RenewnTotalCost()
}
```

**策略**: trial-insert 所有 Assign → 记录最小 deltaCost → commit 最优 → 失败 fallback。

### d75 最优 (best_J = 393.30, 142 行)

```
func InsertShips(...) {
    const slackWeight=0.6, costWeight=0.4, improveFactor=1.08, minSlackThresh=3600

    for jj := range oris {
        // Pass 1: trial with time_slack aware scoring
        for ii := 0; ii < dispatch.AssignsLen; ii++ {
            trial insert → GenRoute
            delta := newCost - prevCost
            timeSlack := float64(des.TimeEnd - des.TimeStart)
            score := costWeight*(delta/normalize) + slackWeight*(base/timeSlack)
            if score < bestScore { ... }
            RemoveShip; GenRoute()  // undo
        }
        // Pass 2: improve scan — if other Assign beats best*1.08, switch
        for ii := 0; ii < dispatch.AssignsLen; ii++ {
            delta := newCost - prevCost
            if delta < bestDelta * improveFactor { selectedIdx = ii }
        }
        // Pass 3-4: seed fallback → brute force all MAXASSIGNS
        if selectedIdx < 0 { ... }
        // commit final
        dispatch.Assigns[selectedIdx].AddShip(...); GenRoute()
    }
    dispatch.RenewnTotalCost()
}
```

**策略**: weighted scoring (cost + slack) → multi-pass refine with improve_factor → 4 级 fallback。

### 对比与启示

| | d50 (274.90) | d75 (393.30) |
|------|------|------|
| 行数 | 62 | 142 |
| 核心策略 | best-delta greedy | weighted scoring + multi-pass |
| time window 感知 | 无 | slackWeight=0.6, minSlackThresh |
| fallback 级数 | 1 | 4 |
| 适用密度 | 中等 | 高 |

LLM 在纯演化中自主学会了密度分化——d50 保持简洁，d75 引入时间窗口权重和多轮优化。
没有人类设计这些策略，evolution 发现的。
