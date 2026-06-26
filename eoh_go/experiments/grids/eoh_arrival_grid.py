"""Backward-compat shim — renamed to arrival_scale_grid.py."""
from eoh_go.experiments.grids.arrival_scale_grid import *  # noqa: F401,F403
from eoh_go.experiments.grids.arrival_scale_grid import main

if __name__ == "__main__":
    main()
