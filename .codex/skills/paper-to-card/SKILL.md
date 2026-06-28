---
name: paper-to-card
description: Use when converting a paper, abstract, PDF notes, arXiv link, or method summary into TOCC-RAG algorithm cards. Trigger for paper-to-card, strategy-card drafting, literature-to-RAG corpus, or extracting optimization ideas for EOH.
---

# Paper To Strategy Card

Turn research text into grounded TOCC-RAG card drafts.

## Input

Accept:

```text
paper title
abstract
PDF text
arXiv link
reading notes
method excerpt
```

Browse or inspect source material when the paper or URL is not already provided in full.

## Extract

Identify:

```text
method idea
problem family
strategy features
expected benefit: depth | breadth | robustness | validity
implementation risk
failure modes
what not to copy
provenance / citation note
```

## Card Draft Shape

Use this JSONL-compatible shape:

```json
{
  "id": "paper_short_method_name",
  "kind": "algorithm_card",
  "title": "Readable Strategy Name",
  "tags": ["regret", "population", "diversity"],
  "summary": "One or two evidence-backed sentences.",
  "constraints": "Where this idea should and should not be used.",
  "content": "Do: ...\nAvoid: ...\nUseful for: ..."
}
```

## Guardrails

- Do not invent paper claims.
- Keep provenance clear enough to trace back to the source.
- Distinguish author claims from TOCC-RAG implementation ideas.
- Prefer canonical strategy features used by `eoh_go.rag.features`.
- Do not add the card to corpus automatically unless the user explicitly asks.

## Output

Return:

```text
card draft
feature tags
applicable problems
expected benefit
risk / anti-patterns
source citation note
```
