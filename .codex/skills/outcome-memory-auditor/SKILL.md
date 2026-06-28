---
name: outcome-memory-auditor
description: Use to audit card_outcomes.jsonl, outcome memory quality, boost/suppress evidence, decision thresholds, and whether outcome-aware rerank has real evidence. Trigger when the user mentions outcome_file, card_outcomes, boost, suppress, collapse, or outcome memory.
---

# Outcome Memory Auditor

Audit whether outcome memory can support rerank decisions.

## Inputs

Preferred file:

```text
eoh_go_workspace/rag/corpus/card_outcomes.jsonl
```

Use:

```python
from eoh_go.rag.card_outcomes import load_outcomes, summarize_all_cards
```

## Checks

Report:

```text
record count
card summary count
boost / suppress / neutral distribution
cards with insufficient evidence
cards with collapse evidence
high-variance cards
problem coverage
whether decisions are based on repeat evidence or single-run evidence
```

## Warnings

Flag:

```text
missing outcome file
empty summarize_all_cards()
all decisions neutral
suppress based on very few records
outcome memory from mismatched problem family
outcome_file passed but rag_outcome_summary_count == 0
```

Do not recommend threshold changes during linkage validation or first paid smoke. Threshold tuning is a separate experiment.

## Output

Return:

```text
usable_for_rerank: yes | no | partial
evidence summary
risks
recommended next action
```
