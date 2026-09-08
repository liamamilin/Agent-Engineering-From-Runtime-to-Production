# -*- coding: utf-8 -*-
"""
M4 完整案例 — Evaluation：评估、追踪与失败分析
===============================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.5:9b-mlx / deepseek-chat

运行：  python M4_eval_trace.py

本案例演示本章核心概念：
  1. 评估 = 在固定数据集上跑 Agent，用确定性检查（rubric）判定通过/失败
  2. 追踪（trace）= 记录每次运行的输入、输出、token、延迟、中间动作
  3. 失败分析：从 trace 里回答"哪条失败、为什么失败、败在哪一层"
  4. 评估结果落盘为 JSON，可对比不同版本的表现（回归测试的雏形）

如何阅读本文件：
  文件按"配置 → 客户端 → 被测系统 → 评估数据集与检查 → 跑评估 → 汇总"
  从上到下排列，建议按编号顺序阅读。第一次读可以只看
  EVAL_CASES（评估用例长什么样）、check_case（怎么判定通过/失败）
  和 run_eval（怎么记录 trace）这三处，其余是支撑代码。
"""

import json
import os
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.5:9b-mlx"              # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
# 这里不装任何第三方库，直接用 Python 标准库 urllib 发 HTTP 请求。
# 大模型 API 本质上就是一个 HTTP 接口：POST 一段 JSON，返回一段 JSON。
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=4000):
    """调用 OpenAI 兼容接口，返回 (回答文本, 用量统计)。
    带指数退避重试：网络抖动是常态，失败后等 1s、2s、4s 再试，
    避免一次偶然超时就让整个评估中断。"""
    # 接口地址拼接 + 把请求参数打包成 JSON 字节串（HTTP 请求体）
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # max_retries + 1 = 最多尝试 4 次（1 次首发 + 3 次重试）
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # usage 里含本次调用消耗的 token 数（见 M5 对 token 的解释）
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                # 2**attempt → 1, 2, 4 秒，间隔越来越长，给服务端喘息时间
                time.sleep(2 ** attempt)
    # 重试用尽仍失败：抛异常，让上层把这次记为"系统层失败"
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


# ========================= 3. 被测系统：一个极简问答助手 =========================
KNOWLEDGE = (
    "产品FAQ：\n"
    "- 学生版价格：每学期 99 元\n"
    "- 退款政策：7 天内无理由全额退款\n"
    "- 客服时间：工作日 9:00-18:00\n"
    "- 支持学校：华中农业大学等 50 所高校\n"
)


def answer(question):
    """被测函数：用内置 FAQ 知识回答问题（以后会换成完整 Agent）。
    评估是围绕"被测系统的接口"展开的：只要输入问题、输出回答，
    内部实现随便换，评估代码不用改。"""
    # system 消息给模型立规矩：只能依据 FAQ 答，没有的就答"不知道"
    messages = [
        {"role": "system", "content": "你是客服助手。只依据下面的FAQ回答，"
                                      "FAQ里没有的信息就回答'不知道'。\n" + KNOWLEDGE},
        {"role": "user", "content": question},
    ]
    text, usage = chat(messages)
    return text, usage


# ========================= 4. 评估数据集与确定性检查 =========================
# 一条评估用例（case）= 一个固定问题 + 判定标准。
# "确定性检查"指用关键词断言来判分：答案里必须出现/不得出现某些词。
# 好处是可复现——同样的答案永远得到同样的判定，
# 不像"再叫一个 LLM 来打分"那样每次结论都可能不同。
# must_contain：回答里必须出现的词；must_not：回答里绝不能出现的词。
EVAL_CASES = [
    {"id": "price",    "question": "学生版多少钱？",
     "must_contain": ["99"], "must_not": ["199", "不知道"]},
    {"id": "refund",   "question": "可以退款吗？",
     "must_contain": ["7"], "must_not": []},
    {"id": "support",  "question": "晚上十点能找客服吗？",
     "must_contain": ["18", "9"], "must_not": []},
    {"id": "school",   "question": "支持哪些学校？",
     "must_contain": ["华中农业大学"], "must_not": []},
    {"id": "unknown",  "question": "你们 CEO 是谁？",
     "must_contain": ["不知道"], "must_not": []},  # 必须拒答，不许编造
    {"id": "infer",    "question": "我和朋友各买一份学生版，一共多少钱？",
     "must_contain": ["198"], "must_not": []},    # 需要 99*2 的推断，小模型常在这里失败
]


def check_case(result, case):
    """确定性检查：不依赖另一个 LLM 来打分，结果可复现。
    就是简单的"子串在不在"判断，执行一百万次结果都一样，
    这是评估可信度的基石。"""
    errors = []   # 收集所有不满足的断言，空列表 = 本用例通过
    # 正向断言：必须包含的关键词，缺一个就记一条错误
    for kw in case["must_contain"]:
        if kw not in result:
            errors.append(f"应包含 {kw!r} 但未找到")
    # 反向断言：禁止出现的内容（比如不许答 199、不许把该答的答成"不知道"）
    for kw in case["must_not"]:
        if kw in result:
            errors.append(f"不应出现 {kw!r} 但出现了")
    return errors


def classify_failure(trace):
    """失败分层归因：先问失败发生在哪一层，再谈怎么修。
    - 系统层：网络/超时/异常，问题出在基础设施 → 查服务、加重试
    - 生成层：模型压根没产出文本 → 查 max_tokens、换模型
    - 内容层：答了但答错 → 查提示词、知识、模型能力
    归因错层会白费力气：内容层的病，加服务器是治不好的。"""
    # runtime_error 非空说明请求本身就没成功，属于基础设施问题
    if trace.get("runtime_error"):
        return "系统层（网络/超时/异常）"
    # 请求成功了但回答是空的：生成环节出了问题
    if trace["answer"] is None or trace["answer"] == "":
        return "生成层（模型没有产出回答，常见于思考型模型被 max_tokens 截断）"
    # 有回答但不满足 rubric：剩下的问题都归为内容层
    return "内容层（回答了，但不满足 rubric）"


# ========================= 5. 运行评估并生成追踪 =========================
def run_eval():
    """逐条跑评估用例，每条记录一份 trace（运行轨迹）。
    trace 落盘 = 把每次调用的输入、输出、token 消耗、耗时等
    原始记录存成 JSON 文件。事后排查"那天为什么错"全靠它，
    而不是靠回忆——这就是可追溯性。"""
    records = []   # 所有用例的 trace 汇总在这里
    for case in EVAL_CASES:
        # 先建一个空 trace 模板：字段齐全，后面逐项填入
        trace = {"id": case["id"], "question": case["question"],
                 "model": LLM_MODEL_ID, "latency_s": 0, "tokens": 0,
                 "answer": None, "errors": [], "runtime_error": None,
                 "attempts": []}
        # 第 1 次尝试：temperature=0（生产默认）
        # temperature=0 表示让模型尽量走"最可能"的输出，减少随机性
        start = time.time()
        try:
            text, usage = chat([
                {"role": "system", "content": "你是客服助手。只依据下面的FAQ回答，"
                                              "FAQ里没有的信息就回答'不知道'。\n" + KNOWLEDGE},
                {"role": "user", "content": case["question"]},
            ])
            trace["answer"] = text
            trace["tokens"] = usage.get("total_tokens", 0)          # 本次调用烧了多少 token
            trace["latency_s"] = round(time.time() - start, 2)      # 本次调用耗时（秒）
            trace["errors"] = check_case(text, case)                # 跑确定性检查
        except Exception as e:
            # 请求层面就崩了：记为系统层错误，继续跑下一条用例
            trace["runtime_error"] = f"运行时异常: {e}"
            trace["errors"] = [trace["runtime_error"]]

        # 失败归因后再决定是否重试：温度抖动可能救回生成层失败
        if trace["errors"]:
            trace["failure_layer"] = classify_failure(trace)
            # 只对生成层（空回答）用高温重试：随机性可能让模型这次正常输出
            if "生成层" in trace["failure_layer"]:
                print(f"[{case['id']}] 空回答，用 temperature=0.7 重试一次...")
                start = time.time()
                text, usage = chat([
                    {"role": "system", "content": "你是客服助手。只依据下面的FAQ回答，"
                                                  "FAQ里没有的信息就回答'不知道'。\n" + KNOWLEDGE},
                    {"role": "user", "content": case["question"]},
                ], temperature=0.7)
                retry_errors = check_case(text, case)
                # 重试的原始记录也塞进 attempts，trace 要保留全过程
                trace["attempts"].append({"temperature": 0.7, "answer": text,
                                          "tokens": usage.get("total_tokens", 0),
                                          "errors": retry_errors})
                if not retry_errors:
                    trace["answer"] = text
                    trace["errors"] = []
                    # 首跑失败、重试通过：标记为不稳定用例（flaky）。
                    # flaky 用例说明行为依赖运气，生产上必须重点盯，
                    # 不能因为"最终通过了"就当作没问题。
                    trace["flaky"] = True  # 首跑失败、重试通过：标记为不稳定用例
        # 最终判定：只要还有 errors 就算失败
        trace["passed"] = not trace["errors"]
        status = "PASS" if trace["passed"] else "FAIL"
        extra = " (重试后通过, flaky)" if trace.get("flaky") else ""
        print(f"[{status}] {case['id']}: {trace.get('errors') or 'ok'}{extra}")
        # 重试路径没走到的失败，在这里补一次归因，保证每条 trace 都有 failure_layer
        if trace["errors"] and not trace.get("failure_layer"):
            trace["failure_layer"] = classify_failure(trace)
        records.append(trace)
    return records


# ========================= 6. 汇总报告与失败分析 =========================
def summarize(records):
    """汇总所有 trace：算通过率、写入 JSON、对失败逐条归因分析。
    这份 JSON 就是"版本对比"的依据：改了提示词后重跑一遍，
    对比两份报告就知道改好了还是改坏了（回归测试的雏形）。"""
    # sum 对布尔值求和 = 统计 True 的个数，即通过的用例数
    passed = sum(r["passed"] for r in records)
    report = {
        "model": LLM_MODEL_ID,
        "total": len(records),
        "passed": passed,
        "pass_rate": f"{passed / len(records):.0%}",
        "cases": records,   # 每条用例的完整 trace 都放进报告
    }
    # 落盘：ensure_ascii=False 让中文原样写入而不是 \u 转义，indent=2 方便人读
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", "eval_trace_M4.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n追踪已写入 {path}")

    print(f"\n通过率: {report['pass_rate']} ({passed}/{len(records)})")
    # 单独把 flaky 用例列出来：它们"碰巧通过"，风险比明确失败更大
    flaky = [r for r in records if r.get("flaky")]
    failures = [r for r in records if not r["passed"]]
    if flaky:
        print("\n不稳定用例（首跑失败、重试才通过，生产上要重点盯）：")
        for r in flaky:
            print(f"- [{r['id']}] {r['question']}")
    if failures:
        # 失败分析按"层"输出：修系统层 / 修生成层 / 修内容层是完全不同的活
        print("\n失败分析（先归因到层，再决定修哪里）：")
        for r in failures:
            print(f"- [{r['id']}] 问题: {r['question']}")
            print(f"  回答: {r['answer']!r}")
            print(f"  归因: {r.get('failure_layer', '内容层')}")
            print(f"  原因: {r['errors']}")
    else:
        print("\n失败分析：全部通过，本轮无需修复。")


# ========================= 7. 演示主流程 =========================
def main():
    # 主流程很短：跑评估 → 汇总报告，复杂逻辑都在前面各节里
    print("=" * 60)
    print("M4 案例：评估、追踪与失败分析")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")
    records = run_eval()
    summarize(records)


if __name__ == "__main__":
    main()
