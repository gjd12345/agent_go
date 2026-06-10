# agent_go / TOCC 阶段成果总结

日期：2026-06-09  
性质：阶段性研究记录与导师汇报材料，不作为统计显著性结论。  

## 一句话结论

项目已经从单函数 InsertShips 演化实验推进到可复用的 TOCC 闭环：run trace -> 诊断搜索偏差 -> 选择 operator cards 和 query -> Official EOH 实跑 -> 自动记录 trace、best code 和结果。当前最明确的发现是：RAG 的主要变量不是“是否加上下文”，而是“选中了什么卡”。默认检索容易选到与 baseline 重合或方向错误的卡；有针对性的 regret + farthest / far-first 卡在 TSP、CVRP 上产生了正向 best-score 信号。

## 现有工程资产

| 层 | 已完成内容 |
|---|---|
| Corpus / RAG | algorithm cards、API rules、two-section prompt context、selected-card tracing |
| Official EOH | TSP/CVRP/BP official target runner、manifest runner、resume/no-run/force gate |
| TOCC V1 | rule controller: trace diagnosis -> selected cards + query |
| TOCC V2 | LLM proposer + rule gatekeeper，字段边界与 problem-prefix 约束 |
| V3 pilot | bounded loop 能基于 weak_negative trace 做一次纠偏并回收新 trace |
| Evidence | 自动 summary、best-code records、中文报告、card decision records |

## 当前实验信号

| Problem | 当前判断 | 证据 |
|---|---|---|
| TSP | 方差大；targeted 有 best-score 信号，但 repeat 均值暂不稳定 | V2 agent best=6.217；18-run repeat 中 r3 init-only 新低 6.189，但 tocc_corrected 均值受 9.656 outlier 影响 |
| CVRP | 当前最可靠正面证据 | repeat=3 中 tocc_corrected 3/3 优于 pure，均值约 12.970 vs 13.596，改善约 4.6% |
| BP/OBP | 当前没有 RAG 增益证据 | pure 已自发学到 tight-fit/best-fit 类策略，RAG 未突破 0.03984 |

## 18/18 stabilization repeat 快照

| Problem | Arm | Mean | r1 | r2 | r3 / note |
|---|---:|---:|---:|---:|---|
| TSP | pure_eoh | 6.751 | 6.608 | 7.057 | third run in record set |
| TSP | default_rag | 6.756 | 6.273 | 7.194 | unstable |
| TSP | tocc_corrected | 7.618 | 9.656 | 7.010 | r3 init-only new low 6.189; mean hit by outlier |
| CVRP | pure_eoh | 13.596 | 13.565 | 13.611 | baseline repeat |
| CVRP | default_rag | 13.283 | 13.283 | 13.283 | low but valid=1 degenerate |
| CVRP | tocc_corrected | 12.970 | 12.738 | 12.888 | 3/3 better than pure |

## 最优代码证据

TSP 最优代码核心不是 nearest neighbor，而是把 immediate distance、isolation 和 two-hop regret 组合成 score；CVRP 最优代码先用 far-first seed 远端簇，再用 close-to-current and far-from-depot 的组合分数推进路线。后续报告必须继续保留 best code snippet，而不是只写策略名。

## 方法伪代码

已补充 algorithm2e 版本的 TOCC method-level pseudocode：

    Algorithm 1: Trace-Conditioned Operator-Card Controller
    Input: manifest M, card library C, EOH runner E, budget B, loop limit K
    for k = 1..K:
      T_k <- collect run trace
      d_k <- diagnose search bias
      S_k, q_k <- select operator cards and query by diagnosis
      pi_k <- gatekeep(d_k, S_k, q_k, B)
      if pi_k is accepted:
        R_k <- run official EOH with selected cards
        V_k <- verify trace, best code, valid rate, objective
        archive(T_k, d_k, pi_k, R_k, V_k)
    return run archive

对应 LaTeX 源文件：eoh_go_workspace/reports/tocc_summary_20260609_assets/tocc_operator_card_controller_algorithm.tex。

## 边界

- 现在只能说 exploratory best-score signal，不能说统计稳定或证明有效。
- TSP 需要更多 repeat 或 gen>=1 排查 outlier。
- CVRP 是当前优先稳定的正面证据。
- BP/OBP 不应作为主线正面结果，除非后续改 target 或 operator cards。

## 下一步

1. 先补 CVRP repeat 的可追溯表格和 best-code 记录，巩固当前正面证据。
2. 对 TSP 进行 outlier 诊断：看 r1=9.656 的 selected cards、LLM output、valid/candidate 分布。
3. 将 TOCC controller 的选择理由、selected cards、trace、best code、valid rate 作为每次实验的强制记录字段。
4. 准备导师汇报时，主线写“框架已搭通 + CVRP repeat 正向 + TSP 方差待稳定”，不要夸大。

## 公开代码文献源码阅读

已完成公开源码调研报告：eoh_go_workspace/reports/paper_notes/llm_co_public_code_source_reading_20260609.md。

纳入：

| Work | Code | 本轮状态 |
|---|---|---|
| CO-Bench | github.com/sunnweiwei/CO-Bench | clone 成功，读 agent API 和 evaluator |
| HeuriGym | github.com/cornell-zhang/heurigym | clone 成功，读 executor / verifier / metric |
| HeurAgenix | github.com/microsoft/HeurAgenix | clone 成功，读 generator / evolver / selector / tool schema |
| EoH-S | github.com/FeiLiu36/EoH-S | 公开仓库可读，clone early EOF，待单独 sparse/zip |
| ReEvo | github.com/ai4co/reevo | 公开仓库可读，clone early EOF，待单独 sparse/zip |

直接启发：

- CO-Bench: agent.step -> evaluator.evaluate -> agent.feedback -> finalize，可作为 TOCC agent loop 的外部对齐口径。
- HeuriGym: verifier/evaluator 分离，支持把 valid/yield 和 objective 同时作为主指标。
- HeurAgenix: LLMSelectionHyperHeuristic 是 solving-state-level selector；TOCC 是 run-level operator-card selector。
- HeurAgenix function_to_tool.py 用 AST 把 heuristic function 转成 tool schema，可借鉴为 TOCC TraceReader/CardSelector/Gatekeeper/Summarizer tool schemas。
