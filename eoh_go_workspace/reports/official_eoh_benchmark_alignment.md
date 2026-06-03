# 官方 EoH Benchmark 对齐审计记录

日期：2026-06-03

本文是 Phase A 资产审计记录，用于指导后续 `bp_online`、`tsp_construct`、`cvrp_construct` 的官方 benchmark 对齐。它是 agent 工作记录，不是论文最终结论。

## 总结

官方 EoH main 分支已经下载并解压到：

```text
/private/tmp/EoH-main
```

当前本地 `Agent_EOH` vendor 不完整：`Agent_EOH/eoh/src/eoh/problems/problems.py` 引用了 `tsp_construct` 和 `bp_online`，但 `Agent_EOH/eoh/src/eoh/problems/optimization/` 目录不存在。因此后续不能继续把本地 vendor 当成完整官方 benchmark。

官方 main 分支中，三项资产均存在：

| 对齐项 | 官方路径 | 本地 vendor 状态 | 审计结论 |
|---|---|---|---|
| `bp_online` | `/private/tmp/EoH-main/examples/bp_online` | 本地只有自定义 Go `ScoreBin` wrapper | 官方资产存在，优先接入 |
| `tsp_construct` | `/private/tmp/EoH-main/examples/tsp_construct` | 本地只有残缺引用 | 官方资产存在，优先接入 |
| `cvrp_construct` | `/private/tmp/EoH-main/examples/cvrp_construct` | 本地无完整注册/代码/数据 | 官方资产存在，但排在第三 |

## 官方目标函数

### `bp_online`

目标函数：

```python
def score(item: int, bins: np.ndarray) -> np.ndarray:
    return bins
```

语义：

- `item` 是当前待放入物品。
- `bins` 是所有 feasible bin 的剩余容量。
- 返回每个 bin 的 priority score，分数越高越优先。
- 目标最小化 used bins，相当于最小化 excess gap。

官方数据：

```text
examples/bp_online/testingdata/test_dataset_1k.pkl
examples/bp_online/testingdata/test_dataset_2k.pkl
examples/bp_online/testingdata/test_dataset_5k.pkl
examples/bp_online/testingdata/test_dataset_10k.pkl
examples/bp_online/testingdata/test_dataset_100k.pkl
```

seed/evaluation smoke：

```text
python3 runEval.py
Weibull 5k, 100, Excess: 3.98%
Weibull 5k, 300, Excess: 0.91%
Weibull 5k, 500, Excess: 0.50%
```

注意：上述 smoke 使用的是官方 `evaluation/heuristic.py` 中的示例启发式 `score = item - bins`，不是 `prob.py` 中 EoH template 的 `return bins`。

判断：PASS for evaluation。官方 BP `evaluation/runEval.py` 可在当前 Python 3.9 环境下直接运行；但如果 import `prob.py` 或运行 `runEoH.py`，仍会触发官方 EoH core 的 Python 3.10+ 要求。

### `tsp_construct`

目标函数：

```python
def select_next_node(current_node: int, destination_node: int,
                     unvisited_nodes: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
```

语义：

- greedy TSP construction 每一步选择下一个节点。
- `unvisited_nodes` 是候选未访问节点。
- objective 是平均 tour distance，越小越好。

官方数据：

```text
examples/tsp_construct/trainingdata/instances.pkl
examples/tsp_construct/testingdata/instance_data_10.pkl
examples/tsp_construct/testingdata/instance_data_20.pkl
examples/tsp_construct/testingdata/instance_data_50.pkl
examples/tsp_construct/testingdata/instance_data_100.pkl
examples/tsp_construct/testingdata/instance_data_200.pkl
```

注意：官方 `evaluation/runEval.py` 当前实际只跑 problem size `[20, 50, 100]`；`10` 和 `200` 数据文件存在，但不在默认 evaluation 列表中。

seed/evaluation smoke：

```text
python3 runEval.py
ModuleNotFoundError: No module named 'matplotlib'
```

进一步直接调用 `prob.py` 时，官方 main 分支触发 Python 3.10 语法需求：

```text
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

原因：当前系统 `python3` 是 3.9.6，而官方 `eoh/setup.py` 声明 `python_requires=">=3.10"`。

判断：WARNING。官方 TSP 资产完整，但当前环境需要 Python 3.10+，且 evaluation 需要补 `matplotlib` 或绕开 plotting import。

### `cvrp_construct`

目标函数：

```python
def select_next_node(current_node: int, depot: int,
                     unvisited_nodes: np.ndarray,
                     rest_capacity: float,
                     demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
```

语义：

- greedy CVRP construction 每一步选择下一个 customer。
- `unvisited_nodes` 已经过容量可行性过滤。
- 函数可以返回 `depot` 提前回仓。
- objective 是平均总路径距离，越小越好。

官方数据：

```text
examples/cvrp_construct/get_instance.py
```

官方 CVRP 使用随机实例生成器，不依赖外部 CVRPLib 文件。

seed/evaluation smoke：

```text
python3 runEval.py
Start CVRP evaluation...
Avg distance on 64 instances, 50 customers: 13.9964  time: 0.036s
```

判断：PASS for evaluation。官方 CVRP evaluation 可在当前 Python 3.9 环境下运行；但 EoH evolution 入口仍受官方 core 的 Python 3.10+ 约束。

## 环境差距

官方 main 分支要求：

```text
python_requires >= 3.10
install_requires = numpy, joblib
```

当前本机：

```text
python3 --version = Python 3.9.6
```

已观察到的缺口：

| 缺口 | 影响 | 建议 |
|---|---|---|
| Python 3.10+ 缺失 | 官方 EoH core 不能稳定 import | 新建 Python 3.11/3.12 venv |
| `matplotlib` 缺失 | TSP `evaluation/runEval.py` 失败 | 加入官方 benchmark venv requirements |
| 本地 `Agent_EOH` 是旧/残缺接口 | 不能直接跑官方 main examples | 官方 benchmark 单独走 external harness，不覆盖当前 `Agent_EOH` |

## 下一步建议

1. 新建独立环境，不污染当前项目：

```text
eoh_go_workspace/external/eoh_official/
```

或继续使用 `/private/tmp/EoH-main` 做只读源，复制最小必要 assets 到受控目录。

2. 先做 seed/evaluator wrapper：

```text
bp_online: 已可跑，优先封装 summary parser
tsp_construct: 先解决 Python 3.10+ 和 matplotlib
cvrp_construct: evaluation 已可跑，优先封装 summary parser
```

3. 再接入四臂对照：

```text
pure_eoh: 官方原始 prompt
api_only: 官方 prompt + 本项目固定 API contract
literature_rag: 官方 prompt + target-specific skill cards
history_rag: 官方 prompt + 历史有效候选/code examples
```

4. 五天交付优先级：

```text
第一优先：bp_online + cvrp_construct evaluation wrapper 和 smoke 表
第二优先：tsp_construct 环境修复后 smoke
第三优先：四臂 gen=1/pop=8 LLM 小矩阵
```

## 当前裁决

Verdict: WARNING

官方 assets 已确认存在，且 BP/CVRP evaluation smoke 可运行；但当前系统 Python 版本不足以直接运行官方 EoH main branch evolution。因此下一步应先准备 Python 3.10+ 独立环境和统一 wrapper，再启动 LLM 实验。
