# NLNS: Neural Large Neighborhood Search 复现报告

## 论文基本信息

- 论文：Neural Large Neighborhood Search for the Capacitated Vehicle Routing Problem
- 论文链接：https://arxiv.org/abs/1911.09539
- 官方代码：https://github.com/ahottung/NLNS
- 任务：CVRP、SDVRP
- 本地复现状态：`plan-only / local-partial candidate`

## 研究问题

很多神经构造式方法一次性生成完整解，后续很难继续改进。传统 LNS 能在长运行时间下不断改进，但 destroy/repair 规则依赖人工设计。NLNS 的问题是：能否用神经网络学习 repair heuristic，把学习模型嵌入 LNS。

## 算法原理

NLNS 从一个可行解开始，每轮执行：

1. Destroy：移除部分客户或 route 片段。
2. Repair：用神经 attention 模型把被移除客户重新插入。
3. Evaluate：计算新解成本与可行性。
4. Accept：按搜索策略接受或拒绝。

它的优势是可以随运行时间继续搜索，而不是一次 forward 后结束。

## 核心实现与代码框架

官方仓库包含：

- `train.py`：训练神经 repair 模型。
- `search.py` / `search_single.py` / `search_batch.py`：执行 LNS 搜索。
- `repair.py`：repair 逻辑。
- `instances/`：论文使用的实例集合。

README 明确描述了 destroy/repair 框架和 CVRP/SDVRP 支持。

## 方法级伪代码

```text
Input: initial feasible solution S
best = S

for iteration = 1..T:
    removed = destroy(S)
    S_candidate = neural_repair(S without removed, removed)
    if feasible(S_candidate) and cost(S_candidate) < cost(best):
        best = S_candidate
    S = accept(S, S_candidate)

return best
```

## 数据集

NLNS 使用 CVRP 与 SDVRP 实例，仓库包含 XE instances。复现时要记录：

- instance set。
- destroy size。
- search runtime，例如 60s 以上。
- 是否使用训练好的 repair model。
- 与 LKH/HGS/OR-Tools 等基线比较的 runtime budget。

## 论文实验结果

论文报告 NLNS 在 CVRP 和 SDVRP 上能利用更长 runtime 持续改进，并可处理真实规模实例。具体 gap/runtime 需要从论文表格和仓库配置中逐项提取。

## 本地复现结果

本轮未运行官方代码。建议最小复现先跑 search，不先训练：

```bash
git clone https://github.com/ahottung/NLNS
cd NLNS
python3 search_single.py
```

若默认脚本缺模型路径，先定位 README 中 checkpoint 或实例配置。

## 图表复现

未重画图。后续应画 runtime 增加时 best cost 的下降曲线。

## 差异分析

NLNS 对现有 Go 最直接。当前 Smart Operator 重写 `InsertShips` 的风险高；NLNS 提供更稳定框架：保留 SA 解，只局部 destroy/repair。

## 复现结论

结论：`local-partial candidate`。完整训练需要资源，但 destroy/repair 结构应优先迁移到 Go。

## 下一步计划

1. 跑官方 `search_single.py` smoke。
2. 把 Go 中一个 dispatch 解转成 route list。
3. 实现 destroy：移除 k 个 ship 或受触发影响的任务。
4. repair 先用模板/SA，后续再接学习模型。
