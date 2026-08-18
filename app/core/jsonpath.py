# -*- coding: utf-8 -*-
"""简易 JSONPath 提取（支持 itemArr[0]/[*]）"""


def jsonpath_get(data, path):
    """提取 JSONPath 值，支持 $.content.itemArr[0].id / $.content.itemArr[*].id"""
    if not path:
        return data
    p = path[2:] if path.startswith("$.") else path
    parts = p.split(".")
    cur = data

    def walk_one(cur, key):
        # 处理键名中的索引或通配符，如 itemArr[0]、itemArr[*]
        if "[" in key:
            base, rest = key.split("[", 1)
            idx = rest.rstrip("]")
            if isinstance(cur, dict) and base in cur:
                cur = cur[base]
            if idx == "*":
                # 通配符：cur 应为列表，直接返回
                return cur if isinstance(cur, list) else None
            if isinstance(cur, list) and idx.isdigit():
                i = int(idx)
                return cur[i] if i < len(cur) else None
            return None

        # 通配：cur 是列表时，遍历每个元素提取 key
        if isinstance(cur, list):
            out = []
            for item in cur:
                if isinstance(item, dict):
                    v = item.get(key)
                    if v is not None:
                        out.append(v)
            return out if out else None

        if isinstance(cur, dict):
            return cur.get(key)
        return None

    for part in parts:
        cur = walk_one(cur, part)
        if cur is None:
            return None
    return cur
