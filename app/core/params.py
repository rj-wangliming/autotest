# -*- coding: utf-8 -*-
"""参数解析与配置生成"""
import random
import re
import string


def to_snake(name):
    """参数名统一转 Python 风格（snake_case）：startIp→start_ip、usbTypeIdArr→usb_type_id_arr；
    已是 snake/全小写的原样返回。yaml 因此「一个语义只留一个键」，
    文档里 ${param.startIp} 这类驼峰引用归一后命中同一键"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _random_prefix():
    """随机桌面名前缀：字母开头、5 位小写字母数字（服务端限制 1-5 字符）"""
    return "vd" + "".join(random.choices(string.ascii_lowercase + string.digits, k=3))


def materialize_naming(params, log=None):
    """命名参数物化（原地改 params），规则：
    - desktop_pre_name 为空 → 随机生成前缀；
    - desktop_name 按 seat_num 补齐：已填的保留（多座位只填一个时其余按命名规则 pre+序号 生成），
      完整列表存 desktop_name_arr，desktop_name 保留第一个（兼容标量消费方）；
    - desktop_name_start_num 为空默认 1；desktop_name 带尾数字时从中推导前缀和起始值；
    - computer_name 为空 → 用前缀（LIKE 前缀匹配命中全部桌面）。
    """
    log = log or (lambda level, msg: None)

    def to_int(v, d):
        try:
            return int(v)
        except (TypeError, ValueError):
            return d

    n = to_int(params.get("seat_num"), 1)
    pre = (params.get("desktop_pre_name") or "").strip()
    start = to_int(params.get("desktop_name_start_num"), 0)

    # 确保非数组参数是标量（从全局 params YAML 中列表转为字符串）
    for k in ("classroom_name", "image_name", "student_image_name",
              "teacher_mode", "student_start_ip", "student_end_ip"):
        v = params.get(k)
        if isinstance(v, list) and v:
            params[k] = v[0]

    raw = params.get("desktop_name")
    names = [] if raw in (None, "") else (
        [raw] if isinstance(raw, str) else [x for x in raw if x])

    # 前缀/起始值没填时，从已填名字推导（尾数字解析：vditest1 → vditest + 1）
    if names and (not pre or not start):
        m = re.match(r"^([A-Za-z][A-Za-z0-9]*?)(\d+)$", names[0])
        if m:
            pre = pre or m.group(1)
            start = start or int(m.group(2))
    if not pre:
        pre = _random_prefix()
        log("info", "[params] desktop_pre_name 未填，随机生成前缀: %s" % pre)
    if not start:
        start = 1

    while len(names) < n:
        names.append("%s%d" % (pre, start + len(names)))
    if len(names) > 1:
        log("info", "[params] seat_num=%s，desktop_name 补齐 %d 个: %s"
            % (params.get("seat_num"), len(names), names))

    params["desktop_pre_name"] = pre
    params["desktop_name_start_num"] = start
    params["desktop_name"] = names[0]
    params["desktop_name_arr"] = names
    if not (params.get("computer_name") or "").strip():
        params["computer_name"] = pre
        log("info", "[params] computer_name 未填，用前缀做 LIKE 匹配: %s" % pre)


# ---------- 参数解析 ----------
def _note_ref_fallback(ctx, ref, step_name, field):
    """记录 ${prev.*} 模糊回退命中（executor 汇入 result.warnings）"""
    if isinstance(ctx, dict):
        ctx.setdefault("_ref_warnings", []).append(
            "引用 %s 未精确命中，模糊回退到步骤 %s 的产出 %s" % (ref, step_name, field))


def _lookup(kind, name, ctx, idx=None):
    """取引用原始值（保留类型）；idx 支持 ${param.x[N]} / ${prev.step.output.y[N]} 显式索引；
    param 值为列表且 ctx 有 _batch_index 时，隐式取当前批量索引（批量展开用）"""
    if kind == "param":
        v = ctx.get("params", {}).get(to_snake(name), None)
        if idx is not None:
            return v[idx] if isinstance(v, list) and idx < len(v) else None
        if isinstance(v, list) and "_batch_index" in ctx:
            i = ctx["_batch_index"]
            return v[i] if i < len(v) else None
        # 非批量上下文：值为列表时自动取首元素
        if isinstance(v, list):
            return v[0] if v else v
        return v
    if kind == "prev":
        # 嵌套 ${prev.<step>.output.<field>}（接口文档 body 标准格式）
        # 兼容单层 ${prev.<field>}（旧格式 / setup 扁平引用）
        if ".output." in name:
            sname, fld = name.split(".output.", 1)
            v = (ctx.get("steps") or {}).get(sname, {}).get(fld, "")
            # 模糊回退：sname 不存在时，查找所有步骤中产出该 field 的步骤
            # 注意：产出 key 可能因命名规范化使用下划线（如 classroom_id vs classroomId）
            # 回退属兜底路径（编排期 _link_prev_refs 已应改写正确步骤名），
            # 命中时记录告警，由 executor 汇入 result.warnings，不再静默
            if v == "" and fld in ("classroomId",):
                for sn, bucket in (ctx.get("steps") or {}).items():
                    if fld in bucket:
                        v = bucket[fld]
                        _note_ref_fallback(ctx, name, sn, fld)
                        break
                    # 不区分大小写 + 下划线匹配
                    for bk in bucket:
                        if bk.lower().replace("_", "") == fld.lower().replace("_", ""):
                            v = bucket[bk]
                            _note_ref_fallback(ctx, name, sn, bk)
                            break
                    if v != "":
                        break
        else:
            v = ctx.get(name, "")
        if idx is not None and isinstance(v, list):
            return v[idx] if idx < len(v) else None
        # 批量上下文：prev 值为列表时取当前批量索引
        if isinstance(v, list) and "_batch_index" in ctx:
            i = ctx["_batch_index"]
            return v[i] if i < len(v) else None
        # 非批量上下文：prev 值为列表时自动取首元素（跨步骤引用场景）
        if isinstance(v, list):
            return v[0] if v else v
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
            raw = _lookup(m.group(1), m.group(2), ctx, idx)
            # 解析结果为空字符串 → 返回 None（调用方可跳过该字段）
            if raw == "":
                return None
            return raw
        # 字符串内插值 → str 替换
        def repl(mm):
            idx = int(mm.group(3)) if mm.group(3) else None
            raw = _lookup(mm.group(1), mm.group(2), ctx, idx)
            return "" if raw is None else str(raw)
        result = re.sub(r"\$\{(param|prev|context)\.([\w.]+)(?:\[\d+\])?\}", repl, val)
        # 如果结果是空字符串 → 返回 None
        if result == "":
            return None
        return result
    if isinstance(val, dict):
        # 仅字段描述符（含 type）折叠取 value；
        # 业务对象自带的 value 字段（如 matchArr 的 Match.value）须保留结构
        if "value" in val and "type" in val:
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
            result = resolve_value(v["value"], ctx)
            # 值为 None 或空字符串时表示参数缺失；若为 Boolean 类型则用默认值 True
            if result is None or result == "":
                field_type = v.get("type", "")
                if "Boolean" in str(field_type) or "boolean" in str(field_type):
                    result = True
                else:
                    continue
            # 先清理 None（含空列表变 None）
            result = _clean_none(result)
            # 特殊处理：matchArr/exactMatchArr 中的元素若无 valueArr（参数未提供），跳过整个字段
            if k in ("matchArr", "exactMatchArr") and isinstance(result, list):
                result = [elem for elem in result if isinstance(elem, dict) and elem.get("valueArr") is not None]
                if not result:
                    continue
            out[k] = result
        elif isinstance(v, dict) and v.get("generated_by"):
            out[k] = gen_config_value(k, v, ctx)
        elif isinstance(v, dict) and "type" in v and "value" not in v and not v.get("generated_by"):
            # 纯类型描述（无值）→ 若 required 则赋默认值，否则跳过
            if v.get("required"):
                _type = v.get("type", "")
                _constraint = v.get("constraint", "") or ""
                # 优先从 constraint 中提取默认值（如 "@Range(1-1000) 默认20" → 20）
                import re as _re
                _dm = _re.search(r"默认(\d+)", _constraint)
                if _dm:
                    default_val = int(_dm.group(1))
                elif "limit" == k:
                    default_val = 1000
                elif "page" == k:
                    default_val = 0
                elif "Integer" in _type or "Long" in _type or "Double" in _type:
                    default_val = 0
                elif "String" in _type:
                    default_val = ""
                elif "Boolean" in _type or "boolean" in _type:
                    default_val = False
                else:
                    default_val = None
                if _type and "Integer" in _type:
                    # Integer 默认最小为 1（除非 constraint 指定了范围下限）
                    _rng = _re.search(r"@Range\(\d+", _constraint)
                    if _rng:
                        pass  # 用 constraint 中的范围
                    elif default_val is not None and default_val == 0:
                        default_val = 1 if k != "page" else 0
                out[k] = default_val
            else:
                continue
        else:
            out[k] = resolve_value(v, ctx)
    # 最终清理：递归移除所有 None 值
    return _clean_none(out)


def _clean_none(obj):
    """递归清理 None 值：None → 被移除/替换为默认；空列表/空字典 → 视为无效返回 None"""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if v is None:
                continue
            cv = _clean_none(v)
            if cv is not None:
                cleaned[k] = cv
        # 空字典视为无效（无意义的空 body 段）
        return cleaned if cleaned else None
    if isinstance(obj, list):
        cleaned = [_clean_none(item) for item in obj]
        cleaned = [c for c in cleaned if c is not None]
        # 空列表视为无效（如 matchArr.valueArr: [] 应跳过）
        return cleaned if cleaned else None
    return obj


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
    if field == "enableHide":
        return False
    if field == "studentModeArr":
        return ["VDI"]  # 学生机类型数组默认
    if field == "enableTeacher":
        return True   # 教师机默认 true
    if field == "desktopNum":
        return 1
    if field == "studentClassroomStrategyId":
        return None  # 依赖前置策略查询（保留 None 由后续步骤填充）
    # 分页参数默认值（查询类接口安全默认，不涉业务语义）
    if field == "page":
        return 0
    if field == "limit":
        return 20
    if field == "rows":
        return 20
    if field == "sort":
        return ""
    if field == "sortArr":
        return []
    return None


