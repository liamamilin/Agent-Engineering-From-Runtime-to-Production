# -*- coding: utf-8 -*-
"""
P5 实战案例 — 终端 Coding Agent：在沙箱里修 Bug
================================================

运行前修改配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   建议用支持工具调用的模型，如 qwen3.8:27b-mlx

运行：  python P5_coding_agent.py

本案例演示 Coding Agent 的最小安全骨架：
  1. 沙箱：agent 只能读写 sandbox_p5/ 目录内的文件，路径越界直接拒绝
  2. 工具：list_dir / read_file / write_file / run_python / finish
     其中 run_python 用 subprocess 执行，带超时与输出截断
  3. 闭环：运行测试 -> 观察失败 -> 修改代码 -> 再运行 -> 通过 -> finish
  4. 护栏与能力分层：文件系统是真实接触点，所以必须配边界检查；
      这是 M10 guardrails 在 coding 场景的落地

如何阅读本文件（零基础读者建议顺序）：
   - 先看 SANDBOX 与 DEMO_FILES：理解"沙箱"——agent 只能碰这个目录里的
     文件，越界一律拒绝，这是让 agent 安全操作文件系统的大前提；
   - 再看第 2 节工具实现：注意每个工具入口都先过 resolve_in_sandbox 检查；
   - 最后看第 4 节控制循环：体会"红-绿循环"——运行测试看到红（失败），
     改代码，再运行看到绿（通过），这个节奏由模型自己驱动。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 建议支持 tools 的模型
RUN_TIMEOUT = 10          # run_python 超时（秒）：防止模型写的代码死循环卡住整个 agent
OUTPUT_LIMIT = 1500       # 子进程输出截断长度：防止海量输出撑爆上下文窗口
# =======================================================================

# 沙箱根目录：agent 的全部文件操作都被限制在这个目录里。
# 用脚本自身所在目录拼出来，保证换个机器跑也能定位到
SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox_p5")

# 演示项目：shop.py 里 final_price 有个 bug（原价乘折扣百分比，应为乘 (1-百分比)），
# test_shop.py 是验收测试，初始必然失败——这就是"红"的起点
DEMO_FILES = {
    "shop.py": (
        'def final_price(price, discount_pct):\n'
        '    """折后价：price 原价，discount_pct 折扣百分比（如 25 表示 75 折）"""\n'
        '    return price * discount_pct\n'
    ),
    "test_shop.py": (
        'from shop import final_price\n\n'
        'assert final_price(200, 25) == 150, f"got {final_price(200, 25)}"\n'
        'assert final_price(100, 10) == 90\n'
        'assert final_price(59.9, 50) == 29.95\n'
        'print("all tests passed")\n'
    ),
}


def ensure_sandbox():
    """首次运行生成演示项目：一个带 bug 的模块 + 一个测试文件。"""
    # exist_ok=True：目录已存在就不报错，保证重复运行也安全
    os.makedirs(SANDBOX, exist_ok=True)
    for name, content in DEMO_FILES.items():
        path = os.path.join(SANDBOX, name)
        # 只在文件不存在时写入，避免覆盖 agent 上一次修改的成果
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


# ========================= 2. 沙箱工具（每一步都有边界检查） =========================
def resolve_in_sandbox(name):
    """把相对路径解析到沙箱内；越界路径直接拒绝。

    安全要点：先用 os.path.realpath 把路径"归一化"——消解掉 ../ 和符号链接，
    得到真实的绝对路径，再检查它是否以沙箱根目录为前缀。
    如果不归一化，模型传一个 "../xx.py" 就能骗过简单的字符串检查，
    读写到沙箱外的任何文件（路径穿越攻击）。
    """
    # 沙箱根目录的真实绝对路径（作为比对基准）
    sandbox_root = os.path.realpath(SANDBOX)
    # 把"沙箱内相对路径"拼起来后同样归一化，../ 会被就地消解
    target = os.path.realpath(os.path.join(sandbox_root, name))
    # 归一化后必须仍落在沙箱根目录之内，否则视为越界，拒绝执行
    if not target.startswith(sandbox_root + os.sep):
        raise PermissionError(f"路径越界：{name!r} 不在沙箱内")
    return target


def tool_list_dir(args):
    # 列出沙箱内容：目录名后补一个 / 方便模型区分文件和目录
    entries = []
    for name in sorted(os.listdir(SANDBOX)):
        path = os.path.join(SANDBOX, name)
        entries.append(f"{name}{'/' if os.path.isdir(path) else ''}")
    return "沙箱文件：\n" + "\n".join(entries)


def tool_read_file(args):
    # 每个工具入口先做沙箱边界检查，再读文件
    path = resolve_in_sandbox(args["name"])
    if not os.path.isfile(path):
        return f"错误：文件 {args['name']} 不存在"
    with open(path, encoding="utf-8") as f:
        return f.read()


def tool_write_file(args):
    # 写文件同样先过边界检查；注意是覆盖写
    path = resolve_in_sandbox(args["name"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(args["content"])
    return f"已写入 {args['name']}（{len(args['content'])} 字符）"


def tool_run_python(args):
    # 运行沙箱内的 Python 文件：这是 agent "动手验证"的手段
    path = resolve_in_sandbox(args["name"])
    if not path.endswith(".py"):
        return "错误：只能运行 .py 文件"
    try:
        # subprocess.run 阻塞等子进程跑完：
        #   cwd=SANDBOX     —— 在沙箱目录里运行，import 才能找到 shop.py
        #   capture_output  —— 收集 stdout/stderr 作为观察结果回喂模型
        #   timeout         —— 超时强制终止，防死循环
        proc = subprocess.run(
            [sys.executable, path], cwd=SANDBOX, capture_output=True,
            text=True, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        # 超时不让程序崩溃，而是作为一条观察结果告诉模型
        return f"错误：运行超过 {RUN_TIMEOUT} 秒被终止"
    # 合并 stdout 与 stderr（报错信息往往在 stderr），截断防止撑爆上下文
    output = (proc.stdout + proc.stderr).strip()[:OUTPUT_LIMIT]
    # 退出码 0 表示成功，非 0 表示有错——模型靠这个判断测试是否通过
    return f"exit={proc.returncode}\n{output if output else '(无输出)'}"


# 工具的"说明书"：告诉模型每个工具叫什么、干什么、要什么参数。
# parameters 就是 JSON Schema，与 OpenAI function calling 的格式完全一致
TOOL_SCHEMAS = [
    {"name": "list_dir", "description": "列出沙箱内的文件",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "read_file", "description": "读取沙箱内指定文件的内容",
     "parameters": {"type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"]}},
    {"name": "write_file", "description": "把内容写入沙箱内指定文件（覆盖）",
     "parameters": {"type": "object",
                    "properties": {"name": {"type": "string"},
                                   "content": {"type": "string"}},
                    "required": ["name", "content"]}},
    {"name": "run_python", "description": "运行沙箱内的一个 .py 文件，返回退出码与输出",
     "parameters": {"type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"]}},
    {"name": "finish", "description": "任务目标已达成时调用，结束任务",
     "parameters": {"type": "object",
                    "properties": {"summary": {"type": "string"}},
                    "required": ["summary"]}},
]

# 工具名 -> 实现函数的映射：模型只能报工具名，实际执行由这张表分发
TOOL_IMPL = {
    # 注意 finish 不在实现表里：它是"任务结束信号"，在控制循环里特殊处理
    "list_dir": tool_list_dir,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "run_python": tool_run_python,
}


# ========================= 3. Mini 客户端 =========================
def chat(messages, temperature=0.0, max_retries=3, timeout=180):
    # 最小 OpenAI 兼容客户端：拼请求体 -> POST -> 解析响应（带重试）
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {"model": LLM_MODEL_ID, "messages": messages, "temperature": temperature,
               "tools": [{"type": "function", "function": t} for t in TOOL_SCHEMAS]}
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # 网络偶发失败时重试，等待时间逐次翻倍（指数退避），不轻易放弃
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            return data["choices"][0]["message"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 4. 控制循环 =========================
def run_agent(task, max_steps=10):
    # 控制循环：反复"问模型 -> 执行工具 -> 结果回喂"，直到模型调 finish 或步数用尽
    messages = [
        # system 提示词里写死了工作方法：这正是"红-绿循环"的驱动指令——
        # 先运行测试看它红（失败），改代码，再运行看它绿（通过），才许 finish
        {"role": "system", "content":
            "你是软件工程助手，只能操作给定沙箱内的文件。"
            "先运行测试观察失败，再修改代码，再运行测试确认通过。"
            "测试全部通过后调用 finish 结束。"},
        {"role": "user", "content": task},
    ]
    done = False
    stop_reason = None
    # 步数上限：没有它，模型若陷入循环会一直烧 token
    for step in range(1, max_steps + 1):
        print(f"\n--- step {step}/{max_steps} ---")
        reply = chat(messages)
        calls = reply.get("tool_calls") or []
        # 模型这条回复（含 tool_calls）先记进历史，保持上下文完整
        messages.append({"role": "assistant", "content": reply.get("content") or "",
                         **({"tool_calls": calls} if calls else {})})
        if not calls:
            # 模型光说话不调工具：多半是忘了流程，nudge 一下让它继续
            messages.append({"role": "user",
                             "content": "任务还没完成，请继续用工具或调用 finish。"})
            continue
        for call in calls:
            name = call["function"]["name"]
            # 模型给出的 arguments 是 JSON 字符串，要解析成字典
            arguments = json.loads(call["function"].get("arguments") or "{}")
            print(f"[动作] {name}({str(arguments)[:80]}...)" if len(str(arguments)) > 80
                  else f"[动作] {name}({arguments})")
            try:
                if name == "finish":
                    # finish 是结束信号：不执行任何代码，只记录"任务完成"
                    result = f"任务结束：{arguments.get('summary', '')}"
                    done = True
                    stop_reason = "model_finish"
                else:
                    result = TOOL_IMPL[name](arguments)
            except (PermissionError, KeyError) as e:
                # 关键设计：错误不抛出去让程序崩溃，而是转成文字结果回喂模型——
                # 比如路径越界时，模型能看到报错并换一个合法路径重试
                result = f"错误：{e}"
            text = result if isinstance(result, str) else str(result)
            print(f"[结果] {text[:200]}")
            # 把工具执行结果回喂给模型，它据此决定下一步动作
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                             "content": text})
        if done:
            break
    if not done:
        stop_reason = "max_steps"
    print(f"\n=== 终止：{stop_reason} ===")


# ========================= 5. 演示主流程 =========================
def main():
    # 演示主流程：准备沙箱 -> 交给 agent 修 bug -> 打印最终代码
    print("=" * 60)
    print("P5 案例：终端 Coding Agent（沙箱修 Bug）")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}")
    ensure_sandbox()
    print(f"沙箱: {SANDBOX}")
    print("演示项目：shop.py 的 final_price 有 bug，test_shop.py 是验收测试\n")

    task = ("运行 test_shop.py，观察失败原因；修复 shop.py 中的 bug；"
            "再运行测试确认全部通过后调用 finish。")
    run_agent(task)

    # 收尾展示：agent 修改后的 shop.py 长什么样
    print("\n--- 最终 shop.py ---")
    with open(os.path.join(SANDBOX, "shop.py"), encoding="utf-8") as f:
        print(f.read())
    print("要点：沙箱边界检查发生在每个工具入口；run_python 有超时与输出截断；"
          "红-绿循环（失败->修复->通过）由模型自己驱动。")


if __name__ == "__main__":
    main()
