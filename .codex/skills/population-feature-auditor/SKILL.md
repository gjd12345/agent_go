---
name: population-feature-auditor
description: Use to inspect previous-run populations, extracted strategy features, population-aware dedup signals, and overlap with candidate cards. Trigger when the user mentions prev_run_dir, population_features, dedup, breadth, code_family, or population-aware rerank.
---

# Population Feature Auditor

Verify whether a previous population produces meaningful strategy features.

## Inputs

Use a previous run directory with:

```text
results/pops/population_generation_*.json
```

The latest population should be loaded and passed through:

```python
from eoh_go.rag.features import load_population_features
```

## Checks

Report:

```text
latest population path
population size
valid candidates
extracted canonical features
dominant strategy families
duplicate strategy risk
candidate card overlap
whether population_feature_count should be > 0 in rag_trace
```

## Risks

Flag:

```text
missing population files
population file not a list
no valid candidates
no code fields
only weak context tokens
features dominated by API noise
prev_run_dir passed but rag_population_feature_count == 0
```

## Output

Return:

```text
usable_for_population_rerank: yes | no | partial
features
overlap risks
recommended next card families to avoid or encourage
```
