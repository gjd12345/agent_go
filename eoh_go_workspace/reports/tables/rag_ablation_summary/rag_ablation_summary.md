# RAG Ablation Summary

## Overall

- Paired cells: 2
- Complete cells: 2
- Unpaired cells: 0
- Seed J mismatches (>5%): 0
- Seed Res. mismatches (>5%): 0
- RAG improved J: 0
- RAG same J: 2
- RAG worse J: 0

Legend: delta_J < 0 = RAG improves J; res_ratio < 1 = faster first response; n/a = incomplete.

## Core Questions

| Problem | Density | t | Complete | Δ valid rate | Δ bad rate | ΔJ | Baseline Res ratio | RAG Res ratio | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rc101.json | d50 | 1.0 | true | 0.000 | 0.000 | 0.00 | 0.973 | 1.023 | - |
| rc101.json | d75 | 1.0 | true | 0.000 | 0.000 | 0.00 | 0.905 | 1.010 | - |
