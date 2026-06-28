---
name: related-work-writer
description: Use when drafting TOCC-RAG related work or positioning. Trigger for EoH, FunSearch, AlphaEvolve, Reflexion, PaperQA, Agent Laboratory, AFlow, AI Scientist, RAG surveys, or questions about how TOCC-RAG fits the literature.
---

# TOCC-RAG Related Work Writer

Use this to turn literature notes into project positioning.

## Buckets

Organize related work into:

```text
LLM-guided evolutionary algorithm design
automated scientific discovery agents
retrieval and memory for scientific / agent systems
agent workflow optimization
TOCC-RAG position
```

## Priority Sources

Start with:

```text
EoH
FunSearch
EoH-S
AlphaEvolve
Reflexion
PaperQA
Agent Laboratory
AFlow
AI Scientist
```

Browse or verify sources before giving precise paper claims, citations, dates, or URLs.

## Positioning

Keep this distinction:

```text
TOCC-RAG does not replace EoH.
TOCC-RAG adds a trace-conditioned card selection and rerank controller.
```

Core chain:

```text
candidate_card_ids
  -> keyword retrieve
  -> outcome/population rerank
  -> final injected cards
  -> trace/outcome feedback
```

## Output

Return:

```text
paragraph draft
paper-to-module mapping
what to borrow
what not to copy
claims requiring citation
```
