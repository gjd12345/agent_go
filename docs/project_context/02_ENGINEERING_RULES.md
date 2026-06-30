# Engineering Rules

## Naming

- Package: `eoh_rag` (not eoh_go)
- Workspace: `eoh_rag_workspace/`
- CLI: `eoh-batch` (via pyproject.toml)
- Evidence: `evidence/<name>/` (immutable once created)

## File Header (every new .py must have)

```python
"""
Module: <ModuleName>
Purpose: <one sentence what this module does>
Owns: <what data/logic this module is responsible for>
Does not own: <what it must NOT do — prevents scope creep>
Main callers: <who imports/calls this module>
"""
```

## Directory Rules

| Path | Content | Tracked in git? |
|------|---------|-----------------|
| `eoh_rag/` | Python source code | Yes |
| `tests/` | Unit tests | Yes |
| `docs/` | Specs, TRD, rules | Yes |
| `evidence/` | Frozen experiment results | Yes |
| `eoh_rag_workspace/rag/corpus/` | RAG cards, outcomes | Yes |
| `eoh_rag_workspace/experiments/manifests/` | Experiment configs | Yes |
| `eoh_rag_workspace/shared_pool/` | Runtime pool data | No (.gitignore) |
| `eoh_rag_workspace/reports/auto_experiment_reports/run_*/` | Raw outputs | No |
| `legacy/` | Archived old code | Yes |
| `archive/` | Archived old reports | Yes |

## Commit Rules

- No `Co-Authored-By` lines
- No hardcoded absolute paths (use env vars or relative)
- No API keys in code (env vars only)
- Every feature commit must include test + spec/doc update
- Evidence freeze commits are separate from code changes

## Testing

```bash
# Full suite (excludes known pre-existing Go evaluator issues)
python3 -m pytest tests/ -q --ignore=tests/test_official_eoh_run.py \
  -k "not test_bin_packing_seed and not test_knapsack_seed and not test_mixer_split_seed"

# Quick smoke
python3 -m eoh_rag.experiments.batch_runner --manifest <manifest> --dry-run
```

## Deterministic Core vs LLM Layer

| Deterministic (no LLM calls) | LLM Layer (replaceable) |
|-----|-----|
| batch_runner scheduling | llm_reranker.py |
| PoolAPI read/write | card_synthesis.py |
| evaluator.py | rag_context_builder prompt assembly |
| run_tracker.py | tocc/agent.py diagnosis |
| problem_registry.py | eoh subprocess code generation |

## API / Env Configuration

```bash
# OpenCode (current default)
DEEPSEEK_API_KEY=...
DEEPSEEK_API_ENDPOINT=https://opencode.ai/zen/go/v1/chat/completions
DEEPSEEK_MODEL=deepseek-v4-flash

# JoyAI (internal, night use)
# stored in ~/.config/agent_go/chatrhino.env
```

## Shared Pool Convention

All experiment processes MUST use `--shared-pool-dir` when running batch experiments.
Never call `eoh_single_runner` directly for data collection (bypasses pool).
