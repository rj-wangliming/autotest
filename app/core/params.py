# -*- coding: utf-8 -*-
"""参数解析与配置生成"""
import re


# ---------- 参数解析 ----------
def _lookup(kind, name, ctx):
    """取引用原始值（保留类型：数组/数字/布尔），整值引用时直接返回"""
    if kind == "param":
        return ctx.get("params", {}).get(name, "")
    if kind == "prev":
        # 嵌套 ${prev.<step>.output.<field>}（接口文档 body 标准格式）
        # 兼容单层 ${prev.<field>}（旧格式 / setup 扁平引用）
        if ".output." in name:
            sname, fld = name.split(".output.", 1)
            return (ctx.get("steps") or {}).get(sname, {}).get(fld, "")
        return ctx.get(name, "")
    if kind == "context":
        return ctx.get("context", {}).get(name, "")
    return None


def resolve_value(val, ctx):
    """解析 ${param.x} / ${prev.y} / ${context.z} / 固定值
    整值为单个引用时返回原始类型（数组/数字/布尔），字符串内插值则做 str 替换"""
    if isinstance(val, str):
        # 整值是单个 ${...} → 返回原始类型（不 str 化，避免数组/数字变字符串）
        m = re.fullmatch(r"\$\{(param|prev|context)\.([\w.]+)\}", val)
        if m:
            return _lookup(m.group(1), m.group(2), ctx)
        # 字符串内插值 → str 替换
        def repl(mm):
            raw = _lookup(mm.group(1), mm.group(2), ctx)
            return "" if raw is None else str(raw)
        return re.sub(r"\$\{(param|prev|context)\.([\w.]+)\}", repl, val)
    if isinstance(val, dict):
        if "value" in val:
            return resolve_value(val["value"], ctx)
        return {k: resolve_value(v, ctx) for k, v in val.items()}
    if isinstance(val, list):
        return [resolve_value(v, ctx) for v in val]
    return val


def resolve_body(body, ctx):
    if not isinstance(body, dict):
        return body
    out = {}
    for k, v in body.items():
        if isinstance(v, dict) and "value" in v:
            out[k] = resolve_value(v["value"], ctx)
        elif isinstance(v, dict) and v.get("generated_by"):
            out[k] = gen_config_value(k, v, ctx)
        elif isinstance(v, dict) and "type" in v and "value" not in v and not v.get("generated_by"):
            # 纯类型描述（无值）→ 跳过（可选字段）
            continue
        else:
            out[k] = resolve_value(v, ctx)
    return out


def gen_config_value(field, spec, ctx):
    """配置生成规则表：cpu/memory/systemSize 按约束生成"""
    c = str(spec.get("constraint", ""))
    if field == "cpu":
        return ctx["params"].get("cpu", 4)
    if field == "memory":
        return ctx["params"].get("memory", 8192)
    if field == "systemSize":
        return ctx["params"].get("systemSize", 80)
    if field == "platformStrategyGroup":
        # 外设/协议等嵌套：返回最小结构
        return {"strategyGroupFacadeStr": "{}"}
    if field == "deskCreateMode":
        return "NEW"
    if field == "studentModeArr":
        return ["VDI"]  # 学生机类型数组默认
    if field == "desktopNum":
        return 1
    if field == "studentClassroomStrategyId":
        return None  # 依赖前置策略查询（保留 None 由后续步骤填充）
    return None


