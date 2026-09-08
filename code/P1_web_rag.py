# -*- coding: utf-8 -*-
"""
P1 实战案例 — 联网 RAG：检索接地的生产形态
==========================================

运行前修改配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

联网搜索 key 在 websearch.py 顶部配置区设置（支持 Exa / Parallel，
环境变量 EXA_API_KEY / PARALLEL_API_KEY / WEBSEARCH_PROVIDER 可覆盖）。

运行：  python P1_web_rag.py

本案例演示：
  1. 直答模式：模型不联网，凭训练记忆回答时效性问题 -> 可能编造
  2. 接地模式：先联网取证，再基于证据回答，并强制标注引用 [n]
  3. 拒答机制：证据不足时明确说"无法回答"，而不是硬编

如何阅读本文件（给第一次写网络程序的读者）：
  1. 先看 chat()：一个 ~20 行的"迷你 LLM 客户端"，向 OpenAI 兼容接口
     发 HTTP 请求并解析回复，带指数退避重试。
  2. 再看 build_context()：把搜索结果"组包"成带编号 [1] [2] 的证据块，
     编号即引用号，模型回复里的 [n] 就能对应回具体网页。
  3. 最后看 answer_directly / answer_with_grounding 两种模式的对比，
     以及 GROUNDED_SYSTEM 里约束模型行为的三条铁律。
"""

import json
import time
import urllib.error
import urllib.request

import websearch   # 同目录的搜索封装模块：统一接口，provider 可切换

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
# 不用任何第三方 SDK，直接用 Python 标准库向 LLM 的 HTTP 接口发请求。
# 好处：能看清"调用大模型本质上就是发一个 HTTP POST 请求"这件事。
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=2000):
    # OpenAI 兼容接口的地址固定是 {BASE_URL}/chat/completions。
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体是 JSON：模型名 + 消息列表 + 采样参数。
    # temperature=0 让输出尽量确定，便于复现教学效果。
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    # Authorization: Bearer <key> 是 OpenAI 兼容接口的标准认证头。
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            # 打印 token 用量，帮助读者直观感受每次调用的成本。
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 回复文本藏在嵌套结构 choices[0].message.content 里。
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            # 网络/服务抖动是常态，所以重试；sleep 2^attempt 秒
            # 叫"指数退避"：第 1 次等 2 秒、第 2 次等 4 秒……
            # 避免密集重试把已经过载的服务器再打一轮。
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 证据组包 =========================
# "组包"= 把检索到的材料整理成模型能读懂、能引用的格式。
# 编号 [1] [2] 就是引用号：模型回复里的 [n] 对应这里的第 n 块证据，
# 读者可据此回溯到具体网页——这是接地回答可验证的关键。
def build_context(hits, pages, max_chars=900):
    """把搜索结果 + 正文拼成带编号的证据块，喂给模型。"""
    blocks = []
    # zip 把第 i 条搜索结果和第 i 个正文配对；enumerate 从 1 开始
    # 计数，得到证据编号 1, 2, 3……
    for i, (hit, page) in enumerate(zip(hits, pages), 1):
        # 优先用抓到的正文；正文抓取失败（page 为 None 或空）就退回摘要。
        text = (page.text if page and page.text else hit.snippet)
        # 把换行压成空格并截断：模型上下文有限，每条证据留 900 字符够用。
        text = text.replace("\n", " ").strip()[:max_chars]
        title = page.title if page and page.title else hit.title
        # 每块证据的格式：[编号] 标题 + 网址 + 正文。
        blocks.append(f"[{i}] {title}\n{hit.url}\n{text}")
    return "\n\n".join(blocks)


# 受限生成的核心：用系统提示给模型立规矩，只允许它做三件事——
# 标引用、不编造、不足就拒答。这三条是检索接地（RAG）的铁律。
GROUNDED_SYSTEM = (
    "你是带引用的问答助手。只根据给出的证据材料回答问题：\n"
    "1. 每个事实性陈述后标注来源编号，如 [1] [2]\n"
    "2. 证据材料里没有的信息，不要编造\n"
    "3. 如果证据不足以回答，明确说\"根据检索到的证据无法回答\"，并说明缺什么\n"
    "回答不超过 200 字。"
)


# ========================= 4. 两种模式 =========================
def answer_directly(question):
    """方式 A：直答。模型只凭参数记忆，不联网。"""
    # 只有 system+user 消息里没有证据材料，模型只能"凭记忆"回答。
    print(f">>> [直答] {question}")
    reply = chat([
        {"role": "user", "content": question},
    ])
    print(f"<<< 直答：\n{reply.strip()}\n")
    return reply.strip()


def answer_with_grounding(provider, question, num_results=3):
    """方式 B：接地。联网取证 -> 组包 -> 带引用回答 -> 证据不足则拒答。"""
    print(f">>> [接地] {question}")
    print("[search] 联网检索中...")
    # 一步完成"搜索 + 抓正文"，拿到两份对齐的列表。
    hits, pages = provider.search_and_fetch(question, num_results=num_results)
    print(f"[search] 命中 {len(hits)} 条：")
    for i, h in enumerate(hits, 1):
        print(f"  [{i}] {h.title}  {h.url}")

    # 组包：把证据块连同问题一起放进 user 消息，system 消息
    # 里的三条铁律负责约束模型"只能基于这些证据说话"。
    context = build_context(hits, pages)
    reply = chat([
        {"role": "system", "content": GROUNDED_SYSTEM},
        {"role": "user", "content": f"证据材料：\n{context}\n\n问题：{question}"},
    ])

    # 简单的"事后检查"：回复里有没有引用标注 [n]、有没有拒答表述。
    has_citation = "[1]" in reply or "[2]" in reply
    refused = "无法回答" in reply
    print(f"[check] 引用标注: {'有' if has_citation else '无'} | "
          f"拒答: {'是' if refused else '否'}")
    print(f"<<< 接地回答：\n{reply.strip()}\n")
    return reply.strip()


# ========================= 5. 演示主流程 =========================
def main():
    print("=" * 60)
    print("P1 案例：联网 RAG（检索接地的生产形态）")
    print("=" * 60)
    # 工厂模式：按配置区/环境变量决定用 Exa 还是 Parallel，
    # 后面的代码完全不关心具体是哪家。
    provider = websearch.make_provider()
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}")
    print(f"搜索: {provider.name}\n")

    # 时效性问题：训练数据里的答案是过时的，直答有编造风险
    q1 = "vLLM 现在怎么启动一个 OpenAI 兼容服务器？用什么命令？"
    print("---------- ① 直答模式（不联网） ----------")
    answer_directly(q1)

    print("---------- ② 接地模式（联网取证后回答） ----------")
    answer_with_grounding(provider, q1)

    # 没有真实答案的问题：接地模式应当拒答，而不是硬编
    q2 = "AgentLab 课程平台 4.0 版本内测的报名截止日期是什么时候？"
    print("---------- ③ 拒答测试（证据不足时） ----------")
    answer_with_grounding(provider, q2)

    print("要点：直答暴露编造风险；接地回答每个事实都带 [n] 可回溯；"
          "证据不足时拒答优于硬编——这是检索接地的三条铁律。")


if __name__ == "__main__":
    main()
