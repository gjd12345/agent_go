# Four-Arm RAG Cross-Branch Analysis

## Scope

This note compares the evidence currently available on two branches. It does not
combine their runs into one sample because the providers, run budgets, and outcome
memory versions are not yet aligned.

| Branch | Provider | Evidence |
|---|---|---|
| `experiment/rag-ablation-4arm@b22f234` | JoyAI-LLM-Pro | Complete 24-run, four-arm, generation-4 ablation. Reports were produced at `5f10b8b`; `b22f234` later fixed nested population lookup and expanded outcome memory. |
| `run_codex@0994c19` | OpenCode `glm-5.2` | One successful TSP generation-0 outcome+population smoke and one interrupted CVRP A-arm generation-0 smoke. No comparable four-arm matrix. |

## JoyAI Four-Arm Results

All 24 runs completed with four valid candidates and no reported run failure.
The table below independently recomputes the central values from the committed
lightweight run indexes.

| Problem | Arm | Median | Mean | Sample std | Interpretation |
|---|---|---:|---:|---:|---|
| CVRP | A_pure | 13.519 | 13.391 | 0.230 | Baseline |
| CVRP | B_keyword | 13.126 | 13.219 | 0.247 | Median improvement 2.91%; weak/marginal signal |
| CVRP | C_keyword_outcome | 12.715 | 12.744 | 0.130 | Median improvement 5.95%; all three C values beat all three A values |
| CVRP | D_keyword_outcome_pop | 12.930 | 12.860 | 0.216 | Not a valid population ablation because population features were zero |
| TSP | A_pure | 6.560 | 6.506 | 0.137 | Baseline |
| TSP | B_keyword | 6.608 | 6.571 | 0.065 | Median regression 0.73% |
| TSP | C_keyword_outcome | 6.506 | 6.419 | 0.229 | Median improvement 0.83%; high variance and substantial overlap with A |
| TSP | D_keyword_outcome_pop | 6.764 | 6.599 | 0.389 | Not a valid population ablation because population features were zero |

The CVRP C-vs-A result is the strongest observation. Its median improvement is
5.95%, but its mean improvement is 4.83%. The result therefore crosses the 5%
target only under the predeclared median metric. With three repeats per arm it is
a repeat-level positive signal, not paper-grade statistical evidence.

TSP does not show a stable RAG gain. One C run reached 6.159, while the other two
were 6.506 and 6.592. The current evidence is compatible with an occasional good
outcome-guided run, not a consistent improvement.

## Population Ablation Validity

The committed JoyAI report correctly records `rag_population_feature_count=0`
for every D run. Consequently:

- D vs C does not estimate the population-aware contribution.
- The negative D medians must not be interpreted as evidence that population
  features are harmful.
- `b22f234` adds a nested `results/pops` lookup, but the branch does not contain a
  post-fix D-arm rerun proving that population features became non-zero.

The path fix is an engineering prerequisite. It should be validated with a small
D-arm smoke before any full population ablation.

## GLM Evidence

### Successful TSP linkage smoke

The local ignored summary for `glm52_tsp_outcome_population_smoke` records:

- generation: 0
- population size / valid candidates: 4 / 4
- best objective: 6.23782
- runtime: 680.593 seconds
- selected cards: `tsp_farthest_insertion`, `tsp_regret_insertion`
- outcome summaries: 11
- population features: 5

This proves that GLM, outcome memory, population features, reranking, and official
EoH can complete one TSP run together. It is not a performance comparison with
the JoyAI generation-4 matrix because there is no matched GLM A/B/C/D baseline or
repeat set.

### Interrupted CVRP smoke

The CVRP A-arm smoke ended with `failure_reason=timeout`, zero final candidates,
and no usable objective. The recorded runtime was 16,770 seconds and includes a
long computer sleep interval. The EoH log later showed repeated API failures during
initial sampling. A direct probe after stopping the run reached GLM successfully,
so this is classified as execution/recovery instability rather than model-quality
evidence.

## Outcome Memory Versioning

The two relevant outcome-memory states are different:

| State | Records | Git blob |
|---|---:|---|
| Original backfill used for the first ablation | 68 | `1f5af0a08de0ddcd2207cd3945319afa3bd5ad12` |
| JoyAI branch after `b22f234` | 104 | `e26d613359d43bfee8d2203806cf5fcb646e7722` |

Future cross-provider validation must pin one blob. Adding the 36 post-ablation
records changes the treatment itself and would confound provider comparison with
outcome-memory enrichment.

## Current Conclusions

1. **CVRP outcome-aware reranking:** promising repeat-level positive signal on
   JoyAI; strongest current result.
2. **Keyword retrieval alone:** inconclusive to weak; marginal on CVRP and slightly
   negative on TSP.
3. **Population-aware reranking:** not yet evaluated because the JoyAI D runs did
   not load population features.
4. **TSP outcome-aware reranking:** inconclusive; one strong run but no stable
   three-repeat gain.
5. **Provider comparison:** not yet possible. GLM currently has linkage evidence,
   not a matched ablation.

## Recommended Controlled Comparison

1. Pin the 68-record outcome blob and the same official EoH revision on both
   machines.
2. Validate D r2 with `rag_population_feature_count > 0` before paid matrix runs.
3. Run the same A/B/C/D manifest independently for JoyAI and GLM; retain provider
   as a separate experimental factor and never pool the repeats.
4. Use three repeats only for exploration. Expand promising cells to at least
   5-10 repeats before making stable-effect claims.
5. Report both median and mean improvement so a threshold result is not driven by
   the choice of aggregation alone.

