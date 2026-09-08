# -*- coding: utf-8 -*-
"""
M8 完整案例 — Human in the Loop：计划、审批门与修订
====================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

运行：  python M8_plan_approve.py

本案例演示本章核心概念：
  1. 先规划后执行：高风险任务先产出计划，人审批后再执行
  2. 审批门（approval gate）：每个计划步骤执行前都要过人工确认
  3. 拒绝≠终止：被拒的步骤回到模型修订，修订后再次送审
  4. 演示中用脚本代替真人输入（生产中把 approve() 换成 input() 或审批系统）

如何阅读本文件（写给零基础读者）：
  - 全文按 1~5 分区从上往下读：配置 -> 迷你客户端 -> 审批门 -> 工作流 -> 主流程。
  - 核心流程一句话：先让模型出"计划"，每个步骤执行前都要经过一个"审批门"，
    人批准了才执行；被拒绝的步骤退回模型修改，改完再送审——这就是 HITL
    （Human in the Loop，人在回路中）的落地方式。
  - 为什么需要审批门？因为 Agent 会自己动手做事，如果涉及花钱、发消息、
    删文件等高风险操作，必须有人在执行前把关，防止模型"好心办坏事"。
  - 本文件所有与真人打交道的部分都被简化成固定脚本，方便课堂演示可复现。
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
    """调用大模型的最小客户端（与 M7 相同）：urllib 发 HTTP 请求，失败重试。"""
    # OpenAI 兼容接口的固定路径：基础地址 + /chat/completions
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：模型名 + 完整对话历史 + 生成参数，打包成 JSON 字节串
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    # 请求头：内容类型 + Bearer 鉴权
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    last_error = None
    # 网络调用不可靠，最多重试 max_retries 次；2**attempt 是"指数退避"：
    # 每次失败后等待时间翻倍（1s、2s、4s...），避免把服务端打爆
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            # 打印 token 用量，便于观察每次调用的成本
            print(f"[model] tokens: prompt={usage.get('prompt_tokens', '?')} "
                  f"completion={usage.get('completion_tokens', '?')}")
            # 响应 JSON 层层嵌套，真正的话在 choices[0].message.content
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    # 重试用尽仍未成功，把异常抛给上层处理
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


# ========================= 3. 人工审批门（演示用脚本替代真人） =========================
# 生产中这里是 input("批准该步骤? [y/n] ") 或对接审批系统。
# 演示脚本：第 2 步第一次拒绝（考察修订路径），其余批准。
# SCRIPTED_DECISIONS 是留给真实交互改造的占位：换成 input() 循环即可变成真人审批
SCRIPTED_DECISIONS = []


def approve(step_no, step_text, revision=0):
    """审批门：对每个计划步骤返回 批准(True) 或 拒绝(False)。
    这是整个案例的"安全阀"——任何步骤在过这道门之前都不会被执行。"""
    # 演示设定：第 2 步的初版（revision==0 表示还没修订过）被人为拒绝，
    # 目的是让读者看到"拒绝 -> 修订 -> 再审批"这条路径长什么样
    if revision == 0 and step_no == 2:
        print(f"[审批门] 步骤 {step_no} -> 拒绝（脚本模拟，考察修订路径）")
        return False
    print(f"[审批门] 步骤 {step_no}{'（修订版）' if revision else ''} -> 批准")
    return True


# ========================= 4. 工作流：规划 -> 逐条审批 -> 执行 =========================
def make_plan(task, rejected_step=None, feedback=None):
    """生成计划（或对被拒步骤生成修订）。
    rejected_step / feedback 只在被拒绝后重试时传入，用来告诉模型哪里不行。"""
    # 基础提示词：把任务拆成 3 步，并要求输出 JSON 数组（结构化输出，方便程序处理）
    messages = [
        {"role": "system", "content":
            "你是活动策划助手。把任务拆成 3 个可执行步骤，"
            "输出 JSON 数组，每个元素是一个步骤字符串（不超过40字）。只输出 JSON。"},
        {"role": "user", "content": f"任务：{task}"},
    ]
    # 如果某个步骤被否决，把"第几步 + 否决理由"追加到对话里，
    # 让模型在同一轮上下文中给出修订版，而不是从头再猜
    if rejected_step is not None:
        messages.append({"role": "user", "content":
            f"步骤 {rejected_step + 1} 被否决了，理由：{feedback}。"
            f"请重新输出完整计划（3 步），替换被否决的步骤。只输出 JSON。"})
    # 模型输出可能不合法，最多重试 3 次
    for attempt in range(3):
        try:
            plan = extract_json(chat(messages))
            # 结构校验：必须是列表，且步骤数在 2~5 之间才算合理计划
            if isinstance(plan, list) and 2 <= len(plan) <= 5:
                return [str(s) for s in plan]
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[plan attempt {attempt+1}] 解析失败：{e}")
    # 三次都失败就放弃：宁可明确报错，也不拿一份坏计划往下走
    raise RuntimeError("计划生成失败")


def execute_step(step_no, step_text, task):
    """执行单个步骤：让模型把这一步落实成具体产出。
    注意：能走到这里，说明该步骤已经通过了审批门。"""
    # 把"总任务 + 当前步骤"都给模型，让它知道自己做的是全局中的哪一环
    output = chat([
        {"role": "system", "content":
            "你在协助完成一个任务。请把下面的步骤落实成具体产出（一段可直接使用的文字，"
            "不超过120字），不要复述步骤本身。"},
        {"role": "user", "content": f"总任务：{task}\n当前步骤：{step_text}"},
    ])
    print(f"[执行] 步骤 {step_no} 产出：{output.strip()[:100]}...")
    return output


def run_workflow(task):
    """完整工作流：规划 -> 每步过审批门 -> 批准才执行 -> 汇总。"""
    print(f"[规划] 为任务生成计划：{task}")
    # 第一步永远是先有计划，而不是直接开干
    plan = make_plan(task)
    for i, step in enumerate(plan):
        print(f"  计划步骤 {i+1}: {step}")

    results = []
    # enumerate(plan) 同时给出下标 i 和步骤内容 step
    for i, step in enumerate(plan):
        # --- 审批门：先过人，再执行 ---
        # revision 记录当前步骤被修订了几次
        revision = 0
        # while 循环：只要审批不通过，就不断修订、再送审
        while not approve(i + 1, step, revision):
            revision += 1
            if revision > 2:
                # 安全上限：修订两次仍被拒就跳过，防止无限循环
                print(f"[审批门] 步骤 {i+1} 两次修订仍被拒，跳过该步骤")
                break
            # 把被拒步骤连同理由发回模型，取回修订后的第 i 步
            plan = make_plan(task, rejected_step=i,
                             feedback="太笼统/不切实际，请更具体")
            step = plan[i]
            print(f"[修订] 步骤 {i+1} 修订为：{step}")
        else:
            # Python 特有的 while...else：while 没被 break（即最终批准）才执行这里，
            # 也就是说"执行"严格发生在"审批通过"之后
            results.append(execute_step(i + 1, step, task))

    print(f"\n[汇总] {len(results)} 个步骤执行完成")
    return results


# ========================= 5. 演示主流程 =========================
def main():
    print("=" * 60)
    print("M8 案例：计划、审批门与修订")
    print("=" * 60)
    print(f"模型: {LLM_MODEL_ID} @ {LLM_BASE_URL}\n")

    task = "为 90 分钟的班级技术分享会做筹备"
    # 跑一遍完整工作流，观察步骤 2 走"拒绝 -> 修订 -> 再审批"的路径
    run_workflow(task)
    print("\n要点：步骤 2 走了 拒绝->修订->再审批 路径；"
          "所有执行都发生在审批通过之后。")


if __name__ == "__main__":
    main()
