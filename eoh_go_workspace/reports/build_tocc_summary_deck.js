const fs = require("fs");
const path = require("path");
const childProcess = require("child_process");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../..");
const REPORT_DIR = path.resolve(__dirname);
const ASSET_DIR = path.join(REPORT_DIR, "tocc_summary_20260609_assets");
const PPTX_PATH = path.join(REPORT_DIR, "tocc_summary_20260609.pptx");
const MD_PATH = path.join(REPORT_DIR, "tocc_summary_20260609.md");
const DRAWIO_PATH = path.join(ASSET_DIR, "tocc_architecture.drawio");
const DRAWIO_PNG = path.join(ASSET_DIR, "tocc_architecture.drawio.png");
const COVER_SRC = "/Users/guojiadong.9/.codex/generated_images/019e97f4-6904-7041-ade4-704a56848629/ig_047af4775241f4d3016a26d2e5e9f88199b54180afb61509d7.png";
const COVER_DST = path.join(ASSET_DIR, "tocc_cover_gpt.png");

fs.mkdirSync(ASSET_DIR, { recursive: true });
if (fs.existsSync(COVER_SRC) && !fs.existsSync(COVER_DST)) {
  fs.copyFileSync(COVER_SRC, COVER_DST);
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/\\n/g, "&#xa;")
    .replace(/\n/g, "&#xa;");
}

function v(id, value, x, y, w, h, fill, stroke = "6B7280", style = "") {
  return `<mxCell id="${id}" value="${esc(value)}" style="rounded=1;whiteSpace=wrap;html=1;fontSize=14;align=center;verticalAlign=middle;arcSize=8;fillColor=#${fill};strokeColor=#${stroke};${style}" vertex="1" parent="1"><mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry"/></mxCell>`;
}

function e(id, source, target, label = "", stroke = "374151", dashed = false) {
  const dash = dashed ? "dashed=1;dashPattern=6 4;" : "";
  return `<mxCell id="${id}" value="" style="endArrow=block;html=1;rounded=0;fontSize=12;strokeColor=#${stroke};${dash}" edge="1" parent="1" source="${source}" target="${target}"><mxGeometry relative="1" as="geometry"/></mxCell>`;
}

function writeDrawio() {
  const cells = [
    v("title", "agent_go TOCC: Trace-Conditioned Operator-Card Controller", 40, 25, 980, 42, "111827", "111827", "fontColor=#FFFFFF;fontSize=20;fontStyle=1;"),
    v("lane1", "Observation", 40, 105, 150, 330, "EEF2FF", "4F46E5", "fontStyle=1;"),
    v("lane2", "Controller", 240, 105, 260, 330, "ECFDF5", "059669", "fontStyle=1;"),
    v("lane3", "Execution", 550, 105, 230, 330, "FFF7ED", "EA580C", "fontStyle=1;"),
    v("lane4", "Evidence", 830, 105, 190, 330, "F8FAFC", "64748B", "fontStyle=1;"),
    v("trace", "Run trace\\nsummary + rag_trace\\nbest code + valid rate", 60, 180, 110, 120, "FFFFFF", "4F46E5"),
    v("diag", "Diagnose bias\\nbaseline_overlap\\nwrong_bias\\nlow_diversity", 270, 165, 180, 95, "FFFFFF", "059669"),
    v("cards", "Select cards + query\\nregret / farthest\\ncapacity / savings", 270, 300, 180, 95, "FFFFFF", "059669"),
    v("gate", "Gatekeeper\\nfield boundary\\nproblem-prefix check", 500, 232, 145, 95, "FFFFFF", "059669"),
    v("runner", "Official EOH runner\\nselected-card IDs\\nLLM + evaluator", 665, 180, 95, 120, "FFFFFF", "EA580C"),
    v("summ", "Auto summarizer\\nCSV / Markdown\\ncode evidence", 855, 170, 125, 100, "FFFFFF", "64748B"),
    v("report", "Research outputs\\nrepeat tables\\nPPT + reports", 855, 310, 125, 80, "FFFFFF", "64748B"),
    v("claim", "Claim boundary\\nexploratory signal now\\nrepeat stability next", 350, 470, 340, 70, "FEF2F2", "DC2626", "fontColor=#991B1B;"),
    e("a1", "trace", "diag", "observe", "4F46E5"),
    e("a2", "diag", "cards", "decision", "059669"),
    e("a3", "cards", "gate", "proposal", "059669"),
    e("a4", "gate", "runner", "bounded action", "EA580C"),
    e("a5", "runner", "summ", "new trace", "64748B"),
    e("a6", "summ", "report", "evidence", "64748B"),
    e("a7", "summ", "trace", "next loop", "991B1B", true),
    e("a8", "report", "claim", "validity boundary", "DC2626", true),
  ];
  const xml = `<mxfile host="app.diagrams.net"><diagram name="TOCC Architecture"><mxGraphModel dx="1200" dy="760" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="620" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>${cells.join("")}</root></mxGraphModel></diagram></mxfile>`;
  fs.writeFileSync(DRAWIO_PATH, xml, "utf8");
}

function tryExportDrawio() {
  const cli = "/Applications/draw.io.app/Contents/MacOS/draw.io";
  if (!fs.existsSync(cli)) return false;
  try {
    childProcess.execFileSync(cli, ["-x", "-f", "png", "-e", "-b", "10", "-o", DRAWIO_PNG, DRAWIO_PATH], { stdio: "inherit" });
    return fs.existsSync(DRAWIO_PNG);
  } catch (err) {
    console.warn(`draw.io export skipped: ${err.message}`);
    return false;
  }
}

function writeMarkdown() {
  const md = `# agent_go / TOCC 阶段成果总结

日期：2026-06-09  
性质：阶段性研究记录与导师汇报材料，不作为统计显著性结论。  

## 一句话结论

项目已经从单函数 InsertShips 演化实验推进到可复用的 TOCC 闭环：run trace -> 诊断搜索偏差 -> 选择 operator cards 和 query -> Official EOH 实跑 -> 自动记录 trace、best code 和结果。当前最明确的发现是：RAG 的主要变量不是“是否加上下文”，而是“选中了什么卡”。默认检索容易选到与 baseline 重合或方向错误的卡；有针对性的 regret + farthest / far-first 卡在 TSP、CVRP 上产生了正向 best-score 信号。

## 现有工程资产

| 层 | 已完成内容 |
|---|---|
| Corpus / RAG | algorithm cards、API rules、two-section prompt context、selected-card tracing |
| Official EOH | TSP/CVRP/BP official target runner、manifest runner、resume/no-run/force gate |
| TOCC V1 | rule controller: trace diagnosis -> selected cards + query |
| TOCC V2 | LLM proposer + rule gatekeeper，字段边界与 problem-prefix 约束 |
| V3 pilot | bounded loop 能基于 weak_negative trace 做一次纠偏并回收新 trace |
| Evidence | 自动 summary、best-code records、中文报告、card decision records |

## 当前实验信号

| Problem | 当前判断 | 证据 |
|---|---|---|
| TSP | 方差大；targeted 有 best-score 信号，但 repeat 均值暂不稳定 | V2 agent best=6.217；18-run repeat 中 r3 init-only 新低 6.189，但 tocc_corrected 均值受 9.656 outlier 影响 |
| CVRP | 当前最可靠正面证据 | repeat=3 中 tocc_corrected 3/3 优于 pure，均值约 12.970 vs 13.596，改善约 4.6% |
| BP/OBP | 当前没有 RAG 增益证据 | pure 已自发学到 tight-fit/best-fit 类策略，RAG 未突破 0.03984 |

## 18/18 stabilization repeat 快照

| Problem | Arm | Mean | r1 | r2 | r3 / note |
|---|---:|---:|---:|---:|---|
| TSP | pure_eoh | 6.751 | 6.608 | 7.057 | third run in record set |
| TSP | default_rag | 6.756 | 6.273 | 7.194 | unstable |
| TSP | tocc_corrected | 7.618 | 9.656 | 7.010 | r3 init-only new low 6.189; mean hit by outlier |
| CVRP | pure_eoh | 13.596 | 13.565 | 13.611 | baseline repeat |
| CVRP | default_rag | 13.283 | 13.283 | 13.283 | low but valid=1 degenerate |
| CVRP | tocc_corrected | 12.970 | 12.738 | 12.888 | 3/3 better than pure |

## 最优代码证据

TSP 最优代码核心不是 nearest neighbor，而是把 immediate distance、isolation 和 two-hop regret 组合成 score；CVRP 最优代码先用 far-first seed 远端簇，再用 close-to-current and far-from-depot 的组合分数推进路线。后续报告必须继续保留 best code snippet，而不是只写策略名。

## 方法伪代码

已补充 algorithm2e 版本的 TOCC method-level pseudocode：

    Algorithm 1: Trace-Conditioned Operator-Card Controller
    Input: manifest M, card library C, EOH runner E, budget B, loop limit K
    for k = 1..K:
      T_k <- collect run trace
      d_k <- diagnose search bias
      S_k, q_k <- select operator cards and query by diagnosis
      pi_k <- gatekeep(d_k, S_k, q_k, B)
      if pi_k is accepted:
        R_k <- run official EOH with selected cards
        V_k <- verify trace, best code, valid rate, objective
        archive(T_k, d_k, pi_k, R_k, V_k)
    return run archive

对应 LaTeX 源文件：eoh_go_workspace/reports/tocc_summary_20260609_assets/tocc_operator_card_controller_algorithm.tex。

## 边界

- 现在只能说 exploratory best-score signal，不能说统计稳定或证明有效。
- TSP 需要更多 repeat 或 gen>=1 排查 outlier。
- CVRP 是当前优先稳定的正面证据。
- BP/OBP 不应作为主线正面结果，除非后续改 target 或 operator cards。

## 下一步

1. 先补 CVRP repeat 的可追溯表格和 best-code 记录，巩固当前正面证据。
2. 对 TSP 进行 outlier 诊断：看 r1=9.656 的 selected cards、LLM output、valid/candidate 分布。
3. 将 TOCC controller 的选择理由、selected cards、trace、best code、valid rate 作为每次实验的强制记录字段。
4. 准备导师汇报时，主线写“框架已搭通 + CVRP repeat 正向 + TSP 方差待稳定”，不要夸大。

## 公开代码文献源码阅读

已完成公开源码调研报告：eoh_go_workspace/reports/paper_notes/llm_co_public_code_source_reading_20260609.md。

纳入：

| Work | Code | 本轮状态 |
|---|---|---|
| CO-Bench | github.com/sunnweiwei/CO-Bench | clone 成功，读 agent API 和 evaluator |
| HeuriGym | github.com/cornell-zhang/heurigym | clone 成功，读 executor / verifier / metric |
| HeurAgenix | github.com/microsoft/HeurAgenix | clone 成功，读 generator / evolver / selector / tool schema |
| EoH-S | github.com/FeiLiu36/EoH-S | 公开仓库可读，clone early EOF，待单独 sparse/zip |
| ReEvo | github.com/ai4co/reevo | 公开仓库可读，clone early EOF，待单独 sparse/zip |

直接启发：

- CO-Bench: agent.step -> evaluator.evaluate -> agent.feedback -> finalize，可作为 TOCC agent loop 的外部对齐口径。
- HeuriGym: verifier/evaluator 分离，支持把 valid/yield 和 objective 同时作为主指标。
- HeurAgenix: LLMSelectionHyperHeuristic 是 solving-state-level selector；TOCC 是 run-level operator-card selector。
- HeurAgenix function_to_tool.py 用 AST 把 heuristic function 转成 tool schema，可借鉴为 TOCC TraceReader/CardSelector/Gatekeeper/Summarizer tool schemas。
`;
  fs.writeFileSync(MD_PATH, md, "utf8");
}

function makePpt() {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "agent_go";
  pptx.subject = "TOCC阶段成果总结";
  pptx.title = "agent_go / TOCC阶段成果总结";
  pptx.company = "agent_go";
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: "Microsoft YaHei",
    bodyFontFace: "Microsoft YaHei",
    lang: "zh-CN",
  };
  pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
  pptx.layout = "WIDE";

  const C = {
    navy: "172033",
    ink: "111827",
    muted: "6B7280",
    blue: "2563EB",
    teal: "0F766E",
    green: "16A34A",
    orange: "EA580C",
    red: "DC2626",
    bg: "F8FAFC",
    card: "FFFFFF",
    line: "CBD5E1",
    sand: "FFF7ED",
  };

  function addFooter(slide, idx, source = "source: local reports, 2026-06-09") {
    slide.addText(source, { x: 0.35, y: 7.15, w: 8.0, h: 0.2, fontSize: 8.2, color: C.muted, margin: 0 });
    slide.addText(String(idx), { x: 12.65, y: 7.12, w: 0.35, h: 0.2, fontSize: 8.2, color: C.muted, align: "right", margin: 0 });
  }
  function title(slide, t, sub) {
    slide.addText(t, { x: 0.45, y: 0.25, w: 12.1, h: 0.42, fontSize: 25, bold: true, color: C.ink, margin: 0 });
    if (sub) slide.addText(sub, { x: 0.47, y: 0.76, w: 11.8, h: 0.25, fontSize: 10.5, color: C.muted, margin: 0 });
  }
  function card(slide, x, y, w, h, header, body, color = C.blue) {
    slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: C.card }, line: { color: "E5E7EB", width: 1 }, shadow: { type: "outer", color: "000000", opacity: 0.10, blur: 1, angle: 45, distance: 1 } });
    slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.07, h, fill: { color }, line: { color } });
    slide.addText(header, { x: x + 0.18, y: y + 0.14, w: w - 0.3, h: 0.23, fontSize: 12.5, bold: true, color: C.ink, margin: 0 });
    slide.addText(body, { x: x + 0.18, y: y + 0.47, w: w - 0.32, h: h - 0.6, fontSize: 9.4, color: C.ink, breakLine: false, fit: "shrink", margin: 0.02 });
  }
  function kpi(slide, x, y, w, h, value, label, note, color) {
    slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: "E5E7EB", width: 1 } });
    slide.addText(value, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: 0.45, fontSize: 23, bold: true, color, margin: 0 });
    slide.addText(label, { x: x + 0.16, y: y + 0.67, w: w - 0.3, h: 0.22, fontSize: 9.5, bold: true, color: C.ink, margin: 0 });
    slide.addText(note, { x: x + 0.16, y: y + 0.97, w: w - 0.3, h: h - 1.05, fontSize: 8.2, color: C.muted, fit: "shrink", margin: 0 });
  }
  function table(slide, rows, x, y, w, h, widths, fontSize = 8.5) {
    slide.addTable(rows, {
      x, y, w, h,
      colW: widths,
      border: { type: "solid", color: "D1D5DB", pt: 0.6 },
      fill: { color: "FFFFFF" },
      color: C.ink,
      fontFace: "Microsoft YaHei",
      fontSize,
      margin: 0.04,
      valign: "mid",
      fit: "shrink",
      autoFit: false,
    });
  }
  function codeBox(slide, x, y, w, h, code, label) {
    slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: "0B1220" }, line: { color: "1F2937", width: 1 } });
    slide.addText(label, { x: x + 0.18, y: y + 0.15, w: w - 0.36, h: 0.22, fontSize: 9, color: "93C5FD", bold: true, margin: 0 });
    slide.addText(code, { x: x + 0.18, y: y + 0.47, w: w - 0.36, h: h - 0.55, fontSize: 8.4, fontFace: "Consolas", color: "E5E7EB", fit: "shrink", margin: 0 });
  }
  function arrow(slide, x1, y1, x2, y2, color = C.blue) {
    slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width: 1.6, beginArrowType: "none", endArrowType: "triangle" } });
  }

  let slide = pptx.addSlide();
  slide.background = { color: C.navy };
  if (fs.existsSync(COVER_DST)) {
    slide.addImage({ path: COVER_DST, x: 6.65, y: 0, w: 6.68, h: 7.5, transparency: 10 });
  }
  slide.addText("agent_go / TOCC 阶段成果总结", { x: 0.65, y: 0.78, w: 6.15, h: 0.6, fontSize: 29, bold: true, color: "FFFFFF", margin: 0 });
  slide.addText("Trace-Conditioned Operator-Card Controller for LLM-based heuristic evolution", { x: 0.68, y: 1.55, w: 5.7, h: 0.5, fontSize: 14.5, color: "CBD5E1", margin: 0 });
  slide.addText("当前定位：框架闭环已搭通；CVRP repeat 证据最稳定；TSP 方差仍需收敛。", { x: 0.68, y: 5.85, w: 6.0, h: 0.42, fontSize: 14, color: "FFFFFF", bold: true, margin: 0 });
  slide.addText("2026-06-09 | 本地实验记录汇总", { x: 0.68, y: 6.42, w: 4.2, h: 0.22, fontSize: 9.5, color: "94A3B8", margin: 0 });

  slide = pptx.addSlide();
  title(slide, "结论不再是“RAG有没有用”，而是“选卡是否控制了搜索方向”", "现有结果支持把研究问题从 context 注入切换到 operator-card selection / search steering。");
  kpi(slide, 0.55, 1.25, 2.85, 1.32, "18/18", "repeat finished", "TSP/CVRP x 3 arms x 3 repeats。", C.blue);
  kpi(slide, 3.65, 1.25, 2.85, 1.32, "3/3", "CVRP positive", "TOCC corrected 全部优于 pure。", C.green);
  kpi(slide, 6.75, 1.25, 2.85, 1.32, "6.217", "TSP best", "V2 targeted 刷新 best-score。", C.teal);
  kpi(slide, 9.85, 1.25, 2.85, 1.32, "valid=1", "default risk", "CVRP default RAG 有退化风险。", C.orange);
  card(slide, 0.55, 3.05, 3.95, 2.35, "当前正面证据", "CVRP tocc_corrected repeat=3 均优于 pure；均值约 12.970 vs 13.596。", C.green);
  card(slide, 4.7, 3.05, 3.95, 2.35, "当前不确定性", "TSP 受 9.656 outlier 影响；同批仍有 6.189 新低。", C.orange);
  card(slide, 8.85, 3.05, 3.95, 2.35, "叙事边界", "只能写 exploratory signal；不写统计证明或稳定超越。", C.red);
  addFooter(slide, 2);

  slide = pptx.addSlide();
  title(slide, "项目已经从单函数进化升级为可复用的官方 EOH + TOCC 闭环", "从 InsertShips 自定义 harness 到 TSP/CVRP/BP official benchmark，核心资产是可复用实验流水线。");
  const timeline = [
    ["InsertShips", "自定义 Go 函数演化；验证 API skeleton 与 guard。"],
    ["Literature-RAG", "将文献伪代码重构为短 operator skill cards。"],
    ["Official EOH", "对齐 BP/TSP/CVRP official targets，避免只在自定义任务上自证。"],
    ["TOCC V1", "规则诊断：trace -> cards/query -> manifest runner。"],
    ["TOCC V2/V3", "LLM proposer + gatekeeper；bounded loop 已完成一次纠偏。"],
  ];
  timeline.forEach((t, i) => {
    const x = 0.75 + i * 2.48;
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 2.35, w: 0.36, h: 0.36, fill: { color: i < 3 ? C.blue : C.green }, line: { color: "FFFFFF", width: 1 } });
    if (i < timeline.length - 1) arrow(slide, x + 0.45, 2.53, x + 2.05, 2.53, "94A3B8");
    card(slide, x - 0.25, 3.05, 2.05, 1.65, t[0], t[1], i < 3 ? C.blue : C.green);
  });
  slide.addText("主线变化：从“把 RAG 加进 prompt”变成“根据 trace 选择 operator-card prior 来 steering EOH 搜索方向”。", { x: 1.15, y: 5.55, w: 11, h: 0.38, fontSize: 15, bold: true, color: C.ink, align: "center", margin: 0 });
  addFooter(slide, 3);

  slide = pptx.addSlide();
  title(slide, "TOCC 的数据流把选卡、执行和证据记录串成一个闭环", "draw.io 源图已保留，可继续编辑；PPT 中使用导出 PNG 作为方法图。");
  if (fs.existsSync(DRAWIO_PNG)) {
    slide.addImage({ path: DRAWIO_PNG, x: 0.42, y: 1.05, w: 12.45, h: 5.45, sizing: { type: "contain", w: 12.45, h: 5.45 } });
  } else {
    card(slide, 1.0, 1.2, 11.2, 4.8, "TOCC Architecture", "run trace -> diagnose bias -> select cards/query -> gatekeeper -> official EOH runner -> summarizer -> next trace", C.blue);
  }
  addFooter(slide, 4, `source: ${path.relative(ROOT, DRAWIO_PATH)}`);

  slide = pptx.addSlide();
  title(slide, "Algorithm 1: TOCC 方法伪代码");
  const algo = `Input: M, C, E, B, K
A <- empty archive
for k = 1..K:
    T_k, d_k <- ObserveAndDiagnose(A, M)
    S_k, q_k <- SelectCards(C, T_k, d_k)
    pi_k <- Gatekeep(d_k, S_k, q_k, B)
    if pi_k accepted:
        R_k, V_k <- ExecuteAndVerify(E, M, pi_k)
        A <- Archive(T_k, d_k, pi_k, R_k, V_k)
    if Stop(A, B): break
return A`;
  codeBox(slide, 0.7, 1.13, 7.65, 5.35, algo, "Trace-Conditioned Operator-Card Controller");
  card(slide, 8.75, 1.25, 3.85, 1.35, "抽象层级", "trace -> cards -> gate -> EOH。", C.blue);
  card(slide, 8.75, 2.95, 3.85, 1.35, "复杂度", "controller: O(K * |C|)。", C.green);
  card(slide, 8.75, 4.65, 3.85, 1.35, "源文件", "完整 algorithm2e 已保存。", C.orange);
  addFooter(slide, 5, "source: gen-pseudocode-skill / algorithm2e reconstruction");

  slide = pptx.addSlide();
  title(slide, "18/18 repeat 结果显示：CVRP 稳定转正，TSP 仍受方差支配", "数值越低越好；TSP 当前不做稳定性结论，CVRP 是可优先汇报的正面证据。");
  const rows = [
    [{ text: "Problem" }, { text: "Arm" }, { text: "Mean" }, { text: "r1" }, { text: "r2" }, { text: "备注" }],
    ["TSP", "pure_eoh", "6.751", "6.608", "7.057", "baseline repeat"],
    ["TSP", "default_rag", "6.756", "6.273", "7.194", "不稳定"],
    ["TSP", "tocc_corrected", "7.618", "9.656", "7.010", "r3 init-only 新低 6.189；r1 outlier"],
    ["CVRP", "pure_eoh", "13.596", "13.565", "13.611", "baseline repeat"],
    ["CVRP", "default_rag", "13.283", "13.283", "13.283", "valid=1，退化风险"],
    ["CVRP", "tocc_corrected", "12.970", "12.738", "12.888", "3/3 优于 pure，当前最可靠"],
  ];
  table(slide, rows, 0.65, 1.15, 7.4, 4.65, [0.9, 1.45, 0.95, 0.85, 0.85, 2.4], 8.6);
  kpi(slide, 8.45, 1.35, 3.9, 1.4, "-4.6%", "CVRP TOCC mean vs pure", "12.970 vs 13.596，repeat 级正向信号。", C.green);
  kpi(slide, 8.45, 3.05, 3.9, 1.4, "9.656", "TSP outlier", "该 run 使均值失真；需回看 trace 和候选分布。", C.orange);
  kpi(slide, 8.45, 4.75, 3.9, 1.4, "6.189", "TSP init-only new low", "同一批 repeat 内仍有强 best-score 信号。", C.teal);
  addFooter(slide, 6, "source: user-provided 18/18 stabilization repeat snapshot, 2026-06-09");

  slide = pptx.addSlide();
  title(slide, "TSP 的证据是“潜力明确但方差未稳”，不能直接写稳定超越", "V2 targeted 出现历史最优，但 stabilization repeat 中 outlier 说明还需诊断。");
  table(slide, [
    ["Setting", "Best / Mean", "Cards", "解释"],
    ["pure init", "6.839", "-", "baseline"],
    ["default RAG", "6.840", "nearest cards", "与模型自发策略重合，基本无增益"],
    ["targeted smoke", "6.475", "regret + farthest", "端到端链路通过"],
    ["V2 agent", "6.217", "regret + farthest", "当前 best-score 最强信号"],
    ["repeat tocc", "mean 7.618", "regret + farthest", "受 9.656 outlier 影响，需排查"],
  ], 0.65, 1.12, 6.15, 4.4, [1.35, 1.2, 1.6, 2.0], 8.5);
  card(slide, 7.1, 1.2, 5.55, 1.25, "机制解释", "regret + farthest 引入 lookahead 和 isolation 信号。", C.blue);
  card(slide, 7.1, 2.75, 5.55, 1.25, "不能夸大", "TSP 有 best-score 潜力，但 repeat 方差仍大。", C.red);
  card(slide, 7.1, 4.3, 5.55, 1.25, "下一步", "回看 9.656 run 的 trace、候选分布和代码结构。", C.orange);
  addFooter(slide, 7);

  slide = pptx.addSlide();
  title(slide, "CVRP 是当前最可靠的正面证据：TOCC corrected 在 repeat 中 3/3 优于 pure", "default RAG 虽均值低，但 valid=1 退化，不能作为主证据；targeted / tocc_corrected 更可信。");
  table(slide, [
    ["Arm", "Mean", "Run-level evidence", "Validity caveat"],
    ["pure_eoh", "13.596", "13.565 / 13.611 / repeat baseline", "valid 正常"],
    ["default_rag", "13.283", "三次相同", "valid=1，疑似 recipe/退化"],
    ["tocc_corrected", "12.970", "12.738 / 12.888 / third repeat better than pure", "当前最可靠正面证据"],
  ], 0.72, 1.2, 7.1, 2.35, [1.35, 1.0, 2.9, 1.85], 8.6);
  kpi(slide, 8.25, 1.22, 4.0, 1.25, "12.970", "TOCC corrected mean", "低于 pure mean 13.596。", C.green);
  kpi(slide, 8.25, 2.77, 4.0, 1.25, "3/3", "run-level direction", "三次 repeat 都优于 pure。", C.green);
  kpi(slide, 8.25, 4.32, 4.0, 1.25, "regret + far_first", "stable selected cards", "CVRP 当前应优先稳定这组卡。", C.teal);
  addFooter(slide, 8);

  slide = pptx.addSlide();
  title(slide, "TOCC 改变了生成代码结构");
  const tspCode = `regret_val = max(0.0, two_hop_min - d_current)\nscores.append((0.4*iso_factor + 0.6*regret_val) / d_current)\nreturn unvisited_nodes[np.argmax(scores)]`;
  const cvrpCode = `if current_node == depot: return farthest_from_depot(unvisited_nodes)\nscores = normalize(cur_dists) - depot_distance(unvisited_nodes)/max_depot_dist\nreturn unvisited_nodes[np.argmin(scores)]`;
  table(slide, [
    ["Problem", "Best", "Cards", "Role"],
    ["TSP", "6.21694", "regret+far", "best-score"],
    ["CVRP", "12.82084", "regret+far_first", "targeted best"],
  ], 0.65, 1.05, 12.15, 0.85, [1.2, 1.35, 3.0, 2.4], 8.8);
  codeBox(slide, 0.65, 2.12, 5.95, 3.85, tspCode, "TSP: regret + isolation");
  codeBox(slide, 6.85, 2.12, 5.95, 3.85, cvrpCode, "CVRP: far-first + distance");
  addFooter(slide, 9, "source: auto_experiment_reports/tocc_best_code_records.md");

  slide = pptx.addSlide();
  title(slide, "V1 到 V3 的自动化重点是逐步减少人工选卡，而不是放开模型直接控制实验", "LLM proposer 只给 diagnosis/cards/query；gatekeeper 保证预算、执行、路径等字段不可越权。");
  const xs = [0.9, 4.85, 8.8];
  [
    ["V1 规则控制器", "hardcoded rules\ntrace -> diagnosis\ncards/query 手工规则", C.blue],
    ["V2 agent-assisted", "LLM proposer\nrule gatekeeper\nbounded real runs", C.green],
    ["V3 bounded loop", "observe new trace\npropose correction\nmax iterations gate", C.orange],
  ].forEach((b, i) => card(slide, xs[i], 1.4, 3.45, 3.2, b[0], b[1], b[2]));
  arrow(slide, 4.45, 2.95, 4.8, 2.95, C.muted);
  arrow(slide, 8.4, 2.95, 8.75, 2.95, C.muted);
  slide.addText("定位：Trace-Conditioned Operator-Card Controller，不直接声称是泛化 ReAct agent。", { x: 1.05, y: 5.45, w: 11.2, h: 0.35, fontSize: 15, bold: true, color: C.ink, align: "center", margin: 0 });
  addFooter(slide, 10);

  slide = pptx.addSlide();
  title(slide, "论文材料必须把证据强度说清楚：当前是探索性信号，不是统计证明", "这一页可直接作为导师汇报的 validity boundary。");
  table(slide, [
    ["风险", "当前状态", "处理方式"],
    ["TSP 方差", "repeat 中出现 9.656 outlier", "先诊断 trace，再决定是否 gen>=1 复跑"],
    ["default RAG 退化", "CVRP default_rag valid=1", "不作为主证据，只作为 failure mode"],
    ["BP 无增益", "0.03984 未突破", "写 inconclusive，不写负面定论"],
    ["重复次数", "CVRP repeat=3，TSP 还不稳", "只能写 repeat-level signal"],
    ["人工选卡", "V2/V3 已开始自动化，但仍需门禁", "记录每次 selected cards 和选择理由"],
  ], 0.72, 1.15, 11.85, 4.75, [1.75, 4.0, 6.1], 9);
  addFooter(slide, 11);

  slide = pptx.addSlide();
  title(slide, "下一步不是扩大矩阵，而是把自动化实验记录制度固定下来", "每次 run 必须能回答：为什么选这些卡、模型看到了什么、生成了什么最优代码、结果是否可信。");
  card(slide, 0.75, 1.25, 3.8, 2.05, "1. 补 CVRP 证据链", "把 repeat=3 的 card decisions、trace、best code、valid/candidate 分布写入统一报告。", C.green);
  card(slide, 4.85, 1.25, 3.8, 2.05, "2. 诊断 TSP outlier", "读取 9.656 run 的 raw candidates 与 best code，判断是选卡问题、代码退化还是随机方差。", C.orange);
  card(slide, 8.95, 1.25, 3.8, 2.05, "3. 固化 TOCC run schema", "强制记录 selected_card_ids、selection reason、rag_trace、best score、best code、valid rate。", C.blue);
  card(slide, 2.8, 4.0, 3.8, 1.55, "4. 准备导师版本", "主线：框架搭通 + CVRP 稳定正向 + TSP 待稳定。", C.teal);
  card(slide, 6.9, 4.0, 3.8, 1.55, "5. 论文方向", "把 operator-card injection 定义为 search steering，而非普通 RAG。", C.red);
  addFooter(slide, 12);

  slide = pptx.addSlide();
  slide.background = { color: C.navy };
  slide.addText("导师汇报压缩话术", { x: 0.65, y: 0.6, w: 5.8, h: 0.55, fontSize: 30, bold: true, color: "FFFFFF", margin: 0 });
  slide.addText("主线：TOCC 把 RAG 从“加上下文”变成“根据 trace 选择 operator-card prior 来控制搜索方向”。", { x: 0.8, y: 1.45, w: 11.4, h: 0.5, fontSize: 18, color: "E5E7EB", bold: true, margin: 0 });
  table(slide, [
    ["可以说", "不能说", "下一步"],
    ["框架闭环已搭通；CVRP repeat 当前最稳", "TOCC 已被统计证明；RAG 必然有效", "补 CVRP 证据链和 best code"],
    ["TSP 有 best-score 潜力但方差大", "TSP 稳定优于 pure", "诊断 9.656 outlier trace"],
    ["贡献点是 search steering controller", "只是普通 ReAct agent", "固化每次选卡与代码记录"],
  ], 0.85, 2.25, 11.5, 3.2, [3.75, 3.75, 4.0], 10.2);
  slide.addText("可汇报结论：框架已搭通；CVRP 是当前正面证据；TSP 还需稳定；论文贡献点写成 search steering。", { x: 0.95, y: 5.92, w: 11.0, h: 0.35, fontSize: 15, color: "FFFFFF", bold: true, margin: 0 });
  slide.addText("agent_go / TOCC | 2026-06-09", { x: 0.8, y: 6.75, w: 4.5, h: 0.25, fontSize: 9.5, color: "94A3B8", margin: 0 });

  slide = pptx.addSlide();
  title(slide, "公开代码文献调研：只保留能读源码或至少有官方仓库的工作", "本轮不再讨论只有论文没有代码的工作；CoupleEvo 仓库当前 404，CoEvo-AHD 暂未找到公开代码。");
  table(slide, [
    ["Work", "Code", "Status", "Read"],
    ["CO-Bench", "sunnweiwei/CO-Bench", "clone OK", "agent API + evaluator"],
    ["HeuriGym", "cornell-zhang/heurigym", "clone OK", "executor + verifier"],
    ["HeurAgenix", "microsoft/HeurAgenix", "clone OK", "selector + tool schema"],
    ["EoH-S", "FeiLiu36/EoH-S", "public; clone early EOF", "README only"],
    ["ReEvo", "ai4co/reevo", "public; clone early EOF", "README only"],
    ["CoupleEvo", "repo 404", "excluded", "no source claim"],
  ], 0.62, 1.05, 12.05, 4.8, [1.25, 2.75, 2.2, 5.85], 8.7);
  card(slide, 0.8, 6.05, 3.8, 0.75, "报告路径", "paper_notes/llm_co_public_code_source_reading_20260609.md", C.blue);
  card(slide, 4.85, 6.05, 3.8, 0.75, "原则", "没有代码不写源码结论；clone 失败只写公开结构。", C.red);
  card(slide, 8.9, 6.05, 3.8, 0.75, "下一步", "EoH-S/ReEvo 用 sparse checkout 或 zip 单独拉。", C.orange);
  addFooter(slide, 13, "source: local source reading report + public GitHub repos, 2026-06-09");

  slide = pptx.addSlide();
  title(slide, "源码读到的三种 agent/harness 形态", "三类实现对应 TOCC 的 loop、metric、tool-use。");
  table(slide, [
    ["Codebase", "Core abstraction", "Files", "TOCC borrow"],
    ["CO-Bench", "step / feedback", "agents/*", "agent loop"],
    ["HeuriGym", "verify + evaluate", "scripts/*", "yield metric"],
    ["HeurAgenix", "state selector", "pipeline/*", "tool schema"],
  ], 0.65, 1.15, 12.05, 2.25, [1.35, 2.8, 3.35, 4.55], 8.3);
  card(slide, 0.8, 4.0, 3.55, 1.65, "CO-Bench", "标准 agent loop。", C.blue);
  card(slide, 4.65, 4.0, 3.55, 1.65, "HeuriGym", "valid + quality 双指标。", C.green);
  card(slide, 8.5, 4.0, 3.55, 1.65, "HeurAgenix", "AST -> tool schema。", C.orange);
  addFooter(slide, 14, "source: cloned repositories under eoh_go_workspace/external_repos/");

  slide = pptx.addSlide();
  title(slide, "HeurAgenix 原图：它是 solving-state-level heuristic selector，不是 run-level card controller", "这些原图来自公开仓库 doc/；它们说明相邻工作的 tool-use 是求解过程内选 heuristic。");
  const heuraDoc = path.join(ROOT, "eoh_go_workspace/external_repos/HeurAgenix/doc");
  const heuraFramework = path.join(heuraDoc, "framework.png");
  const heuraProblemSolving = path.join(heuraDoc, "problem_solving.png");
  const heuraEvolution = path.join(heuraDoc, "heuristic_evolution_multiple.png");
  if (fs.existsSync(heuraFramework)) {
    slide.addImage({ path: heuraFramework, x: 0.55, y: 1.05, w: 5.85, h: 4.55, sizing: { type: "contain", w: 5.85, h: 4.55 } });
  } else {
    card(slide, 0.55, 1.05, 5.85, 4.55, "HeurAgenix framework", "framework.png not found", C.orange);
  }
  if (fs.existsSync(heuraProblemSolving)) {
    slide.addImage({ path: heuraProblemSolving, x: 6.85, y: 1.05, w: 5.85, h: 2.15, sizing: { type: "contain", w: 5.85, h: 2.15 } });
  }
  if (fs.existsSync(heuraEvolution)) {
    slide.addImage({ path: heuraEvolution, x: 6.85, y: 3.45, w: 5.85, h: 2.15, sizing: { type: "contain", w: 5.85, h: 2.15 } });
  }
  slide.addText("TOCC 边界：HeurAgenix 选择“当前求解状态用哪个 heuristic”；TOCC 选择“下一轮 EOH 注入哪些 operator cards”。", { x: 0.7, y: 6.1, w: 11.9, h: 0.35, fontSize: 14, bold: true, color: C.ink, align: "center", margin: 0 });
  addFooter(slide, 15, "source: microsoft/HeurAgenix public repository doc images");

  slide = pptx.addSlide();
  title(slide, "TOCC 应实现为 tool-using research controller", "把可执行动作拆成工具，并用 gatekeeper 限制。");
  table(slide, [
    ["TOCC Tool", "Borrowed from", "Implementation direction"],
    ["TraceReader", "CO-Bench", "read trace"],
    ["CardSelector", "HeurAgenix", "cards + query"],
    ["Gatekeeper", "HeuriGym", "block unsafe fields"],
    ["ManifestRunner", "CO-Bench", "bounded run"],
    ["Summarizer", "HeuriGym", "quality + funnel"],
  ], 0.65, 1.0, 12.05, 3.35, [1.75, 2.0, 8.3], 8.6);
  codeBox(slide, 0.85, 4.85, 5.75, 1.45, `allowed:
diagnosis, cards, query,
rationale, expected_effect, confidence`, "LLM proposer");
  codeBox(slide, 6.9, 4.85, 5.75, 1.45, `blocked:
budget, shell, key,
delete path, git operation`, "Gatekeeper");
  addFooter(slide, 16, "source: source reading report + TOCC goal document");

  return pptx.writeFile({ fileName: PPTX_PATH });
}

async function main() {
  writeDrawio();
  tryExportDrawio();
  writeMarkdown();
  await makePpt();
  console.log(`wrote ${MD_PATH}`);
  console.log(`wrote ${DRAWIO_PATH}`);
  console.log(`wrote ${DRAWIO_PNG}`);
  console.log(`wrote ${PPTX_PATH}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
