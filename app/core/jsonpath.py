# -*- coding: utf-8 -*-
"""简易 JSONPath 提取（支持 itemArr[0]/[*]）"""

# ---------- 简易 JSONPath（支持 itemArr[0]/[*]） ----------
def jsonpath_get(data, path):
    """提取 JSONPath 值，支持 $.content.itemArr[0].id / [*]"""
    if not path:
        return data
    p = path[2:] if path.startswith("$.") else path
    parts = p.split(".")
    cur = data

    def walk_one(cur, key):
        if key.endswith("]") and "[" in key:
            base, rest = key.split("[", 1)
            idx = rest.rstrip("]")
            if isinstance(cur, dict) and base in cur:
                cur = cur[base]
            if idx == "*":
                return cur if isinstance(cur, list) else None
            if isinstance(cur, list) and idx.isdigit():
                i = int(idx)
                return cur[i] if i < len(cur) else None
            return None
        if isinstance(cur, list):
            # 通配：对每个元素提取并收集
            out = []
            for item in cur:
                v = item.get(key) if isinstance(item, dict) else None
                if v is not None:
                    out.append(v)
            return out if out else None
        return cur.get(key) if isinstance(cur, dict) else None

    for part in parts:
        cur = walk_one(cur, part)
        if cur is None:
            return None
    return cur


