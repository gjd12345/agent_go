# Governed Review Template

Use subagents to review the current diff.

## Workflow

1. Spawn `scout` — identify changed files, affected modules, call paths.
2. Spawn `gatekeeper` — correctness, security, coverage, maintainability review.
3. Spawn `verifier` — run or identify required verification commands.

## Output

- Overall verdict: PASS / CONDITIONAL PASS / FAIL
- P0/P1 blocking issues with evidence (file:line)
- P2/P3 non-blocking issues
- Verification evidence (commands run, results)
- Merge recommendation

## Rules

- Do not edit files.
- P0/P1 issues block merge.
- Do not approve without evidence.
