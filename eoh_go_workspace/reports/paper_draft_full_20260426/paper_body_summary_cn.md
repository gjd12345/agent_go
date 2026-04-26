# 面向实时动态调度的 Guarded EOH-Go 启发式代码进化研究

这是一份由 `eoh_go_phase0_summary.md` 提炼出的论文主体草稿。它只保留最终实现内容：动态密度源、arrival scale、Guarded EOH、filtered-best、repeat validation 和论文图表。早期错误尝试不作为主线，只作为引出 guard 必要性的背景。

核心结果：共 75 个 cell，清洗后有效 43 个；EOH improved 16、tie 11、worse 16；排除 32 个。最强单次改善是 RC105 d50 t=0.9，Delta J=-174.15。Repeat validation 显示 RC105 的部分 cell 更值得保留，但整体结论应保持“局部有效、场景敏感、需要 guard”。

完整正文请见 `guarded_eoh_go_full_draft_cn.tex`，编译 PDF 位于 `build/guarded_eoh_go_full_draft_cn.pdf`。
