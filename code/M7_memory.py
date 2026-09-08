# -*- coding: utf-8 -*-
"""
M7 完整案例 — Memory：跨会话的记忆持久化
=========================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

运行：  python M7_memory.py

本案例演示本章核心概念：
  1. 对话历史 ≠ 记忆：记忆是"从对话中提炼出的、值得跨会话保留的事实"
  2. 记忆必须显式持久化（本案例用 JSON 文件，原理同生产中的数据库）
  3. 新会话启动时把记忆注入系统提示，模型才能"记得"用户
  4. 记忆提取是结构化输出问题：解析失败要重试（复用 M1 的方法）

如何阅读本文件（写给零基础读者）：
  - 全文只有约 160 行，按 1~5 的分区编号从上往下读即可，每个分区是一个独立职责。
  - 第 1 区是配置，第 2 区是调用大模型的"迷你客户端"（不用装任何第三方库），
    第 3 区是记忆的读写（JSON 文件 = 最简版数据库），第 4 区是记忆的提炼与注入，
    第 5 区把前面的零件串成"两次会话"的演示。
  - 建议先跑一遍程序，对照运行输出再回来看代码；正文有 # 注释的行是关键逻辑。
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================

MEMORY_FILE = os.path.join("memory", "memory.json")
# 记忆文件的存放路径：memory/ 目录下的 memory.json。
# 为什么用 JSON 文件？因为它就是一个"最简版数据库"：
#   - 程序重启后数据还在（持久化），这是"跨会话记忆"的物理基础；
#   - 生产系统会换成 SQLite/Redis 等真数据库，但读写思路完全一样。


# ========================= 2. Mini 客户端 =========================
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=1500):
    """调用大模型的最小客户端：发 HTTP 请求，拿回回复文本。
    不依赖 openai 库，只用 Python 自带的 urllib，方便看清楚网络调用的本质。"""
    # 接口地址：把配置里的基础地址拼上统一的路径 /chat/completions
    #（这是 OpenAI 兼容 API 的通用约定，Ollama/DeepSeek 等都遵守）
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：把"用哪个模型 + 完整对话历史 + 温度/长度限制"打包成 JSON 字符串
    #（.encode("utf-8") 是因为 HTTP 请求体要求字节而不是字符串）
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    # 请求头：声明内容类型，并用 Bearer 方式带上 API Key 做身份验证
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # 网络请求随时可能失败（断网、服务重启），所以重试是客户端的标配。
    # 共尝试 max_retries+1 次；2**attempt 让每次等待时间翻倍（1s、2s、4s...），
    # 给服务端留出恢复时间，这叫"指数退避"。
    for attempt in range(max_retries + 1):
        try:
            # 构造请求对象并真正发出，timeout 限制最多等多久，防止无限挂起
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            # 打印本次调用的 token 用量：token 是模型计费与上下文长度的单位，
            # 从一开始就盯着它，是控制成本的好习惯
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # API 返回的 JSON 层层嵌套，真正的话在 choices[0].message.content 里
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            # 记下失败原因，等一会儿再试；只有重试用尽才向调用方抛异常
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


def extract_json(text):
    """复用 M1 的方法：从回复中提取 JSON，支持 ```json 代码块。
    模型有时会用 Markdown 代码块包住 JSON，所以两种格式都要能解析。"""
    # 第一选择：整个回复就是纯 JSON，直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 第二选择：JSON 被包在 ```json ... ``` 代码块里，用正则把中间那段抠出来
    match = re.search(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # 两种格式都解析不出来，说明模型没按要求输出，交给调用方重试
    raise ValueError(f"回复中找不到合法 JSON：{text[:120]!r}...")


# ========================= 3. 记忆存储层 =========================
def load_memory():
    """从磁盘加载记忆。文件不存在 = 全新用户。
    把"读数据"封装成一个函数，调用方不用关心文件细节，这就是分层的好处。"""
    # os.path.exists 先判断文件在不在，避免对不存在的文件 open 报错
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f:
            memory = json.load(f)   # 把 JSON 文件读回 Python 列表
        print(f"[memory] 从 {MEMORY_FILE} 加载了 {len(memory)} 条记忆")
        return memory
    # 第一次使用时还没有记忆文件，返回空列表即可
    print(f"[memory] {MEMORY_FILE} 不存在，全新会话")
    return []


def save_memory(memory):
    """把记忆写回磁盘——这一步让记忆跨会话存活。
    不写盘的话，程序一退出记忆就消失了，等于没记。"""
    # 先确保 memory/ 目录存在（exist_ok=True：目录已存在也不报错）
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False 让中文原样存入文件（否则会变成 \uXXXX 转义码）
        # indent=2 让文件带缩进，人类可以直接打开阅读
        json.dump(memory, f, ensure_ascii=False, indent=2)
    print(f"[memory] 已保存 {len(memory)} 条记忆到 {MEMORY_FILE}")


# ========================= 4. 记忆提取与注入 =========================
def extract_facts(user_text, existing_memory, max_attempts=3):
    """从用户消息中提炼值得长期记住的事实（结构化输出 + 失败重试）。
    为什么存"提炼后的事实"而不是原始聊天记录？
      - 原始记录又长又杂，全部塞进提示词又贵又吵，模型反而抓不住重点；
      - 提炼成"姓名/偏好/目标"这样的短句，几十个字就能让模型"记得"用户，
        而且过滤掉了寒暄等不值得记住的内容。"""
    # 这里的提示词让模型做两件事：提炼事实 + 输出 JSON 数组（结构化输出），
    # 结构化输出便于程序直接使用，而不是去解析一段自由文本
    messages = [
        {"role": "system", "content":
            "从用户消息中提炼值得长期记住的事实（姓名、偏好、目标等），"
            "输出 JSON 数组，每个元素是一个短字符串。"
            "没有值得记住的内容就输出 []。只输出 JSON。"},
        {"role": "user", "content":
            # 把已有记忆也给模型看，避免重复提炼已经记过的内容
            f"已有记忆：{json.dumps(existing_memory, ensure_ascii=False)}\n"
            f"用户新消息：{user_text}"},
    ]
    # 模型输出不一定每次都合法，最多试 max_attempts 次，全失败就放弃（返回空）
    for attempt in range(1, max_attempts + 1):
        try:
            facts = extract_json(chat(messages))
            if not isinstance(facts, list):
                # 就算解析成了 JSON，顶层也必须是数组，否则后续代码会出错
                raise ValueError("顶层不是数组")
            # 逐项转成字符串并过滤空值，保证存进记忆的都是干净的短句
            return [str(x) for x in facts if x]
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[attempt {attempt}] 记忆提取失败：{e}")
    return []


def build_system_prompt(memory):
    """把记忆"注入"系统提示：新会话里模型本身什么都不知道，
    是我们把这些事实写进提示词，它才表现得"记得用户"。"""
    # 没有记忆时用最朴素的开场白即可
    if not memory:
        return "你是个人助理，回答简短。"
    # 有记忆时逐条列出来，模型读到这些，回答就会带上"上次聊过"的感觉
    return ("你是个人助理，回答简短。以下是你在过往会话中记住的用户信息：\n"
            + "\n".join(f"- {m}" for m in memory))


# ========================= 5. 演示主流程：两次"会话" =========================
# 两条演示消息：第一条让 Agent 认识用户，第二条考察它是否"记得"
SESSION1 = "你好，我叫小明，喜欢跑步，正在准备考研，目标是华中农业大学。"
SESSION2 = "你还记得我是谁吗？我最近该注意什么？"


def main():
    print("=" * 60)
    print("M7 案例：跨会话记忆持久化")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    # --- 会话 1：用户自我介绍，Agent 提炼并保存记忆 ---
    print(">>> [会话1] 用户：", SESSION1)
    # 先读旧记忆（首次运行为空），再从新消息里提炼事实
    memory = load_memory()
    facts = extract_facts(SESSION1, memory)
    print("[memory] 新提炼的记忆：", facts)
    # 去重合并：只追加记忆里没有的新事实（in 判断列表是否已含该元素）
    for fact in facts:
        if fact not in memory:
            memory.append(fact)
    # 关键一步：写盘。没有这一步，进程结束后记忆就丢了
    save_memory(memory)
    # 把磁盘上的文件原文打印出来，让读者亲眼看到"记忆确实被存下来了"
    with open(MEMORY_FILE, encoding="utf-8") as f:
        print("[memory] 磁盘上的记忆文件内容：")
        print(f.read())

    # --- 会话 2：模拟 Agent 重启，从磁盘重新加载记忆 ---
    # 真实场景中两次会话之间程序早就关了，这里只是演示：内存变量全丢，
    # 唯一能依靠的就是磁盘上的 memory.json
    print("\n--- 模拟 Agent 重启（进程结束再启动）---\n")
    print(">>> [会话2] 用户：", SESSION2)
    # 重启后第一步：从磁盘把记忆读回来
    memory = load_memory()
    # 把记忆注入系统提示，模型才知道"小明是谁"；对话历史里并没有这条消息
    answer = chat([
        {"role": "system", "content": build_system_prompt(memory)},
        {"role": "user", "content": SESSION2},
    ])
    print(f"<<< [会话2] 助手：{answer.strip()}")

    print("\n要点：会话2 能答对，靠的是磁盘上的 memory.json，"
          "而不是上一轮对话历史。")


if __name__ == "__main__":
    main()
