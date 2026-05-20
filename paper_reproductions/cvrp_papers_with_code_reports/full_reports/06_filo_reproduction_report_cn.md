# FILO: Fast Iterated Local Search for Large-scale CVRP 复现报告

## 论文基本信息

- 项目：FILO / Fast Iterated Local Search localized optimization algorithm for CVRP
- 项目页：https://acco93.github.io/filo/
- 官方代码：https://github.com/acco93/filo
- 任务：large-scale CVRP
- 本地复现状态：`plan-only / local-run candidate`

## 研究问题

FILO 关注大规模 CVRP 的快速局部搜索。问题不是训练一个策略，而是在大实例上用高效数据结构和 localized optimization 快速改善解。

## 算法原理

FILO 属于迭代局部搜索：

- 从初始可行解出发。
- 使用局部 move 改进。
- 通过 shaking/perturbation 跳出局部最优。
- 只在局部相关区域更新，降低大规模实例计算量。
- 反复执行“扰动 -> 重新优化”。

## 核心实现与代码框架

项目页给出 C++ 构建流程：

- 需要 COBRA 库。
- `cmake .. -DCMAKE_BUILD_TYPE=Release`
- `make -j`
- 执行 `filo` 读取 `.vrp` 实例。

可选 GUI 和 verbose 输出，但复现核心实验不需要 GUI。

## 方法级伪代码

```text
S = initial_solution(instance)
best = local_search(S)

while time budget not exhausted:
    S_perturbed = shake(best or current)
    S_local = localized_local_search(S_perturbed)
    if cost(S_local) < cost(best):
        best = S_local
    current = accept(S_local)

return best
```

## 数据集

FILO 面向 CVRPLIB 和 large-scale CVRP。复现时重点记录：

- `.vrp` 文件来源。
- 是否使用作者 docker 环境。
- release/native build。
- time budget。
- initial solution 生成方式。

## 论文实验结果

项目页说明该代码与大规模 CVRP 启发式论文相关，并提供结果复现环境说明。具体论文数值需下载作者提供环境或按论文表格重跑。

## 本地复现结果

本轮未运行 FILO。建议最小复现：

```bash
git clone https://github.com/acco93/filo
cd filo
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_VERBOSE=ON
make -j
./filo /path/to/instance.vrp
```

注意 COBRA 依赖是主要阻塞。

## 图表复现

未重画图。建议画 best cost 随 runtime 下降曲线。

## 差异分析

FILO 对 Go 的价值在性能工程：增量 cost、局部邻域、扰动强度、route cache。它比神经模型更容易转成 Go 代码。

## 复现结论

结论：`local-run candidate`，但依赖 COBRA。适合在 HGS 之后做工程迁移。

## 下一步计划

1. 确认 COBRA 依赖和构建方式。
2. 本地跑一个小 `.vrp`。
3. 提取可迁移 move：relocate、swap、2-opt、cross-route swap。
4. 在 Go 中实现局部搜索后处理。
