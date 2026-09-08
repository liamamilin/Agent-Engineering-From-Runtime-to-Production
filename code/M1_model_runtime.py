# -*- coding: utf-8 -*-
"""
M1 完整案例 — Model Runtime：带重试与校验的结构化抽取器
=========================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.5:9b-mlx / deepseek-chat

运行：  python M1_model_runtime.py

本案例演示本章核心概念：
  1. Model 是运行时依赖，不是 Agent 本身（mini 客户端与业务逻辑分离）
  2. 结构化输出必须解析 + 校验，不能直接信任模型返回
  3. 重试策略处理两类故障：网络层临时错误、输出格式错误
  4. 每次调用都跟踪 token 用量

如何阅读本文件（零基础读者）：
  - 全部代码只用 Python 标准库，不需要 pip 安装任何东西。
  - 本文件讲的是"怎么稳定地用模型"：真实世界里，网络会抖动、模型会输出
    不合规范的 JSON，所以要有重试和校验。
  - 建议按编号顺序读：Mini 客户端（怎么调模型、怎么重试）-> 解析与校验
    （怎么检查模型输出）-> extract_meeting（把前面所有手段串起来）-> main()。
"""

# json：标准库，用于 JSON 与 Python 对象的互相转换。
# JSON 是 LLM API 的通用数据格式（形如 {"key": "值", "list": [1, 2]}）。
import json
# re：标准库的"正则表达式"模块，用于按模式从文本里找东西（这里用来找 ```json 代码块）。
import re
# time：标准库，sleep() 可以让程序暂停几秒——重试前歇一下就靠它。
import time
# urllib 是 Python 标准库自带的 HTTP 客户端，不用 pip 装任何东西
# 就能向 LLM 服务发网络请求；urllib.error 里有网络相关的异常类型。
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.5:9b-mlx"              # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
def chat(messages, temperature=0.0, max_retries=3, timeout=60):
    """调用 OpenAI 兼容的 /chat/completions 接口，返回回复文本与用量。

    这是全书统一的 mini 客户端：屏蔽 provider 差异，处理网络层临时错误，
    并在每次调用后报告 token 用量。

    参数说明（供零基础读者参考）：
      messages    对话历史，每项形如 {"role": ..., "content": ...}。
                  role 有四种：system（给模型的人设/规则）、user（用户说的话）、
                  assistant（模型说过的话）、tool（工具结果回传时用）。
      temperature 温度：控制模型回答随机性的旋钮，越低越稳定可复现，
                  越高越发散有创意。结构化抽取这类任务用 0.0 最合适。
      max_retries 网络失败时最多重试几次。
      timeout     网络请求的超时秒数，防止程序卡死。
    """
    # API 地址：去掉末尾多余的 "/"，再拼上 OpenAI 兼容服务统一约定的路径。
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：把参数打包成 dict 再转成 JSON 字节串（encode 是网络传输必需的编码步骤）。
    payload = json.dumps({
        "model": LLM_MODEL_ID,
        "messages": messages,
        "temperature": temperature,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    # ---- 重试机制 ----
    # 网络请求随时可能失败（服务重启、Wi-Fi 抖动……），所以不能一次失败就放弃。
    # 策略：失败后等待 2 ** attempt 秒再试——这叫"指数退避"：1s、2s、4s……
    # 间隔越来越长，给服务恢复的时间，也避免短时间内疯狂轰炸服务器。
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # usage 记录本次调用的 token 用量（token 大致相当于"半个词"，
            # 是 API 计费和上下文长度的基本单位），打印出来便于观察成本。
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 成功：取出模型回复的文本内容并返回，重试循环结束。
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            # 网络层错误：可重试（指数退避）
            last_error = e
            if attempt < max_retries:
                # 2 ** attempt 即 2 的 attempt 次方：1、2、4……秒，间隔指数增长。
                delay = 2 ** attempt
                print(f"[retry] 第 {attempt + 1} 次失败（{e}），{delay}s 后重试")
                time.sleep(delay)
    # 所有重试都失败：抛出异常，让调用方知道"这不是偶发问题"。
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 结构化输出解析与校验 =========================
# MEETING_SCHEMA 定义"合格输出长什么样"：每个字段必须存在、类型必须正确。
# 这里用的是最朴素的校验表（字段名 -> Python 类型），后面 validate() 按它逐项检查。
MEETING_SCHEMA = {
    "title": str,        # 会议主题
    "date": str,         # 日期，格式 YYYY-MM-DD
    "attendees": list,   # 参会人姓名列表
    "decisions": list,   # 形成的决定列表
}


def extract_json(text):
    """从模型回复中提取 JSON：先直接解析，再尝试从 ```json 代码块中提取。

    为什么需要它？模型经常不守规矩——你说"只输出 JSON"，
    它可能在前后加解释性文字，或者套一层 Markdown 代码块。
    所以要做两层尝试，尽量把 JSON "抢救"出来。
    """
    try:
        # 第一层尝试：整个回复就是 JSON，直接解析。
        return json.loads(text)
    except json.JSONDecodeError:
        # 解析失败不代表没有 JSON，可能只是裹在别的文字里，继续往下试。
        pass
    # 第二层尝试：用正则找出 ```json ... ``` 代码块里的内容再解析。
    # re.DOTALL 让 "." 也能匹配换行符，这样代码块可以跨多行。
    match = re.search(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # 两层都失败：抛错。这里绝不能"硬返回个默认值"糊弄过去——
    # 坏数据要显式暴露，由上层决定重试。
    raise ValueError(f"回复中找不到合法 JSON：{text[:120]!r}...")


def validate(data, schema):
    """按 schema 校验字段存在性与类型，返回错误信息列表（空列表=通过）。"""
    errors = []
    # 顶层必须是 dict（JSON 的"对象"），否则后面的逐字段检查无从谈起。
    if not isinstance(data, dict):
        return ["顶层必须是对象（dict）"]
    # 逐个字段对照 schema 检查：缺字段、类型不对都记下来。
    for field, expected in schema.items():
        if field not in data:
            errors.append(f"缺少字段 {field}")
        elif not isinstance(data[field], expected):
            errors.append(f"字段 {field} 类型错误：期望 {expected.__name__}，"
                          f"实际 {type(data[field]).__name__}")
    return errors


def extract_meeting(raw_text, max_attempts=3):
    """带格式重试的结构化抽取：解析/校验失败时把错误信息喂回模型重试。

    这是本文件的"主菜"：把 chat（网络重试）+ extract_json（解析）
    + validate（校验）三层保护串成一个闭环——
    模型输出不合格时，不是直接失败，而是把错误信息发回去让它改正。
    """
    # system 消息给模型定角色和输出格式规矩；字段要求写得越明确，出错越少。
    system = (
        "你是信息抽取助手。从会议纪要中抽取信息，"
        "只输出一个 JSON 对象，不要输出任何其他文字。"
        "字段：title(字符串)、date(YYYY-MM-DD 字符串)、"
        "attendees(字符串数组)、decisions(字符串数组)。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": raw_text},
    ]
    # 注意区分两层重试：chat() 里的重试管"网络失败"，
    # 这里的循环管"模型输出格式不对"——两类故障分开处理。
    for attempt in range(1, max_attempts + 1):
        reply = chat(messages, temperature=0.0)
        try:
            data = extract_json(reply)
        except (ValueError, json.JSONDecodeError) as e:
            # 解析失败：把模型刚才的回复（assistant 角色）和纠错提示（user 角色）
            # 追加进对话历史，让模型"看到自己刚才的输出"并知道错在哪，然后重试。
            print(f"[attempt {attempt}] 解析失败：{e}")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "JSON 格式错误，请重新只输出合法 JSON。"})
            continue
        errors = validate(data, MEETING_SCHEMA)
        if errors:
            # 校验失败：同样把具体错误信息喂回模型（比如"date 类型错误"），
            # 比笼统地说"错了"有效得多。
            print(f"[attempt {attempt}] 校验失败：{errors}")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user",
                             "content": f"字段校验未通过：{errors}。请修正后重新只输出 JSON。"})
            continue
        # 解析和校验都通过：返回干净的结构化数据。这是唯一的成功出口。
        return data
    # max_attempts 轮内始终不合格：放弃并抛错，宁可失败也不要返回坏数据。
    raise RuntimeError(f"抽取在 {max_attempts} 次尝试内未产出合法结果")


# ========================= 4. 演示主流程 =========================
MEETING_NOTE = """
会议纪要：新产品上线评审
时间：2026年9月10日下午2点
参会：张伟、李娜、王强
讨论内容：确认 v2.3 版本于9月18日上线；客服团队增加两人支援；
首页改版延后到下个季度。另外决定下周三前完成压测报告。
"""


def main():
    print("=" * 60)
    print("M1 案例：结构化抽取（重试 + 校验）")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    data = extract_meeting(MEETING_NOTE)
    # indent=2 让输出的 JSON 带缩进、更好读；ensure_ascii=False 让中文原样显示
    # （否则会变成 \u 转义的乱码样子）。
    print("\n抽取结果：")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    errors = validate(data, MEETING_SCHEMA)
    print(f"\n校验结果：{'通过' if not errors else errors}")


if __name__ == "__main__":
    main()
