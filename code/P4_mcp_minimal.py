# -*- coding: utf-8 -*-
"""
P4 实战案例 — MCP 实战：纯标准库实现最小 MCP Server + Agent
============================================================

运行前修改配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   建议用支持工具调用的模型，如 qwen3.8:27b-mlx

运行（单文件双模式）：

    python P4_mcp_minimal.py server          # 终端 1：手工调试 MCP server
    python P4_mcp_minimal.py agent "问题"    # 完整演示：agent 子进程启动 server

本案例演示：
  1. MCP 的本质：JSON-RPC 2.0 over stdio 的协议层，
     initialize 握手 -> tools/list 工具发现 -> tools/call 工具调用
  2. server 端零第三方依赖实现 MCP 最小可用子集
  3. agent 端用 subprocess 启动 server，把 MCP 工具动态转成
     LLM function calling 的工具表——工具在协议层发现，而非硬编码
  4. function calling 是"模型怎么选工具"，MCP 是"工具从哪来、怎么接"——
      两者是互补的两层，不是竞争方案

如何阅读本文件（零基础读者建议顺序）：
   - 先看第 2 节 safe_calc：理解"为什么不用 eval"（eval 会执行任意代码，不安全）；
   - 再看第 3 节 run_server：理解 JSON-RPC 2.0 协议长什么样（请求带 id，
     响应回同一个 id；通知没有 id，所以不需要响应）；
   - 最后看第 4 节 McpClient / run_agent：理解 agent 如何用 subprocess 把
     server 当子进程启动，并让两个进程通过 stdio 通话。
   - 术语提示：stdio 指"标准输入/标准输出"——对进程来说，stdin/stdout
     本身就是一条通信管道，这里约定"一行一条 JSON 消息"。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from ast import BinOp, Constant, UnaryOp, USub, UAdd, Add, Sub, Mult, Div

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 建议支持 tools 的模型
# =======================================================================

PROTOCOL_VERSION = "2025-06-18"   # MCP 协议版本号，握手时双方要协商一致
SERVER_INFO = {"name": "course-mcp-server", "version": "1.0.0"}   # 握手时告诉客户端"我是谁"


# ========================= 2. 三个内置工具 =========================
def safe_calc(expression):
    """只允许 + - * / 和数字、括号的表达式求值（禁止任意代码执行）。

    为什么不用 eval：eval 会把字符串当代码执行，模型给一句
    "__import__('os').system(...)" 就能删文件，等于开门放进任意代码。
    正确做法是先把表达式解析成 AST（语法树），再用"白名单"逐节点检查：
    只有明确允许的节点类型才放行，其余一律拒绝。
    """
    import ast
    # 白名单：只放行这四种四则运算节点，幂、比较、调用函数等统统不在名单里
    ALLOW_OPS = {Add, Sub, Mult, Div}

    def ev(node):
        # 递归遍历语法树的每个节点，按节点类型决定"算"还是"拒绝"
        if isinstance(node, Constant):
            # 常量节点（数字）：只允许数字，字符串/布尔等一律拒绝
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不允许的常量: {node.value!r}")
        if isinstance(node, UnaryOp) and isinstance(node.op, (USub, UAdd)):
            # 一元正负号，如 "-3" 或 "+5"
            v = ev(node.operand)
            return -v if isinstance(node.op, USub) else +v
        if isinstance(node, BinOp) and type(node.op) in ALLOW_OPS:
            # 二元运算（加减乘除）：先递归算出左右两边，再做运算
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, Add):
                return left + right
            if isinstance(node.op, Sub):
                return left - right
            if isinstance(node.op, Mult):
                return left * right
            if right == 0:
                raise ZeroDivisionError("除数为 0")
            return left / right
        # 走到这里说明遇到了白名单之外的节点（如函数调用、变量名），直接拒绝
        raise ValueError(f"不允许的语法: {type(node).__name__}")

    # mode="eval" 表示把字符串解析成"一个表达式"的语法树，body 是树的根节点
    return ev(ast.parse(expression, mode="eval").body)


# 每个工具由三部分组成：description（给模型看的功能说明）、
# inputSchema（告诉模型参数长什么样，就是个 JSON Schema）、run（真正干活的函数）
TOOLS_IMPL = {
    "calculator": {
        "description": "计算算术表达式，只支持 + - * / 和括号，如 (128+72)*3",
        # inputSchema 描述"调用这个工具需要传什么参数"，后面会原样转成
        # function calling 的 parameters，两者格式天然同构
        "inputSchema": {"type": "object",
                        "properties": {"expression": {"type": "string"}},
                        "required": ["expression"]},
        # lambda 是匿名函数：收到参数字典后执行安全计算，结果转成字符串返回
        "run": lambda args: str(safe_calc(args["expression"])),
    },
    "current_time": {
        "description": "获取服务器当前的日期和时间",
        # 不需要任何参数，所以 properties 为空
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "run": lambda args: time.strftime("%Y-%m-%d %H:%M:%S %A"),
    },
    "note_add": {
        "description": "往笔记簿里追加一条笔记（服务进程内存，进程退出即清空）",
        "inputSchema": {"type": "object",
                        "properties": {"topic": {"type": "string"},
                                       "content": {"type": "string"}},
                        "required": ["topic", "content"]},
        "run": None,   # 有状态工具，在 server 循环里特殊处理
    },
    "note_list": {
        "description": "列出笔记簿里的全部笔记",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "run": None,   # 有状态工具，在 server 循环里特殊处理
    },
}
# 有状态工具：NOTES 这个列表活在 server 进程的内存里，
# 所以 note_add 之后再 note_list 能看到之前的记录；但 server 进程一退出就全没了
NOTES = []   # server 进程内存中的笔记簿


def execute_tool(name, arguments):
    # 工具的统一入口：查名字 -> 分发执行 -> 统一兜底异常
    tool = TOOLS_IMPL.get(name)
    if tool is None:
        # 第二个返回值 True 表示"这是次失败的调用"，会写进响应的 isError 字段
        return f"错误：工具 {name!r} 不存在", True
    try:
        if name == "note_add":
            # 有状态工具不走 tool["run"]，直接操作进程内存里的 NOTES 列表
            NOTES.append(f"[{arguments.get('topic', '未分类')}] "
                         f"{arguments.get('content', '')}")
            return f"已记录，笔记簿现有 {len(NOTES)} 条", False
        if name == "note_list":
            if not NOTES:
                return "（笔记簿为空）", False
            return "\n".join(f"{i}. {n}" for i, n in enumerate(NOTES, 1)), False
        # 无状态工具统一走 run 函数
        return tool["run"](arguments), False
    except Exception as e:
        # 关键设计：工具出错不抛异常让 server 崩溃，而是把错误信息当作
        # 工具结果返回给模型，让模型自己看到错误并想办法调整
        return f"工具执行失败：{e}", True


# ========================= 3. server 模式：JSON-RPC 2.0 over stdio =========================
def run_server():
    """从 stdin 读一行 JSON-RPC 请求，向 stdout 写一行 JSON-RPC 响应。

    术语提示：stdio 就是"标准输入/标准输出"。子进程的 stdin/stdout
    本身就是一条现成的通信管道，MCP 约定：一行一条 JSON 消息。
    """
    # for line in sys.stdin：逐行读取标准输入，没有消息就阻塞等待
    for line in sys.stdin:
        line = line.strip()
        if not line:
            # 空行不是消息，跳过
            continue
        try:
            # 把这一行文本解析成 JSON 对象（一条 JSON-RPC 请求）
            req = json.loads(line)
        except json.JSONDecodeError:
            # 连 JSON 都解析不了：按协议回一个固定的解析错误（-32700）
            _reply(None, error={"code": -32700, "message": "Parse error"})
            continue

        # method 决定"要做什么"，params 是"做这件事的参数"
        method = req.get("method", "")
        params = req.get("params") or {}
        # 请求带 id，响应要回同一个 id；通知（notification）没有 id，不需要响应
        request_id = req.get("id")          # 通知（notification）没有 id

        if method == "initialize":
            # 握手第一步：客户端问"你支持什么协议版本、有什么能力"，
            # server 报上自己的版本、能力和名字
            _reply(request_id, result={
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            })
        elif method == "notifications/initialized":
            # 握手第二步：客户端确认"我知道了"。这是通知（无 id），不回话
            pass                            # 通知：无需响应
        elif method == "tools/list":
            # 工具发现：把工具表里的 name/description/inputSchema 列给客户端
            # 注意 run 函数不外传——客户端只需要"怎么调用"，不需要实现
            tools = [{"name": n, "description": t["description"],
                      "inputSchema": t["inputSchema"]}
                     for n, t in TOOLS_IMPL.items()]
            _reply(request_id, result={"tools": tools})
        elif method == "tools/call":
            # 工具调用：按客户端给的名字和参数真正执行工具
            text, is_error = execute_tool(params.get("name", ""),
                                          params.get("arguments") or {})
            _reply(request_id, result={
                "content": [{"type": "text", "text": text}],
                "isError": is_error,
            })
        elif request_id is not None:
            # 有 id 的未知请求：必须回错误，否则客户端会一直等（-32601 方法不存在）
            _reply(request_id, error={"code": -32601,
                                      "message": f"Method not found: {method}"})
        else:
            pass                            # 未知通知：忽略


def _reply(request_id, result=None, error=None):
    # 组装一条 JSON-RPC 响应：id 必须与请求一致，result（成功）和 error（失败）二选一
    resp = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        resp["error"] = error
    else:
        resp["result"] = result
    # 往 stdout 写一行 JSON 并立即冲刷缓冲区，确保客户端马上收到
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


# ========================= 4. agent 模式：子进程 + 动态工具发现 =========================
class McpClient:
    """启动 MCP server 子进程，按 JSON-RPC 协议与它对话。"""

    def __init__(self):
        # subprocess.Popen 启动一个子进程：还是运行本文件，但参数是 "server"
        # 三个管道的含义——我们把数据写进它的 stdin，从它的 stdout 读回响应，
        # stderr 丢弃（防止 server 的报错文本混进 JSON 消息流）
        self.proc = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
        # 自增计数器：每发一个请求编号 +1，用来配对"哪个响应对应哪个请求"
        self.request_id = 0

    def _send(self, obj):
        # 把消息序列化成一行 JSON 写进子进程的 stdin，flush 确保立刻发出
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        # 发一个"带 id 的请求"并阻塞等待响应（通知则用下面的 notify）
        self.request_id += 1
        self._send({"jsonrpc": "2.0", "id": self.request_id,
                    "method": method, "params": params or {}})
        while True:
            # 从子进程 stdout 逐行读响应
            line = self.proc.stdout.readline()
            if not line:
                # readline 返回空说明子进程已关闭、管道断了
                raise RuntimeError("MCP server 无响应（进程退出？）")
            resp = json.loads(line)
            # 响应可能乱序到达：只认 id 与本次请求相同的那条
            if resp.get("id") == self.request_id:
                if "error" in resp:
                    raise RuntimeError(f"MCP 错误: {resp['error']}")
                return resp["result"]

    def notify(self, method, params=None):
        # 通知 = 不带 id 的消息，发出去就行，不需要等响应
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def handshake(self):
        # MCP 三步握手中的前两步：发 initialize 请求，再发 initialized 通知
        info = self.request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {}, "clientInfo": {"name": "course-agent", "v": "1.0"}})
        self.notify("notifications/initialized")
        print(f"[mcp] 握手成功: {info['serverInfo']['name']} "
              f"(protocol {info['protocolVersion']})")
        return info

    def list_tools(self):
        # 工具发现：问 server 有哪些工具可用（而不是在代码里硬编码工具表）
        return self.request("tools/list")["tools"]

    def call_tool(self, name, arguments):
        # 工具调用：把结果里的文本片段拼起来，同时带上"是否出错"标记
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        texts = [c.get("text", "") for c in result.get("content", [])
                 if c.get("type") == "text"]
        return "\n".join(texts), result.get("isError", False)

    def close(self):
        # 收尾：关掉 stdin（子进程读到 EOF 会自然退出），最多等 5 秒；
        # 等不到就强杀，保证不留下僵尸进程
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def chat(messages, tools=None, temperature=0.0, max_retries=3, timeout=180):
    # 手写一个最小的 OpenAI 兼容客户端：拼请求体 -> POST -> 解析响应
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {"model": LLM_MODEL_ID, "messages": messages, "temperature": temperature}
    # 如果有工具表，按 OpenAI function calling 的格式包一层 {"type": "function", ...}
    if tools:
        payload["tools"] = [{"type": "function", "function": t} for t in tools]
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # 网络请求可能偶发失败，重试若干次；指数退避（等待时间逐次翻倍）
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 返回模型这条回复消息（可能含 content，也可能含 tool_calls）
            return data["choices"][0]["message"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


def to_llm_tools(mcp_tools):
    """MCP inputSchema 直接就是 JSON Schema —— 与 function calling 同构。

    这正是本案例的核心洞察：MCP 在协议层用 inputSchema 描述工具参数，
    function calling 在模型层用 parameters 描述，两者结构完全一样，
    所以转换只是改个字段名，不需要写任何适配逻辑。
    """
    # inputSchema 原样搬进 parameters——这就是"同构"的含义
    return [{"name": t["name"], "description": t["description"],
             "parameters": t["inputSchema"]} for t in mcp_tools]


def run_agent(task, max_steps=8):
    # agent 主循环：发现工具 -> 反复"问模型 -> 执行工具 -> 回喂结果" -> 收尾
    mcp = McpClient()
    try:
        # 第 1 步：握手，确认协议版本双方一致
        mcp.handshake()
        # 第 2 步：工具发现——工具表是运行时从 server 拿的，不是写死的
        mcp_tools = mcp.list_tools()
        print(f"[mcp] 发现 {len(mcp_tools)} 个工具: "
              f"{[t['name'] for t in mcp_tools]}")
        # 第 3 步：把 MCP 工具转成 function calling 格式喂给模型
        llm_tools = to_llm_tools(mcp_tools)

        # 对话历史：system 定规矩，user 放任务
        messages = [
            {"role": "system", "content":
                "你是助手。用工具完成任务；完成后用一句话总结，不再调用工具。"},
            {"role": "user", "content": task},
        ]
        # 最多走 max_steps 步，防止模型无限循环调用工具
        for step in range(1, max_steps + 1):
            # 问模型：给它全部历史 + 工具表，让它决定"回话"还是"调工具"
            reply = chat(messages, tools=llm_tools)
            calls = reply.get("tool_calls") or []
            # 先把模型这条回复原样记进历史（含 tool_calls），保持上下文完整
            messages.append({"role": "assistant", "content": reply.get("content") or "",
                             **({"tool_calls": calls} if calls else {})})
            if not calls:
                # 模型没有调用任何工具 = 它认为任务完成，输出最终回答
                print(f"\n[final] {reply.get('content', '').strip()}")
                return
            for call in calls:
                # 取出模型要调的工具名和参数（arguments 是 JSON 字符串，要解析）
                name = call["function"]["name"]
                arguments = json.loads(call["function"].get("arguments") or "{}")
                print(f"[step {step}] MCP tools/call: {name}({arguments})")
                # 真正通过 MCP 协议调用 server 上的工具
                text, is_error = mcp.call_tool(name, arguments)
                print(f"[step {step}] 结果: {text}")
                # 关键闭环：把工具结果作为 tool 消息回喂给模型，
                # 模型看到结果后才能决定下一步
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                                 "content": text})
        print("[final] 达到步数上限")
    finally:
        # 无论正常结束还是中途出错，都要关闭 server 子进程
        mcp.close()
        print("[mcp] server 子进程已关闭")


# ========================= 5. 入口：双模式 =========================
def main():
    # 双模式入口：同一个文件，带 "server" 参数就是 MCP server，
    # 带 "agent" 参数就是 agent 客户端（agent 会再启动一个 server 子进程）
    if len(sys.argv) >= 2 and sys.argv[1] == "server":
        run_server()
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "agent":
        # 命令行没给任务就用默认演示任务
        task = " ".join(sys.argv[2:]) or (
            "计算 (250+150)*3 的结果，把'预算核算是 1200'作为一条笔记记录下来，"
            "然后告诉我现在几点、笔记簿里有几条")
        run_agent(task)
        return
    # 不带参数：打印文件顶部的使用说明
    print(__doc__)


if __name__ == "__main__":
    main()
