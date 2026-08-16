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

from .jsonpath import jsonpath_get
from .params import resolve_body, gen_config_value, to_snake, materialize_naming

# 目标环境为自签 HTTPS 证书，禁用 SSL 证书验证告警（verify=False 时的 InsecureRequestWarning）
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


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
        """
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
                token = self.login(p.get("rcdc_user") or p.get("admin_user"),
                                   p.get("rcdc_passwd") or p.get("admin_password"))
                ctx["token"] = token
                headers["iac-token"] = token
                if cookies is not None:
                    cookies = {"iac-token": token, "rcdcAdmin-Token": token}
                resp = session.request(method, url, json=body, headers=headers,
                                       cookies=cookies, timeout=30, verify=False)
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                self.log("resp", "HTTP %s（重试）" % resp.status_code)
            return resp.status_code, data
        except Exception as e:
            self.log("error", "请求失败: %s" % e)
            return 0, {"status": "ERROR", "message": str(e)}

    def login(self, admin_user=None, admin_password=None):
        """框架内置登录（loginAdmin）。凭据优先参数传入，其次环境变量，缺失则报错（不留明文默认）。"""
        admin_user = admin_user or os.environ.get("TEST_ADMIN_USER")
        admin_password = admin_password or os.environ.get("TEST_ADMIN_PASSWORD")
        if not admin_user or not admin_password:
            raise RuntimeError(
                "缺少登录凭据：请在用例参数 rcdc_user/rcdc_passwd（或 admin_user/admin_password）"
                "或环境变量 TEST_ADMIN_USER/TEST_ADMIN_PASSWORD 中提供"
            )
        import time as _time
        body = {
            "userName": admin_user,
            "pwd": admin_password,
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
        body = resolve_body(step.get("body", {}), ctx)
        self.log("info", "[step] %s resolved body: %s" % (
            step.get("step_name") or step.get("name") or "",
            json.dumps(self._mask(body), ensure_ascii=False)))

        # 登录内置
        if "loginAdmin" in api:
            p = ctx["params"]
            ctx["token"] = self.login(p.get("rcdc_user") or p.get("admin_user"),
                                      p.get("rcdc_passwd") or p.get("admin_password"))
            ctx["context"] = {"token": ctx["token"]}
            return {"status": "SUCCESS", "content": {"token": ctx["token"]}}

        # 幂等 reuse：存在同名直接复用、跳过创建（用于策略/镜像等环境已有资源）
        if step.get("idempotent") == "reuse" and step.get("reuse_query"):
            reused = self._try_reuse(step, ctx)
            if reused is not None:
                return reused

        # 幂等 recreate：先删同名再建
        if step.get("idempotent") == "recreate" and step.get("delete_api"):
            self._recreate(step, path, body, ctx)

        # 幂等 true：先尝试创建（存在则幂等通过）
        if step.get("idempotent") is True:
            status, data = self.http_request(method, path, body or None, ctx)
            if jsonpath_get(data, "$.status") == "SUCCESS":
                self.log("info", "[idempotent] 创建成功或已存在")
            return data

        status, data = self.http_request(method, path, body or None, ctx)

        # extract 产出（多变量）
        self._extract(step, data, ctx)

        # polling 异步任务
        if step.get("poll") and status in (200, 201):
            self._poll(step["poll"], ctx)

        # 断言
        self._assert_step(step, data)
        return data

    def _recreate(self, step, path, body, ctx):
        """幂等 recreate：存在同名先调 delete_api 删除再创建"""
        del_api = step["delete_api"]
        del_path = del_api.split(" ", 1)[-1] if " " in del_api else del_api
        status, data = self.http_request("POST", path, body or None, ctx)
        found_id = jsonpath_get(data, "$.content.id") or jsonpath_get(data, "$.content.classroomId")
        if found_id:
            self.log("info", "[recreate] 存在同名资源 %s，先删除" % found_id)
            self.http_request("POST", del_path, {"id": found_id}, ctx)

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
        """轮询异步任务至终态"""
        api = poll.get("api", "common_get_msgct_detail_info")
        path = api if api.startswith("/") else "/" + api
        task_id = ctx.get("taskId") or jsonpath_get(ctx.get("_last_data") or {}, "$.content.taskId")
        interval = poll.get("interval_ms", 2000) / 1000.0
        timeout = poll.get("timeout_ms", 120000) / 1000.0
        ok_states = poll.get("terminal_states", {}).get("success", ["SUCCESS"])
        fail_states = poll.get("terminal_states", {}).get("fail", ["FAILURE"])
        deadline = time.time() + timeout
        while time.time() < deadline:
            status, data = self.http_request("POST", path, {"msgrelationid": task_id}, ctx)
            st = jsonpath_get(data, "$.content.taskStatus") or jsonpath_get(data, "$.content.status")
            self.log("info", "[poll] taskStatus=%s" % st)
            if st in ok_states:
                self.log("info", "[poll] 任务成功")
                return True
            if st in fail_states:
                raise AssertionError("轮询任务失败: taskId=%s" % task_id)
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
        results = []
        start = time.time()
        try:
            steps = plan.get("steps", [])
            for i, step in enumerate(steps, 1):
                self.log("step", "[Step%d] %s %s" % (i, step.get("name", ""), step.get("api", "")))
                st = time.time()
                bs = self._batch_size(step, ctx)
                if bs > 0:
                    self.log("info", "[batch] 参数含列表，展开 %d 次" % bs)
                    last = None
                    for bi in range(bs):
                        ctx["_batch_index"] = bi
                        self.log("info", "[batch] 第 %d/%d 次" % (bi + 1, bs))
                        last = self.execute_step(step, ctx)
                    ctx.pop("_batch_index", None)
                    data = last
                else:
                    data = self.execute_step(step, ctx)
                ctx["_last_data"] = data
                results.append({"step": i, "name": step.get("name", ""),
                                "api": step.get("api", ""), "status": "PASS",
                                "duration_ms": int((time.time() - st) * 1000)})
            return {"status": "PASS", "duration_ms": int((time.time() - start) * 1000),
                    "steps": results, "cleanup": "PASS"}
        except Exception as e:
            import traceback
            self.log("error", "步骤失败: %s\n%s" % (e, traceback.format_exc()))
            self._cleanup(ctx)
            return {"status": "FAIL", "duration_ms": int((time.time() - start) * 1000),
                    "steps": results, "error": str(e), "cleanup": "DONE"}

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
                    self.http_request("POST", del_path, {"id": rid}, ctx)
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
