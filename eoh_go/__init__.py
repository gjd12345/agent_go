"""EOH-Go experiment framework — Trace-Conditioned Small-Model Controller.

Active modules:
- eoh_go.experiments: batch_runner, eoh_single_runner, rag_context_builder
- eoh_go.rag: retriever, reranker, llm_reranker, card_outcomes, features
- eoh_go.tocc: agent, gatekeeper, pipeline, controller
- eoh_go.llm: client

Legacy modules moved to legacy/insertships_eoh_v0/
"""

from .memory import read_text_file, write_text_file, append_research_note

__all__ = [
    "read_text_file",
    "write_text_file",
    "append_research_note",
]
