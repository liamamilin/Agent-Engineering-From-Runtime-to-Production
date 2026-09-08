# -*- coding: utf-8 -*-
"""
M11 完整案例 — Production Delivery：CLI、日志与会话落盘
=========================================================

运行前只需修改下面 3 行配置（任何 OpenAI 兼容 API 都可以）：

    LLM_BASE_URL   例如 http://localhost:11434/v1（Ollama）
                     或 https://api.deepseek.com/v1
    LLM_API_KEY    本地 Ollama 随便填，云端填你的 key
    LLM_MODEL_ID   例如 qwen3.8:27b-mlx

运行：  python M11_cli_agent.py --task "用一句话介绍什么是 Agent" --max-steps 3
        python M11_cli_agent.py --help

本案例演示本章核心概念：
  1. 生产交付的第一形态是 CLI：有 --help、有参数、有退出码
  2. 日志同时进控制台与文件（agent.log），出问题可回放
  3. 会话记录落盘（sessions/*.json）：每次运行可审计、可复现
  4. 失败也有序：异常被捕获、记录日志、以非零退出码结束

如何阅读本文件（写给零基础读者）：
  - 全文按 1~6 分区从上往下读：配置 -> 迷你客户端 -> 日志 -> 会话落盘 -> Agent -> CLI 入口。
  - 这是全书第一个"像正经软件"的命令行程序，新增了几个工程概念：
    * argparse：Python 标准库的命令行参数解析器，让程序能接收 --task 这样的参数，
      并自动生成 --help 帮助信息；
    * logging 双写：日志同时输出到屏幕（StreamHandler）和文件（FileHandler），
      屏幕给人看，文件留下来供事后排查——两边各一份，所以叫"双写"；
    * 会话落盘：每次运行把完整过程存成 sessions/ 下的 JSON 文件，
      相当于"最简版数据库"，让每次运行可审计、可复现；
    * 非零退出码：程序结束时用 sys.exit(0) 表示成功、非 0 表示失败，
      这是所有命令行工具的通用约定，方便脚本和调度系统判断成败。
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request

# ========================= 1. 配置区：只改这里 =========================
LLM_BASE_URL = "http://localhost:11434/v1"   # 你的 API 地址（OpenAI 兼容）
LLM_API_KEY = "ollama"                       # 你的 API Key
LLM_MODEL_ID = "qwen3.8:27b-mlx"             # 你的模型名
# =======================================================================


# ========================= 2. Mini 客户端 =========================
def chat(messages, temperature=0.0, timeout=180, max_tokens=2000):
    """调用大模型的最小客户端（与 M7 相同，但把 usage 完整返回，供会话记录用）。"""
    # OpenAI 兼容接口的固定路径：基础地址 + /chat/completions
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # 请求体：模型名 + 对话历史 + 生成参数，打包成 JSON 字节串
    payload = json.dumps({"model": LLM_MODEL_ID, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": max_tokens}).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LLM_API_KEY}"}
    request = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # 返回 (回复文本, 完整用量字典)：用量会原样写进会话 JSON，方便审计成本
    return (data["choices"][0]["message"]["content"],
            data.get("usage", {}))


# ========================= 3. 日志：控制台 + 文件双写 =========================
def setup_logging(log_file="agent.log"):
    """配置日志系统：同一条日志同时写到文件和控制台。
    - FileHandler：写入 agent.log，程序结束后仍可回放排查；
    - StreamHandler：打到 stdout，运行的人当场就能看到。"""
    logging.basicConfig(
        level=logging.INFO,   # INFO 级别：常规运行信息也记录（DEBUG 更细，此处不需要）
        # 每条日志格式：时间 + 级别 + 内容，便于按时间线定位问题
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])
    # 返回一个带名字的 logger；各模块用同一个名字拿到的就是同一个记录器
    return logging.getLogger("cli_agent")


# ========================= 4. 会话落盘 =========================
def save_session(session):
    """把本次会话（任务、模型、每步结果、状态）存成 JSON 文件。
    为什么落盘？控制台输出转瞬即逝，文件才是可审计、可复现的凭证——
    出了问题能翻出"当时模型到底回了什么"。"""
    # sessions 目录不存在就创建（exist_ok=True：已存在也不报错）
    os.makedirs("sessions", exist_ok=True)
    # 文件名带时间戳，保证每次运行各存一份、互不覆盖
    path = os.path.join("sessions",
                        f"session_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(path, "w", encoding="utf-8") as f:
        # ensure_ascii=False 保留中文可读，indent=2 方便人工打开检查
        json.dump(session, f, ensure_ascii=False, indent=2)
    return path


# ========================= 5. Agent 核心 =========================
def run_task(task, max_steps):
    """执行任务并记录完整会话。返回 (会话字典, 退出码)：0 成功，1 失败。"""
    log = logging.getLogger("cli_agent")
    # 会话字典是本次运行的"档案"：从一开始就记录任务与模型信息
    session = {"task": task, "model": LLM_MODEL_ID, "steps": [],
               "started_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    messages = [
        {"role": "system", "content": "你是命令行里的专业助理，回答准确、简洁。"},
        {"role": "user", "content": task},
    ]
    # 按步数上限循环：真实多步任务每步调用一次模型并推进工作
    for step in range(1, max_steps + 1):
        log.info("step %d/%d 开始调用模型", step, max_steps)
        try:
            answer, usage = chat(messages)
        except Exception as e:
            # 失败也要"有序失败"：先写进日志和会话档案，再以失败状态返回，
            # 而不是让异常把程序炸出一个堆栈
            log.error("模型调用失败: %s", e)
            session["status"] = "error"
            session["error"] = str(e)
            return session, 1  # 非零退出码 = 失败
        log.info("step %d 完成，tokens=%s", step,
                 usage.get("total_tokens", "?"))
        # 每一步的回答和 token 用量都存进会话档案
        session["steps"].append({"step": step, "answer": answer,
                                 "tokens": usage})
        # 本案例单步即可完成；max_steps 为多轮任务预留（与 M3 循环结合）
        break
    # 走到这里说明至少成功执行了一步：标记成功并提取最终答案
    session["status"] = "ok"
    session["answer"] = session["steps"][0]["answer"].strip()
    return session, 0


# ========================= 6. CLI 入口 =========================
def main():
    # argparse：解析命令行参数。运行 python M11_cli_agent.py --help
    # 会自动打印下面每个参数的说明，无需额外写帮助文档
    parser = argparse.ArgumentParser(
        description="CLI 版 Agent：可审计、可复现的生产交付形态")
    parser.add_argument("--task", required=True, help="要完成的任务描述")
    parser.add_argument("--max-steps", type=int, default=3,
                        help="最大步数上限（默认 3）")
    parser.add_argument("--log", default="agent.log", help="日志文件路径")
    # parse_args() 读取真实的命令行参数；--task 缺失时 argparse 会报错并退出
    args = parser.parse_args()

    # 先配置日志再干活，后面的 log.info 才能落到文件里
    setup_logging(args.log)
    log = logging.getLogger("cli_agent")
    # 启动时记录关键配置：将来排查问题先看这条，确认当时用的是哪个模型
    log.info("启动 | model=%s base_url=%s max_steps=%d",
             LLM_MODEL_ID, LLM_BASE_URL, args.max_steps)

    session, exit_code = run_task(args.task, args.max_steps)
    # 无论成败都落盘会话——失败的现场同样是排查问题的宝贵材料
    path = save_session(session)
    log.info("会话已保存: %s", path)

    if exit_code == 0:
        # 成功才把答案打印到屏幕；失败时答案不存在，靠日志和会话文件说明原因
        print("\n=== 结果 ===")
        print(session["answer"])
    # 用 sys.exit 把退出码交还给操作系统：脚本/调度器据此判断本次运行成败
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
