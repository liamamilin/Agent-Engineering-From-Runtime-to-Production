# 代码目录：全书完整案例

本书每一章都配有一个**完整可运行的案例**。所有脚本：

- **零第三方依赖**：纯 Python 标准库（`urllib`/`json`/`argparse` 等），无需 `pip install`
- **单文件自包含**：每个脚本内置约 50 行的 mini LLM 客户端，复制到任何地方都能跑
- **只改 3 行配置**：OpenAI 兼容 API，本地 Ollama、DeepSeek、OpenAI、Moonshot 等都可以
- **面向零基础读者的注释**：所有脚本带中文注释，解释"这行在做什么、为什么"，
  术语（temperature、token、tool_calls、JSON-RPC……）首次出现都有白话解释；
  每个文件顶部 docstring 有"如何阅读本文件"指引。建议先读注释再读代码。

## 快速开始

1. 打开脚本，修改顶部的 3 个配置值：

```text
LLM_BASE_URL  = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY   = "ollama"                      # 你的 API Key
LLM_MODEL_ID  = "qwen3.8:27b-mlx"             # 你的模型名
```

2. 运行：

```bash
python M0_first_agent.py
```

## 案例索引

| 脚本 | 对应章节 | 案例 |
|------|----------|------|
| `M0_first_agent.py` | M0 | 直接调用 LLM vs Agent 循环对比 |
| `M1_model_runtime.py` | M1 | 带重试与校验的结构化抽取器 |
| `M2_tools.py` | M2 | function calling 工具循环（计算器 + 天气查询） |
| `M3_control_loop.py` | M3 | 多步任务 Agent：状态、终止条件、步数上限 |
| `M4_eval_trace.py` | M4 | 评估数据集 + trace 落盘 + 失败分层归因 |
| `M5_context_budget.py` | M5 | token 预算 + 旧历史压缩 + 事实召回 |
| `M6_grounding.py` | M6 | 本地语料检索 + 证据引用 + 拒绝编造 |
| `M7_memory.py` | M7 | JSON 文件持久化记忆，跨会话（模拟重启）召回 |
| `M8_plan_approve.py` | M8 | 计划 → 人工审批门 → 拒绝修订 → 执行 |
| `M9_delegation.py` | M9 | 主 Agent 拆解任务、委派两个专家子 Agent、综合结论 |
| `M10_guardrails.py` | M10 | 输入过滤 / token 预算 / 超时的三道防护闸门 |
| `M11_cli_agent.py` | M11 | argparse CLI + 日志双写 + 会话 JSON 落盘 |
| `websearch.py` | P1–P3 共用 | 联网搜索统一封装（Exa / Parallel 可插拔 provider） |
| `P1_web_rag.py` | P1 | 联网 RAG：直答对照 → 接地回答 → 证据不足拒答 |
| `P2_deep_research.py` | P2 | Deep Research：子问题分解 → 证据库 → 带引用报告 |
| `P3_hitl_research.py` | P3 | 计划-审批式调研：stdin 审批门 × 机器护栏 |
| `P4_mcp_minimal.py` | P4 | 单文件双模式 MCP：stdio server + 动态工具发现 agent |
| `P5_coding_agent.py` | P5 | 沙箱 Coding Agent：跑测试 → 修 bug → 再验证 |
| `capstone_agent.py` | Capstone | 项目理解 Agent（整合 M2/M3/M5/M6/M10/M11） |

**实战篇说明（P1–P5）**：

- P1/P2/P3 需要 `import websearch`（同目录共享模块），请在 `code/` 目录下运行；
  搜索 key 是私密信息，不写在代码里：把 `.env.example` 复制为 `.env` 并填入
  Exa / Parallel 的 key（`.env` 已被 git 忽略），`websearch.py` 会自动加载；
  环境变量 `EXA_API_KEY` / `PARALLEL_API_KEY` / `WEBSEARCH_PROVIDER` 优先级更高
- P3 是真实 stdin 交互，自动化演示可用管道：`printf "s\ny\nn\ny\ny\n" | python P3_hitl_research.py`
- P4 单文件双模式：`python P4_mcp_minimal.py server`（手工调试协议）、
  `python P4_mcp_minimal.py agent "任务"`（完整 agent 流程）
- P5 首次运行自动生成 `sandbox_p5/` 演示项目（含 1 个真实 bug），删除该目录即重置

## 运行时生成的文件

| 路径 | 由谁生成 | 说明 |
|------|----------|------|
| `corpus/` | M6 | 本地语料 txt 文件 |
| `memory/memory.json` | M7 | 持久化记忆（删除它即可重置记忆） |
| `outputs/eval_trace_M4.json` | M4 | 评估追踪记录 |
| `sessions/`、`agent.log` | M11 | 会话记录与日志 |
| `agent.log` | M11 | 运行日志 |
| `sandbox_p5/` | P5 | 沙箱演示项目（含 bug，删目录重置） |
| `capstone_demo_project/`、`capstone_report.json` | Capstone | 演示项目与理解报告 |

## 模型选择建议

- **工具调用类**（M0/M2/M3/M8/Capstone/P4/P5）：使用支持 function calling 的模型，建议 `qwen3.8:27b-mlx` 或云端 `deepseek-chat` / `gpt-4o-mini`
- **纯文本类**（M1/M4/M5/M6/M7/M9/M10/M11/P1/P2/P3）：任意指令模型即可
- **思考型模型**（如 qwen3 系列思考模式）：可能把 token 花在内部思考上导致答案为空，可调大脚本里的 `max_tokens`——这也是 M4/M10 案例演示的故障模式

## 全书小模型实测说明

书中"运行结果（真实输出节选）"均来自本地 Ollama 实跑：

- 基础/工具案例：`qwen3.8:27b-mlx`
- 评估案例：`qwen3.5:9b-mlx`（含一条真实的 flaky 用例与生成层失败，用于演示失败分析）

你的模型输出可能与书中不同（LLM 本身非确定性），这恰好是 M4 评估方法论要解决的问题。

实战篇（P1–P3）还叠加了**联网检索的非确定性**：每次搜索命中的网页、URL 与字数都会不同，
所以节选中的证据 URL/字符数与你运行时几乎必然不同——证据结构（编号、去重、预算）、
引用格式与拒答行为才是案例要观察的重点。

`websearch.py` 可独立自检：`python websearch.py --provider exa "查询"` 或
`python websearch.py --provider parallel "查询"`。
