---
name: tocc-pseudocode
description: Use for writing publication-quality pseudocode for TOCC, operator-card selection, card synthesis, RAG context construction, and EOH harness loops from agent_go code and reports.
---

# TOCC Pseudocode Skill

Use this skill to reconstruct paper-ready pseudocode for `agent_go`.

## Source Priority

1. Project code in `eoh_go/experiments/`, `eoh_go/rag/`, and `eoh_go/eoh_runner/`.
2. Goal and method notes in `.codex/goals/`.
3. Current reports in `eoh_go_workspace/reports/auto_experiment_reports/`.
4. Historical notes in `archived_experiments/reports_20260619/`.

## Algorithms To Cover

Common pseudocode targets:

- TOCC controller: trace diagnosis and operator-card selection.
- Manifest runner: experiment plan to EOH execution.
- RAG context builder: API rules, warnings, strategy cards.
- Card synthesis: best code to history card memory.
- Summarizer: run traces to evidence tables and best-code records.

## Style

- Prefer LaTeX `algorithm2e` for paper drafts.
- Keep pseudocode method-level, not line-by-line Python.
- Include inputs, outputs, decision rules, and update steps.
- Separate policy/controller logic from EOH execution logic.

## Validation

Before finalizing pseudocode:

- Check function names and fields against source code.
- Make clear which parts are deterministic rules and which parts call an LLM.
- State whether the controller is rule-based, tool-using, or learning-based.

If the external `algo-reconstruct` skill is installed, use it for final algorithm2e polish.
