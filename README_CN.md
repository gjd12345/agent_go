# agent_go 中文说明

本仓库是 LLM 启发式进化与 TOCC（Trace-Conditioned Operator-Card Controller）实验工作区，用于研究如何用运行 trace 选择 operator card，从而引导 EOH 在组合优化问题上生成更有效的启发式代码。

早期主线是 Go 程序里的 `InsertShips` 函数。当前主线已经扩展为 TOCC 自动化实验闭环：manifest 生成实验、RAG/operator card 注入、EOH 执行、trace 汇总、best code 记录和下一轮 card 选择。

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
- 当前 TOCC 报告、PPT 和实验摘要：`eoh_go_workspace/reports/auto_experiment_reports/`
- 论文阅读、related work 和方法笔记：`eoh_go_workspace/reports/paper_notes/`
- 历史 Guarded EOH-Go 表格、图和论文草稿归档：`archived_experiments/reports_20260619/`

## 主要产物

- 当前 TOCC 进展报告：`eoh_go_workspace/reports/auto_experiment_reports/tocc_current_progress_20260619.md`
- 当前 TOCC 进展 PPT：`eoh_go_workspace/reports/auto_experiment_reports/tocc_current_progress_20260619.pptx`
- 最优进化代码与 verified score 记录：`eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md`
- 当前实验报告索引：`eoh_go_workspace/reports/auto_experiment_reports/README.md`
- reports 目录说明：`eoh_go_workspace/reports/README.md`
- 旧版 Guarded EOH-Go 表格、图表和论文草稿：`archived_experiments/reports_20260619/`
- 阶段总结：`eoh_go/eoh_go_phase0_summary.md`

## 快速验证

clone 仓库后，先安装项目 Codex skills：

```bash
bash scripts/install_codex_skills.sh
```

这个脚本会把项目内的 TOCC 实验、PPT/画图、伪代码 skills 安装到 `$CODEX_HOME/skills`。说明见 `docs/codex_skills.md`。

在仓库根目录运行：

```powershell
go build -o mainbin_sa.exe .
python -m pytest tests/ -q
python -m unittest discover -s tests -q
```

## 开发工作流

### 编译

```bash
go build -o mainbin_sa.exe .
```

或使用 Makefile：

```bash
make build          # 编译主求解器
```

### 运行测试

**Python 单元测试（guard、operator、templates）：**

```bash
python -m pytest tests/ -q
```

**Go 基准集成测试（需要 solomon_benchmark 数据）：**

```bash
make test           # 运行 SA 求解器基准测试
```

### 代码质量

项目目前没有配置自动 Go 代码检查或格式化钩子。提交代码时请注意：

- 确保 `go build .` 无报错。
- 运行 `python -m pytest tests/ -q` 并确认所有测试通过。
- 保持 Python import 整洁；项目使用 `pytest` 和 `unittest`。

## 运行一组小规模 EOH 实验

运行 EOH 需要配置 DeepSeek/OpenAI-compatible API key。建议先在环境变量中设置：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_API_ENDPOINT="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
```

然后运行一个 RC101 的小网格：

```powershell
python -m eoh_go.experiments.grids.arrival_scale_grid `
  --root "." `
  --problem rc101.json `
  --density d25 --density d50 --density d75 `
  --arrival-scale 1.0 --arrival-scale 0.9 --arrival-scale 0.8 --arrival-scale 0.7 --arrival-scale 0.6 `
  --use-density-source-dirs `
  --llm-model deepseek-v4-flash `
  --output-dir eoh_go_workspace/reports/auto_experiment_reports/manual_eoh_arrival_grid `
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
