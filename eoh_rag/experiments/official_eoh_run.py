"""Backward-compat shim — renamed to eoh_single_runner.py."""
from eoh_rag.experiments.eoh_single_runner import *  # noqa: F401,F403
from eoh_rag.experiments.eoh_single_runner import main

if __name__ == "__main__":
    main()
