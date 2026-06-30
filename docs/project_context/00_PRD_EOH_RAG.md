# PRD: EOH-RAG — Trace-Conditioned Small-Model Controllers

## Problem

LLM-driven heuristic evolution (EoH) can discover strong heuristic code, but:
- High cost: each run requires dozens of LLM API calls
- Low stability: valid candidate rate varies, many runs don't beat baseline
- Black-box search: no learning across runs, each starts fresh

## Solution

Build a data flywheel where:
1. Batch EOH experiments generate traces (code, outcomes, failures, card selections)
2. Small models learn from traces to replace/assist LLM in two roles:
   - **RAG reranker**: select which strategy cards to inject (replace LLM rerank)
   - **Code gen/repair**: generate valid heuristic code (replace LLM code generation)
3. Learned models feed back into EOH, reducing cost and improving stability

## Success Criteria

| Metric | Target |
|--------|--------|
| Best objective vs EoH baseline | >5% improvement on all 3 problems |
| Median objective improvement | >3% |
| Valid candidate rate | >75% |
| Cost reduction (small model vs LLM) | >10x fewer tokens |
| Reproducibility | All results replay-verifiable |

## Problems

| Problem | Type | Benchmark | Metric |
|---------|------|-----------|--------|
| bp_online | Online Bin Packing | Weibull(3,45), cap=100 | excess_ratio over LB |
| tsp_construct | TSP50 | 8 instances | avg tour length |
| cvrp_construct | CVRP50 | 16 instances | avg total distance |

## Current Best Results

| Problem | Baseline | Best | Improvement |
|---------|----------|------|-------------|
| bp_online | 0.0398 | 0.00674 | +83.1% |
| tsp_construct | 6.560 | 6.004 | +8.5% |
| cvrp_construct | 13.519 | 12.356 | +8.6% |

## Stakeholders

- Researcher (you): experiment design, analysis, paper writing
- Claude Code: implementation, experiment execution, data processing
- GPT: code review, architecture advice
