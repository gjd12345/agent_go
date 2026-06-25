from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "eoh_go_workspace" / "reports" / "tables" / "eoh_grid_cleaned_summary_rc101_105"
REPEAT_DIR = ROOT / "eoh_go_workspace" / "reports" / "tables" / "eoh_selected_repeats_summary_20260426"
OUT_DIR = ROOT / "eoh_go_workspace" / "reports" / "paper_report_20260426"
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"


STATUS_COLORS = {
    "improved": "#58a55c",
    "tie": "#b8b8b8",
    "worse": "#d95f5f",
    "excluded_no_sa": "#8ea7d8",
    "excluded_no_eoh": "#c69c6d",
    "excluded_suspicious_low": "#a574c7",
    "excluded_negative_eoh": "#4b4b4b",
}

LATEX_COLORS = {
    "improved": "improvedGreen",
    "tie": "tieGray",
    "worse": "worseRed",
    "excluded_no_sa": "excludedBlue",
    "excluded_no_eoh": "excludedBrown",
    "excluded_suspicious_low": "excludedPurple",
    "excluded_negative_eoh": "excludedBlack",
}

STATUS_LABELS = {
    "improved": "I",
    "tie": "T",
    "worse": "W",
    "excluded_no_sa": "Xsa",
    "excluded_no_eoh": "Xe",
    "excluded_suspicious_low": "Xs",
    "excluded_negative_eoh": "Xn",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "--"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _latex_escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.small{font-size:12px}.label{font-size:13px;font-weight:600}.title{font-size:18px;font-weight:700}.cell{stroke:#ffffff;stroke-width:2}</style>",
    ]


def _write_status_heatmap(rows: list[dict[str, Any]]) -> None:
    instances = sorted({str(row["problem"]).replace(".json", "").upper() for row in rows})
    densities = ["d25", "d50", "d75"]
    scales = [1.0, 0.9, 0.8, 0.7, 0.6]
    by_key = {
        (str(row["problem"]).replace(".json", "").upper(), row["density"], float(row["arrival_scale"])): row
        for row in rows
    }
    cell_w, cell_h = 58, 30
    left, top = 78, 70
    panel_gap = 34
    panel_h = 34 + len(densities) * cell_h
    width = left + len(scales) * cell_w + 210
    height = top + len(instances) * panel_h + (len(instances) - 1) * panel_gap + 80
    svg = _svg_header(width, height)
    svg.append('<text x="20" y="32" class="title">Guarded EOH outcomes over density and arrival scale</text>')
    svg.append('<text x="20" y="52" class="small">I=improved, T=tie, W=worse, X*=excluded by guard or missing evaluation</text>')
    legend_x = left + len(scales) * cell_w + 35
    legend_y = top
    for idx, status in enumerate(["improved", "tie", "worse", "excluded_no_sa", "excluded_no_eoh", "excluded_suspicious_low", "excluded_negative_eoh"]):
        y = legend_y + idx * 24
        svg.append(f'<rect x="{legend_x}" y="{y-12}" width="16" height="16" fill="{STATUS_COLORS[status]}"/>')
        svg.append(f'<text x="{legend_x+24}" y="{y+1}" class="small">{STATUS_LABELS[status]}: {status}</text>')
    for inst_i, inst in enumerate(instances):
        y0 = top + inst_i * (panel_h + panel_gap)
        svg.append(f'<text x="20" y="{y0+17}" class="label">{inst}</text>')
        for col, scale in enumerate(scales):
            x = left + col * cell_w
            svg.append(f'<text x="{x+cell_w/2}" y="{y0+17}" text-anchor="middle" class="small">t={scale:.1f}</text>')
        for row_i, density in enumerate(densities):
            y = y0 + 28 + row_i * cell_h
            svg.append(f'<text x="34" y="{y+20}" class="small">{density}</text>')
            for col, scale in enumerate(scales):
                x = left + col * cell_w
                item = by_key.get((inst, density, scale))
                status = item.get("clean_class") if item else "excluded_no_sa"
                label = STATUS_LABELS.get(status, "?")
                color = STATUS_COLORS.get(status, "#dddddd")
                svg.append(f'<rect class="cell" x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}"/>')
                svg.append(f'<text x="{x+cell_w/2}" y="{y+20}" text-anchor="middle" class="small">{label}</text>')
    svg.append("</svg>")
    (FIG_DIR / "status_heatmap.svg").write_text("\n".join(svg), encoding="utf-8")


def _write_count_bar(counts: dict[str, int]) -> None:
    order = ["improved", "tie", "worse", "excluded_no_sa", "excluded_no_eoh", "excluded_suspicious_low", "excluded_negative_eoh"]
    width, height = 820, 360
    left, top, bottom = 70, 60, 70
    plot_h = height - top - bottom
    bar_w, gap = 70, 28
    max_count = max(counts.values()) if counts else 1
    svg = _svg_header(width, height)
    svg.append('<text x="20" y="34" class="title">Outcome counts after guard/filter cleaning</text>')
    svg.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{width-30}" y2="{top+plot_h}" stroke="#222"/>')
    for idx, status in enumerate(order):
        count = counts.get(status, 0)
        h = 0 if max_count == 0 else plot_h * count / max_count
        x = left + idx * (bar_w + gap)
        y = top + plot_h - h
        svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{STATUS_COLORS[status]}"/>')
        svg.append(f'<text x="{x+bar_w/2}" y="{y-8}" text-anchor="middle" class="label">{count}</text>')
        svg.append(f'<text x="{x+bar_w/2}" y="{top+plot_h+20}" text-anchor="middle" class="small">{STATUS_LABELS[status]}</text>')
    svg.append("</svg>")
    (FIG_DIR / "outcome_counts.svg").write_text("\n".join(svg), encoding="utf-8")


def _write_latex_tables(rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], counts: dict[str, int]) -> None:
    improved = sorted([row for row in rows if row["clean_class"] == "improved"], key=lambda row: row["delta_J"])[:12]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Top improved valid EOH cells after guard/filter cleaning. Negative \\(\\Delta J\\) indicates EOH improves over SA.}",
        "\\label{tab:top-improvements}",
        "\\small",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Inst. & Cell & SA J & EOH J & $\\Delta J$ & SA Res. & EOH Res. \\\\",
        "\\midrule",
    ]
    for row in improved:
        inst = str(row["problem"]).replace(".json", "").upper()
        cell = f"{row['density']}, t={float(row['arrival_scale']):.1f}"
        lines.append(
            f"{inst} & {_latex_escape(cell)} & {_fmt(row['seed_J'])} & {_fmt(row['best_EOH_J'])} & {_fmt(row['delta_J'])} & {_fmt(row.get('seed_Res'), 3)} & {_fmt(row.get('best_EOH_Res'), 3)} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLE_DIR / "top_improvements.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Summary by Solomon instance and density. Excluded rows include missing SA/EOH values, negative EOH cost, and suspiciously low EOH values.}",
        "\\label{tab:summary-density}",
        "\\small",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Inst. & Density & Rows & Improved & Tie & Worse & Excluded \\\\",
        "\\midrule",
    ]
    for row in summary_rows:
        lines.append(
            f"{row['inst']} & {row['density']} & {row['rows']} & {row['improved']} & {row['tie']} & {row['worse']} & {row['excluded']} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLE_DIR / "summary_by_density.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Outcome counts over the 75-cell RC101--RC105 grid.}",
        "\\label{tab:outcome-counts}",
        "\\small",
        "\\begin{tabular}{lr}",
        "\\toprule",
        "Outcome & Count \\\\",
        "\\midrule",
    ]
    for key in ["improved", "tie", "worse", "excluded_no_sa", "excluded_no_eoh", "excluded_suspicious_low", "excluded_negative_eoh"]:
        lines.append(f"{_latex_escape(key)} & {counts.get(key, 0)} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLE_DIR / "outcome_counts.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    repeat_csv = REPEAT_DIR / "selected_repeat_summary.csv"
    if repeat_csv.exists():
        with repeat_csv.open(newline="", encoding="utf-8") as handle:
            repeat_rows = list(csv.DictReader(handle))
        lines = [
            "\\begin{table}[t]",
            "\\centering",
            "\\caption{Repeat validation on selected high-value improved cells. Each cell was rerun twice with the same model and guard/filter pipeline.}",
            "\\label{tab:repeat-validation}",
            "\\small",
            "\\begin{tabular}{llrrrrrr}",
            "\\toprule",
            "Inst. & Cell & Runs & Improved & Tie & Worse & Excl. & Mean $\\Delta J$ \\\\",
            "\\midrule",
        ]
        for row in repeat_rows:
            inst = str(row["problem"]).replace(".json", "").upper()
            cell = f"{row['density']}, t={float(row['arrival_scale']):.1f}"
            lines.append(
                f"{inst} & {_latex_escape(cell)} & {row['runs']} & {row['improved']} & {row['tie']} & {row['worse']} & {row['excluded']} & {_fmt(row['mean_delta_J'])} \\\\"
            )
        lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
        (TABLE_DIR / "repeat_validation.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_heatmap_latex(rows: list[dict[str, Any]]) -> None:
    instances = sorted({str(row["problem"]).replace(".json", "").upper() for row in rows})
    densities = ["d25", "d50", "d75"]
    scales = [1.0, 0.9, 0.8, 0.7, 0.6]
    by_key = {
        (str(row["problem"]).replace(".json", "").upper(), row["density"], float(row["arrival_scale"])): row
        for row in rows
    }
    lines = [
        "\\begin{figure}[p]",
        "\\centering",
        "\\caption{Density--arrival-scale outcome map. I=improved, T=tie, W=worse, Xsa=missing SA, Xe=missing EOH, Xs=suspicious low EOH, Xn=negative EOH.}",
        "\\label{fig:status-heatmap}",
        "\\scriptsize",
    ]
    for inst in instances:
        lines.append(f"\\textbf{{{inst}}}\\\\[-0.4em]")
        lines.append("\\begin{tabular}{lccccc}")
        lines.append("\\toprule")
        lines.append("d/t & 1.0 & 0.9 & 0.8 & 0.7 & 0.6 \\\\")
        lines.append("\\midrule")
        for density in densities:
            cells = []
            for scale in scales:
                status = by_key[(inst, density, scale)]["clean_class"]
                color = LATEX_COLORS.get(status, "white")
                label = STATUS_LABELS.get(status, "?")
                text_color = "white" if status == "excluded_negative_eoh" else "black"
                cells.append(f"\\cellcolor{{{color}}}\\textcolor{{{text_color}}}{{{label}}}")
            lines.append(f"{density} & " + " & ".join(cells) + " \\\\")
        lines.append("\\bottomrule")
        lines.append("\\end{tabular}\\\\[0.8em]")
    lines.append("\\end{figure}")
    (FIG_DIR / "status_heatmap_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_report(rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], counts: dict[str, int]) -> None:
    total = len(rows)
    valid = sum(counts.get(k, 0) for k in ["improved", "tie", "worse"])
    excluded = total - valid
    report = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{xcolor}}
\usepackage{{colortbl}}
\usepackage{{graphicx}}
\usepackage{{hyperref}}
\usepackage{{amsmath}}
\usepackage{{enumitem}}
\definecolor{{improvedGreen}}{{HTML}}{{BFE6BF}}
\definecolor{{tieGray}}{{HTML}}{{D9D9D9}}
\definecolor{{worseRed}}{{HTML}}{{F2B8B8}}
\definecolor{{excludedBlue}}{{HTML}}{{C9D8F0}}
\definecolor{{excludedBrown}}{{HTML}}{{E0C4A2}}
\definecolor{{excludedPurple}}{{HTML}}{{D8B8EA}}
\definecolor{{excludedBlack}}{{HTML}}{{4B4B4B}}
\title{{Guarded Evolution of Go Insertion Heuristics for Real-Time Dynamic Dispatch}}
\author{{Automated draft from the EOH-Go experimental workspace}}
\date{{{datetime.now().strftime('%Y-%m-%d')}}}
\begin{{document}}
\maketitle

\begin{{abstract}}
This report summarizes the current phase of the EOH-Go study, positioned as a follow-up to the real-time routing system studied in the reference paper on closed-campus pickup-and-delivery services. That paper defines response time as the interval between a newly revealed request state and the generation of a corresponding route, and evaluates algorithms jointly by response time (Res.) and objective value \(J\). Following this evaluation style, we ask whether a large-language-model-driven Evolution of Heuristics (EOH) loop can evolve executable Go insertion heuristics for dynamic dispatch. The experiment spans 75 density--arrival-scale cells from RC101--RC105. The main empirical finding is conditional: guarded EOH improves over the SA baseline in 16 cells, ties in 11 cells, and worsens in 16 cells, while 32 cells must be excluded due to missing or suspicious evaluations. These results support a guarded code-evolution workflow rather than an unfiltered claim that EOH universally dominates SA.
\end{{abstract}}

\section{{Connection to the Reference Real-Time Routing Paper}}
The reference paper studies a closed-campus dynamic pickup-and-delivery setting with mixed delivery services, time-window constraints, and a real-time routing solver (RTRS). Its experimental logic is important for this work in three ways. First, it treats response time as an operational metric rather than a secondary implementation detail. Second, it reports both response time and route quality \(J\), usually in tables where the best and second-best values are identified. Third, it explicitly varies dynamic request proportions and hyperparameters to show that algorithmic behavior depends on the dynamic scenario.

This report keeps that framing but changes the research question. Rather than manually designing a new RTRS variant, we study whether LLM-guided EOH can automatically synthesize the Go insertion heuristic used when new requests arrive. Thus, the baseline real-time routing code remains the environment and evaluator, while EOH becomes a code-level heuristic design mechanism.

\section{{Problem Setting}}
The target function is the Go method \texttt{{InsertShips}}, which updates a dispatch solution when dynamic requests arrive. The baseline is the existing SA executable. The EOH loop mutates Go code, compiles it, evaluates it under dynamic Solomon-style sources, and selects candidates. We vary two experimental factors: request density \(d\in\{{d25,d50,d75\}}\) and arrival scale \(t\in\{{1.0,0.9,0.8,0.7,0.6\}}\). Here, \(d\) follows the reference paper's dynamic-density idea, while \(t\) controls the arrival rhythm. As in the reference paper, the reported metrics are Res. and \(J\): Res. is the first feasible response time measured by the simulator, and \(J\) is the final route cost.

\section{{Method: Guarded EOH}}
The implemented workflow is:
\[
\text{{SA seed}} \rightarrow \text{{LLM mutation}} \rightarrow \text{{Go compile}} \rightarrow \text{{dynamic simulation}} \rightarrow \text{{guard/filter}} \rightarrow \text{{cleaned report}}.
\]
The guard is necessary because raw LLM code can exploit evaluator loopholes. We exclude candidates with missing SA or EOH values, negative EOH costs, and suspiciously low EOH costs below \(0.3\times\) the SA cost. The report keeps raw results for traceability, but the main comparisons use filtered results. This is a methodological difference from a hand-coded solver comparison: an automatic code-evolution loop must validate that a low \(J\) is caused by a better dispatch heuristic rather than by missing requests, early loop termination, invalid state, or parser artifacts.

\section{{Experimental Data and Cleaning Protocol}}
The active dataset contains {total} cells. After filtering, {valid} cells remain as valid SA--EOH comparisons, while {excluded} cells are excluded. Table~\ref{{tab:outcome-counts}} gives the overall distribution.

\input{{tables/outcome_counts.tex}}

\section{{Main Results}}
Table~\ref{{tab:top-improvements}} lists the strongest valid improvements. The best cells are concentrated in medium-density and selected high-density settings, rather than uniformly across the grid.

\input{{tables/top_improvements.tex}}

\input{{tables/summary_by_density.tex}}

\input{{figures/status_heatmap_table.tex}}

\section{{Observations}}
\begin{{enumerate}}[leftmargin=*]
  \item \textbf{{Conditional superiority.}} EOH is useful in local regions of the density--arrival-scale grid. It is not a universal replacement for SA.
  \item \textbf{{Density sensitivity.}} Several improvements occur at \(d50\), suggesting that balanced-density cases provide enough structure for LLM-generated insertion heuristics to improve the baseline.
  \item \textbf{{Guard necessity.}} Excluded cells are not noise to hide; they are evidence that code-level heuristic evolution requires an evaluator guard. Negative or suspiciously low costs must not enter the main table.
  \item \textbf{{Runtime trade-off.}} Many improved cells reduce \(J\) at the cost of slower response time. This supports reporting both Res and \(J\), rather than a single objective.
  \item \textbf{{Alignment with the reference paper.}} Like the RTRS study, the results should be read as guidance for dynamic-scenario-dependent algorithm selection. Our current evidence is strongest for the claim that EOH can discover useful insertion heuristics in selected dynamic regimes, not that it always replaces the baseline.
\end{{enumerate}}

\section{{Repeat Validation Plan}}
We repeated eight high-value improved cells twice with the same model and guard/filter pipeline. Table~\ref{{tab:repeat-validation}} shows that the initial improvements do not all replicate: several RC102/RC104 cells become ties or worse in the repeat runs. The strongest repeated evidence is concentrated in RC105 \(d50,t=0.9\) and RC105 \(d75,t=0.9/0.6\), where at least one repeat remains improved and the mean \(\Delta J\) stays negative for the two high-density cells. This supports a cautious conclusion: EOH can discover useful insertion heuristics, but stochastic code generation requires repeat validation before a cell is treated as stable.

\input{{tables/repeat_validation.tex}}

\section{{Related Work}}
The immediate application context follows the reference paper's real-time dynamic pickup-and-delivery formulation and its dual emphasis on response time and route quality~\cite{{campus}}. This study is based on EOH~\cite{{eoh}}, and is methodologically close to LLM-assisted algorithm design frameworks such as LLM4AD~\cite{{llm4ad}}, FunSearch~\cite{{funsearch}}, and reflective evolutionary approaches such as ReEvo~\cite{{reevo}}. Our focus is narrower: executable Go heuristics for dynamic dispatch with guard-based evaluation.

\section{{Conclusion}}
The current evidence supports writing a focused paper on guarded EOH for dynamic Go dispatch. The contribution is not a new universal routing solver; it is an empirical and methodological demonstration that LLM-generated Go heuristics can improve selected dynamic dispatch regimes when paired with compilation, simulation, guard filtering, and cleaned reporting.

\begin{{thebibliography}}{{9}}
\bibitem{{campus}} Reference manuscript: \textit{{Application of Real-Time Routing and Concurrent Computing in Closed Commercial Park Delivery Services}}. Local file: \texttt{{second\_paper\_cn.pdf}}.
\bibitem{{eoh}} Fei Liu et al. \textit{{Evolution of Heuristics: Towards Efficient Automatic Algorithm Design Using Large Language Model}}. ICML 2024. \url{{https://arxiv.org/abs/2401.02051}}.
\bibitem{{llm4ad}} LLM4AD project. \url{{https://arxiv.org/abs/2412.17287}}.
\bibitem{{funsearch}} Bernardino Romera-Paredes et al. \textit{{Mathematical discoveries from program search with large language models}}. Nature, 2023. \url{{https://www.nature.com/articles/s41586-023-06924-6}}.
\bibitem{{reevo}} ReEvo: Reflective Evolution. \url{{https://arxiv.org/abs/2402.01145}}.
\end{{thebibliography}}

\end{{document}}
"""
    (OUT_DIR / "guarded_eoh_report.tex").write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_json(DATA_DIR / "clean_summary.json")
    rows = data["rows"]
    summary_rows = data["summary_by_instance_density"]
    counts = data["counts"]
    _write_status_heatmap(rows)
    _write_count_bar(counts)
    _write_latex_tables(rows, summary_rows, counts)
    _write_heatmap_latex(rows)
    _write_report(rows, summary_rows, counts)
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": str(DATA_DIR / "clean_summary.json"),
        "outputs": [
            "guarded_eoh_report.tex",
            "figures/status_heatmap.svg",
            "figures/outcome_counts.svg",
            "figures/status_heatmap_table.tex",
            "tables/top_improvements.tex",
            "tables/summary_by_density.tex",
            "tables/outcome_counts.tex",
            "tables/repeat_validation.tex",
        ],
    }
    (OUT_DIR / "ARTIFACTS.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out_dir": str(OUT_DIR), "outputs": manifest["outputs"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
