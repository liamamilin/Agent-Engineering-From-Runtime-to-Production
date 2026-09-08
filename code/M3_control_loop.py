# -*- coding: utf-8 -*-
"""
M3 完整案例 — Control Loop：状态、控制循环与终止
=================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx（工具调用建议用较大模型）

运行：  python M3_control_loop.py

本案例演示本章核心概念：
  1. Agent = 状态 + 控制循环 + 终止条件，"LLM 只做决策，循环负责推进"
  2. 状态（AgentState）显式记录：步数、消息历史、是否完成、终止原因
  3. 三种终止方式：模型主动声明完成 / 达到步数上限 / 出现不可恢复错误
  4. 每一步都打印状态，让控制流可观察、可调试

如何阅读本文件（零基础读者）：
  - 全部代码只用 Python 标准库，不需要 pip 安装任何东西。
  - 本文件比 M0/M2 多了两样东西：一个显式的"状态对象"（AgentState，
    把步数、历史、是否完成等记录在一起）和更完整的"终止条件"设计
    （模型主动 finish / 步数用尽 / 错误纠正）。
  - 建议按编号顺序读：Mini 客户端 -> AgentState -> 虚拟文件系统工具
    -> 控制循环（最核心）-> main()。
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
    """向 LLM 服务发送对话，返回模型生成的整条消息（dict）。

    参数说明：
      messages    对话历史，每项形如 {"role": ..., "content": ...}。
                  role 四种取值：system（人设/规则）、user（用户输入）、
                  assistant（模型说过的话）、tool（工具结果回传时用）。
      temperature 温度：控制回答随机性，越低越稳定可复现，本书一律用 0.0。
      max_retries 网络失败时最多重试几次。
      timeout     单次网络请求的超时秒数，防止程序卡死。
    """
    # API 地址：去掉末尾多余的 "/"，再拼上 OpenAI 兼容服务统一约定的路径。
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {"model": LLM_MODEL_ID, "messages": messages, "temperature": temperature}
    if tools:
        # 把工具说明书列表包成 API 要求的格式，随请求一起告诉模型。
        payload["tools"] = [{"type": "function", "function": t} for t in tools]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }
    # ---- 重试机制（指数退避）----
    # 网络偶发失败很正常：失败后等 2 ** attempt 秒（1s、2s、4s……）再试，
    # 间隔指数增长，给服务恢复时间，也避免短时间反复冲击服务器。
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # usage 是本次调用的 token 用量（token 约等于半个词，
            # 是 API 计费和上下文长度的单位）。
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 返回整条 message（dict）而非纯文本：里面可能带 tool_calls 字段。
            return data["choices"][0]["message"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                # 2 ** attempt：2 的 attempt 次方，等待时间逐次翻倍。
                time.sleep(2 ** attempt)
    # 重试用尽仍失败：抛异常并带上最后一次错误原因，方便排查。
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. AgentState：显式的状态对象 =========================
class AgentState:
    """Agent 的全部可变状态都集中在这里，方便打印、调试、持久化。

    字段一览：
      task / max_steps   任务描述与步数上限（创建时确定，不再改变）
      messages           对话历史（system/user/assistant/tool 消息都存这里）
      step               已执行的循环轮数
      done               任务是否已完成（finish 工具会把它置 True）
      stop_reason        终止原因：model_finish（模型主动完成）或 max_steps（步数用尽）
      tool_calls_made    执行过的工具名列表，便于事后统计
    """

    def __init__(self, task, max_steps):
        self.task = task
        self.max_steps = max_steps
        self.messages = []          # 对话历史
        self.step = 0               # 当前步数
        self.done = False           # 是否完成
        self.stop_reason = None     # 终止原因
        self.tool_calls_made = []   # 执行过的工具调用记录

    def summary(self):
        return (f"step={self.step}/{self.max_steps} done={self.done} "
                f"stop_reason={self.stop_reason} "
                f"tool_calls={len(self.tool_calls_made)}")


# ========================= 4. 边界内工具：虚拟文件系统 =========================
# TOOL_SCHEMAS 用 JSON Schema 格式描述工具（给模型看的"说明书"）：
# JSON Schema 是描述数据结构的通用规范，这里声明每个工具的名字、
# 用途、参数和必填项。模型据此决定调不调、怎么调，看不到内部实现。
TOOL_SCHEMAS = [
    {"name": "list_files",
     "description": "列出虚拟文件系统中的所有文件名",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "read_file",
     "description": "读取指定文件的内容",
     "parameters": {"type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"]}},
    {"name": "write_file",
     "description": "把内容写入指定文件（覆盖）",
     "parameters": {"type": "object",
                    "properties": {"name": {"type": "string"},
                                   "content": {"type": "string"}},
                    "required": ["name", "content"]}},
    # finish 是特殊的"自终止工具"：模型确认任务完成后主动调用它，
    # 这是三种终止方式中最好的一种（模型自己宣布"我做完了"）。
    {"name": "finish",
     "description": "当任务目标已达成时调用，结束任务",
     "parameters": {"type": "object",
                    "properties": {"summary": {"type": "string",
                                               "description": "一句话总结做了什么"}},
                    "required": ["summary"]}},
]

# VIRTUAL_FS 是内存里的"假文件系统"：用 dict 模拟文件名 -> 文件内容。
# 真实工具环境里可以换成真正的磁盘文件，对模型来说接口完全一样。
VIRTUAL_FS = {
    "notes.txt": (
        "9月8日 会议记录：\n"
        "1. 周五前提交周报（张伟）\n"
        "2. 下单新的服务器（李娜）\n"
        "3. 更新课程大纲（王强）\n"
    ),
}


def execute_tool(name, arguments, state):
    """真正执行工具的地方。比前两章多传了 state 参数：
    因为工具执行可能改变 Agent 状态（比如 finish 工具要把 state.done 置 True）。
    """
    if name == "list_files":
        # 把所有文件名转成 JSON 字符串回传给模型。
        return json.dumps(list(VIRTUAL_FS), ensure_ascii=False)
    if name == "read_file":
        content = VIRTUAL_FS.get(arguments.get("name", ""))
        return content if content is not None else f"错误：文件不存在"
    if name == "write_file":
        # 直接改 dict 就相当于"写文件"——这就是虚拟文件系统的全部实现。
        VIRTUAL_FS[arguments["name"]] = arguments["content"]
        return f"已写入 {arguments['name']}（{len(arguments['content'])} 字符）"
    if name == "finish":
        # 模型主动宣布完成：修改共享状态 state，控制循环下一轮判断时就会停止。
        # 这是"模型主动声明完成"这种终止条件的实现方式。
        state.done = True
        state.stop_reason = "model_finish"
        return f"任务结束：{arguments.get('summary', '')}"
    return f"错误：工具 {name!r} 不存在"


# ========================= 5. 控制循环 =========================
def run_agent(task, max_steps=8):
    """本文件的核心：把"状态 + 循环 + 终止条件"组装成一个完整 Agent。

    循环条件 while not state.done and state.step < state.max_steps
    蕴含了两种终止方式：模型主动 finish（done=True），或步数用尽。
    """
    # 第一步：创建状态对象，之后每一步的进展都记录在这里。
    state = AgentState(task, max_steps)
    state.messages = [
        {"role": "system", "content":
            "你是文件整理助手。用工具完成任务；"
            "任务目标达成后必须调用 finish 工具结束。"},
        {"role": "user", "content": task},
    ]
    while not state.done and state.step < state.max_steps:
        state.step += 1
        # 每一步都打印状态摘要：让循环的推进过程"看得见"，方便课堂演示和调试。
        print(f"\n--- {state.summary()} ---")
        reply = chat(state.messages, tools=TOOL_SCHEMAS)

        if reply.get("tool_calls"):
            # 模型发起了工具调用：先把"意图消息"记入历史（API 规定必须保留，
            # 后面回传的 tool 结果才能通过 tool_call_id 对上号）。
            state.messages.append({"role": "assistant",
                                   "content": reply.get("content") or "",
                                   "tool_calls": reply["tool_calls"]})
            for call in reply["tool_calls"]:
                name = call["function"]["name"]
                # arguments 是 JSON 字符串，解析成 dict 才能取参数；
                # "or '{}'" 兜底：模型没写参数时按空参数处理。
                args = json.loads(call["function"].get("arguments") or "{}")
                print(f"[动作] {name}({args})")
                state.tool_calls_made.append(name)
                # 真正执行工具的是这里——模型只负责"提议"。
                result = execute_tool(name, args, state)
                print(f"[结果] {result}")
                # 工具结果用 "tool" 角色消息追加进历史，供模型下一轮阅读。
                state.messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", f"call_{state.step}"),
                    "content": result,
                })
        else:
            # 模型没调工具也没 finish：把回复喂回去并提醒它必须 finish
            # 这种情况说明模型"跑神"了，不强行终止，而是给一次纠正机会。
            state.messages.append({"role": "assistant",
                                   "content": reply.get("content") or ""})
            state.messages.append({"role": "user",
                                   "content": "任务还没结束，请继续用工具或调用 finish。"})

    # 走到这里循环已退出。如果 done 不是被 finish 置位的，
    # 说明是步数用尽被 while 条件终止的——把终止原因补记为 max_steps。
    if not state.done:
        state.stop_reason = "max_steps"
        state.done = True
    print(f"\n=== 终止：{state.stop_reason} | {state.summary()} ===")
    # 返回整个状态对象：调用方可以据此分析这次运行的全过程。
    return state


# ========================= 6. 演示主流程 =========================
def main():
    print("=" * 60)
    print("M3 案例：控制循环与终止")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    # 任务示例：读文件 -> 整理 -> 写文件，模型需要多步工具调用才能完成。
    task = "读取 notes.txt，把里面的待办事项整理成'事项 - 责任人'列表，写入 todo.txt"
    state = run_agent(task)

    # 最后展示虚拟文件系统的全部内容，验证 todo.txt 是否真的写成功了。
    print("\n最终文件系统：")
    for name, content in VIRTUAL_FS.items():
        print(f"--- {name} ---\n{content}")


if __name__ == "__main__":
    main()
