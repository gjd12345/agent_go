# agent_go 中文说明

本仓库是 EOH-Go 实验的最小可复现实现，用于研究大语言模型驱动的 Evolution of Heuristics (EOH) 是否能够自动进化 Go 实时动态调度程序中的插入启发式代码。

项目的核心对象是 Go 程序里的 `InsertShips` 函数。实验从已有 SA 插入基线出发，让 LLM 生成和变异 Go 代码，然后经过 Go 编译、动态源仿真、候选过滤和 filtered-best 选择，得到可以和 SA 进行对比的结果。

## 当前结论

当前结果不能说明 EOH 全面优于 SA。更准确的结论是：

> 在部分动态密度和请求到达节奏下，Guarded EOH-Go 能够发现优于 SA seed 的 Go 插入启发式；但这种优势具有场景敏感性，必须通过 evaluator guard、异常候选过滤和 repeat validation 才能形成可信结论。

主实验覆盖 RC101--RC105、三种动态密度 `d25/d50/d75` 和五种请求到达节奏 `t=1.0,0.9,0.8,0.7,0.6`，共 75 个 cell。清洗后得到 43 个有效 SA-vs-EOH 对比，其中 EOH 改善 16 个、持平 11 个、变差 16 个。论文草稿采用保守表述：EOH-Go 是一种场景相关的自动启发式设计工具，而不是稳定替代 SA 的通用算法。

## 仓库内容

- Go 动态调度求解器：`main.go`、`routing.go`、`go.mod`、`go.sum`
- EOH-Go 实验封装：`eoh_go/`
- 必要的 Agent_EOH 核心与 Go `InsertShips` 示例：`Agent_EOH/eoh/src/eoh/`
- 动态 Solomon-style 数据源：`solomon_benchmark_d25/`、`solomon_benchmark_d50/`、`solomon_benchmark_d75/`
- 候选 Go 启发式代码：`eoh_go_workspace/candidate_sources/`
- 清洗后的实验表格与 repeat validation：`eoh_go_workspace/reports/tables/`
- 论文风格图表：`eoh_go_workspace/reports/figures/`
- 中文 LaTeX 论文草稿与编译 PDF：`eoh_go_workspace/reports/paper_draft_full_20260426/`

## 主要产物

- 中文论文草稿 PDF：`eoh_go_workspace/reports/paper_draft_full_20260426/build/guarded_eoh_go_full_draft_cn.pdf`
- 中文论文 LaTeX 源文件：`eoh_go_workspace/reports/paper_draft_full_20260426/guarded_eoh_go_full_draft_cn.tex`
- 有效 SA-vs-EOH 对比图表：`eoh_go_workspace/reports/figures/valid_comparison_charts_20260426/`
- 论文风格主表与 repeat 表：`eoh_go_workspace/reports/figures/paper_style_tables_20260426/`
- 清洗后主结果：`eoh_go_workspace/reports/tables/eoh_grid_cleaned_summary_rc101_105/clean_summary.md`
- repeat validation 结果：`eoh_go_workspace/reports/tables/eoh_selected_repeats_summary_20260426/selected_repeat_summary.md`
- 阶段总结：`eoh_go/eoh_go_phase0_summary.md`

## 快速验证

在仓库根目录运行：

```powershell
go build -o mainbin_sa.exe .
python -m pytest tests/test_candidate_guard.py -q
python -m eoh_go.experiments.build_paper_style_table_image
python -m eoh_go.experiments.build_paper_style_table_image --repeat-only
python -m eoh_go.experiments.build_full_paper_draft
```

如果需要重新编译中文论文 PDF，可以使用 Tectonic：

```powershell
cd eoh_go_workspace/reports/paper_draft_full_20260426
tectonic --outdir build guarded_eoh_go_full_draft_cn.tex
```

## 运行一组小规模 EOH 实验

运行 EOH 需要配置 DeepSeek/OpenAI-compatible API key。建议先在环境变量中设置：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_API_ENDPOINT="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
```

然后运行一个 RC101 的小网格：

```powershell
python -m eoh_go.experiments.eoh_arrival_grid `
  --root "." `
  --problem rc101.json `
  --density d25 --density d50 --density d75 `
  --arrival-scale 1.0 --arrival-scale 0.9 --arrival-scale 0.8 --arrival-scale 0.7 --arrival-scale 0.6 `
  --use-density-source-dirs `
  --llm-model deepseek-v4-flash `
  --output-dir eoh_go_workspace/reports/tables/eoh_arrival_grid_flash_dynamic_full `
  --generations 1 `
  --pop-size 4 `
  --eva-timeout 120 `
  --run-timeout-s 60 `
  --objective-res-weight 0.2
```

## 方法说明

最终论文主线不是完整 ReAct、多智能体或后训练系统，而是一个小型 Guarded EOH-Go pipeline：

```text
SA seed
  -> LLM mutation
  -> Go code extraction
  -> Go compile
  -> dynamic source evaluation
  -> candidate guard
  -> filtered-best selection
  -> cleaned reporting
```

其中 `candidate guard` 是关键组件。LLM 生成的代码可能出现编译失败、运行超时、漏单、异常低成本、负值输出等情况。如果直接使用 raw-best，容易把无效候选误判为算法进步。因此本项目主表只使用 guard 后的 filtered-best，并保留 excluded/suspicious 统计。

## 注意事项

- 私有参考论文 PDF 未包含在仓库中。论文草稿会引用它作为本地参考论文，并沿用其 `Res.`/`J` 双指标评价风格。
- 当前实验结果主要用于支撑“局部有效、场景敏感、需要可信评价”的结论。
- ReAct、多智能体调度、自动切换 EOH/ReEVO 框架和后训练机制均属于未来展望，不属于当前最小实现主线。
