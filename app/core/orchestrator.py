# -*- coding: utf-8 -*-
"""用例编排（结构化模板 → 意图 → DAG）"""
import json
import re
import uuid

import yaml

from .jsonpath import jsonpath_get
from .params import gen_config_value
from . import index as index_mod


# ---------- 用例编排（结构化模板 → 意图 → DAG） ----------
class Orchestrator:
    """结构化用例 → 执行计划（通道 A：规则解析，0 AI）"""

    def __init__(self, index=None):
        self.index = index or index_mod.get_index()
        if not self.index.api_map:
            self.index.load()
        self.rules = self._load_rules()

    def log(self, level, msg):
        """编排期日志（LOCK 字段处理等 debug 输出；编排无执行器回调，打印 stdout）"""
        print("[%s] %s" % (level, msg), flush=True)

    # ---------- 业务规则库加载（business_rules.md） ----------
    def _load_rules(self):
        """加载业务规则库 front-matter（依赖链/操作前置状态/用例前置条件）"""
        import os
        rules = {}
        for cand in (index_mod.API_MD_DIR,
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "api_md_staging")):
            p = os.path.join(cand, "business_rules.md")
            if os.path.isfile(p):
                try:
                    text = open(p, encoding="utf-8").read()
                    fm = yaml.safe_load(text.split("---\n", 2)[1])
                    if isinstance(fm, dict):
                        rules = {k: v for k, v in fm.items()
                                 if k in ("resource_chains", "state_prereq", "case_prereq",
                                          "semantic_rules", "auto_provision", "param_ref_rules")}
                    break
                except Exception as e:
                    print(f"[orchestrator] business_rules.md 解析失败: {e}")
        return rules

    @staticmethod
    def _norm(api):
        """去掉方法前缀：'POST /rcc/x' -> '/rcc/x'"""
        if not api:
            return api
        for m in ("POST", "GET", "PUT", "DELETE", "PATCH"):
            if api.startswith(m + " "):
                return api[len(m) + 1:]
        return api

    def _find_state_prereq(self, api):
        """查操作接口的 state_prereq 规则（模式匹配：URL 含 resource 段 + action 段即命中）"""
        api = self._norm(api)
        if not api:
            return None
        api_l = api.lower()
        for sp in self.rules.get("state_prereq", []) or []:
            # 规则声明 api 精确路径 → 优先精确匹配（避免子路径误匹配，如 classroom/delete vs image/student/delete）
            if sp.get("api"):
                if api == sp["api"]:
                    return sp
                continue
            res = str(sp.get("resource", "") or "").lower()
            act = str(sp.get("action", "") or "").lower()
            if not res or not act:
                continue
            # resource 段匹配（desktop 兼容 desktop/cloudDesktop；strategy 兼容 strategy/strategygroup）
            if sp.get("resource_optional"):
                res_ok = True  # 动作词特异（如 forcewakeup），URL 无需含 resource 段
            elif res == "desktop":
                res_ok = "desktop" in api_l or "clouddesktop" in api_l
            elif res == "strategy":
                res_ok = "strategy" in api_l or "strategygroup" in api_l or "deskstrategy" in api_l
            else:
                res_ok = res in api_l
            # action 段匹配（词边界，避免 restart 误匹配 start 子串；支持下划线分段如 lesson_start）
            if "_" in act:
                act_ok = all(re.search(r"\b" + re.escape(seg) + r"\b", api_l) for seg in act.split("_"))
            else:
                act_ok = re.search(r"\b" + re.escape(act) + r"\b", api_l) is not None
            if res_ok and act_ok:
                return sp
        return None

    def validate_plan(self, plan):
        """编排后校验（规则库驱动，确定性逻辑，非 AI）：
        1. 前置状态校验：操作步骤命中 state_prereq 且缺达成步骤 → 自动补 achieve_via 步骤
        2. 依赖顺序修正：资源依赖链接口若逆序 → 按链顺序重排
        返回修正后的 plan（自动补的步骤标记 _auto_by_rules，可人工确认）
        """
        steps = plan.get("steps", [])
        added = []

        # 0. 资源依赖链自动补：操作步骤的资源在 resource_chains 中，且 plan 无该链任何造数接口
        #    → 在操作步骤前补完整造数链（如：教室 → 座位 → 分配镜像）
        steps = self._ensure_resource_chain(steps, added)

        # 1. 前置状态校验 + 补步骤
        i = 0
        while i < len(steps):
            st = steps[i]
            api = st.get("api", "")
            rule = self._find_state_prereq(api)
            if not rule:
                i += 1
                continue
            achieve_apis = {self._norm(a.get("api", "")) for a in (rule.get("achieve_via") or [])}
            has_achieve = any(self._norm(s.get("api", "")) in achieve_apis for s in steps)
            if has_achieve:
                i += 1
                continue
            # 补第一条达成途径（须为索引内真实 HTTP 接口）
            for a in (rule.get("achieve_via") or []):
                a_api = self._norm(a.get("api", ""))
                if not self.index.get(a_api):
                    continue
                step = self._build_step(a_api, a.get("note", "") or ("达成前置状态: " + rule.get("required_state", "")))
                step["step_name"] = "rule_auto_" + a_api.rstrip("/").rsplit("/", 1)[-1]
                step["name"] = "规则自动补: " + (a.get("note", "") or rule.get("required_state", ""))[:30]
                step["section"] = "pre"
                step["_auto_by_rules"] = True
                steps.insert(i, step)
                added.append(step["step_name"])
                i += 1
                break
            i += 1

        # 2. 用例前置条件校验（case_prereq）：前置文本命中 keyword → 检查/补达成步骤
        steps = self._ensure_case_prereq(steps, plan, added)

        # 2b. 禁止状态校验（forbidden）：命中规则的步骤若 plan 已有达成 forbidden 状态的步骤 → 警告
        warns = self._check_forbidden(steps)

        # 3. 依赖顺序修正（资源依赖链）
        steps = self._fix_chain_order(steps)

        # 3b. 查询产物后置（desktop/list 等查询移到资源链完成后）
        steps = self._fix_query_after_chain(steps)

        # 4. 引用链接：${prev.*} 统一改写到 plan 内真实步骤名（缺省 step_name 补齐），
        #    断裂引用在编排期暴露（warns），不再依赖执行期模糊回退静默兜底
        self._link_prev_refs(steps, warns)

        # 5. param_ref_rules 确定性消费：扫描 body 中引用不存在 param 的字段，
        #    命中规则的 target_fields 就按 source_param 改写，覆盖 setup 步骤
        self._apply_param_ref_rules(steps, warns)

        plan["steps"] = steps
        plan["rule_added"] = added
        if warns:
            plan["warns"] = warns
        return plan

    def _link_prev_refs(self, steps, warns):
        """plan 期引用链接（确定性，非 AI）：
        1. 所有步骤补齐确定 step_name（缺省按 URL 末段生成，执行期产出桶键不再漂移）
        2. ${prev.X.output.Y} 的 X 不在 plan 步骤名中 / 平铺 ${prev.Y} 有产出者
           → 改写为「最近的、产出 Y 的前序步骤」标准三段式，warns 记录改写
        3. 无产出者的三段式引用 → warns 记录 ref_unresolved（执行期将解析为空）
        改写后执行期 _lookup 精确命中，params 模糊回退仅作最后兜底（会告警）

        _locked 字段：value 含 # LOCK 标记的 body 字段跳过引用改写（由文档 value 严格锁定）"""
        used = set()
        for st in steps:
            if not st.get("step_name"):
                st["step_name"] = self._auto_step_name(st.get("api", ""))
            base = st["step_name"]
            if base in used:  # URL 末段生成的默认名可能撞名（产出桶键冲突）→ 追加序号
                i = 2
                while "%s_%d" % (base, i) in used:
                    i += 1
                st["step_name"] = "%s_%d" % (base, i)
            used.add(st["step_name"])
        producers = {}      # 产出变量名 -> 最近产出步骤名（按 plan 顺序向后推进）
        norm_producers = {}  # 归一键（小写去下划线）-> 步骤名（classroomId ≈ classroom_id）

        def norm(s):
            return str(s).lower().replace("_", "")

        for st in steps:
            sname = st.get("step_name") or ""
            if isinstance(st.get("body"), dict):
                st["body"] = self._rewrite_body_refs(
                    st["body"], used, producers, norm_producers, sname, warns)
            for var in (st.get("extract") or {}):
                if isinstance(var, str):
                    producers[var] = sname
                    norm_producers[norm(var)] = sname

    def _rewrite_body_refs(self, obj, names, producers, norm_producers, sname, warns, _skip_key=None):
        """递归改写 body 中的 ${prev.*} 引用（见 _link_prev_refs）
        _skip_key: 若不为 None，该 key 对应的 dict 值含 _locked 标记，跳过改写"""
        if isinstance(obj, str):
            def repl(m):
                ref, idx = m.group(1), m.group(2) or ""
                if ".output." in ref:
                    target, fld = ref.split(".output.", 1)
                    if target in names:
                        return m.group(0)
                    p = producers.get(fld) or norm_producers.get(fld.lower().replace("_", ""))
                    if p:
                        warns.append({"code": "ref_rewritten", "step": sname, "ref": ref,
                                      "to": "%s.output.%s" % (p, fld),
                                      "hint": "引用步骤 %s 不在 plan 中，已改写为产出 %s 的步骤 %s" % (target, fld, p)})
                        return "${prev.%s.output.%s%s}" % (p, fld, idx)
                    warns.append({"code": "ref_unresolved", "step": sname, "ref": ref,
                                  "hint": "引用 %s 无产出步骤，执行期将解析为空" % ref})
                    return m.group(0)
                # 平铺 ${prev.Y}：有产出者 → 升格标准三段式；无产出者保留（执行期 ctx 顶层查找，兼容 token 等）
                p = producers.get(ref) or norm_producers.get(ref.lower().replace("_", ""))
                if p:
                    return "${prev.%s.output.%s%s}" % (p, ref, idx)
                return m.group(0)
            return re.sub(r"\$\{prev\.([\w.]+?)(?:\[(\d+)\])?\}", repl, obj)
        if isinstance(obj, dict):
            # 跳过 _locked 标记的字段（value 含 # LOCK 标记，由文档 value 严格锁定）
            if obj.get("_locked"):
                return obj
            return {k: self._rewrite_body_refs(v, names, producers, norm_producers, sname, warns,
                                               _skip_key=k) if isinstance(v, dict) and v.get("_locked")
                    else self._rewrite_body_refs(v, names, producers, norm_producers, sname, warns)
                    for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._rewrite_body_refs(v, names, producers, norm_producers, sname, warns)
                    for v in obj]
        return obj

    def _ensure_case_prereq(self, steps, plan, added):
        """用例前置条件达成：前置文本命中 case_prereq.keyword → 若 plan 无达成步骤则自动补
        （如前置"运行中"→ 补上课开机；前置"已分配"→ 补分配学生机镜像）"""
        sections = plan.get("sections") or {}
        for item in sections.get("前置", []) or []:
            for cp in self.rules.get("case_prereq", []) or []:
                kw = cp.get("keyword")
                if not kw or kw not in item:
                    continue
                achieve_apis = {self._norm(a.get("api", "")) for a in (cp.get("achieve_via") or [])}
                has = any(self._norm(s.get("api", "")) in achieve_apis for s in steps)
                if has:
                    continue
                # 补第一条达成途径，插到首个 action 步骤前（无 action 则追加到末尾）
                for a in (cp.get("achieve_via") or []):
                    a_api = self._norm(a.get("api", ""))
                    if not self.index.get(a_api):
                        continue
                    step = self._build_step(a_api, a.get("note", "") or ("达成前置条件: " + cp.get("required_state", "")))
                    step["step_name"] = "rule_case_" + a_api.rstrip("/").rsplit("/", 1)[-1]
                    step["name"] = "规则补前置: " + (a.get("note", "") or cp.get("required_state", ""))[:30]
                    step["section"] = "pre"
                    step["_auto_by_rules"] = True
                    action_idx = next((i for i, s in enumerate(steps) if s.get("section") == "action"), len(steps))
                    steps.insert(action_idx, step)
                    added.append(step["step_name"])
                    break
        return steps

    def _check_forbidden(self, steps):
        """禁止状态校验：仅当 plan 中存在「另一步骤的 required_state 命中本步骤 forbidden」的真实冲突时警告"""
        warns = []
        # 收集每个步骤的资源+要求状态
        step_states = []  # (api, resource, required_state)
        for st in steps:
            api = self._norm(st.get("api", ""))
            rule = self._find_state_prereq(api)
            if rule and rule.get("required_state"):
                step_states.append((api, rule.get("resource"), rule.get("required_state")))
        for st in steps:
            api = self._norm(st.get("api", ""))
            rule = self._find_state_prereq(api)
            if not rule or not rule.get("forbidden"):
                continue
            res = rule.get("resource")
            forb = rule.get("forbidden")
            # 真实冲突：另一步骤要求的状态 ∈ 本步骤 forbidden（如 lesson_end 要求 IN_CLASS 与 lesson_start 禁止 IN_CLASS）
            for other_api, other_res, other_state in step_states:
                if other_api == api or other_res != res:
                    continue
                if other_state in forb:
                    warns.append({"api": api, "forbidden_state": other_state,
                                  "conflict_with": other_api,
                                  "hint": "%s 禁止 %s 状态，但步骤 %s 要求 %s，请确认执行顺序" % (api, other_state, other_api, other_state)})
        return warns

    def _ensure_resource_chain(self, steps, added):
        """资源依赖链自动补：操作步骤的资源在 resource_chains 中，且 plan 无该链任何造数接口
        → 在操作步骤前补完整造数链（create → seat → 分配镜像），解决"有桌面可操作但没造桌面"的通用缺口"""
        chains = self.rules.get("resource_chains", {}) or {}
        if not chains:
            return steps
        result = steps[:]
        for st in list(result):
            api = self._norm(st.get("api", ""))
            if not api or not self.index.get(api):
                continue
            # 仅对命中 state_prereq 的操作步骤补造数链（查询类/无状态前置的操作不造数）
            rule = self._find_state_prereq(api)
            if not rule:
                continue
            # 规则显式 chain: false（如上课/下课是状态达成步骤，非消耗资源的操作）→ 不补链
            if rule.get("chain") is False:
                continue
            api_l = api.lower()
            # 操作对象含 desktop/cloudDesktop → 只匹配 desktop 类链（避免教室链连带分配教师镜像）
            if "clouddesktop" in api_l or "desktop" in api_l:
                relevant = {k: v for k, v in chains.items() if "desktop" in k}
            else:
                relevant = chains
            for res, chain in relevant.items():
                order = [self._norm(u) for u in (chain.get("order") or [])]
                if not order:
                    continue
                # 资源段匹配（vdi_desktop 要求 desktop 且非 tci；tci_desktop 要求 tci/lessonimage）
                res_l = str(res).lower()
                if "tci" in res_l:
                    res_ok = "tci" in api_l or "lessonimage" in api_l or "spacetci" in api_l
                elif "desktop" in res_l:
                    res_ok = ("desktop" in api_l or "clouddesktop" in api_l) and "tci" not in api_l
                else:
                    res_ok = res_l in api_l
                if not res_ok:
                    continue
                # 链本身的造数接口不触发
                if api in order:
                    break
                # 逐接口检查链完整性：补缺失的链接口（如已有 create/seat 但缺 image → 只补 image）
                plan_chain = [self._norm(s.get("api", "")) for s in result]
                missing = [u for u in order if self._norm(u) not in plan_chain]
                if not missing:
                    break
                # 补缺失链接口：先展开【操作接口自身】的文档 setup（含 create_seat/分配镜像/query_desktop 等完整声明），
                # 再对链中仍缺失的接口补其 setup + 主接口（文档 setup 优先，规则库兜底）
                new_steps = []
                seen = {self._norm(s.get("api", "")) for s in result if s.get("api")}
                self._expand_setup(api, new_steps, seen)      # 展开操作接口自身 setup
                for u in missing:
                    if self._norm(u) in seen:                 # setup 已声明该接口则跳过
                        continue
                    if not self.index.get(u):
                        continue
                    self._expand_setup(u, new_steps, seen)   # 展开缺失链接口的 setup 依赖
                    if self._norm(u) in seen:                 # _expand_setup 不加入接口本身
                        continue
                    step = self._build_step(u, "规则补链造数: %s" % u)
                    segs = u.strip("/").rsplit("/", 2)[-2:]
                    step["step_name"] = "chain_" + "_".join(segs)
                    step["section"] = "pre"
                    step["_auto_by_rules"] = True
                    new_steps.append(step)
                    seen.add(self._norm(u))
                for s in new_steps:
                    s["_auto_by_rules"] = True
                    s["name"] = "规则补链: " + (s.get("name") or s.get("step_name") or "")[:40]
                    if s.get("step_name") and s["step_name"] not in added:
                        added.append(s["step_name"])
                if new_steps:
                    idx = result.index(st)
                    result[idx:idx] = new_steps
                break
        return result

    def _fix_query_after_chain(self, steps):
        """查询产物后置：查询某资源产物的步骤（如 desktop/list 查运行中桌面）应在其资源链完成后执行，
        否则在造座位/分配镜像之前查询会落空（LLM 常把查询步骤排在造数链中间/前）"""
        chains = self.rules.get("resource_chains", {}) or {}
        if not chains:
            return steps
        result = steps[:]
        # 所有链资源段的 (资源名, 段词) 表（用于识别查询对象）
        res_seg_map = {}
        for rr, cc in chains.items():
            rl = str(rr).lower()
            if "tci" in rl:
                res_seg_map[rl] = ("tci", "lessonimage", "spacetci")
            elif "desktop" in rl:
                res_seg_map[rl] = ("desktop", "clouddesktop")
            elif "image" in rl:
                res_seg_map[rl] = ("image", "lessonimage", "spacetci")
            else:
                res_seg_map[rl] = (rl,)
        for res, chain in chains.items():
            # 查询后置只对桌面类链生效（desktop/list 查运行中桌面必须在座位+镜像后）;
            # 其他链的查询由 _expand_setup 拓扑序保证，无需移动（避免索引错乱波及依赖步骤）
            if "desktop" not in str(res).lower():
                continue
            order = [self._norm(u) for u in (chain.get("order") or [])]
            if not order:
                continue
            res_l = str(res).lower()
            # 链最后接口位置（该资源数据就绪点）
            last_pos = -1
            for i, st in enumerate(result):
                if self._norm(st.get("api", "")) in order:
                    last_pos = i
            if last_pos < 0:
                continue
            # 收集需要后移的查询步骤（静态判断，避免 pop/insert 快照索引错乱）
            to_move = []
            for st in result:
                api = self._norm(st.get("api", ""))
                api_l = api.lower()
                if api in order:
                    continue
                # 查询对象 = list 前紧邻路径段含的资源词（desktop/list → desktop；deskNetwork/list → 无链词不动；
                # assignImage/yetAssign/list → 无链词不动；避免前缀段误伤）
                seg_before = ""
                for marker in ("/list", "/getinfo", "/detail", "/select"):
                    if marker in api_l:
                        seg_before = api_l.rsplit(marker, 1)[0].rsplit("/", 1)[-1]
                        break
                if not seg_before:
                    continue
                obj_res = None
                for rr, segs in res_seg_map.items():
                    if any(seg in seg_before for seg in segs):
                        obj_res = rr
                        break
                if obj_res != res:
                    continue
                # 查询步骤在链完成后？是则不动；否则后移到链最后接口之后
                if result.index(st) <= last_pos:
                    to_move.append(st)
            if not to_move:
                continue
            for st in to_move:
                result.remove(st)
            # 重新定位链最后接口（移除后索引变化），统一插入其后
            last_pos = max(i for i, s in enumerate(result) if self._norm(s.get("api", "")) in order)
            result[last_pos + 1:last_pos + 1] = to_move
        return result

    def _fix_chain_order(self, steps):
        """资源依赖链顺序修正：链中接口若逆序出现 → 按链顺序重排（保持其他步骤相对位置）"""
        chains = self.rules.get("resource_chains", {}) or {}
        if not chains:
            return steps
        for chain in chains.values():
            order = [self._norm(u) for u in (chain.get("order") or [])]
            if not order:
                continue
            hits = []  # (链内序号, plan 内位置)
            for i, st in enumerate(steps):
                u = self._norm(st.get("api", ""))
                if u in order:
                    hits.append((order.index(u), i))
            if len(hits) < 2:
                continue
            order_seq = [oi for oi, _ in hits]       # 链内序号序列（应递增 = 链顺序正确）
            if order_seq != sorted(order_seq):
                # 逆序 → 按链顺序重排命中的步骤，移到最前命中位置
                ordered_steps = [steps[pos] for _, pos in sorted(hits)]
                first_pos = min(pos for _, pos in hits)
                for pos in sorted((p for _, p in hits), reverse=True):
                    del steps[pos]
                steps[first_pos:first_pos] = ordered_steps
        return steps

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
            if not api:
                continue
            # 状态声明句（"...处于运行中/存在/已分配..."且匹配到查询类接口）→ 不作为造数步骤，
            # 前置状态由 business_rules case_prereq + validate_plan 校验达成
            if self._is_state_declaration(item, api):
                continue
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
        plan = {"id": str(uuid.uuid4())[:8], "steps": steps, "assertions": assertions,
                "sections": sections}
        return self.validate_plan(plan)

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
            produce = self._collect_produce(m)
            catalog.append({"url": m["url"], "name": (m.get("name") or "")[:50],
                            "fields": flds, "produce": produce})

        # 生成 auto_provision + param_ref_rules 规则摘要（传给 LLM 理解）
        rules_text = self._build_auto_provision_rules_text()
        param_ref_text = self._build_param_ref_rules_text()
        if param_ref_text:
            rules_text = rules_text + "\n\n" + param_ref_text if rules_text else param_ref_text

        intent = client.parse_use_case(sections, catalog, sorted((params or {}).keys()), rules_text=rules_text)

        # 自动补充策略创建步骤（auto_provision 规则）
        # 在 LLM 编排后检查：即使用例文本中提到了"获取 VDI/TCI/教室策略"，
        # LLM 也可能漏编出查询步骤。我们基于用户用例文本 + 全局参数来检测并注入。
        intent = self._apply_auto_provision(intent, sections, params or {})

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
        plan = {"id": str(uuid.uuid4())[:8], "steps": steps, "assertions": assertions,
                "sections": sections, "mode": "ai"}
        return self.validate_plan(plan)

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
            # dep in _stack：自引用 setup 项（被测接口声明自身以携带幂等信息），
            # 不作为独立步骤注入，避免消费方流程被依赖文档的自我声明覆盖
            if ("loginAdmin" in dep or not self.index.get(dep)
                    or dep in seen or dep in _stack):
                continue
            self._expand_setup(dep, steps, seen, _stack)   # 先展开依赖的依赖
            if dep not in seen:                            # 递归内可能已加入
                steps.append(self._build_setup_step(item, dep))
                seen.add(dep)
        _stack.discard(api)

    def _build_setup_step(self, item, dep_api):
        """setup 声明项 → 可执行 step（从接口文档填充 body + 按 step_name 关联 extract）"""
        raw = item.get("api", "")
        method = raw.split(" ", 1)[0] if " " in raw else "POST"
        sname = item.get("name") or dep_api.rstrip("/").split("/")[-1]
        # 从接口文档填充 body（包含必填字段），setup 项的 body 作为覆盖/补充
        base_step = self._build_step(dep_api, item.get("purpose") or sname)
        body = base_step.get("body") or {}
        # setup 项声明的 body 覆盖文档默认值
        setup_body = dict((item.get("request") or {}).get("body") or {})
        for k, v in setup_body.items():
            if isinstance(v, dict):
                body[k] = v
            else:
                # 裸值（如 ${param.xxx}）→ 包装为 {value: ...}
                body[k] = {"value": v}
        ex_raw = item.get("extract") or {}
        if isinstance(ex_raw, list):
            # SETUP_PARAM_SPEC §2.2：list 格式（多 extract / assert）
            # 每项 {var, from, jsonpath}，产出 var -> jsonpath
            extract = {}
            for it in ex_raw:
                if isinstance(it, dict) and it.get("var") and it.get("jsonpath"):
                    extract[it["var"]] = it["jsonpath"]
        elif isinstance(ex_raw, dict):
            extract = {k: v for k, v in ex_raw.items()
                       if (isinstance(v, str) and v.startswith("$")) or isinstance(v, dict)}
        else:
            extract = {}
        dep_meta = self.index.get(dep_api) or {}          # setup 项对应接口的 polling
        dep_poll = dep_meta.get("polling") or None
        if isinstance(dep_poll, dict) and dep_poll.get("api") and not str(dep_poll["api"]).startswith("/"):
            resolved = self.index.resolve(dep_poll["api"])
            if resolved:
                dep_poll = dict(dep_poll, api=resolved)
        step = {"step_name": sname, "name": (item.get("purpose") or sname)[:24],
                "api": dep_api, "method": method, "body": body,
                "extract": extract, "poll": dep_poll,
                "section": "pre"}
        if base_step.get("fill"):
            step["fill"] = base_step["fill"]
        if item.get("idempotent"):
            step["idempotent"] = item["idempotent"]
            if item.get("delete_api"):
                step["delete_api"] = item["delete_api"]
            if item.get("reuse_query"):
                step["reuse_query"] = item["reuse_query"]
        return step

    def _is_state_declaration(self, item, api):
        """判断前置句是否为「状态声明」（含状态词且匹配到查询类接口）：
        状态声明不作为造数步骤，其状态达成由 business_rules case_prereq + validate_plan 校验"""
        state_words = ("运行中", "处于", "存在", "已分配", "可用", "关机", "在线", "离线", "已创建", "启动")
        if not any(w in item for w in state_words):
            return False
        # 匹配到的是查询类接口（list/getInfo/detail/get/select）→ 判定为状态声明
        api_l = self._norm(api).lower()
        return any(q in api_l for q in ("/list", "/getinfo", "/detail", "/get", "/select", "page"))

    def _build_step_named(self, api, sname, reason, section="action",
                          param_map=None, extract_override=None):
        """主接口 → step（request.body 填充 + step_name + section；
        param_map 覆盖/补全 body 字段来源；extract_override 覆盖该步产出）"""
        step = self._build_step(api, reason)
        step["step_name"] = sname
        step["section"] = section
        # extract：默认空（产出由依赖步骤提供）；extract_override 声明该步产出（可数组）
        step["extract"] = dict(extract_override) if extract_override else {}
        # param_map：LLM 声明的 body 字段来源，仅在文档未声明 value 时补充（不覆盖文档已有 value）
        # _locked 字段：value 含 # LOCK 标记，禁止 param_map 覆盖
        if param_map and isinstance(param_map, dict):
            body = step.get("body") or {}
            for fld, src in param_map.items():
                if src is not None and fld not in body:
                    body[fld] = {"value": src}      # 保留 LLM 给的类型(${}引用/字面值)，resolve_body 解析
                elif src is not None and fld in body:
                    fld_spec = body[fld]
                    if fld_spec.get("_locked"):
                        self.log("debug", f"[orchestrator] param_map 跳过 LOCK 字段 {fld}: src={src}")
                    else:
                        self.log("debug", f"[orchestrator] param_map 跳过覆盖 {fld}（文档已有 value）: src={src}")
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
                    val_str = str(v.get("value", ""))
                    # 检查 LOCK 标记：value 中包含 # LOCK 时，标记该字段为锁定（不可被 param_map/LLM 覆盖）
                    is_locked = "# LOCK" in val_str or "#锁定" in val_str
                    if is_locked:
                        # 清理注释前缀，保留纯引用
                        clean_val = val_str.split("#")[0].strip()
                        body[k] = dict(v, value=clean_val, _locked=True)
                        self.log("debug", f"[orchestrator] value LOCK 标记 {k}: {clean_val}")
                    else:
                        body[k] = v
                elif v.get("generated_by"):
                    # 生成器标记 + 字段名；预判生成值，None 则跳过（避免请求体带 null）
                    gv = gen_config_value(k, v, {"params": {}})
                    if gv is not None:
                        body[k] = dict(v, _field=k)
                else:
                    # 裸字段（无 value/generated_by）：按字段名推断 value 引用
                    inferred = self._infer_body_value(k, v, meta)
                    if inferred == "generated":
                        gv = gen_config_value(k, v, {"params": {}})
                        if gv is not None:
                            body[k] = dict(v, _field=k)  # 生成字段走 generated 逻辑
                    elif inferred is not None:
                        body[k] = dict(v, value=inferred)
                # 纯描述（无 value 无 generated_by 且无法推断）→ 跳过
            # 兜底：必填字段若未被包含且有 value 声明，强制加入（防止 YAML 解析异常导致丢失）
            if isinstance(v, dict) and v.get("required") and k not in body and v.get("value") is not None:
                body[k] = v
        # extract：优先接口【自身】setup 声明的产出（自引用条目描述本接口出参，
        # 如 strategygroup/vdi/create 的 vdiStrategyId=$.content.id）；
        # 无自引用产出则取第一个有产出变量的 setup 步骤（历史行为）
        extract = {}

        def _ex_of(s):
            ex = s.get("extract")
            if isinstance(ex, dict) and ex:
                return {k: jp for k, jp in ex.items() if isinstance(jp, str) and jp.startswith("$")}
            if isinstance(ex, list):
                out = {}
                for it in ex:
                    if isinstance(it, dict) and it.get("var") and it.get("jsonpath"):
                        out[it["var"]] = it["jsonpath"]
                return out
            return {}

        for s in meta.get("setup") or []:
            sraw = s.get("api", "")
            sdep = sraw.split(" ", 1)[-1] if " " in sraw else sraw
            if sdep == api:
                extract = _ex_of(s)
                if extract:
                    break
        if not extract:
            for s in meta.get("setup") or []:
                extract = _ex_of(s)
                if extract:
                    break
        # polling：接口 polling 配置（api 为节点名时经索引别名解析为真实 url，
        # 如 common_get_msgct_detail_info → /rco/msgct/msg/detail，避免执行期 404）
        poll = meta.get("polling") or None
        if isinstance(poll, dict) and poll.get("api") and not str(poll["api"]).startswith("/"):
            resolved = self.index.resolve(poll["api"])
            if resolved:
                poll = dict(poll, api=resolved)
        step = {"name": item[:20], "api": api, "body": body, "extract": extract, "poll": poll}
        # 文档驱动补数声明（executor._apply_fill 执行期消费：字段缺失时按声明查接口取值）
        if meta.get("fill"):
            step["fill"] = meta.get("fill")
        # 幂等：接口 setup 中若有【该接口自身】的步骤带 idempotent，继承
        # （仅 api 匹配，避免 create_classroom 等前置项泄漏给主接口造成重复调用）
        for s in meta.get("setup") or []:
            sraw = s.get("api", "")
            sdep = sraw.split(" ", 1)[-1] if " " in sraw else sraw
            if sdep != api:
                continue
            if s.get("idempotent") and (s.get("delete_api") or s.get("reuse_query")):
                step["idempotent"] = s["idempotent"]
                if s.get("delete_api"):
                    step["delete_api"] = s["delete_api"]
                if s.get("reuse_query"):
                    step["reuse_query"] = s["reuse_query"]
                break
        # 特殊处理：desktop/list 的最小查询条件（classroomId 过滤）与 yetAssign 的
        # exactMatchArr 注入均已迁移到接口文档 front-matter 的 fill 声明（文档驱动补数），
        # 编排器不再硬编码（远端 a0382a6 的代码注入方案被 fill 声明方案取代）
        return step

    def _collect_produce(self, meta):
        """收集接口的「产出 jsonpath」（供 LLM 写 extract_override 时从清单选取，而非猜）：
        1. setup 各步骤 extract 的 jsonpath（编排器实际提取路径，真实）
        2. 本接口 upstream 的 produces 字段（上游接口的产出，供跨接口关联）
        返回去重后的 jsonpath 列表（截断防止 prompt 过长）。"""
        seen = []
        # 1. setup extract jsonpath
        for s in meta.get("setup") or []:
            ex = s.get("extract")
            if isinstance(ex, dict):
                for var, jp in ex.items():
                    if isinstance(jp, str) and jp.startswith("$") and jp not in seen:
                        seen.append(jp)
            elif isinstance(ex, list):
                for it in ex:
                    if isinstance(it, dict) and it.get("jsonpath") and str(it["jsonpath"]).startswith("$") \
                            and str(it["jsonpath"]) not in seen:
                        seen.append(str(it["jsonpath"]))
        # 2. response.body 的 itemArr 元素字段（分页列表的真实产出，如 itemArr[]_desktopId）
        resp_body = (meta.get("response") or {}).get("body") or {}
        if isinstance(resp_body, dict):
            for k in resp_body:
                if k.startswith("itemArr[]_") and k not in ("itemArr[]",):
                    jp = "$.content.itemArr[*]." + k[len("itemArr[]_"):]
                    if jp not in seen:
                        seen.append(jp)
        # 3. upstream produces（上游产出 jsonpath，来自 field_map 关联）
        for u in meta.get("upstream") or []:
            p = u.get("produces")
            if isinstance(p, str) and p.startswith("$") and p not in seen:
                seen.append(p)
            elif isinstance(p, list):
                for x in p:
                    if isinstance(x, str) and x.startswith("$") and x not in seen:
                        seen.append(x)
        return seen[:8]

    def _infer_body_value(self, field, spec, meta):
        """推断裸请求字段的 value 引用（确定性规则，非 AI）：
        1. 字段名 snake_case 命中文档 params → ${param.<snake>}
        2. 字段命中已知生成规则（cpu/memory/systemSize 等）→ 标记 generated_by
        3. 字段名匹配 setup extract 产出变量 → ${prev.<var>}
        否则返回 None（保持裸字段，由 param_map/人工补充）
        """
        import re
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', field).lower()
        # 1. params 节变量（required + 全量）
        pnames = set()
        params = meta.get("params") or {}
        for grp in ("required", "optional"):
            for p in (params.get(grp) or []) or []:
                if isinstance(p, dict) and p.get("name"):
                    pnames.add(p["name"])
        if snake in pnames:
            return "${param." + snake + "}"
        # 2. 生成规则字段
        gen_fields = ("cpu", "memory", "systemSize", "platformStrategyGroup", "deskCreateMode",
                      "desktopPreName", "desktopNameStartNum", "desktopNum", "seatNum",
                      "page", "limit", "rows", "sort", "sortArr")
        if field in gen_fields:
            return "generated"
        # 3. setup extract 产出（prev 变量）：引用「该 setup 步骤」的标准三段式
        for s in meta.get("setup", []):
            ex = s.get("extract") or {}
            if isinstance(ex, dict):
                for var in ex:
                    if var.lower() == snake or var.lower() == field.lower():
                        sname = s.get("name") or self._auto_step_name(s.get("api", ""))
                        return "${prev.%s.output.%s}" % (sname, var)
        return None

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
        "上课|开课": ["lesson/start"],
        "下课|结束上课|结束课程": ["lesson/end"],
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
        # 操作句剔除查询类动作词（列表/获取/查看），避免干扰操作动作（如"选择多个...重启"不应命中 list/get）
        query_actions = ("list", "getInfo", "detail", "get", "page")
        has_op = any(a not in query_actions for a in self._actions_of(item))
        url = self._semantic_match(item, prefer_create=False, drop_query=has_op)
        return url

    def _actions_of(self, item):
        """提取例句命中的动作词列表"""
        actions = []
        for act_kw, act_urls in self.ACTION_WORDS.items():
            if any(kw in item for kw in act_kw.split("|")):
                actions.extend(act_urls)
        return actions

    def _apply_semantic_rules(self, url, name, entities):
        """semantic_rules 打分修正（business_rules.md 数据驱动）：
        命中 if_entities / url_any / name_any（且不命中 name_none）的规则叠加 delta。
        语义冲突惩罚、侧别偏好等规则只在规则库维护，代码保持通用。"""
        delta = 0
        for r in self.rules.get("semantic_rules", []) or []:
            if not isinstance(r, dict):
                continue
            ents = [str(e) for e in (r.get("if_entities") or [])]
            if ents and not any(e in entities for e in ents):
                continue
            url_any = [str(u) for u in (r.get("url_any") or [])]
            if url_any and not any(u.lower() in url.lower() for u in url_any):
                continue
            name_any = [str(n) for n in (r.get("name_any") or [])]
            if name_any and not any(n in name for n in name_any):
                continue
            name_none = [str(n) for n in (r.get("name_none") or [])]
            if name_none and any(n in name for n in name_none):
                continue
            if not url_any and not name_any:
                continue
            delta += int(r.get("delta", 0))
        return delta

    def _semantic_match(self, item, prefer_create, drop_query=False):
        """通用语义匹配：例句动作词+实体词 → 接口 URL 打分"""
        # 提取例句中的动作词与实体词
        actions = []
        entities = []
        for act_kw, act_urls in self.ACTION_WORDS.items():
            # key 内 | 分隔的任一词在例句中即命中（"收集|收集日志" 匹配"收集终端日志"）
            if any(kw in item for kw in act_kw.split("|")):
                actions.extend(act_urls)
        if drop_query:
            actions = [a for a in actions if a not in ("list", "getInfo", "detail", "get", "page")]
        for ent_kw, ent_urls in self.ENTITY_WORDS.items():
            if any(kw in item for kw in ent_kw.split("|")):
                entities.extend(ent_urls)

        best_url = None
        best_score = 0
        for meta in self.index.all():
            url = meta.get("url", "")
            score = 0
            name = meta.get("name", "")
            # 规则库修正（semantic_rules）：语义冲突惩罚、RDCD/Space 侧别偏好等
            score += self._apply_semantic_rules(url, name, entities)
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

    def _build_auto_provision_rules_text(self):
        """生成 auto_provision 规则摘要文本，供 LLM 编排时理解"""
        rules = self.rules.get("auto_provision", {})
        idempotent = rules.get("idempotent_create", []) or []
        if not idempotent:
            return ""

        lines = ["【全局规则 — 自动造数（幂等复用）】"]
        for item in idempotent:
            rtype = item.get("resource_type", "")
            pkey = item.get("param_key", "")
            create_url = "/" + item.get("create_api", "").split(" ", 1)[-1] if " " in item.get("create_api", "") else item.get("create_api", "")
            note = item.get("note", "")
            lines.append("- %s：当查询 %s 无结果时，必须先从 param 读取 %s 获取名称，再调 %s 创建策略，然后用查询接口拿到 ID 传给后续步骤。%s" % (rtype, pkey, pkey, create_url, note))
        lines.append("- 全局参数清单中已有的参数（${param.xxx}）可直接使用，无需从全局参数清单编造新参数名。")
        lines.append("- 当用例需要获取策略/教室等资源且查询无结果时，遵循「先创建同名策略，再查询得到 ID」的顺序。")
        return "\n".join(lines)

    def _build_param_ref_rules_text(self):
        """生成 param_ref_rules 规则摘要文本，供 LLM 编排时理解参数来源继承"""
        rules = self.rules.get("param_ref_rules", []) or []
        if not rules:
            return ""

        lines = ["【全局规则 — 参数引用继承】"]
        for r in rules:
            name = r.get("name", "")
            desc = r.get("description", "")
            if desc:
                lines.append("- %s" % desc)
            sources = r.get("target_interfaces", []) or []
            targets = r.get("target_fields", []) or []
            source_param = r.get("source_param", "")
            if source_param:
                for src_url in sources:
                    for tgt_fld in targets:
                        lines.append("  - %s (%s) → %s = param.%s[0]" % (tgt_fld, src_url, tgt_fld, source_param))
            note = r.get("note", "")
            if note:
                lines.append("- %s" % note)
        lines.append("- 当 param_map 中有字段需要引用 param 时，必须检查 param_ref_rules 声明的继承关系，优先使用声明的来源参数，不得编造 param 中不存在的参数名。")
        return "\n".join(lines)

    def _apply_param_ref_rules(self, steps, warns):
        """param_ref_rules 确定性消费：扫描所有步骤 body 中引用不存在的 param，
        命中规则的 target_fields 就按 source_param 改写值。覆盖 setup 步骤和主步骤。"""
        rules = self.rules.get("param_ref_rules", []) or []
        if not rules:
            return

        import re
        for rule in rules:
            source_param = rule.get("source_param", "")
            target_fields = rule.get("target_fields", []) or []
            if not source_param or not target_fields:
                continue

            for st in steps:
                body = st.get("body") or {}
                for fld in target_fields:
                    if fld not in body:
                        continue
                    fld_spec = body[fld]
                    if not isinstance(fld_spec, dict):
                        continue
                    val = fld_spec.get("value")
                    if val is None:
                        continue
                    val_str = str(val)
                    # 检查 value 是否引用了不存在的 param
                    param_match = re.search(r"\$\{param\.([\w_]+)\}", val_str)
                    if not param_match:
                        continue
                    ref_param = param_match.group(1)
                    if ref_param == source_param:
                        continue  # 已经是正确的 source_param，跳过

                    # 替换为正确的引用
                    # 支持带 [0] 索引（如 param.student_mode_arr[0]）
                    new_val = re.sub(r"\$\{param\.[\w_]+\}", "${param.%s[0]}" % source_param, val_str)
                    body[fld] = dict(fld_spec, value=new_val)

        # 写回步骤 body
        for st in steps:
            if st.get("body"):
                st["body"] = st["body"]

    def _apply_auto_provision(self, intent, sections, params):
        """auto_provision 规则：智能补充策略创建步骤（编排阶段）

        当 LLM 编排出的步骤中只包含查询（如 get_vdi_strategy）但不包含
        对应创建步骤时，自动注入「创建 + 查询」链路到编排计划中。
        规则来源：business_rules.md 中的 auto_provision.idempotent_create
        """
        auto_rules = self.rules.get("auto_provision", {}).get("idempotent_create", []) or []
        if not auto_rules:
            return intent

        steps_list = intent.get("steps", [])
        step_apis = [s.get("api", "") for s in steps_list]
        step_names = [s.get("step_name", "") for s in steps_list]

        for rule in auto_rules:
            resource_type = rule.get("resource_type", "")
            query_api = rule.get("query_api", "")
            create_api = rule.get("create_api", "")
            param_key = rule.get("param_key", "")

            def _bare(raw):
                """'POST /x/y' → '/x/y'（intent 步骤 api 为裸路径，index 按裸路径索引；
                直接前置 '/' 会产生 // 双斜杠导致 has_query 永远不命中）"""
                raw = str(raw or "")
                path = raw.split(" ", 1)[-1] if " " in raw else raw
                return path if path.startswith("/") else "/" + path

            create_url = _bare(create_api)
            query_url = _bare(query_api)

            # 检查：编排中是否有该查询步骤
            has_query = any(query_url in api for api in step_apis)
            if not has_query:
                continue

            # 检查：编排中是否已有该创建步骤
            has_create = any(create_url in api for api in step_apis)
            if has_create:
                continue

            # 检查：全局参数中是否有同名配置
            if not params.get(param_key):
                continue

            # 注入创建步骤到编排计划中（放在查询之前；api 必须为裸路径，
            # 否则 build_plan_ai 主循环 index.get(api) 查不到会被当「不在索引」丢弃）
            create_step = {
                "section": "pre",
                "api": create_url,
                "step_name": "create_" + resource_type,
                "reason": "auto_provision: 策略不存在则自动创建",
            }
            # 找到查询步骤在 steps_list 中的位置，在它之前插入创建步骤
            query_idx = None
            for i, s in enumerate(steps_list):
                if query_url in s.get("api", ""):
                    query_idx = i
                    break

            if query_idx is not None:
                steps_list.insert(query_idx, create_step)
            else:
                steps_list.insert(0, create_step)

        return intent

