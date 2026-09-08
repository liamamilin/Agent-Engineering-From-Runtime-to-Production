# -*- coding: utf-8 -*-
"""维护工具：向 13 个章节 .qmd 注入/重建"完整案例"小节，并修复 Lab 悬空引用。

用法（在本书根目录运行）：
    python gen_case_sections.py
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

所有案例脚本**零第三方依赖**（纯 Python 标准库），任何 OpenAI 兼容 API（Ollama、DeepSeek、OpenAI 等）都可以使用。'''

OUTPUTS = {
"M0_first_agent.py": """\
问题：AgentLab 平台上学期开了多少门课？

--- 方式 A：直接调用 LLM ---
抱歉，我无法回答这个问题。我没有关于"AgentLab"平台任何课程数据的信息，
也无法访问该平台的内部系统。

--- 方式 B：Agent 循环（LLM + 工具） ---
[agent step 1] 工具调用: query_platform_stats({'platform': 'AgentLab'})
[agent step 1] 工具结果: {"courses": 12, "students": 300, "semester": "2026 春季"}
根据查询结果，AgentLab 平台在 2026 春季学期共开设了 12 门课程，注册学生数为 300 人。""",
"M1_model_runtime.py": """\
抽取结果：
{
  "title": "新产品上线评审",
  "date": "2026-09-10",
  "attendees": ["张伟", "李娜", "王强"],
  "decisions": [
    "确认 v2.3 版本于 9 月 18 日上线",
    "客服团队增加两人支援",
    "首页改版延后到下个季度",
    "下周三前完成压测报告"
  ]
}

校验结果：通过""",
"M2_tools.py": """\
>>> 任务：武汉现在多少度？比北京高还是低？
[step 1] 工具调用: get_city_weather({'city': '武汉'})
[step 1] 工具结果: {"condition": "晴", "temp_c": 33}
[step 1] 工具调用: get_city_weather({'city': '北京'})
[step 1] 工具结果: {"condition": "多云", "temp_c": 27}
[step 2] 模型给出最终答案
<<< 答案：武汉现在 33°C（晴），比北京（27°C，多云）高 6°C。

>>> 任务：帮我算一下 (128 + 72) * 3 等于多少？
[step 1] 工具调用: calculate({'expression': '(128 + 72) * 3'})
[step 1] 工具结果: 600
<<< 答案：(128 + 72) × 3 的结果是 600。""",
"M3_control_loop.py": """\
--- step=1/8 done=False stop_reason=None tool_calls=0 ---
[动作] read_file({'name': 'notes.txt'})
[结果] 9月8日 会议记录：1. 周五前提交周报（张伟）...

--- step=2/8 done=False ... ---
[动作] write_file({'name': 'todo.txt', 'content': '待办事项列表：...'})
[结果] 已写入 todo.txt（56 字符）

--- step=3/8 ... ---
[动作] finish({'summary': '已读取 notes.txt，将3条待办事项整理为"事项 - 责任人"格式并写入 todo.txt。'})

=== 终止：model_finish | step=3/8 done=True stop_reason=model_finish tool_calls=3 ===

--- todo.txt ---
待办事项列表：
1. 周五前提交周报 - 张伟
2. 下单新的服务器 - 李娜
3. 更新课程大纲 - 王强""",
"M4_eval_trace.py": """\
[PASS] price: ok
[PASS] refund: ok
[support] 空回答，用 temperature=0.7 重试一次...
[FAIL] support: ["应包含 '18' 但未找到", "应包含 '9' 但未找到"]
[PASS] school: ok
[PASS] unknown: ok
[infer] 空回答，用 temperature=0.7 重试一次...
[PASS] infer: ok (重试后通过, flaky)

通过率: 83% (5/6)

不稳定用例（首跑失败、重试才通过，生产上要重点盯）：
- [infer] 我和朋友各买一份学生版，一共多少钱？

失败分析（先归因到层，再决定修哪里）：
- [support] 问题: 晚上十点能找客服吗？
  回答: ''
  归因: 生成层（模型没有产出回答，常见于思考型模型被 max_tokens 截断）""",
"M5_context_budget.py": """\
>>> 用户：评估用的数据集是课程题库 v7，一共 1200 道题。
[budget] 超预算（224 > 180），压缩 4 条旧消息
[context] 本轮发送上下文 ≈ 146 tokens (预算 180)
<<< 助手：收到，已补充：评估数据集（课程题库 v7，1200 题）

>>> 用户：对了，服务器编号是多少来着？
[context] 本轮发送上下文 ≈ 142 tokens (预算 180)
<<< 助手：节点编号是 WH-01。

最终压缩摘要（系统提示中携带）：
- 评估服务：全量评估，节点WH-01
- 频率：每晚02:00
- 时长：约40分钟""",
"M6_grounding.py": """\
>>> 问题：服务器 WH-01 出了重大故障，多久内必须响应？打什么电话？
[retrieve] 命中 2 条证据：
  [1] (5分, server_ops.txt) 运维值班电话 027-888888，重大故障需 15 分钟内响应...
  [2] (4分, server_ops.txt) 生产服务器 WH-01 位于武汉机房...
<<< 回答：服务器 WH-01 作为生产服务器 [2]，若发生重大故障，需 15 分钟内响应，
运维值班电话为 027-888888 [1]。

>>> 问题：课程平台支持微信登录吗？
[retrieve] 命中 1 条证据：
  [1] (3分, course_policy.txt) 课程平台 AgentLab 的作业政策：每周三晚 23:59 截止提交...
<<< 回答：证据不足，无法回答。提供的证据仅涉及作业提交政策，未包含任何关于
登录方式的信息。""",
"M7_memory.py": """\
>>> [会话1] 用户： 你好，我叫小明，喜欢跑步，正在准备考研，目标是华中农业大学。
[memory] memory/memory.json 不存在，全新会话
[memory] 新提炼的记忆： ['姓名：小明', '爱好：跑步', '正在准备考研', '考研目标院校：华中农业大学']
[memory] 已保存 4 条记忆到 memory/memory.json

--- 模拟 Agent 重启（进程结束再启动）---

>>> [会话2] 用户： 你还记得我是谁吗？我最近该注意什么？
[memory] 从 memory/memory.json 加载了 4 条记忆
<<< [会话2] 助手：记得，小明！你最近在备考华中农业大学的研究生……加油，华农在等你！""",
"M8_plan_approve.py": """\
[规划] 为任务生成计划：为 90 分钟的班级技术分享会做筹备
  计划步骤 1: 确定分享主题与嘉宾，规划90分钟议程
  计划步骤 2: 预订教室，调试投影与麦克风等设备
  计划步骤 3: 发布通知邀请同学参加，提前一天彩排
[审批门] 步骤 1 -> 批准
[审批门] 步骤 2 -> 拒绝（脚本模拟，考察修订路径）
[修订] 步骤 2 修订为：提前2天收齐PPT统一16:9模板，当天提前1小时调试设备
[审批门] 步骤 2（修订版） -> 批准
[审批门] 步骤 3 -> 批准
[汇总] 3 个步骤执行完成""",
"M9_delegation.py": """\
[主 Agent] 接到任务：……是否引入 LLM 自动批改主观题的功能，请分析该不该做。
[委派] -> 需求分析师：分析引入LLM批改的需求、技术可行性、准确率风险及教学影响
[委派] -> 成本评估师：估算300名学生每晚全量LLM批改的API调用成本，对比人工批改ROI
[综合] 主 Agent 最终结论：
应引入，但采用"LLM初筛＋教师终审"模式。
理由：①ROI＞99%，月成本约$460对比人工$6万，首月即回本；②300人/晚远超人工负荷，
LLM吞吐完全可行；③须锚定评分标准并日抽检10%校准，防分数漂移。""",
"M10_guardrails.py": """\
>>> 问题：帮我看看怎么查自己的登录密码？
[guardrail] 输入拦截：命中敏感词 '密码'
<<< 答案：（输入被安全策略拒绝）

>>> 问题：图书馆周末几点开门？
[guardrail] 用量 113 tokens（累计 113/2000）
<<< 答案：一般高校图书馆周末开放时间为 8:00–22:00，但各校不同……

>>> 问题：再帮我总结一下这学期的选课建议。
[guardrail] 预算耗尽（已用 113/113 tokens），停止服务
<<< 答案：（预算耗尽，本轮服务已停止）""",
"M11_cli_agent.py": """\
$ python M11_cli_agent.py --task "用一句话介绍什么是 Agent" --max-steps 3
2026-09-07 21:32:05 INFO 启动 | model=qwen3.8:27b-mlx base_url=http://localhost:11434/v1 max_steps=3
2026-09-07 21:32:05 INFO step 1/3 开始调用模型
2026-09-07 21:32:16 INFO step 1 完成，tokens=294
2026-09-07 21:32:16 INFO 会话已保存: sessions/session_20260907_213216.json

=== 结果 ===
Agent（智能体）是一个能感知环境、自主决策并执行动作以达成目标的实体；
例如在 AI 课程中，AlphaGo 就是一个感知棋盘状态、自主选择落子的 Agent。""",
"capstone_agent.py": """\
[setup] 演示项目就绪：capstone_demo_project/（3 个文件）
[step 1] tokens=505 (累计 505/20000)
  -> list_files({})
[step 2] tokens=642 (累计 1147/20000)
  -> read_file({'name': 'README.md'})
  -> read_file({'name': 'main.py'})
  -> read_file({'name': 'todo.py'})
[step 3] tokens=1633 (累计 2780/20000)
  -> finish({...})

=== 项目理解报告（节选） ===
{
  "purpose": "taskcli：一个基于 Python 的命令行待办事项工具，支持 add/list/done 三个子命令",
  "entry_points": ["main.py"],
  "risks": [
    "todo.py: complete() 索引越界时直接抛出 IndexError，无友好提示",
    "main.py: 未对 sys.argv[1] 做存在性检查，未输入子命令将抛出 IndexError",
    "todo.py: open() 未使用 with 语句，存在资源泄漏风险"
  ]
}
[deliver] 报告已写入 capstone_report.json""",
}

CASES = [
    ("M0.qmd", "## 10. 小结", "## 10. 完整案例：直接调用 vs Agent 循环", "M0_first_agent.py",
     ["直接调用时，LLM 没有私有数据，只能拒绝或猜测",
      "Agent 循环 = LLM（决策）+ 工具（取数）+ 循环（推进）",
      "系统提示明确要求'先查工具再回答'，这是把心智模型落到提示上的做法",
      "本章其余各节解释的对象（Context、Model、Tool、Loop）在这个脚本里全部出现"]),
    ("M1.qmd", "## 10. Summary", "## 10. 完整案例：带重试与校验的结构化抽取器", "M1_model_runtime.py",
     ["`chat()` 是 mini 客户端：屏蔽 provider 差异 + 网络层重试 + token 用量跟踪",
      "`extract_json()` + `validate()` 落实'结构化输出必须解析再校验'",
      "格式失败时把错误信息喂回模型重试——Policy 层故障的修复方式",
      "业务逻辑（extract_meeting）与模型调用（chat）分离，Model 始终只是运行时依赖"]),
    ("M2.qmd", "## 10. Summary", "## 10. 完整案例：function calling 工具循环", "M2_tools.py",
     ["工具 schema 用 JSON Schema 描述，模型的'工具知识'完全来自 schema",
      "`execute_tool()` 在边界内执行；模型只产生调用意图，永远碰不到实现",
      "幻觉工具返回错误字符串而不是抛异常，让模型在下一轮自行纠正",
      "循环直到模型不再请求工具（给出最终答案）才结束"]),
    ("M3.qmd", "## 10. Summary", "## 10. 完整案例：状态与控制循环", "M3_control_loop.py",
     ["`AgentState` 集中全部可变状态：步数、历史、终止原因、工具记录",
      "`finish` 工具是模型主动终止的出口；`max_steps` 是兜底强制终止",
      "每步打印 `state.summary()`，让控制流完全可观察",
      "模型'只说不做'时被推回循环——控制权在循环手里，不在模型手里"]),
    ("M4.qmd", "## 10. Summary", "## 10. 完整案例：评估、追踪与失败分析", "M4_eval_trace.py",
     ["6 条用例覆盖正例、拒答、推断；检查是确定性的（关键词），可复现",
      "trace 记录输入、输出、token、延迟，落盘为 `outputs/eval_trace_M4.json`",
      "失败先归因到层（系统/生成/内容），再决定修哪里——本章的核心方法",
      "`infer` 用例首跑失败、重试通过，被标记为 flaky：不稳定用例要单独盯"]),
    ("M5.qmd", "## 10. Summary", "## 10. 完整案例：token 预算与历史压缩", "M5_context_budget.py",
     ["发送前用估算函数预检上下文规模，而不是等 API 报错",
      "压缩 = 旧历史交给模型提炼成摘要 + 保留最近 2 轮原文",
      "压缩摘要以 system 消息注入——所以'服务器编号'这类旧事实仍可被召回",
      "每次调用都打印当前上下文规模，让预算从隐形变可见"]),
    ("M6.qmd", "## 10. Summary", "## 10. 完整案例：检索、证据与拒绝编造", "M6_grounding.py",
     ["检索在生成之前：先命中相关句子，再让模型只基于证据作答",
      "字符 2-gram 打分是无依赖的朴素检索——RAG 的第一性原理，不依赖向量库",
      "回答必须标注 [1][2] 证据编号，可追溯到来源文件",
      "证据不足时模型被要求回答'证据不足'——拒答优于编造"]),
    ("M7.qmd", "## 10. Summary", "## 10. 完整案例：跨会话记忆持久化", "M7_memory.py",
     ["记忆 = 提炼出的长期事实，不是原始对话历史",
      "`save_memory()`/`load_memory()` 让记忆跨进程存活（原理同生产数据库）",
      "记忆提取是结构化输出问题，解析失败重试（复用 M1 的方法）",
      "新会话把记忆注入系统提示，模型因此'记得'用户"]),
    ("M8.qmd", "## 10. Summary", "## 10. 完整案例：计划、审批门与修订", "M8_plan_approve.py",
     ["先规划后执行：3 步计划生成后逐条过审批门",
      "`approve()` 是审批门的抽象：演示里用脚本代替真人，生产里换成 input() 或审批系统",
      "拒绝不终止工作流：被拒步骤回炉修订，修订版再次送审",
      "执行只发生在审批通过之后——人工控制在动作之前"]),
    ("M9.qmd", "## 10. Summary", "## 10. 完整案例：多 Agent 委派与综合", "M9_delegation.py",
     ["主 Agent 只做三件事：拆解、委派、综合，不亲自回答",
      "子 Agent 各有独立系统提示，互不共享上下文——传递的只有任务描述",
      "拆解是结构化输出：无效的 agent key 会被过滤并重试",
      "综合时附上每个子 Agent 的任务与产出，结论可追溯"]),
    ("M10.qmd", "## 10. Summary", "## 10. 完整案例：防护栏（预算/敏感词/超时）", "M10_guardrails.py",
     ["三道闸门顺序执行：输入过滤 -> 预算检查 -> 调用（带超时）-> 输出过滤",
      "token 预算是累计的：`record_usage()` 后超限即优雅停止，不抛异常",
      "敏感词在'模型看到前'和'用户看到前'两个位置各拦一次",
      "`events` 日志记录所有防护动作——防护栏本身必须可观察"]),
    ("M11.qmd", "## 10. Summary", "## 10. 完整案例：CLI、日志与会话落盘", "M11_cli_agent.py",
     ["argparse 提供 --task/--max-steps/--log：生产交付的第一形态是 CLI",
      "logging 双写控制台与 agent.log，出问题可回放",
      "每次运行的会话保存为 sessions/*.json，可审计、可复现",
      "失败也有序：异常被记录、以非零退出码退出"]),
    ("Capstone.qmd", "## 小结", "## 完整案例：项目理解 Agent（可运行的参考实现）", "capstone_agent.py",
     ["整合 M2/M3（工具 + 循环）、M5（读文件截断与预算）、M6（结论标注来源文件）、M10（token 预算）、M11（报告落盘）",
      "Agent 用 list_files/read_file 探索运行时生成的演示项目，再调用 finish 提交报告",
      "报告中的风险点均可追溯到具体文件——证据支持的声明，不是幻觉",
      "运行结束输出 capstone_report.json：结构化交付物（本章 TaskSpec 的最小满足版）"]),
]


def build_section(case_title, code_file, points, sec_anchor):
    with open(os.path.join(CODE, code_file), encoding="utf-8") as f:
        code = f.read().rstrip("\n")
    output = OUTPUTS[code_file]
    bullets = "\n".join(f"- {p}" for p in points)
    run_cmd = f"python code/{code_file}"
    if code_file == "M11_cli_agent.py":
        run_cmd = 'python code/M11_cli_agent.py --task "用一句话介绍什么是 Agent" --max-steps 3'
    return f"""\
{case_title} {sec_anchor}

完整脚本位于 `code/{code_file}`。{CONFIG_BLOCK}

### 运行方式

```bash
{run_cmd}
```

### 完整代码

::: {{.callout-note collapse="true"}}
## 点击展开完整代码

````python
{code}
````
:::

### 运行结果（真实输出节选）

```text
{output}
```

### 案例要点

{bullets}

"""


def main():
    for qmd, anchor, case_title, code_file, points in CASES:
        path = os.path.join(CH, qmd)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if "### 案例要点" in content:
            print(f"-- {qmd}: 已存在完整案例小节，跳过（如需重建请先移除旧小节）")
            continue
        sec_anchor = "{#sec-%s-case}" % qmd.split(".")[0].lower()
        if anchor not in content:
            print(f"!! {qmd}: anchor {anchor!r} not found, skipped")
            continue
        section = build_section(case_title, code_file, points, sec_anchor)
        content = content.replace(anchor, section + anchor, 1)
        content = content.replace(
            "见 `lab/README.md`。",
            "可直接运行的完整案例见本章末尾“完整案例”一节，脚本位于 `code/` 目录。")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK {qmd}: 注入 {code_file}")


if __name__ == "__main__":
    main()
