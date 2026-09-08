# -*- coding: utf-8 -*-
"""
M9 完整案例 — Multi-Agent：委派、子 Agent 与结果综合
=====================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

运行：  python M9_delegation.py

本案例演示本章核心概念：
  1. 主 Agent 负责拆解与综合，子 Agent 负责专项工作（职责分离）
  2. 每个子 Agent 有独立的系统提示与专长，互不共享上下文——
     传递给它们的只有任务描述，这正是"委派"的含义
  3. 拆解是结构化输出：主 Agent 输出子任务 JSON，解析失败要重试
  4. 子 Agent 结果回到主 Agent 综合成最终结论，附上"谁贡献了什么"

如何阅读本文件（写给零基础读者）：
  - 全文按 1~5 分区从上往下读：配置 -> 迷你客户端 -> 子 Agent 定义 -> 主 Agent -> 主流程。
  - "多 Agent"听起来复杂，本质是分工：主 Agent 像项目经理，只做三件事——
    把大任务拆成小任务、把小任务交给合适的专家（委派）、把专家的产出拼成最终答案（综合）。
  - 关键概念"上下文隔离"：子 Agent 每次只收到自己的任务描述，看不到主 Agent 的
    完整对话，也看不到其他子 Agent 说了什么。好处是每个子 Agent 提示词短、
    注意力集中、不会被无关信息干扰；代价是信息要靠任务描述显式传递。
  - 每个"Agent"在这里就是"一段系统提示 + 一次模型调用"，没有更神秘的东西。
"""

import json
import re
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
def chat(messages, temperature=0.0, max_retries=3, timeout=180, max_tokens=2000):
    """调用大模型的最小客户端（与 M7 相同）：urllib 发请求 + 失败重试。"""
    # OpenAI 兼容接口的固定路径：基础地址 + /chat/completions
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：模型名 + 对话历史 + 生成参数，打包成 JSON 字节串
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    # 请求头：内容类型 + Bearer 鉴权
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # 网络不可靠，重试 max_retries 次；2**attempt 是指数退避（1s、2s、4s...）
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            # 打印 token 用量：多 Agent 会多次调用模型，成本更要盯紧
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败（已重试 {max_retries} 次）：{last_error}")


def extract_json(text):
    """从模型回复里解析 JSON：先试整体解析，再试 ```json 代码块。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 模型常把 JSON 包在 Markdown 代码块里，用正则抠出中间部分
    match = re.search(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"回复中找不到合法 JSON：{text[:120]!r}...")


# ========================= 3. 子 Agent 定义 =========================
# 每个"子 Agent"就是一段专属系统提示：key 是主 Agent 指派时用的代号，
# "system" 是它的人设/专长。子 Agent 互相不知道对方存在（上下文隔离）。
SUB_AGENTS = {
    "analyst": {
        "name": "需求分析师",
        "system": "你是需求分析师，站在教学效果角度分析问题，"
                  "回答不超过 100 字，给出 2-3 条要点。",
    },
    "cost": {
        "name": "成本评估师",
        "system": "你是成本评估师，站在工程与维护成本角度分析问题，"
                  "回答不超过 100 字，给出 2-3 条要点。",
    },
}


def delegate_to(name, task):
    """委派：把任务交给指定子 Agent。子 Agent 看不到主 Agent 的上下文。
    注意这里 messages 只有两条：子 Agent 的专属系统提示 + 任务描述本身，
    没有任何主 Agent 的对话历史——这就是"上下文隔离"的实现方式。"""
    # 用 key 从花名册里取出这个子 Agent 的名字和系统提示
    agent = SUB_AGENTS[name]
    print(f"[委派] -> {agent['name']}：{task[:50]}...")
    output = chat([
        {"role": "system", "content": agent["system"]},
        {"role": "user", "content": task},
    ])
    print(f"[返回] <- {agent['name']} 完成")
    # 返回"谁 + 干了什么 + 干出了什么"，主 Agent 综合时要靠这份记录
    return {"agent": agent["name"], "task": task, "output": output.strip()}


# ========================= 4. 主 Agent：拆解 -> 委派 -> 综合 =========================
def split_task(main_task, max_attempts=3):
    """主 Agent 把任务拆成指派给子 Agent 的子任务（结构化输出）。
    拆解也是一次模型调用：让主 Agent 读任务和"专家花名册"，输出指派方案。"""
    # 把子 Agent 花名册拼成清单文本，塞进提示词，主 Agent 才知道有哪些专家可用
    roster = "\n".join(f"- {key}: {a['name']}" for key, a in SUB_AGENTS.items())
    messages = [
        {"role": "system", "content":
            "你是主 Agent。把用户任务拆成 2 个子任务，分别委派给这些专家：\n"
            f"{roster}\n"
            '输出 JSON：[{"agent": "专家key", "task": "给该专家的任务描述"}]，'
            "任务描述不超过 60 字。只输出 JSON。"},
        {"role": "user", "content": main_task},
    ]
    # 结构化输出可能失败（不是 JSON、指派了不存在的专家），最多重试 3 次
    for attempt in range(1, max_attempts + 1):
        try:
            subtasks = extract_json(chat(messages))
            # 校验：每一项得是字典，且 agent 字段必须是花名册里真实存在的 key，
            # 防止模型编造出一个不存在的专家
            valid = [s for s in subtasks
                     if isinstance(s, dict) and s.get("agent") in SUB_AGENTS]
            if len(valid) >= 2:
                return valid[:2]
            raise ValueError(f"有效子任务不足 2 个：{subtasks}")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[split attempt {attempt}] 解析失败：{e}")
    raise RuntimeError("任务拆解失败")


def run_main_agent(main_task):
    """主 Agent 的完整一轮：拆解 -> 逐个委派 -> 汇总综合。
    注意主 Agent 自己不分析问题，它只做组织协调工作。"""
    print(f"[主 Agent] 接到任务：{main_task}")
    # 第一步：拆解
    subtasks = split_task(main_task)
    results = []
    # 第二步：委派——按拆解结果逐个调用子 Agent，收集它们各自的产出
    for s in subtasks:
        results.append(delegate_to(s["agent"], s["task"]))

    # 把所有子 Agent 报告拼成一段文本，标明每段是谁写的、任务是啥
    contributions = "\n\n".join(
        f"【{r['agent']}】（任务：{r['task']}）\n{r['output']}" for r in results)
    # 第三步：综合——主 Agent 再调一次模型，把子报告熔成最终结论
    final = chat([
        {"role": "system", "content":
            "你是主 Agent。综合子 Agent 的报告给出最终建议，"
            "格式：结论一句话 + 理由 3 条以内，不超过 150 字。"},
        {"role": "user", "content": f"主任务：{main_task}\n\n子 Agent 报告：\n{contributions}"},
    ])
    print(f"\n[综合] 主 Agent 最终结论：\n{final.strip()}")
    return results, final


# ========================= 5. 演示主流程 =========================
def main():
    print("=" * 60)
    print("M9 案例：多 Agent 委派与综合")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    task = ("我们课程平台（300 名学生、每晚跑全量评估）在考虑是否引入"
            "LLM 自动批改主观题的功能，请分析该不该做。")
    # 一个"该不该做"的决策题，正好需要效果、成本两个视角 -> 两个子 Agent
    run_main_agent(task)
    print("\n要点：主 Agent 没有亲自回答，它只做了拆解、委派、综合三件事；"
          "子 Agent 之间互不知晓对方的存在。")


if __name__ == "__main__":
    main()
