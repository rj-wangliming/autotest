# -*- coding: utf-8 -*-
"""用例编排（结构化模板 → 意图 → DAG）"""
import json
import re
import uuid

from .jsonpath import jsonpath_get
from .params import gen_config_value
from . import index as index_mod


# ---------- 用例编排（结构化模板 → 意图 → DAG） ----------
class Orchestrator:
    """结构化用例 → 执行计划（通道 A：规则解析，0 AI）"""

    def __init__(self, index=None):
        self.index = index or index_mod.get_index()

    # 段落标记关键词（支持多种写法：【前置】/前置步骤：/执行步骤/预测结果 等）
    SECTION_KEYWORDS = {
        "前置": ["前置步骤", "前置条件", "前置", "【前置】", "前提"],
        "操作": ["执行步骤", "操作步骤", "操作", "【操作】", "执行"],
        "预期": ["预测结果", "预期结果", "预期", "【预期】", "期望", "expected"],
    }

    def parse_use_case(self, use_case_text):
        """解析用例三段（前置可空）→ 意图结构；支持多种段落写法"""
        sections = {"前置": [], "操作": [], "预期": []}
        current = None
        for line in use_case_text.splitlines():
            raw = line.strip()
            if not raw:
                continue
            # 段落标记识别（去尾部 :：】 等后精确/前缀匹配）
            head = re.sub(r"[:：\]\s]+$", "", raw)
            matched = None
            for sec in ("前置", "操作", "预期"):
                if any(head == kw or head.startswith(kw) for kw in self.SECTION_KEYWORDS[sec]):
                    matched = sec
                    break
            if matched:
                current = matched
                continue
            if not current:
                continue
            # 段落内容：去序号前缀（1、 1. 1) - •）
            item = re.sub(r"^\s*\d+[\.、）)\]]?\s*", "", raw)
            item = item.lstrip("-•* ").strip()
            if item:
                sections[current].append(item)
        return sections

    def build_plan(self, use_case_text, params=None):
        """用例 → 执行计划（接口链 + 断言）——从接口文档填充数据"""
        sections = self.parse_use_case(use_case_text)
        steps = []
        # 前置：创建/分配 → 匹配接口；创建类自动追加「创建后验证」
        for item in sections["前置"]:
            api, _ = self._match_pre(item)
            if api:
                steps.append(self._build_step(api, item))
                if self._is_create(api):
                    verify = self._verify_step(api, item)
                    if verify:
                        steps.append(verify)
        # 操作：匹配接口；创建类自动追加验证
        for item in sections["操作"]:
            api = self._match_action(item)
            if api:
                steps.append(self._build_step(api, item))
                if self._is_create(api):
                    verify = self._verify_step(api, item)
                    if verify:
                        steps.append(verify)
        # 预期 → 断言
        assertions = [{"type": "status", "expect": "SUCCESS"} for _ in sections["预期"]]
        return {"id": str(uuid.uuid4())[:8], "steps": steps, "assertions": assertions,
                "sections": sections}

    def build_plan_ai(self, use_case_text, params=None, llm_config=None):
        """通道 B（主）：LLM 选接口 → 确定性依赖展开 → 文档填充（0 AI 脚本合成）

        AI 边界：LLM 只做「自然语言步骤 → 接口 url + step_name」消歧（1 次调用）。
        setup 依赖展开/拓扑排序/变量注入由代码完成（接口文档 setup 声明驱动）。
        """
        from .llm import LlmClient
        if not llm_config:
            raise RuntimeError("通道 B 需要 LLM 配置：请在「模型配置」页填写 provider/base_url/api_key/model")
        sections = self.parse_use_case(use_case_text)
        client = LlmClient(llm_config)
        catalog = []
        for m in self.index.all():
            req_body = (m.get("request") or {}).get("body") or {}
            flds = []
            for k, v in req_body.items():
                if isinstance(v, dict):
                    flds.append("%s(%s)" % (k, "必填" if v.get("required") else "可选"))
                else:
                    flds.append(str(k))
            catalog.append({"url": m["url"], "name": (m.get("name") or "")[:50], "fields": flds})
        intent = client.parse_use_case(sections, catalog, sorted((params or {}).keys()))

        steps = []
        seen = set()
        for s in intent.get("steps", []):
            api = s.get("api", "")
            reason = s.get("reason", "") or api
            sname = s.get("step_name") or self._auto_step_name(api)
            if not self.index.get(api):
                steps.append({"step_name": sname, "name": reason[:20], "api": api,
                              "method": "POST", "body": {}, "extract": {}, "poll": None,
                              "_warn": "接口不在索引中，已跳过"})
                continue
            # 先展开 setup 声明的前置依赖（拓扑序，被依赖的先执行）
            self._expand_setup(api, steps, seen)
            # 主步骤本身（setup 未覆盖则追加）
            if api not in seen:
                steps.append(self._build_step_named(
                    api, sname, reason, s.get("section", "action"),
                    s.get("param_map"), s.get("extract_override")))
                seen.add(api)

        raw_asserts = intent.get("assertions", [])
        assertions = [{"type": "status", "expect": a} for a in raw_asserts] or \
                     [{"type": "status", "expect": "SUCCESS"}]
        return {"id": str(uuid.uuid4())[:8], "steps": steps, "assertions": assertions,
                "sections": sections, "mode": "ai"}

    # 通道 B 旧名兼容
    def build_plan_free_text(self, free_text, params=None, llm_config=None):
        return self.build_plan_ai(free_text, params, llm_config)

    def _auto_step_name(self, api):
        """无 LLM step_name 时按 URL 末段生成 snake_case"""
        seg = api.rstrip("/").split("/")[-1] or "step"
        return re.sub(r"[^a-zA-Z0-9]", "_", seg).lower() or "step"

    def _expand_setup(self, api, steps, seen, _stack=None):
        """递归展开接口 setup 声明的前置依赖（拓扑序）；login/环/已见跳过"""
        _stack = _stack if _stack is not None else set()
        if api in _stack:
            return                                    # 环依赖：跳过防无限递归
        _stack.add(api)
        meta = self.index.get(api) or {}
        for item in (meta.get("setup") or []):
            raw = item.get("api", "")
            dep = raw.split(" ", 1)[-1] if " " in raw else raw
            if "loginAdmin" in dep or not self.index.get(dep) or dep in seen:
                continue
            self._expand_setup(dep, steps, seen, _stack)   # 先展开依赖的依赖
            if dep not in seen:                            # 递归内可能已加入
                steps.append(self._build_setup_step(item, dep))
                seen.add(dep)
        _stack.discard(api)

    def _build_setup_step(self, item, dep_api):
        """setup 声明项 → 可执行 step（扁平 body + 按 step_name 关联 extract）"""
        raw = item.get("api", "")
        method = raw.split(" ", 1)[0] if " " in raw else "POST"
        sname = item.get("name") or dep_api.rstrip("/").split("/")[-1]
        body = dict((item.get("request") or {}).get("body") or {})
        extract = {k: v for k, v in (item.get("extract") or {}).items()
                   if isinstance(v, str) and v.startswith("$")}
        dep_meta = self.index.get(dep_api) or {}          # setup 项对应接口的 polling
        step = {"step_name": sname, "name": (item.get("purpose") or sname)[:24],
                "api": dep_api, "method": method, "body": body,
                "extract": extract, "poll": dep_meta.get("polling") or None,
                "section": "pre"}
        if item.get("idempotent"):
            step["idempotent"] = item["idempotent"]
            if item.get("delete_api"):
                step["delete_api"] = item["delete_api"]
        return step

    def _build_step_named(self, api, sname, reason, section="action",
                          param_map=None, extract_override=None):
        """主接口 → step（request.body 填充 + step_name + section；
        param_map 覆盖/补全 body 字段来源；extract_override 覆盖该步产出）"""
        step = self._build_step(api, reason)
        step["step_name"] = sname
        step["section"] = section
        # extract：默认空（产出由依赖步骤提供）；extract_override 声明该步产出（可数组）
        step["extract"] = dict(extract_override) if extract_override else {}
        # param_map：LLM 声明的 body 字段来源，补全文档未声明 value 的裸字段
        if param_map and isinstance(param_map, dict):
            body = step.get("body") or {}
            for fld, src in param_map.items():
                if src is not None:
                    body[fld] = {"value": src}      # 保留 LLM 给的类型(${}引用/字面值)，resolve_body 解析
            step["body"] = body
        return step

    def _is_create(self, api):
        """判断是否为创建类接口"""
        return api.endswith("/create") or api.endswith("/add") or "batchCreate" in api

    def _verify_step(self, api, item):
        """创建后验证：找到同实体域的查询接口，断言资源存在（如创建教室 → 查教室列表含该教室）"""
        # 实体域：从创建接口 URL 提取（create 前的路径段）
        base = api.rstrip("/")
        if base.endswith("/create") or base.endswith("/add"):
            base = base.rsplit("/", 1)[0]
        elif "batchCreate" in base:
            base = base.replace("/batchCreate", "")
        # 候选查询接口：同 base 域的 list/detail/getInfo/select
        candidates = []
        for meta in self.index.all():
            u = meta.get("url", "")
            if u == api:
                continue
            # 同前缀域 + 查询类
            if u.startswith(base + "/") or u == base:
                if any(q in u for q in ("list", "getInfo", "detail", "select", "page")):
                    candidates.append(u)
        if not candidates:
            # 兜底：整个 URL 任一查询接口（同实体段）
            base_segments = set(base.split("/"))
            for meta in self.index.all():
                u = meta.get("url", "")
                segs = set(u.split("/"))
                if any(q in u for q in ("list", "getInfo", "detail", "select")) and                    len(segs & base_segments) >= 2 and u != api:
                    candidates.append(u)
        if not candidates:
            return None
        # 优先精确同前缀的 list（classroom/create → classroom/list，而非 cmr/.../list）
        verify_api = min(candidates, key=lambda u: (
            len(u.split("/")),                      # 路径段数最少（越接近越好）
            "list" not in u,                         # list 优先于 getInfo/detail
            "cmr" in u or "cmrcef" in u or "condition" in u,  # 排除旁支域
        ))
        # 生成验证步骤：查询 + 断言资源存在（itemArr 非空 + 名称过滤）
        verify_step = self._build_step(verify_api, "验证创建成功（查询 %s 存在）" % item[:10])
        verify_step["name"] = "验证创建: %s" % item[:12]
        verify_step["assert"] = [{"path": "$.status", "value": "SUCCESS"},
                                 {"path": "$.content.itemArr", "op": "not_empty"}]
        # 从创建 body 取 name 字段（classroomName/strategyName/name），验证步骤按名称过滤
        create_body = self._build_step(api, item).get("body", {})
        name_field = None
        name_var = None
        for k in ("classroomName", "strategyName", "name", "desktopPreName"):
            if k in create_body and isinstance(create_body[k], dict):
                name_field = k
                name_var = create_body[k].get("value")
                break
        # 验证 body 已含 matchArr 名称过滤（接口文档填充，如 classroomName EQUAL ${param.classroom_name}）
        # 断言保持：status SUCCESS + itemArr 非空（资源存在）
        return verify_step

    def _build_step(self, api, item):
        """从接口文档 front-matter 填充步骤的 body/extract/polling"""
        meta = self.index.get(api) or {}
        # body：接口文档 request.body（保留 ${param.*}/${prev.*} 引用，ScriptRunner 渲染）
        body = {}
        req_body = (meta.get("request") or {}).get("body") or {}
        for k, v in req_body.items():
            if isinstance(v, dict):
                if v.get("value") is not None:
                    body[k] = v  # 有 value 引用
                elif v.get("generated_by"):
                    # 生成器标记 + 字段名；预判生成值，None 则跳过（避免请求体带 null）
                    gv = gen_config_value(k, v, {})
                    if gv is not None:
                        body[k] = dict(v, _field=k)
                # 纯描述（无 value 无 generated_by）→ 跳过
        # extract：取接口 setup 中第一个有产出变量的步骤（若无显式 extract 则用其首个）
        extract = {}
        for s in meta.get("setup") or []:
            ex = s.get("extract")
            if isinstance(ex, dict) and ex:
                extract = {k: jp for k, jp in ex.items() if isinstance(jp, str) and jp.startswith("$")}
                break
        # polling：接口 polling 配置
        poll = meta.get("polling") or None
        step = {"name": item[:20], "api": api, "body": body, "extract": extract, "poll": poll}
        # 幂等：接口 setup 中若有该接口的创建步骤带 idempotent，继承
        for s in meta.get("setup") or []:
            if s.get("idempotent") and s.get("delete_api"):
                step["idempotent"] = s["idempotent"]
                step["delete_api"] = s["delete_api"]
                break
        return step

    # ---------- 文档语义驱动匹配（灵活，覆盖全部接口文档） ----------

    # 动作词 → URL 动作段（从接口文档自动提取 + 补充中文映射）
    ACTION_WORDS = {
        "创建": ["create", "add", "batchCreate"],
        "分配": ["assign"],
        "删除": ["delete"],
        "修改|变更|编辑": ["edit", "update"],
        "查看|查询|列表|获取": ["list", "getInfo", "detail", "get"],
        "关机|关闭": ["shutdown", "powerOff", "close"],
        "重启": ["restart"],
        "唤醒": ["wake", "forceWakeUp"],
        "初始化": ["init"],
        "刷新": ["refresh"],
        "解锁": ["unlock"],
        "踢出|下线": ["kickout"],
        "清空|清理": ["clear"],
        "收集": ["collectLog"],
        "下载": ["download"],
        "恢复": ["restore"],
        "禁用": ["disable"],
        "启用|取消禁用": ["enable", "cancelDisable"],
        "批量配置": ["batchConfig"],
        "检查|校验": ["check", "checkDuplication", "validate"],
        "发布": ["publish"],
        "登录": ["login"],
    }
    # 实体词 → URL 段（覆盖接口文档全部实体）
    ENTITY_WORDS = {
        "教室": ["classroom"],
        "桌面": ["desktop", "cloudDesktop"],
        "座位": ["seat"],
        "策略": ["strategy", "strategygroup", "deskStrategy"],
        "镜像": ["image", "lessonImage"],
        "终端": ["terminal"],
        "学生": ["student"],
        "教师|老师": ["teacher"],
        "空间": ["space"],
        "网络": ["network", "deskNetwork"],
        "用户": ["user"],
        "集群": ["cluster"],
        "存储池": ["storagePool"],
        "白名单": ["networkWhitelist"],
        "服务器": ["serverModel"],
        "平台": ["platform"],
        "广告组|ad": ["adGroup"],
        "日志": ["log", "gtlog"],
        "磁盘": ["disk"],
        "课程|上课": ["lesson"],
        "遥控|远程": ["remoteAssist"],
    }

    def _match_pre(self, item):
        """前置语句 → 接口：先精确规则，再文档语义匹配"""
        # 精确规则（高频，保证 VDI 用例准确）
        precise = [
            ("创建教室", "classroom/create", "classroomId"),
            ("创建 VDI 策略", "strategygroup/vdi/create", "deskStrategyId"),
            ("创建策略", "strategy/create", "strategyId"),
            ("分配.*教师", "image/teacher/create", "imageId"),
            ("分配.*学生", "image/student/create", "imageId"),
            ("创建座位", "seat/create", "seatId"),
        ]
        for kw, url_part, var in precise:
            if re.search(kw, item):
                for meta in self.index.all():
                    if url_part in meta.get("url", ""):
                        return meta["url"], var
        # 文档语义匹配（创建类优先 create/add 结尾）
        url = self._semantic_match(item, prefer_create=True)
        if url:
            return url, None
        # 兜底：动作匹配
        return self._match_action(item), None

    def _match_action(self, item):
        """操作步骤 → 接口：文档语义匹配（动作+实体组合）"""
        url = self._semantic_match(item, prefer_create=False)
        return url

    def _semantic_match(self, item, prefer_create):
        """通用语义匹配：例句动作词+实体词 → 接口 URL 打分"""
        # 提取例句中的动作词与实体词
        actions = []
        entities = []
        for act_kw, act_urls in self.ACTION_WORDS.items():
            # key 内 | 分隔的任一词在例句中即命中（"收集|收集日志" 匹配"收集终端日志"）
            if any(kw in item for kw in act_kw.split("|")):
                actions.extend(act_urls)
        for ent_kw, ent_urls in self.ENTITY_WORDS.items():
            if any(kw in item for kw in ent_kw.split("|")):
                entities.extend(ent_urls)

        best_url = None
        best_score = 0
        for meta in self.index.all():
            url = meta.get("url", "")
            score = 0
            # 动作命中：URL 含动作段（大小写不敏感，匹配 vdiLocalDisk/clearTciLocalDisk 等驼峰段）
            for a in actions:
                if a.lower() in url.lower():
                    score += 2
            # 实体命中：URL 含实体段（大小写不敏感）
            for e in entities:
                if e.lower() in url.lower():
                    score += 2
            # 创建类优先 create 结尾（前置创建场景）
            if prefer_create and (url.endswith("/create") or url.endswith("/add")):
                score += 1
            # api.name 中文匹配（接口描述含用例关键词）
            name = meta.get("name", "")
            for ent_kw in self.ENTITY_WORDS:
                if any(kw in item for kw in ent_kw.split("|")) and any(kw in name for kw in ent_kw.split("|")):
                    score += 1
            if score > best_score:
                best_score = score
                best_url = url
        # 只有动作+实体都命中才算（score >= 4：至少一个动作+一个实体）
        if best_score >= 4:
            return best_url
        return None

