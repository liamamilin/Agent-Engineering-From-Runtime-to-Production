# -*- coding: utf-8 -*-
"""
P3 实战案例 — 计划-审批式调研（Human in the Loop）
==================================================

运行前修改配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

联网搜索 key 在 websearch.py 顶部配置区设置（Exa / Parallel 均可）。

运行：  python P3_hitl_research.py
（纯自动演示：printf "a\n" | python P3_hitl_research.py）

本案例演示把 M8 的审批门用到真实联网调研上：
  1. Agent 先产出可执行的调研计划（search 步骤 + synthesize 步骤）
  2. 每一步执行前必须过人工审批门（stdin 交互）：
       a=批准全部计划   s=逐项审批（可跳过单项）   q=放弃
  3. 执行期还有第二道机器护栏：搜索次数与证据总量预算（M10 思想）
  4. 人的意图决定"做什么"，护栏决定"最多做多少"，两层正交

如何阅读本文件（给第一次写网络程序的读者）：
  1. 先看 draft_plan()：让模型输出 JSON 步骤列表（结构化输出 + 重试）。
  2. 再看两个"审批门"：用真实的 input() 在终端等人工按键确认，
     人才是执行网络操作的最后决策者。
  3. 最后看 Guardrails：就算人批了，机器护栏照样卡额度——
     审批管意图、护栏管额度，两层互不替代。
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
MAX_TOTAL_SEARCHES = 4      # 机器护栏：本次会话最多联网搜索次数
MAX_EVIDENCE_CHARS = 16000  # 机器护栏：证据总字符预算
# 注意这两个上限与人工审批是"两层正交"的机制：
#   审批门（人）回答"这个动作该不该做"——管意图；
#   护栏（机器）回答"额度还剩多少"——管数量。
# 人批了超出额度的动作也不行，护栏说了算。
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
    # 先尝试整体解析，失败再从 ```json 代码块里抠——
    # 模型常给 JSON 套一层 Markdown 代码围栏。
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"回复中找不到合法 JSON：{text[:120]!r}...")


# ========================= 3. 计划：可审批的动作序列 =========================
# 与 P2 的区别：这里产出的不是"子问题"而是"动作序列"——
# 每一步都有明确的 action（search/synthesize），所以要交给人审批。
def draft_plan(question, max_attempts=3):
    """产出结构化调研计划：2-3 个 search 步骤 + 1 个 synthesize 步骤。"""
    messages = [
        {"role": "system", "content":
            "你是调研规划器。为研究问题设计 3 步计划："
            "前 2 步 action=search（query 是可联网检索的具体查询词，互补不重复），"
            '第 3 步 action=synthesize（desc 说明综合方式）。'
            '输出 JSON：{"steps": [{"action": "search", "query": "..."},'
            '{"action": "synthesize", "desc": "..."}]}，只输出 JSON。'},
        {"role": "user", "content": question},
    ]
    # 结构化输出重试：解析失败或计划里没有 search 步骤就再要一次。
    for attempt in range(1, max_attempts + 1):
        try:
            data = extract_json(chat(messages))
            steps = data.get("steps", [])
            # 校验：至少要有一步搜索，否则这个计划没有执行价值。
            if any(s.get("action") == "search" for s in steps):
                return steps
            raise ValueError(f"计划中没有 search 步骤：{steps}")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[plan attempt {attempt}] 解析失败：{e}")
    raise RuntimeError("计划生成失败")


# ========================= 4. 审批门（真实 stdin 交互） =========================
# 审批门 = Human in the Loop 的落地点：Agent 把"想做什么"摆到台面上，
# 真实的 input() 会阻塞程序、在终端等你按键，你不开口它就不动。
# 这保证联网等有成本的敏感操作永远由人拍板。
def show_plan(steps):
    # 把计划渲染成人能读懂的清单，供审批时参考。
    print("[计划]")
    for i, s in enumerate(steps, 1):
        what = s.get("query") or s.get("desc") or ""
        print(f"  步骤 {i}. {s['action']}: {what}")


def gate_whole_plan(steps):
    """整体审批门。返回 'a'（全批）/ 's'（逐项）/ 'q'（放弃）。"""
    # while True + 无效输入重问：人工交互必须容错，用户按错键
    # 不能让程序崩掉，也不能糊里糊涂放行。
    while True:
        cmd = input("[审批门] 批准该计划? a=批准全部 s=逐项审批 q=放弃: ").strip().lower()
        if cmd in ("a", "s", "q"):
            return cmd
        print("  无效输入，请输入 a / s / q")


def gate_step(i, step):
    """单步审批门。返回 True（执行）/ False（跳过）。"""
    while True:
        # 只展示前 40 字符，避免长查询把审批提示刷乱。
        what = step.get("query") or step.get("desc") or ""
        cmd = input(f"[审批门] 执行步骤 {i}（{step['action']}: {what[:40]}）? "
                    f"y=批准 n=跳过: ").strip().lower()
        if cmd == "y":
            return True
        if cmd == "n":
            return False


# ========================= 5. 执行（带机器护栏） =========================
class Guardrails:
    """第二道防线：与审批门正交的机器护栏，人批了也不能超。"""
    # 审批门管"意图"（做不做），护栏管"额度"（做多少）。
    # 两层正交意味着互不覆盖：a 键批准全部计划，也不代表能无限搜索。

    def __init__(self, max_searches, max_chars):
        self.max_searches = max_searches
        self.max_chars = max_chars
        self.searches = 0
        self.chars = 0
        self.seen_urls = set()

    def allow_search(self):
        # 额度检查：搜索次数达到上限后一律拒绝，并说明原因。
        if self.searches >= self.max_searches:
            print(f"  [护栏] 搜索次数已达上限 {self.max_searches}，拒绝")
            return False
        return True

    def record_search(self):
        # 每次真正联网后计数 +1，额度就是这么被消耗的。
        self.searches += 1

    def allow_evidence(self, url, text):
        # 证据入库前的双重检查：URL 去重 + 字符预算。
        if url in self.seen_urls:
            print(f"  [护栏] 重复 URL，跳过 {url}")
            return False
        # 预算按"总量"算：现有 + 新增不能超过上限，超了整条拒绝。
        if self.chars + len(text) > self.max_chars:
            print(f"  [护栏] 证据预算超限（{self.chars}+{len(text)}"
                  f">{self.max_chars}），拒绝入库")
            return False
        self.seen_urls.add(url)
        self.chars += len(text)
        return True


def execute(steps, provider, guard):
    # 执行阶段：跑每一步，search 步骤走护栏额度并累积证据，
    # synthesize 步骤只是登记，真正综合在后面的 synthesize() 里做。
    approved = []   # [{"action", "query"/"desc", "evidence": [编号]}]
    store = []      # 全局编号的证据列表
    searches_used = 0

    for i, step in enumerate(steps, 1):
        if step["action"] == "search":
            # 双保险：本地计数 + 护栏对象都查一遍，任一拒绝就跳过。
            if searches_used >= guard.max_searches or not guard.allow_search():
                print(f"  [跳过] 步骤 {i} 因护栏未执行")
                continue
            query = step["query"]
            print(f"\n[执行] 步骤 {i}: search(\"{query}\")")
            searches_used += 1
            guard.record_search()
            hits, pages = provider.search_and_fetch(query, num_results=2,
                                                    max_chars=2200)
            evidence_ns = []
            for hit, page in zip(hits, pages):
                # 优先用正文，抓不到就退回摘要。
                text = (page.text if page and page.text else hit.snippet)
                text = text.replace("\n", " ").strip()
                # 过了护栏（不重复、不超预算）才入库，len(store)+1
                # 就是这条证据的全局编号（即引用号）。
                if guard.allow_evidence(hit.url, text):
                    store.append({"url": hit.url,
                                  "title": page.title if page and page.title
                                  else hit.title, "text": text})
                    evidence_ns.append(len(store))
                    print(f"  + 证据[{len(store)}] {hit.url}")
            # 把"这一步搜到了哪些证据"记录回计划，便于追溯。
            approved.append({"action": "search", "query": query,
                             "evidence": evidence_ns})
        elif step["action"] == "synthesize":
            print(f"\n[执行] 步骤 {i}: synthesize（{step.get('desc', '')}）")
            approved.append({"action": "synthesize", "desc": step.get("desc", "")})
    return approved, store


def render_evidence(store):
    # 把证据列表渲染成"编号 + 标题 + 网址 + 正文"的文本块，
    # 编号按列表顺序 1..n，即报告里的引用号。
    return "\n\n".join(
        f"[{i}] {it['title']}\n{it['url']}\n{it['text']}"
        for i, it in enumerate(store, 1))


# ========================= 6. 综合报告 =========================
def synthesize(question, store):
    reply = chat([
        {"role": "system", "content":
            "你是研究报告作者。只依据给出的证据材料写研究短报告，"
            "结构：结论（3 句以内）+ 关键发现（每条标注 [n]）+ 局限。"
            "证据里没有的信息不要写。"},
        {"role": "user", "content":
            f"研究问题：{question}\n\n证据材料：\n{render_evidence(store)}"},
    ])
    return reply.strip()


# ========================= 7. 演示主流程 =========================
def main():
    print("=" * 60)
    print("P3 案例：计划-审批式调研（Human in the Loop）")
    print("=" * 60)
    provider = websearch.make_provider()
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}")
    print(f"搜索: {provider.name} | 护栏: 搜索<={MAX_TOTAL_SEARCHES}次, "
          f"证据<={MAX_EVIDENCE_CHARS}字符\n")

    question = "2026 年企业落地 AI Agent 的主要模式有哪些？"
    print(f"[question] {question}\n")

    steps = draft_plan(question)
    show_plan(steps)

    cmd = gate_whole_plan(steps)
    if cmd == "q":
        # 整体放弃：一行联网代码都没跑过，这就是"先审后行"。
        print("[abort] 用户放弃，未执行任何联网操作")
        return
    if cmd == "s":
        # 逐项审批模式：对每一步单独问一遍，可以只砍掉某一步
        # 而不放弃整个计划——细粒度的控制权交给用户。
        executed = []
        for i, step in enumerate(steps, 1):
            if gate_step(i, step):
                executed.append(step)
            else:
                print(f"  [跳过] 步骤 {i}")
        steps = executed if executed else []
    else:
        executed = steps

    if not executed:
        print("[abort] 无被批准的步骤")
        return

    # 执行前才创建护栏实例：额度只统计本次实际执行的部分。
    guard = Guardrails(MAX_TOTAL_SEARCHES, MAX_EVIDENCE_CHARS)
    _, store = execute(executed, provider, guard)
    print(f"\n[guard] 实际联网 {guard.searches} 次，证据 {len(store)} 条 / "
          f"{guard.chars} 字符")

    report = synthesize(question, store)
    print("=" * 60)
    print("调研报告：")
    print(report)
    print("\n要点：人的审批决定'做不做'，护栏决定'最多做多少'，两层正交；"
          "逐项审批模式可以砍掉单个步骤而不放弃整个计划。")


if __name__ == "__main__":
    main()
