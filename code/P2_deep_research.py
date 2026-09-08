# -*- coding: utf-8 -*-
"""
P2 实战案例 — Deep Research：迭代式深度调研
===========================================

运行前修改配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

联网搜索 key 在 websearch.py 顶部配置区设置（Exa / Parallel 均可）。

运行：  python P2_deep_research.py

本案例演示 Deep Research 的最小可运行骨架：
  1. 计划：把研究问题分解成 3 个可检索的子问题（结构化输出）
  2. 执行：逐个子问题联网检索，证据库按 URL 去重、累积、限量
  3. 综合：基于全部证据写成带引用编号的研究报告
  4. 预算：搜索次数与证据总量双重上限，防止成本失控

如何阅读本文件（给第一次写网络程序的读者）：
  1. 先看 plan_subquestions()：让模型输出 JSON 格式的子问题列表，
     解析失败就重试——"结构化输出重试"是让模型当调度器的关键技巧。
  2. 再看 EvidenceStore：证据库按 URL 去重、受字符预算约束，
     每条证据的全局编号就是最终报告里的引用号 [n]。
  3. 最后看 execute_research / synthesize：检索循环和成稿。
"""

import json
import re
import time
import urllib.error
import urllib.request

import websearch

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
MAX_SUBQUESTIONS = 3        # 子问题上限
MAX_EVIDENCE_CHARS = 24000  # 证据总字符预算（组进提示词前截断）
# 预算是"机器护栏"：模型再能编计划，也不能突破这两个上限，
# 防止一次调研把搜索配额和模型上下文窗口打爆。
# =======================================================================


# ========================= 2. Mini 客户端 =========================
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=3000):
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


def extract_json(text):
    # 模型经常"好心"在 JSON 外面包一层 ```json 代码块或解释文字，
    # 所以解析分两步：先直接解析，失败再从代码块里抠出来。
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 用正则匹配 ```json ... ``` 围栏里的内容（DOTALL 让 . 能匹配换行）。
    match = re.search(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"回复中找不到合法 JSON：{text[:120]!r}...")


# ========================= 3. 计划：分解子问题 =========================
def plan_subquestions(question, max_attempts=3):
    # 大问题往往拆开查更准：让模型把研究问题分解成若干个
    # "具体、可搜索、互补不重复"的子问题，再逐个联网检索。
    messages = [
        {"role": "system", "content":
            "你是深度调研规划器。把研究问题分解成 "
            f"{MAX_SUBQUESTIONS} 个可以独立联网检索的子问题。"
            "子问题要具体、可搜索、互补而不重复，"
            '输出 JSON：{"subquestions": ["...", "..."]}，只输出 JSON。'},
        {"role": "user", "content": question},
    ]
    # 结构化输出重试：模型输出可能不是合法 JSON 或子问题太少，
    # 解析/校验失败就再要一次，最多 3 次——这是拿到结构化输出的
    # 最朴素也最常用的手段。
    for attempt in range(1, max_attempts + 1):
        try:
            data = extract_json(chat(messages))
            # 去掉空字符串，只留有效的子问题。
            subs = [s.strip() for s in data.get("subquestions", []) if s.strip()]
            # 至少 2 个子问题才值得"分解"，否则视为失败重试。
            if len(subs) >= 2:
                return subs[:MAX_SUBQUESTIONS]
            raise ValueError(f"有效子问题不足：{subs}")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[plan attempt {attempt}] 解析失败：{e}")
    raise RuntimeError("子问题分解失败")


# ========================= 4. 执行：迭代检索，累积证据库 =========================
class EvidenceStore:
    """证据库：按 URL 去重，总量有预算，每条证据有全局编号（即引用号）。"""

    def __init__(self, budget_chars):
        self.budget_chars = budget_chars
        self.items = []      # [{"url", "title", "text", "n"}]
        self.seen_urls = set()
        # set（集合）查重是 O(1)：判断 URL 见没见过，比遍历列表快得多。

    def add(self, url, title, text):
        # 去重：不同子问题常搜到同一个网页，同一 URL 只入库一次，
        # 既省预算，也避免报告里引用重复来源。
        if url in self.seen_urls:
            return None      # 去重：同一 URL 不重复入库
        used = sum(len(it["text"]) for it in self.items)
        text = text.replace("\n", " ").strip()
        remaining = self.budget_chars - used
        # 预算护栏：剩余空间不足 100 字符就整体停摆，防止证据
        # 无限累积把后面的综合步骤挤爆上下文。
        if remaining <= 100:
            print(f"[budget] 证据预算已用尽（{used}/{self.budget_chars} 字符），停止入库")
            return None
        if len(text) > remaining:
            # 超预算的正文截断到剩余空间，"能装多少装多少"。
            text = text[:remaining]
        self.seen_urls.add(url)
        # n 是全局编号：按入库顺序 1、2、3……递增，这个编号就是
        # 最终报告里 [n] 引用号，全局唯一、可回溯。
        self.items.append({"url": url, "title": title, "text": text,
                           "n": len(self.items) + 1})
        # 返回编号，调用方借此知道这条证据是否真的入库了。
        return self.items[-1]["n"]

    def total_chars(self):
        # 当前证据总字符数，用于打印预算使用情况。
        return sum(len(it["text"]) for it in self.items)

    def render(self):
        # 把整库证据渲染成"编号 + 标题 + 网址 + 正文"的大文本块，
        # 直接塞进综合步骤的提示词里。
        return "\n\n".join(
            f"[{it['n']}] {it['title']}\n{it['url']}\n{it['text']}"
            for it in self.items)


def execute_research(provider, subquestions):
    # 执行阶段：逐个子问题检索，把新证据累积进同一个证据库。
    store = EvidenceStore(MAX_EVIDENCE_CHARS)
    for qi, sub in enumerate(subquestions, 1):
        print(f"\n[research {qi}/{len(subquestions)}] {sub}")
        hits, pages = provider.search_and_fetch(sub, num_results=2, max_chars=2500)
        for hit, page in zip(hits, pages):
            # 优先用正文，抓不到就退回搜索摘要。
            text = page.text if page and page.text else hit.snippet
            n = store.add(hit.url, page.title if page and page.title else hit.title,
                          text)
            # add 返回编号 = 入库成功；返回 None = 重复或超预算被拒。
            if n:
                print(f"  + 证据[{n}] {hit.url}（{len(text)} 字符）")
            else:
                print(f"  - 跳过（重复或超预算）{hit.url}")
        print(f"  证据库：{len(store.items)} 条 / {store.total_chars()} 字符")
    return store


# ========================= 5. 综合：带引用的研究报告 =========================
def synthesize(question, store):
    # 综合阶段：一次 LLM 调用，把全部证据渲染进提示词，
    # 要求模型产出带 [n] 引用号的报告，并主动交代"证据覆盖不到什么"。
    reply = chat([
        {"role": "system", "content":
            "你是研究报告作者。只依据给出的证据材料，写出结构化研究短报告：\n"
            "## 结论（3 句以内）\n## 关键发现（3-5 条，每条标注证据编号 [n]）\n"
            "## 局限（1-2 条，指出证据覆盖不到的方面）\n"
            "证据里没有的信息不要写。"},
        {"role": "user", "content":
            f"研究问题：{question}\n\n证据材料（编号即引用号）：\n{store.render()}"},
    ])
    return reply.strip()


# ========================= 6. 演示主流程 =========================
def main():
    print("=" * 60)
    print("P2 案例：Deep Research 迭代式深度调研")
    print("=" * 60)
    provider = websearch.make_provider()
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}")
    print(f"搜索: {provider.name}\n")

    question = "现在本地部署大模型（本地推理引擎）有哪些主流选择，各自适合什么场景？"
    print(f"[question] {question}\n")

    subs = plan_subquestions(question)
    print(f"[plan] 分解出 {len(subs)} 个子问题：")
    for s in subs:
        print(f"  - {s}")

    store = execute_research(provider, subs)
    print(f"\n[evidence] 证据库最终：{len(store.items)} 条 / "
          f"{store.total_chars()} 字符（预算 {MAX_EVIDENCE_CHARS}）\n")

    report = synthesize(question, store)
    print("=" * 60)
    print("研究报告：")
    print(report)
    print("\n要点：计划-执行-综合三段式；证据库全局编号即引用号；"
          "搜索次数与证据总量都有预算上限。")


if __name__ == "__main__":
    main()
