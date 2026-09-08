# -*- coding: utf-8 -*-
"""
M2 完整案例 — Tools：function calling 工具循环
================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx（工具调用建议用较大模型）

运行：  python M2_tools.py

本案例演示本章核心概念：
  1. 工具 = Agent 可调用的动作接口，模型只产生"调用意图"，真正执行在边界内
  2. 工具 schema（JSON Schema）告诉模型有哪些工具、参数是什么
  3. 工具结果以 tool 角色消息回传，模型基于结果继续推理
  4. 模型幻觉出不存在的工具时，必须显式报错而不是硬编码兜底

如何阅读本文件（零基础读者）：
  - 全部代码只用 Python 标准库，不需要 pip 安装任何东西。
  - 核心概念"function calling（工具调用）"一句话概括：
    模型只负责"说"要调用哪个工具、带什么参数（返回 tool_calls），
    真正动手执行的是我们写的 Python 代码（execute_tool），
    执行结果再以 tool 角色消息回传给模型继续推理。
  - 建议按编号顺序读：Mini 客户端 -> 工具定义与实现 -> 工具调用循环 -> main()。
"""

# json：标准库，JSON 是 LLM API 的通用数据格式，负责对象与文本的互相转换。
import json
# time：标准库，sleep() 让程序暂停几秒，用在网络失败后的重试等待。
import time
# urllib 是 Python 标准库自带的 HTTP 客户端，不用 pip 装任何东西
# 就能向 LLM 服务发网络请求；urllib.error 提供网络相关异常类型。
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名（建议支持 tools 的模型）
# =======================================================================


# ========================= 2. Mini 客户端（支持工具） =========================
def chat(messages, tools=None, temperature=0.0, max_retries=3, timeout=120):
    """调用 OpenAI 兼容接口；tools 非空时模型可返回工具调用意图。

    参数说明：
      messages    对话历史，每项形如 {"role": ..., "content": ...}。
                  role 有四种：system（人设/规则）、user（用户输入）、
                  assistant（模型说过的话）、tool（工具结果回传时用）。
      temperature 温度：控制回答随机性，越低越稳定。工具调用要结果可复现，
                  所以本书一律用 0.0。
      max_retries 网络失败时最多重试几次。
      timeout     单次网络请求的超时秒数，防止程序卡死。
    """
    # API 地址：去掉末尾多余的 "/"，再拼上 OpenAI 兼容服务统一约定的路径。
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体（payload）：稍后会被转成 JSON 文本发给服务端。
    payload = {"model": LLM_MODEL_ID, "messages": messages, "temperature": temperature}
    if tools:
        # 把工具说明书列表包成 API 要求的格式，随请求一起告诉模型。
        payload["tools"] = [{"type": "function", "function": t} for t in tools]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    # ---- 重试机制（指数退避）----
    # 网络偶发失败很正常：失败后等 2 ** attempt 秒（1s、2s、4s……）再试。
    # 间隔指数增长，既给服务恢复时间，也不至于反复冲击服务器。
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # usage 是本次调用的 token 用量（token 约等于半个词，
            # 是 API 计费和上下文长度的单位），打印出来便于观察开销。
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 注意返回的是整条 message（dict），不只是文本——
            # 因为 message 里可能带 tool_calls 字段，调用方需要判断。
            return data["choices"][0]["message"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                # 2 ** attempt：2 的 attempt 次方，实现指数增长的等待间隔。
                delay = 2 ** attempt
                print(f"[retry] 第 {attempt + 1} 次失败（{e}），{delay}s 后重试")
                time.sleep(delay)
    # 重试用尽仍失败：抛异常，把最后一次错误原因带上，方便排查。
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 工具定义与实现 =========================
# TOOL_SCHEMAS 是给模型看的"工具说明书"，用 JSON Schema 格式书写。
# JSON Schema 是一种描述数据结构的通用规范：这里告诉模型
# 每个工具叫什么名字、干什么用、需要哪些参数、哪些参数必填。
# 模型只根据这份说明书决定"调不调、怎么调"，并不知道工具内部如何实现。
TOOL_SCHEMAS = [
    {
        "name": "calculate",
        "description": "计算一个四则运算表达式，仅支持 + - * / 和括号",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "如 (12 + 8) * 3"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_city_weather",
        "description": "查询城市当前天气（演示用，只内置了少数城市）",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市中文名，如 武汉"}
            },
            "required": ["city"],
        },
    },
]

# 工具的真实实现在边界内（模型永远摸不到这个 dict）
FAKE_WEATHER = {
    "武汉": {"condition": "晴", "temp_c": 33},
    "北京": {"condition": "多云", "temp_c": 27},
    "上海": {"condition": "小雨", "temp_c": 29},
}


def execute_tool(name, arguments):
    """在 Agent 侧执行工具，返回字符串结果。这是唯一真正"做事"的地方。

    name      模型想调用的工具名（从 TOOL_SCHEMAS 里选的）
    arguments 模型给出的参数（JSON 字符串解析后的 dict）
    """
    if name == "calculate":
        expression = arguments.get("expression", "")
        # 安全防护：先检查表达式是否只含数字和四则运算符，
        # 防止模型（或恶意输入）传进奇怪的内容。
        allowed = set("0123456789+-*/(). ")
        # set(expression) <= allowed 是集合子集判断：表达式里的每个字符都在允许范围内。
        if not set(expression) <= allowed:
            return f"错误：表达式包含非法字符：{expression!r}"
        try:
            # eval 把字符串当 Python 表达式求值——方便但危险，
            # 所以上面必须先做字符白名单检查，并禁用内建函数（第二个参数）。
            return str(eval(expression, {"__builtins__": {}}, {}))
        except Exception as e:
            # 除零、语法错误等都会走到这里；返回错误字符串而不是崩溃，
            # 这样模型能看到错误并有机会自己修正。
            return f"错误：无法计算 {expression!r}（{e}）"
    if name == "get_city_weather":
        city = arguments.get("city", "")
        weather = FAKE_WEATHER.get(city)
        if weather is None:
            # 查不到时把"可用城市"一并告诉模型，它下一轮就知道怎么改参数。
            return f"错误：没有 {city} 的天气数据，可用城市：{', '.join(FAKE_WEATHER)}"
        # dict 转成 JSON 字符串回传给模型（ensure_ascii=False 让中文原样显示）。
        return json.dumps(weather, ensure_ascii=False)
    # 幻觉工具：显式报错，让模型自己纠正
    return f"错误：工具 {name!r} 不存在，可用工具：calculate, get_city_weather"


# ========================= 4. 工具调用循环 =========================
def run_tool_loop(user_task, max_steps=6):
    """完整的工具调用循环：模型提议 -> 边界内执行 -> 结果回传 -> 直到给出答案。

    max_steps 是保险丝：无论模型多"话痨"，最多执行这么几轮就强制停止，
    避免程序无限运行下去。
    """
    # 对话从 system（定规矩）+ user（任务）两条消息开始，之后逐步追加历史。
    messages = [
        {"role": "system", "content":
            "你是助手。需要计算或查天气时调用工具；"
            "拿到工具结果后用一句话给出最终答案。"},
        {"role": "user", "content": user_task},
    ]
    for step in range(1, max_steps + 1):
        # 每轮都把"完整对话历史"发给模型——模型没有记忆，
        # 它能看到的一切都在 messages 里，所以我们每轮都要带上全部历史。
        reply = chat(messages, tools=TOOL_SCHEMAS)
        # tool_calls 非空 = 模型说"我想调用这些工具"——注意此时什么都没执行，
        # 只是意图；真正执行在下面的 execute_tool。
        if reply.get("tool_calls"):
            # 先把模型的"意图消息"原样记入历史。
            # API 规定：模型发起的 tool_calls 必须保留，后面回传的 tool
            # 结果才能通过 tool_call_id 对上号。
            messages.append({"role": "assistant",
                             "content": reply.get("content") or "",
                             "tool_calls": reply["tool_calls"]})
            # 模型可能一次请求多个工具调用，逐个执行。
            for call in reply["tool_calls"]:
                name = call["function"]["name"]
                # arguments 是 JSON 字符串，解析成 dict 才能取参数；
                # "or '{}'" 兜底：模型没写参数时按空参数处理。
                args = json.loads(call["function"].get("arguments") or "{}")
                print(f"[step {step}] 工具调用: {name}({args})")
                result = execute_tool(name, args)
                print(f"[step {step}] 工具结果: {result}")
                # 把工具结果用 "tool" 角色消息追加进历史，
                # tool_call_id 标明这条结果对应哪一次调用。
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", f"call_{step}"),
                    "content": result,
                })
            # 执行完本轮工具后回到循环开头，让模型看到结果再决定下一步。
        else:
            # 没有 tool_calls = 模型认为信息够了，直接给出最终文字答案。
            # 这是循环的正常终止条件。
            print(f"[step {step}] 模型给出最终答案")
            return reply["content"]
    # 跑满步数上限还没答案：强制终止，返回提示而不是死循环。
    return "（达到最大步数上限，循环终止）"


# ========================= 5. 演示主流程 =========================
def main():
    print("=" * 60)
    print("M2 案例：工具调用循环")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    # 两个演示任务：一个查天气（需要两次工具调用对比），一个做计算。
    tasks = [
        "武汉现在多少度？比北京高还是低？",
        "帮我算一下 (128 + 72) * 3 等于多少？",
    ]
    for task in tasks:
        print(f"\n>>> 任务：{task}")
        answer = run_tool_loop(task)
        print(f"<<< 答案：{answer}\n")


if __name__ == "__main__":
    main()
