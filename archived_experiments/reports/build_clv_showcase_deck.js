const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.company = "Local research workspace";
pptx.subject = "C+L+V harness weekly showcase";
pptx.title = "C+L+V Harness Weekly Showcase";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "PingFang SC",
  bodyFontFace: "PingFang SC",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "LAYOUT_WIDE";

const C = {
  navy: "051C2C",
  blue: "2251FF",
  cyan: "12B5CB",
  green: "2F855A",
  orange: "ED8936",
  red: "C53030",
  purple: "6B46C1",
  ink: "1A1A1A",
  gray: "64748B",
  mid: "94A3B8",
  line: "D8DEE9",
  pale: "F6F8FB",
  bluePale: "EAF0FF",
  greenPale: "EAF7EF",
  orangePale: "FFF3E6",
  purplePale: "F2ECFF",
  white: "FFFFFF",
};

const W = 13.333;
const H = 7.5;
const M = 0.55;
const BODY = "PingFang SC";
const HEAD = "PingFang SC";

function addBg(slide) {
  slide.background = { color: C.white };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.white }, line: { color: C.white } });
}

function addFooter(slide, n, source = "Source: clv_harness_weekly_showcase.md; code_evolution_insertships_gen8.md") {
  slide.addShape(pptx.ShapeType.line, { x: M, y: 7.03, w: W - 2 * M, h: 0, line: { color: C.line, width: 0.6 } });
  slide.addText(source, { x: M, y: 7.09, w: 10.6, h: 0.22, fontFace: BODY, fontSize: 7.5, color: C.gray, margin: 0, breakLine: false, fit: "shrink" });
  slide.addText(String(n).padStart(2, "0"), { x: 12.15, y: 7.06, w: 0.65, h: 0.25, fontFace: BODY, fontSize: 8, color: C.gray, align: "right", margin: 0 });
}

function title(slide, text, subtitle) {
  slide.addText(text, { x: M, y: 0.38, w: 11.6, h: 0.6, fontFace: HEAD, fontSize: 22, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  slide.addShape(pptx.ShapeType.line, { x: M, y: 1.08, w: 12.1, h: 0, line: { color: C.line, width: 1.2 } });
  if (subtitle) {
    slide.addText(subtitle, { x: M, y: 1.16, w: 11.6, h: 0.28, fontFace: BODY, fontSize: 9.5, color: C.gray, margin: 0, fit: "shrink" });
  }
}

function text(slide, t, x, y, w, h, opts = {}) {
  slide.addText(t, {
    x, y, w, h,
    fontFace: opts.fontFace || BODY,
    fontSize: opts.size || 11,
    bold: opts.bold || false,
    color: opts.color || C.ink,
    margin: opts.margin ?? 0.05,
    breakLine: false,
    fit: opts.fit || "shrink",
    valign: opts.valign || "top",
    align: opts.align || "left",
    paraSpaceAfterPt: opts.paraSpaceAfterPt || 0,
    breakLine: false,
  });
}

function card(slide, x, y, w, h, label, value, color = C.blue, note = "") {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.06,
    fill: { color: C.pale },
    line: { color: "E7ECF3", width: 0.8 },
  });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.06, h, fill: { color }, line: { color } });
  text(slide, value, x + 0.18, y + 0.18, w - 0.3, 0.38, { size: 18, bold: true, color: C.navy });
  text(slide, label, x + 0.18, y + 0.68, w - 0.3, 0.28, { size: 8.8, bold: true, color: C.gray });
  if (note) text(slide, note, x + 0.18, y + 1.0, w - 0.3, h - 1.05, { size: 8, color: C.gray });
}

function bulletList(slide, items, x, y, w, h, opts = {}) {
  const fontSize = opts.size || 11;
  const runs = [];
  items.forEach((item, i) => {
    runs.push({ text: item, options: { bullet: { indent: 12 }, hanging: 4, breakLine: i < items.length - 1 } });
  });
  slide.addText(runs, { x, y, w, h, fontFace: BODY, fontSize, color: opts.color || C.ink, margin: 0.03, fit: "shrink", breakLine: false, paraSpaceAfterPt: opts.spaceAfter || 6 });
}

function tag(slide, x, y, label, color, w = 1.0) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.26, rectRadius: 0.04, fill: { color }, line: { color } });
  text(slide, label, x + 0.05, y + 0.055, w - 0.1, 0.14, { size: 6.8, bold: true, color: C.white, align: "center" });
}

function simpleTable(slide, rows, x, y, w, h, colWidths, opts = {}) {
  const tableRows = rows.map((row, r) => row.map((cell) => ({
    text: String(cell),
    options: {
      fontFace: BODY,
      fontSize: r === 0 ? (opts.headerSize || 8.5) : (opts.size || 8),
      bold: r === 0,
      color: r === 0 ? C.white : C.ink,
      fill: { color: r === 0 ? (opts.headerColor || C.navy) : (r % 2 === 0 ? "FAFBFD" : C.white) },
      margin: 0.06,
      valign: "mid",
      fit: "shrink",
      border: { type: "solid", color: "E3E8EF", pt: 0.5 },
    },
  })));
  slide.addTable(tableRows, { x, y, w, h, colW: colWidths, margin: 0.04, autoFit: false, fit: "shrink" });
}

function metricBar(slide, x, y, label, seed, best, color) {
  const max = Math.max(seed, best);
  const bw = 4.2;
  text(slide, label, x, y, 1.3, 0.24, { size: 9, bold: true, color: C.navy });
  slide.addShape(pptx.ShapeType.rect, { x: x + 1.45, y: y + 0.02, w: bw, h: 0.16, fill: { color: "DFE7F1" }, line: { color: "DFE7F1" } });
  slide.addShape(pptx.ShapeType.rect, { x: x + 1.45, y: y + 0.02, w: bw * seed / max, h: 0.16, fill: { color: C.mid }, line: { color: C.mid } });
  slide.addShape(pptx.ShapeType.rect, { x: x + 1.45, y: y + 0.28, w: bw, h: 0.16, fill: { color: "DFE7F1" }, line: { color: "DFE7F1" } });
  slide.addShape(pptx.ShapeType.rect, { x: x + 1.45, y: y + 0.28, w: bw * best / max, h: 0.16, fill: { color }, line: { color } });
  text(slide, `Seed ${seed.toFixed(2)}`, x + 5.8, y - 0.02, 1.2, 0.2, { size: 7.5, color: C.gray });
  text(slide, `Best ${best.toFixed(2)}`, x + 5.8, y + 0.25, 1.2, 0.2, { size: 7.5, color });
}

function slide1() {
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.navy }, line: { color: C.navy } });
  s.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.22, w: 0.11, h: 3.0, fill: { color: C.blue }, line: { color: C.blue } });
  text(s, "C+L+V Harness Weekly Showcase", 0.95, 1.18, 9.7, 0.62, { size: 27, bold: true, color: C.white });
  text(s, "跨 target / 跨组合优化问题迁移进展", 0.95, 1.95, 8.4, 0.38, { size: 15, color: "DCE7F7" });
  text(s, "汇报版 | Data as of 2026-06-01", 0.95, 2.48, 5.0, 0.28, { size: 10.5, color: "AAB7C6" });
  card(s, 0.95, 4.25, 2.35, 1.35, "Evolvable targets", "4", C.blue, "InsertShips / Optimization / SelectItems / SplitOrders");
  card(s, 3.55, 4.25, 2.35, 1.35, "Problem families", "3", C.cyan, "VRP, 0/1 knapsack, mixer order splitting");
  card(s, 6.15, 4.25, 2.35, 1.35, "Validation suite", "54 OK", C.green, "Full unit suite after context and evaluator fixes");
  card(s, 8.75, 4.25, 2.35, 1.35, "Formal lift line", "InsertShips", C.orange, "Only target with stable performance evidence");
  text(s, "Sources: clv_harness_weekly_showcase.md; code_evolution_insertships_gen8.md", 0.95, 6.9, 8.4, 0.24, { size: 7.5, color: "91A0B5" });
}

function slide2() {
  const s = pptx.addSlide(); addBg(s); title(s, "Harness 已证明可迁移，但性能证据仍集中在 InsertShips", "Executive summary | evidence boundary first");
  card(s, 0.65, 1.55, 2.55, 1.25, "Target × problem coverage", "4 × 3", C.blue, "同一 registry 抽象覆盖多函数和多问题族。");
  card(s, 3.45, 1.55, 2.55, 1.25, "InsertShips best J", "274.90", C.green, "rc101 d50，从 713.52 降至 274.90。");
  card(s, 6.25, 1.55, 2.55, 1.25, "Context trace", "870-974 chars", C.cyan, "四个 target 的 API skeleton 均进入 global context。");
  card(s, 9.05, 1.55, 2.55, 1.25, "New-target evidence", "smoke", C.orange, "Optimization / Knapsack / Mixer 均跑通但未超过 seed。");
  bulletList(s, [
    "本周可展示的核心成果是 framework portability：从单一 InsertShips 扩展到多 target、多 evaluator、多 context path。",
    "正式性能结论只保留 InsertShips；Optimization、Knapsack、Mixer 目前作为 feasibility / smoke evidence。",
    "早期新 target 未提升的主因已从“LLM能力不足”校正为“C 层 target-specific context 未适配”。",
    "下一阶段应补 domain skill cards、多实例 evaluator 和更长 generation，而不是继续证明 harness 能否跑通。"
  ], 0.95, 3.25, 11.5, 2.35, { size: 12, spaceAfter: 8 });
  addFooter(s, 2);
}

function slide3() {
  const s = pptx.addSlide(); addBg(s); title(s, "证据边界将正式结果与 smoke 结果分开", "Academic reporting standard: claim strength matches validation depth");
  simpleTable(s, [
    ["Target", "Problem", "Evidence", "RAG/API context", "Performance status"],
    ["InsertShips", "VRP dynamic insertion", "Formal multi-run + code evolution", "Verified", "Stable improvement branches"],
    ["Optimization", "VRP route/order improvement", "Smoke", "Verified", "Seed only"],
    ["SelectItems", "0/1 knapsack", "LLM smoke", "knapsack_api_skeleton verified", "Seed only"],
    ["SplitOrders", "Mixer order splitting", "LLM smoke", "mixer_split_api_skeleton verified", "Seed only"],
  ], 0.75, 1.55, 11.8, 2.35, [1.55, 2.15, 2.65, 2.65, 2.8], { size: 8.2 });
  tag(s, 0.9, 4.4, "正式证据", C.green, 1.05);
  text(s, "可用于说明方法有效性和性能提升：guarded external evaluator、多轮结果、代码结构演化均有记录。", 2.1, 4.38, 9.6, 0.36, { size: 10.2, color: C.ink });
  tag(s, 0.9, 5.05, "smoke 证据", C.orange, 1.05);
  text(s, "可用于说明链路跑通：prompt -> code generation -> build -> evaluator -> trace，但不能支持“优于 seed”的结论。", 2.1, 5.03, 9.6, 0.36, { size: 10.2, color: C.ink });
  tag(s, 0.9, 5.7, "阻塞已校正", C.blue, 1.15);
  text(s, "Knapsack/Mixer 的 API context 已注入；后续性能不足更可能来自 skill cards、实例数和 generation 深度不足。", 2.1, 5.68, 9.6, 0.36, { size: 10.2, color: C.ink });
  addFooter(s, 3);
}

function slide4() {
  const s = pptx.addSlide(); addBg(s); title(s, "TargetSpec / ProblemSpec 把演化边界从单函数扩展到多问题", "Harness architecture: registry separates function boundary from optimization problem");
  const boxes = [
    ["TargetSpec", "函数名 / 签名 / 抽取替换 / prompt guard / RAG API context", C.blue],
    ["ProblemSpec", "语言 / 源文件 / evaluator / benchmark / 指标方向", C.cyan],
    ["Registry", "target 与 problem 组合注册；保持 InsertShips 向后兼容", C.green],
    ["Guarded evaluator", "build + runtime checks + objective summary + trace", C.orange],
  ];
  boxes.forEach((b, i) => {
    const x = 0.75 + i * 3.05;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 1.55, w: 2.65, h: 1.35, rectRadius: 0.05, fill: { color: i % 2 ? "F8FBFF" : C.pale }, line: { color: b[2], width: 1.1 } });
    text(s, b[0], x + 0.18, 1.78, 2.2, 0.24, { size: 12, bold: true, color: b[2] });
    text(s, b[1], x + 0.18, 2.18, 2.26, 0.46, { size: 8.4, color: C.gray });
    if (i < boxes.length - 1) s.addShape(pptx.ShapeType.chevron, { x: x + 2.72, y: 2.03, w: 0.28, h: 0.32, fill: { color: C.line }, line: { color: C.line } });
  });
  simpleTable(s, [
    ["Registered target", "Problem", "Role in showcase"],
    ["InsertShips", "VRP dynamic insertion", "Main performance and code-evolution evidence"],
    ["Optimization", "VRP route/order improvement", "Same Go solver, second target feasibility"],
    ["SelectItems", "0/1 knapsack", "Different problem family and evaluator"],
    ["SplitOrders", "Mixer/concrete truck split", "Greenfield domain migration target"],
  ], 1.0, 3.55, 11.25, 2.35, [2.2, 3.1, 5.95], { size: 8.5 });
  addFooter(s, 4);
}

function slide5() {
  const s = pptx.addSlide(); addBg(s); title(s, "InsertShips 在 d50 和 d75 分支保留唯一稳定性能提升", "Lower J is better; performance claims use guarded external evaluator results");
  metricBar(s, 0.95, 1.55, "RC101 d50", 713.52, 274.90, C.green);
  metricBar(s, 0.95, 2.35, "RC101 d75", 549.48, 266.06, C.blue);
  card(s, 8.25, 1.35, 2.05, 1.15, "d50 reduction", "-61.5%", C.green, "713.52 -> 274.90");
  card(s, 10.55, 1.35, 2.05, 1.15, "d75 reduction", "-51.6%", C.blue, "549.48 -> 266.06");
  simpleTable(s, [
    ["Configuration", "Cell", "valid pairs", "median ΔJ", "better / worse / same"],
    ["d50 API-only", "RC101-d50", "3/3", "-95.44", "2 / 0 / 1"],
    ["d50 History-RAG", "RC101-d50", "3/3", "+97.15", "1 / 2 / 0"],
    ["d75 API-only", "RC101-d75", "5/5", "0.00", "2 / 1 / 2"],
    ["d75 History-RAG", "RC101-d75", "3/3", "-134.52", "2 / 0 / 1"],
  ], 0.95, 3.65, 11.55, 2.15, [2.55, 1.75, 1.4, 1.55, 2.35], { size: 8.5 });
  text(s, "Interpretation: API-only works on d50; History-RAG is the stronger d75 branch. d75 API-only remains inconclusive despite 5 valid pairs.", 0.95, 6.08, 11.5, 0.38, { size: 9.2, color: C.gray });
  addFooter(s, 5);
}

function slide6() {
  const s = pptx.addSlide(); addBg(s); title(s, "代码演化从 first-feasible 转向 guarded best-delta", "L-layer evidence: evolution changes algorithmic structure, not only objective values");
  const steps = [
    ["Gen 1", "first feasible", "找到第一个可行 Assign 后立即提交；简单 fallback。", C.mid],
    ["Gen 3-4", "trial-all + delta", "遍历多个 Assign，计算 cost delta，并显式 rollback。", C.blue],
    ["Gen 5-8", "best-delta + fallback", "选择最小 cost increase；失败时创建/使用新 Assign。", C.green],
    ["d75 Gen 6+", "weighted best-delta", "加入 slack / penalty / normalized delta，适配更密集实例。", C.purple],
  ];
  steps.forEach((st, i) => {
    const x = 0.85 + i * 3.05;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 1.55, w: 2.65, h: 2.15, rectRadius: 0.05, fill: { color: i === 0 ? C.pale : "F8FBFF" }, line: { color: st[3], width: 1.2 } });
    text(s, st[0], x + 0.18, 1.8, 1.0, 0.24, { size: 9, bold: true, color: st[3] });
    text(s, st[1], x + 0.18, 2.2, 2.2, 0.34, { size: 13, bold: true, color: C.navy });
    text(s, st[2], x + 0.18, 2.78, 2.22, 0.52, { size: 8.8, color: C.gray });
    if (i < steps.length - 1) s.addShape(pptx.ShapeType.chevron, { x: x + 2.74, y: 2.42, w: 0.26, h: 0.35, fill: { color: C.line }, line: { color: C.line } });
  });
  simpleTable(s, [
    ["Cell", "Seed J", "Verified best EOH J", "Selected generation", "Selected strategy"],
    ["rc101 d50 t=1.0", "713.52", "274.90", "Gen 8", "best-delta + fallback"],
    ["rc101 d75 t=1.0", "549.48", "393.30", "Gen 8", "weighted best-delta"],
  ], 1.15, 4.35, 10.8, 1.25, [2.2, 1.3, 1.9, 1.8, 2.45], { size: 8.6 });
  text(s, "Note: per-generation pops_best objectives are internal EOH selection signals; final claims use guarded external evaluations.", 1.15, 5.95, 10.8, 0.32, { size: 8.6, color: C.gray });
  addFooter(s, 6);
}

function slide7() {
  const s = pptx.addSlide(); addBg(s); title(s, "C 层 target-specific context 绑定已从缺失修复为可追踪", "Early non-improvement was a context adaptation issue, not a harness failure");
  simpleTable(s, [
    ["Target", "Before", "After context chars", "Global items"],
    ["InsertShips", "available", "974", "insertships_api_skeleton + failure cases"],
    ["Optimization", "target-bound gap", "911", "optimization_api_skeleton + failure cases"],
    ["SelectItems", "ctx_chars=MISSING", "870", "knapsack_api_skeleton + failure cases"],
    ["SplitOrders", "greenfield", "949", "mixer_split_api_skeleton + failure cases"],
  ], 0.8, 1.55, 11.75, 2.25, [1.7, 2.0, 1.75, 5.7], { size: 8.4 });
  card(s, 0.95, 4.2, 3.0, 1.35, "Root cause corrected", "tag alias", C.blue, "SelectItems 与 knapsack tag 不匹配的问题已修复。");
  card(s, 4.25, 4.2, 3.0, 1.35, "Prompt path fixed", "EOH_RAG_CONTEXT", C.green, "Knapsack prompt 已实际消费环境变量。");
  card(s, 7.55, 4.2, 3.0, 1.35, "Security hardening", "allowlist env", C.orange, "Knapsack/Mixer evaluator 避免泄露敏感环境变量。");
  text(s, "Implication: 后续新 target 的关键工作是补 target-specific examples / failure cases / constraints，而不是扩大空 context 下的 generation。", 0.95, 6.0, 11.5, 0.36, { size: 9.2, color: C.gray });
  addFooter(s, 7);
}

function slide8() {
  const s = pptx.addSlide(); addBg(s); title(s, "Optimization / Knapsack / Mixer 均已跑通，但 best 仍为 seed", "Smoke evidence proves pipeline portability; it does not prove performance superiority");
  simpleTable(s, [
    ["Target", "Arm", "Population", "Valid", "Best objective / value", "Verdict"],
    ["Optimization d50", "Baseline / Hist-RAG", "gen=1 pop=8", "1", "713.52 seed", "Pipeline runs; no lift"],
    ["Knapsack", "Baseline", "2", "1", "value 283", "Best is seed"],
    ["Knapsack", "API-only", "2", "1", "value 283", "RAG context effective; best is seed"],
    ["Mixer SplitOrders", "Baseline", "2", "1", "cost 175.01468", "Best is seed"],
    ["Mixer SplitOrders", "API-only", "2", "1", "cost 175.01468", "RAG context effective; best is seed"],
  ], 0.7, 1.5, 11.95, 2.75, [2.05, 1.6, 1.4, 0.7, 2.1, 3.05], { size: 7.8 });
  bulletList(s, [
    "Knapsack API-only trace: rag_context_chars=870; global items include knapsack_api_skeleton and failure cases.",
    "Mixer API-only trace: rag_context_chars=949; global items include mixer_split_api_skeleton and failure cases.",
    "In both problems, gen=1 generated only 2 candidates and mutated candidates did not pass evaluator, so seed remained best."
  ], 0.95, 4.75, 11.2, 1.1, { size: 10, spaceAfter: 5 });
  tag(s, 0.95, 6.18, "汇报措辞", C.orange, 1.0);
  text(s, "“已完成真实 LLM smoke，证明链路和 context 注入；尚不支持性能提升结论。”", 2.1, 6.17, 9.5, 0.28, { size: 10.5, color: C.ink });
  addFooter(s, 8);
}

function slide9() {
  const s = pptx.addSlide(); addBg(s); title(s, "SplitOrders 已完成最小可演化 target 抽象", "Mixer/concrete truck migration is now buildable, replaceable, evaluable, and guarded");
  simpleTable(s, [
    ["Component", "Artifact", "Purpose"],
    ["Go evaluator + seed", "mixer_split_solver.go", "Defines Order, Vehicle, SubOrder and seed SplitOrders"],
    ["Test instance", "testdata_01.json", "Small concrete-truck order split case"],
    ["EOH prompt", "prompts_mixer_split_go.py", "Injects RAG context and target constraints"],
    ["Problem wrapper", "prob_mixer_split_go.py", "Build/run evaluator with allowlisted env"],
    ["Smoke runner", "mixer_split_smoke.py", "Baseline/API-only experiment entrypoint"],
  ], 0.8, 1.5, 11.6, 2.5, [2.0, 3.35, 5.45], { size: 8.5 });
  card(s, 1.0, 4.45, 2.55, 1.25, "Seed cost", "175.014675", C.blue, "Direct Go run and Python evaluator agree.");
  card(s, 3.85, 4.45, 2.55, 1.25, "Suborders", "16", C.cyan, "Generated by seed SplitOrders.");
  card(s, 6.7, 4.45, 2.55, 1.25, "Feasibility", "true", C.green, "Evaluator reason: valid.");
  card(s, 9.55, 4.45, 2.55, 1.25, "Unknown capacity", "rejected", C.orange, "Prevents fake oversized vehicles.");
  addFooter(s, 9);
}

function slide10() {
  const s = pptx.addSlide(); addBg(s); title(s, "本轮验收覆盖 registry、RAG、编译和 evaluator", "Validation is scoped to this harness, not historical candidate snippets");
  simpleTable(s, [
    ["Validation command / area", "Observed result"],
    ["Focused unit tests: specs + RAG integration + corpus", "23 tests OK"],
    ["Full unit suite", "54 tests OK"],
    ["compileall: eoh_go + InsertShips/Knapsack/Mixer examples", "OK"],
    ["Top-level Go build", "OK"],
    ["Mixer direct Go run", "cost 175.014675; feasible true"],
    ["Mixer seed evaluator", "Evaluation(seed)=175.014675; last_error=None"],
  ], 0.8, 1.55, 11.6, 2.8, [5.8, 5.8], { size: 8.7 });
  s.addShape(pptx.ShapeType.roundRect, { x: 0.95, y: 4.85, w: 11.2, h: 1.05, rectRadius: 0.05, fill: { color: C.orangePale }, line: { color: "FBD38D", width: 0.8 } });
  text(s, "Scope note", 1.15, 5.05, 1.1, 0.22, { size: 9, bold: true, color: C.orange });
  text(s, "`go test ./...` is intentionally not the acceptance command because it sweeps historical candidate_sources that are raw function snippets, not complete Go packages.", 2.1, 5.02, 9.65, 0.36, { size: 9.5, color: C.ink });
  addFooter(s, 10);
}

function slide11() {
  const s = pptx.addSlide(); addBg(s); title(s, "当前限制主要在问题级知识和评估深度，而不是 harness 链路", "Risk register for honest weekly reporting");
  simpleTable(s, [
    ["Risk / limitation", "Affected assumption", "Expected outcome", "Mitigation"],
    ["New targets return seed", "API skeleton alone is enough", "No performance lift in gen=1", "Add domain skill cards and failure examples"],
    ["Single/small instances", "Smoke reflects stable behavior", "Cannot claim robust performance", "Add 3-5 instances per problem first"],
    ["Short generation depth", "2 candidates can explore enough", "Mutated candidates fail evaluator", "Increase generations after constraints mature"],
    ["Optimization guard gap", "Syntax/feasibility guard is sufficient", "Semantic preservation underchecked", "Add runtime ship-id multiset guard"],
  ], 0.7, 1.5, 12.0, 3.05, [2.8, 2.55, 2.8, 3.85], { size: 8.0 });
  bulletList(s, [
    "Preferred wording: “framework portability is proven; performance improvement is target-specific and currently only demonstrated for InsertShips.”",
    "Do not present Knapsack/Mixer seed results as negative evidence against LLMs; they are under-contextualized smoke runs."
  ], 0.95, 4.95, 11.3, 0.85, { size: 10, spaceAfter: 5 });
  addFooter(s, 11);
}

function slide12() {
  const s = pptx.addSlide(); addBg(s); title(s, "下周应转向 domain skill cards 和多实例评估", "Decision-ready next steps");
  const rows = [
    ["P0", "Knapsack proper smoke rerun", "Confirm rag_global_items includes knapsack_api_skeleton, then add 3-5 instances.", C.red],
    ["P0", "Mixer baseline/API-only smoke", "Keep one instance first; verify generated SplitOrders build/evaluator behavior.", C.red],
    ["P1", "Domain skill cards", "For each new target, add API constraints, code examples, and failure cases beyond skeleton.", C.orange],
    ["P1", "Optimization semantic guard", "Add runtime ship-id multiset preservation before interpreting objective lift.", C.orange],
    ["P2", "Reporting package", "Keep InsertShips code evolution visualization; separate formal vs smoke evidence in all tables.", C.blue],
  ];
  rows.forEach((r, i) => {
    const y = 1.45 + i * 0.85;
    tag(s, 0.85, y + 0.05, r[0], r[3], 0.55);
    text(s, r[1], 1.55, y, 3.0, 0.28, { size: 11.2, bold: true, color: C.navy });
    text(s, r[2], 4.65, y, 7.3, 0.35, { size: 9.3, color: C.ink });
    s.addShape(pptx.ShapeType.line, { x: 1.55, y: y + 0.58, w: 10.4, h: 0, line: { color: "EEF2F7", width: 0.6 } });
  });
  s.addShape(pptx.ShapeType.roundRect, { x: 0.85, y: 6.05, w: 11.6, h: 0.62, rectRadius: 0.05, fill: { color: C.bluePale }, line: { color: "C7D2FE", width: 0.6 } });
  text(s, "Showcase takeaway: 同一 C+L+V harness 已能迁移到多个组合优化问题；下一阶段的瓶颈是 target-specific knowledge 和 evaluator breadth。", 1.05, 6.23, 11.15, 0.22, { size: 10.2, bold: true, color: C.navy });
  addFooter(s, 12);
}

[slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10, slide11, slide12].forEach(fn => fn());

const fs = require("fs");
const JSZip = require("jszip");

async function build() {
  const buf = await pptx.write({ compression: true, outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);

  const ctXml = await zip.file("[Content_Types].xml").async("string");
  const cleaned = ctXml.replace(
    /<Override PartName="\/([^"]+)"[^>]*\/>\n?/g,
    (match, part) => (zip.files[part] ? match : "")
  );
  zip.file("[Content_Types].xml", cleaned);

  const outBuf = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  fs.writeFileSync("clv_harness_weekly_showcase.pptx", outBuf);
  console.log("OK: clv_harness_weekly_showcase.pptx written and cleaned");
}

build().catch(e => { console.error(e); process.exit(1); });
