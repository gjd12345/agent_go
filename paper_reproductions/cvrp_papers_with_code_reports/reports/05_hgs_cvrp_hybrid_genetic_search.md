# HGS-CVRP：Hybrid Genetic Search for CVRP

状态：`local-run`  
代码：https://github.com/vidalt/HGS-CVRP  
论文：https://arxiv.org/abs/2012.10384  
任务：Canonical CVRP

## 论文基本信息

HGS-CVRP 是 Vidal 开源的 CVRP Hybrid Genetic Search 实现，包含 SWAP* 邻域。相比神经方法，它是强工程基线，更适合用来做结果上界、teacher solution 和 benchmark sanity check。

## 方法要点

- Giant tour 表示。
- Split 动态规划把 giant tour 切分成可行车辆路线。
- 遗传搜索维护多样化种群。
- 局部搜索含 SWAP* 等邻域。
- 惩罚项处理容量或车辆数约束，再逐步引导回可行域。

## 代码与数据可用性

GitHub README 给出命令形式：

```bash
./hgs instancePath solPath [-it nbIter] [-t myCPUtime] [-bks bksPath] [-seed mySeed] [-veh nbVehicles] [-log verbose]
```

这是 C++ 项目，通常比神经仓库更容易在本地 CPU 上复现。

## 最小复现路线

```bash
git clone https://github.com/vidalt/HGS-CVRP
cd HGS-CVRP
make
./hgs Instances/CVRP/X-n101-k25.vrp out.sol -t 10 -seed 1
```

如果仓库没有内置对应 instance，则从 CVRPLIB 下载一个标准 `.vrp` 文件。

## 对 Go 项目的价值

HGS-CVRP 对我们非常实用：

1. 作为 Go/SA baseline 的强对照。
2. 输出高质量路线，作为模板策略或 teacher。
3. Split 算法可直接启发 Go 里的 route-first cluster-second 改造。
4. 局部搜索 move 可迁移为 `InsertShips` 后处理。

## 风险

- HGS 是静态 CVRP，需要转换我们的动态实例。
- 如果目标是实时调度，HGS 的全局搜索预算要受限。
- 许可证和集成方式需确认，建议先作为外部 benchmark，不直接嵌入。

## 结论

必须复现。它不一定是论文创新最“AI”的方法，但最能告诉我们当前 Go/SA 到底离强 CVRP 启发式有多远。
