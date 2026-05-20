# Omni-VRP: Towards Omni-generalizable Neural Methods for VRP 复现报告

## 论文基本信息

- 论文：Towards Omni-generalizable Neural Methods for Vehicle Routing Problems
- 论文链接：https://arxiv.org/abs/2305.19587
- 官方代码：https://github.com/RoyalSkye/Omni-VRP
- 会议：ICML 2023
- 任务：TSP、CVRP、多分布 VRP 泛化
- 本地复现状态：`plan-only`

## 研究问题

很多神经 VRP solver 在固定规模、固定分布上有效，但换规模或换分布后退化。Omni-VRP 研究跨规模、跨分布的 omni-generalization：模型能否在未见规模和未见分布上快速适应。

## 算法原理

Omni-VRP 使用 meta-learning 框架训练初始化模型，使模型在新任务/新分布上经过少量适应即可获得较好效果。其重点不是单一 CVRP 指标，而是泛化能力。

## 核心实现与代码框架

官方仓库说明使用 PyTorch，并给出环境：

- Python 3.8
- PyTorch 1.12.1
- CUDA 11.3 相关安装建议
- 代码包含 meta-training / adaptation 逻辑

复现要先确认 CVRP-only 配置，再考虑多任务。

## 方法级伪代码

```text
for meta-iteration:
    sample task distribution D
    sample train/test instances from D
    adapt model on train instances for few steps
    evaluate adapted model on test instances
    update initialization parameters

Inference:
    adapt initialized model on target distribution
    decode CVRP solutions
```

## 数据集

Omni-VRP 关注多规模、多分布。复现需记录：

- 训练规模集合。
- 测试规模集合。
- 坐标分布。
- CVRP demand/capacity 规则。
- 是否使用 benchmark 实例。

## 论文实验结果

论文声称其 meta-learning 框架在 TSP/CVRP 的 unseen size 和 unseen distribution 上优于普通神经方法。具体结果需按表格提取。

## 本地复现结果

本轮未运行。建议先不做完整训练，只做仓库审计和 CVRP small config：

```bash
git clone https://github.com/RoyalSkye/Omni-VRP
cd Omni-VRP
# 按 README 配置 conda / PyTorch 后寻找 CVRP-only eval
```

## 图表复现

未重画图。后续可画 seen vs unseen distribution gap。

## 差异分析

Omni-VRP 与当前 Go 的直接距离较远，但它提示我们：不要只在 RC101/d25/t=1.0 上调策略，必须跨 density、arrival scale、problem family 做泛化评估。

## 复现结论

结论：`plan-only`。作为长期训练方向有价值，不适合作为近期小复现主线。

## 下一步计划

1. 先完成 POMO/SGBS/HGS/NLNS。
2. 再审计 Omni-VRP CVRP-only 配置。
3. 把 Go 的 75-cell grid 作为泛化 benchmark。
