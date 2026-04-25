from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EOHGoPaths:
    root: Path

    @property
    def workspace(self) -> Path:
        return self.root / "eoh_go_workspace"

    @property
    def candidates_dir(self) -> Path:
        return self.workspace / "candidates"

    @property
    def runs_dir(self) -> Path:
        return self.workspace / "runs"

    @property
    def memory_dir(self) -> Path:
        return self.workspace / "memory"

    @property
    def reports_dir(self) -> Path:
        return self.workspace / "reports"

    @property
    def report_tables_dir(self) -> Path:
        return self.reports_dir / "tables"

    @property
    def report_probes_dir(self) -> Path:
        return self.reports_dir / "probes"

    @property
    def report_summaries_dir(self) -> Path:
        return self.reports_dir / "summaries"

    @property
    def generated_dir(self) -> Path:
        return self.workspace / "generated"

    @property
    def generated_projects_dir(self) -> Path:
        return self.generated_dir / "projects"

    @property
    def generated_bins_dir(self) -> Path:
        return self.generated_dir / "bins"

    @property
    def generated_reports_dir(self) -> Path:
        return self.generated_dir / "reports"

    @property
    def plan_path(self) -> Path:
        return self.memory_dir / "PLAN.md"

    @property
    def memory_path(self) -> Path:
        return self.memory_dir / "MEMORY.md"

    @property
    def research_notes_path(self) -> Path:
        return self.memory_dir / "research_notes.md"

    @property
    def registry_path(self) -> Path:
        return self.workspace / "candidate_registry.json"

    @property
    def run_index_path(self) -> Path:
        return self.runs_dir / "run_index.json"


def ensure_workspace(paths: EOHGoPaths) -> None:
    for path in [
        paths.workspace,
        paths.candidates_dir,
        paths.runs_dir,
        paths.memory_dir,
        paths.reports_dir,
        paths.report_tables_dir,
        paths.report_probes_dir,
        paths.report_summaries_dir,
        paths.generated_dir,
        paths.generated_projects_dir,
        paths.generated_bins_dir,
        paths.generated_reports_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
