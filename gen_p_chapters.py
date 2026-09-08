# -*- coding: utf-8 -*-
"""维护工具：生成实战篇 5 章（P1-P5.qmd）。

每章结构对齐 M 系列：理论小节 + "完整案例"小节（从 code/P*.py 读取
真实代码嵌入，保证代码与脚本严格同步）+ Summary。

用法（在本书根目录运行，幂等，直接覆盖重生成）：
    python gen_p_chapters.py
"""
import os

BOOK = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(BOOK, "code")
CH = os.path.join(BOOK, "chapters")

CONFIG_BLOCK = '''
```text
LLM_BASE_URL  = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY   = "ollama"                      # 你的 API Key
LLM_MODEL_ID  = "qwen3.8:27b-mlx"             # 你的模型名
```

案例脚本**零第三方依赖**（纯 Python 标准库），任何 OpenAI 兼容 API（Ollama、DeepSeek、OpenAI 等）都可以使用。联网搜索的 key 属于私密信息，不写在代码里：把 `code/.env.example` 复制为 `code/.env` 并填入 key 即可（`.env` 已被 git 忽略），支持 **Exa**（[dashboard.exa.ai](https://dashboard.exa.ai) 注册）与 **Parallel**（[platform.parallel.ai](https://platform.parallel.ai) 注册）两家免费服务；`websearch.py` 会自动加载 `.env`，环境变量 `EXA_API_KEY` / `PARALLEL_API_KEY` / `WEBSEARCH_PROVIDER` 优先级更高。'''

# 每章的真实运行输出节选（来自本地 Ollama + 真实联网检索的实跑记录）
OUTPUTS = {
    "P1_web_rag.py": """\\
---------- ① 直答模式（不联网） ----------
>>> [直答] vLLM 现在怎么启动一个 OpenAI 兼容服务器？用什么命令？
[model] tokens: prompt=27 completion=1428
<<< 直答：
# vLLM 启动 OpenAI 兼容 API 服务器
## 最简命令（vLLM ≥ 0.6，推荐）
vllm serve <model_name_or_path>
……（直答一口气输出了上百行"教程"，但没有任何出处，无法核验）

---------- ② 接地模式（联网取证后回答） ----------
>>> [接地] vLLM 现在怎么启动一个 OpenAI 兼容服务器？用什么命令？
[search] 命中 3 条：
  [1] OpenAI 兼容服务器 | vLLM 中文站  https://vllm.hyper.ai/docs/inference-and-serving/openai_compatible_server/
  [2] OpenAI-Compatible Server - vLLM  https://www.aidoczh.com/vllm/serving/openai_compatible_server.html
  [3] 快速开始 | vLLM 中文站  https://vllm.hyper.ai/docs/getting-started/quickstart/
[check] 引用标注: 有 | 拒答: 否
<<< 接地回答：
vLLM 通过 `vllm serve` 命令或 Docker 容器启动 OpenAI 兼容服务器 [1]。示例命令：
vllm serve NousResearch/Meta-Llama-3-8B-Instruct --dtype auto --api-key token-abc123
依赖条件：Linux 系统、Python 3.9–3.12；NVIDIA GPU 用户可通过 `pip install vllm` 安装 [3]。

---------- ③ 拒答测试（证据不足时） ----------
>>> [接地] AgentLab 课程平台 4.0 版本内测的报名截止日期是什么时候？
[search] 命中 3 条：……（都是同名无关网站）
[check] 引用标注: 有 | 拒答: 是
<<< 接地回答：
根据检索到的证据无法回答。现有材料仅涉及 AgentLab 作为 AI Agent 技术实验平台 [1][3]，
均未提及"课程平台 4.0 版本内测"或其报名截止日期。""",
    "P2_deep_research.py": """\\
[question] 现在本地部署大模型（本地推理引擎）有哪些主流选择，各自适合什么场景？

[plan] 分解出 3 个子问题：
  - 2024-2025年主流本地大模型推理引擎有哪些，各自的核心架构和开源协议是什么？
  - 本地推理引擎在显存占用、量化支持（GGUF/AWQ/GPTQ）、并发吞吐量等指标上的对比如何？
  - 不同本地推理引擎分别适合哪些典型场景：个人调试、私有化部署、高并发服务、端侧设备？

[research 1/3] 2024-2025年主流本地大模型推理引擎有哪些……
  + 证据[1] https://blog.csdn.net/...（2500 字符）
  + 证据[2] https://adg.csdn.net/...（2500 字符）
  证据库：2 条 / 5000 字符
……（子问题 2、3 同样各命中 2 条）
[evidence] 证据库最终：6 条 / 15000 字符（预算 24000）

研究报告（节选）：
## 结论
本地大模型推理引擎可按"抽象层次"与"目标平台"两个维度分类，主流选择已形成以
llama.cpp 生态（Ollama、LM Studio）和 PyTorch 生态（vLLM、SGLang、TensorRT-LLM、TGI）
为两大主干的格局 [5]。……
## 关键发现
1. **五大引擎定位互补，覆盖从"零配置"到"极致性能"的全谱系。** vLLM 以 PagedAttention +
   连续批处理实现最高吞吐量，是生产级事实标准；Ollama 一键安装、零配置，但并发能力弱 [1][5]。
……
## 局限
- 性能实测数据仅覆盖 RTX 4090 24 GB 单一 GPU 及 M4 16 GB 等有限配置 [1]，
  缺少 AMD GPU、多卡分布式及数据中心级场景的对比数据。""",
    "P3_hitl_research.py": """\\
[question] 2026 年企业落地 AI Agent 的主要模式有哪些？

[计划]
  步骤 1. search: 企业 AI Agent 落地架构模式 单Agent 多Agent 编排 2025 2026 部署方式
  步骤 2. search: 2025 2026 企业 AI Agent 行业实践 案例 趋势 金融 制造 零售 落地路径
  步骤 3. synthesize: 将技术架构维度（单Agent、多Agent协作、编排/工作流等）与行业实践维度
（金融、制造、零售等场景的落地路径、成熟度、ROI）交叉整合，归纳出 3-5 种主要模式

[审批门] 批准该计划? a=批准全部 s=逐项审批 q=放弃: s
[审批门] 执行步骤 1（search: 企业 AI Agent 落地架构模式 单Agent 多Agent 编排 2025）? y=批准 n=跳过: y
[审批门] 执行步骤 2（search: 2025 2026 企业 AI Agent 行业实践 案例 趋势 金融 制造 零...）? y=批准 n=跳过: n
  [跳过] 步骤 2
[审批门] 执行步骤 3（synthesize: ...）? y=批准 n=跳过: y

[执行] 步骤 1: search("企业 AI Agent 落地架构模式 单Agent 多Agent 编排 2025 2026 部署方式")
  + 证据[1] https://www.homenew.cc/tech-trends/2026-04-30-multi-agent-orchestration/
  + 证据[2] https://blog.csdn.net/qq_56999332/article/details/161201121
[guard] 实际联网 1 次，证据 2 条 / 4399 字符

调研报告（节选）：
## 结论
2026 年企业 AI Agent 落地正沿"单 Agent → 多 Agent 协作（Agent Swarm）"路径演进，
已形成按任务复杂度区分的四类主流编排模式 [1][2]。然而多数项目仍停滞于 Pilot 阶段，
架构过度设计与工具层缺陷是核心瓶颈 [2]。
## 关键发现
- **四类落地模式与对应框架**：① 单 Agent + 固定工具链（适合强推理、轻量原型）；
  ② 多角色协作 + 流水线任务（CrewAI）；③ 复杂状态机 + 人机协作（LangGraph）；
  ④ 多 Agent 自由对话协商（AutoGen）[2]。
## 局限
- 证据 [1] 正文未加载，仅标题可提取"单 Agent → Agent Swarm"的演进判断，缺乏架构细节 [1]。
- 两篇证据均为技术博客/趋势解读，缺少经审计的企业级落地案例与量化 ROI 数据。""",
    "P4_mcp_minimal.py": """\\
$ python P4_mcp_minimal.py agent "计算 (250+150)*3 的结果，把'预算核算是 1200'作为一条笔记记录下来，然后告诉我现在几点、笔记簿里有几条"

[mcp] 握手成功: course-mcp-server (protocol 2025-06-18)
[mcp] 发现 4 个工具: ['calculator', 'current_time', 'note_add', 'note_list']
[step 1] MCP tools/call: calculator({'expression': '(250+150)*3'})
[step 1] 结果: 1200
[step 1] MCP tools/call: note_add({'content': '预算核算是 1200', 'topic': '预算'})
[step 1] 结果: 已记录，笔记簿现有 1 条
[step 1] MCP tools/call: current_time({})
[step 1] 结果: 2026-09-07 23:37:20 Monday
[final] 计算结果：(250+150)*3 = 1200；笔记已记录，当前时间 2026-09-07 23:37:20，笔记簿里共有 1 条笔记。
[mcp] server 子进程已关闭

$ printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"calculator","arguments":{"expression":"(128+72)*3"}}}\\n' | python P4_mcp_minimal.py server

{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "course-mcp-server", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "600"}], "isError": false}}""",
    "P5_coding_agent.py": """\\
沙箱: .../code/sandbox_p5
演示项目：shop.py 的 final_price 有 bug，test_shop.py 是验收测试

--- step 1/10 ---
[动作] list_dir({})
[结果] 沙箱文件：shop.py / test_shop.py

--- step 2/10 ---
[动作] read_file({'name': 'shop.py'})   read_file({'name': 'test_shop.py'})

--- step 3/10 ---
[动作] run_python({'name': 'test_shop.py'})
[结果] exit=1
Traceback (most recent call last): ... assert final_price(200, 25) == 150

--- step 4/10 ---
[动作] write_file({'name': 'shop.py', 'content': 'def final_price(...'})
[结果] 已写入 shop.py（138 字符）

--- step 5/10 ---
[动作] run_python({'name': 'test_shop.py'})
[结果] exit=0 / all tests passed

--- step 6/10 ---
[动作] finish({'summary': '修复了 final_price 的 bug：原实现直接返回 price * discount_pct
（200*25=5000），正确逻辑应为 price * (1 - discount_pct/100)。修复后测试全部通过。'})

=== 终止：model_finish ===

修复后的关键行：
return price * (1 - discount_pct / 100)""",
}

POINTS = {
    "P1_web_rag.py": [
        "直答（1428 tokens）输出长而无法核验；接地回答短而每个事实都带 [n]",
        "证据编号即引用号：组包时编号，回答时引用，读者可回溯原文",
        "证据不足时拒答优于硬编——拒答测试真实触发（同名无关网站不构成证据）",
        "搜索 provider 在 websearch.py 里切换（exa/parallel），案例代码零改动",
    ],
    "P2_deep_research.py": [
        "计划-执行-综合三段式：子问题分解是结构化输出，解析失败自动重试",
        "证据库全局编号即引用号：按 URL 去重，同一页面不重复入库",
        "双重预算：证据总字符（24000）+ 子问题数（3），成本可预估",
        "报告含'局限'一节：模型自己声明证据覆盖不到的方面，抑制过度自信",
    ],
    "P3_hitl_research.py": [
        "人的审批决定'做不做'，机器护栏决定'最多做多少'，两层正交",
        "逐项审批模式（s）演示了砍掉步骤 2 而不放弃整个计划",
        "审批门是真实 stdin 交互：自动化演示可用 printf \"s\\ny\\nn\\ny\\ny\" | python 管道",
        "所有联网动作都发生在审批通过之后；放弃（q）时零联网零花费",
    ],
    "P4_mcp_minimal.py": [
        "MCP 的本质是 JSON-RPC 2.0 over stdio：握手 → 发现 → 调用，纯标准库即可实现",
        "MCP 的 inputSchema 就是 JSON Schema，与 function calling 的 parameters 同构，转换零成本",
        "工具在协议层发现（tools/list）而非硬编码——server 换了工具，agent 代码不变",
        "单文件双模式：server 可独立手工调试（原始 JSON-RPC），agent 自动完成全流程",
    ],
    "P5_coding_agent.py": [
        "红-绿循环由模型自己驱动：跑测试→观察失败→改代码→再跑→通过→finish",
        "路径越界检查（resolve_in_sandbox）发生在每个工具入口，../ 逃逸直接拒绝",
        "run_python 用 subprocess 隔离：超时 10 秒、输出截断 1500 字符",
        "演示项目由脚本自动生成（含 1 个真实 bug），删掉 sandbox_p5/ 即可重置",
    ],
}


def case_section(slug, script, case_title, run_note):
    with open(os.path.join(CODE, script), encoding="utf-8") as f:
        code = f.read().rstrip()
    excerpt = OUTPUTS[script]
    points = "\n".join(f"- {p}" for p in POINTS[script])
    return f'''## 10. 完整案例：{case_title} {{#sec-{slug}-case}}

完整脚本位于 `code/{script}`。{run_note}

{CONFIG_BLOCK}

### 运行方式

```bash
cd code
python {script}
```

### 完整代码

::: {{.callout-note collapse="true"}}
## 点击展开完整代码

````python
{code}
````

:::

### 运行结果（真实输出节选）

以下输出来自本地 Ollama（`qwen3.8:27b-mlx`）+ 真实联网检索的实跑记录：

```text
{excerpt}
```

### 案例要点

{points}
'''


def write_chapter(slug, title, body, script, case_title, run_note, summary_lines):
    parts = [
        f"# {title}\n",
        body.rstrip(),
        "",
        case_section(slug, script, case_title, run_note),
        "## 11. Summary\n",
        "\n".join(f"- {line}" for line in summary_lines),
        "",
    ]
    path = os.path.join(CH, f"{slug}.qmd")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"写入 {path}")


# ============================ 章节正文 ============================

P1_BODY = r'''
## Learning Objectives

By the end of this module, the learner can:

- 说清"直答"与"接地回答"在工程上的本质差异：可核验性
- 实现证据组包（evidence packing）：编号、截断、去重
- 实现带引用的受限生成，并让模型在证据不足时拒答
- 理解搜索 provider 抽象：统一接口下可切换/新增搜索服务
- 评估联网 RAG 系统的失败模式并给出对应防护

## 1. Engineering Problem

M6 的检索接地建立在**本地语料**上：证据可控、可信、免费。但生产环境里，用户的问题大多关于**模型训练数据覆盖不到或已过时**的事实——新工具的用法、上周的发布公告、竞品的最新价格。这时只有两条路：

1. **直答**：模型凭参数记忆回答。风险三连：答案过时、细节编造、无法核验。
2. **联网接地**：先检索取证，再基于证据回答，每个事实标注出处。

本章把 M6 的接地管道从本地语料升级到真实网络，并解决三个工程问题：

- **证据从哪来**：搜索服务（Exa / Parallel / 未来的任何服务）如何抽象成可插拔组件
- **证据怎么喂**：网页原文又长又脏，如何组包成模型能用的证据块
- **什么时候闭嘴**：证据不足时如何让模型拒答而不是硬编

## 2. Mental Model

### 2.1 接地管道全景

```text
用户问题
    ↓
[检索] search(question) ──→ [提取] fetch(urls)
    ↓                            ↓
SearchHit 列表 ──────────→ PageContent 列表
    ↓
[组包] 证据块（编号 [1][2][3]，截断、去重）
    ↓
[受限生成] system prompt 三条铁律
    ↓
┌─────────────────────────────┐
│ 证据充分 → 带引用回答 [n]      │
│ 证据不足 → 明确拒答 + 缺什么    │
└─────────────────────────────┘
```

### 2.2 检索 provider 抽象

不同搜索服务的 API 形态各异（Exa 用 `query`，Parallel 用 `objective + search_queries`），但能力可归纳为两个动作：

| 动作 | 输入 | 输出 | Exa | Parallel |
|------|------|------|-----|----------|
| search | 查询词 | 命中列表（url/title/摘要） | `/search` | `/v1/search` |
| fetch | URL 列表 | 正文/摘录 | `/contents` | `/v1/extract` |

封装成统一接口后，调用方只依赖抽象，不依赖具体服务：

```text
调用方（P1/P2/P3）
      │ from websearch import make_provider
      ▼
make_provider("parallel")   ← 注册表 + 工厂
      ├── WebSearchProvider   统一接口
      ├── ExaProvider         /search + /contents
      ├── ParallelProvider    /v1/search + /v1/extract
      └── 未来新服务：一个子类 + @register，调用方零改动
```

这是**依赖倒置**在 Agent 工程里的直接应用：搜索服务是易变的外部依赖（换服务商、调价格、加配额），抽象层让变化被隔离在一个文件里。

### 2.3 证据组包三原则

1. **编号即引用号**：组包时给每条证据编 [1][2][3]，回答中出现的 [n] 可以直接回溯
2. **截断有度**：每条证据截到几百~两千字符——检索摘录通常已对齐问题，全文反而稀释注意力（M5 的预算思想）
3. **去重**：同一 URL 只进一次证据库（P2 的证据库进一步强化这一点）

### 2.4 拒答是一等公民

接地系统的价值不在"总能回答"，而在"知道什么时候回答不了"。证据与问题不相关时（比如搜回来的是同名无关网站），正确的输出是**拒答 + 说明缺什么**，而不是用最像的证据硬凑答案。这是 M4 失败分层里的 Knowledge 层问题的正确处理方式。

## 3. Runtime Walkthrough

### 3.1 直答 vs 接地的对照

```python
# 方式 A：直答——模型只凭参数记忆
reply = chat([{"role": "user", "content": question}])

# 方式 B：接地——联网取证后受限生成
hits, pages = provider.search_and_fetch(question, num_results=3)
context = build_context(hits, pages)          # 编号 + 截断组包
reply = chat([
    {"role": "system", "content": GROUNDED_SYSTEM},
    {"role": "user", "content": f"证据材料：\n{context}\n\n问题：{question}"},
])
```

### 3.2 受限生成的三条铁律

```python
GROUNDED_SYSTEM = (
    "你是带引用的问答助手。只根据给出的证据材料回答问题：\n"
    "1. 每个事实性陈述后标注来源编号，如 [1] [2]\n"
    "2. 证据材料里没有的信息，不要编造\n"
    "3. 如果证据不足以回答，明确说\"根据检索到的证据无法回答\"，并说明缺什么\n"
    "回答不超过 200 字。"
)
```

### 3.3 输出自检

回答结束后做两个机械检查：是否含引用标注（`[1]` 等）、是否触发拒答。这两个信号进入 M4 式的评估体系，就是联网 RAG 的最基本质量指标。

## 4. Minimal Implementation

### 4.1 证据组包

```python
def build_context(hits, pages, max_chars=900):
    blocks = []
    for i, (hit, page) in enumerate(zip(hits, pages), 1):
        text = (page.text if page and page.text else hit.snippet)
        text = text.replace("\n", " ").strip()[:max_chars]
        title = page.title if page and page.title else hit.title
        blocks.append(f"[{i}] {title}\n{hit.url}\n{text}")
    return "\n\n".join(blocks)
```

### 4.2 Provider 注册表（websearch.py）

```python
PROVIDERS = {}

def register(cls):
    PROVIDERS[cls.name] = cls
    return cls

def make_provider(name=None, **kwargs):
    name = (name or WEBSEARCH_PROVIDER).lower().strip()
    if name not in PROVIDERS:
        raise ProviderError(f"未知 provider: {name}")
    return PROVIDERS[name](**kwargs)
```

新增一个搜索服务 = 写一个 `WebSearchProvider` 子类（实现 `_search` / `_fetch`）+ 挂上 `@register`，仅此而已。

## 5. Failure Modes

| 层级 | 故障 | 示例 | 防护 |
|------|------|------|------|
| Knowledge | 检索命中无关页面 | 同名无关网站被当作证据 | 拒答机制 + 相关性二次过滤 |
| Knowledge | 模型引用编号幻觉 | 编造 [5] 但只有 3 条证据 | 输出自检：引用号必须 ≤ 证据数 |
| Context | 证据截断丢关键信息 | 命令行参数恰好被截掉 | 分段截断 / 用摘要对齐问题的摘录 |
| Resource | 搜索服务配额耗尽 | 免费额度用完 | 统一 ProviderError + provider 切换 |
| Policy | 该拒答却硬编 | 证据含糊时模型仍给出答案 | 提示词铁律 + 评估集覆盖拒答用例 |

**调试规则**：回答错了先看证据——证据里有没有？证据相关但答错是生成层问题；证据缺失却作答是流程问题（应拒答）。

## 6. Engineering Upgrade

从本案例到生产级联网 RAG：

1. **引用校验器**：机械检查回答中每个 [n] 的证据片段确实支持对应陈述（可用第二个模型判卷）
2. **多源交叉**：关键事实要求 ≥2 个独立来源支持
3. **结果缓存**：同一 query 的搜索结果缓存复用，降本提速
4. **新鲜度控制**：时效性问题强制要求近期发布日期的结果
5. **provider 降级链**：主力服务超时/配额耗尽时自动切换备用服务

## 7. Lab

构建你自己的联网 RAG，演示：

- 用 `websearch.make_provider()` 分别以 exa 和 parallel 回答同一个问题，对比命中质量
- 构造 3 个"证据不足"的问题，验证拒答率
- 给回答加引用校验：引用号超出证据数时报错

完整可运行的参照实现见本章末尾"完整案例"一节。

## 8. Evaluation

- 同一问题集上，接地回答的引用可回溯率（[n] 能否对应到真实证据）
- 拒答正确率：无证据问题被拒答、有证据问题不被误拒
- 组包后的上下文 token 占用是否在预算内

## 9. 与教学篇组件的关系

- **M6 检索接地**：本地语料检索 → 真实网络检索，评分检索被 provider 抽象替代
- **M5 上下文预算**：组包截断就是预算控制的检索场景应用
- **M4 评估追踪**：`[check] 引用标注/拒答` 两个信号可接入 trace
- **约定变化**：从本章起，实战案例通过 `import websearch` 复用共享模块（搜索 abstraction 只写一次）；P4/P5 仍保持单文件自包含

'''

P2_BODY = r'''
## Learning Objectives

By the end of this module, the learner can:

- 说清 Deep Research 与单轮问答的本质差异：多步计划与证据累积
- 实现计划-执行-综合三段式调研管道
- 实现带去重与预算的证据库（EvidenceStore）
- 产出带引用编号、含"局限"声明的研究报告
- 识别深度调研系统的成本失控点并设置护栏

## 1. Engineering Problem

P1 的联网 RAG 是**单轮**的：一次检索、一次回答。真实的研究任务往往做不到一步到位——"本地推理引擎该怎么选"这样的问题，一次搜索既覆盖不了广度，也撑不起结论的置信度。

Deep Research（深度调研）是 2025-2026 年 Agent 落地最热的形态之一，其工程本质是：

1. **计划**：把研究问题分解成若干可独立检索的子问题
2. **执行**：逐个检索，把证据累积进一个去重、限量的证据库
3. **综合**：基于全部证据写报告，每个结论可回溯到证据编号

本章实现这个骨架的最小可运行版本——没有花哨的反思循环，但三段式、证据库、预算控制一样不少。

## 2. Mental Model

### 2.1 三段式管道

```text
研究问题
   ↓
[计划] LLM 分解 → 子问题 1..3（结构化输出，可重试）
   ↓
[执行] for 子问题 in 计划:
          search_and_fetch(子问题)
          → EvidenceStore.add(url, title, text)
             ├─ URL 去重
             ├─ 字符预算（超预算拒绝入库）
             └─ 全局编号 [1][2][3]...
   ↓
[综合] 证据全部组包 → 研究报告
        ├─ 结论（3 句以内）
        ├─ 关键发现（每条带 [n]）
        └─ 局限（证据覆盖不到什么）
```

### 2.2 证据库是核心数据结构

Deep Research 与单轮 RAG 的分水岭是**证据的生命周期**：单轮 RAG 的证据用完即弃，深度调研的证据要跨多个检索步骤累积。因此需要显式的证据库对象，承担三件事：

| 职责 | 实现 | 为什么 |
|------|------|--------|
| 去重 | `seen_urls` 集合 | 不同子问题常命中同一页面 |
| 预算 | 总字符上限 | 证据无限累积 → 提示词爆炸（M5） |
| 编号 | 递增全局编号 | 编号即引用号，报告中可回溯 |

### 2.3 双重预算

- **子问题数上限**（`MAX_SUBQUESTIONS=3`）：限制搜索次数
- **证据总字符上限**（`MAX_EVIDENCE_CHARS=24000`）：限制上下文体积

没有预算的 Deep Research 是成本黑洞：模型"再多查一点"的倾向会无限放大。预算让成本**在开工前就可预估**：最坏情况 = 3 次搜索 + 24000 字符上下文 + 4 次模型调用。

### 2.4 "局限"节是对抗过度自信的工程手段

报告模板强制包含"局限"一节，让模型显式声明证据覆盖不到的方面。这把 LLM 常见的"什么都敢说"转化为"明确说自己不知道什么"——是一次廉价的可靠性投资。

## 3. Runtime Walkthrough

### 3.1 计划：子问题分解

```python
def plan_subquestions(question, max_attempts=3):
    messages = [
        {"role": "system", "content":
            "你是深度调研规划器。把研究问题分解成 "
            f"{MAX_SUBQUESTIONS} 个可以独立联网检索的子问题。"
            "子问题要具体、可搜索、互补而不重复，"
            '输出 JSON：{"subquestions": ["...", "..."]}，只输出 JSON。'},
        {"role": "user", "content": question},
    ]
    # ... extract_json 解析失败自动重试（M1 结构化输出模式）
```

### 3.2 执行：检索与入库

```python
for qi, sub in enumerate(subquestions, 1):
    hits, pages = provider.search_and_fetch(sub, num_results=2, max_chars=2500)
    for hit, page in zip(hits, pages):
        n = store.add(hit.url, title, text)   # 去重 + 预算 + 编号
```

### 3.3 综合：带引用报告

证据库整体组包（编号即引用号），要求报告按"结论 / 关键发现 / 局限"结构输出，每条发现标注 [n]。

## 4. Minimal Implementation

### 4.1 EvidenceStore

```python
class EvidenceStore:
    def __init__(self, budget_chars):
        self.budget_chars = budget_chars
        self.items = []          # 每条: {"url", "title", "text", "n"}
        self.seen_urls = set()

    def add(self, url, title, text):
        if url in self.seen_urls:
            return None                          # 去重
        used = sum(len(it["text"]) for it in self.items)
        remaining = self.budget_chars - used
        if remaining <= 100:
            return None                          # 预算耗尽
        text = text.replace("\n", " ").strip()[:remaining]
        self.items.append({"url": url, "title": title, "text": text,
                           "n": len(self.items) + 1})
        return self.items[-1]["n"]
```

## 5. Failure Modes

| 层级 | 故障 | 示例 | 防护 |
|------|------|------|------|
| Task | 子问题重复 | 两个子问题搜出同样的页面 | 提示词要求互补 + 证据库去重 |
| Knowledge | 检索源质量差 | 内容农场页面混入证据 | 综合时要求标注来源；升级时加域过滤 |
| Context | 证据超预算 | 提示词膨胀、成本失控 | EvidenceStore 硬预算 |
| Knowledge | 报告超出证据 | 模型用世界知识补足论证 | "只依据证据材料"指令 + 局限节 |
| Control | 子问题生成失败 | JSON 解析失败 | 重试（M1 模式），3 次后报错 |

**调试规则**：报告结论可疑时，先核对每个 [n] 指向的证据片段是否真的支持该结论——大多数"幻觉"其实是证据-结论错配。

## 6. Engineering Upgrade

1. **反思轮次**：综合前让模型评估"证据够不够"，不够则追加子问题（受总轮次预算约束）
2. **引用校验**：机械核对 [n] 存在性 + 用第二个模型核对证据-结论支持关系
3. **并行检索**：子问题相互独立，可并发搜索（M9 的思想提前预演）
4. **多源交叉验证**：关键结论要求多个独立来源
5. **缓存与断点续跑**：证据库落盘，崩溃后不重复搜索

## 7. Lab

构建你自己的 Deep Research，演示：

- 换一个研究问题跑通三段式，观察子问题分解质量
- 把 `MAX_EVIDENCE_CHARS` 调到 6000，观察预算早停行为
- 在综合前加一轮"证据是否充分"的自评估

完整可运行的参照实现见本章末尾"完整案例"一节。

## 8. Evaluation

- 子问题质量：互补性（互不重复）与可检索性（能否命中）
- 引用可回溯率：报告中的 [n] 是否都能对应到证据库条目
- 预算符合率：实际搜索次数与证据字符是否在上限内
- 局限声明质量：声明的缺口是否真实存在

## 9. 与教学篇组件的关系

- **M5 上下文预算**：证据库的字符预算就是 token 预算的证据侧变体
- **M6 检索接地**：单轮接地 → 多轮累积接地
- **M9 任务拆解**：子问题分解就是"拆解-委派"的单体版（拆给自己执行）
- **M4 评估**：预算符合率、引用可回溯率可直接进入评估数据集

'''

P3_BODY = r'''
## Learning Objectives

By the end of this module, the learner can:

- 把 M8 的审批门应用到真实联网任务（花钱且不可逆的操作）
- 实现两级审批：批准全部 / 逐项审批（可跳过单项）/ 放弃
- 实现与审批正交的机器护栏（搜索次数、证据预算）
- 理解"人的意图决定做什么，护栏决定最多做多少"的分层控制
- 识别审批疲劳等 HITL 特有失败模式

## 1. Engineering Problem

P2 的 Deep Research 全自动执行：模型分解、模型检索、模型综合。这在演示里没问题，但在生产里**联网是有成本、有外部副作用的操作**——搜索要花钱、抓取可能触发对方风控、调研方向可能根本不是用户想要的。

M8 已经建立了审批门的概念，但那是在虚拟文件系统上演练的。本章把它放到**真实联网场景**里，并补上第二层控制：

- **人工审批门**（HITL）：每一步执行前，人确认"做不做"
- **机器护栏**（Guardrails）：即使人批了，搜索次数、证据预算也不能超——防的是人的"全批"手滑和模型的过度倾向

两层正交：人管意图，护栏管额度。

## 2. Mental Model

### 2.1 两层控制

```text
研究问题
   ↓
[计划] LLM 产出结构化计划
        步骤 1. search: query_1
        步骤 2. search: query_2
        步骤 3. synthesize
   ↓
═══════════ 审批门（人） ═══════════
   a=批准全部   s=逐项审批   q=放弃
   逐项时还可跳过（n）单个步骤
═══════════════════════════════════
   ↓（仅被批准的步骤进入执行）
═══════════ 护栏（机器） ═══════════
   搜索次数 ≤ MAX_TOTAL_SEARCHES
   证据字符 ≤ MAX_EVIDENCE_CHARS
   URL 去重
═══════════════════════════════════
   ↓
[执行] 合规动作 → 证据库 → 报告
```

### 2.2 三种审批粒度

| 模式 | 命令 | 行为 | 适用 |
|------|------|------|------|
| 批准全部 | `a` | 计划原样执行 | 信任计划、赶时间 |
| 逐项审批 | `s` | 每步 y/n，可砍单项 | 想微调方向但不想重写计划 |
| 放弃 | `q` | 零执行 | 计划方向不对 |

逐项审批是关键设计：它允许**砍掉一个坏步骤而不放弃整个计划**——比"全有或全无"的粗粒度审批实用得多。

### 2.3 审批门与护栏的失效面不同

审批门失效于**人**（审批疲劳、误操作），护栏失效于**配置**（阈值定错）。两者同时失效才会出事故，这正是纵深防御（defense in depth）的意义。

## 3. Runtime Walkthrough

### 3.1 计划生成

模型输出的计划是结构化动作序列：`search` 步骤带可检索的 query，`synthesize` 步骤带综合说明。计划先打印给人看，人再决定怎么批。

### 3.2 审批门交互

```python
cmd = input("[审批门] 批准该计划? a=批准全部 s=逐项审批 q=放弃: ")
if cmd == "q":
    print("[abort] 用户放弃，未执行任何联网操作")
    return
if cmd == "s":
    executed = []
    for i, step in enumerate(steps, 1):
        if gate_step(i, step):        # y=批准 n=跳过
            executed.append(step)
    steps = executed
```

### 3.3 护栏检查

```python
class Guardrails:
    def allow_search(self):
        if self.searches >= self.max_searches:
            print(f"  [护栏] 搜索次数已达上限，拒绝")
            return False
        return True
```

注意顺序：护栏检查在执行入口，与审批结果无关——人批了 3 个搜索步骤，护栏上限是 4，一切正常；若上限是 1，第 2 步照样被拒。**审批不覆盖护栏，护栏不取代审批**。

## 4. Minimal Implementation

### 4.1 单步审批门

```python
def gate_step(i, step):
    while True:
        what = step.get("query") or step.get("desc") or ""
        cmd = input(f"[审批门] 执行步骤 {i}（{step['action']}: {what[:40]}）? "
                    f"y=批准 n=跳过: ").strip().lower()
        if cmd == "y":
            return True
        if cmd == "n":
            return False
```

## 5. Failure Modes

| 层级 | 故障 | 示例 | 防护 |
|------|------|------|------|
| Control | 审批疲劳 | 人对每一步都无脑按 y | 机器护栏兜底；计划要短 |
| Control | 计划粒度失衡 | 一步太大（不敢批）或太碎（审批烦） | 步骤数上限 + query 具体化 |
| Control | 非交互环境 | 服务端无 stdin | 对接审批系统/IM，stdin 仅用于教学 |
| Resource | 护栏过紧 | 预算太小导致 0 产出 | 最小可行预算 + 护栏触发时明确报告 |
| Policy | 放弃后残留 | q 之后仍有后台任务 | 放弃路径立即 return，不启动执行 |

**调试规则**：调研结果跑偏时，先看审批记录——是计划本身偏了（人的意图问题），还是执行偏了（护栏/检索问题）。

## 6. Engineering Upgrade

1. **计划修订路径**：M8 的"拒绝→修订→再审批"——人在 q 之外还能让模型改计划
2. **审批 UI**：stdin 换成 Web/IM 审批卡片，支持 diff 预览（这条 query 会搜什么）
3. **审计日志**：每一步"谁批的、何时批的、批了什么"落盘，事后可追责
4. **预算动态调整**：运行中允许人提升护栏上限（显式二次审批）
5. **幂等执行**：被跳过的步骤记录原因，重跑时不重复已批准部分

## 7. Lab

构建你自己的审批式调研，演示：

- 用 `a` 全批跑一遍，再用 `s` 逐项砍掉一个 search 步骤跑一遍，对比报告差异
- 把 `MAX_TOTAL_SEARCHES` 设为 1、计划 3 步搜索，验证护栏拒绝路径
- 给审批门加"修订"选项（e=修改 query 后批准）

完整可运行的参照实现见本章末尾"完整案例"一节。

## 8. Evaluation

- 审批有效性：被拒绝的步骤确实没有执行（零副作用）
- 护栏有效性：任何输入序列下，搜索次数与证据字符不超上限
- 粒度实用性：砍掉单项后计划仍能产出报告（而非整体报废）
- 交互成本：完成一次调研的最少人工操作次数

## 9. 与教学篇组件的关系

- **M8 计划与审批门**：虚拟场景 → 真实联网场景；脚本模拟审批 → 真实 stdin
- **M10 护栏与资源控制**：护栏类就是"输入过滤/预算/上限"三闸门的调研场景实例
- **P2 Deep Research**：同一管道加上"人"这个控制层
- **M4 评估**：审批与护栏的触发记录是现成的 trace 事件

'''

P4_BODY = r'''
## Learning Objectives

By the end of this module, the learner can:

- 说清 function calling 与 MCP 分别解决什么问题、为什么是互补的两层
- 用纯标准库实现 MCP 最小可用子集（JSON-RPC 2.0 over stdio）
- 实现 initialize 握手、tools/list 工具发现、tools/call 工具调用
- 用 subprocess 把 MCP server 接入 LLM 控制循环，工具动态发现而非硬编码
- 识别跨进程工具调用的新增失败面（进程崩溃、阻塞、协议版本）

## 1. Engineering Problem

M2 的工具循环里，工具实现和 agent 在**同一个进程**：`TOOLS` 字典就写在脚本里。这在教学里够用，但生产中工具往往有独立的生命周期——数据库客户端、浏览器自动化、公司内部系统——甚至需要被**多个不同的 agent/客户端复用**。

把每个 agent 都复制粘贴一遍工具实现显然不行。业界给出的答案是 **MCP（Model Context Protocol）**：一个标准化的"工具如何被发现与调用"的协议层。M9 讲了协议的"为什么"，本章动手实现协议的"怎么做"——用纯标准库写一个最小 MCP server，并让 LLM agent 通过它干活。

先纠正一个常见误解：**function calling 和 MCP 不是竞争方案**。

- **function calling** 解决"模型怎么表达要调用工具"（模型 ↔ 你的代码）
- **MCP** 解决"工具从哪来、怎么被多个客户端共享"（你的代码 ↔ 工具进程）

## 2. Mental Model

### 2.1 通信形态：JSON-RPC 2.0 over stdio

MCP 最常用的传输就是**每行一个 JSON-RPC 2.0 消息**，进程的 stdin/stdout 就是信道：

```text
Agent 进程                        MCP Server 进程
    │  {"method":"initialize",...}    │
    │ ─────────────────────────────→ │  握手：协议版本、能力、名字
    │  {"method":"notifications/initialized"}
    │ ─────────────────────────────→ │  通知（无 id，无需响应）
    │  {"method":"tools/list"}        │
    │ ─────────────────────────────→ │  工具发现
    │  ←──────── {"tools":[...]}      │
    │  {"method":"tools/call",...}    │
    │ ─────────────────────────────→ │  工具调用
    │  ←──────── {"content":[...]}    │
```

### 2.2 三条协议消息

| 消息 | 方向 | 作用 |
|------|------|------|
| `initialize` | 请求 | 协商协议版本、交换能力与身份 |
| `tools/list` | 请求 | 枚举 server 提供的工具及 JSON Schema |
| `tools/call` | 请求 | 调用工具，返回 `content` 与 `isError` |

另有 `notifications/initialized` 等**通知**：没有 `id`，不要求响应——区分请求与通知是协议实现的第一课。

### 2.3 两层互补架构

```text
┌────────────────────────────────────┐
│ LLM (function calling)             │  "我想调 calculator(250+150)*3"
│   ↕ 工具表 ←────────────┐           │
│ Agent 控制循环           │           │
│   ↕ JSON-RPC over stdio │ 同构转换   │
│ MCP Server              ▼           │  "工具从哪来"
│   calculator / time / notes         │
└────────────────────────────────────┘
```

关键观察：MCP 的 `inputSchema` 就是 **JSON Schema**，与 function calling 的 `parameters` 字段同构——所以"MCP 工具 → LLM 工具表"的转换几乎是零成本的字段改名。

## 3. Runtime Walkthrough

### 3.1 server 端：分派循环

```python
def run_server():
    for line in sys.stdin:                 # 一行一个 JSON-RPC 消息
        req = json.loads(line)
        method, params, request_id = req.get("method"), req.get("params") or {}, req.get("id")
        if method == "initialize":
            _reply(request_id, result={...})
        elif method == "tools/list":
            _reply(request_id, result={"tools": [...]})
        elif method == "tools/call":
            text, is_error = execute_tool(...)
            _reply(request_id, result={"content": [...], "isError": is_error})
        elif request_id is not None:
            _reply(request_id, error={"code": -32601, ...})   # 方法不存在
```

### 3.2 agent 端：动态工具发现

```python
mcp = McpClient()                    # subprocess 启动 server
mcp.handshake()                      # initialize + notifications/initialized
mcp_tools = mcp.list_tools()         # 工具表来自协议，不是硬编码
llm_tools = to_llm_tools(mcp_tools)  # inputSchema → parameters（同构转换）
# 之后进入 M2/M3 式工具循环，只是 execute 换成了 mcp.call_tool(name, args)
```

### 3.3 安全工具实现

`calculator` 不用 `eval()`（任意代码执行），而是用 `ast` 解析后**白名单遍历**：只允许数字、四则运算和括号——这是 M10"工具是最大攻击面"的具体化。

## 4. Minimal Implementation

### 4.1 请求-响应配对

```python
def request(self, method, params=None):
    self.request_id += 1
    self._send({"jsonrpc": "2.0", "id": self.request_id,
                "method": method, "params": params or {}})
    while True:
        resp = json.loads(self.proc.stdout.readline())
        if resp.get("id") == self.request_id:      # 只认自己的 id
            return resp["result"]
```

### 4.2 Schema 同构转换

```python
def to_llm_tools(mcp_tools):
    return [{"name": t["name"], "description": t["description"],
             "parameters": t["inputSchema"]} for t in mcp_tools]
```

## 5. Failure Modes

| 层级 | 故障 | 示例 | 防护 |
|------|------|------|------|
| Reliability | server 进程崩溃 | 工具实现抛未捕获异常 | server 捕获异常 → isError 响应 |
| Reliability | 响应错位 | 并发请求时读到别人的响应 | 请求-响应按 id 配对 |
| Control | stdin 阻塞 | server 卡死，agent 的 readline 挂起 | readline 超时 + kill 子进程 |
| Transition | 协议版本不匹配 | 客户端只支持旧版本 | initialize 返回版本，客户端校验 |
| Safety | 工具注入 | calculator 收到 `__import__('os')` | AST 白名单，禁止任意求值 |
| Resource | 状态进程化 | 笔记存 server 内存，进程死即丢 | 状态落盘（升级路径） |

**调试规则**：先用原始 JSON-RPC 手工调一遍 server（`printf '...' | python P4_mcp_minimal.py server`），排除协议层问题后，再去查 LLM 的工具选择——分层排障。

## 6. Engineering Upgrade

1. **真实 MCP SDK**：生产中用官方 SDK 获得完整协议（resources、prompts、sampling 等能力）
2. **传输升级**：stdio → Streamable HTTP/SSE，支持远程 server 与多客户端
3. **状态持久化**：note 工具落盘到文件/数据库
4. **工具版本化与鉴权**：工具带版本、调用带配额，防滥用
5. **健康检查**：agent 侧 ping server，异常自动重启子进程

## 7. Lab

构建你自己的 MCP 工具集，演示：

- 给 server 增加一个新工具（如 `word_count`），不改动 agent 代码，验证 agent 能"自动"发现并使用它
- 手工构造 JSON-RPC 消息调用一个不存在的工具，验证 -32601 错误路径
- 故意让工具抛异常，验证 isError 响应如何回到 LLM

完整可运行的参照实现见本章末尾"完整案例"一节。

## 8. Evaluation

- 协议符合性：握手→发现→调用的消息序列正确，通知无响应
- 动态性：server 工具集变化后，agent 无需改代码即可使用新工具
- 安全性：calculator 拒绝非算术表达式
- 生命周期：任务结束后子进程被正确关闭（无僵尸进程）

## 9. 与教学篇组件的关系

- **M2 工具循环**：工具执行从进程内字典 → 跨进程协议调用
- **M3 控制循环**：循环骨架完全不变，只有 execute 换了实现——好的抽象让控制层无感
- **M9 协议**：讲"为什么需要协议层"，本章给出协议层的最小实现
- **M10 安全**：AST 白名单是工具输入校验的典型手法

'''

P5_BODY = r'''
## Learning Objectives

By the end of this module, the learner can:

- 说清 Coding Agent 的核心循环：观察（跑测试）→ 修改 → 验证
- 实现文件系统沙箱：路径归一化 + 越界拒绝
- 安全地让 Agent 执行代码：subprocess 隔离、超时、输出截断
- 识别 coding 场景特有的失败模式（reward hacking、危险代码、死循环）
- 理解"能力越大，护栏越要硬"的能力-护栏匹配原则

## 1. Engineering Problem

Coding Agent 是当前 Agent 落地最成功的形态之一：读代码、改代码、跑测试、修 bug。但它是所有 Agent 形态里**接触面最危险**的——工具直接读写真实文件系统、执行真实进程。M3 的控制循环在虚拟文件系统上演练过，本章让 Agent 接触**真实文件**，因此必须先回答安全问题：

1. Agent 能碰哪些文件？→ **沙箱**（一个目录，路径越界拒绝）
2. Agent 能执行什么？→ 只能 `python <沙箱内的.py>`，带超时与输出截断
3. 出错了怎么兜底？→ 每个工具入口做边界检查，异常转化为工具结果回喂模型

在安全边界之内，Coding Agent 的工程核心是**红-绿循环**：跑测试看失败（红）→ 修改代码 → 再跑测试（绿）→ 结束。这个循环由模型自己驱动，控制循环只负责推进与终止。

## 2. Mental Model

### 2.1 闭环结构

```text
┌──────────────────── 沙箱 sandbox_p5/ ────────────────────┐
│  shop.py（含 bug）     test_shop.py（验收测试）            │
└──────────────────────────────────────────────────────────┘
        ↑ read/write            ↑ run_python（subprocess）
        │                       │
┌───────┴───────────────────────┴──────┐
│ LLM 工具循环                          │
│  list_dir → read_file → run_python   │
│  → [观察失败] → write_file(修复)      │
│  → run_python → [观察通过] → finish  │
└──────────────────────────────────────┘
   护栏：路径边界检查 | 超时 10s | 输出截断 | 步数上限
```

### 2.2 能力-护栏匹配

| 能力（工具） | 风险 | 必配护栏 |
|------|------|----------|
| read_file | 读到沙箱外文件 | 路径归一化 + 前缀检查 |
| write_file | 覆盖任意文件、写恶意代码 | 同上 + 沙箱内白名单行为 |
| run_python | 任意代码执行 | 仅限沙箱内 .py + 超时 + 输出截断 |

**原则**：工具的破坏力越大，入口检查越要硬——护栏检查在工具入口（防御点前移），而不是在模型输出的某个下游环节碰运气。

### 2.3 沙箱是信任边界的物理化

`../` 路径穿越、软链接指向外部——这些攻击都被同一个动作化解：`os.path.realpath` 归一化后再做前缀检查。归一化**先于**判断，是路径安全的第一规则。

## 3. Runtime Walkthrough

### 3.1 沙箱边界

```python
def resolve_in_sandbox(name):
    sandbox_root = os.path.realpath(SANDBOX)
    target = os.path.realpath(os.path.join(sandbox_root, name))
    if not target.startswith(sandbox_root + os.sep):
        raise PermissionError(f"路径越界：{name!r} 不在沙箱内")
    return target
```

### 3.2 受控执行

```python
def tool_run_python(args):
    path = resolve_in_sandbox(args["name"])
    if not path.endswith(".py"):
        return "错误：只能运行 .py 文件"
    try:
        proc = subprocess.run([sys.executable, path], cwd=SANDBOX,
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"错误：运行超过 {RUN_TIMEOUT} 秒被终止"
    output = (proc.stdout + proc.stderr).strip()[:OUTPUT_LIMIT]
    return f"exit={proc.returncode}\n{output}"
```

注意异常的流向：`PermissionError` 等异常**不冒泡终止循环**，而是转成文本结果回喂模型——模型会读到"错误：路径越界"，下一次就不再尝试。工具错误是给模型的信息，不是给程序的异常。

### 3.3 演示项目（自动生成）

脚本首次运行时在沙箱里生成一个带 bug 的 `shop.py` 与验收测试 `test_shop.py`。任务交给模型："跑测试、修 bug、再跑、finish"。

## 4. Minimal Implementation

### 4.1 工具循环（与 M3 同构）

```python
for step in range(1, max_steps + 1):
    reply = chat(messages)                  # 模型选工具
    calls = reply.get("tool_calls") or []
    if not calls:
        # 提醒模型：任务还没完成，继续用工具或 finish
        continue
    for call in calls:
        result = TOOL_IMPL[name](arguments)  # 沙箱内执行
        messages.append({"role": "tool", "content": result})
    if done:
        break
```

## 5. Failure Modes

| 层级 | 故障 | 示例 | 防护 |
|------|------|------|------|
| Safety | 路径穿越 | `read_file("../../etc/passwd")` | realpath + 前缀检查 |
| Safety | 恶意代码 | 写入并执行 `os.system(...)` | 沙箱 + 容器化（升级路径） |
| Resource | 死循环 | 被执行的代码 while True | run_timeout 强杀 |
| Policy | reward hacking | 模型改测试文件让断言通过 | 规则：测试文件不可修改；或 diff 审计 |
| Context | 输出截断丢信息 | traceback 关键行被截掉 | 截断保留头部与退出码 |
| Control | 不收敛 | 反复改不对直到步数上限 | 终止条件 + 失败报告 |

**调试规则**：Agent "修好了但测试是它自己改的"是最危险的失败——验收标准必须独立于被修改的产物，这是所有评估工作的元原则（M4 的延伸）。

## 6. Engineering Upgrade

1. **版本控制集成**：每次写文件前 git diff，可回滚、可审计
2. **规则注入**：把"测试文件不可修改"写进系统提示 + 写后校验
3. **容器级沙箱**：Docker/firejail 隔离，网络禁用，防恶意代码
4. **权限分级**：read 免审批，write/run 触发审批门（接 P3 的 HITL）
5. **多文件与重构**：工具升级为 patch/diff 应用，支持跨文件改动

## 7. Lab

构建你自己的 Coding Agent，演示：

- 故意让 agent 读 `../../secrets.txt`，验证路径越界拒绝
- 写一个含 `while True` 的脚本让 agent 运行，验证超时强杀
- 换一个更隐蔽的 bug（如边界条件 off-by-one），观察模型能否定位

完整可运行的参照实现见本章末尾"完整案例"一节。

## 8. Evaluation

- 修复成功率：真实 bug 被修复且测试通过（且测试文件未被改动）
- 护栏有效性：所有越界/超时尝试被拦截并转化为可读错误
- 效率：达到修复的平均步数与 token 成本
- 终止质量：成功路径以 finish 结束，失败路径以明确报告结束

## 9. 与教学篇组件的关系

- **M3 控制循环**：虚拟文件系统 → 真实沙箱文件系统
- **M10 安全与护栏**：路径检查、超时、输出截断是三闸门的 coding 实例
- **P3 审批门**：写文件/执行动作可升级为需人工审批的操作
- **M11 生产交付**：日志、会话落盘的做法直接复用

'''

CHAPTERS = [
    {
        "slug": "P1",
        "title": "P1 — Web-Grounded RAG（联网检索接地）",
        "body": P1_BODY,
        "script": "P1_web_rag.py",
        "case_title": "联网 RAG：从直答到接地",
        "run_note": "本案例需要在 `code/` 目录下运行（脚本通过 `import websearch` 复用共享搜索模块）。",
        "summary_lines": [
            "联网 RAG 的三铁律：引用可回溯、不编造、证据不足就拒答",
            "证据组包：编号即引用号、截断有度、URL 去重",
            "provider 抽象让搜索服务可插拔：统一接口 + 注册表 + 工厂",
            "直答与接地不是二选一：先直答保流畅，可疑事实触发接地",
        ],
    },
    {
        "slug": "P2",
        "title": "P2 — Deep Research（迭代式深度调研）",
        "body": P2_BODY,
        "script": "P2_deep_research.py",
        "case_title": "Deep Research：计划-执行-综合",
        "run_note": "本案例需要在 `code/` 目录下运行（脚本通过 `import websearch` 复用共享搜索模块）。",
        "summary_lines": [
            "Deep Research = 计划（分解子问题）+ 执行（累积证据库）+ 综合（带引用报告）",
            "证据库是核心数据结构：去重、预算、全局编号",
            "双重预算让成本开工前可预估：子问题数 + 证据总字符",
            "强制'局限'节把过度自信转化为明确的未知声明",
        ],
    },
    {
        "slug": "P3",
        "title": "P3 — Human-Gated Research（计划-审批式调研）",
        "body": P3_BODY,
        "script": "P3_hitl_research.py",
        "case_title": "HITL 调研：审批门 × 机器护栏",
        "run_note": "本案例包含真实 stdin 交互。纯自动演示：`printf \"a\\n\" | python P3_hitl_research.py`，逐项审批演示：`printf \"s\\ny\\nn\\ny\\ny\\n\" | python P3_hitl_research.py`。",
        "summary_lines": [
            "人工审批（做不做）与机器护栏（最多做多少）是正交的两层控制",
            "三种审批粒度：批准全部 / 逐项审批（可砍单项）/ 放弃",
            "逐项审批的关键价值：砍掉坏步骤而不报废整个计划",
            "审批疲劳是 HITL 的头号失效模式——护栏是兜底，不是摆设",
        ],
    },
    {
        "slug": "P4",
        "title": "P4 — MCP in Practice（最小 MCP 实现）",
        "body": P4_BODY,
        "script": "P4_mcp_minimal.py",
        "case_title": "MCP：纯标准库 Server + 动态工具发现",
        "run_note": "单文件双模式：`python P4_mcp_minimal.py server` 手工调试协议，`python P4_mcp_minimal.py agent \"任务\"` 跑完整 agent 流程。",
        "summary_lines": [
            "function calling 管'模型怎么选工具'，MCP 管'工具从哪来、怎么共享'——互补两层",
            "MCP 最小子集：initialize 握手、tools/list 发现、tools/call 调用（JSON-RPC 2.0 over stdio）",
            "inputSchema 与 function calling 的 parameters 同构，转换零成本",
            "工具动态发现：server 换工具集，agent 代码零改动",
        ],
    },
    {
        "slug": "P5",
        "title": "P5 — Terminal Coding Agent（沙箱修 Bug）",
        "body": P5_BODY,
        "script": "P5_coding_agent.py",
        "case_title": "Coding Agent：红-绿循环与沙箱",
        "run_note": "脚本首次运行会自动在 `code/sandbox_p5/` 生成含 1 个真实 bug 的演示项目；删除该目录即可重置。",
        "summary_lines": [
            "Coding Agent 的核心闭环：跑测试（红）→ 修改 → 再跑（绿）→ finish",
            "沙箱边界检查在每个工具入口：realpath 归一化先于前缀判断",
            "subprocess 隔离执行：超时强杀 + 输出截断 + 退出码回喂",
            "最危险的不是修不好，而是改了验收标准（reward hacking）",
        ],
    },
]


def main():
    for ch in CHAPTERS:
        write_chapter(
            slug=ch["slug"], title=ch["title"], body=ch["body"],
            script=ch["script"], case_title=ch["case_title"],
            run_note=ch["run_note"], summary_lines=ch["summary_lines"])
    print("完成：实战篇 5 章已生成")


if __name__ == "__main__":
    main()
