from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from ..strategy_router import route_instance


DEFAULT_DENSITY_DIRS = {
    "d25": "solomon_benchmark_d25",
    "d50": "solomon_benchmark_d50",
    "d75": "solomon_benchmark_d75",
    "d100": "solomon_benchmark",
}


def build_markdown(rows: list[dict]) -> str:
    lines = [
        "| Inst. | d | t | n total | n max | density | avg window | tightness | difficulty | route |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        feat = row["features"]
        lines.append(
            "| "
            + " | ".join(
                [
                    row["problem"].replace(".json", "").upper(),
                    row["density"],
                    str(row["time_interval"]),
                    str(feat["request_count"]),
                    str(feat["max_batch_request_count"]),
                    f"{feat['density_ratio']:.2f}",
                    f"{feat['avg_window_width']:.1f}",
                    f"{feat['time_tightness']:.2f}",
                    f"{feat['difficulty']:.2f}",
                    row["family"],
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def run_probe(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    out_base = (root / args.output_dir).resolve()
    out_dir = out_base / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    out_dir.mkdir(parents=True, exist_ok=False)

    problems = args.problem or [f"rc10{i}.json" for i in range(1, 9)]
    densities = args.density or ["d25", "d50", "d75", "d100"]
    intervals = args.time_interval or [1, 2]

    rows = []
    for density in densities:
        ds_dir = root / DEFAULT_DENSITY_DIRS[density]
        for interval in intervals:
            for problem in problems:
                result = route_instance(
                    ds_dir / problem,
                    full_request_count=args.full_request_count,
                    time_interval=interval,
                )
                rows.append(
                    {
                        "problem": problem,
                        "density": density,
                        "time_interval": interval,
                        "family": result["family"],
                        "features": result["features"],
                    }
                )

    payload = {
        "output_dir": str(out_dir),
        "rule": "t>=2 -> robust; density<=0.35 -> fast; density<=0.65 -> balanced; else robust",
        "rows": rows,
    }
    (out_dir / "router_probe.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "router_probe.md").write_text(build_markdown(rows), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe density-aware strategy routing.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/probes/router")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append", choices=list(DEFAULT_DENSITY_DIRS))
    parser.add_argument("--time-interval", action="append", type=int)
    parser.add_argument("--full-request-count", type=int, default=15)
    args = parser.parse_args()
    payload = run_probe(args)
    print(build_markdown(payload["rows"]))
    print(f"Wrote router probe to {payload['output_dir']}")


if __name__ == "__main__":
    main()
