# Agent Governance Rules

## Purpose

Use subagents to prevent uncontrolled code growth, untested changes, and unsafe generated-code execution.

## Agent Roles

**Core (always available):**

- `scout`: read-only. Maps affected files, defines scope, identifies test gaps. Merges repo_mapper + architect + test_designer.
- `implementer`: workspace-write. Only agent allowed to edit files.
- `gatekeeper`: read-only. Reviews correctness, security, test coverage, maintainability, delivery readiness. Merges reviewer + security_auditor + quality_supervisor.
- `verifier`: read-only. Runs tests and smoke checks, reports command evidence.

**On-demand:**

- `rag_researcher`: read-only. Researches RAG, papers, external repos. Enable only for tasks involving retrieval, literature, or external knowledge.

## Task Tiers

| Tier | Scope | Agents |
|------|-------|--------|
| **S** | docs, config, small fixes | scout → implementer → verifier |
| **M** | feature, refactor, code change | scout → implementer → gatekeeper → verifier |
| **L** | RAG, sandbox, auth, security boundary, core architecture | scout → rag_researcher? → implementer → gatekeeper → verifier |

**Escalation rule:** If the change touches auth, sandbox, permissions, external calls, data deletion, secrets, RAG retrieval, eval logic, eval-guard, or test infrastructure, the workflow MUST use L tier. For L tasks, gatekeeper may request an extra focused security or test-design pass.

## Write Discipline

Only `implementer` may edit files.

Do not spawn multiple write-capable agents. Do not allow parallel edits.

Implementation begins only after scout returns its report.

## Subagent Output Contract

- **PASS**: Return only the verdict line. Do not write a report.
- **WARNING or FAIL**: Return verdict + findings (P0/P1/P2/P3) + evidence (file:line) + recommended action.

## Merge Gate

The task is not complete if `gatekeeper` or `verifier` returns FAIL.

P0/P1 findings block completion.

`implementer` cannot self-approve.

## Conflict Resolution

1. Correctness beats style.
2. Security beats convenience.
3. Tests beat assumptions.
4. Existing architecture beats speculative redesign.
5. Runtime evidence beats static speculation.
6. If unresolved, choose the lower-risk option and document the tradeoff.

## Safety Rules

Generated candidate code must run only through guarded evaluator paths.
Do not execute generated Python or Go directly in the main process.
RAG code must live under `eoh_go/rag/`; generated artifacts and reports stay under `eoh_go_workspace/`.

## Completion Requirements

Final response must include:

- files changed
- commands run
- test results
- subagent verdicts
- unresolved risks
- merge recommendation
