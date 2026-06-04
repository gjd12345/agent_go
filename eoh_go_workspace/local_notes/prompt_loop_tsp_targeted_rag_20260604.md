# Prompt Loop: TSP targeted Literature-RAG 验证 + 多问题整理

创建时间：2026-06-04
目的：将 TSP targeted RAG 的 6.51118 signal 验证稳定 + 准备导师展示材料
预计总耗时：~1h (repeat) + ~3.5-10h (深度进化探索)
原则：每完成一个 Step，立即更新对应文档并 git commit，不堆积到最后一并处理
原则：每次完成后做文档留存和git提交
## 前置条件

```bash
# Gate 0: 确认环境
python3 -c "import os; assert os.path.isdir('/Users/guojiadong.9/agent_ad/agent_go'), 'project missing'"
python3 -c "import os; assert os.path.isdir('/private/tmp/EoH-main'), 'official EOH missing'"
PYTHONPATH=/Users/guojiadong.9/agent_ad/agent_go python3 -c "from eoh_go.rag.build_corpus import load_all_corpora; print('RAG OK')"

# Gate 1: 确认测试通过
PYTHONPATH=/Users/guojiadong.9/agent_ad/agent_go python3 -m unittest discover -s /Users/guojiadong.9/agent_ad/agent_go/tests -q
# 期望: 73 tests OK

# Gate 2: 确认 API 可用 (只检查布尔，不打印值)
# Env 文件: ~/.config/agent_go/chatrhino.env
# Env 变量: DEEPSEEK_API_KEY / DEEPSEEK_API_ENDPOINT / DEEPSEEK_MODEL
# 实际模型: JoyAI-LLM-Pro @ api.chatrhino.jd.com
source ~/.config/agent_go/chatrhino.env
python3 -c "
import os
k=os.environ.get('DEEPSEEK_API_KEY','')
e=os.environ.get('DEEPSEEK_API_ENDPOINT','')
m=os.environ.get('DEEPSEEK_MODEL','')
assert k, 'missing DEEPSEEK_API_KEY'
assert e, 'missing DEEPSEEK_API_ENDPOINT'
assert m, 'missing DEEPSEEK_MODEL'
print(f'API env OK: model={m}, endpoint_present={bool(e.strip())}, key_present={bool(k.strip())}')
"
```

---

## Step 1: TSP targeted RAG repeat=3 (init-only)

- **目的**: 验证 best=6.51118 稳定，排除单次随机波动
- **预计耗时**: 3×20min ≈ 60min
- **命令前缀**: `set -a; source ~/.config/agent_go/chatrhino.env; set +a`

```bash
# 三步串行，每步等前一步完成。用 caffeinate 防止熄屏中断。

REPEAT_DIR="eoh_go_workspace/local_runs/official_eoh_tsp_targeted_repeats_20260604"
PROJECT="/Users/guojiadong.9/agent_ad/agent_go"

set -a; source ~/.config/agent_go/chatrhino.env; set +a

for i in 1 2 3; do
  echo "========== TSP targeted RAG repeat $i/3 =========="
  echo "start: $(date '+%H:%M:%S')"
  
  caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
    --problem tsp_construct \
    --arm literature_rag \
    --rag-query "tsp construct select next node regret farthest insertion lookahead second best global route length" \
    --rag-top-k 2 \
    --rag-max-chars 2500 \
    --pop-size 4 \
    --generations 0 \
    --operators i1 \
    --n-processes 1 \
    --eval-timeout-s 40 \
    --llm-timeout-s 180 \
    --run-timeout-s 1800 \
    --output-dir "${REPEAT_DIR}/repeat_${i}" \
    --official-root /private/tmp/EoH-main \
    --python /private/tmp/eoh_official_venv/bin/python

  echo "end: $(date '+%H:%M:%S')"
  echo ""
done
```

### Step 1 验收

```bash
# Gate: 每个 repeat 的 summary 存在且 ok=true
for i in 1 2 3; do
  f="eoh_go_workspace/local_runs/official_eoh_tsp_targeted_repeats_20260604/repeat_${i}/official_eoh_run_summary.json"
  if [ -f "$f" ]; then
    python3 -c "
import json; d=json.load(open('$f'))
ok=d['run_summary']['ok']
best=d['run_summary']['best_objective']
cards=[c['id'] for c in d['rag_trace']['rag_selected_items']]
print(f'repeat $i: ok={ok}, best={best}, cards={cards}')
"
  else
    echo "repeat $i: MISSING summary"
  fi
done
```

**Pass 条件**:
- 3/3 ok=true
- 3/3 selected cards = tsp_regret_insertion + tsp_farthest_insertion
- best objective 均 ≤ 6.79（低于 api_only 基线）
- 记录 median 和 min

**Step 1 完成后文档提交**:
```bash
# 更新 TSP 结果文档 + 执行记录
git add eoh_go_workspace/local_notes/official_eoh_tsp_pop4_init_20260604.md
git add eoh_go_workspace/local_notes/official_eoh_plan_execution_note_20260604.md
git add .codex/goals/weekly_showcase.md
git commit -m "docs(tsp): record targeted literature-RAG repeat=3 results"
```

---

## Step 2: TSP targeted RAG 深度进化探索

- **前置**: Step 1 3/3 pass
- **目的**: 探索 generations 和 pop_size 扩展后，LLM 进化能否进一步改善
- **样本量估算**: init=2×pop, per_gen=pop。每样本 ~2.5min

| 配置 | 总样本 | 预计耗时 | 风险 |
|---|---|---|---|
| gen=1, pop=4 | 12 | ~30min | 最低 |
| gen=4, pop=8 | 48 | ~120min | 中等 |
| gen=8, pop=8 | 80 | ~200min (3.3h) | 需 caffeinate |
| gen=16, pop=8 | 144 | ~360min (6h) | **最后执行**，不阻塞其他任务 |

- **策略**: gen=1 → gen=4 → gen=8 串行，每级先看结果再决定是否开下一级。gen=16 排到最后，做完 gen=8 就转向 CVRP 和汇总，gen=16 有空再补。

### Step 2a: gen=1, pop=4（最轻量）

```bash
set -a; source ~/.config/agent_go/chatrhino.env; set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
  --problem tsp_construct \
  --arm literature_rag \
  --rag-query "tsp construct select next node regret farthest insertion lookahead second best global route length" \
  --rag-top-k 2 \
  --rag-max-chars 2500 \
  --pop-size 4 \
  --generations 1 \
  --operators i1 \
  --n-processes 1 \
  --eval-timeout-s 40 \
  --llm-timeout-s 180 \
  --run-timeout-s 2400 \
  --output-dir eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen1_pop4 \
  --official-root /private/tmp/EoH-main \
  --python /private/tmp/eoh_official_venv/bin/python
```

```bash
# 验收: 比较 gen=1 best vs gen=0 init best (6.51118)
python3 -c "
import json
f='eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen1_pop4/official_eoh_run_summary.json'
d=json.load(open(f)); s=d['run_summary']
print(f'gen={s[\"latest_generation\"]}, pop_size={s[\"population_size\"]}, best={s[\"best_objective\"]}, valid={s[\"valid_candidates\"]}')
print(f'init_best=6.51118, delta={s[\"best_objective\"]-6.51118:.5f}')
"
```

**Gate to Step 2b**: best ≤ 6.511（低于 init best 6.51118 即可进入下一级）

### Step 2b: gen=4, pop=8（探索中等进化深度）

```bash
set -a; source ~/.config/agent_go/chatrhino.env; set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
  --problem tsp_construct \
  --arm literature_rag \
  --rag-query "tsp construct select next node regret farthest insertion lookahead second best global route length" \
  --rag-top-k 2 \
  --rag-max-chars 2500 \
  --pop-size 8 \
  --generations 4 \
  --operators i1 \
  --n-processes 1 \
  --eval-timeout-s 40 \
  --llm-timeout-s 180 \
  --run-timeout-s 9000 \
  --output-dir eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen4_pop8 \
  --official-root /private/tmp/EoH-main \
  --python /private/tmp/eoh_official_venv/bin/python
```

```bash
# 验收
python3 -c "
import json
f='eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen4_pop8/official_eoh_run_summary.json'
d=json.load(open(f)); s=d['run_summary']
print(f'gen={s[\"latest_generation\"]}, pop_size={s[\"population_size\"]}, best={s[\"best_objective\"]}, valid={s[\"valid_candidates\"]}')
print(f'vs init=6.51118 delta={s[\"best_objective\"]-6.51118:.5f}')
"
```

**Gate to Step 2c**: best ≤ 6.51 + 有新的 best code 不同于 gen=1 的策略

### Step 2c: gen=8, pop=8（深度进化）

```bash
set -a; source ~/.config/agent_go/chatrhino.env; set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
  --problem tsp_construct \
  --arm literature_rag \
  --rag-query "tsp construct select next node regret farthest insertion lookahead second best global route length" \
  --rag-top-k 2 \
  --rag-max-chars 2500 \
  --pop-size 8 \
  --generations 8 \
  --operators i1 \
  --n-processes 1 \
  --eval-timeout-s 40 \
  --llm-timeout-s 180 \
  --run-timeout-s 14400 \
  --output-dir eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen8_pop8 \
  --official-root /private/tmp/EoH-main \
  --python /private/tmp/eoh_official_venv/bin/python
```

### Step 2d: gen=16, pop=8（最后执行，不阻塞其他任务）

```bash
set -a; source ~/.config/agent_go/chatrhino.env; set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
  --problem tsp_construct \
  --arm literature_rag \
  --rag-query "tsp construct select next node regret farthest insertion lookahead second best global route length" \
  --rag-top-k 2 \
  --rag-max-chars 2500 \
  --pop-size 8 \
  --generations 16 \
  --operators i1 \
  --n-processes 1 \
  --eval-timeout-s 40 \
  --llm-timeout-s 180 \
  --run-timeout-s 25200 \
  --output-dir eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/gen16_pop8 \
  --official-root /private/tmp/EoH-main \
  --python /private/tmp/eoh_official_venv/bin/python
```

### Step 2 结果汇总

```bash
for cfg in gen1_pop4 gen4_pop8 gen8_pop8 gen16_pop8; do
  f="eoh_go_workspace/local_runs/official_eoh_tsp_targeted_gen_20260604/${cfg}/official_eoh_run_summary.json"
  if [ -f "$f" ]; then
    python3 -c "
import json; d=json.load(open('$f')); s=d['run_summary']
print(f'${cfg}: gen={s[\"latest_generation\"]}, pop={s[\"population_size\"]}, best={s[\"best_objective\"]}, valid={s[\"valid_candidates\"]}')
print(f'  delta_vs_init={s[\"best_objective\"]-6.51118:.5f}')
"
  else
    echo "${cfg}: not run"
  fi
done
```

**Step 2a-c 完成后文档提交**:
```bash
git add eoh_go_workspace/local_notes/official_eoh_tsp_pop4_init_20260604.md
git add eoh_go_workspace/local_notes/official_eoh_plan_execution_note_20260604.md
git add .codex/goals/weekly_showcase.md
git commit -m "docs(tsp): record targeted literature-RAG gen1-8 evolution results"
```

---

## Step 3: CVRP card 审查

- **前置**: 不阻塞 TSP，可并行进行
- **目的**: 诊断 CVRP RAG 为什么变差 (14.49 vs 13.21 pure)，修复 cards

```bash
# 查看当前 CVRP skill cards
PYTHONPATH=/Users/guojiadong.9/agent_ad/agent_go python3 -c "
from pathlib import Path
from eoh_go.rag.build_corpus import load_all_corpora
corpus = load_all_corpora(Path('/Users/guojiadong.9/agent_ad/agent_go'))
cvrp = [c for c in corpus if c.id.startswith('cvrp_') and c.kind == 'algorithm_card']
print(f'CVRP algorithm cards ({len(cvrp)}):')
for c in cvrp:
    print(f'  [{c.id}] ({len(c.content)} chars)')
    print(f'  content: {c.content[:200]}...')
    print()
"
```

### Step 3 诊断清单

对每张 CVRP card 检查：
- [ ] `cvrp_nearest_capacity`: 是否过度强调 capacity 优先，忽略距离？
- [ ] `cvrp_capacity_slack`: 是否引导模型只填满车辆而非最小化总距离？
- [ ] `cvrp_sweep`: 极坐标 sweep 是否适合当前 50-customer 规模？
- [ ] `cvrp_savings`: 是否与官方 evaluator target 一致？
- [ ] `cvrp_regret_insertion`: regret 计算是否正确映射到 CVRP？

**修复后验证**:
```bash
# 重跑 CVRP init-only，期望 lit_rag ≤ pure_eoh
```

**Step 3 完成后文档提交**:
```bash
git add eoh_go_workspace/rag/corpus/algorithm_cards.jsonl  # 如有修改
git add eoh_go_workspace/local_notes/official_eoh_plan_execution_note_20260604.md
git commit -m "docs(cvrp): diagnose and fix CVRP literature-RAG cards"
```

---

## Step 4: 数据汇总

- **前置**: Step 1 + Step 2a-2c 完成（gen=16 不阻塞汇总）
- **产出**: 一个可复制粘贴到 PPT 的汇总表

### 汇总表

| problem | arm | best objective | delta vs pure | valid/pop | selected cards |
|---|---|---|---|---|---|
| `tsp_construct` | `pure_eoh` | 6.83907 | baseline | 4/4 | - |
| `tsp_construct` | `api_only` | 6.78953 | -0.04954 | 4/4 | - |
| `tsp_construct` | `lit_rag_default` | 6.83954 | +0.00047 | 4/4 | nearest_insertion, nearest_neighbor |
| `tsp_construct` | `lit_rag_targeted` | **6.51118** | **-0.32789** | 4/4 | regret_insertion, farthest_insertion |
| `tsp_construct` | `lit_rag_targeted_rep1` | (Step 1) | | | |
| `tsp_construct` | `lit_rag_targeted_rep2` | (Step 1) | | | |
| `tsp_construct` | `lit_rag_targeted_rep3` | (Step 1) | | | |
| `tsp_construct` | `lit_rag_targeted_gen1_pop4` | (Step 2a) | | | |
| `tsp_construct` | `lit_rag_targeted_gen4_pop8` | (Step 2b) | | | |
| `tsp_construct` | `lit_rag_targeted_gen8_pop8` | (Step 2c) | | | |
| `tsp_construct` | `lit_rag_targeted_gen16_pop8` | (Step 2d) | | | |
| `bp_online` | `pure_eoh` | 0.03984 | baseline | - | - |
| `bp_online` | `lit_rag_default` | 0.03984 | 0 | - | best_fit, first_fit |
| `cvrp_construct` | `pure_eoh` | 13.20696 | baseline | - | - |
| `cvrp_construct` | `lit_rag_default` | 14.49387 | +1.28691 | - | nearest_capacity, capacity_slack |

### 核心 narrative

1. **BP 不能证明 RAG**: 目标空间太小，pure EOH 已经找到强基线
2. **默认 RAG 不提升不是链路失败**: 是检索选卡太保守（nearest/nearest 与模型自发生成策略重合）
3. **Targeted RAG 有效**: 把 regret/farthest 拉进上下文后，best 从 6.84 → 6.51
4. **CVRP 需要 card 修复**: capacity 导向过强，需要平衡距离与容量

**Step 4 完成后文档提交**:
```bash
git add .codex/goals/weekly_showcase.md
git add eoh_go_workspace/local_notes/official_eoh_plan_execution_note_20260604.md
git commit -m "docs: aggregate multi-problem RAG comparison table for advisor showcase"
```

---

## Step 5: Git 提交

原则：每 Step 完成即提交，不堆积。实验产物 (`local_runs/`) 不入 git。

### 提交节奏

| 时机 | commit message | 涉及文件 |
|---|---|---|
| 初始（当前） | `docs(tsp): record targeted literature-RAG positive signal and prompt loop` | prompt_loop, tsp_pop4_init, plan_exec_note, weekly_showcase |
| Step 1 后 | `docs(tsp): record targeted literature-RAG repeat=3 results` | tsp_pop4_init, plan_exec_note, weekly_showcase |
| Step 2a-c 后 | `docs(tsp): record targeted literature-RAG gen1-8 evolution results` | 同上 |
| Step 3 后 | `docs(cvrp): diagnose and fix CVRP literature-RAG cards` | CVRP cards, plan_exec_note |
| Step 4 后 | `docs: aggregate multi-problem RAG comparison table` | weekly_showcase |
| Step 2d 后 | `docs(tsp): record targeted literature-RAG gen16 result` | tsp_pop4_init |

**禁止提交**:
```text
eoh_go_workspace/local_runs/**
.DS_Store
```

---

## 降级规则

| 阻塞 | 处理 |
|---|---|
| API 额度耗尽 | 等待恢复，记录已完成的配置 |
| TSP repeat 不稳定 (best 波动 > 0.3) | 说明 init-only 随机性大，多加 2 个 repeat |
| Step 2a gen=1 无改善 | 说明 deeper gen 可能无收益，但仍跑 gen=4 确认 |
| Step 2b/c/d 超时 | 降 pop_size 到 4，或分时段跑 |
| gen=16 耗时过长 | 改为晚间跑，或 skip gen=16 |
| CVRP cards 修后仍变差 | 暂不扩大 CVRP，记录为已知限制 |

## 最终交付物

1. `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/local_notes/official_eoh_tsp_pop4_init_20260604.md` — 更新 repeat+Gen1 结果
2. `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/local_notes/official_eoh_plan_execution_note_20260604.md` — 追加执行记录
3. `/Users/guojiadong.9/agent_ad/agent_go/.codex/goals/weekly_showcase.md` — 更新结果表+下一步
4. (可选) PPT 用汇总表 — 可从 Step 4 直接复制
