# AI Assistant Skill — EOH-RAG Operations Guide

## When You (AI) Are Asked to Work on This Project

Read these files first:
1. `docs/project_context/00_PRD_EOH_RAG.md` — what the project does
2. `docs/project_context/02_ENGINEERING_RULES.md` — how to write code here
3. This file — how to operate

## Common Operations

### Run an experiment
```bash
export $(grep -v '^#' ~/.config/agent_go/opencode.env | xargs)
python3 -m eoh_rag.experiments.batch_runner \
  --manifest eoh_rag_workspace/experiments/manifests/<manifest>.json \
  --force --shared-pool-dir eoh_rag_workspace/shared_pool
```

### Check experiment status
```python
from eoh_rag.experiments.pool_api import PoolAPI
pool = PoolAPI("eoh_rag_workspace/shared_pool")
print(pool.best_codes("bp_online", top_k=3))
```

### Freeze evidence
```bash
mkdir -p evidence/<name>
# Copy best code, write result.json, commit_hash, REPRODUCE.md
```

### Run tests
```bash
python3 -m pytest tests/ -q --ignore=tests/test_official_eoh_run.py \
  -k "not test_bin_packing_seed and not test_knapsack_seed and not test_mixer_split_seed"
```

## What NOT To Do

- Don't modify `main.go` or `routing.go` (frozen Go solver)
- Don't add `Co-Authored-By` to commits
- Don't hardcode absolute paths
- Don't write to shared_pool without using PoolAPI
- Don't change baselines (they are fixed constants)
- Don't run experiments without `--shared-pool-dir`
- Don't commit raw run outputs (they're .gitignored)

## Module Quick Reference

| Need to... | Look at... |
|------------|-----------|
| Run batch experiments | `eoh_rag/experiments/batch_runner.py` |
| Understand RAG card selection | `eoh_rag/experiments/rag_context_builder.py` |
| Read/write shared pool | `eoh_rag/experiments/pool_api.py` |
| Evaluate results | `eoh_rag/experiments/evaluator.py` |
| Understand BP best formula | `evidence/bp_interpretability/` |
| Find experiment manifests | `eoh_rag_workspace/experiments/manifests/` |
| Find algorithm cards | `eoh_rag_workspace/rag/corpus/algorithm_cards.jsonl` |
| Find historical reports | `archive/` or `legacy/` |

## Modification Guidelines

When adding a new feature:
1. Check if similar pattern exists (grep the codebase)
2. Write module with 5-line header (Purpose, Owns, Does not own, Callers)
3. Write test in `tests/test_<module>.py`
4. Update relevant SPEC in `docs/specs/`
5. Run full test suite before committing
