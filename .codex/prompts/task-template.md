# Governed Task Template

Use subagents for this task. Pick the tier based on task scope.

## Goal

[Describe the task here]

## S Tier — Docs, config, small fixes

1. Spawn `scout` — map affected files, define scope.
2. Spawn `implementer` — make the change.
3. Spawn `verifier` — run checks, report evidence.

## M Tier — Feature, refactor, code change

1. Spawn `scout` — map files, scope, test gaps, risks.
2. Spawn `implementer` — smallest defensible change.
3. Spawn `gatekeeper` — correctness, security, coverage review.
4. Spawn `verifier` — run tests, report evidence.
5. Fix all P0/P1 findings. Re-run verifier.
6. Final report: files changed, commands run, test results, verdicts, risks, merge recommendation.

## L Tier — RAG, sandbox, auth, security boundary, core architecture

1. Spawn `scout` — map files, scope, risks.
2. Spawn `rag_researcher` (if retrieval/papers/external knowledge needed).
3. Spawn `implementer`.
4. Spawn `gatekeeper` — may request an extra focused security or test-design pass.
5. Spawn `verifier`.
6. Fix all P0/P1. Re-run verifier.
7. Final report as above.

## Rules

- Follow `AGENTS.md`.
- Only `implementer` may edit files.
- P0/P1 findings block completion.
- Do not claim success without command evidence.
