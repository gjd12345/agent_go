"""Backward-compat shim — renamed to batch_runner.py."""
from eoh_go.experiments.batch_runner import *  # noqa: F401,F403
from eoh_go.experiments.batch_runner import main

if __name__ == "__main__":
    main()
