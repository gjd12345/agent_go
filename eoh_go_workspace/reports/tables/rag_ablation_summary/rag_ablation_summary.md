# RAG Ablation Summary

## Overall

- Paired cells: 9
- Complete cells: 6
- Unpaired cells: 0
- Seed J mismatches (>5%): 1
- Seed Res. mismatches (>5%): 4
- RAG improved J: 4
- RAG same J: 0
- RAG worse J: 2

Legend: delta_J < 0 = RAG improves J; res_ratio < 1 = faster first response; n/a = incomplete.

## Core Questions

| Problem | Density | t | Complete | Δ valid rate | Δ bad rate | ΔJ | Baseline Res ratio | RAG Res ratio | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rc101.json | d25 | 1.0 | true | 0.000 | 0.000 | -86.32 | 1.154 | 0.997 | - |
| rc101.json | d50 | 1.0 | true | 0.250 | -0.250 | 13.21 | 0.474 | 1.417 | - |
| rc101.json | d75 | 1.0 | true | 0.250 | -0.250 | 31.02 | 1.296 | 1.268 | seed_res_mismatch |
| rc102.json | d25 | 1.0 | true | -0.250 | 0.250 | -159.83 | 2.069 | 1.859 | - |
| rc102.json | d50 | 1.0 | true | 0.250 | -0.250 | -256.83 | 1.764 | 1.828 | seed_res_mismatch |
| rc102.json | d75 | 1.0 | false | -0.250 | 0.250 | n/a | n/a | 0.985 | missing_j, missing_res, seed_j_mismatch, seed_res_mismatch |
| rc103.json | d25 | 1.0 | false | 0.000 | 0.000 | n/a | n/a | n/a | missing_j, missing_res |
| rc103.json | d50 | 1.0 | false | 0.250 | -0.250 | n/a | n/a | n/a | missing_j, missing_res |
| rc103.json | d75 | 1.0 | true | 0.083 | -0.083 | -39.19 | 1.835 | 1.030 | seed_res_mismatch |
