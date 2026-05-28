# RAG Ablation Summary

## Overall

- Paired cells: 4
- Complete cells: 1
- Unpaired cells: 0
- Seed J mismatches (>5%): 0
- Seed Res. mismatches (>5%): 2
- RAG improved J: 0
- RAG same J: 0
- RAG worse J: 1

Legend: delta_J < 0 = RAG improves J; res_ratio < 1 = faster first response; n/a = incomplete.

## Core Questions

| Problem | Density | t | Complete | Δ valid rate | Δ bad rate | ΔJ | Baseline Res ratio | RAG Res ratio | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rc101.json | d50 | 1.0 | false | 0.000 | 0.000 | n/a | n/a | 0.573 | build_failed, missing_j, missing_res, seed_res_mismatch |
| rc101.json | d75 | 1.0 | true | 0.125 | -0.125 | 10.77 | 1.688 | 1.426 | - |
| rc102.json | d50 | 1.0 | false | -0.250 | 0.250 | -623.20 | 0.639 | 0.780 | no_valid_candidate, seed_res_mismatch |
| rc102.json | d75 | 1.0 | false | -0.208 | 0.208 | n/a | n/a | n/a | missing_j, missing_res |
