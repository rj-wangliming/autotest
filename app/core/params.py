# -*- coding: utf-8 -*-
"""参数解析与配置生成"""
import re


def to_snake(name):
    """参数名统一转 Python 风格（snake_case）：startIp→start_ip、usbTypeIdArr→usb_type_id_arr；
    已是 snake/全小写的原样返回。yaml 因此「一个语义只留一个键」，
    文档里 ${param.startIp} 这类驼峰引用归一后命中同一键"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# ---------- 参数解析 ----------
def _lookup(kind, name, ctx, idx=None):
    """取引用原始值（保留类型）；idx 支持 ${param.x[N]} / ${prev.step.output.y[N]} 显式索引；
    param 值为列表且 ctx 有 _batch_index 时，隐式取当前批量索引（批量展开用）"""
    if kind == "param":
        v = ctx.get("params", {}).get(to_snake(name), "")
        if idx is not None:
            return v[idx] if isinstance(v, list) and idx < len(v) else None
        if isinstance(v, list) and "_batch_index" in ctx:
            i = ctx["_batch_index"]
            return v[i] if i < len(v) else None
        return v
    if kind == "prev":
        # 嵌套 ${prev.<step>.output.<field>}（接口文档 body 标准格式）
        # 兼容单层 ${prev.<field>}（旧格式 / setup 扁平引用）
        if ".output." in name:
            sname, fld = name.split(".output.", 1)
            v = (ctx.get("steps") or {}).get(sname, {}).get(fld, "")
        else:
            v = ctx.get(name, "")
        if idx is not None and isinstance(v, list):
            return v[idx] if idx < len(v) else None
        return v
    if kind == "context":
        return ctx.get("context", {}).get(name, "")
    return None


def resolve_value(val, ctx):
    """解析 ${param.x} / ${prev.y} / ${context.z} / 固定值
    整值引用返回原始类型（数组/数字/布尔）；支持 ${param.x[N]} 索引；
    param 列表在批量上下文（ctx._batch_index）取当前索引"""
    if isinstance(val, str):
        # 整值是单个 ${...}[N]? → 返回原始类型
        m = re.fullmatch(r"\$\{(param|prev|context)\.([\w.]+)(?:\[(\d+)\])?\}", val)
        if m:
            idx = int(m.group(3)) if m.group(3) else None
            return _lookup(m.group(1), m.group(2), ctx, idx)
        # 字符串内插值 → str 替换
        def repl(mm):
            idx = int(mm.group(3)) if mm.group(3) else None
            raw = _lookup(mm.group(1), mm.group(2), ctx, idx)
            return "" if raw is None else str(raw)
        return re.sub(r"\$\{(param|prev|context)\.([\w.]+)(?:\[\d+\])?\}", repl, val)
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
        return ctx["params"].get("system_size", 80)
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


