from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eoh_go.experiments.summarize_manifest_runs import _write_markdown


class SummarizeManifestRunsTests(unittest.TestCase):
    def test_markdown_summary_table_has_matching_column_count(self) -> None:
        summary = {
            "suite": "test_suite",
            "problems": {
                "tsp_construct": [
                    {
                        "arm": "pure_eoh",
                        "gen": 0,
                        "pop": 4,
                        "best": 6.5,
                        "valid": "4/4",
                        "cards": [],
                        "status": "ok",
                    }
                ]
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "summary.md"
            _write_markdown(summary, str(output))
            lines = output.read_text(encoding="utf-8").splitlines()

        header = next(line for line in lines if line.startswith("| problem |"))
        separator = lines[lines.index(header) + 1]
        self.assertEqual(header.count("|"), separator.count("|"))


if __name__ == "__main__":
    unittest.main()
