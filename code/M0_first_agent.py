# -*- coding: utf-8 -*-
"""
M0 完整案例 — 心智模型：直接调用 LLM vs 运行一个 Agent
========================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx（工具调用建议用较大模型）

运行：  python M0_first_agent.py

本案例演示本章核心概念：
  1. LLM 是"大脑"，但大脑本身不掌握你的私有数据，也不执行动作
  2. Agent = LLM + 工具 + 控制循环：大脑通过工具拿到数据、由循环推进任务
  3. 同一个问题：直接问 LLM 会得到不可靠答案，Agent 能查到真数据
  4. 这就是贯穿全书的问题：如何围绕 LLM 工程化地构建可靠系统

如何阅读本文件（零基础读者）：
  - 整个文件只用了 Python 标准库，不需要 pip 安装任何东西。
  - 建议按编号顺序阅读：配置区 -> Mini 客户端 -> 工具定义 -> 两种回答方式 -> main()。
  - "Mini 客户端"就是一个小函数 chat()，负责把对话发给 LLM 服务并拿回结果。
    它是本文件的"发动机"，后面的两种回答方式都靠它。
  - 第一次接触"工具调用（function calling）"的读者，重点看第 4 节的
    answer_by_agent_loop()：模型只"说"要调用哪个工具、带什么参数，
    真正执行工具的是我们自己写的 Python 代码（execute_tool 函数）。
"""

# json 是 Python 标准库：用于在"Python 对象"和"JSON 文本"之间互相转换。
# JSON 是一种通用的纯文本数据格式（形如 {"name": "张三", "age": 18}），
# LLM API 的请求和返回都使用 JSON，所以这里离不开它。
import json
# time 用于 sleep（暂停等待），本文件虽引入但暂时没用到，保留它无害。
import time
# urllib 是 Python 标准库自带的 HTTP 客户端（相当于内置的"网页请求工具"），
# 不用 pip 装任何东西就能向 LLM 服务发送网络请求。
# - urllib.request：发送请求、接收响应
# - urllib.error：请求出错时的异常类型（比如地址连不上）
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名（建议支持 tools 的模型）
# =======================================================================


# ========================= 2. Mini 客户端（支持工具） =========================
def chat(messages, tools=None, temperature=0.0, timeout=180):
    """向 LLM 服务发送一轮对话，返回模型生成的"一条消息"（dict）。

    参数说明：
      messages    对话历史，是一个列表，每项形如 {"role": ..., "content": ...}。
                  role 有四种取值（后面会反复见到）：
                  - system：给模型的"人设/规则"，模型会尽量遵守
                  - user：  用户（我们）说的话
                  - assistant：模型之前说过的话
                  - tool：  工具执行结果回传给模型时用的角色
      tools       可选。告诉模型"有哪些工具可用"，详见 TOOL_SCHEMAS。
      temperature 温度（0~1 左右）：控制模型回答的随机性。
                  越低越稳定可复现（适合做数据查询类任务），越高越发散有创意。
                  本书几乎所有例子都用 0.0，方便课堂演示结果一致。
      timeout     网络请求的超时秒数，超过就报错，避免程序卡死。
    """
    # API 地址：把末尾多余的 "/" 去掉再拼上统一路径 /chat/completions，
    # 这是所有 OpenAI 兼容服务约定的接口路径。
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # payload 是要发给 API 的请求体，会被转成 JSON 文本发出去。
    payload = {"model": LLM_MODEL_ID, "messages": messages, "temperature": temperature}
    if tools:
        # 如果传入了工具列表，就把它们包成 API 要求的格式一并告知模型。
        payload["tools"] = [{"type": "function", "function": t} for t in tools]
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    # 构造 HTTP 请求：请求体必须编码成 UTF-8 字节（encode），才能在网络上传送。
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    # urlopen 真正发出请求并等待响应（with 语句保证用完自动关闭连接）。
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        # 响应是 JSON 文本 -> decode 成字符串 -> 解析成 Python 的 dict。
        data = json.loads(resp.read().decode("utf-8"))
    # API 返回结构形如 {"choices": [{"message": {...}}]}，
    # 这里取出第一条候选消息（通常也是唯一一条）返回。
    return data["choices"][0]["message"]


# ========================= 3. 私有数据：LLM 的参数里没有的东西 =========================
# FAKE_DB 模拟一个只有我们自己知道的"数据库"。
# 模型训练时没见过这些数据，所以它只能靠工具来查询——这正是本案例的关键。
FAKE_DB = {
    "AgentLab": {"courses": 12, "students": 300, "semester": "2026 春季"},
}


# TOOL_SCHEMAS 用 JSON Schema 的格式描述工具：
# JSON Schema 是一种"说明书格式"，告诉模型工具叫什么、干什么用、需要哪些参数。
# 注意：这里只是"说明书"，模型读了它才知道可以调用什么工具；
# 工具真正做什么，由下面的 execute_tool 函数实现。
TOOL_SCHEMAS = [{
    "name": "query_platform_stats",
    "description": "查询指定课程平台的统计数据（课程数、学生数）",
    "parameters": {
        "type": "object",
        "properties": {"platform": {"type": "string",
                                    "description": "平台名称，如 AgentLab"}},
        "required": ["platform"],
    },
}]


def execute_tool(name, arguments):
    """真正执行工具的地方：模型只提出"想调用什么工具"，这里是落地实现。

    name      工具名（模型从 TOOL_SCHEMAS 里挑的）
    arguments 工具参数，是模型生成的 JSON 解析后的 dict
    """
    if name == "query_platform_stats":
        # 用 get 是为了防止模型没传 platform 参数时报错崩溃。
        stats = FAKE_DB.get(arguments.get("platform", ""))
        if stats is None:
            # 查不到时返回错误字符串（而不是抛异常崩溃），
            # 这样错误信息会回传给模型，它有机会自己纠正。
            return f"错误：没有平台 {arguments.get('platform')} 的数据"
        # dict 转成 JSON 字符串返回，这是回传给模型的标准做法。
        return json.dumps(stats, ensure_ascii=False)
    # 模型可能"幻觉"出不存在的工具名，此时也返回错误字符串让它纠正。
    return f"错误：工具 {name} 不存在"


# ========================= 4. 两种方式回答同一个问题 =========================
QUESTION = "AgentLab 平台上学期开了多少门课？"


def answer_by_direct_call():
    """方式 A：直接调用 LLM——它没有我们的私有数据。"""
    # 只发一条 user 消息（最简单的对话），不带任何工具。
    reply = chat([{"role": "user", "content": QUESTION}])
    # get("content", "")：如果模型没返回文字内容，就返回空串，避免报错。
    return reply.get("content", "")


def answer_by_agent_loop(max_steps=4):
    """方式 B：Agent 循环——模型调用工具查库，再基于数据回答。

    这就是本书的主角"Agent"的最小雏形：
    模型（大脑）+ 工具（手脚）+ 一个 for 循环（控制流）。
    max_steps 是"保险丝"：防止模型无限调用工具、程序永远跑不完。
    """
    # 对话从两条消息开始：system 定规矩（必须用工具，禁止瞎猜），user 提问题。
    messages = [
        {"role": "system", "content":
            "你是平台数据助手。回答数据问题前必须先调用查询工具，禁止凭记忆猜测。"},
        {"role": "user", "content": QUESTION},
    ]
    # 核心循环：每轮把整个对话历史发给模型，看它接下来想做什么。
    for step in range(1, max_steps + 1):
        reply = chat(messages, tools=TOOL_SCHEMAS)
        # tool_calls 是模型返回的"工具调用意图"列表：
        # 模型只说"我要调用某工具、参数是什么"，此时什么都还没执行；
        # 真正执行的是我们下面写的代码。
        if reply.get("tool_calls"):
            # 先把模型的这条"意图消息"原样记进对话历史
            # （API 要求：模型发起的 tool_calls 必须保留在历史里，后续 tool 结果才有归属）。
            messages.append({"role": "assistant", "content": reply.get("content") or "",
                             "tool_calls": reply["tool_calls"]})
            # 逐个执行模型请求的每一次工具调用。
            for call in reply["tool_calls"]:
                # arguments 是 JSON 字符串，要解析成 dict 才能取参数；
                # "or '{}'" 兜底：模型没写参数时按空参数处理。
                args = json.loads(call["function"].get("arguments") or "{}")
                print(f"[agent step {step}] 工具调用: {call['function']['name']}({args})")
                result = execute_tool(call["function"]["name"], args)
                print(f"[agent step {step}] 工具结果: {result}")
                # 把工具结果用 "tool" 角色的消息回传给模型，
                # tool_call_id 用来告诉 API 这条结果对应哪一次调用。
                messages.append({"role": "tool",
                                 "tool_call_id": call.get("id", f"call_{step}"),
                                 "content": result})
            # 执行完工具后不返回，回到循环开头：让模型看到结果再决定下一步。
        else:
            # 模型没有发起工具调用，说明它认为信息够了，给出了最终文字答案。
            # 这就是循环的"正常终止条件"。
            return reply.get("content", "")
    # 跑满 max_steps 轮模型还没给答案：强制终止，防止死循环。
    return "（步数用尽）"


# ========================= 5. 演示主流程 =========================
def main():
    # 主流程：先跑方式 A，再跑方式 B，方便对比同一个问题的两种答案。
    print("=" * 60)
    print("M0 案例：直接调用 LLM vs 运行 Agent")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    print(f"问题：{QUESTION}\n")

    print("--- 方式 A：直接调用 LLM ---")
    print(answer_by_direct_call().strip())

    print("\n--- 方式 B：Agent 循环（LLM + 工具） ---")
    print(answer_by_agent_loop().strip())

    print("\n要点：同一模型、同一问题，方式 B 用工具查到了私有数据库的真实值。"
          "本书要回答的就是：如何把方式 B 工程化，做到可靠、可测、可控。")


if __name__ == "__main__":
    main()
