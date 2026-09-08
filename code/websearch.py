# -*- coding: utf-8 -*-
"""
websearch.py —— 联网搜索能力的统一封装
======================================

把"搜索 + 取正文"抽象成两个统一方法，底层 provider 可插拔。
实战篇的联网案例（P1/P2/P3）都通过本模块访问网络，未来加新服务
只需实现一个 Provider 子类并注册，调用方代码零改动。

内置 provider：
  - exa       https://api.exa.ai        （dashboard.exa.ai 拿 key）
  - parallel  https://api.parallel.ai   （platform.parallel.ai 拿 key）

用法（作为模块被 import）：

    from websearch import make_provider
    provider = make_provider()                  # 用顶部配置区的默认 provider
    hits = provider.search("vLLM 怎么部署", num_results=3)
    pages = provider.fetch([h.url for h in hits])

用法（独立自检）：

    python websearch.py "OpenAI 兼容接口的推理框架"
    python websearch.py --provider parallel "vLLM OpenAI compatible"

API key 放哪里：
    优先读同名目录下的 .env 文件（KEY=VALUE 每行一条，见 .env.example），
    其次读环境变量；都没有则报错并提示注册地址。key 属于私密信息，
    请勿写进代码提交到仓库。

如何阅读本文件（给第一次写网络程序的读者）：
  1. 先看「配置区」：API key 和默认用哪家搜索服务，都在这里改。
  2. 再看 WebSearchProvider 类：它定义了 search/fetch 两个统一方法，
     这叫"统一接口"——上层调用方只认这两个方法，根本不知道背后是哪家公司。
  3. 然后看 ExaProvider / ParallelProvider：同一个接口的两家实现，
     都发 HTTP 请求，只是请求地址和返回格式不同。
  4. 最后看「注册表」：@register 装饰器把类登记进一个字典，
     make_provider 按名字从字典里取用——这就是"工厂模式"。
     以后接入新搜索服务，只需写一个新子类并注册，其余代码零改动。
"""

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


# ===================== 0. 加载 .env（私密配置） =====================
def load_dotenv(path=None, override=False):
    """从 .env 文件读取 KEY=VALUE 行，写进环境变量（不覆盖已有值）。

    这是 .env 机制的迷你实现（生产项目常用 python-dotenv 库，原理相同）：
    把私密信息（API key）放在不被 git 提交的 .env 里，代码只写逻辑不写 key。
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行、# 注释、没有 = 的行
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            # 跳过空的值；override=False 时环境变量优先于 .env
            if not value or (not override and os.environ.get(key)):
                continue
            os.environ[key] = value
            count += 1
    return count


load_dotenv()

# ========================= 1. 配置区：只改这里 =========================
# key 优先级：环境变量 > .env 文件 > 空（缺失时调用会报错并提示注册地址）
WEBSEARCH_PROVIDER = os.environ.get("WEBSEARCH_PROVIDER", "parallel")
EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
PARALLEL_API_KEY = os.environ.get("PARALLEL_API_KEY", "")
REQUEST_TIMEOUT = 60   # 秒
# =======================================================================


@dataclass
class SearchHit:
    """一条搜索结果（统一格式，各 provider 共用）"""
    # dataclass 是"自动生成 __init__ 的结构体"：下面写的每个字段名
    # 会自动变成构造参数，如 SearchHit(url="...", title="...")，
    # 不用手写 __init__ 里一堆 self.xxx = xxx。
    # 无论底层是 Exa 还是 Parallel，搜到的结果都装进同一个结构，
    # 上层代码就能用同一套字段处理，这就是"统一格式"的意义。
    url: str
    title: str = ""
    snippet: str = ""
    published: str = ""


@dataclass
class PageContent:
    """一个 URL 的正文提取结果"""
    url: str
    title: str = ""
    text: str = ""


class ProviderError(Exception):
    """provider 调用失败（网络/鉴权/配额等）"""


class WebSearchProvider:
    """所有 provider 的统一接口。子类实现 _search / _fetch 即可接入"""
    # 这是"模板方法"式的基类：search/fetch 负责参数校验这类公共逻辑，
    # 真正"怎么联网"留给子类的 _search/_fetch 实现。
    # 好处：调用方永远只写 provider.search(...) / provider.fetch(...)，
    # 换一家搜索服务（比如从 Exa 换成 Parallel）调用方一行代码都不用改。

    name = "base"
    # 类属性：每个子类用自己的名字覆盖它（如 "exa"、"parallel"），
    # 注册表就是拿这个名字当 key 登记的。

    def search(self, query, num_results=5):
        # type: (str, int) -> list[SearchHit]
        # 公共入口：先校验参数，再交给子类真正联网搜索。
        if not query or not query.strip():
            raise ProviderError("query 不能为空")
        return self._search(query.strip(), num_results)

    def fetch(self, urls, max_chars=2000):
        # type: (list, int) -> list[PageContent]
        # 公共入口：过滤空 URL 后，交给子类去抓取正文。
        urls = [u for u in urls if u]
        if not urls:
            raise ProviderError("urls 不能为空")
        return self._fetch(urls, max_chars)

    def search_and_fetch(self, query, num_results=5, max_chars=2000):
        """最常用组合：搜到 URL 再取正文（Deep Research 的核心动作）"""
        # 先搜索拿 URL 列表，再抓正文；用字典把正文按 URL 对回去，
        # 保证返回的第 i 个正文对应第 i 条搜索结果。
        hits = self.search(query, num_results)
        by_url = {p.url: p for p in self.fetch([h.url for h in hits], max_chars)}
        return hits, [by_url.get(h.url) for h in hits]

    # ---- 通用 HTTP 助手 ----
    def _post(self, endpoint, headers, payload):
        # 所有 provider 的 POST 请求都走这里，把"发请求 + 解析 JSON +
        # 统一报错"封装成一处，子类只需给出地址、请求头和数据。
        request = urllib.request.Request(
            endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            # urlopen 是 Python 标准库发 HTTP 请求的方式（无需 pip 装库）。
            # with 语句保证请求结束后自动关闭连接。
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # HTTPError：服务器"收到了并明确拒绝"——比如 key 错误（401）、
            # 配额用尽（429）、地址写错（404），错误码 e.code 会说明原因。
            detail = e.read().decode("utf-8", "replace")[:300]
            raise ProviderError(f"[{self.name}] HTTP {e.code} {endpoint}: {detail}")
        except urllib.error.URLError as e:
            # URLError：请求根本没到服务器——比如断网、域名解析失败、
            # 服务器没开机。区别于 HTTPError：连 HTTP 状态码都拿不到。
            raise ProviderError(f"[{self.name}] 网络错误: {e.reason}")

    def _require_key(self, key, where):
        # 启动前先检查 key 是否配置，缺 key 时给出明确指引，
        # 而不是等到请求发出去才收到一个含糊的 401。
        if not key:
            raise ProviderError(
                f"[{self.name}] 缺少 API key，请在 {where} 或环境变量中配置")


# ============================ Exa 实现 ============================

class ExaProvider(WebSearchProvider):
    # Exa（api.exa.ai）：语义搜索 API，直接给 query 返回网页，
    # /search 搜、/contents 抓正文，接口简洁，适合当作默认搜索。
    name = "exa"
    BASE = "https://api.exa.ai"   # API 服务器的根地址，后面拼上具体路径

    def __init__(self, api_key=None):
        # 构造时确定用哪个 key：传了参数用参数，否则退回配置区的默认 key。
        self.api_key = api_key or EXA_API_KEY

    def _headers(self):
        # HTTP 请求头：Content-Type 告诉服务器"发的是 JSON"；
        # x-api-key 是 Exa 的认证方式——把 key 放在这个自定义请求头里，
        # 服务器靠它确认"你是谁、有没有权限调用"。
        self._require_key(self.api_key, "环境变量 EXA_API_KEY 或 code/.env 文件"
                          "（注册：https://dashboard.exa.ai）")
        return {"Content-Type": "application/json", "x-api-key": self.api_key}

    def _search(self, query, num_results):
        # 真正联网搜索：POST 到 /search，再把返回的 JSON
        # 逐条"翻译"成统一的 SearchHit 结构。
        data = self._post(self.BASE + "/search", self._headers(),
                          {"query": query, "numResults": num_results})
        hits = []
        for r in data.get("results", []):
            # Exa 返回的字段叫 text/publishedDate，统一格式里叫
            # snippet/published，这里做字段名映射并兜底为空字符串。
            hits.append(SearchHit(
                url=r.get("url", ""), title=r.get("title", "") or "",
                snippet=(r.get("text") or "")[:300],
                published=r.get("publishedDate") or ""))
        return hits

    def _fetch(self, urls, max_chars):
        # 抓正文：把 URL 列表交给 /contents，Exa 会返回每个 URL 的正文，
        # maxCharacters 让服务端先截断，省流量也省 token。
        data = self._post(self.BASE + "/contents", self._headers(),
                          {"ids": list(urls), "text": {"maxCharacters": max_chars}})
        pages = []
        for r in data.get("results", []):
            pages.append(PageContent(
                url=r.get("url", ""), title=r.get("title", "") or "",
                text=r.get("text") or ""))
        return pages


# =========================== Parallel 实现 ===========================

class ParallelProvider(WebSearchProvider):
    """Parallel Web Systems：objective + 关键词组，返回 LLM 优化的摘录"""
    # Parallel（api.parallel.ai）与 Exa 的差异：
    #   - 请求方式不同：Exa 直接给搜索词；Parallel 要求描述"搜索目标
    #     (objective)"，再由它自己去组合关键词（search_queries），
    #     更擅长完成"帮我找到能回答这个目标的内容"这类任务。
    #   - 返回格式不同：Exa 返回网页正文；Parallel 返回为 LLM 优化过的
    #     摘录（excerpts，一段段精选片段），我们拼接后当作正文。
    #   - 有 turbo/fast/advanced 三档速度，按延迟和深度取舍。
    # 但对调用方来说，这些都隐藏在同一个 search/fetch 接口之下——
    # 这正是"统一接口"的价值。
    name = "parallel"
    BASE = "https://api.parallel.ai"

    def __init__(self, api_key=None, mode="fast"):
        self.api_key = api_key or PARALLEL_API_KEY
        self.mode = mode   # turbo(~200ms) / fast(~700ms) / advanced(~3s)

    def _headers(self):
        # 与 Exa 相同：用 x-api-key 请求头携带 API key 做认证。
        self._require_key(self.api_key, "环境变量 PARALLEL_API_KEY 或 code/.env 文件"
                          "（注册：https://platform.parallel.ai）")
        return {"Content-Type": "application/json", "x-api-key": self.api_key}

    @staticmethod
    def _join_excerpts(result):
        # 静态方法：不需要访问 self，纯粹做"把摘录列表拼成一段文字"。
        # "or []" 兜底：字段缺失时按空列表处理，避免 None 报错。
        return "\n".join(result.get("excerpts") or [])

    def _search(self, query, num_results):
        # POST 到 /v1/search：objective 是搜索目标，search_queries
        # 是我们提供的查询词，mode 控制速度档位。
        data = self._post(self.BASE + "/v1/search", self._headers(), {
            "objective": query,
            "search_queries": [query],
            "mode": self.mode,
        })
        hits = []
        # 服务端可能返回多于要求数量的结果，用切片 [:num_results] 截取。
        for r in data.get("results", [])[:num_results]:
            hits.append(SearchHit(
                url=r.get("url", ""), title=r.get("title", "") or "",
                snippet=self._join_excerpts(r)[:300],
                published=r.get("publish_date") or ""))
        return hits

    def _fetch(self, urls, max_chars):
        # POST 到 /v1/extract 抓取正文摘录；Parallel 只能整体返回摘录，
        # 无法像 Exa 那样指定字数，所以在本地按 max_chars 截断。
        data = self._post(self.BASE + "/v1/extract", self._headers(), {
            "urls": list(urls),
        })
        pages = []
        for r in data.get("results", []):
            pages.append(PageContent(
                url=r.get("url", ""), title=r.get("title", "") or "",
                text=self._join_excerpts(r)[:max_chars]))
        return pages


# ====================== 注册表：新服务从这里接入 ======================

# 注册表就是一个字典：{"exa": ExaProvider 类, "parallel": ParallelProvider 类}
# 这叫"工厂模式"的原料——工厂 make_provider 按名字从字典里取出对应的类。
PROVIDERS = {}


def register(cls):
    """装饰器：把 provider 类登记进注册表"""
    # @register 的作用：把类作为值、类名 name 作为 key 存进 PROVIDERS。
    # 装饰器本身只是"登记 + 原样返回类"，不修改类内部任何东西。
    PROVIDERS[cls.name] = cls
    return cls


# 模块被 import 时这段循环就会执行，把两个内置 provider 先登记好。
for _cls in (ExaProvider, ParallelProvider):
    register(_cls)


def make_provider(name=None, **kwargs):
    """工厂：按名字构造 provider，缺省用顶部配置区设置"""
    # 工厂模式：调用方只说"我要 exa/parallel"，不必知道具体类名，
    # 更不必 import 各个类。想换服务只需换名字，调用方代码零改动。
    name = (name or WEBSEARCH_PROVIDER).lower().strip()
    if name not in PROVIDERS:
        raise ProviderError(
            f"未知 provider: {name}（可选: {', '.join(sorted(PROVIDERS))}）")
    # 按名字从注册表取出类，并实例化（**kwargs 透传构造参数）。
    return PROVIDERS[name](**kwargs)


# ============================ 自检入口 ============================

def main(argv):
    # 直接运行本文件时的自检流程：解析命令行 -> 构造 provider ->
    # 实际搜索一次、抓一次正文，验证 key 和网络都正常。
    provider_name = None
    query_parts = []   # 不带 --参数 的词都算查询词的一部分
    i = 0
    # 手写的小型命令行解析（比 argparse 教学上更直白）：
    # --provider 指定搜索服务，--mode 指定 parallel 的速度档。
    while i < len(argv):
        if argv[i] == "--provider":
            provider_name = argv[i + 1]
            i += 2   # 跳过参数名和它的值，两个元素都消费掉了
        elif argv[i] == "--mode":
            # 仅 parallel 有效: turbo / fast / advanced
            # 通过环境变量中转给 provider 构造之后再设置（见下方）。
            os.environ.setdefault("_WS_MODE", argv[i + 1])
            i += 2
        else:
            query_parts.append(argv[i])
            i += 1
    # 没给查询词就用默认示例，保证不带参数直接跑也能自检。
    query = " ".join(query_parts) or "OpenAI 兼容接口的本地大模型推理框架"

    provider = make_provider(provider_name)
    # 只有 ParallelProvider 有 mode 属性，用 hasattr 探测后再覆盖。
    if hasattr(provider, "mode"):
        mode = os.environ.get("_WS_MODE")
        if mode:
            provider.mode = mode

    print(f"provider = {provider.name} | query = {query}\n" + "-" * 60)
    hits = provider.search(query, num_results=3)
    for i, h in enumerate(hits, 1):
        print(f"[{i}] {h.title}")
        print(f"    {h.url}")
    print("\n-- fetch 第 1 条正文 --")
    pages = provider.fetch([hits[0].url], max_chars=300)
    for p in pages:
        print(f"{p.title}\n{(p.text or '(空)').replace(chr(10), ' ')[:250]}...")
    print("\nwebsearch 自检通过 ✓")


if __name__ == "__main__":
    # "__main__" 表示"这个文件被直接运行"（而非被 import），
    # 只有直接运行才走自检；被 P1/P2/P3 import 时不会触发。
    try:
        main(sys.argv[1:])   # sys.argv[1:] 去掉脚本名本身，只留参数
    except ProviderError as e:
        # 自检失败（缺 key、断网等）打印到标准错误流并返回非 0 退出码，
        # 方便脚本化使用时判断成败。
        print(f"失败: {e}", file=sys.stderr)
        sys.exit(1)
