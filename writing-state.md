# Writing State

## Book Metadata

- title: Agent 工程：从运行时到生产（Agent Engineering: From Runtime to Production）
- author: 华中农业大学 大模型课程组
- book_type: 技术书（工程教程）
- target_reader: 要构建可靠 Agent 系统的工程师/学生
- total_parts: 7（基础/测量/信息与知识/控制架构/组合与生产/实战/Capstone）
- total_chapters: 18（M0–M11 + P1–P5 + Capstone）

## Chapter Manifest

| NN | Part | Chapter Title | File | Status | Notes |
|---|---|---|---|---|---|
| M0 | 基础篇 | Agent 系统心智模型 | chapters/M0.qmd | done | 含完整案例 M0_first_agent.py |
| M1 | 基础篇 | Model Runtime & Structured Interaction | chapters/M1.qmd | done | 含完整案例 M1_model_runtime.py |
| M2 | 基础篇 | Tools & Action Interfaces | chapters/M2.qmd | done | 含完整案例 M2_tools.py |
| M3 | 基础篇 | State, Control Loop & Termination | chapters/M3.qmd | done | 含完整案例 M3_control_loop.py |
| M4 | 测量篇 | Evaluation, Tracing & Failure Analysis | chapters/M4.qmd | done | 含完整案例 M4_eval_trace.py |
| M5 | 信息与知识篇 | Context Engineering & Working State | chapters/M5.qmd | done | 含完整案例 M5_context_budget.py |
| M6 | 信息与知识篇 | Retrieval, Grounding & Evidence | chapters/M6.qmd | done | 含完整案例 M6_grounding.py |
| M7 | 信息与知识篇 | Memory & Persistence | chapters/M7.qmd | done | 含完整案例 M7_memory.py |
| M8 | 控制架构篇 | Planning, Workflows & Human Control | chapters/M8.qmd | done | 含完整案例 M8_plan_approve.py |
| M9 | 组合与生产篇 | Delegation, Multi-Agent & Protocols | chapters/M9.qmd | done | 含完整案例 M9_delegation.py |
| M10 | 组合与生产篇 | Safety, Reliability & Resource Control | chapters/M10.qmd | done | 含完整案例 M10_guardrails.py |
| M11 | 组合与生产篇 | Production Delivery & Operations | chapters/M11.qmd | done | 含完整案例 M11_cli_agent.py |
| P1 | 实战篇 | Web-Grounded RAG（联网检索接地） | chapters/P1.qmd | done | 含完整案例 P1_web_rag.py，用 websearch.py |
| P2 | 实战篇 | Deep Research（迭代式深度调研） | chapters/P2.qmd | done | 含完整案例 P2_deep_research.py |
| P3 | 实战篇 | Human-Gated Research（计划-审批式调研） | chapters/P3.qmd | done | 含完整案例 P3_hitl_research.py，stdin 交互 |
| P4 | 实战篇 | MCP in Practice（最小 MCP 实现） | chapters/P4.qmd | done | 含完整案例 P4_mcp_minimal.py，单文件双模式 |
| P5 | 实战篇 | Terminal Coding Agent（沙箱修 Bug） | chapters/P5.qmd | done | 含完整案例 P5_coding_agent.py，沙箱 sandbox_p5/ |
| Capstone | 综合项目 | 项目理解 Agent | chapters/Capstone.qmd | done | 含完整案例 capstone_agent.py |

## Terminology

| Chinese | English | Abbrev | Notes |
|---|---|---|---|
| 模型运行时 | Model Runtime | — | M1 |
| 结构化输出 | Structured Output | — | M1 |
| 工具调用 | Function/Tool Calling | — | M2 |
| 控制循环 | Control Loop | — | M3 |
| 评估与追踪 | Evaluation & Tracing | — | M4 |
| 上下文工程 | Context Engineering | — | M5 |
| 检索接地 | Retrieval Grounding | — | M6 |
| 记忆持久化 | Memory Persistence | — | M7 |
| 人工确认 | Human in the Loop | HITL | M8 |
| 委派 | Delegation | — | M9 |
| 防护栏 | Guardrails | — | M10 |
| 生产交付 | Production Delivery | — | M11 |

## 2026-09-07 变更：每章完整可运行案例

用户要求：每章必须有完整、可运行的案例（不是代码片段），读者只需修改 LLM API 配置即可运行。

实现：

- 新增 `code/` 目录：13 个单文件脚本 + `code/README.md` + `.env.example`
- 每个脚本：零第三方依赖（纯标准库 urllib）、内置 mini 客户端、顶部 3 行配置区
  （`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL_ID`，任何 OpenAI 兼容 API 通用）
- 13 个章节 `.qmd` 在 Summary/小结 前新增"完整案例"小节：
  运行方式 + 完整代码（可折叠 callout）+ 真实运行输出节选 + 案例要点
- 修复各章 Lab 悬空引用（"见 lab/README.md" → 指向本章完整案例与 code/ 目录）
- `index.qmd` 重写"如何使用本书"：三步运行说明 + provider 配置对照表
- `gen_case_sections.py`：注入/重建案例小节的维护工具

验证（本地 Ollama 实跑）：

- 全部 13 个脚本实跑通过（`qwen3.8:27b-mlx` 为主，M4 用 `qwen3.5:9b-mlx`）
- M4 真实产出一条 flaky 用例与一个生成层失败样本，用于演示失败分析
- M5 真实触发两次历史压缩，压缩摘要中保留了被裁剪的服务器编号（召回成功）
- 结构校验：代码围栏/callout 配对平衡，章节锚点唯一，悬空引用清零
- 已知限制：本机未安装 quarto，未能执行 `quarto render` 终检；下次构建时注意查看
  collapse callout 在 html 输出中的渲染效果

## Open Issues

- [ ] 本机没有 quarto CLI，`quarto render` 未验证（结构校验已通过）
- [ ] M4 的 flaky/失败样本依赖模型行为，换模型后"运行结果节选"可能与新输出不完全一致（属预期，README 已说明）
- [ ] `agent_course_blueprint/projects/`（旧参考实现）与 `code/` 并存，Capstone 章两者都有引用，后续可统一
- [ ] M0/M10/capstone_agent.py 有未使用的 `import time`（无害）；因 M 章节嵌入代码是注入快照，改脚本需同步重建案例小节，暂缓
- [ ] 章节输出节选是某次实跑的快照：P1–P3 每次联网检索结果都不同（URL/字数会变），属预期；README 需保持"输出可能与书中不同"的说明

## 2026-09-08 变更：GitHub 发布与仓库修复

仓库：https://github.com/liamamilin/Agent-Engineering-From-Runtime-to-Production

- **修复 submodule**：code/ 内嵌 .git 导致首次 push 时 20 个案例脚本未入库
  （GitHub 显示为空 gitlink）；已删除 code/.git，脚本正式入库
- **API key 脱敏**：websearch.py / exa_search_test.py 移除内置 key，改为
  自动加载 code/.env（新增迷你 load_dotenv，环境变量优先）；code/.env 含
  真实 key 且被 .gitignore 忽略；.env.example 提供模板。缺 key 时报错并
  提示注册地址。文档（index.qmd / code/README.md / P1-P3 章节配置块）同步更新
- **仓库清理**：.gitignore 新增（__pycache__/.DS_Store/.Rhistory/.Rproj.user/
  _book/agent.log/sessions/memory/outputs/capstone_demo_project 等）；
  已从 git 跟踪中移除（git rm --cached）
- **CI 发布**：新增 .github/workflows/publish.yml（quarto-dev 官方 action，
  push 到 main 自动 render 并 deploy 到 GitHub Pages）。需在仓库
  Settings → Pages → Build and deployment → Source 选 "GitHub Actions"
- 验证：脱敏后 exa/parallel 双 provider 实跑通过，缺 key 报错路径验证；
  暂存树确认无任何 key 字符串；P 章节重生成后字节级校验通过
- **历史泄露处置**：旧提交 acaaea7 的 .Rproj.user（RStudio 编辑器快照）内含
  当时未脱敏的 websearch.py/exa_search_test.py；已用 git filter-branch 重写全部
  历史 + reflog expire + gc，本地所有可达提交零 key 命中；用户已 force-push。
  **旧 key 已公开暴露，已在 Exa/Parallel 后台轮换，新 key 只存 code/.env**
- **CI 渲染修复**：GitHub Actions 失败根因 = `quarto render` 不带参数会渲染
  _quarto.yml 里声明的全部格式，PDF 需要 LaTeX scrreprt + PingFang SC（CI 无）；
  本地下载 quarto 1.10.18（经 ghproxy 镜像）复现确认 HTML 20/20 全部通过、
  PDF 挂在 scrreprt.cls not found；workflow 改为 `render with: to: html`；
  本地 _book 抽查：18 章 HTML、折叠 callout、案例锚点（sec-P4-case 等）均正常。
  上线地址：https://liamamilin.github.io/Agent-Engineering-From-Runtime-to-Production/
  （前置条件：仓库 Settings → Pages → Source 选 "GitHub Actions"）
- **移除 PDF 格式**（用户决定只出 HTML）：_quarto.yml 删除 pdf 声明块，
  本地 `quarto render`（无参数）验证全绿 18 章；CI workflow 的 `to: html` 作为双保险保留

## 2026-09-07 变更：联网搜索封装 websearch.py（实战篇前置工作）

用户提供了 Parallel AI key（platform.parallel.ai），要求把联网搜索封装成可扩展模块。

- 新增 `code/websearch.py`：统一接口 `search()` / `fetch()` / `search_and_fetch()`，
  provider 可插拔（注册表 + 工厂模式），内置 exa 与 parallel 两个实现
- Parallel API：`POST https://api.parallel.ai/v1/search`（objective + search_queries + mode），
  `POST /v1/extract`（urls）；认证 header `x-api-key`；extract 不接受 `full_content`/空 `objective` 字段（422）
- 配置区支持环境变量覆盖：`WEBSEARCH_PROVIDER` / `EXA_API_KEY` / `PARALLEL_API_KEY`
  （2026-09-08 起改为 .env 机制，见上）
- 自检：`python websearch.py [--provider exa|parallel] "查询"` 两个 provider 实跑通过
- 约定变化：实战篇 P1–P3 将 `import websearch`（共享模块），不再是单文件自包含；P4/P5 仍单文件
- 后续：实战篇 P1 联网 RAG / P2 Deep Research / P3 HITL 调研 将基于本模块构建

## 2026-09-07 变更：实战篇 P1–P5

- 新增 Part"实战篇"插在 M11 之后、Capstone 之前，5 章完整深度（对齐 M 系列结构：
  Learning Objectives → Engineering Problem → Mental Model → Runtime Walkthrough →
  Minimal Implementation → Failure Modes → Engineering Upgrade → Lab → Evaluation →
  完整案例 → Summary；锚点 {#sec-p1-case}…{#sec-p5-case}）
- 新脚本：P1_web_rag / P2_deep_research / P3_hitl_research / P4_mcp_minimal / P5_coding_agent
- 新共享模块：websearch.py（P1–P3 复用；约定变化：实战联网案例不再是单文件自包含）
- 新维护工具：gen_p_chapters.py（幂等重生成 5 章，嵌入代码直接读 code/P*.py）
- 实跑验证要点：P1 拒答真实触发；P2 证据库 6 条/15000 字符 + 带引用报告；
  P3 逐项审批真实跳过步骤 2；P4 agent 完成 握手→发现→调用 全流程且原生 JSON-RPC 可手工调试；
  P5 真实修复 shop.py 的 final_price bug（红→绿 6 步）
- Parallel API 适配注意：/v1/extract 不接受 full_content / 空 objective 字段（422）

### 2026-09-07 变更：全书代码加小白注释

- code/ 全部 20 个脚本（13 个 M/Case + websearch + 5 个 P + exa_search_test）添加
  面向零基础读者的中文注释，共 +745 行注释；每个文件顶部 docstring 追加"如何阅读本文件"指引
- 验证：AST 对比（剥离 docstring 后逐节点比对）确认全部脚本**逻辑零变更**，
  章节中的"运行结果（真实输出节选）"因此仍然有效
- 章节同步：新增 rebuild_case_sections.py（替换式重建 M0-M11+Capstone 案例小节；
  gen_case_sections.py 是注入式、已存在会跳过）；13 章重建 + 5 个 P 章重生成
- 全书校验：18 章嵌入代码与脚本逐字节一致、围栏配对、锚点唯一，全部通过
- 注释约定：解释"做什么/为什么"而非逐字翻译；术语首次出现给白话解释
  （temperature/token/tool_calls/指数退避/2-gram/JSON-RPC/沙箱 realpath 等）；
  不注释显而易见的代码

### 复查修复（同日）

- **P3 真 bug 修复**：Guardrails.allow_evidence 只检查不累加 self.chars，证据预算从未生效；
  已修复（入库时 chars += len(text)），重新实跑并更新章节输出节选（4399 字符）
- **P4 代码坏味修复**：McpClient.request 的可变默认参数 request_id=[0]（跨实例共享计数器）
  → 改为实例属性 self.request_id；章节正文 4.1 片段本就是正确写法，无需改
- 清理未使用 import：P3 的 sys、websearch.py 的 field（M0/M10/capstone_agent 的未使用
  `import time` 属旧有小瑕疵，因 M 章节代码是 gen_case_sections.py 注入快照、改动会造成
  脚本与书中代码漂移，暂不动，见 Open Issues）
- 复查后回归：P4/P5/P3 全部重跑通过；结构校验（围栏/锚点/字节级代码一致/伪影）全绿；
  sandbox_p5/ 已再次清理

## Progress Log

- 2026-09-07: 13 章注入完整案例；新增 code/ 目录并全部实跑验证；index.qmd 与 code/README.md 更新
- 2026-09-07: 新增实战篇（P1–P5 + Capstone 前）：websearch.py 搜索封装（Exa/Parallel
  双 provider，实跑验证）；5 个实战脚本全部用 Ollama qwen3.8:27b-mlx + 真实联网实跑通过；
  5 个完整深度章节由新维护工具 gen_p_chapters.py 生成（代码从脚本注入，保证同步）；
  更新 _quarto.yml / index.qmd / code/README.md
- 2026-09-08: 仓库修复（submodule/清理/脱敏 .env 机制）+ CI 发布工作流；见"GitHub 发布与仓库修复"
