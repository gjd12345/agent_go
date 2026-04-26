from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
        "axes.edgecolor": "#222222",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#E5E5E5",
        "grid.linewidth": 0.55,
        "grid.alpha": 1.0,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.edgecolor": "white",
    }
)

COLORS = {
    "improved": "#2E8B57",
    "tie": "#8A8A8A",
    "worse": "#C44E52",
    "excluded": "#4B4B4B",
}


def _ensure_problem(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["inst"] = out["problem"].str.replace(".json", "", regex=False).str.upper()
    out["cell"] = out["inst"] + "," + out["density"] + ",t=" + out["arrival_scale"].astype(str)
    out["delta_res"] = out["best_EOH_Res"] - out["seed_Res"]
    out["eoh_j_ratio"] = out["best_EOH_J"] / out["seed_J"]
    return out


def _save(fig: plt.Figure, out_path: Path) -> None:
    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), format="pdf", bbox_inches="tight")
    plt.close(fig)


def _bar_labels(ax, values, fmt="{:.0f}") -> None:
    for idx, value in enumerate(values):
        ax.text(idx, value, fmt.format(value), ha="center", va="bottom", fontsize=8)


def plot_outcome_counts(df: pd.DataFrame, out_dir: Path) -> None:
    order = ["improved", "tie", "worse"]
    counts = df["clean_class"].value_counts().reindex(order, fill_value=0)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(order, counts.values, color=[COLORS[x] for x in order])
    ax.set_title("Valid SA vs EOH Outcomes")
    ax.set_ylabel("Number of valid cells")
    _bar_labels(ax, counts.values)
    _save(fig, out_dir / "01_outcome_counts.svg")


def plot_outcome_by_density(df: pd.DataFrame, out_dir: Path) -> None:
    densities = sorted(df["density"].unique(), key=lambda x: int(x.replace("d", "")))
    classes = ["improved", "tie", "worse"]
    table = (
        df.groupby(["density", "clean_class"]).size().unstack(fill_value=0).reindex(densities).reindex(columns=classes, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bottom = np.zeros(len(table))
    for cls in classes:
        vals = table[cls].to_numpy()
        ax.bar(table.index, vals, bottom=bottom, color=COLORS[cls], label=cls)
        bottom += vals
    ax.set_title("Outcome Counts by Density")
    ax.set_ylabel("Valid cells")
    ax.legend(frameon=False, ncol=3)
    _save(fig, out_dir / "02_outcome_by_density.svg")


def plot_delta_by_density(df: pd.DataFrame, out_dir: Path) -> None:
    densities = sorted(df["density"].unique(), key=lambda x: int(x.replace("d", "")))
    agg = df.groupby("density")["delta_J"].agg(["mean", "median", "count"]).reindex(densities)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = [COLORS["improved"] if v < 0 else COLORS["worse"] if v > 0 else COLORS["tie"] for v in agg["mean"]]
    ax.bar(agg.index, agg["mean"], color=colors)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.set_title("Mean Delta J by Density (EOH - SA)")
    ax.set_ylabel("Mean Delta J")
    for i, (density, row) in enumerate(agg.iterrows()):
        ax.text(i, row["mean"], f"n={int(row['count'])}", ha="center", va="bottom" if row["mean"] >= 0 else "top", fontsize=8)
    _save(fig, out_dir / "03_mean_delta_by_density.svg")


def plot_delta_heatmap_all(df: pd.DataFrame, out_dir: Path) -> None:
    tmp = df.copy()
    tmp["row"] = tmp["inst"] + " " + tmp["density"]
    row_order = sorted(tmp["row"].unique(), key=lambda r: (r.split()[0], int(r.split()[1].replace("d", ""))))
    col_order = sorted(tmp["arrival_scale"].unique(), reverse=True)
    pivot = tmp.pivot_table(index="row", columns="arrival_scale", values="delta_J", aggfunc="first").reindex(row_order)
    pivot = pivot.reindex(columns=col_order)

    fig, ax = plt.subplots(figsize=(8.5, max(4, 0.36 * len(row_order))))
    max_abs = np.nanmax(np.abs(pivot.to_numpy())) if not pivot.empty else 1
    max_abs = max(max_abs, 1)
    im = ax.imshow(pivot.to_numpy(), cmap="RdYlGn_r", vmin=-max_abs, vmax=max_abs, aspect="auto")
    ax.set_title("Delta J Heatmap for Valid Cells (EOH - SA)")
    ax.set_xticks(range(len(col_order)), [f"t={x:g}" for x in col_order])
    ax.set_yticks(range(len(row_order)), row_order)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.iat[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=7, color="#111111")
    fig.colorbar(im, ax=ax, label="Delta J")
    _save(fig, out_dir / "04_delta_j_heatmap_all_valid.svg")


def plot_per_instance_heatmaps(df: pd.DataFrame, out_dir: Path) -> list[str]:
    names: list[str] = []
    scales = sorted(df["arrival_scale"].unique(), reverse=True)
    densities = sorted(df["density"].unique(), key=lambda x: int(x.replace("d", "")))
    max_abs = np.nanmax(np.abs(df["delta_J"].to_numpy()))
    max_abs = max(max_abs, 1)
    for inst in sorted(df["inst"].unique()):
        sub = df[df["inst"] == inst]
        pivot = sub.pivot_table(index="density", columns="arrival_scale", values="delta_J", aggfunc="first").reindex(densities)
        pivot = pivot.reindex(columns=scales)
        fig, ax = plt.subplots(figsize=(7, 3.4))
        im = ax.imshow(pivot.to_numpy(), cmap="RdYlGn_r", vmin=-max_abs, vmax=max_abs, aspect="auto")
        ax.set_title(f"{inst}: Delta J by Density and Arrival Scale")
        ax.set_xticks(range(len(scales)), [f"t={x:g}" for x in scales])
        ax.set_yticks(range(len(densities)), densities)
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                val = pivot.iat[i, j]
                if pd.notna(val):
                    ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=8, color="#111111")
                else:
                    ax.text(j, i, "-", ha="center", va="center", fontsize=8, color="#777777")
        fig.colorbar(im, ax=ax, label="Delta J")
        name = f"05_delta_j_heatmap_{inst.lower()}.svg"
        names.append(name)
        _save(fig, out_dir / name)
    return names


def plot_scatter(df: pd.DataFrame, out_dir: Path, x: str, y: str, title: str, filename: str, label: str) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    for cls, sub in df.groupby("clean_class"):
        ax.scatter(sub[x], sub[y], label=cls, color=COLORS.get(cls, "#333333"), alpha=0.8, edgecolor="white", linewidth=0.6)
    lo = min(df[x].min(), df[y].min())
    hi = max(df[x].max(), df[y].max())
    ax.plot([lo, hi], [lo, hi], "--", color="#444444", linewidth=1, label="SA = EOH")
    ax.set_title(title)
    ax.set_xlabel(f"SA {label}")
    ax.set_ylabel(f"EOH {label}")
    ax.legend(frameon=False)
    _save(fig, out_dir / filename)


def plot_sorted_delta(df: pd.DataFrame, out_dir: Path) -> None:
    ordered = df.sort_values("delta_J")
    fig, ax = plt.subplots(figsize=(10, max(5, 0.18 * len(ordered))))
    colors = [COLORS[x] for x in ordered["clean_class"]]
    y = np.arange(len(ordered))
    ax.barh(y, ordered["delta_J"], color=colors)
    ax.axvline(0, color="#222222", linewidth=1)
    ax.set_yticks(y, ordered["cell"], fontsize=7)
    ax.set_title("All Valid Cells Sorted by Delta J")
    ax.set_xlabel("Delta J (EOH - SA)")
    _save(fig, out_dir / "08_sorted_delta_j_all_valid.svg")


def plot_tradeoff(df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5.2))
    for cls, sub in df.groupby("clean_class"):
        ax.scatter(sub["delta_res"], sub["delta_J"], color=COLORS.get(cls, "#333333"), label=cls, alpha=0.82, edgecolor="white", linewidth=0.6)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.axvline(0, color="#222222", linewidth=1)
    ax.set_title("Quality-Time Tradeoff for Valid Cells")
    ax.set_xlabel("Delta Res. (EOH - SA)")
    ax.set_ylabel("Delta J (EOH - SA)")
    ax.legend(frameon=False)
    _save(fig, out_dir / "09_quality_time_tradeoff.svg")


def plot_valid_candidates(df: pd.DataFrame, out_dir: Path) -> None:
    tmp = df.copy()
    tmp["valid_candidates"] = pd.to_numeric(tmp["valid_candidates"], errors="coerce")
    agg = tmp.groupby(["density", "clean_class"])["valid_candidates"].mean().unstack(fill_value=np.nan)
    densities = sorted(tmp["density"].unique(), key=lambda x: int(x.replace("d", "")))
    agg = agg.reindex(densities)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(agg.index))
    width = 0.25
    for idx, cls in enumerate(["improved", "tie", "worse"]):
        vals = agg[cls] if cls in agg else np.zeros(len(agg))
        ax.bar(x + (idx - 1) * width, vals, width=width, color=COLORS[cls], label=cls)
    ax.set_xticks(x, agg.index)
    ax.set_title("Mean Valid Candidate Count by Outcome")
    ax.set_ylabel("Mean valid candidates")
    ax.legend(frameon=False, ncol=3)
    _save(fig, out_dir / "10_valid_candidates_by_outcome.svg")


def plot_repeat_validation(repeat_csv: Path, out_dir: Path) -> bool:
    if not repeat_csv.exists():
        return False
    repeat = pd.read_csv(repeat_csv)
    if repeat.empty:
        return False
    repeat["inst"] = repeat["problem"].str.replace(".json", "", regex=False).str.upper()
    repeat["cell"] = repeat["inst"] + "," + repeat["density"] + ",t=" + repeat["arrival_scale"].astype(str)
    repeat = repeat.sort_values("mean_delta_J")
    fig, ax = plt.subplots(figsize=(9, max(4.5, 0.38 * len(repeat))))
    y = np.arange(len(repeat))
    ax.barh(y - 0.16, repeat["mean_delta_J"], height=0.3, label="mean Delta J", color="#4C78A8")
    ax.barh(y + 0.16, repeat["best_delta_J"], height=0.3, label="best Delta J", color="#F58518")
    ax.axvline(0, color="#222222", linewidth=1)
    ax.set_yticks(y, repeat["cell"], fontsize=8)
    ax.set_title("Selected Repeat Validation")
    ax.set_xlabel("Delta J (EOH - SA)")
    ax.legend(frameon=False)
    _save(fig, out_dir / "11_repeat_validation_delta_j.svg")
    return True


def write_index(df: pd.DataFrame, out_dir: Path, chart_names: list[str]) -> None:
    counts = df["clean_class"].value_counts().reindex(["improved", "tie", "worse"], fill_value=0)
    lines = [
        "# Valid SA vs EOH Comparison Charts",
        "",
        f"Valid cells: {len(df)}",
        f"Improved: {counts['improved']}; Tie: {counts['tie']}; Worse: {counts['worse']}",
        "",
        "All charts use cleaned valid comparisons only. `Delta J = EOH J - SA J`; negative values mean EOH is better.",
        "",
    ]
    for name in chart_names:
        title = name.replace(".svg", "").replace("_", " ")
        lines.extend([f"## {title}", "", f"![]({name})", ""])
    (out_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--valid-csv",
        default="eoh_go_workspace/reports/tables/eoh_grid_cleaned_summary_rc101_105/clean_valid_comparisons.csv",
    )
    parser.add_argument(
        "--repeat-csv",
        default="eoh_go_workspace/reports/tables/eoh_selected_repeats_summary_20260426/selected_repeat_summary.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="eoh_go_workspace/reports/figures/valid_comparison_charts_20260426",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    valid_csv = root / args.valid_csv
    repeat_csv = root / args.repeat_csv
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    df = _ensure_problem(pd.read_csv(valid_csv))
    df.to_csv(out_dir / "valid_comparison_chart_data.csv", index=False)

    chart_names: list[str] = []
    plot_outcome_counts(df, out_dir)
    chart_names.append("01_outcome_counts.svg")
    plot_outcome_by_density(df, out_dir)
    chart_names.append("02_outcome_by_density.svg")
    plot_delta_by_density(df, out_dir)
    chart_names.append("03_mean_delta_by_density.svg")
    plot_delta_heatmap_all(df, out_dir)
    chart_names.append("04_delta_j_heatmap_all_valid.svg")
    chart_names.extend(plot_per_instance_heatmaps(df, out_dir))
    plot_scatter(df, out_dir, "seed_J", "best_EOH_J", "SA vs EOH Final Cost J", "06_sa_vs_eoh_j_scatter.svg", "J")
    chart_names.append("06_sa_vs_eoh_j_scatter.svg")
    plot_scatter(df, out_dir, "seed_Res", "best_EOH_Res", "SA vs EOH Response Time", "07_sa_vs_eoh_res_scatter.svg", "Res.")
    chart_names.append("07_sa_vs_eoh_res_scatter.svg")
    plot_sorted_delta(df, out_dir)
    chart_names.append("08_sorted_delta_j_all_valid.svg")
    plot_tradeoff(df, out_dir)
    chart_names.append("09_quality_time_tradeoff.svg")
    plot_valid_candidates(df, out_dir)
    chart_names.append("10_valid_candidates_by_outcome.svg")
    if plot_repeat_validation(repeat_csv, out_dir):
        chart_names.append("11_repeat_validation_delta_j.svg")

    summary = (
        df.groupby(["density", "clean_class"]).size().unstack(fill_value=0).reset_index()
    )
    summary.to_csv(out_dir / "valid_outcome_summary_by_density.csv", index=False)
    write_index(df, out_dir, chart_names)
    print(
        {
            "out_dir": str(out_dir),
            "valid_cells": len(df),
            "charts": chart_names,
        }
    )


if __name__ == "__main__":
    main()
