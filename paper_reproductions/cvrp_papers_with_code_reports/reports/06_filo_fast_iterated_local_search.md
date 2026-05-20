# FILO：Fast Iterated Local Search for Large-scale CVRP

状态：`local-run`  
代码：https://github.com/acco93/filo  
项目页：https://acco93.github.io/filo/  
任务：Large-scale CVRP

## 论文基本信息

FILO 是面向大规模 CVRP 的快速迭代局部搜索方法。项目页说明它和 COBRA 一起提供论文相关源码与支持材料，并给出从 clone、build 到运行 `.vrp` 实例的命令。

## 方法要点

- 以局部搜索为核心。
- 通过 shaking / perturbation 跳出局部最优。
- 快速邻域评估，面向大规模实例。
- 重点不是训练，而是高效工程实现。

## 代码与数据可用性

项目页给出 C++ build 与运行命令：

```bash
git clone https://github.com/acco93/filo.git
./filo /path/to/instance.vrp
```

同时页面提到 GUI 可选项，但复现 benchmark 不需要 GUI。

## 最小复现路线

```bash
git clone https://github.com/acco93/filo
cd filo
mkdir build
cd build
cmake ..
make -j4
./filo /path/to/X-n101-k25.vrp
```

建议先用 CVRPLIB 小实例验证输出格式和 runtime，再扩大到大实例。

## 对 Go 项目的价值

FILO 的价值在于 move 设计和性能工程：

1. 给当前 SA/InsertShips 加局部改进后处理。
2. 借鉴局部 move 的增量 cost 计算。
3. 在 Go 里维护 route cache，避免每次全量重算。
4. ReAct 可以负责选择 shaking 强度和局部搜索预算。

## 风险

- 算法面向静态 CVRP，需适配动态调度。
- C++ 代码迁移到 Go 可能需要重写数据结构。
- 若只追求短 runtime，完整 FILO 预算可能过大。

## 结论

FILO 适合作为工程启发来源。建议在 HGS 之后复现，用来决定 Go 后处理局部搜索该实现哪些 move。
