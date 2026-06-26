from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _fmt_res(value: float) -> str:
    return f"{value:.3f}"


def _fmt_j(value: float, star: bool = False) -> str:
    text = f"{value:.2f}"
    return f"{text}*" if star else text


def _fmt_delta(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}"


def build_table(valid_csv: Path, out_dir: Path, *, max_rows: int | None = None) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(valid_csv)
    df["inst"] = df["problem"].str.replace(".json", "", regex=False).str.upper()
    density_order = {"d25": 25, "d50": 50, "d75": 75, "d100": 100}
    df["_density_order"] = df["density"].map(density_order).fillna(999)
    df = df.sort_values(["inst", "_density_order", "arrival_scale"], ascending=[True, True, False])
    if max_rows is not None:
        df = df.head(max_rows)

    rows: list[list[str]] = []
    row_classes: list[str] = []
    for _, row in df.iterrows():
        delta = float(row["delta_J"])
        sa_best = delta >= 0
        eoh_best = delta <= 0
        rows.append(
            [
                row["inst"],
                row["density"],
                f"{float(row['arrival_scale']):.1f}",
                _fmt_res(float(row["seed_Res"])),
                _fmt_j(float(row["seed_J"]), star=sa_best),
                _fmt_res(float(row["best_EOH_Res"])),
                _fmt_j(float(row["best_EOH_J"]), star=eoh_best),
                _fmt_delta(delta),
                str(row["clean_class"]),
            ]
        )
        row_classes.append(str(row["clean_class"]))

    n = len(rows)
    fig_w = 13.2
    fig_h = max(8.0, 1.15 + 0.245 * n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    left, right = 0.035, 0.985
    top = 0.965
    bottom = 0.055
    title_y = top - 0.035
    header_group_y = top - 0.092
    header_sub_y = top - 0.135
    rule_top_y = top - 0.07
    rule_mid_y = top - 0.162
    note_y = 0.021

    # Blue double rule, matching the visual style of the reference screenshot.
    ax.plot([0, 1], [0.994, 0.994], color="#0000cc", linewidth=2.4, clip_on=False)
    ax.plot([0, 1], [0.987, 0.987], color="#0000cc", linewidth=1.2, clip_on=False)

    ax.text(
        left,
        title_y,
        r"$\bf{Table\ 1}$  Performance of SA and Guarded EOH on valid dynamic-dispatch cells",
        fontsize=15.5,
        fontfamily="serif",
        va="center",
    )

    # Column layout. Values are relative axis coordinates.
    col_edges = [
        left,
        0.132,
        0.188,
        0.242,
        0.325,
        0.425,
        0.515,
        0.615,
        0.730,
        right,
    ]
    col_centers = [(col_edges[i] + col_edges[i + 1]) / 2 for i in range(len(col_edges) - 1)]

    # Booktabs-like rules.
    ax.plot([left, right], [rule_top_y, rule_top_y], color="#111111", linewidth=1.3)
    ax.plot([left, right], [rule_mid_y, rule_mid_y], color="#111111", linewidth=0.95)

    # Group headers and cmidrules.
    ax.text(col_centers[0], header_group_y, "Instance", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[1], header_group_y, "d", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[2], header_group_y, "t", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text((col_edges[3] + col_edges[5]) / 2, header_group_y, "SA", ha="center", va="center", fontsize=14, fontfamily="serif")
    ax.text((col_edges[5] + col_edges[7]) / 2, header_group_y, "Guarded EOH", ha="center", va="center", fontsize=14, fontfamily="serif")
    ax.text(col_centers[7], header_group_y, r"$\Delta J$", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[8], header_group_y, "Outcome", ha="center", va="center", fontsize=13, fontfamily="serif")

    for a, b in [(3, 5), (5, 7)]:
        ax.plot([col_edges[a] + 0.008, col_edges[b] - 0.008], [header_group_y - 0.026, header_group_y - 0.026], color="#777777", linewidth=0.9)

    subheaders = ["", "", "", "Res.", r"$J$", "Res.", r"$J$", "", ""]
    for i, label in enumerate(subheaders):
        if label:
            ax.text(col_centers[i], header_sub_y, label, ha="center", va="center", fontsize=12.5, fontfamily="serif")

    row_top = rule_mid_y - 0.022
    row_bottom = bottom + 0.045
    row_h = (row_top - row_bottom) / max(n, 1)
    outcome_color = {"improved": "#2E8B57", "tie": "#666666", "worse": "#B23B3B"}
    delta_color = {"improved": "#2E8B57", "tie": "#444444", "worse": "#B23B3B"}

    for r, values in enumerate(rows):
        y = row_top - (r + 0.5) * row_h
        if r % 2 == 1:
            ax.add_patch(
                plt.Rectangle(
                    (left, y - row_h / 2),
                    right - left,
                    row_h,
                    facecolor="#F7F7F7",
                    edgecolor="none",
                    zorder=-1,
                )
            )
        cls = row_classes[r]
        for c, value in enumerate(values):
            ha = "left" if c == 0 else "center"
            x = col_edges[c] + 0.006 if c == 0 else col_centers[c]
            color = "#111111"
            weight = "normal"
            if c == 7:
                color = delta_color.get(cls, "#111111")
                weight = "bold"
            if c == 8:
                color = outcome_color.get(cls, "#111111")
                weight = "bold"
            if c in (4, 6) and value.endswith("*"):
                weight = "bold"
            ax.text(x, y, value, ha=ha, va="center", fontsize=9.2, fontfamily="serif", color=color, fontweight=weight)

    final_rule_y = row_bottom
    ax.plot([left, right], [final_rule_y, final_rule_y], color="#111111", linewidth=1.0)
    ax.plot([left, right], [note_y + 0.026, note_y + 0.026], color="#111111", linewidth=1.2)
    ax.text(
        left,
        note_y,
        "Note: Only cleaned valid cells are shown. * marks the lower J in each row. "
        "Delta J = EOH J - SA J; negative values indicate improvement by EOH.",
        fontsize=10.5,
        fontfamily="serif",
        va="bottom",
    )

    stem = "table3_valid_sa_eoh_comparison"
    svg = out_dir / f"{stem}.svg"
    png = out_dir / f"{stem}.png"
    pdf = out_dir / f"{stem}.pdf"
    fig.savefig(svg, format="svg", bbox_inches="tight")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    fig.savefig(pdf, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return {"svg": str(svg), "png": str(png), "pdf": str(pdf), "rows": str(n)}


def build_repeat_table(repeat_csv: Path, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(repeat_csv)
    df["inst"] = df["problem"].str.replace(".json", "", regex=False).str.upper()
    density_order = {"d25": 25, "d50": 50, "d75": 75, "d100": 100}
    df["_density_order"] = df["density"].map(density_order).fillna(999)
    df = df.sort_values(["inst", "_density_order", "arrival_scale"], ascending=[True, True, False])

    rows: list[list[str]] = []
    classes: list[str] = []
    for _, row in df.iterrows():
        mean_delta = float(row["mean_delta_J"])
        if int(row["improved"]) > 0 and mean_delta < 0:
            cls = "improved"
        elif int(row["worse"]) > 0 and mean_delta > 0:
            cls = "worse"
        else:
            cls = "tie"
        classes.append(cls)
        rows.append(
            [
                row["inst"],
                row["density"],
                f"{float(row['arrival_scale']):.1f}",
                str(int(row["runs"])),
                str(int(row["improved"])),
                str(int(row["tie"])),
                str(int(row["worse"])),
                str(int(row["excluded"])),
                _fmt_delta(mean_delta),
                _fmt_delta(float(row["best_delta_J"])),
            ]
        )

    n = len(rows)
    fig_w = 12.5
    fig_h = max(4.7, 1.28 + 0.36 * n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    left, right = 0.04, 0.985
    top = 0.965
    bottom = 0.085
    title_y = top - 0.05
    header_group_y = top - 0.135
    header_sub_y = top - 0.192
    rule_top_y = top - 0.095
    rule_mid_y = top - 0.226
    note_y = 0.028

    ax.plot([0, 1], [0.994, 0.994], color="#0000cc", linewidth=2.4, clip_on=False)
    ax.plot([0, 1], [0.987, 0.987], color="#0000cc", linewidth=1.2, clip_on=False)
    ax.text(
        left,
        title_y,
        r"$\bf{Table\ 2}$  Repeat validation of selected Guarded EOH cells",
        fontsize=15.5,
        fontfamily="serif",
        va="center",
    )

    col_edges = [
        left,
        0.145,
        0.205,
        0.265,
        0.335,
        0.420,
        0.500,
        0.585,
        0.685,
        0.835,
        right,
    ]
    col_centers = [(col_edges[i] + col_edges[i + 1]) / 2 for i in range(len(col_edges) - 1)]

    ax.plot([left, right], [rule_top_y, rule_top_y], color="#111111", linewidth=1.3)
    ax.plot([left, right], [rule_mid_y, rule_mid_y], color="#111111", linewidth=0.95)

    ax.text(col_centers[0], header_group_y, "Instance", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[1], header_group_y, "d", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[2], header_group_y, "t", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text(col_centers[3], header_group_y, "Runs", ha="center", va="center", fontsize=13, fontfamily="serif")
    ax.text((col_edges[4] + col_edges[8]) / 2, header_group_y, "Outcome counts", ha="center", va="center", fontsize=14, fontfamily="serif")
    ax.text((col_edges[8] + col_edges[10]) / 2, header_group_y, r"$\Delta J$ over repeats", ha="center", va="center", fontsize=14, fontfamily="serif")
    for a, b in [(4, 8), (8, 10)]:
        ax.plot([col_edges[a] + 0.008, col_edges[b] - 0.008], [header_group_y - 0.032, header_group_y - 0.032], color="#777777", linewidth=0.9)

    subheaders = ["", "", "", "", "Imp.", "Tie", "Worse", "Excl.", "Mean", "Best"]
    for i, label in enumerate(subheaders):
        if label:
            ax.text(col_centers[i], header_sub_y, label, ha="center", va="center", fontsize=12.5, fontfamily="serif")

    row_top = rule_mid_y - 0.035
    row_bottom = bottom + 0.055
    row_h = (row_top - row_bottom) / max(n, 1)
    outcome_color = {"improved": "#2E8B57", "tie": "#666666", "worse": "#B23B3B"}
    for r, values in enumerate(rows):
        y = row_top - (r + 0.5) * row_h
        if r % 2 == 1:
            ax.add_patch(
                plt.Rectangle((left, y - row_h / 2), right - left, row_h, facecolor="#F7F7F7", edgecolor="none", zorder=-1)
            )
        cls = classes[r]
        for c, value in enumerate(values):
            ha = "left" if c == 0 else "center"
            x = col_edges[c] + 0.006 if c == 0 else col_centers[c]
            color = "#111111"
            weight = "normal"
            if c in (8, 9):
                color = outcome_color.get(cls, "#111111") if c == 8 else "#111111"
                weight = "bold"
            if c == 4 and int(value) > 0:
                color, weight = "#2E8B57", "bold"
            if c == 6 and int(value) > 0:
                color, weight = "#B23B3B", "bold"
            ax.text(x, y, value, ha=ha, va="center", fontsize=11, fontfamily="serif", color=color, fontweight=weight)

    ax.plot([left, right], [row_bottom, row_bottom], color="#111111", linewidth=1.0)
    ax.plot([left, right], [note_y + 0.031, note_y + 0.031], color="#111111", linewidth=1.2)
    ax.text(
        left,
        note_y,
        "Note: Repeat data are reruns of selected cells from the cleaned main grid. "
        "Mean and Best use Delta J = EOH J - SA J; negative values favor EOH.",
        fontsize=10.5,
        fontfamily="serif",
        va="bottom",
    )

    stem = "table4_repeat_validation"
    svg = out_dir / f"{stem}.svg"
    png = out_dir / f"{stem}.png"
    pdf = out_dir / f"{stem}.pdf"
    fig.savefig(svg, format="svg", bbox_inches="tight")
    fig.savefig(png, dpi=240, bbox_inches="tight")
    fig.savefig(pdf, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return {"svg": str(svg), "png": str(png), "pdf": str(pdf), "rows": str(n)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--valid-csv",
        default="eoh_go_workspace/reports/tables/eoh_grid_cleaned_summary_rc101_105/clean_valid_comparisons.csv",
    )
    parser.add_argument("--out-dir", default="eoh_go_workspace/reports/figures/paper_style_tables_20260426")
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument(
        "--repeat-csv",
        default="eoh_go_workspace/reports/tables/eoh_selected_repeats_summary_20260426/selected_repeat_summary.csv",
    )
    parser.add_argument("--repeat-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.repeat_only:
        result = build_repeat_table(root / args.repeat_csv, root / args.out_dir)
    else:
        result = build_table(root / args.valid_csv, root / args.out_dir, max_rows=args.max_rows)
    print(result)


if __name__ == "__main__":
    main()
