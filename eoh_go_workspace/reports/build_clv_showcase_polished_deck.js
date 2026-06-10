const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.company = "Local research workspace";
pptx.subject = "C+L+V harness weekly showcase polished";
pptx.title = "C+L+V Harness Weekly Showcase - Polished";
pptx.lang = "zh-CN";
pptx.theme = { headFontFace: "PingFang SC", bodyFontFace: "PingFang SC", lang: "zh-CN" };

const C = {
  navy: "061A2B",
  blue: "2563EB",
  cyan: "0891B2",
  green: "15803D",
  orange: "EA580C",
  red: "B91C1C",
  purple: "6D28D9",
  ink: "16202A",
  gray: "64748B",
  line: "D7DEE8",
  pale: "F6F8FB",
  bluePale: "EAF0FF",
  greenPale: "EAF7EF",
  orangePale: "FFF3E6",
  redPale: "FEE2E2",
  white: "FFFFFF",
};

const W = 13.333;
const H = 7.5;
const M = 0.62;
const FONT = "PingFang SC";

function bg(slide, color = C.white) {
  slide.background = { color };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color }, line: { color } });
}

function txt(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace: FONT,
    fontSize: opts.size || 11,
    bold: !!opts.bold,
    color: opts.color || C.ink,
    align: opts.align || "left",
    valign: opts.valign || "top",
    margin: opts.margin ?? 0.04,
    fit: "shrink",
    breakLine: opts.breakLine ?? true,
  });
}

function shape(slide, type, x, y, w, h, fill, line = fill, opts = {}) {
  slide.addShape(type, {
    x, y, w, h,
    rectRadius: opts.radius || 0.05,
    fill: { color: fill, transparency: opts.transparency || 0 },
    line: { color: line, width: opts.lineWidth || 0.6, transparency: opts.lineTransparency || 0 },
  });
}

function card(slide, x, y, w, h, fill = C.pale, line = "E7ECF3") {
  shape(slide, pptx.ShapeType.roundRect, x, y, w, h, fill, line);
}

function footer(slide, n) {
  shape(slide, pptx.ShapeType.line, M, 7.03, W - 2 * M, 0, C.line, C.line, { lineWidth: 0.6 });
  txt(slide, "Sources: weekly; gen8", M, 7.1, 10.2, 0.22, { size: 7.8, color: C.gray, margin: 0, breakLine: false });
  txt(slide, String(n).padStart(2, "0"), 12.2, 7.08, 0.6, 0.22, { size: 8, color: C.gray, align: "right", margin: 0 });
}

function title(slide, claim, page, subtitle = "") {
  txt(slide, claim, M, 0.36, 11.8, 0.58, { size: 22.5, bold: true, color: C.navy, margin: 0, breakLine: false });
  shape(slide, pptx.ShapeType.line, M, 1.08, W - 2 * M, 0, C.line, C.line, { lineWidth: 1.0 });
  if (subtitle) txt(slide, subtitle, M, 1.18, 11.5, 0.26, { size: 9.5, color: C.gray, margin: 0, breakLine: false });
  footer(slide, page);
}

function kpi(slide, x, y, w, value, label, color, fill, note = "") {
  card(slide, x, y, w, 1.12, fill, fill);
  shape(slide, pptx.ShapeType.rect, x, y, 0.07, 1.12, color, color);
  txt(slide, value, x + 0.2, y + 0.16, w - 0.34, 0.36, { size: 20, bold: true, color, margin: 0, align: "center" });
  txt(slide, label, x + 0.2, y + 0.62, w - 0.34, 0.2, { size: 8.8, bold: true, color: C.ink, margin: 0, align: "center" });
  if (note) txt(slide, note, x + 0.2, y + 0.86, w - 0.34, 0.16, { size: 7.8, color: C.gray, margin: 0, align: "center" });
}

function bullets(slide, items, x, y, w, rowH, opts = {}) {
  items.forEach((item, i) => {
    const yy = y + i * rowH;
    shape(slide, pptx.ShapeType.ellipse, x, yy + 0.08, 0.1, 0.1, opts.dot || C.blue, opts.dot || C.blue);
    txt(slide, item, x + 0.2, yy, w - 0.2, rowH - 0.02, { size: opts.size || 10.2, color: opts.color || C.ink, margin: 0 });
  });
}

function table(slide, rows, x, y, colW, rowH, opts = {}) {
  rows.forEach((row, r) => {
    let xx = x;
    const fill = r === 0 ? (opts.header || C.navy) : (r % 2 ? C.white : "F8FAFC");
    const color = r === 0 ? C.white : C.ink;
    row.forEach((cell, c) => {
      shape(slide, pptx.ShapeType.rect, xx, y + r * rowH, colW[c], rowH, fill, C.line);
      txt(slide, String(cell), xx + 0.08, y + r * rowH + 0.07, colW[c] - 0.16, rowH - 0.12, {
        size: r === 0 ? 8.6 : 8.2,
        bold: r === 0 || c === 0,
        color,
        align: c === 0 ? "left" : "center",
        margin: 0,
        valign: "mid",
      });
      xx += colW[c];
    });
  });
}

function pill(slide, label, x, y, w, color) {
  shape(slide, pptx.ShapeType.roundRect, x, y, w, 0.3, color, color);
  txt(slide, label, x + 0.06, y + 0.075, w - 0.12, 0.14, { size: 8, bold: true, color: C.white, align: "center", margin: 0 });
}

function resultRow(slide, y, label, d50, d75, verdict, color) {
  txt(slide, label, 1.05, y, 2.4, 0.24, { size: 11.4, bold: true, color: C.navy, margin: 0 });
  txt(slide, d50, 3.7, y, 2.0, 0.24, { size: 11.2, bold: true, color, align: "center", margin: 0 });
  txt(slide, d75, 6.0, y, 2.0, 0.24, { size: 11.2, bold: true, color, align: "center", margin: 0 });
  pill(slide, verdict, 8.65, y - 0.02, 1.45, color);
  shape(slide, pptx.ShapeType.line, 1.05, y + 0.46, 10.1, 0, "EEF2F7", "EEF2F7", { lineWidth: 0.6 });
}

// 1
{
  const s = pptx.addSlide();
  bg(s, C.navy);
  shape(s, pptx.ShapeType.rect, 0.68, 1.18, 0.12, 3.2, C.blue, C.blue);
  txt(s, "C+L+V Harness Weekly Showcase", 0.95, 1.18, 9.8, 0.62, { size: 28, bold: true, color: C.white, margin: 0 });
  txt(s, "跨 target / 跨组合优化问题迁移进展", 0.95, 1.96, 8.6, 0.34, { size: 15, color: "DCE7F7", margin: 0 });
  txt(s, "汇报版 | Data as of 2026-06-01", 0.95, 2.48, 5.2, 0.24, { size: 10.5, color: "AAB7C6", margin: 0 });
  kpi(s, 0.95, 4.25, 2.25, "4", "Targets", C.blue, "10243A", "InsertShips / Opt / Knap / Mixer");
  kpi(s, 3.55, 4.25, 2.25, "3", "Problem families", C.cyan, "10243A", "VRP / Knapsack / Split");
  kpi(s, 6.15, 4.25, 2.25, "54 OK", "Validation suite", C.green, "10243A", "Full unit suite");
  kpi(s, 8.75, 4.25, 2.25, "InsertShips", "Formal lift", C.orange, "10243A", "Only stable lift evidence");
  txt(s, "Sources: weekly; gen8", 0.95, 6.9, 8.4, 0.22, { size: 7.8, color: "91A0B5", margin: 0 });
}

// 2
{
  const s = pptx.addSlide(); bg(s); title(s, "Harness 可迁移已成立，性能结论只属于 InsertShips", 2, "Portability is proven; lift remains target-specific");
  kpi(s, 0.8, 1.62, 2.5, "4 × 3", "Target × problem coverage", C.blue, C.bluePale);
  kpi(s, 3.55, 1.62, 2.5, "274.90", "InsertShips best J", C.green, C.greenPale, "713.52 -> 274.90");
  kpi(s, 6.3, 1.62, 2.5, "870-974", "Context chars", C.cyan, "E0F7FA");
  kpi(s, 9.05, 1.62, 2.5, "smoke", "New-target evidence", C.orange, C.orangePale);
  card(s, 0.95, 3.35, 11.5, 1.65, C.white);
  bullets(s, [
    "同一 registry 已覆盖多 target、多 evaluator、多 context path。",
    "正式性能结论只保留 InsertShips；其余目标只作 smoke evidence。",
    "下一阶段瓶颈：domain skill cards、多实例 evaluator、generation depth。"
  ], 1.25, 3.75, 10.8, 0.42, { size: 10.8, dot: C.blue });
}

// 3
{
  const s = pptx.addSlide(); bg(s); title(s, "证据边界必须分开 formal 与 smoke", 3);
  table(s, [
    ["Target", "Problem", "Evidence", "Status"],
    ["InsertShips", "VRP insertion", "formal multi-run", "stable lift"],
    ["Optimization", "VRP order improve", "smoke", "seed only"],
    ["SelectItems", "0/1 knapsack", "LLM smoke", "Seed only"],
    ["SplitOrders", "Mixer split", "LLM smoke", "Seed only"],
  ], 0.8, 1.55, [1.75, 2.7, 3.35, 4.0], 0.58);
  pill(s, "正式证据", 1.0, 4.75, 1.0, C.green);
  txt(s, "可说性能提升：external evaluator、多轮结果、代码演化齐全。", 2.2, 4.78, 9.8, 0.22, { size: 10.2, margin: 0 });
  pill(s, "smoke证据", 1.0, 5.42, 1.0, C.orange);
  txt(s, "只说明链路跑通：prompt -> code -> build -> evaluator；不能说优于 seed。", 2.2, 5.45, 9.8, 0.22, { size: 10.2, margin: 0 });
}

// 4
{
  const s = pptx.addSlide(); bg(s); title(s, "Specs 让 harness 跨问题复用", 4);
  const boxes = [
    ["TargetSpec", "function / guard / context", C.blue],
    ["ProblemSpec", "source / evaluator / metric", C.cyan],
    ["Registry", "target × problem", C.green],
    ["Evaluator", "build / runtime / objective", C.orange],
  ];
  boxes.forEach((b, i) => {
    const x = 0.85 + i * 3.05;
    card(s, x, 1.62, 2.62, 1.35, i % 2 ? C.white : C.pale, b[2]);
    txt(s, b[0], x + 0.2, 1.85, 2.1, 0.24, { size: 12.2, bold: true, color: b[2], margin: 0 });
    txt(s, b[1], x + 0.2, 2.24, 2.18, 0.38, { size: 8.6, color: C.gray, margin: 0 });
    if (i < boxes.length - 1) shape(s, pptx.ShapeType.chevron, x + 2.72, 2.15, 0.28, 0.3, C.line, C.line);
  });
  table(s, [
    ["Target", "Problem", "Role"],
    ["InsertShips", "VRP insertion", "formal lift"],
    ["Optimization", "VRP improve", "second target"],
    ["SelectItems", "knapsack", "new family"],
    ["SplitOrders", "Mixer split", "greenfield"],
  ], 1.0, 3.65, [2.3, 3.25, 5.55], 0.52);
}

// 5
{
  const s = pptx.addSlide(); bg(s); title(s, "InsertShips 是唯一稳定性能提升线", 5);
  kpi(s, 0.9, 1.58, 2.15, "-61.5%", "d50 best reduction", C.green, C.greenPale, "713.52 -> 274.90");
  kpi(s, 3.25, 1.58, 2.15, "-51.6%", "d75 best reduction", C.blue, C.bluePale, "549.48 -> 266.06");
  card(s, 5.8, 1.58, 6.05, 1.12, C.orangePale, "FBD38D");
  txt(s, "Boundary", 6.08, 1.8, 1.2, 0.18, { size: 9.5, bold: true, color: C.orange, margin: 0 });
  txt(s, "Only InsertShips has formal lift evidence; all new targets remain smoke-only.", 7.25, 1.78, 4.3, 0.22, { size: 9.8, bold: true, color: C.ink, margin: 0 });

  card(s, 0.9, 3.18, 10.9, 2.35, C.white);
  txt(s, "Arm", 1.05, 3.45, 2.2, 0.18, { size: 8.5, bold: true, color: C.gray, margin: 0 });
  txt(s, "d50 median ΔJ", 3.62, 3.45, 2.0, 0.18, { size: 8.5, bold: true, color: C.gray, align: "center", margin: 0 });
  txt(s, "d75 median ΔJ", 5.92, 3.45, 2.0, 0.18, { size: 8.5, bold: true, color: C.gray, align: "center", margin: 0 });
  txt(s, "Interpretation", 8.55, 3.45, 1.8, 0.18, { size: 8.5, bold: true, color: C.gray, align: "center", margin: 0 });
  resultRow(s, 4.02, "API-only", "-95.44", "0.00", "d50 win", C.green);
  resultRow(s, 4.78, "History-RAG", "+97.15", "-134.52", "d75 win", C.blue);
  txt(s, "Read: density branch matters. API-only wins d50; History-RAG wins d75.", 0.95, 6.1, 11.4, 0.25, { size: 10.2, bold: true, color: C.navy, margin: 0 });
}

// 6
{
  const s = pptx.addSlide(); bg(s); title(s, "C 层 context 已修复，后续补 domain knowledge", 6);
  table(s, [
    ["Target", "Before", "Context", "Global items"],
    ["InsertShips", "ready", "974", "api skeleton + failures"],
    ["Optimization", "binding gap", "911", "api skeleton + failures"],
    ["SelectItems", "missing", "870", "knapsack skeleton"],
    ["SplitOrders", "greenfield", "949", "mixer skeleton"],
  ], 0.85, 1.55, [1.65, 2.25, 1.85, 5.75], 0.56);
  kpi(s, 1.0, 4.55, 2.75, "tag alias", "Root cause corrected", C.blue, C.bluePale);
  kpi(s, 4.1, 4.55, 2.75, "EOH_RAG_CONTEXT", "Prompt path fixed", C.green, C.greenPale);
  kpi(s, 7.2, 4.55, 2.75, "allowlist env", "Security hardening", C.orange, C.orangePale);
}

// 7
{
  const s = pptx.addSlide(); bg(s); title(s, "Knapsack 和 Mixer 已跑通，但 best 仍为 seed", 7, "Smoke proves portability, not superiority");
  table(s, [
    ["Target", "Arm", "Valid", "Best", "Verdict"],
    ["Optimization d50", "Base / Hist", "1", "713.52 seed", "runs; no lift"],
    ["Knapsack", "Base / API", "1", "value 283", "seed best"],
    ["Mixer", "Base / API", "1", "cost 175.01", "seed best"],
  ], 0.85, 1.58, [2.25, 2.0, 0.8, 2.35, 4.4], 0.62);
  card(s, 1.0, 4.35, 11.3, 1.05, C.orangePale, "FBD38D");
  txt(s, "汇报措辞：真实 LLM smoke 已证明链路和 context 注入；尚不支持性能提升。", 1.28, 4.72, 10.7, 0.24, { size: 11.2, bold: true, color: C.orange, margin: 0 });
}

// 8
{
  const s = pptx.addSlide(); bg(s); title(s, "下周应转向 skill cards 和多实例评估", 8, "Decision-ready next steps");
  const rows = [
    ["P0", "Knapsack smoke rerun", "确认 skeleton 注入；扩到 3-5 instances", C.red],
    ["P0", "Mixer baseline/API smoke", "验证 generated code build/evaluator", C.red],
    ["P1", "Domain skill cards", "补 constraints、examples、failure cases", C.orange],
    ["P1", "Optimization guard", "加 ship-id multiset guard 再解释 lift", C.orange],
    ["P2", "Reporting package", "所有表格分开 formal vs smoke", C.blue],
  ];
  rows.forEach((r, i) => {
    const y = 1.55 + i * 0.82;
    pill(s, r[0], 0.95, y + 0.04, 0.55, r[3]);
    txt(s, r[1], 1.8, y, 3.3, 0.28, { size: 11.2, bold: true, color: C.navy, margin: 0 });
    txt(s, r[2], 5.25, y + 0.02, 7.2, 0.26, { size: 9.6, color: C.ink, margin: 0 });
    shape(s, pptx.ShapeType.line, 1.8, y + 0.58, 10.5, 0, "EEF2F7", "EEF2F7", { lineWidth: 0.6 });
  });
  card(s, 0.95, 6.15, 11.7, 0.58, C.bluePale, "C7D2FE");
  txt(s, "Takeaway: harness 已能迁移；下一阶段瓶颈是 target knowledge 和 evaluator breadth。", 1.2, 6.34, 11.15, 0.18, { size: 10.2, bold: true, color: C.navy, align: "center", margin: 0 });
}

const out = path.join(__dirname, "clv_harness_weekly_showcase_polished.pptx");
pptx.writeFile({ fileName: out }).then(() => console.log(`OK: ${out}`));
