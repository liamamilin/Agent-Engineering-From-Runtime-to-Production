# -*- coding: utf-8 -*-
"""
M10 完整案例 — Guardrails：预算、敏感词与超时的防护层
======================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

运行：  python M10_guardrails.py

本案例演示本章核心概念：
  1. 防护栏在业务逻辑之外：输入过滤 -> 预算检查 -> 调用 -> 输出过滤
  2. token 预算是累计的：不限制就等于无限烧钱，超限必须优雅停止
  3. 敏感词拦截发生在"模型看到之前"和"用户看到之前"两个位置
  4. 超时是资源保护：宁可快速失败，不可无限等待

如何阅读本文件（写给零基础读者）：
  - 全文按 1~5 分区从上往下读：配置 -> 迷你客户端 -> 防护栏类 -> 带护栏的 Agent -> 主流程。
  - "护栏"（Guardrails）是包在 Agent 外面的一层安全检查，和业务逻辑（回答问题）
    完全分开：输入先过滤、预算先检查、再调用模型、最后输出再过滤。
  - token 预算是累计的：每次调用的 token 用量都要累加记账，累计超限就拒绝服务。
    为什么？因为按 token 计费，不限预算 = 不设上限的花钱。
  - 所有拦截和异常都记录进 events 日志：出了问题不能只"悄悄拦下"，
    要留下证据可查（可观察性），上线后排查故障全靠它。
"""

import json
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端（带超时与用量返回） =========================
def chat(messages, temperature=0.0, timeout=60, max_tokens=1500):
    """调用大模型的最小客户端。与 M7 的区别：返回值多带一份 token 用量，
    供护栏记账用；timeout 传给 urlopen，超时直接抛 TimeoutError 快速失败。"""
    # OpenAI 兼容接口的固定路径：基础地址 + /chat/completions
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：模型名 + 对话历史 + 生成参数，打包成 JSON 字节串
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    # timeout 参数是本案例的重点之一：一旦服务端 60 秒没响应就放弃，
    # 而不是让用户一直干等——这就是"资源保护"
    request = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # 返回 (回复文本, 总 token 数) 二元组：total_tokens 是护栏记账的依据
    return (data["choices"][0]["message"]["content"],
            data.get("usage", {}).get("total_tokens", 0))


# ========================= 3. 防护栏实现 =========================
class Guardrails:
    """护栏：一个持有预算、敏感词表和事件日志的对象。
    三道闸门：输入过滤 -> 预算检查 -> 输出过滤，外加调用超时保护。"""

    def __init__(self, total_budget_tokens=2000):
        # 总预算：本进程累计最多消耗这么多 token（生产中按天/按用户计）
        self.budget = total_budget_tokens
        # 已用量：每调用一次模型就累加，是"记账本"
        self.used = 0
        # 敏感词表：命中任何一个词都拦截。真实系统会用更完善的规则/分类器
        self.denylist = ["密码", "身份证号", "转账", "验证码"]
        # 防护栏事件日志：每一次拦截/异常/用量都记一笔。
        # 为什么记日志？因为拦截动作必须可追溯——上线后出了投诉或事故，
        # 要能回答"它当时为什么拒了/放行了哪条输入"，光拦不记等于黑箱
        self.events = []  # 防护栏事件日志：可观察性

    def log(self, event):
        """写一笔事件：既存进内存列表（最后统一打印），也立即打上控制台。"""
        self.events.append(event)
        print(f"[guardrail] {event}")

    def check_input(self, text):
        """输入过滤：在模型看到之前拦截。
        用户想问密码/验证码这类敏感内容时，请求根本不会发给模型，
        既不泄露也不花冤枉钱。"""
        for word in self.denylist:
            if word in text:
                self.log(f"输入拦截：命中敏感词 {word!r}")
                return False
        return True

    def check_budget(self):
        """预算检查：调用前确认还有余量。
        注意是"调用前"检查——一旦超限，后续所有请求都被拒绝，优雅停止。"""
        if self.used >= self.budget:
            self.log(f"预算耗尽（已用 {self.used}/{self.budget} tokens），停止服务")
            return False
        return True

    def record_usage(self, tokens):
        """记账：把本次调用的 token 用量累加进已用总额，并写日志。"""
        self.used += tokens
        self.log(f"用量 {tokens} tokens（累计 {self.used}/{self.budget}）")

    def check_output(self, text):
        """输出过滤：在用户看到之前拦截（防止模型自己说出敏感内容）。
        即使输入是干净的，模型也可能跑题说出不该说的话，所以要双向把关。"""
        for word in self.denylist:
            if word in text:
                self.log(f"输出拦截：回复包含敏感词 {word!r}")
                # 用一句固定提示替代原回复，而不是把敏感回复交给用户
                return "（回复被安全过滤，请换个问法）"
        return text


# ========================= 4. 带防护栏的 Agent =========================
def guarded_agent(guard, question):
    print(f"\n>>> 问题：{question}")

    # 闸门 1：输入过滤
    if not guard.check_input(question):
        return "（输入被安全策略拒绝）"
    # 闸门 2：预算检查
    if not guard.check_budget():
        return "（预算耗尽，本轮服务已停止）"

    # 调用模型（带超时保护）
    try:
        answer, tokens = chat([
            {"role": "system", "content": "你是校园助理，回答不超过 80 字。"},
            {"role": "user", "content": question},
        ], timeout=45)
    except TimeoutError:
        # 超时 = 服务端 45 秒都没响应。快速失败并记录，比让用户无限等好
        guard.log("调用超时（45s），快速失败")
        return "（服务超时，请稍后重试）"
    except Exception as e:
        # 其他异常（断网、接口变更等）也兜住：不能让程序直接崩溃在用户面前
        guard.log(f"调用异常：{e}")
        return "（服务暂时不可用）"

    # 调用成功，把这次消耗的 token 记账（影响后续预算检查）
    guard.record_usage(tokens)
    # 闸门 3：输出过滤
    return guard.check_output(answer.strip())


# ========================= 5. 演示主流程：三个场景 =========================
SCENARIOS = [
    ("敏感词拦截", "帮我看看怎么查自己的登录密码？", None),
    ("正常服务", "图书馆周末几点开门？", None),
    ("预算耗尽", "再帮我总结一下这学期的选课建议。", 0),  # 0=调用前预算已耗尽
]


def main():
    print("=" * 60)
    print("M10 案例：防护栏（预算/敏感词/超时）")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    guard = Guardrails(total_budget_tokens=2000)
    # 场景 1：敏感词 -> 应被输入闸门拦截，不消耗预算
    #（拦截发生在调用模型之前，所以这次是 0 成本的）
    answer = guarded_agent(guard, SCENARIOS[0][1])
    print(f"<<< 答案：{answer}")
    # 场景 2：正常请求 -> 通过三道闸门
    answer = guarded_agent(guard, SCENARIOS[1][1])
    print(f"<<< 答案：{answer}")
    # 场景 3：把预算压到已用值，演示优雅停止
    # guard.budget = guard.used 相当于把额度烧光，下一个请求应被预算闸门拦下
    guard.budget = guard.used
    answer = guarded_agent(guard, SCENARIOS[2][1])
    print(f"<<< 答案：{answer}")

    # 最后统一回放整个事件日志：这三轮里每一次拦截/记账都有据可查
    print("\n防护栏事件日志：")
    for e in guard.events:
        print(f"  - {e}")


if __name__ == "__main__":
    main()
