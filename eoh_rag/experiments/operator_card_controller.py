"""Backward-compatibility shim — actual implementation in eoh_rag.tocc.controller.

This file was moved to eoh_go/tocc/controller.py during P3 refactoring.
Re-exported here so that AGENTS.md / SKILL.md references and any external
scripts that import from this path continue to work.
"""
from eoh_rag.tocc.controller import *  # noqa: F401,F403
from eoh_rag.tocc.controller import OperatorCardController  # noqa: F401
