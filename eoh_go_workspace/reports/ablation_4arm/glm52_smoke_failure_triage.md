# GLM 5.2 CVRP Smoke Failure Triage

## Incident

- branch: `run_codex`
- manifest: `rag_ablation_4arm_cvrp_smoke_codex_glm52.json`
- attempted cell: `cvrp_construct / A_pure / generation=0 / repeat=1`
- result: `timeout`
- final population: absent
- valid candidates: 0
- raw run directory: local and git-ignored

## Observed Sequence

1. The OpenCode endpoint passed the EoH connection check.
2. The computer entered a long sleep interval during initial sampling.
3. After resume, repeated GLM requests failed and only one sample artifact was
   produced before the run was stopped.
4. The wrapper wrote a structured timeout summary with no usable objective.
5. A direct post-stop probe reached `glm-5.2` successfully in about three seconds.

## Classification

This run is an infrastructure/recovery failure. It provides no evidence about
CVRP objective quality and must not be counted as an A-arm repeat.

## Safety Action

- The paid smoke process tree was stopped.
- No further paid runs were started.
- No raw logs, API credentials, samples, or population artifacts were added to
  git.

## Before Resuming

1. Add process-level restart/resume handling for sleep or reboot.
2. Record sanitized request failure types so gateway failures can be separated
   from empty model responses and parsing failures.
3. Run one CVRP A-arm generation-0 smoke while the machine remains awake.
4. Start the four-arm smoke only after that single cell completes cleanly.

