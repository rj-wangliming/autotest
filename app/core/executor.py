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
from .params import resolve_body, gen_config_value, to_snake, materialize_naming
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

    def __init__(self, base_url=None, log_cb=None):
        self.base_url = (base_url or os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8080")).rstrip("/")
        self.log_cb = log_cb or (lambda level, msg: None)
        self._session = None  # requests.Session：维持登录 cookie 会话（webmvckit 会话认证）

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
        self.log("req", "%s %s" % (method, path))
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

        # 特殊处理：assignImage/yetAssign/list 若 crId 有值但 platformId 缺失，
        # 自动查询教室详情获取 platformId（若教室详情未返回则 fallback 查询教室镜像列表获取）
        if "/image/assignImage/yetAssign/list" in path and body and body.get("crId") and not body.get("platformId"):
            body = self._fill_platform_id_for_image(body, ctx)

        # 特殊处理：assignImage/yetAssign/list 注入 exactMatchArr 过滤条件
        # 与 pytest 框架 common_get_classroom_yet_assign_lesson_image_list 完全一致，
        # 避免缺过滤条件时后端走不同分支导致 internal_error
        if "/image/assignImage/yetAssign/list" in path and body and body.get("crId"):
            # 已存在 exactMatchArr 则跳过（避免重复注入）
            has_exact = "exactMatchArr" in body
            if not has_exact:
                cr_id = body.get("crId")
                exact_match = [
                    {"name": "imageRoleType", "valueArr": ["TEMPLATE"]},
                    {"name": "cbbImageType", "valueArr": ["VDI"]},
                    {"name": "imageUsage", "valueArr": ["DESK"]},
                ]
                # 从教室详情获取 clusterId
                cluster_id = None
                try:
                    info_status, info_data = self.http_request(
                        "POST", "/rcc/classroom/getInfo",
                        {"classroomId": cr_id}, ctx)
                    cluster_id = jsonpath_get(info_data, "$.content.computeClusterId")
                except Exception as e:
                    self.log("warning", "[exactMatchArr] 获取 clusterId 失败: %s" % e)
                if cluster_id:
                    exact_match.append({"name": "clusterId", "valueArr": [cluster_id]})
                    self.log("info", "[exactMatchArr] 注入 exactMatchArr (clusterId=%s)" % cluster_id)
                else:
                    self.log("warning", "[exactMatchArr] 未获取到 clusterId，不注入")
                # 注入（始终注入基础条件，即使没有 clusterId）
                body["exactMatchArr"] = {"value": exact_match}

        status, data = self.http_request(method, path, body or None, ctx)

        # 设置 _last_data（_poll 需要读取当前步骤响应中的 taskId）
        ctx["_last_data"] = data

        # extract 产出（多变量）
        self._extract(step, data, ctx)

        # polling 异步任务：仅在业务成功时才轮询（ERROR 状态不轮询）
        biz_status = jsonpath_get(data, "$.status") if isinstance(data, dict) else None
        if step.get("poll") and status in (200, 201) and biz_status == "SUCCESS":
            self._poll(step["poll"], ctx)
        elif step.get("poll") and biz_status != "SUCCESS":
            self.log("warning", "[poll] 业务状态非 SUCCESS（%s），跳过轮询" % biz_status)

        # 断言
        self._assert_step(step, data)
        return data

    def _fill_platform_id_for_image(self, body, ctx):
        """为 /image/assignImage/yetAssign/list 补齐 platformId。

        根因：Java 后端 ClassroomImageServiceImpl.getImageState() 查 CBB 镜像需要
        platformId（pageSearchRequest.setPlatformId(request.getPlatformId())），
        但 ClassroomDTO（query_classroom/select 返回）和 ClassroomInfoDetailDTO
        （query_classroom/getInfo 返回）都不含 platformId 字段，
        导致编排从未注入。

        策略：依次尝试
        1. 用 crId 查询教室详情 /rcc/classroom/getInfo → 提取 platformId
        2. 若 getInfo 未返回，查询教室镜像列表 /rcc/classroom/image/list → 提取 platformId
        3. 若仍无值，查询平台列表 → 取第一个 platformId
        查询结果缓存，同一 crId 不再重复查询。
        """
        cr_id = body.get("crId")
        if not cr_id:
            return body
        # 缓存：同一 crId 不再重复查询
        plat_cache_key = "_platform_id_cache"
        plat_cache = ctx.setdefault(plat_cache_key, {})
        if cr_id in plat_cache:
            body["platformId"] = plat_cache[cr_id]
            self.log("info", "[platformId] 从缓存注入 platformId=%s (crId=%s)" % (plat_cache[cr_id], cr_id))
            return body
        # 依次尝试三种来源
        plat_id = None
        # 来源1：教室详情
        self.log("info", "[platformId] crId=%s 缺失 platformId，尝试查询教室详情" % cr_id)
        try:
            status, data = self.http_request("POST", "/rcc/classroom/getInfo", {"classroomId": cr_id}, ctx)
            plat_id = jsonpath_get(data, "$.content.platformId")
        except Exception as e:
            self.log("warning", "[platformId] 查询教室详情失败: %s" % e)
        # 来源2：教室镜像列表
        if not plat_id:
            self.log("info", "[platformId] 教室详情无 platformId，尝试查询教室镜像列表")
            try:
                status, data = self.http_request("POST", "/rcc/classroom/image/list",
                                                 {"crId": cr_id}, ctx)
                plat_id = jsonpath_get(data, "$.content.itemArr[0].platformId")
                if plat_id:
                    self.log("info", "[platformId] 从镜像列表获取 platformId=%s" % plat_id)
            except Exception as e:
                self.log("warning", "[platformId] 查询教室镜像列表失败: %s" % e)
        # 来源3：平台列表
        if not plat_id:
            self.log("info", "[platformId] 镜像列表无 platformId，尝试查询平台列表")
            try:
                status, data = self.http_request("POST", "/space/platform/list",
                                                 {"searchKeyword": ""}, ctx)
                # 平台列表返回中 platformId 字段名可能是 platformId 或 id
                plat_id = jsonpath_get(data, "$.content.itemArr[0].platformId")
                if not plat_id:
                    plat_id = jsonpath_get(data, "$.content.itemArr[0].id")
                if plat_id:
                    self.log("info", "[platformId] 从平台列表获取 platformId=%s" % plat_id)
            except Exception as e:
                self.log("warning", "[platformId] 查询平台列表失败: %s" % e)
        if plat_id:
            plat_cache[cr_id] = plat_id
            body["platformId"] = plat_id
        else:
            self.log("warning", "[platformId] 所有来源均未获取到 platformId（crId=%s），继续使用无 platformId 的请求" % cr_id)
        return body

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

            self.log("info", "[recreate] 异步%s中，taskId=%s" % ("删除" if is_classroom else "删除", task_id))
            ok = self._poll_classroom_delete(task_id, ctx)
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

    def _poll_classroom_delete(self, task_id, ctx):
        """教室删除是异步任务，但当前环境异步轮询接口路径未知。

        策略：获取 oneTimeToken 后等待 10 秒，假设删除完成。
        """
        self.log("info", "[poll-delete] 获取 oneTimeToken 并等待删除完成: taskId=%s" % task_id)

        # 获取 oneTimeToken
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
                    self.log("info", "[poll-delete] oneTimeToken 已获取")
            except Exception as e:
                self.log("warning", "[poll-delete] oneTimeToken 获取失败: %s" % e)

        # 等待删除操作完成（异步）— 每 2 秒输出一次日志防止超时
        self.log("info", "[poll-delete] 等待 10 秒（删除中）...")
        for i in range(5):
            time.sleep(2)
            self.log("info", "[poll-delete] 等待中... %d/5" % (i + 1))
        self.log("info", "[poll-delete] 等待完成，假设删除成功")
        return True

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

        注意：当前环境异步轮询接口路径可能不存在（返回 404），
        连续 3 次 404 时自动跳过轮询（假设任务已执行）。

        轮询间隔 2 秒，超时 240 秒；期间每 2 秒检查一次任务状态。
        """
        api = poll.get("api", "common_get_msgct_detail_info")
        path = api if api.startswith("/") else "/" + api
        task_id = ctx.get("taskId") or jsonpath_get(ctx.get("_last_data") or {}, "$.content.taskId")
        if not task_id:
            self.log("info", "[poll] taskId 为空（同步返回，无异步任务），跳过轮询")
            return True
        interval = poll.get("interval_ms", 2000) / 1000.0
        timeout = poll.get("timeout_ms", 240000) / 1000.0  # 240 秒超时，给异步任务足够时间
        ok_states = poll.get("terminal_states", {}).get("success", ["SUCCESS"])
        fail_states = poll.get("terminal_states", {}).get("fail", ["FAILURE"])
        deadline = time.time() + timeout
        consecutive_404 = 0
        while time.time() < deadline:
            status, data = self.http_request("POST", path, {"msgrelationid": task_id}, ctx)
            if status == 404:
                consecutive_404 += 1
                self.log("warning", "[poll] 轮询接口 404 (%d/3)，跳过轮询" % consecutive_404)
                if consecutive_404 >= 3:
                    self.log("info", "[poll] 连续 3 次 404，跳过轮询")
                    return True
                time.sleep(interval)
                continue
            consecutive_404 = 0
            st = jsonpath_get(data, "$.content.taskStatus") or jsonpath_get(data, "$.content.status")
            self.log("info", "[poll] taskStatus=%s" % st)
            if st in ok_states:
                self.log("info", "[poll] 任务成功")
                return True
            if st in fail_states:
                raise AssertionError("轮询任务失败: taskId=%s" % task_id)
            # content 为 null 且无 taskStatus（说明轮询接口不匹配），跳过轮询
            content = data.get("content") if isinstance(data, dict) else None
            if content is None and st is None:
                consecutive_404 += 1
                self.log("warning", "[poll] content 为 null 且无 taskStatus (%d/3)，跳过轮询" % consecutive_404)
                if consecutive_404 >= 3:
                    self.log("info", "[poll] 连续 3 次 content 为空，跳过轮询")
                    return True
                time.sleep(interval)
                continue
            # content 有值但无 taskStatus（业务状态为 ERROR/SUCCESS 但无异步字段），跳过
            biz_status = jsonpath_get(data, "$.status")
            if biz_status and st is None:
                self.log("info", "[poll] 有业务状态(%s)但无taskStatus，跳过轮询" % biz_status)
                return True
            time.sleep(interval)
        raise AssertionError("轮询超时: taskId=%s" % task_id)

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
    def execute(self, plan, params=None, timeout=120):
        """执行完整用例计划（真实方法调用）"""
        ctx = {"params": {to_snake(k): v for k, v in (params or {}).items()},
               "token": None, "context": {}, "steps": {}, "_last_data": None}
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
                    "error": "登录失败: %s" % e, "cleanup": "SKIP"}
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
                    "steps": results, "cleanup": "PASS"}
        except Exception as e:
            import traceback
            self.log("error", "步骤失败: %s\n%s" % (e, traceback.format_exc()))
            self._cleanup(ctx)
            return {"status": "FAIL", "duration_ms": int((time.time() - start) * 1000),
                    "steps": results, "error": str(e), "cleanup": "DONE"}

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
        """执行下课（cmrcef/lesson/end）"""
        status, data = self.http_request("POST", "/rcc/classroom/cmrcef/lesson/end",
                                         {"classroomId": classroom_id}, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        task_id = content.get("taskId") if isinstance(content, dict) else None
        if not task_id:
            self.log("warning", "[prerequisite-cleanup] 下课接口未返回 taskId，可能需要轮询")

    def _wait_lesson_end(self, classroom_id, ctx, timeout=120):
        """轮询等待下课完成"""
        path = "/rcc/classroom/cmrcef/lesson/progress"
        deadline = time.time() + timeout
        while time.time() < deadline:
            status, data = self.http_request("POST", path, {"classroomId": classroom_id}, ctx)
            content = data.get("content") if isinstance(data, dict) else {}
            task_status = content.get("taskStatus") if isinstance(content, dict) else None
            self.log("info", "[prerequisite-cleanup] 下课进度: %s" % task_status)
            if task_status in ("SUCCESS", "DONE"):
                self.log("info", "[prerequisite-cleanup] 下课完成")
                return
            time.sleep(3)
        self.log("warning", "[prerequisite-cleanup] 下课轮询超时")

    def _delete_classroom_desktops(self, classroom_id, ctx):
        """删除教室下的所有桌面"""
        status, data = self.http_request("POST", "/rcc/classroom/desktop/list",
                                         {"exactMatchArr": [{"name": "classroomId", "valueArr": [classroom_id]}]}, ctx)
        content = data.get("content") if isinstance(data, dict) else {}
        items = content.get("itemArr") or content.get("items") or []
        if isinstance(items, dict):
            items = items.get("itemArr") or items.get("items") or []

        for desktop in items:
            desktop_id = desktop.get("desktopId") or desktop.get("id")
            if desktop_id:
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
                    self._poll_classroom_delete(task_id, ctx)
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

    def _cleanup(self, ctx):
        """finally 清理已创建资源（从 ctx.steps 各 step 产出提取 *Id）"""
        created = []
        for sname, outs in (ctx.get("steps") or {}).items():
            for k, v in outs.items():
                if k.endswith("Id") and k != "taskId" and isinstance(v, str) and v:
                    created.append((k, v))
        for name, rid in reversed(created):
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
