"""EOH runner support package.

当前主线内容：问题/目标规格注册表（registry / problem_spec / target_spec）。
RAG 上下文组装的主线入口在
``eoh_rag.experiments.rag_context_builder.build_official_rag_context``；
failure_case 语料由 ``eoh_rag.rag.failure_cases`` 提供（curated）。

历史说明：早期 InsertShips v0 的 RAG runner（runner.py）、其配置（config.py）
与候选分类守卫（candidate_guard.py）已归档到 ``legacy/eoh_runner_v0/``，
不再属于主线，也不再从本包导出。
"""
