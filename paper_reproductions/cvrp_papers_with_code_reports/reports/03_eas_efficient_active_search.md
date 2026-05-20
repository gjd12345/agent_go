# EAS：Efficient Active Search for CO Problems

状态：`local-partial`  
代码：https://github.com/ahottung/EAS  
论文：https://openreview.net/forum?id=nO5caZwFwYu  
任务：TSP / CVRP / JSSP

## 论文基本信息

EAS 关注“推理时适应单个实例”。官方仓库说明该方法基于 POMO，面向 TSP、CVRP、JSSP，并包含论文使用的 instances 与 trained models。仓库还列出三种 EAS：embedding updates、added layer updates、tabular updates。

## 方法要点

- 不只训练一个通用模型，而是在求解某个实例时做少量参数/表更新。
- EAS-Emb 更新 embedding。
- EAS-Lay 更新额外层。
- EAS-Tab 更新 tabular 参数。
- 与 sampling、原始 active search 做对比。

## 代码与数据可用性

官方 README 写明依赖 Python >= 3.7、numpy、PyTorch，并说明实验曾在 NVIDIA V100 32GB 上运行，需要根据 GPU 内存降低 batch size。

CVRP 复现需要关注：

- `instances/`
- `trained_models/`
- `run_search.py`
- CVRP100 或 XE instances 的模型路径和 batch size

## 最小复现路线

建议先复现一个很小 batch 的 CVRP search：

```bash
git clone https://github.com/ahottung/EAS
cd EAS
python3 run_search.py \
  -problem CVRP \
  -method eas-tab \
  -max_iter 20 \
  -batch_size 16
```

具体 `model_path` 和 `instances_path` 需要从仓库目录中确认后补齐。CPU 可跑通流程，但有效速度通常需要 GPU。

## 对 Go 项目的价值

EAS 的思想非常适合我们的动态场景：不是一次性训练通用最优策略，而是对当前实例做短时自适应。对应到 Go：

1. 每个 cell 或每个 density/arrival_scale 维护一组策略参数。
2. 跑若干候选后，根据 evaluator 反馈更新参数。
3. ReAct 只负责解释失败和调参，不直接生成大段代码。
4. 参数可以是插入优先级权重：距离、容量剩余、等待时间、未来触发风险。

## 风险

- 官方设置偏 GPU，完整复现实验资源要求高。
- 依赖旧版 PyTorch，环境可能要 pin。
- 训练/搜索参数较多，直接大规模跑容易耗时。

## 结论

EAS 不一定第一个完整复现，但它是最适合转化成“Go 参数在线学习”的论文。短期建议先复现 EAS-Tab 小样本。
