# COMPASS：Policy Adaptation with Latent Space Search

状态：`local-partial`  
代码：https://github.com/instadeepai/compass  
论文：https://arxiv.org/abs/2310.01510  
任务：TSP / CVRP / JSSP

## 论文基本信息

COMPASS 是 NeurIPS 2023 项目，官方仓库说明它是一个通用组合优化框架，包含 TSP、CVRP、JSSP 的 JAX 实现，并提供训练、评估脚本、checkpoint 和数据文件。

## 方法要点

- 学习一个 conditioned policy。
- 条件来自连续 latent space。
- 推理时搜索 latent 条件，寻找适合当前实例的策略。
- 本质是“策略族 + 实例自适应搜索”。

## 代码与数据可用性

GitHub README 说明：

```bash
python experiments/train.py --config-name config_exp_cvrp.yaml
```

也提供 `validate.py` 和 `slowrl_validate.py`。依赖栈是 JAX，可能需要特定 CPU/GPU/TPU 环境。

## 最小复现路线

```bash
git clone https://github.com/instadeepai/compass
cd compass
pip install -e .
python experiments/train.py --config-name config_exp_cvrp.yaml
```

建议先改小配置：减少 instance 数、batch、训练步数，确认 pipeline。

## 对 Go 项目的价值

COMPASS 对我们的最大启发是“不要找一个策略，维护一族策略”：

1. Go 里可以定义多个 InsertShips template。
2. 每个 template 有参数向量。
3. ReAct/optimizer 在参数空间里搜索，而非改代码文本。
4. 对每个 cell 学一个 latent preference：偏快、偏稳、偏低成本、偏少超时。

## 风险

- JAX 环境在本机可能比 PyTorch 更麻烦。
- 完整训练资源需求较高。
- 直接迁移模型到 Go 不现实，更适合作为设计灵感。

## 结论

适合作为中长期方向。短期不要先完整训练 COMPASS，而是把它的“策略族/latent search”思想移植到 Smart Operator。
