# -*- coding: utf-8 -*-
"""接口语义索引模块（方案子文档1）
- 扫描 api_md_staging/*.md，解析 front-matter YAML
- 构建 ApiMetadata Map + 倒排索引 + DAG（setup/upstream/downstream）
- 提供检索：精准查询 / 模糊搜索 / 依赖链展开 / 字段列表
"""
import os
import re
import yaml
import threading

# 接口文档目录：优先环境变量 API_MD_DIR，其次自动探测（工程旁/相对路径）
# 项目根 = app/core/index.py 向上两级（不依赖任何机器绝对路径，便于迁移）
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_CANDIDATES = [
    os.path.join(_PROJ_ROOT, "api_md"),                       # 交付：项目根/api_md（优先）
    os.path.join(_PROJ_ROOT, "docs", "api_md_staging"),       # 开发：项目根/docs/api_md_staging
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_md_staging"),  # 兜底：app/api_md_staging
]

def _resolve_md_dir():
    env = os.environ.get("API_MD_DIR")
    if env and os.path.isdir(env):
        return env
    for cand in _DEFAULT_CANDIDATES:
        if os.path.isdir(cand):
            return cand
    return _DEFAULT_CANDIDATES[0]

API_MD_DIR = _resolve_md_dir()


class ApiIndex:
    """接口语义索引（内存 Map + 倒排索引 + DAG）"""

    def __init__(self, md_dir=None):
        self.md_dir = md_dir or API_MD_DIR
        self.api_map = {}          # url -> metadata dict
        self.inverted = {}         # keyword -> [api_url]
        self.dag = {}              # api_url -> [upstream api_urls]
        self.lock = threading.Lock()
        self._loaded = False

    def load(self, force=False):
        """全量扫描加载（冷启动）"""
        if self._loaded and not force:
            return self.api_map
        with self.lock:
            self.api_map = {}
            self.inverted = {}
            self.dag = {}
            for fname in sorted(os.listdir(self.md_dir)):
                if not fname.endswith(".md"):
                    continue
                if any(k in fname for k in ("README", "code_map", "error_code_map",
                                            "SETUP_PARAM", "用例参数", "外部接口", "修订记录")):
                    continue
                path = os.path.join(self.md_dir, fname)
                try:
                    text = open(path, encoding="utf-8").read()
                    parts = text.split("---\n", 2)
                    if len(parts) < 2:
                        continue
                    fm = yaml.safe_load(parts[1])
                    if not fm or "api" not in fm:
                        continue
                    api = fm.get("api", {})
                    url = api.get("url", "")
                    if not url:
                        continue
                    meta = {
                        "file": fname,
                        "url": url,
                        "method": api.get("method", "POST"),
                        "name": api.get("name", ""),
                        "async": api.get("async", False),
                        "exec_mode": api.get("exec_mode", ""),
                        "description": api.get("description", ""),
                        "request": fm.get("request", {}),
                        "response": fm.get("response", {}),
                        "setup": fm.get("setup", []),
                        "polling": fm.get("polling", {}),
                        "assertions": fm.get("assertions", {}),
                        "cleanup": fm.get("cleanup", []),
                        "params": fm.get("params", {}),
                        "upstream": fm.get("upstream", []),
                        "downstream": fm.get("downstream", []),
                        "idempotency": fm.get("idempotency", {}),
                    }
                    self.api_map[url] = meta
                    # 倒排索引
                    for kw in self._keywords(fm, url):
                        self.inverted.setdefault(kw, [])
                        if url not in self.inverted[kw]:
                            self.inverted[kw].append(url)
                except Exception as e:
                    print(f"[index] 解析失败 {fname}: {e}")
            self._build_dag()
            self._loaded = True
        return self.api_map

    def _keywords(self, fm, url):
        """提取索引关键词：URL 路径段 + api.name + description"""
        kws = set()
        for seg in url.split("/"):
            if seg and not seg.startswith("{"):
                kws.add(seg.lower())
        name = (fm.get("api", {}).get("name") or "")
        for w in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", name):
            kws.add(w.lower())
        return kws

    def _build_dag(self):
        """构建 DAG：setup/upstream 的 API → 本接口"""
        for url, meta in self.api_map.items():
            upstreams = []
            for s in meta.get("setup", []):
                api = s.get("api", "")
                path = api.split(" ", 1)[-1] if " " in api else api
                if path.startswith("/") and path in self.api_map:
                    upstreams.append(path)
            for u in meta.get("upstream", []):
                api = str(u.get("api", ""))
                path = api.split(" ", 1)[-1] if " " in api else api
                if path.startswith("/") and path in self.api_map:
                    upstreams.append(path)
            self.dag[url] = list(dict.fromkeys(upstreams))

    # ---- 检索服务 ----
    def get(self, url):
        return self.api_map.get(url)

    def search(self, keyword, limit=50):
        """模糊语义检索（倒排）"""
        kw = keyword.lower()
        hits = {}
        for k, urls in self.inverted.items():
            if kw in k or k in kw:
                for u in urls:
                    hits[u] = hits.get(u, 0) + 1
        ranked = sorted(hits.items(), key=lambda x: -x[1])
        return [self.api_map[u] for u, _ in ranked[:limit]]

    def all(self):
        return list(self.api_map.values())

    def get_upstream_chain(self, url):
        """依赖链展开（上游链，BFS）"""
        chain = []
        visited = set()
        queue = list(self.dag.get(url, []))
        while queue:
            u = queue.pop(0)
            if u in visited or u == url:
                continue
            visited.add(u)
            chain.append(u)
            queue.extend(self.dag.get(u, []))
        return chain

    def get_downstream(self, url):
        """反向影响分析：谁依赖本接口"""
        return [u for u, ups in self.dag.items() if url in ups]


# 全局单例
_index = ApiIndex()


def get_index():
    return _index
