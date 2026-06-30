# Loop Prompt: BP Interpretability + Evidence Freeze

Execute the BP interpretability TRD (docs/TRD_bp_interpretability.md) step by step.

## Context
- BP Online best code (obj=0.00674) is in shared_pool/best_codes_bp_online.jsonl
- EoH evaluator is at /private/tmp/EoH-main with venv at /private/tmp/eoh_official_venv/bin/python
- 8+ experiment processes still running (don't interrupt them)
- Working dir: /Users/guojiadong.9/agent_ad/agent_go

## Execution Order

### Step 0: Freeze evidence
1. Read best code from shared pool (obj=0.00674)
2. Create evidence/bp_interpretability/ directory
3. Save best_code.py, best_record.json (with commit hash, timestamp)
4. Commit + push

### Step 1a: Replay validation
1. Create eoh_go/experiments/interpretability/replay_bp.py
2. Run the score function against EoH's BP benchmark (Weibull(3,45), cap=100, 5000 items)
3. Use 20 different random seeds
4. Record: mean objective, std, invalid_placement_count, overflow_count, nan_count
5. Save to evidence/bp_interpretability/replay_results.json
6. STOP if invalid/overflow > 0 — investigate evaluator first

### Step 1b: Behavior plot
1. Create eoh_go/experiments/interpretability/behavior_plot.py
2. For item_sizes = [5, 10, 20, 40, 60]:
   - Generate bins array from 1 to 100
   - Compute residual = bins - item
   - Compute score using the formula
   - Plot (residual/item) vs score
3. Mark vertical lines at residual=0, residual=item, residual=2*item
4. Save to evidence/bp_interpretability/behavior_plot.png

### Step 1c: ab-baselines
1. Create eoh_go/experiments/interpretability/ab_baselines.py
2. Implement: FirstFit, BestFit, WorstFit, Harmonic
3. Implement ab-variants with grid search (a: 8 values, b: 6 values)
4. Implement αβ-variants with grid (α: 4 values, β: 4 values)
5. Run all on same benchmark as replay (Weibull(3,45), cap=100, 5000 items, 3 seeds)
6. Save comparison table to evidence/bp_interpretability/ab_comparison.md

### Step 1d: Formula ablation
1. Create eoh_go/experiments/interpretability/formula_ablation.py
2. Implement 7 variants (V1-V7 from TRD)
3. Run each on same benchmark (3 seeds)
4. Save results to evidence/bp_interpretability/formula_ablation.md

### Step 1e: Generalization
1. Create eoh_go/experiments/interpretability/generalization_test.py
2. Run evolved formula on 4 distributions
3. Compare with BestFit and best ab/αβ on each
4. Save to evidence/bp_interpretability/generalization_matrix.md

### Step 2 prep: Corpus variants (no run)
1. Create eoh_go_workspace/rag/corpus_variants/ directories
2. Extract BP-only cards → bp_clean_v1/algorithm_cards.jsonl
3. Snapshot current mixed cards → bp_noisy_current/
4. Build mixed-25 and mixed-50 variants
5. Write manifest templates (don't start them)

## After each step
- Commit progress (small commits)
- Check experiment processes still alive
- Report current pool best objectives
- If any step takes > 30min, report status and continue

## Constraints
- Don't modify main experiment code (batch_runner, eoh_single_runner)
- Don't interrupt running experiments
- All new code goes into eoh_go/experiments/interpretability/
- Evidence goes into evidence/bp_interpretability/
- Use OpenCode API env for evaluator runs: source ~/.config/agent_go/opencode.env
