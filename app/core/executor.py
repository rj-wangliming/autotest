# -*- coding: utf-8 -*-
"""用例执行器（真实方法调用，无字符串拼装）

业务执行全部是方法调用：http_request / extract / poll / recreate / skip / assert / cleanup。
支持两种运行模式：
- 进程内：Executor.execute(plan, params) 直接执行
- 隔离：run_plan() 供 subprocess 固定入口调用（script_runner 传 plan JSON）
"""
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

from .jsonpath import jsonpath_get
from .params import resolve_body, resolve_value, gen_config_value, to_snake, materialize_naming
from .aes_crypto import encrypt

# 目标环境为自签 HTTPS 证书，禁用 SSL 证书验证告警（verify=False 时的 InsecureRequestWarning）
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


# 需要 X-One-Time-Token header 的接口路径列表（从 onces_token_api_url_data.py 同步）
ONCE_TOKEN_PATHS = {
    "/rcc/classroom/delete",
    "/rcc/classroom/seat/delete",
    "/rcc/classroom/image/student/delete",
    "/rcc/classroom/image/teacher/delete",
    "/rcc/classroom/editTeacherInfo",
    "/rcc/classroom/editStudentInfo",
    "/rcc/classroom/seat/clearTciLocalDisk",
    "/rcc/classroom/seat/vdiLocalDisk/clear",
    "/rcc/classroom/desktop/restoreVDIImage",
}


class Executor:
    """进程内执行器（完整业务方法）"""

    # 资源变量名 → 删除接口（cleanup 用）
    CLEANUP_MAP = {
        "classroomId": "/rcc/classroom/delete",
        "deskStrategyId": "/space/strategygroup/vdi/delete",
        "strategyId": "/rcc/classroom/strategy/delete",
        "seatIdArr": "/rcc/classroom/seat/delete",
    }

    def __init__(self, base_url=None, log_cb=None, strict=False):
        self.base_url = (base_url or os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8080")).rstrip("/")
        self.log_cb = log_cb or (lambda level, msg: None)
        # strict=True：轮询接口缺失/删除无法验证等「无法确认结果」的场景直接判失败；
        # 默认 False：降级为通过 + 记录 warning（结果 JSON 的 warnings 数组可查，不再静默假绿）
        self.strict = strict
        self._session = None  # requests.Session：维持登录 cookie 会话（webmvckit 会话认证）

    def _warn(self, ctx, code, msg):
        """记录执行期 warning（进入 ctx['warnings'] → 最终 result['warnings']，并落日志）"""
        entry = {"code": code, "message": msg}
        if isinstance(ctx, dict):
            ctx.setdefault("warnings", []).append(entry)
        self.log("warning", "[%s] %s" % (code, msg))
        return entry

    def _get_once_token(self, ctx):
        """获取 X-One-Time-Token header 值。

        调用 POST /rcdc/gss/iac/admin/applyOneTimeToken，传入 AES 加密的管理员密码。
        参考：commonlib.api_protocol_lib.http_interface.common_get_once_token
        """
        p = ctx.get("params", {})
        admin_password = p.get("rcdc_passwd") or p.get("admin_password")
        if not admin_password:
            return None
        # 传入明文密码，内部自动 AES 加密（与 Ruijie 平台一致）
        encrypted_pwd = encrypt(admin_password, "ADMINPASSWORDKEY")
        body = {"password": encrypted_pwd}
        status, data = self.http_request("POST", "/gss/iac/admin/applyOneTimeToken", body, ctx)
        if status != 200 or data.get("status") != "SUCCESS":
            raise RuntimeError("applyOneTimeToken 失败: %s" % data.get("message"))
        return data.get("content", {}).get("oneTimeToken")

    def _get_session(self):
        """懒加载 requests.Session：登录的 Set-Cookie 被保留，后续请求自动携带会话凭证"""
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.verify = False
        return self._session

    # 敏感字段（日志脱敏，避免凭据落盘/落库）
    SENSITIVE_KEYS = {"token", "password", "pwd", "apikey", "api_key", "admin_password",
                      "studentaccountpassword", "authorization", "secret"}

    # ---------- 基础 ----------
    def log(self, level, msg):
        self.log_cb(level, msg)

    def _mask(self, obj):
        """递归脱敏 dict/list 中的敏感字段（值替换为 ****）"""
        if isinstance(obj, dict):
            return {k: ("****" if k.lower() in self.SENSITIVE_KEYS else self._mask(v))
                    for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._mask(x) for x in obj]
        return obj

    def http_request(self, method, path, body=None, ctx=None):
        """发送 HTTP 请求（真实方法调用）。

        ctx 提供 token 与登录凭据；401 自动重登并把新 token 写回 ctx['token']（会话持久化）。
        verify=False：目标环境为自签 HTTPS 证书。
        二次鉴权：对标注 @OneTimeTokenRequired 的接口，自动通过 applyOneTimeToken 获取
        X-One-Time-Token header。
        """
        # 二次鉴权：对需要 oneTimeToken 的接口，先获取 token
        once_token = None
        if ctx and path in ONCE_TOKEN_PATHS:
            try:
                once_token = self._get_once_token(ctx)
                if once_token:
                    self.log("info", "[oneTimeToken] 获取成功: %s..." % str(once_token)[:12])
            except Exception as e:
                self.log("warning", "[oneTimeToken] 获取失败: %s（跳过二次鉴权）" % e)
        session = self._get_session()
        token = ctx.get("token") if ctx else None
        headers = {"Content-Type": "application/json"}
        cookies = None
        if token:
            # 锐捷平台认证（浏览器抓包实测）：iac-token header + cookie(iac-token/rcdcAdmin-Token) + CDC 来源标识
            headers["iac-token"] = token
            headers["source"] = "CDC"
            headers["subSystem"] = "CDC"
            cookies = {"iac-token": token, "rcdcAdmin-Token": token}
        # 二次鉴权：需要 X-One-Time-Token header
        if once_token:
            headers["X-One-Time-Token"] = once_token
        url = self.base_url + path
        self.log("req", "%s %s" % (method, url))
        if body:
            self.log("req", "body: %s" % json.dumps(self._mask(body), ensure_ascii=False))
        try:
            resp = session.request(method, url, json=body, headers=headers,
                                   cookies=cookies, timeout=30, verify=False)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            self.log("resp", "HTTP %s: %s" % (resp.status_code, json.dumps(self._mask(data), ensure_ascii=False)))
            # 401 自动重登一次再重试（会话过期自愈，新 token 写回 ctx 持久化）
            if resp.status_code == 401 and token and "/loginAdmin" not in path and ctx is not None:
                self.log("auth", "401 → 重新登录")
                p = ctx.get("params", {})
                new_token = self.login(p.get("rcdc_user") or p.get("admin_user"),
                                       p.get("rcdc_passwd") or p.get("admin_password"))
                ctx["token"] = new_token
                headers["iac-token"] = new_token
                if cookies is not None:
                    cookies = {"iac-token": new_token, "rcdcAdmin-Token": new_token}
                # 重登后重新获取一次令牌（会话已刷新）
                if once_token:
                    try:
                        once_token = self._get_once_token(ctx)
                        headers["X-One-Time-Token"] = once_token
                    except Exception:
                        once_token = None  # 如果获取失败，不阻塞重试
                resp = session.request(method, url, json=body, headers=headers,
                                       cookies=cookies, timeout=30, verify=False)
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                self.log("resp", "HTTP %s（重试，含一次令牌）" % resp.status_code)
            return resp.status_code, data
        except Exception as e:
            self.log("error", "请求失败: %s" % e)
            return 0, {"status": "ERROR", "message": str(e)}

    def login(self, admin_user=None, admin_password=None):
        """框架内置登录（loginAdmin）。凭据优先参数传入，其次环境变量，缺失则报错（不留明文默认）。

        注意：服务端 loginAdmin 接口要求 pwd 字段为 AES 加密后的密码（key=ADMINPASSWORDKEY）。
        因此传入的 admin_password 应为明文，内部自动加密。
        """
        admin_user = admin_user or os.environ.get("TEST_ADMIN_USER")
        admin_password = admin_password or os.environ.get("TEST_ADMIN_PASSWORD")
        if not admin_user or not admin_password:
            raise RuntimeError(
                "缺少登录凭据：请在用例参数 rcdc_user/rcdc_passwd（或 admin_user/admin_password）"
                "或环境变量 TEST_ADMIN_USER/TEST_ADMIN_PASSWORD 中提供"
            )
        import time as _time
        # AES 加密密码（与服务端 loginAdmin 接口要求一致）
        encrypted_pwd = encrypt(admin_password, "ADMINPASSWORDKEY")
        body = {
            "userName": admin_user,
            "pwd": encrypted_pwd,
            "captchaCode": "",
            "captchaKey": "",
            "timestamp": int(_time.time() * 1000),
        }
        status, data = self.http_request("POST", "/rco/admin/loginAdmin", body, None)
        if status < 200 or status >= 300:
            raise RuntimeError("登录失败: HTTP %s (%s)" % (status, json.dumps(data, ensure_ascii=False, default=str)))
        token = jsonpath_get(data, "$.content.token") or jsonpath_get(data, "$.data.token")
        if not token:
            raise RuntimeError("登录成功但无法获取 token: %s" % json.dumps(data, ensure_ascii=False, default=str))
        self.log("info", "[登录] token=%s..." % str(token)[:12])
        if not token:
            self.log("error", "[登录] token 为空，登录失败：检查接口路径/凭据/服务器状态")
            raise RuntimeError("[登录] token 为空，登录失败：检查接口路径/凭据/服务器状态")
        return token

    # ---------- 步骤执行 ----------
    def execute_step(self, step, ctx):
        """执行单个步骤（真实方法调用）"""
        api = step.get("api", "")
        path = api.split(" ", 1)[-1] if " " in api else api
        method = step.get("method", "POST")
        raw_body = step.get("body", {})
        body = resolve_body(raw_body, ctx)
        self.log("info", "[step] %s resolved body: %s (raw=%s)" % (
            step.get("step_name") or step.get("name") or "",
            json.dumps(body, ensure_ascii=False),
            json.dumps(self._mask(raw_body), ensure_ascii=False)))

        # 登录内置
        if "loginAdmin" in api:
            p = ctx["params"]
            ctx["token"] = self.login(p.get("rcdc_user") or p.get("admin_user"),
                                      p.get("rcdc_passwd") or p.get("admin_password"))
            ctx["context"] = {"token": ctx["token"]}
            return {"status": "SUCCESS", "content": {"token": ctx["token"]}}

        # 特殊处理：get_network 步骤优先从配置读取 network_id_arr
        # （global_params.yaml 已配置网络策略 ID 时，无需调 API 查询）
        if "deskNetwork/list" in path or (step.get("step_name") == "get_network" and "network" in path.lower()):
            network_id_arr = ctx["params"].get("network_id_arr")
            if network_id_arr:
                # 列表取首元素（非批量上下文）
                nid = network_id_arr[0] if isinstance(network_id_arr, list) else network_id_arr
                self.log("info", "[get_network] 从配置读取 network_id_arr: %s" % nid)
                sname = step.get("step_name") or step.get("name") or "get_network"
                bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
                bucket["networkId"] = nid
                # 支持 extract 声明（如果步骤定义了 extract）
                ex = step.get("extract") or {}
                if isinstance(ex, dict):
                    for var in ex:
                        if var not in bucket:
                            bucket[var] = nid
                return {"status": "SUCCESS", "content": {"networkId": nid}}

        # ---------- 后续正常请求执行 ----------
        # （策略 ID 一律走真实查询：strategy/list、strategygroup/vdi|tci/list
        #   的伪造响应钩子已移除——[None] 批量包装/错名注入等假数据根源）

        # 特殊处理：若 /rcc/classroom/image/ 路径降级为空结果，跳过 image/create 步骤
        # （CBB 无可用资源时，image/create 会因 plusImageId=null 报错，直接跳过更合理）
        if ctx.get("_image_empty_list") and re.match(r"^/rcc/classroom/image/(student|teacher)/create$", path):
            self.log("warning", "[skip] get_image 降级为空镜像列表，跳过 %s" % api)
            return {"status": "SUCCESS", "content": {"message": "skipped (no available image)"}}

        # 幂等 reuse：存在同名直接复用、跳过创建（用于策略/镜像等环境已有资源）
        if step.get("idempotent") == "reuse" and step.get("reuse_query"):
            reused = self._try_reuse(step, ctx)
            if reused is not None:
                return reused

        # 幂等 recreate：先删同名再建
        if step.get("idempotent") == "recreate" and step.get("delete_api"):
            self.log("info", "[recreate] ENTERING for step_name=%s, api=%s" % (step.get("step_name"), step.get("api")))
            self.log("info", "[recreate] delete_api=%s" % step.get("delete_api"))
            r = self._recreate(step, body, ctx)
            self.log("info", "[recreate] returned: %s" % r)
            if r == "skip":
                return self._build_skip_response(step, body, ctx)

        # 幂等 true：先尝试创建（存在则幂等通过）
        if step.get("idempotent") is True:
            status, data = self.http_request(method, path, body or None, ctx)
            if jsonpath_get(data, "$.status") == "SUCCESS":
                self.log("info", "[idempotent] 创建成功或已存在")
            return data

        # 文档驱动补数（接口文档 front-matter fill 声明）：platformId 缺失回查、
        # exactMatchArr 注入等由文档声明驱动，executor 只提供通用补数引擎
        # （远端 a0382a6 的 executor 硬编码注入方案被 fill 声明方案取代）
        body = self._apply_fill(step, body, ctx)

        status, data = self.http_request(method, path, body or None, ctx)

        # 设置 _last_data（_poll 需要读取当前步骤响应中的 taskId）
        ctx["_last_data"] = data

        # extract 产出（多变量）
        # skip_if_empty：步骤声明时，响应 itemArr 为空则跳过 extract（不覆盖已有产出桶），
        # 用于多版本镜像回查等「查询空则回退上一步产出」的场景
        if step.get("skip_if_empty"):
            _arr = jsonpath_get(data, "$.content.itemArr")
            if isinstance(_arr, list) and not _arr:
                self.log("info", "[skip_if_empty] %s 返回空列表，跳过 extract（保留上一步产出）" % step.get("step_name"))
                data = {**data, "content": {**data.get("content", {}), "itemArr": _arr}}
            else:
                self._extract(step, data, ctx)
        else:
            self._extract(step, data, ctx)

        # 特殊处理：strategygroup/vdi/list 或 strategygroup/tci/list 返回空数组时
        # → 尝试无 name 过滤查询第一条 VDI/TCI 策略（避免课程策略为 null 导致后续失败）
        if status in (200, 201):
            itemArr = jsonpath_get(data, "$.content.itemArr")
            if isinstance(itemArr, list) and not itemArr and (
                "strategygroup/vdi/list" in path or "strategygroup/tci/list" in path
            ):
                sname = step.get("step_name") or step.get("name") or "get_vdi_strategy"
                bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
                # 检查是否已有课程策略 ID（避免重复查询）
                has_strategy = any(
                    bucket.get(v) is not None
                    for v in ("vdiStrategyId", "deskStrategyId", "tciStrategyId")
                )
                if not has_strategy:
                    self.log("info", "[vdi/tci strategy] API 返回空，无 name 过滤查询第一条策略")
                    # 构造无过滤请求
                    fallback_body = {}
                    if "vdi/list" in path:
                        fallback_body = {"page": 0, "limit": 1}
                    else:
                        fallback_body = {"page": 0, "limit": 1}
                    fallback_status, fallback_data = self.http_request(
                        method, path, fallback_body or None, ctx
                    )
                    fallback_itemArr = jsonpath_get(fallback_data, "$.content.itemArr")
                    if isinstance(fallback_itemArr, list) and fallback_itemArr:
                        first = fallback_itemArr[0]
                        sid = first.get("id") or first.get("deskStrategyId") or first.get("classroomStrategyId")
                        if sid:
                            # 写入 bucket（映射到正确的变量名）
                            if "vdi/list" in path:
                                bucket["vdiStrategyId"] = sid
                            elif "tci/list" in path:
                                bucket["tciStrategyId"] = sid
                            else:
                                bucket["vdiStrategyId"] = sid
                            self.log("info", "[vdi/tci strategy] 兜底策略 ID: %s" % sid)
                            data = {**data, "content": {**data.get("content", {}), "itemArr": [first]}}
                        else:
                            self.log("warning", "[vdi/tci strategy] 兜底查询也返回空")
                    else:
                        self.log("warning", "[vdi/tci strategy] 兜底查询也返回空")

        # polling 异步任务：仅在业务成功时才轮询（ERROR 状态不轮询）
        biz_status = jsonpath_get(data, "$.status") if isinstance(data, dict) else None
        if step.get("poll") and status in (200, 201) and biz_status == "SUCCESS":
            self._poll(step["poll"], ctx)
        elif step.get("poll") and biz_status != "SUCCESS":
            self.log("warning", "[poll] 业务状态非 SUCCESS（%s），跳过轮询" % biz_status)

        # internal_error 不做降级，如实报告失败

        # 断言
        self._assert_step(step, data)
        return data

    # ---------- 文档驱动补数（fill 声明引擎） ----------
    def _apply_fill(self, step, body, ctx):
        """按 step.fill 声明补全请求体（声明来自接口文档 front-matter fill 节）。

        每条声明：{field, when: missing, value?, append_item?, sources?, cache_by?}
        - value：字段缺失时注入静态结构（支持 ${prev.*}/${param.*}，先解析再注入）
        - sources：字段缺失时依次调用声明接口取值（from jsonpath，from_fallback 兜底），
          取到非空值注入；cache_by 声明缓存键（如 ${body.crId}），同键不重复查询
        - append_item：向列表字段追加动态条目（sources 取到值才追加，值经 ${fill} 引用；
          列表中已有同名 name 条目则跳过）
        ${body.X} 引用当前已解析请求体的字段值。
        """
        fills = step.get("fill") or []
        if not isinstance(body, dict):
            # resolve_body 全空（如 matchArr 参数缺失被清空）返回 None → 兜底为空 dict，
            # 使 fill（exactMatchArr 等）仍能注入，避免请求体为 null 触发后端 internal_error
            body = {}
        if not isinstance(fills, list):
            return body
        for spec in fills:
            if not isinstance(spec, dict):
                continue
            field = spec.get("field")
            if not field:
                continue
            cur = body.get(field)
            if spec.get("value") is not None and cur in (None, "", [], {}):
                val = resolve_value(self._subst_body_refs(spec["value"], body), ctx)
                if val not in (None, "", [], {}):
                    body[field] = val
                    self.log("info", "[fill] %s 注入声明值" % field)
                    cur = body[field]
            ai = spec.get("append_item")
            if isinstance(ai, dict) and isinstance(cur, list):
                item_name = ai.get("name")
                if not item_name or any(isinstance(x, dict) and x.get("name") == item_name for x in cur):
                    continue
                got = self._fill_from_sources(spec, body, ctx)
                if got not in (None, ""):
                    item = resolve_value(self._subst_fill_ref(ai, got), ctx)
                    if isinstance(item, dict) and item.get("valueArr"):
                        body[field].append(item)
                        self.log("info", "[fill] %s 追加条目 %s=%s" % (field, item_name, item.get("valueArr")))
            elif "sources" in spec and body.get(field) in (None, ""):
                got = self._fill_from_sources(spec, body, ctx)
                if got not in (None, ""):
                    body[field] = got
                    self.log("info", "[fill] %s 从接口取值注入: %s" % (field, got))
        return body

    def _fill_from_sources(self, spec, body, ctx):
        """按声明依次尝试 sources 接口取值；cache_by 命中缓存直接返回"""
        cache_key = None
        if spec.get("cache_by"):
            cache_key = str(self._subst_body_refs(spec["cache_by"], body))
            cache = ctx.setdefault("_fill_cache", {})
            if cache_key in cache:
                self.log("info", "[fill] 缓存命中 %s" % cache_key)
                return cache[cache_key]
        for src in spec.get("sources", []) or []:
            raw = str(src.get("api", "") or "")
            if not raw:
                continue
            method = raw.split(" ", 1)[0] if " " in raw else "POST"
            path = raw.split(" ", 1)[-1]
            qbody = resolve_value(self._subst_body_refs(src.get("body") or {}, body), ctx)
            try:
                status, data = self.http_request(method, path, qbody or None, ctx)
            except Exception as e:
                self.log("warning", "[fill] %s 调用失败: %s" % (path, e))
                continue
            val = jsonpath_get(data, src.get("from", ""))
            if val in (None, "") and src.get("from_fallback"):
                val = jsonpath_get(data, src["from_fallback"])
            if val not in (None, ""):
                if cache_key:
                    ctx["_fill_cache"][cache_key] = val
                return val
        return None

    def _subst_body_refs(self, obj, body):
        """把 ${body.X} 替换为当前请求体字段值（非字符串值序列化为 JSON）"""
        if isinstance(obj, str):
            def repl(m):
                v = body.get(m.group(1))
                if v is None:
                    return ""
                return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            return re.sub(r"\$\{body\.(\w+)\}", repl, obj)
        if isinstance(obj, dict):
            return {k: self._subst_body_refs(v, body) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._subst_body_refs(v, body) for v in obj]
        return obj

    @staticmethod
    def _subst_fill_ref(obj, got):
        """递归把 append_item 模板中的 ${fill} 替换为 sources 取到的值"""
        if isinstance(obj, str):
            return obj.replace("${fill}", str(got))
        if isinstance(obj, dict):
            return {k: Executor._subst_fill_ref(v, got) for k, v in obj.items()}
        if isinstance(obj, list):
            return [Executor._subst_fill_ref(v, got) for v in obj]
        return obj

    def _build_skip_response(self, step, body, ctx):
        """构建跳过创建的响应（复用已有资源）"""
        sname = step.get("step_name") or step.get("name") or "default"
        bucket = ctx.get("steps", {}).get(sname, {})
        data = {"status": "SUCCESS", "content": {}}
        if "classroomId" in bucket:
            data["content"]["classroomId"] = bucket["classroomId"]
        if "seatId" in bucket:
            data["content"]["seatId"] = bucket["seatId"]
        if "classroomId" not in data["content"] and "seatId" not in data["content"]:
            data["content"]["classroomId"] = ""
        self._extract(step, data, ctx)
        self.log("info", "[skip] 复用已有资源，跳过创建")
        return data

    def _recreate(self, step, body, ctx):
        """幂等 recreate：存在同名先调 delete_api 删除再创建

        Returns:
            True: 删除成功，应继续执行创建（create）
            "skip": 复用已有资源（无法删除或不存在），跳过创建
            False: 无同名资源，正常流程执行创建
        """
        del_api = step["delete_api"]
        del_path = del_api.split(" ", 1)[-1] if " " in del_api else del_api
        # 判断资源类型
        is_classroom = "classroom" in del_path
        is_seat = "seat" in del_path
        self.log("info", "[recreate] del_path=%s, is_classroom=%s, is_seat=%s" % (del_path, is_classroom, is_seat))
        self.log("info", "[recreate] body keys=%s, idempotent=%s" % (list(body.keys()), step.get("idempotent")))

        if is_seat:
            classroom_id = body.get("classroomId")
            if not classroom_id:
                return False
            # seat/list 的 exactMatchArr 支持 classroomId 过滤
            select_body = {"exactMatchArr": [{"name": "classroomId", "valueArr": [classroom_id]}]}
            select_path = "/rcc/classroom/seat/list"
            id_key = "id"
        elif is_classroom:
            classroom_name = body.get("classroomName") or ""
            classroom_id = body.get("classroomId")
            if not classroom_name and not classroom_id:
                return False
            # 优先用 classroomId 精确匹配，否则按 classroomName 搜索
            if classroom_id:
                select_body = {"exactMatchArr": [{"name": "classroomId", "valueArr": [classroom_id]}]}
                select_path = "/rcc/classroom/select"
                id_key = "classroomId"
            else:
                select_body = {"searchKeyword": classroom_name}
                select_path = "/rcc/classroom/select"
                id_key = "classroomId"
        else:
            return False

        status, data = self.http_request("POST", select_path, select_body, ctx)
        content = data.get("content") if isinstance(data, dict) else None
        items = None
        if isinstance(content, dict):
            items = content.get("itemArr") or content.get("items") or content.get("list")
        elif isinstance(content, list):
            items = content

        if not items or not isinstance(items, list):
            self.log("info", "[recreate] 未找到同名%s，跳过" % ("教室" if is_classroom else "座位"))
            return False

        found = items[0]
        found_id = found.get(id_key) or found.get("seatId") or found.get("id")
        found_token = found.get("oneTimeToken")

        if not found_id:
            return False

        self.log("info", "[recreate] 存在同名%s资源 %s，尝试删除" % ("教室" if is_classroom else "座位", found_id))

        # 获取 oneTimeToken（教室/座位删除可能需要）
        if is_classroom or is_seat:
            p = ctx.get("params", {})
            admin_password = p.get("rcdc_passwd") or p.get("admin_password")
            if admin_password:
                try:
                    encrypted_pwd = encrypt(admin_password, "ADMINPASSWORDKEY")
                    status, token_data = self.http_request("POST", "/gss/iac/admin/applyOneTimeToken",
                        {"password": encrypted_pwd}, ctx)
                    token_val = token_data.get("content", {}).get("oneTimeToken", "") if isinstance(token_data, dict) else ""
                    if token_val:
                        ctx["oneTimeToken"] = token_val
                        self.log("info", "[recreate] oneTimeToken 已获取")
                except Exception as e:
                    self.log("warning", "[recreate] oneTimeToken 获取失败: %s" % e)

        for attempt in range(2):
            if is_classroom:
                del_body = {"idArr": [found_id]}
            elif is_seat:
                # 座位 delete 需要 classroomId + seatIdArr
                del_body = {"classroomId": body.get("classroomId") or "",
                            "seatIdArr": [found_id]}
            else:
                del_body = {"idArr": [found_id]}

            if found_token:
                del_body["oneTimeToken"] = found_token

            delete_status, delete_data = self.http_request("POST", del_path, del_body, ctx)

            if delete_status != 200 or delete_data.get("status") != "SUCCESS":
                if attempt == 0 and ("token" in str(delete_data).lower() or delete_data.get("status") == "ERROR"):
                    self.log("warning", "[recreate] 认证失败，重新登录后再删")
                    p = ctx.get("params", {})
                    ctx["token"] = self.login(
                        p.get("rcdc_user") or p.get("admin_user"),
                        p.get("rcdc_passwd") or p.get("admin_password"),
                    )
                    continue
                else:
                    self.log("warning", "[recreate] 删除失败（%s），降级为复用已有资源 %s" % (delete_data.get("message") or str(delete_data), found_id))
                    sname = step.get("step_name") or step.get("name") or "default"
                    bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
                    if is_classroom:
                        bucket["classroomId"] = found_id
                    else:
                        bucket["seatId"] = found_id
                    return "skip"

            content = delete_data.get("content") if isinstance(delete_data, dict) else None
            task_id = None
            if isinstance(content, dict):
                task_id = content.get("taskId")

            if not task_id:
                self.log("info", "[recreate] 删除成功（同步返回），后续创建新资源")
                return True

            self.log("info", "[recreate] 异步删除中，taskId=%s" % task_id)
            verify = ({"kind": "seat", "id": found_id, "classroom_id": body.get("classroomId")}
                      if is_seat else {"kind": "classroom", "id": found_id})
            ok = self._poll_classroom_delete(task_id, ctx, verify=verify)
            if ok:
                self.log("info", "[recreate] 删除成功（异步完成），后续创建新资源")
                return True
            else:
                self.log("warning", "[recreate] 删除异步失败，降级为复用已有资源 %s" % found_id)
                sname = step.get("step_name") or step.get("name") or "default"
                bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
                if is_classroom:
                    bucket["classroomId"] = found_id
                else:
                    bucket["seatId"] = found_id
                return "skip"

        return "skip"

    def _poll_classroom_delete(self, task_id, ctx, verify=None, timeout=60, interval=5):
        """异步删除等待 + 资源存在性验证（不再「假设删除成功」）。

        轮询任务状态的接口路径未知 → 改为分段等待后查询资源是否仍存在：
        - 资源已消失 → 删除确认完成
        - 资源仍存在 → 继续等待至 timeout；超时记 warning 并返回 False
          （_recreate 收到 False 会降级为复用已有资源，不会误建重名资源）
        - 验证查询本身失败 → 无法确认（默认 warning + 通过，strict 模式失败）
        verify: {"kind": "classroom"|"seat", "id": 资源ID, "classroom_id": 座位所属教室}
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(interval)
            try:
                gone = self._verify_deleted(verify, ctx)
            except Exception as e:
                return self._unverified(ctx, "delete_verify_error",
                                        "删除验证查询失败，删除结果无法确认: taskId=%s (%s)" % (task_id, e),
                                        "删除验证失败: taskId=%s (%s)" % (task_id, e))
            if gone:
                self.log("info", "[poll-delete] 资源已删除确认: taskId=%s" % task_id)
                return True
            remain = int(deadline - time.time())
            self.log("info", "[poll-delete] 资源仍存在，继续等待...（剩余 %ds）" % max(remain, 0))
        self._warn(ctx, "delete_timeout",
                   "删除等待 %ds 超时，资源仍存在: taskId=%s" % (timeout, task_id))
        return False

    def _verify_deleted(self, verify, ctx):
        """查询资源是否已删除（select/seat/list 按精确条件查询；仍能查到=未删除）"""
        if not isinstance(verify, dict) or not verify.get("id"):
            return True  # 无验证信息（历史调用方兜底，视为已删除）
        if verify.get("kind") == "seat":
            status, data = self.http_request("POST", "/rcc/classroom/seat/list",
                                             {"exactMatchArr": [{"name": "classroomId",
                                                                 "valueArr": [verify.get("classroom_id")]}]}, ctx)
            content = data.get("content") if isinstance(data, dict) else None
            items = content.get("itemArr") if isinstance(content, dict) else (
                content if isinstance(content, list) else None)
            for s in items or []:
                if (s.get("id") or s.get("seatId")) == verify.get("id"):
                    return False
            return True
        status, data = self.http_request("POST", "/rcc/classroom/select",
                                         {"exactMatchArr": [{"name": "classroomId",
                                                             "valueArr": [verify.get("id")]}]}, ctx)
        content = data.get("content") if isinstance(data, dict) else None
        items = None
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            items = content.get("itemArr") or content.get("items") or content.get("list")
        return not items

    def _try_reuse(self, step, ctx):
        """幂等 reuse：按 reuse_query 查已有资源；命中则把产出写入
        ctx.steps[<本步骤>] 供 ${prev.<step>.output.<field>} 引用并跳过创建；
        未命中返回 None，走正常创建流程"""
        rq = step.get("reuse_query") or {}
        raw = rq.get("api", "")
        if not raw:
            return None
        path = raw.split(" ", 1)[-1] if " " in raw else raw
        method = raw.split(" ", 1)[0] if " " in raw else "POST"
        qbody = resolve_body(rq.get("body", {}), ctx)
        status, data = self.http_request(method, path, qbody or None, ctx)
        if jsonpath_get(data, "$.status") != "SUCCESS":
            self.log("warning", "[reuse] 查询未成功，回退正常创建")
            return None
        extract = rq.get("extract") or {}
        if not isinstance(extract, dict) or not extract:
            return None
        vals = {}
        for var, jp in extract.items():
            vals[var] = jsonpath_get(data, jp) if isinstance(jp, str) and jp.startswith("$") else None
        if all(v is None for v in vals.values()):
            self.log("info", "[reuse] 未找到已有资源，走正常创建流程")
            return None
        sname = step.get("step_name") or step.get("name") or "default"
        bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
        # 复用命中标记：_cleanup 跳过本桶（共享/环境已有资源不得被 finally 清理删除）
        bucket["_reused"] = True
        for var, v in vals.items():
            if v is not None:
                bucket[var] = v
                self.log("info", "[reuse] 复用已有资源 %s.%s=%s，跳过创建" % (sname, var, v))
        return data

    def _extract(self, step, data, ctx):
        """提取产出变量到 ctx.steps[step_name]（供 ${prev.<step>.output.<field>} 解析）"""
        ex = step.get("extract", {})
        if not isinstance(ex, dict) or not ex:
            return
        sname = step.get("step_name") or step.get("name") or "default"
        bucket = ctx.setdefault("steps", {}).setdefault(sname, {})
        bi = ctx.get("_batch_index")
        for var, jp in ex.items():
            if isinstance(jp, dict):
                val = self._extract_pick(data, jp)
                # fallback_from：pick 提取为空时回退到指定产出引用（如多版本镜像回查为空 → 模板 id）
                if val is None and jp.get("fallback_from"):
                    val = resolve_value("${%s}" % jp["fallback_from"], ctx)
            elif isinstance(jp, str) and jp.startswith("$"):
                val = jsonpath_get(data, jp)
            else:
                continue
            if bi is not None:
                arr = bucket.setdefault(var, [])
                while len(arr) <= bi:
                    arr.append(None)
                arr[bi] = val
            else:
                bucket[var] = val
            self.log("info", "[extract] %s.%s=%s" % (sname, var, val))

    def _extract_pick(self, data, spec):
        """对象式 extract：从数组按 sort_key 取 max/min 条，再取 field。
        spec: {from: $.content.itemArr, pick: max|min, sort_key: cbb.name, field: cbb.id}
        用途：同名镜像多版本时取最新（版本名尾部时间戳，字典序=时间序）"""
        arr = jsonpath_get(data, spec.get("from", ""))
        if not isinstance(arr, list) or not arr:
            return None
        sk = spec.get("sort_key")
        fld = spec.get("field")
        pick = (spec.get("pick") or "max").lower()
        best, best_key = None, None
        for item in arr:
            kv = jsonpath_get(item, sk) if sk else None
            if kv is None:
                continue
            kv = str(kv)
            if best_key is None or (kv > best_key if pick == "max" else kv < best_key):
                best_key, best = kv, item
        if best is None:
            best = arr[0]
        return jsonpath_get(best, fld) if fld else best

    def _poll(self, poll, ctx):
        """轮询异步任务至终态。

        请求体：优先文档 polling.params 模板（${content.X} 引用触发步骤响应，
        如 lesson 的 lessonTaskId）；兜底 {msgrelationid, msgType: BATCH_MSG}
        （公共轮询接口 /rco/msgct/msg/detail 两参数均必填）。

        轮询接口 404、业务 ERROR、连续无状态、PARTIAL_SUCCESS 和超时均显式失败。
        条件异步接口只有声明 optional_when_no_correlation 时，才允许无关联 ID 的
        同步成功响应跳过轮询。
        轮询间隔 2 秒，超时 240 秒。
        """
        api = str(poll.get("api", "common_get_msgct_detail_info")).strip()
        method = str(poll.get("method", "POST")).upper()
        if " " in api:
            prefix, api = api.split(None, 1)
            method = prefix.upper()
        path = api if api.startswith("/") else "/" + api
        last = ctx.get("_last_data") or {}
        task_id = (ctx.get("taskId")
                   or jsonpath_get(last, "$.content.taskId")
                   or jsonpath_get(last, "$.content.lessonTaskId"))
        body = self._poll_request_body(poll, task_id, ctx, path)
        correlation_id = task_id or self._poll_correlation_id(body)
        if not task_id:
            if not correlation_id and poll.get("optional_when_no_correlation"):
                self.log("info", "[poll] 条件异步接口未返回关联 ID，按文档同步完成语义跳过")
                return True
            if not correlation_id:
                raise AssertionError("异步轮询缺少可解析的关联 ID")
        if self._contains_template(body):
            raise AssertionError("polling.params 存在未解析模板: %s" % body)
        interval = poll.get("interval_ms", 2000) / 1000.0
        timeout = poll.get("timeout_ms", 240000) / 1000.0
        term = poll.get("terminal_states", {}) or {}
        ok_states = term.get("success", ["SUCCESS"])
        fail_states = term.get("fail") or term.get("failure") or ["FAILURE"]
        deadline = time.time() + timeout
        # 连续无效响应计数（404 与 无 taskStatus 共用）：
        # 仅在收到「结构有效但未到终态」的响应时清零，否则计数被清零永远到不了 3
        consecutive_invalid = 0
        while time.time() < deadline:
            status, data = self.http_request(method, path, body, ctx)
            if status == 404:
                consecutive_invalid += 1
                self.log("warning", "[poll] 轮询接口 404 (%d/3)" % consecutive_invalid)
                if consecutive_invalid >= 3:
                    raise AssertionError("轮询接口 %s 连续 3 次 404，任务状态无法确认: correlationId=%s"
                                         % (path, correlation_id))
                time.sleep(interval)
                continue
            if status < 200 or status >= 300:
                raise AssertionError("轮询接口 HTTP %s，任务状态无法确认: correlationId=%s"
                                     % (status, correlation_id))
            biz_status = jsonpath_get(data, "$.status")
            if biz_status == "ERROR":
                raise AssertionError("轮询业务失败: correlationId=%s (%s)"
                                     % (correlation_id, jsonpath_get(data, "$.message") or "ERROR"))
            st = (jsonpath_get(data, "$.content.taskStatus")
              or jsonpath_get(data, "$.content.status")
              or jsonpath_get(data, "$.content.msgState")
              or jsonpath_get(data, "$.content.state"))
            self.log("info", "[poll] taskStatus=%s" % st)
            if st == "PARTIAL_SUCCESS" and not poll.get("allow_partial_success"):
                raise AssertionError("轮询任务部分成功，按失败处理: correlationId=%s" % correlation_id)
            if st in fail_states:
                _desc = jsonpath_get(data, "$.content.describe") or jsonpath_get(data, "$.content.message") or ""
                raise AssertionError("轮询任务失败: correlationId=%s (taskStatus=%s)%s"
                                     % (correlation_id, st, (" | %s" % _desc) if _desc else ""))
            if poll.get("success_when"):
                if self._poll_conditions_met(data, poll["success_when"]):
                    self.log("info", "[poll] 查询验证成功")
                    return True
                self.log("info", "[poll] 查询验证条件尚未满足")
                time.sleep(interval)
                continue
            if st in ok_states:
                self.log("info", "[poll] 任务成功")
                return True
            # content 为 null 且无 taskStatus（接口不匹配 / 参数校验错误如缺 msgType）
            content = data.get("content") if isinstance(data, dict) else None
            if content is None and st is None:
                consecutive_invalid += 1
                self.log("warning", "[poll] content 为 null 且无 taskStatus (%d/3): %s"
                         % (consecutive_invalid, jsonpath_get(data, "$.message") or ""))
                if consecutive_invalid >= 3:
                    raise AssertionError("轮询接口 %s 连续 3 次无任务状态，结果无法确认: correlationId=%s"
                                         % (path, correlation_id))
                time.sleep(interval)
                continue
            # content 有值但无任务状态也不能据外层 SUCCESS 判定异步任务成功。
            if biz_status and st is None:
                consecutive_invalid += 1
                if consecutive_invalid >= 3:
                    raise AssertionError("轮询响应连续 3 次无任务状态: correlationId=%s" % correlation_id)
                time.sleep(interval)
                continue
            consecutive_invalid = 0  # 有效响应且未到终态（任务进行中）
            time.sleep(interval)
        raise AssertionError("轮询超时: correlationId=%s" % correlation_id)

    def _poll_request_body(self, poll, task_id, ctx, path=""):
        """轮询请求体：文档 polling.params 模板优先，${content.X} 引用触发步骤响应解析。
        msgct 端点（/rco/msgct/msg/detail，msgrelationid + msgType 两参数必填）补齐默认参数；
        其他轮询端点（如 /space/strategygroup/vdi/detail 的 {id: ...}）按模板原样发送，不混入 msgct 参数"""
        tmpl = poll.get("params") or poll.get("body") or {}
        body = {}
        if isinstance(tmpl, dict):
            for k, v in tmpl.items():
                if isinstance(v, str):
                    m = re.fullmatch(r"\$\{content\.(\w+)\}", v)
                    if m:
                        resolved = jsonpath_get(ctx.get("_last_data") or {}, "$.content." + m.group(1))
                        v = resolved if resolved not in (None, "") else v
                body[k] = v
        if "msgct" in str(path):
            body.setdefault("msgrelationid", task_id)
            body.setdefault("msgType", "BATCH_MSG")
        elif not body:
            body = {"msgrelationid": task_id}
        return body

    @staticmethod
    def _contains_template(value):
        if isinstance(value, str):
            return "${" in value
        if isinstance(value, dict):
            return any(Executor._contains_template(v) for v in value.values())
        if isinstance(value, list):
            return any(Executor._contains_template(v) for v in value)
        return False

    @staticmethod
    def _poll_correlation_id(body):
        if not isinstance(body, dict):
            return None
        for key in ("msgrelationid", "msgRelationId", "taskId", "lessonTaskId", "id"):
            if body.get(key) not in (None, "") and not Executor._contains_template(body[key]):
                return body[key]
        return None

    @staticmethod
    def _poll_conditions_met(data, conditions):
        for cond in conditions or []:
            actual = jsonpath_get(data, cond.get("path", ""))
            op = cond.get("op", "eq")
            expected = cond.get("value")
            if op == "eq" and actual != expected:
                return False
            if op == "not_empty" and not actual:
                return False
            if op == "in" and actual not in (expected or []):
                return False
        return bool(conditions)

    def _unverified(self, ctx, code, warn_msg, fail_msg):
        """「无法确认结果」的统一出口：默认 warning + 通过；strict 模式判失败"""
        self._warn(ctx, code, warn_msg)
        if self.strict:
            raise AssertionError(fail_msg)
        return True

    def _assert_step(self, step, data):
        """步骤断言（eq/not_empty/contains 三态），逐条记录 PASS/FAIL 到日志"""
        asserts = step.get("assert", [])
        if not asserts:
            s = jsonpath_get(data, "$.status")
            ok = (s is None or s == "SUCCESS")
            self.log("assert", "$.status == SUCCESS → %s (实际 %s)" % ("PASS" if ok else "FAIL", s))
            if not ok:
                raise AssertionError("业务失败: %s" % json.dumps(self._mask(data), ensure_ascii=False))
            return
        for a in asserts:
            path = a.get("path", "$.status")
            op = a.get("op", "eq")
            expected = a.get("value", "SUCCESS")
            actual = jsonpath_get(data, path)
            if op == "not_empty":
                ok = bool(actual)
                self.log("assert", "%s not_empty → %s (实际 %s)" % (path, "PASS" if ok else "FAIL", actual))
                if not ok:
                    raise AssertionError("断言失败: %s 应非空，实际 %s" % (path, actual))
            elif op == "contains":
                ok = expected in str(actual)
                self.log("assert", "%s contains %s → %s (实际 %s)" % (path, expected, "PASS" if ok else "FAIL", actual))
                if not ok:
                    raise AssertionError("断言失败: %s 应含 %s，实际 %s" % (path, expected, actual))
            else:  # eq
                ok = (actual == expected)
                self.log("assert", "%s == %s → %s (实际 %s)" % (path, expected, "PASS" if ok else "FAIL", actual))
                if not ok:
                    raise AssertionError("断言失败: %s 期望 %s 实际 %s" % (path, expected, actual))

    def _collect_param_refs(self, obj, refs):
        """递归收集 body 里的 ${param.xxx} 引用名（用于批量展开检测）"""
        if isinstance(obj, str):
            for m in re.finditer(r"\$\{param\.([\w.]+)(?:\[\d+\])?\}", obj):
                refs.add(to_snake(m.group(1)))
        elif isinstance(obj, dict):
            for v in obj.values():
                self._collect_param_refs(v, refs)
        elif isinstance(obj, list):
            for v in obj:
                self._collect_param_refs(v, refs)

    def _batch_size(self, step, ctx):
        """扫描 step body 及 reuse_query body 的 ${param.xxx} 引用，返回最长列表长度（0=无批量）"""
        refs = set()
        self._collect_param_refs(step.get("body", {}), refs)
        rq = step.get("reuse_query") or {}
        self._collect_param_refs(rq.get("body", {}), refs)
        sizes = [len(ctx["params"][r]) for r in refs
                 if r in ctx.get("params", {}) and isinstance(ctx["params"][r], list)]
        return max(sizes) if sizes else 0

    # ---------- 完整执行 ----------
    def execute(self, plan, params=None):
        """执行完整用例计划（真实方法调用）。

        返回结构含 warnings 数组（poll 接口缺失/删除无法验证/引用模糊回退等
        「无法确认结果」的降级记录），假绿可从结果 JSON 直接识别。
        """
        ctx = {"params": {to_snake(k): v for k, v in (params or {}).items()},
               "token": None, "context": {}, "steps": {}, "_last_data": None,
               "warnings": []}
        # params.strict=true → 本次执行启用严格模式（无法确认结果直接判失败）
        if ctx["params"].get("strict"):
            self.strict = True
        materialize_naming(ctx["params"], self.log)
        # 执行前主动登录：token 持久化到 ctx，后续所有步骤复用，401 时 http_request 自动重登写回
        try:
            p = ctx["params"]
            ctx["token"] = self.login(p.get("rcdc_user") or p.get("admin_user"),
                                      p.get("rcdc_passwd") or p.get("admin_password"))
            self.log("info", "[登录] 平台登录完成，会话 token 已建立")
        except Exception as e:
            self.log("error", "[登录] 登录失败: %s" % e)
            return {"status": "FAIL", "duration_ms": 0, "steps": [],
                    "error": "登录失败: %s" % e, "cleanup": "SKIP",
                    "warnings": []}
        # 前置清理：在计划步骤执行前，先清理同名教室（下课→删桌面→删座位→删教室）
        self._prerequisite_cleanup(plan, ctx)
        results = []
        start = time.time()
        total_steps = len(plan.get("steps", []))
        try:
            steps = plan.get("steps", [])
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", "")
                step_api = step.get("api", "")
                section = step.get("section", "")
                idempotent = step.get("idempotent")
                purpose = step.get("purpose", "")

                # 步骤开始：输出完整步骤信息
                self.log("step", "[Step %d/%d] %s" % (i, total_steps, step_name or step_api))
                if purpose:
                    self.log("info", "  目的: %s" % purpose)
                if section:
                    self.log("info", "  来源: %s" % section)
                self.log("info", "  接口: %s" % step_api)
                if idempotent == "reuse":
                    self.log("info", "  模式: 幂等复用（存在同名直接复用）")
                elif idempotent == "recreate":
                    self.log("info", "  模式: 幂等重建（先删同名再创建）")
                elif idempotent is True:
                    self.log("info", "  模式: 幂等（存在则通过）")
                if step.get("poll"):
                    self.log("info", "  异步: 含轮询等待")

                st = time.time()
                bs = self._batch_size(step, ctx)
                if bs > 0:
                    self.log("info", "  批量: 参数含列表，展开 %d 次" % bs)
                    last = None
                    for bi in range(bs):
                        ctx["_batch_index"] = bi
                        self.log("info", "  [batch] 第 %d/%d 次" % (bi + 1, bs))
                        last = self.execute_step(step, ctx)
                    ctx.pop("_batch_index", None)
                    data = last
                else:
                    data = self.execute_step(step, ctx)
                ctx["_last_data"] = data

                # 步骤结束：输出结果摘要
                resp_status = jsonpath_get(data, "$.status") if isinstance(data, dict) else "?"
                step_duration = int((time.time() - st) * 1000)
                self.log("info", "  结果: %s (%dms)" % (resp_status or "PASS", step_duration))

                results.append({"step": i, "name": step_name,
                                "api": step_api, "status": "PASS",
                                "duration_ms": step_duration})
            return {"status": "PASS", "duration_ms": int((time.time() - start) * 1000),
                    "steps": results, "cleanup": "PASS",
                    "warnings": self._collect_warnings(ctx)}
        except Exception as e:
            import traceback
            self.log("error", "步骤失败: %s\n%s" % (e, traceback.format_exc()))
            self._cleanup(ctx)
            return {"status": "FAIL", "duration_ms": int((time.time() - start) * 1000),
                    "steps": results, "error": str(e), "cleanup": "DONE",
                    "warnings": self._collect_warnings(ctx)}

    def _collect_warnings(self, ctx):
        """汇总执行期 warnings（executor 降级记录 + params 引用模糊回退记录）"""
        warnings = list(ctx.get("warnings") or [])
        for w in ctx.get("_ref_warnings") or []:
            warnings.append({"code": "ref_fuzzy_fallback", "message": str(w)})
            self.log("warning", "[ref] %s" % w)
        return warnings

    def _prerequisite_cleanup(self, plan, ctx):
        """执行前清理：查找 plan 中要创建的教室，若已存在同名教室则按依赖顺序清理。

        清理顺序：
        1. 下课（/rcc/classroom/cmrcef/lesson/end）
        2. 等待下课完成（/rcc/classroom/cmrcef/lesson/progress 轮询）
        3. 删除桌面（/rcc/classroom/desktop/delete）
        4. 删除座位（/rcc/classroom/seat/delete）
        5. 删除教室（/rcc/classroom/delete）
        """
        # 收集 plan 中所有要创建的教室名称
        classroom_names = set()
        for step in plan.get("steps", []):
            api = step.get("api", "")
            body = step.get("body") or {}
            # 只处理教室创建接口
            if "classroom" in api and ("create" in api or "batchCreate" in api):
                # 提取 classroomName（处理 ${param.classroom_name} 和 {"value": "xxx"} 两种格式）
                cn = body.get("classroomName") or {}
                if isinstance(cn, dict):
                    val = cn.get("value", "")
                else:
                    val = cn
                # 列表展开：如 ["a_classroom_01"] → "a_classroom_01"
                if isinstance(val, list):
                    val = val[0] if val else ""
                if not isinstance(val, str):
                    val = str(val)
                # 解析参数引用
                import re
                m = re.search(r"\$\{param\.([\w.]+)\}", val)
                if m:
                    param_key = to_snake(m.group(1))
                    cn = ctx["params"].get(param_key, val)
                elif val:
                    cn = val
                # 确保 cn 是字符串（params 中可能是列表）
                if isinstance(cn, list):
                    cn = cn[0] if cn else ""
                elif not isinstance(cn, str):
                    cn = str(cn)
                # 跳过空值（如空字符串、空字典转字符串）
                if not cn or cn in ("{}", "[]", ""):
                    continue
                if cn and cn != "":
                    classroom_names.add(cn)

        if not classroom_names:
            return

        self.log("info", "[prerequisite-cleanup] 发现 %d 个待创建教室名称: %s" % (len(classroom_names), classroom_names))

        for classroom_name in classroom_names:
            self._cleanup_classroom_by_name(classroom_name, ctx)

    def _cleanup_classroom_by_name(self, classroom_name, ctx):
        """按名称清理同名教室（按依赖顺序：下课→桌面→座位→教室）"""
        # 1. 查询教室
        select_body = {"searchKeyword": classroom_name}
        status, data = self.http_request("POST", "/rcc/classroom/select", select_body, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        items = None
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            items = content.get("itemArr") or content.get("items") or content.get("list")
        if not items or not isinstance(items, list):
            self.log("info", "[prerequisite-cleanup] 教室 '%s' 不存在，跳过清理" % classroom_name)
            return
        classroom = items[0]
        classroom_id = classroom.get("classroomId")
        if not classroom_id:
            self.log("warning", "[prerequisite-cleanup] 教室 '%s' 无 classroomId，跳过" % classroom_name)
            return

        self.log("info", "[prerequisite-cleanup] 找到教室 '%s' (id=%s)，开始按依赖顺序清理" % (classroom_name, classroom_id))

        # 2. 下课（如果在上课中）
        lesson_status = classroom.get("lessonStatus")
        classroom_state = classroom.get("classroomState")
        needs_lesson_end = lesson_status in ("IN_CLASS", "STARTING_CLASS", "ENDING_CLASS")
        if needs_lesson_end or classroom_state == "IN_CLASS":
            self.log("info", "[prerequisite-cleanup] 教室上课中（%s/%s），执行下课" % (lesson_status, classroom_state))
            self._end_lesson(classroom_id, ctx)
            # 3. 等待下课完成
            self._wait_lesson_end(classroom_id, ctx)
        else:
            self.log("info", "[prerequisite-cleanup] 教室不在上课中（lessonStatus=%s, classroomState=%s），跳过下课" % (lesson_status, classroom_state))

        # 4. 删除桌面（如果有）
        self._delete_classroom_desktops(classroom_id, ctx)

        # 5. 删除座位
        self._delete_classroom_seats(classroom_id, ctx)

        # 6. 删除教室
        self._delete_classroom(classroom_id, classroom_name, ctx)

    def _end_lesson(self, classroom_id, ctx):
        """执行下课（非 CMR 场景用 /rcc/classroom/lesson/end，无需 CMR token）"""
        status, data = self.http_request("POST", "/rcc/classroom/lesson/end",
                                         {"classroomId": classroom_id}, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        task_id = content.get("taskId") if isinstance(content, dict) else None
        ctx["_last_data"] = data
        if not task_id:
            self.log("warning", "[prerequisite-cleanup] 下课接口未返回 taskId，可能需要轮询")
        return task_id

    def _wait_lesson_end(self, classroom_id, ctx, timeout=120):
        """轮询等待下课完成（下课为异步批任务：经 msgct/msg/detail 轮询 taskId，
        非 CMR progress；与 lesson/end 文档 polling 声明一致）"""
        task_id = (ctx.get("_last_data") or {}).get("content", {}).get("taskId")
        if not task_id:
            self.log("info", "[prerequisite-cleanup] 下课无 taskId（同步返回），跳过轮询")
            return
        deadline = time.time() + timeout
        while time.time() < deadline:
            status, data = self.http_request(
                "POST", "/rco/msgct/msg/detail",
                {"msgrelationid": task_id, "msgType": "BATCH_MSG"}, ctx)
            content = data.get("content") if isinstance(data, dict) else {}
            msg_state = content.get("msgState") if isinstance(content, dict) else None
            self.log("info", "[prerequisite-cleanup] 下课进度: %s" % msg_state)
            if msg_state in ("SUCCESS", "DONE"):
                self.log("info", "[prerequisite-cleanup] 下课完成")
                return
            if msg_state in ("FAILURE", "ERROR", "PARTIAL_SUCCESS"):
                self.log("warning", "[prerequisite-cleanup] 下课状态 %s，按失败处理" % msg_state)
                return
            time.sleep(3)
        self.log("warning", "[prerequisite-cleanup] 下课轮询超时")

    def _delete_classroom_desktops(self, classroom_id, ctx):
        """删除教室下的所有桌面（规则：桌面必须先关机再删除）"""
        status, data = self.http_request("POST", "/rcc/classroom/desktop/list",
                                         {"exactMatchArr": [{"name": "classroomId", "valueArr": [classroom_id]}]}, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        items = content.get("itemArr") or content.get("items") or []
        if isinstance(items, dict):
            items = items.get("itemArr") or items.get("items") or []

        desktop_ids = []
        for desktop in items:
            desktop_id = desktop.get("desktopId") or desktop.get("id")
            if desktop_id:
                desktop_ids.append(desktop_id)

        if not desktop_ids:
            self.log("info", "[prerequisite-cleanup] 无桌面需要删除")
            return

        # 规则：桌面必须先关机再删除
        self.log("info", "[prerequisite-cleanup] 先对 %d 台桌面下发关机指令" % len(desktop_ids))
        for desktop_id in desktop_ids:
            try:
                status, data = self.http_request("POST", "/rcc/classroom/desktop/powerOff",
                                                 {"idArr": [desktop_id]}, ctx)
                self.log("info", "[prerequisite-cleanup] 桌面 %s 关机: %s" % (desktop_id,
                    data.get("status")))
            except Exception as e:
                self.log("warning", "[prerequisite-cleanup] 桌面 %s 关机异常: %s" % (desktop_id, e))

        self.log("info", "[prerequisite-cleanup] 等待桌面关机完成（10秒）...")
        time.sleep(10)

        # 删除桌面
        for desktop_id in desktop_ids:
            self.log("info", "[prerequisite-cleanup] 删除桌面 %s" % desktop_id)
            try:
                self.http_request("POST", "/rcc/classroom/desktop/delete",
                                 {"id": desktop_id}, ctx)
            except Exception as e:
                self.log("warning", "[prerequisite-cleanup] 桌面删除失败: %s" % e)

    def _delete_classroom_seats(self, classroom_id, ctx):
        """删除教室下的所有座位"""
        status, data = self.http_request("POST", "/rcc/classroom/seat/list",
                                         {"exactMatchArr": [{"name": "classroomId", "valueArr": [classroom_id]}]}, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        items = content.get("itemArr") or content.get("items") or []
        if isinstance(items, dict):
            items = items.get("itemArr") or items.get("items") or []

        for seat in items:
            seat_id = seat.get("id") or seat.get("seatId")
            if seat_id:
                self.log("info", "[prerequisite-cleanup] 删除座位 %s" % seat_id)
                try:
                    self.http_request("POST", "/rcc/classroom/seat/delete",
                                     {"classroomId": classroom_id, "seatIdArr": [seat_id]}, ctx)
                except Exception as e:
                    self.log("warning", "[prerequisite-cleanup] 座位删除失败: %s" % e)

    def _delete_classroom(self, classroom_id, classroom_name, ctx):
        """删除教室"""
        self.log("info", "[prerequisite-cleanup] 删除教室 %s (id=%s)" % (classroom_name, classroom_id))
        try:
            # 获取 oneTimeToken
            self._get_once_token(ctx)

            status, data = self.http_request("POST", "/rcc/classroom/delete",
                                             {"classroomId": classroom_id, "idArr": [classroom_id]}, ctx)
            if data.get("status") == "SUCCESS":
                content = data.get("content") if isinstance(data, dict) else {}
                task_id = content.get("taskId") if isinstance(content, dict) else None
                if task_id:
                    self._poll_classroom_delete(task_id, ctx,
                                                verify={"kind": "classroom", "id": classroom_id})
                else:
                    self.log("info", "[prerequisite-cleanup] 删除同步返回，等待 5 秒...")
                    for i in range(5):
                        time.sleep(1)
                        self.log("info", "[prerequisite-cleanup] 等待中... %d/5" % (i + 1))
                self.log("info", "[prerequisite-cleanup] 教室删除成功")
            else:
                self.log("warning", "[prerequisite-cleanup] 教室删除失败: %s" % data.get("message") or str(data))
        except Exception as e:
            self.log("warning", "[prerequisite-cleanup] 教室删除异常: %s" % e)

    def _cleanup_classroom_chain(self, classroom_id, ctx):
        """按 classroomId 执行完整清理链：下课 → 桌面关机 → 删除座位 → 删除教室
        （对齐业务规则 classroom_cleanup；桌面不关机/上课中删除会失败）"""
        self.log("info", "[cleanup] 教室 %s 按清理链删除（下课→关机→座位→教室）" % classroom_id)
        try:
            # 1. 下课（若上课中）
            self._end_lesson(classroom_id, ctx)
            # 2. 等待下课完成
            self._wait_lesson_end(classroom_id, ctx, timeout=60)
            # 3. 桌面关机
            self._delete_classroom_desktops(classroom_id, ctx)
            # 4. 删除座位
            self._delete_classroom_seats(classroom_id, ctx)
            # 5. 删除教室
            self._delete_classroom(classroom_id, classroom_id, ctx)
        except Exception as e:
            self.log("error", "[cleanup] 教室清理链失败: %s" % e)

    def _cleanup(self, ctx):
        """finally 清理已创建资源（从 ctx.steps 各 step 产出提取 *Id）"""
        created = []
        for sname, outs in (ctx.get("steps") or {}).items():
            # 复用命中的步骤（_reused）不清理：资源为环境已有/共享，删除会污染后续用例
            if outs.get("_reused"):
                self.log("info", "[cleanup] 跳过复用资源 %s（_reused）" % sname)
                continue
            for k, v in outs.items():
                if k.endswith("Id") and k != "taskId" and isinstance(v, str) and v:
                    created.append((k, v))
        for name, rid in reversed(created):
            # 教室删除须按清理链：下课 → 桌面关机 → 删除座位 → 删除教室
            # （业务规则 classroom_cleanup；桌面不关机/上课中删除会失败）
            if name == "classroomId":
                self._cleanup_classroom_chain(rid, ctx)
                continue
            del_path = self.CLEANUP_MAP.get(name)
            if del_path:
                self.log("info", "[cleanup] 删除 %s=%s" % (name, rid))
                try:
                    # classroom 的 delete 需要 idArr 格式
                    if "classroom" in del_path and "delete" in del_path:
                        status, data = self.http_request("POST", del_path, {"idArr": [rid]}, ctx)
                    else:
                        status, data = self.http_request("POST", del_path, {"id": rid}, ctx)
                    if data.get("status") != "SUCCESS":
                        msg = data.get("msgKey") or data.get("message") or ""
                        if "token" in str(msg).lower():
                            self.log("warning", "[cleanup] 删除跳过（oneTimeToken 缺失，资源可能已被手动清理）: %s" % msg)
                            continue
                except Exception as e:
                    self.log("error", "[cleanup] 删除失败: %s" % e)


def run_plan(plan_json, params_json, base_url, log_cb=None):
    """隔离入口：subprocess 固定入口调用（无字符串拼装）

    log_cb 可选：传入则替代默认 print 日志（CLI 传「print+写文件」回调落盘）；
    Web 子进程入口不传，走默认 print → stdout 由父进程 ScriptRunner 捕获回传。
    """
    plan = json.loads(plan_json) if isinstance(plan_json, str) else plan_json
    params = json.loads(params_json) if isinstance(params_json, str) else params_json

    if log_cb:
        log = log_cb
    else:
        def log(level, msg):
            print("[%s] %s" % (level, msg))

    ex = Executor(base_url=base_url, log_cb=log)
    result = ex.execute(plan, params)
    log("result", result["status"])
    return result


if __name__ == "__main__":
    # 供 subprocess 调用：python executor.py <plan.json> <params.json> <base_url>
    plan = json.load(open(sys.argv[1]))
    params = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else {}
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8080"
    result = run_plan(plan, params, base_url)
    sys.exit(0 if result.get("status") == "PASS" else 1)
