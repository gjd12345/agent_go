"""Deprecated compatibility shim. Use `eoh_rag` instead.

The `eoh_go` package name is from the earlier InsertShips/Go phase.
Current mainline is EOH-RAG (Trace-Conditioned Small-Model Controllers).
All active code is now in `eoh_rag/`.
"""
import warnings
warnings.warn(
    "eoh_go is deprecated, use eoh_rag instead",
    DeprecationWarning,
    stacklevel=2,
)
from eoh_rag import *  # noqa: F401,F403
