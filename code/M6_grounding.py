# -*- coding: utf-8 -*-
"""
M6 完整案例 — Grounding：检索、证据与拒绝编造
==============================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx（建议支持指令跟随较好的模型）

运行：  python M6_grounding.py

本案例演示本章核心概念：
  1. 生成前先检索：答案必须来自检索到的证据，而不是模型参数里的记忆
  2. 引用机制：回答必须标注证据编号 [1][2]，可追溯
  3. 证据不足时必须拒答——"不知道"优于编造
  4. 检索不必向量库起步：关键词打分检索是理解 RAG 的第一性原理

如何阅读本文件：
  核心只看两个函数：retrieve —— 不用任何外部库，怎么把"与问题最相关
  的句子"从语料里捞出来；grounded_answer —— 怎么让模型只基于捞出来的
  证据作答并标注编号。CORPUS 和 QUESTIONS 是演示用的数据和脚本。
  第一次读 retrieve 时重点理解"字符 2-gram"这个打分思路，
  它是理解向量检索之前最直观的一步。
"""

import json
import os
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
# 与 M4/M5 相同的极简 HTTP 客户端：POST JSON 进、JSON 出，带重试。
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=1000):
    """调用 OpenAI 兼容接口，返回回答文本。带指数退避重试。"""
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
                # 间隔 1s、2s、4s 递增的指数退避
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 本地语料（运行时写入 corpus/ 目录） =========================
# 一小份演示语料：3 篇短文档。真实的 RAG 语料是成千上万篇文档，
# 但检索的原理是一样的——先从海量文本里找出相关的几段。
CORPUS = {
    "course_policy.txt": (
        "课程平台 AgentLab 的作业政策：每周三晚 23:59 截止提交，"
        "逾期每天扣 10%，三天后不再接受。小组作业最多 3 人一组。"
        "期中项目占 30%，期末 Capstone 占 40%，平时作业占 30%。"
    ),
    "server_ops.txt": (
        "生产服务器 WH-01 位于武汉机房，配置 64 核 CPU 与 512GB 内存。"
        "每晚 02:00 自动运行全量评估，耗时约 40 分钟。"
        "运维值班电话 027-888888，重大故障需 15 分钟内响应。"
    ),
    "scholarship.txt": (
        "奖学金政策：绩点 3.5 以上的学生可申请一等助学金 2000 元，"
        "绩点 3.0-3.5 可申请二等助学金 1000 元。"
        "申请材料需在每年 10 月 15 日前提交到教务系统。"
    ),
}


def build_corpus():
    """把语料写成真实文件，让检索流程更接近生产（读文件而非读内存）。
    检索器遍历的是磁盘上的 corpus/ 目录，和真实系统读文档库的方式一致。"""
    os.makedirs("corpus", exist_ok=True)   # 已存在时不报错
    for name, text in CORPUS.items():
        with open(os.path.join("corpus", name), "w", encoding="utf-8") as f:
            f.write(text)


# ========================= 4. 关键词检索器 =========================
def split_sentences(text):
    """把一篇文档切成句子：中文句号当分隔符，逐句产出（yield）。
    检索以"句子"为单位——比整篇文档更精准，比单词更有上下文。"""
    for seg in text.replace("。", "\n").split("\n"):
        seg = seg.strip()
        if seg:   # 跳过切分产生的空串
            yield seg


def retrieve(question, top_k=3):
    """朴素字符 2-gram 检索：给每个句子按问题词覆盖度打分，取 top-k。
    这是 RAG 的第一性原理——先找相关内容，再让模型只基于它作答。
    （中文没有空格分词，字符 2-gram 是无依赖方案；生产中会换成向量检索。）"""
    import re
    # 第 1 步：清洗问题，只保留字母数字和汉字，去掉标点等干扰
    clean = re.sub(r"[^\w\u4e00-\u9fff]", "", question)
    # 第 2 步：把问题切成"字符 2-gram"。中文没有空格，没法按词切分，
    # 于是把文本切成相邻两个字一组来比，例如"期中项目"切成
    # {"期中","中项","项目"}。两个文本共享的 2-gram 越多，越可能相似——
    # 这就是不用分词器、不用向量库也能算"相似度"的土办法。
    question_terms = {clean[i:i + 2] for i in range(len(clean) - 1)}
    scored = []
    # 第 3 步：遍历 corpus/ 目录下的每个文件、每句话，逐句打分
    for doc in os.listdir("corpus"):
        with open(os.path.join("corpus", doc), encoding="utf-8") as f:
            text = f.read()
        for sent in split_sentences(text):
            # 打分规则：问题里有几个 2-gram 出现在这句话中，就得几分
            score = sum(1 for t in question_terms if t in sent)
            if score > 0:
                scored.append((score, doc, sent))
    # 第 4 步：按分数从高到低排序，取前 top_k 句作为检索结果
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


# ========================= 5. 接地回答器 =========================
def grounded_answer(question):
    """接地（grounding）= 让回答"踩在"证据上，而不是踩在模型记忆上。
    流程：检索 → 组装带编号的证据 → 要求模型引用编号作答。
    证据不足时拒答："不知道"永远优于一本正经地编造（幻觉）。"""
    evidence = retrieve(question)
    if not evidence:
        # 一个相关句子都没检索到：直接拒答，不给模型编造的机会
        return "（未检索到任何相关证据，拒答）", []

    # 把证据编号成 [1][2][3] 并注明来源文件。编号让每个关键信息
    # 都可追溯——读者能核对"这句话到底出自哪篇文档哪一句"。
    context_block = "\n".join(
        f"[{i+1}] （来源 {doc}）{sent}" for i, (score, doc, sent) in enumerate(evidence))
    print(f"[retrieve] 命中 {len(evidence)} 条证据：")
    for i, (score, doc, sent) in enumerate(evidence):
        print(f"  [{i+1}] ({score}分, {doc}) {sent[:40]}...")

    # 系统提示里两条铁律：1) 只依据证据回答并标注编号；
    # 2) 证据不够就明说"证据不足"，禁止编造。
    # 这是把"拒答优于编造"从口号落实为提示词约束。
    answer = chat([
        {"role": "system", "content":
            "你是资料问答助手。只依据提供的证据回答，每个关键信息后标注证据编号如 [1]。"
            "如果证据不足以回答问题，必须回答'证据不足，无法回答'，禁止编造。\n\n"
            f"证据：\n{context_block}"},
        {"role": "user", "content": question},
    ])
    return answer.strip(), evidence


# ========================= 6. 演示主流程 =========================
# 4 个测试问题覆盖三种情形：能答（有证据）、能答、期望拒答（语料里没有）。
QUESTIONS = [
    "期中项目占总成绩多少？",
    "服务器 WH-01 出了重大故障，多久内必须响应？打什么电话？",
    "一等助学金多少钱？",           # 语料里写的是"助学金"而非"奖学金"细节可答
    "课程平台支持微信登录吗？",       # 语料里没有：期望拒答
]


def main():
    # 主流程：先把语料写成真实文件，再逐个问题走"检索 → 接地回答"
    print("=" * 60)
    print("M6 案例：检索、证据与拒绝编造")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    build_corpus()
    for q in QUESTIONS:
        print(f"\n>>> 问题：{q}")
        answer, _ = grounded_answer(q)
        print(f"<<< 回答：{answer}")


if __name__ == "__main__":
    main()
