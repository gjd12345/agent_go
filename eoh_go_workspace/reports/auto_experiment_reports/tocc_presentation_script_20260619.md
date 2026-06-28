# TOCC 进展汇报稿

对应 PPT：`tocc_current_progress_20260619.pptx`，共 12 页。预计汇报时间 15-20 分钟。

---

## 第 1 页：封面

> 老师好，今天汇报 TOCC 自动化实验闭环的当前进展。
>
> 一句话总结：我们已经从"手工选 RAG 卡片"推进到了一个完整的自动化闭环——trace 诊断、选卡门禁、manifest 执行、自动汇总、再到 history-card 记忆。
>
> 当前最可靠的正面证据来自 CVRP：在 8 次重复中全部优于 pure EOH，平均改善约 4.2%。TSP 有方向性信号但还不足以写成稳定结论；history-card memory 链路已打通，但收益尚未证明。

---

## 第 2 页：Why TOCC

> 我们为什么需要 TOCC？核心问题不是"有没有 RAG"，而是"RAG 往哪个方向引导搜索"。
>
> EOH 本身能生成和进化启发式代码，但它缺少系统性的搜索方向控制。普通 RAG 只是根据 query 检索 top-k 卡片塞进 prompt，出了问题很难归因——你不知道是检索错了、还是卡片本身有问题、还是生成坍缩了。
>
> TOCC 把这个过程变成了 trace-conditioned action：先读上一轮的 trace，诊断出搜索偏差，再决定选哪些 operator cards，经过 gatekeeper 校验后执行。失败时可以拆到 linkage 层、generation 层、objective 层分别归因。

---

## 第 3 页：Method Loop

> TOCC 的原理可以用一句话概括：控制 LLM 生成启发式程序时看到的先验。
>
> 类比来说，MCTS 有 selection policy 控制搜索树探索方向，Bayesian optimization 有 acquisition function 控制下一个采样点，TOCC 有 trace-conditioned card selection policy 控制 LLM 在生成代码时看到哪些 operator card 作为先验。
>
> 需要强调的是，这是概念类比而非形式等价——TOCC 的 action space 是离散的 card 子集，不具备 regret bound。但核心思想一致：不是让搜索随机跑，而是基于历史观测做方向性控制。
>
> 这张图展示了完整的闭环：trace → 诊断 → 选卡 → 门禁 → 执行 → 汇总 → 记忆 → 下一轮。

---

## 第 4 页：Operator Cards

> TOCC 的 action 是选卡，不是直接改代码。我们把 operator cards 分成四类：
>
> 第一类是 API constraint，这是手工编写的接口约束规则，固定放在 prompt 前面，保证函数签名和返回值正确，不参与检索竞争。
>
> 第二类是 literature card，来自文献中的经典启发式策略，比如 regret insertion、farthest insertion、savings heuristic。这些参与 top-k 策略检索。
>
> 第三类是 history card，从本项目最优代码自动合成。它也参与检索，但受到 gate 和 prior audit 的约束——必须小算子化，不能把整段最优代码压成一个复杂大卡。
>
> 第四类是 failure warning，来自历史失败经验，弱注入或不注入，只是提醒风险。
>
> 每张 strategy card 采用 Skill/When/Do/Fallback/Safety 的短指令格式，是过程指令，不是参考文档。

---

## 第 5 页：Code Map

> 这一页展示当前的代码结构。分为几层：
>
> 目标注册层定义了 TSP、CVRP、BP 等可进化目标。官方 runner 负责构造 RAG context 并调用 EOH。TOCC controller 做规则诊断或 LLM proposal。Gatekeeper 校验 proposal 的合法性和 prior decisions。Manifest runner 展开实验 arms。Auto summarizer 汇总结果并输出 success funnel 和 best code。RAG + Memory 层负责加载 cards、格式化 prompt、从 best code 生成 history card。
>
> 这些都是 Python 模块，官方 EOH 仍然负责实际的代码生成和评估。

---

## 第 6 页：Execution Flow

> V1 是纯规则 controller——读 summary，做规则诊断，输出 selected cards。
>
> V2 加入了 LLM proposer——LLM 可以提出更灵活的 proposal，但必须经过 rule gatekeeper 校验。Gatekeeper 会阻断被 audit 标记为 block 或 split_required 的 cards。
>
> V3 把 V2 接到了 runner 和 summarizer，形成 bounded loop：proposal → run → summary → 下一轮 trace。
>
> 需要强调的是，V3 仍然是受预算约束的小闭环，每轮有明确的 manifest、run count 和停止条件，不是无限自动跑大矩阵。

---

## 第 7 页：Success Funnel

> 这是我们的五层成功漏斗，参考了 HeuriGym 的四阶段错误分类并做了扩展。五层从上到下依次是：
>
> **第一层 Proposal Accept**：TOCC controller 或 LLM proposer 给出的实验方案，能否通过 gatekeeper 的校验？Gatekeeper 检查必填字段是否完整、card id 是否属于当前 problem、是否引用了被 prior audit 标记为 block 的 cards、有没有越权字段。如果这层失败，说明 controller 的 proposal 本身就不合法——可能是 card id 写错、引用了已被封禁的 history card、或者字段格式不符合 manifest schema。这层不涉及 LLM 生成代码，纯粹是实验配置的合法性检查。
>
> **第二层 Linkage**：你选的 cards 真的进入 LLM prompt 了吗？检查 `selected_card_ids`（controller 决定注入的卡）是否等于 `rag_trace.rag_selected_items`（实际进入 prompt 的卡）。失败原因包括：card id 在 corpus 中找不到、检索分数太低被挤出 top-k、prompt context 截断把卡切掉了。如果这层失败，后续所有结果都跟你的选卡策略无关——卡根本没注入，你在评价一个不受控的实验。
>
> **第三层 Generation**：LLM 生成的代码候选是否健康？检查 `valid_candidates >= ceil(0.5 × pop_size)`，即至少一半候选是合法可执行的。失败表现是 valid collapse——种群退化到只剩 seed 解，LLM 生成的代码全部因为 syntax error、API 不符、timeout 等原因被判无效。典型案例：`default_rag` 在 CVRP 上 5/5 出现 valid=1, pop=1，种群坍缩到只剩种子。表面看 objective 是 13.28（不差），但这根本不是搜索结果，只是 seed 回退。
>
> **第四层 Objective**：最终得分是否优于 baseline？检查 `best_objective` 是否优于 `pure_eoh` 的 mean。只有前三层都通过，这层的结论才有因果意义——否则你在评价一个 proposal 不合法、或卡没注入、或种群已坍缩的实验。这层失败说明 cards 方向本身不对，需要换策略。
>
> **第五层 Diagnosis**：TOCC 的诊断是否基于真实 trace 证据？检查诊断中引用的证据（比如"检测到 baseline overlap"或"valid collapse"）是否与实际 trace 数据一致。这层目前需要人工或独立 LLM reviewer 校验，无法全自动统计。它的价值在于：如果 controller 的诊断是错的（比如把正常结果误判为 failure），下一轮的选卡纠正就会走偏，形成错误反馈循环。
>
> 为什么需要这五层而不只看 objective？因为每层失败的应对策略完全不同：
>
> | 失败层 | 含义 | 应对 |
> |---|---|---|
> | Proposal Accept | 实验配置不合法 | 修 proposal 格式或解除 card block |
> | Linkage | 卡没进入 prompt | 检查 corpus/检索/context 长度 |
> | Generation | LLM 生成全废 | 减少 cards 数量/降低复杂度/换 API-only |
> | Objective | 策略方向不对 | 换 cards 组合 |
> | Diagnosis | 诊断偏差 | 校准 controller 规则或 LLM 提示 |
>
> 实际例子：default_rag 在 CVRP 的 objective 看似不差（13.28），但 generation 层 5/5 坍缩到 seed——这不是成功搜索，这是没搜索。如果不看漏斗中间层，你会误以为"RAG 效果还行"，但其实代码根本不是 LLM 搜索出来的。

---

## 第 8 页：CVRP Evidence

> CVRP 是当前最可靠的正面证据。
>
> pure_eoh 8 次平均 13.540，tocc_corrected 8 次平均 12.975，改善约 4.2%。关键是 8 次全部优于 pure 的均值——tocc 的最差一次（13.283）仍然好于 pure 的平均。
>
> 对照组 default_rag 5 次全部出现 generation collapse，种群退化到只剩 seed。注入的卡片是 `cvrp_far_first` + `cvrp_nearest_capacity`。
>
> 核心发现：tocc_corrected 和 default_rag 只差一张卡——把 `cvrp_nearest_capacity` 换成 `cvrp_regret_insertion`。换一张卡，从"全部坍缩"变成"全部有效 + 4.2% 改善"。这直接说明选卡本身就是有效的控制变量。
>
> 不过需要注意，8 次重复没有做统计检验，我们不写"统计显著"，只写"repeat-level positive signal"。

---

## 第 9 页：TSP Evidence

> TSP 的情况更复杂。gen=0 时方差极大——同一组 cards（regret + farthest）在不同 seed 下生成质量差异巨大，最好 6.189，最差 9.656。这说明 gen=0 下 LLM 单次生成的随机性太大。
>
> 但 gen=4 后情况改善了——有了进化选择压，差候选被淘汰。pure_eoh gen=4 均值 6.548，tocc gen=4 均值 6.456，改善约 1.4%，3 次中 2 次优于 pure mean。
>
> 当前只能写：TSP 在 gen=4 下出现 exploratory positive signal，说明 card 方向（regret + farthest）是对的，但还需要更多问题和更多 repeat 来支撑论文级的主张。

---

## 第 10 页：History-Card Memory

> history-card memory 链路已经打通：best code → 特征提取 → 合成 history card → 写入 corpus → 下轮检索 → 注入 prompt → 生成新代码。
>
> 但两轮 smoke 实验的结论是：naive 地把 history card 混进去，效果反而变差。naive mixed 中复合 history card 导致 14.210，远差于 literature-only 的 13.094。
>
> 我们做了拆分：把复合大卡拆成三张小 operator card，重新跑。拆分后最好的 split arm 得到 12.961，接近 literature-only 的 12.728，但仍未超过。
>
> 结论是：history prior 可以可控接入——有 gate、有 audit、有 prior decisions。但当前不能写成"history prior 带来收益"。更有价值的发现是方法论层面的：历史最优代码不能直接压成复杂大卡，必须拆成小 operator，并由 TOCC 基于 trace 选择。
>
> 补充说明：这里 naive mixed 和 literature-only 的 card 组合不同（mixed 用 history card 替换了 `cvrp_far_first`），且每组只有 n=1，所以不能做精确的 pairwise attribution。

---

## 第 11 页：Best Code Evidence

> 报告不能只写策略名称，必须展示代码实际怎么变的。这里列了三个代表性片段：
>
> TSP gen=4 的 best code 构造了 regret + farthest 的混合评分——不是简单 nearest neighbor，而是在当前距离、终点距离和节点间距上综合打分。这说明注入的 regret + farthest cards 确实影响了代码结构。
>
> CVRP literature-only 的 best code 做了距离归一化和远端客户优先策略，是当前 objective 最好的。
>
> CVRP history watchlist 的代码生成了 remaining-aware alpha 结构——根据剩余客户比例动态调整权重。这说明 history card 确实能引导生成特定结构，但 score 没有超过 literature-only。

---

## 第 12 页：Boundaries & Next

> 最后是写作边界和下一步。
>
> **不能写的**：TOCC 已证明统计显著提升、RAG 一定有效或无效、TSP/CVRP 已够支撑完整论文实验、History-RAG 已经带来收益、V3 可以自动跑大矩阵。
>
> **可以写的**：TOCC 是 trace-conditioned operator-card controller、工程闭环已完成、CVRP 有 repeat-level positive signal、success funnel 能解释 RAG 失败来源、history memory 已接入但需 gate/audit。
>
> **下一步**有三件事：
>
> 第一，把方法章节整理进论文初稿——写成 TOCC 扩展层，不覆盖原 Guarded EOH-Go 主线。
>
> 第二，选一个新问题或新的官方 benchmark，验证整个链路能否无人工补洞地跑通。不再继续堆 TSP/CVRP 的 repeat。
>
> 第三，固化 exploration analyst 角色——实时监控 valid rate、selected cards、context truncation，给出 continue/stop/换卡建议。
>
> 以上就是当前进展，请老师指正。

---

## 汇报注意事项

1. **如果被问"4.2% 有没有统计显著性"**：回答 n=8 全部优于 pure mean，但未做 t-test；可以补做，但样本量仍偏小。
2. **如果被问"为什么不继续扩 repeat"**：回答 CVRP 已经 8/8 全部正向，再扩只是缩小置信区间，更有价值的是验证新问题的迁移性。
3. **如果被问"history card 为什么反而变差"**：回答复合大卡引入了过多约束导致 LLM 生成空间被压缩；拆分后接近 literature-only 说明方向对了，但小卡还需要更好的组合策略。
4. **如果被问"跟 HeuriGym/HeurAgenix 的区别"**：回答 HeuriGym 做 benchmark（LLM 直接写代码），HeurAgenix 做运行时启发式选择，TOCC 做实验控制层面的 trace-conditioned context selection，三者互补不竞争。
