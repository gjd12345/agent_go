# NLNS：Neural Large Neighborhood Search for CVRP

状态：`local-partial`  
代码：https://github.com/ahottung/NLNS  
论文：https://arxiv.org/abs/1911.09539  
任务：CVRP / SDVRP

## 论文基本信息

NLNS 是专门针对 CVRP 的神经大邻域搜索。官方仓库说明它将 learned repair heuristic 集成到 LNS 框架中，支持 CVRP 与 split delivery VRP，并可在更长 runtime 下持续改进。

## 方法要点

- 从一个可行解开始。
- Destroy：移除部分客户或 route 片段。
- Repair：用神经网络修复被破坏的解。
- 多轮迭代，接受更优解或按搜索策略接受候选。

## 代码与数据可用性

仓库包含训练、搜索、batch search、single search 脚本，以及 `instances` 目录。Papers with Code 页面也将其列为 Neural Large Neighborhood Search for the CVRP 的代码。

可复现性中等偏高，但依赖年代较旧，完整训练可能需要重新整理环境。

## 最小复现路线

建议先跑单实例或小实例 search，而不是训练：

```bash
git clone https://github.com/ahottung/NLNS
cd NLNS
python3 search_single.py
```

若默认命令依赖模型路径，先根据 README 选择仓库已有模型/实例。下一步才尝试 `train.py`。

## 对 Go 项目的价值

NLNS 是当前 Go 项目最应该借鉴的结构之一。我们之前让 LLM 重写 `InsertShips`，本质上是“一次性全局变异”，不稳定。NLNS 提供更稳的方式：

1. SA 先生成可行解。
2. Destroy 只选择一小部分 ship/customer/route 重排。
3. Repair 用模板、LLM 或学习模型补回。
4. 用 evaluator 判定是否接受。

这比“整段 InsertShips 变异”更可控，也更容易调试失败模式。

## 风险

- 学习 repair 模型需要训练资源。
- 官方代码可能受旧依赖影响，需要环境修复。
- 我们的任务包含动态触发/时间演化，destroy/repair 需要定义在 dispatch 状态上。

## 结论

NLNS 是方法迁移优先级很高的论文。完整训练可以放后，但 destroy/repair 框架应该尽快迁移进 Smart Operator。
