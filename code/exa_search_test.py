# -*- coding: utf-8 -*-
"""
Exa API 连通性测试脚本
======================

Exa 是面向 AI Agent 的搜索 API（https://exa.ai），dashboard.exa.ai 可管理 key。

运行：  python exa_search_test.py

依次测试三个端点：
  1. /search          基础网页搜索
  2. /contents        拉取搜索结果的正文/高亮（Agent 喂上下文用）
  3. /answer          直接返回带引用的答案（RAG 一体化）

如何阅读本文件（零基础读者建议顺序）：
   - 先看 post()：所有请求共用这一个"发 HTTP 请求并解析 JSON"的小函数；
   - 再依次看 test_search / test_contents / test_answer，体会三个端点
     在 Agent 场景里的分工：search 找链接、contents 拿正文、answer 直接给答案；
   - 三个端点层层递进：前一个的输出（URL 列表）会作为后一个的输入。
"""

import json
import os
import urllib.error
import urllib.request


# ========================= 0. 加载 .env（私密配置） =========================
def _load_dotenv(path=None):
    """从同目录 .env 读取 KEY=VALUE 进环境变量（迷你实现，与 websearch.py 相同）。

    key 属于私密信息：放 .env（不提交 git），代码里只写逻辑不写 key。
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not value or os.environ.get(key):
                continue
            os.environ[key] = value
            count += 1
    return count


_load_dotenv()

# ========================= 1. 配置区：只改这里 =========================
EXA_API_KEY = os.environ.get("EXA_API_KEY", "")   # 你的 Exa API Key（环境变量或 .env）
# =======================================================================

if not EXA_API_KEY:
    raise SystemExit("缺少 Exa API key：请在 code/.env 里设置 EXA_API_KEY"
                     "（或环境变量）。注册：https://dashboard.exa.ai")

# 所有请求都发往同一个域名，只是路径不同（/search、/contents、/answer）
BASE = "https://api.exa.ai"
# Exa 用请求头 x-api-key 做身份认证（不是 Bearer token），key 别泄露
HEADERS = {"Content-Type": "application/json", "x-api-key": EXA_API_KEY}


def post(path, payload, timeout=60):
    # 公共请求函数：向 BASE + path 发一个 POST，请求体是 JSON，返回解析好的字典
    request = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode("utf-8"), headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 出错时把服务端返回的错误正文截一小段带出来，方便排查 key 或参数问题
        body = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {e.code} {path}: {body}")


def test_search():
    # 端点 1 /search：基础网页搜索，只返回标题、URL 等元信息，不含正文
    print("--- 测试 1: /search ---")
    data = post("/search", {
        "query": "OpenAI 兼容接口 的本地大模型推理框架",
        "numResults": 3,   # 只要前 3 条结果
    })
    for i, r in enumerate(data.get("results", []), 1):
        print(f"[{i}] {r.get('title')}")
        print(f"    {r.get('url')}")
    print(f"共 {len(data.get('results', []))} 条结果\n")
    # 把前两条 URL 留下来，给下一个端点 /contents 用——演示端点之间的接力
    return [r["url"] for r in data.get("results", [])][:2]


def test_contents(urls):
    # 端点 2 /contents：按 URL 拉取网页正文。Agent 场景里，search 只给链接，
    # 真正要"读"网页内容喂给模型上下文，就得靠这个端点
    print("--- 测试 2: /contents（正文高亮提取）---")
    # ids 传 URL 列表；maxCharacters 限制每篇正文最多取 300 字符
    data = post("/contents", {"ids": urls, "text": {"maxCharacters": 300}})
    for i, c in enumerate(data.get("results", []), 1):
        # 换行压成空格再截断，纯粹为了让终端打印更整齐
        text = (c.get("text") or "").replace("\n", " ")[:150]
        print(f"[{i}] {c.get('title')}")
        print(f"    正文节选: {text}...")
    # API 按用量计费，响应里会带本次调用花了多少钱
    cost = data.get("costDollars", {})
    print(f"（本轮花费: ${cost.get('totalDollars', 0) if isinstance(cost, dict) else cost}）\n")


def test_answer():
    # 端点 3 /answer：搜索 + 阅读网页 + 生成答案一步到位，还附引用来源，
    # 相当于把 RAG 流程封装成了一个 API 调用
    print("--- 测试 3: /answer（带引用的直接回答）---")
    data = post("/answer", {
        "query": "什么是 OpenAI 兼容 API？举两个支持它的服务",
    })
    print(data.get("answer", "")[:500])
    print("\n引用来源：")
    # 引用（citations）标注答案里的信息来自哪些网页，便于核实
    for c in data.get("citations", [])[:5]:
        print(f"  - {c.get('title')}: {c.get('url')}")
    print()


def main():
    # 依次跑三个端点：search 的结果喂给 contents，三个全部通过才算连通
    print(f"Exa API 测试 | key: {EXA_API_KEY[:8]}...{EXA_API_KEY[-4:]}\n")
    try:
        urls = test_search()
        if urls:
            test_contents(urls)
        test_answer()
        print("=" * 50)
        print("全部端点测试通过 ✓")
    except Exception as e:
        # 失败时不让脚本带着堆栈崩溃，而是给出两条最常见的排查方向
        print(f"\n测试失败: {e}")
        print("排查：1) key 是否有效（dashboard.exa.ai 检查）")
        print("      2) 是否有网络/代理问题（需要能访问 api.exa.ai）")


if __name__ == "__main__":
    main()
