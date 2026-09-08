# -*- coding: utf-8 -*-
"""
M5 完整案例 — Context Engineering：token 预算与历史压缩
========================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.5:9b-mlx / deepseek-chat

运行：  python M5_context_budget.py

本案例演示本章核心概念：
  1. 上下文是有限资源：超出预算必须裁剪，而不是无限堆消息
  2. 裁剪策略 = "旧历史压缩成摘要 + 保留最近若干轮原文"
  3. 裁剪后信息有损，所以系统提示里要带上"既往事实摘要"
  4. 每一轮都打印当前上下文规模，让预算可见

如何阅读本文件：
  核心只看两个东西：(1) estimate_tokens —— 怎么估算一段文字占多少
  token；(2) BudgetChatAgent —— 超预算时怎么把旧历史压缩成摘要。
  其余的 chat 函数和 CONVERSATION 对话脚本只是支撑代码。
  建议边跑边看输出里 [budget] / [context] 开头的日志，
  能直观看到上下文是怎么被"裁"下来的。
"""

import json
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"              # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
# 和 M4 一样的极简 HTTP 客户端，不装任何第三方库。
# 区别是这里每次调用都会打印 token 用量，方便观察上下文消耗。
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=1500):
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
            # usage 由服务端返回精确的 token 计数（prompt=输入 / completion=输出）
            usage = data.get("usage", {})
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                # 间隔 1s、2s、4s 递增，给服务端恢复时间
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 预算估算器 =========================
# token 是大模型处理文本的最小单位：模型读的不是"字"，而是 token。
# 一个汉字通常是 1 个左右 token，一个英文单词常被拆成 1~2 个 token。
# 上下文窗口（模型一次能"看到"的全部内容）按 token 计数，
# 计费也按 token 计数，所以它是必须精打细算的资源。
def estimate_tokens(text):
    """粗略估算：中文约 1 字 ≈ 1 token，英文约 4 字符 ≈ 1 token。
    精确计费用 API 返回的 usage；这里用于发送前的预算判断。
    （发送前你还拿不到服务端的精确计数，只能自己估。）"""
    # 统计中文字符个数：Unicode 范围 \u4e00-\u9fff 就是常用汉字区
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    # 剩下的非中文字符（字母/数字/标点）按 4 个字符折 1 token 粗算
    other = len(text) - cjk
    return cjk + other // 4


# ========================= 4. 带预算的对话 Agent =========================
class BudgetChatAgent:
    """超过 token 预算时，把旧历史压缩成摘要，只保留最近 turns_keep 轮。

    为什么旧历史被压缩成摘要、再注入 system 消息后，旧事实还能被召回？
    因为对话历史逐字逐句塞进上下文时极其昂贵且很快撑爆窗口；
    摘要保留了"人名、数字、结论"等关键事实，几十字就能替代几百字。
    每轮都把它放进 system 消息，等于每轮都向模型"重申"一次旧事实，
    模型看不到原始对话，但看得到事实本身——召回靠的是信息，不是原文。
    """

    def __init__(self, budget_tokens=800, turns_keep=2):
        # budget_tokens：本轮发送的上下文（system+历史+新问题）总 token 上限
        self.budget = budget_tokens
        # turns_keep：无论怎么压缩，最近这几轮原文永远保留（最近的话最相关）
        self.turns_keep = turns_keep
        self.system_base = "你是项目助理，回答要简短。"
        # history：多轮对话的原始历史，一条消息一个字典
        self.history = []        # [{'role','content'}]
        # facts_summary：旧历史被压缩后的摘要（为空说明还没触发过压缩）
        self.facts_summary = ""  # 旧历史的压缩摘要

    def _context_messages(self, user_text):
        """拼出本轮真正发给模型的消息列表：system + 摘要 + 历史 + 新问题。"""
        # 固定的系统提示永远排第一
        messages = [{"role": "system", "content": self.system_base}]
        if self.facts_summary:
            # 关键一步：把旧历史的摘要放进 system 消息。
            # system 消息每轮都会发送、且位置靠前权重高，
            # 相当于每轮都帮模型复习一遍旧事实。
            messages.append({
                "role": "system",
                "content": f"此前对话的关键事实（已压缩）：\n{self.facts_summary}"})
        # 保留的最近几轮原文，给模型完整的近期语境
        messages.extend(self.history)
        # 最后附上本轮用户输入
        messages.append({"role": "user", "content": user_text})
        return messages

    def _context_size(self, user_text):
        """把即将发送的所有消息加起来，估一个总 token 数。"""
        total = sum(estimate_tokens(m["content"]) for m in self._context_messages(user_text))
        return total

    def compress_if_needed(self, user_text):
        """预检：若加入新消息会超预算，先压缩旧历史。
        在"发送之前"做预算检查，而不是等 API 报错——
        上下文溢出导致的报错整轮对话就断了。"""
        # 循环压缩直到塞得下（history 空了就停，防止死循环）
        while self._context_size(user_text) > self.budget and len(self.history) > 0:
            before = self._context_size(user_text)
            if len(self.history) <= self.turns_keep:
                # 保留轮数都放不下：硬截断最旧的一条
                # pop(0) 弹出列表第一条 = 最旧的消息
                dropped = self.history.pop(0)
                # 硬截断信息损失大，所以把被丢内容的前 50 字记进摘要留个底
                self.facts_summary += f"\n（已丢弃：{dropped['content'][:50]}...）"
                print(f"[budget] 硬截断最旧一条，当前历史 {len(self.history)} 条")
                continue
            # 正常路径：把最旧的若干轮交给模型压缩
            # 切片：old = 保留区之外的全部旧消息
            old = self.history[:len(self.history) - self.turns_keep]
            self.history = self.history[len(self.history) - self.turns_keep:]
            # 把旧消息拼成一段文字，交给模型提炼要点
            transcript = "\n".join(f"{m['role']}: {m['content']}" for m in old)
            print(f"[budget] 超预算（{before} > {self.budget}），压缩 {len(old)} 条旧消息")
            # 压缩提示词刻意要求"保留人名、数字、结论"——
            # 这些是后续问答最可能被引用的事实
            self.facts_summary = chat([
                {"role": "system", "content":
                    "把下面的对话压缩成不超过100字的要点列表，"
                    "保留人名、数字、结论等事实。只输出要点。"},
                {"role": "user", "content": transcript},
            ], max_tokens=800).strip()

    def reply(self, user_text):
        """处理一轮对话：先做预算检查，再真正调模型，最后把本轮写进历史。"""
        # 发送前先压缩，确保不超预算
        self.compress_if_needed(user_text)
        # 打印本轮上下文规模：让"预算"从抽象概念变成可见的数字
        print(f"[context] 本轮发送上下文 ≈ {self._context_size(user_text)} tokens "
              f"(预算 {self.budget})")
        answer = chat(self._context_messages(user_text))
        # 把本轮的用户输入和模型回答追加进历史，供下一轮使用
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": answer})
        return answer


# ========================= 5. 演示主流程 =========================
# 预设的演示对话：前 5 轮不断提供新事实，把历史越堆越大；
# 第 6 轮突然问最初的事实（服务器编号 WH-01），
# 此时原始历史多半已被压缩，答案必须来自摘要——这就是本案例要验证的点。
# 元组里第二个元素是助教的预设回答（仅作文案展示，主流程实际不用它）。
CONVERSATION = [
    ("我们的课程平台叫 AgentLab，服务器在武汉机房，编号 WH-01。",
     "记住了，AgentLab 在 WH-01。"),
    ("平台有 300 个学生账号，每个账号限 5 个并发会话。",
     "收到：300 账号，并发上限 5。"),
    ("服务器上跑着评估服务，每晚 2 点跑一次全量评估，约 40 分钟。",
     "了解：每晚 2 点全量评估，约 40 分钟。"),
    ("评估用的数据集是课程题库 v7，一共 1200 道题。",
     "好的：题库 v7，1200 题。"),
    ("今年新招了 3 位助教：赵敏、钱峰、孙莉。",
     "收到：3 位新助教。"),
    ("对了，服务器编号是多少来着？", None),   # 关键：靠压缩摘要而不是原始历史记住
]


def main():
    print("=" * 60)
    print("M5 案例：token 预算与历史压缩")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    # 预算故意设得很小（180 tokens）+ 只保留最近 2 轮，
    # 这样演示几轮之内必定触发压缩，方便观察
    agent = BudgetChatAgent(budget_tokens=180, turns_keep=2)
    for user_text, _ in CONVERSATION:
        print(f"\n>>> 用户：{user_text}")
        answer = agent.reply(user_text)
        print(f"<<< 助手：{answer.strip()}")

    # 最后一问靠的是摘要里的 WH-01，而不是原始对话——验证旧事实仍可召回
    print("\n最终压缩摘要（系统提示中携带）：")
    print(agent.facts_summary or "（未触发压缩）")


if __name__ == "__main__":
    main()
