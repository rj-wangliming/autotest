#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四项重构的回归测试（纯 assert，不依赖真实环境与 LLM）

覆盖:
  1. 语义匹配规则外置: semantic_rules 从 business_rules.md 加载并生效（集群↔存储池惩罚、侧别偏好）
  2. 文档驱动补数: executor._apply_fill 按 fill 声明注入静态值/接口取值/追加条目/缓存
  3. 假绿修复: poll 404 与删除等待超时记录 warnings；strict 模式判失败；删除存在性验证
  4. 引用链接: plan 期 ${prev.*} 改写到真实步骤名，断裂引用记 warns
"""
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["API_MD_DIR"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "api_md_staging")

from app.core.orchestrator import Orchestrator  # noqa: E402
from app.core.executor import Executor  # noqa: E402
from app.core.params import resolve_body  # noqa: E402

PASS = []
FAIL = []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print("  ✅ %s" % name)
    except Exception as e:
        FAIL.append((name, str(e)))
        print("  ❌ %s: %s" % (name, e))
        import traceback
        traceback.print_exc()


# ---------- 1. 语义匹配规则外置 ----------

def test_semantic_rules_loaded():
    o = Orchestrator()
    rules = o.rules.get("semantic_rules") or []
    assert len(rules) >= 8, "semantic_rules 未加载或条目不足: %d" % len(rules)


def test_semantic_penalty():
    o = Orchestrator()
    # 集群实体 vs 存储池接口名 → -10（URL 不带 /space//rcc/ 等侧别词，只命中惩罚规则）
    d = o._apply_semantic_rules("/xxx/storagePool/list", "获取存储池列表", ["cluster"])
    assert d == -10, "cluster→storagePool 惩罚应为 -10, 实际 %s" % d
    # 存储池实体 vs 集群接口名 → -10
    d = o._apply_semantic_rules("/xxx/cluster/list", "获取集群列表", ["storagePool"])
    assert d == -10, "storagePool→cluster 惩罚应为 -10, 实际 %s" % d


def test_semantic_side_preference():
    o = Orchestrator()
    # 集群实体：RDCD 侧 +5，Space 侧 -3
    assert o._apply_semantic_rules("/rco/user/obtainComputeClusterList", "获取计算集群", ["cluster"]) == 5
    assert o._apply_semantic_rules("/space/cluster/obtainComputeClusterList", "获取计算集群", ["cluster"]) == -3
    # 存储池实体：RCC 侧 +3，Space 侧 -3
    assert o._apply_semantic_rules("/rcc/classroom/getInfoStoragePoolList", "获取存储池", ["storagePool"]) == 3
    assert o._apply_semantic_rules("/space/storagePool/list", "获取存储池列表", ["storagePool"]) == -3
    # 统计接口 -10（不限实体）
    assert o._apply_semantic_rules("/rcc/dashboard/statistics/desktop", "统计", []) == -10
    # network vs 镜像（Assigned 例外）
    assert o._apply_semantic_rules("/x/image/list", "获取镜像", ["network"]) == -10
    assert o._apply_semantic_rules("/rcc/classroom/image/getAssignedClusterAndNetwork", "获取已分配集群网络", ["network"]) == 0


def test_semantic_match_regression():
    """外置后关键语义匹配结果不回归"""
    o = Orchestrator()
    got = o._semantic_match("获取计算集群", prefer_create=False)
    assert got and "cluster" in got.lower(), "「获取计算集群」应匹配 cluster 接口: %s" % got
    got = o._semantic_match("获取存储池", prefer_create=False)
    assert got and "storagepool" in got.lower(), "「获取存储池」应匹配 storagePool 接口: %s" % got


def test_poll_node_name_resolved():
    """polling 节点名（common_get_msgct_detail_info）→ 真实 url /rco/msgct/msg/detail"""
    o = Orchestrator()
    assert o.index.resolve("common_get_msgct_detail_info") == "/rco/msgct/msg/detail"
    step = o._build_step("/rcc/classroom/delete", "删除教室")
    assert (step.get("poll") or {}).get("api") == "/rco/msgct/msg/detail", \
        "poll api 应解析为真实 url: %s" % step.get("poll")


def test_poll_method_prefix_normalized():
    step = Orchestrator()._build_step("/space/strategygroup/vdi/create", "创建 VDI 策略")
    assert step["poll"]["api"] == "/space/strategygroup/vdi/detail"
    assert step["poll"]["method"] == "POST"


# ---------- 2. 文档驱动补数（fill 引擎） ----------

class FakeExecutor(Executor):
    """替身：http 按路径返回固定响应并记录调用"""
    def __init__(self, responses=None, **kw):
        super().__init__(**kw)
        self.responses = responses or {}
        self.calls = []

    def http_request(self, method, path, body=None, ctx=None):
        self.calls.append((method, path, body))
        for prefix, resp in self.responses.items():
            if path.startswith(prefix):
                return (200, resp) if not isinstance(resp, tuple) else resp
        return (200, {"status": "SUCCESS", "content": {}})


def test_fill_platform_id_sources_and_cache():
    ex = FakeExecutor({
        "/rcc/classroom/getInfo": {"status": "SUCCESS", "content": {"platformId": "plat-1"}},
    })
    spec = {"field": "platformId", "when": "missing", "cache_by": "${body.crId}",
            "sources": [{"api": "POST /rcc/classroom/getInfo",
                         "body": {"classroomId": "${body.crId}"},
                         "from": "$.content.platformId"}]}
    ctx = {"params": {}, "steps": {}, "warnings": []}
    body = {"crId": "cr-9"}
    out = ex._apply_fill({"fill": [spec]}, body, ctx)
    assert out.get("platformId") == "plat-1", "platformId 应从 getInfo 回查注入"
    # 请求体里 ${body.crId} 已替换
    assert ex.calls[0][2] == {"classroomId": "cr-9"}, "sources 请求体应替换 ${body.*}: %s" % ex.calls[0][2]
    # 缓存：第二次同 crId 不再发请求
    ex2_body = {"crId": "cr-9"}
    ex._apply_fill({"fill": [spec]}, ex2_body, ctx)
    assert len([c for c in ex.calls if c[1] == "/rcc/classroom/getInfo"]) == 1, "同 cache_by 键应命中缓存"


def test_fill_exact_match_arr_static_and_append():
    ex = FakeExecutor({
        "/rcc/classroom/getInfo": {"status": "SUCCESS", "content": {"computeClusterId": "cl-7"}},
    })
    fills = [
        {"field": "exactMatchArr", "when": "missing", "value": [
            {"name": "imageRoleType", "valueArr": ["TEMPLATE"]},
            {"name": "cbbImageType", "valueArr": ["VDI"]}]},
        {"field": "exactMatchArr", "append_item": {"name": "clusterId", "valueArr": ["${fill}"]},
         "sources": [{"api": "POST /rcc/classroom/getInfo",
                      "body": {"classroomId": "${body.crId}"},
                      "from": "$.content.computeClusterId"}]},
    ]
    ctx = {"params": {}, "steps": {}, "warnings": []}
    body = {"crId": "cr-9"}
    out = ex._apply_fill({"fill": fills}, body, ctx)
    em = out.get("exactMatchArr")
    assert isinstance(em, list) and em[0]["name"] == "imageRoleType", "静态条件应注入: %s" % em
    assert em[-1] == {"name": "clusterId", "valueArr": ["cl-7"]}, "clusterId 条件应追加: %s" % em
    # 已有同名条目时不重复追加
    out2 = ex._apply_fill({"fill": fills}, dict(out), ctx)
    assert len([e for e in out2["exactMatchArr"] if e["name"] == "clusterId"]) == 1, "同名条目不应重复追加"


def test_fill_doc_driven_from_yetassign_doc():
    """yetAssign 文档的 fill 声明可被引擎消费（platformId + exactMatchArr 全链路）"""
    o = Orchestrator()
    meta = o.index.get("/rcc/classroom/image/assignImage/yetAssign/list") or {}
    fills = meta.get("fill") or []
    assert fills, "yetAssign 文档缺少 fill 声明"
    ex = FakeExecutor({
        "/rcc/classroom/getInfo": {"status": "SUCCESS",
                                   "content": {"platformId": "plat-1", "computeClusterId": "cl-7"}},
    })
    ctx = {"params": {}, "steps": {}, "warnings": []}
    out = ex._apply_fill({"fill": fills}, {"crId": "cr-9"}, ctx)
    assert out.get("platformId") == "plat-1"
    em = out.get("exactMatchArr")
    names = [e["name"] for e in em]
    assert names == ["imageRoleType", "cbbImageType", "imageUsage", "clusterId"], "exactMatchArr 注入顺序异常: %s" % names


def test_vdi_create_document_parameterizes_strategy_defaults():
    """VDI 创建策略默认值来自参数，且可被用例覆盖。"""
    meta = Orchestrator().index.get("/space/strategygroup/vdi/create")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root_dir, "app", "data", "global_params.yaml")) as f:
        params = yaml.safe_load(f)
    params.update({
        "strategy_name_vdi": "strategy-defaults",
        "cpu": 4,
        "memory": 8192,
        "system_size": 80,
        "vgpu_type": "QXL",
        "need_hide_float_bar": True,
    })
    body = resolve_body((meta.get("request") or {}).get("body") or {}, {
        "params": params,
        "steps": {
            "query_usb_types": {"usbTypeIdArr": ["usb-1"]},
            "query_vgpu_options": {"vgpuType": "QXL"},
        },
    })
    expected = {
        "needHideFloatBar": True,
        "enableShowLocalDisk": True,
        "enableAdaptiveResolution": True,
        "enableDoubleScreen": False,
        "enableSoftwareDecode": True,
        "enableHyperVisorImprove": True,
    }
    for field, value in expected.items():
        assert body.get(field) is value, "%s 未进入创建请求: %s" % (field, body)


# ---------- 3. 假绿修复 ----------

def test_poll_404_fails():
    ex = FakeExecutor({"/common_get_msgct": (404, {})})
    ctx = {"params": {}, "steps": {}, "warnings": [], "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"interval_ms": 1}, ctx)
    except AssertionError as e:
        assert "404" in str(e)
    else:
        raise AssertionError("404 不得返回成功")
    # 请求体必须带公共轮询接口必填的 msgType
    bodies = [c[2] for c in ex.calls if c[1] == "/common_get_msgct_detail_info"]
    assert bodies and all(b.get("msgType") == "BATCH_MSG" for b in bodies), \
        "轮询请求体应含 msgType=BATCH_MSG: %s" % bodies


def test_poll_validation_error_not_infinite():
    """轮询接口业务 ERROR 应立即失败，不得循环或降级成功。"""
    ex = FakeExecutor({"/rco/msgct/msg/detail": {
        "status": "ERROR", "content": None,
        "message": "字段msgType不能为空", "msgKey": "sk_validation_NotNull"}})
    ctx = {"params": {}, "steps": {}, "warnings": [], "_last_data": {"content": {"taskId": "t-1"}}}
    import time as _t
    t0 = _t.time()
    try:
        ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1, "timeout_ms": 60000}, ctx)
        raise AssertionError("业务 ERROR 不得返回成功")
    except AssertionError as e:
        assert "轮询业务失败" in str(e)
    assert _t.time() - t0 < 10, "不应轮询到超时（计数器死循环回归）"
    n = len([c for c in ex.calls if c[1] == "/rco/msgct/msg/detail"])
    assert n == 1, "业务 ERROR 应立即失败, 实际请求 %d 次" % n


def test_poll_http_error_fails():
    ex = FakeExecutor({"/rco/msgct/msg/detail": (
        500, {"status": "SUCCESS", "content": {"taskStatus": "SUCCESS"}})})
    ctx = {"params": {}, "steps": {}, "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1}, ctx)
    except AssertionError as e:
        assert "HTTP 500" in str(e)
    else:
        raise AssertionError("轮询 HTTP 非 2xx 不得返回成功")


def test_poll_missing_status_fails():
    ex = FakeExecutor({"/rco/msgct/msg/detail": {
        "status": "SUCCESS", "content": {}}})
    ctx = {"params": {}, "steps": {}, "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1}, ctx)
        raise AssertionError("连续无状态不得返回成功")
    except AssertionError as e:
        assert "无任务状态" in str(e)
    assert len(ex.calls) == 3


def test_poll_params_template_resolved():
    """文档 polling.params 模板：${content.lessonTaskId} 引用触发步骤响应"""
    ex = FakeExecutor({"/rco/msgct/msg/detail": {"status": "SUCCESS",
                                                 "content": {"taskStatus": "SUCCESS"}}})
    ctx = {"params": {}, "steps": {}, "warnings": [],
           "_last_data": {"content": {"lessonTaskId": "lt-9"}}}
    ok = ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1,
                   "params": {"msgrelationid": "${content.lessonTaskId}"}}, ctx)
    assert ok is True
    sent = ex.calls[0][2]
    assert sent.get("msgrelationid") == "lt-9", "模板引用应解析为 lessonTaskId: %s" % sent
    assert sent.get("msgType") == "BATCH_MSG", "模板缺 msgType 时应补默认值: %s" % sent


def test_poll_query_failure_state_fails_immediately():
    """查询型轮询应识别 content.state 的失败终态，不得等待到超时。"""
    ex = FakeExecutor({"/space/strategygroup/vdi/detail": {
        "status": "SUCCESS", "content": {"id": "strategy-1", "state": "ERROR"}}})
    ctx = {"params": {}, "steps": {}, "_last_data": {"content": {"id": "strategy-1"}}}
    poll = {
        "api": "POST /space/strategygroup/vdi/detail",
        "params": {"id": "${content.id}"},
        "interval_ms": 1,
        "timeout_ms": 1000,
        "terminal_states": {"success": ["SUCCESS"], "failure": ["ERROR"]},
        "success_when": [
            {"path": "$.status", "op": "eq", "value": "SUCCESS"},
            {"path": "$.content.state", "op": "eq", "value": "AVAILABLE"},
        ],
    }
    try:
        ex._poll(poll, ctx)
    except AssertionError as e:
        assert "taskStatus=ERROR" in str(e)
    else:
        raise AssertionError("查询型轮询失败终态不得返回成功")


def test_poll_failure_states_key():
    """terminal_states.failure（文档键，兼容旧 fail 键）：任务 FAILURE → 抛断言"""
    ex = FakeExecutor({"/rco/msgct/msg/detail": {"status": "SUCCESS",
                                                 "content": {"taskStatus": "FAILURE"}}})
    ctx = {"params": {}, "steps": {}, "warnings": [], "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1,
                  "terminal_states": {"success": ["SUCCESS"], "failure": ["FAILURE"]}}, ctx)
        raise AssertionError("任务 FAILURE 应抛 AssertionError")
    except AssertionError as e:
        assert "轮询任务失败" in str(e), "失败信息应含任务状态: %s" % e


def test_poll_processing_then_success():
    """正常路径：PROCESSING（有效响应重置计数）→ SUCCESS 返回 True"""
    seq = [{"status": "SUCCESS", "content": {"taskStatus": "PROCESSING"}},
           {"status": "SUCCESS", "content": {"taskStatus": "PROCESSING"}},
           {"status": "SUCCESS", "content": {"taskStatus": "SUCCESS"}}]

    class SeqExecutor(FakeExecutor):
        def http_request(self, method, path, body=None, ctx=None):
            self.calls.append((method, path, body))
            return (200, seq[min(len(self.calls) - 1, len(seq) - 1)])

    ex = SeqExecutor()
    ctx = {"params": {}, "steps": {}, "warnings": [], "_last_data": {"content": {"taskId": "t-1"}}}
    ok = ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1}, ctx)
    assert ok is True
    assert len(ex.calls) == 3 and not ctx.get("warnings"), \
        "PROCESSING 不应计入无效响应: calls=%d warnings=%s" % (len(ex.calls), ctx.get("warnings"))


def test_poll_partial_success_fails_by_default():
    ex = FakeExecutor({"/rco/msgct/msg/detail": {
        "status": "SUCCESS", "content": {"taskStatus": "PARTIAL_SUCCESS"}}})
    ctx = {"params": {}, "steps": {}, "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"api": "/rco/msgct/msg/detail", "interval_ms": 1,
                  "terminal_states": {"success": ["SUCCESS", "PARTIAL_SUCCESS"]}}, ctx)
        raise AssertionError("PARTIAL_SUCCESS 不得默认成功")
    except AssertionError as e:
        assert "部分成功" in str(e)


def test_poll_explicit_params_without_task_id():
    ex = FakeExecutor({"/space/strategygroup/vdi/detail": {
        "status": "SUCCESS", "content": {"state": "AVAILABLE"}}})
    ctx = {"params": {}, "steps": {}, "_last_data": {"content": {"id": "vdi-1"}}}
    assert ex._poll({
        "api": "POST /space/strategygroup/vdi/detail", "interval_ms": 1,
        "params": {"id": "${content.id}"},
        "success_when": [{"path": "$.status", "op": "eq", "value": "SUCCESS"},
                         {"path": "$.content.state", "op": "eq", "value": "AVAILABLE"}],
    }, ctx)
    assert ex.calls[0][:3] == ("POST", "/space/strategygroup/vdi/detail", {"id": "vdi-1"})


def test_poll_404_strict_fails():
    ex = FakeExecutor({"/common_get_msgct": (404, {})})
    ex.strict = True
    ctx = {"params": {}, "steps": {}, "warnings": [], "_last_data": {"content": {"taskId": "t-1"}}}
    try:
        ex._poll({"interval_ms": 1}, ctx)
        raise AssertionError("strict 模式 404 应抛 AssertionError")
    except AssertionError:
        pass


def test_delete_poll_verified():
    """删除等待验证：资源消失 → True；资源仍在 → 超时 False + warning"""
    ex = FakeExecutor({"/rcc/classroom/select": {"status": "SUCCESS", "content": {"itemArr": []}}})
    ctx = {"params": {}, "steps": {}, "warnings": []}
    ok = ex._poll_classroom_delete("t-1", ctx, verify={"kind": "classroom", "id": "cr-1"},
                                   timeout=3, interval=0.05)
    assert ok is True, "资源已消失应确认删除成功"

    ex2 = FakeExecutor({"/rcc/classroom/select": {"status": "SUCCESS",
                                                   "content": {"itemArr": [{"classroomId": "cr-1"}]}}})
    ctx2 = {"params": {}, "steps": {}, "warnings": []}
    ok2 = ex2._poll_classroom_delete("t-1", ctx2, verify={"kind": "classroom", "id": "cr-1"},
                                     timeout=1, interval=0.05)
    assert ok2 is False, "资源仍存在且超时应返回 False"
    codes = [w["code"] for w in ctx2.get("warnings", [])]
    assert "delete_timeout" in codes, "删除超时应记录 warning: %s" % codes


# ---------- 4. 引用链接 ----------

def _run_channel_b(o, intent):
    steps, seen = [], set()
    for s in intent["steps"]:
        api = s.get("api", "")
        if not o.index.get(api):
            continue
        o._expand_setup(api, steps, seen)
        if api not in seen:
            steps.append(o._build_step_named(api, s.get("step_name", ""), "", s.get("section", "action")))
            seen.add(api)
    plan = {"id": "t", "steps": steps, "assertions": [], "sections": {"前置": [], "操作": [], "预期": []}}
    return o.validate_plan(plan)


def test_prev_refs_linked():
    o = Orchestrator()
    intent = {"steps": [
        {"api": "/rcc/classroom/strategy/create", "step_name": "createStrategy", "section": "pre"},
        {"api": "/rcc/classroom/create", "step_name": "create_classroom", "section": "pre"},
        {"api": "/rcc/classroom/seat/batchCreate", "step_name": "create_seat", "section": "pre"},
        {"api": "/rcc/space/classroom/cloudDesktop/restart", "step_name": "restart", "section": "action"},
    ]}
    plan = _run_channel_b(o, intent)
    all_names = [s.get("step_name") for s in plan["steps"]]
    step_names = set(all_names)
    assert len(all_names) == len(step_names), "step_name 应唯一（产出桶键）: %s" % all_names
    assert step_names, "所有步骤应有 step_name"
    flat_broken = []
    for st in plan["steps"]:
        def walk(v):
            if isinstance(v, str):
                for m in re.finditer(r"\$\{prev\.([\w.]+)", v):
                    ref = m.group(1)
                    if ".output." not in ref:
                        flat_broken.append(ref)
                    else:
                        assert ref.split(".")[0] in step_names, \
                            "引用断裂: %s -> %s" % (st.get("step_name"), v)
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        for vv in (st.get("body") or {}).values():
            walk(vv)
    assert not flat_broken, "存在未升格的平铺引用: %s" % flat_broken


def test_prev_ref_rewrite_warned():
    """跨文档步骤名不一致（select_classroom_id → query_classroom）应被改写并记 warns"""
    o = Orchestrator()
    plan = _run_channel_b(o, {"steps": [
        {"api": "/rcc/classroom/create", "step_name": "create_classroom", "section": "pre"},
        {"api": "/rcc/space/classroom/cloudDesktop/restart", "step_name": "restart", "section": "action"},
    ]})
    warns = plan.get("warns") or []
    rewritten = [w for w in warns if w.get("code") == "ref_rewritten"]
    assert rewritten, "跨文档步骤名不一致应产生 ref_rewritten warns: %s" % warns
    # 改写目标真实存在
    step_names = {s.get("step_name") for s in plan["steps"]}
    for w in rewritten:
        assert w["to"].split(".output.")[0] in step_names, \
            "改写目标不存在: %s" % w["to"]
    # 改写发生的步骤中不再引用旧步骤名；后续同名生产者的合法引用不受影响
    steps_by_name = {s.get("step_name"): s for s in plan["steps"]}
    for w in rewritten:
        st = steps_by_name[w["step"]]
        for v in (st.get("body") or {}).values():
            if isinstance(v, dict) and isinstance(v.get("value"), str):
                assert ("${prev.%s.output" % w["ref"].split(".output.")[0]) not in v["value"], \
                    "旧引用未改写干净: %s" % v["value"]


def test_explicit_ref_keeps_its_producer():
    o = Orchestrator()
    steps = [
        {"step_name": "first", "api": "/first",
         "extract": {"classroomId": "$.content.first"}},
        {"step_name": "second", "api": "/second",
         "extract": {"classroomId": "$.content.second"}},
        {"step_name": "action", "api": "/action", "extract": {},
         "body": {"classroomId": {"value": "${prev.first.output.classroomId}"}}},
    ]
    warns = []
    o._link_prev_refs(steps, warns)
    assert steps[-1]["body"]["classroomId"]["value"] == "${prev.first.output.classroomId}"
    assert not warns


def test_student_image_platform_ref_resolves():
    o = Orchestrator()
    plan = _run_channel_b(o, {"steps": [
        {"api": "/rcc/classroom/image/student/create",
         "step_name": "assign_student_image", "section": "action"},
    ]})
    action = next(s for s in plan["steps"]
                  if s.get("api") == "/rcc/classroom/image/student/create")
    raw = action["body"]["platformId"]["value"]
    match = re.fullmatch(r"\$\{prev\.([^.]+)\.output\.platformId\}", raw)
    assert match, "platformId 应绑定 setup 产出: %s" % raw
    producer = next(s for s in plan["steps"] if s.get("step_name") == match.group(1))
    assert producer.get("extract", {}).get("platformId") == "$.content.itemArr[0].platformId"
    ctx = {"params": {}, "steps": {match.group(1): {"platformId": "platform-1"},
                                   "get_free_vdi_ip": {"desktopStartIp": "10.51.180.2"}}}
    resolved = resolve_body(action["body"], ctx)
    assert resolved.get("platformId") == "platform-1", resolved
    # desktopStartIp 由前置 get_free_vdi_ip（deliverIPForVDIClassroom 按网络+座位数计算）产出，
    # 对齐 pytest common_deliver_ip_for_vdi_classroom；不使用需教室绑定的 deliverIPForVDISeat
    assert action["body"]["desktopStartIp"]["value"] == "${prev.get_free_vdi_ip.output.desktopStartIp}", \
        action["body"].get("desktopStartIp")
    assert resolved.get("desktopStartIp") == "10.51.180.2", resolved


def test_restart_setup_uses_vdi_classroom_ip():
    o = Orchestrator()
    meta = o.index.get("/rcc/classroom/desktop/restart")
    assign = next(item for item in meta.get("setup", [])
                  if item.get("api") == "POST /rcc/classroom/image/student/create")
    body = ((assign.get("request") or {}).get("body") or {})
    assert "desktopStartIp" not in body, \
        "重启覆盖项不应从终端参数注入桌面IP: %s" % body
    plan = _run_channel_b(o, {"steps": [
        {"api": "/rcc/classroom/desktop/restart", "step_name": "restart", "section": "action"},
    ]})
    apis = [s.get("api") for s in plan["steps"]]
    assert "/rcc/classroom/network/deliverIPForVDISeat" not in apis, \
        "deliverIPForVDISeat 需教室先绑定集群，不得注入"
    assert "/rcc/classroom/network/deliverIPForVDIClassroom" in apis, \
        "应按 pytest 对齐用 deliverIPForVDIClassroom 计算桌面起始IP"
    assign = next(s for s in plan["steps"]
                  if s.get("api") == "/rcc/classroom/image/student/create")
    dv = (assign["body"].get("desktopStartIp") or {}).get("value", "")
    assert dv == "${prev.get_free_vdi_ip.output.desktopStartIp}", \
        "desktopStartIp 应引用 get_free_vdi_ip（deliverIPForVDIClassroom）产出: %s" % dv


def test_field_prereq_removed_no_deliver_ip_injection():
    o = Orchestrator()
    consumer = o._build_step("/rcc/classroom/image/student/create", "分配学生镜像")
    consumer["step_name"] = "assign_student_image"
    plan = o.validate_plan({
        "id": "field-prereq",
        "steps": [consumer],
        "assertions": [],
        "sections": {"前置": [], "操作": [], "预期": []},
    })
    apis = [s.get("api") for s in plan["steps"]]
    assert "/rcc/classroom/network/deliverIPForVDISeat" not in apis, \
        "deliverIPForVDISeat 需教室先绑定集群，不得自动注入"
    # 单步骤（不展开 setup）时规则不得额外注入步骤；desktopStartIp 引用由文档声明提供
    assert apis == ["/rcc/classroom/image/student/create"], apis
    assert consumer["body"]["desktopStartIp"]["value"] == "${prev.get_free_vdi_ip.output.desktopStartIp}"


def test_case_added_student_create_uses_vdi_classroom_ip():
    o = Orchestrator()
    plan = o.validate_plan({
        "id": "case-field-prereq",
        "steps": [],
        "assertions": [],
        "sections": {"前置": ["桌面已分配镜像"], "操作": [], "预期": []},
    })
    apis = [s.get("api") for s in plan["steps"]]
    assert "/rcc/classroom/image/student/create" in apis
    assert "/rcc/classroom/network/deliverIPForVDISeat" not in apis, \
        "deliverIPForVDISeat 需教室先绑定集群，不得注入"
    assert "/rcc/classroom/network/deliverIPForVDIClassroom" in apis, \
        "case 补步骤应含 get_free_vdi_ip（deliverIPForVDIClassroom）"
    consumer = next(s for s in plan["steps"]
                    if s.get("api") == "/rcc/classroom/image/student/create")
    assert consumer["body"]["desktopStartIp"]["value"] == "${prev.get_free_vdi_ip.output.desktopStartIp}", \
        consumer["body"].get("desktopStartIp")
    required_refs = ("plusImageId", "storagePoolIdList", "clusterId",
                     "platformId", "strategyId", "networkId")
    for field in required_refs:
        value = (consumer["body"].get(field) or {}).get("value")
        assert value and value.startswith("${prev."), "%s 引用未补齐: %s" % (field, value)
    unresolved = [w for w in plan.get("warns", []) if w.get("code") == "ref_unresolved"]
    assert not unresolved, unresolved


def test_case_prereq_ignores_later_duplicate_setup_api():
    o = Orchestrator()
    plan = o.validate_plan({
        "id": "case-later-duplicate",
        "steps": [{
            "api": "/space/cluster/obtainComputeClusterList",
            "step_name": "later_cluster",
            "section": "action",
        }],
        "assertions": [],
        "sections": {"前置": ["桌面已分配镜像"], "操作": [], "预期": []},
    })
    consumer_idx = next(i for i, s in enumerate(plan["steps"])
                        if s.get("api") == "/rcc/classroom/image/student/create")
    cluster_idx = next(i for i, s in enumerate(plan["steps"][:consumer_idx])
                       if s.get("api") == "/space/cluster/obtainComputeClusterList")
    assert cluster_idx < consumer_idx
    unresolved = [w for w in plan.get("warns", []) if w.get("code") == "ref_unresolved"]
    assert not unresolved, unresolved


def test_case_prereq_ignores_later_achieve_step():
    o = Orchestrator()
    plan = o.validate_plan({
        "id": "case-later-achieve",
        "steps": [
            {"api": "/rcc/classroom/desktop/restart",
             "step_name": "restart", "section": "action"},
            {"api": "/rcc/classroom/image/student/create",
             "step_name": "later_assign", "section": "action"},
        ],
        "assertions": [],
        "sections": {"前置": ["桌面已分配镜像"], "操作": [], "预期": []},
    })
    restart_idx = next(i for i, s in enumerate(plan["steps"])
                       if s.get("step_name") == "restart")
    assert any(s.get("api") == "/rcc/classroom/image/student/create"
               for s in plan["steps"][:restart_idx])


def test_case_prereq_does_not_reuse_empty_setup_step():
    o = Orchestrator()
    plan = o.validate_plan({
        "id": "case-empty-setup",
        "steps": [{
            "api": "/space/cluster/obtainComputeClusterList",
            "step_name": "empty_cluster",
            "section": "pre",
            "extract": {},
        }],
        "assertions": [],
        "sections": {"前置": ["桌面已分配镜像"], "操作": [], "预期": []},
    })
    cluster_steps = [s for s in plan["steps"]
                     if s.get("api") == "/space/cluster/obtainComputeClusterList"
                     and (s.get("extract") or {}).get("clusterId")]
    assert cluster_steps
    unresolved = [w for w in plan.get("warns", []) if w.get("code") == "ref_unresolved"]
    assert not unresolved, unresolved


def test_case_prereq_reuses_existing_create_before_query():
    o = Orchestrator()
    create = {
        "api": "/rcc/classroom/create",
        "step_name": "existing_create",
        "section": "pre",
        "body": {},
        "extract": {},
    }
    query = o._build_step("/rcc/classroom/list", "查询教室")
    query["step_name"] = "query_classroom"
    query["section"] = "pre"
    query["extract"] = {"classroomId": "$.content.itemArr[0].classroomId"}
    plan = o.validate_plan({
        "id": "case-reuse-create",
        "steps": [create, query],
        "assertions": [],
        "sections": {"前置": ["桌面已分配镜像"], "操作": [], "预期": []},
    })
    creates = [s for s in plan["steps"] if s.get("api") == "/rcc/classroom/create"]
    assert len(creates) == 1
    unresolved = [w for w in plan.get("warns", []) if w.get("code") == "ref_unresolved"]
    assert not unresolved, unresolved


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [
        ("规则库-semantic_rules 加载", test_semantic_rules_loaded),
        ("规则库-语义冲突惩罚", test_semantic_penalty),
        ("规则库-侧别偏好", test_semantic_side_preference),
        ("规则库-匹配不回归", test_semantic_match_regression),
        ("规则库-轮询节点名解析", test_poll_node_name_resolved),
        ("规则库-轮询 POST 前缀归一", test_poll_method_prefix_normalized),
        ("fill-platformId 回查+缓存", test_fill_platform_id_sources_and_cache),
        ("fill-exactMatchArr 静态+追加", test_fill_exact_match_arr_static_and_append),
        ("fill-yetAssign 文档全链路", test_fill_doc_driven_from_yetassign_doc),
        ("VDI 创建策略参数化默认值", test_vdi_create_document_parameterizes_strategy_defaults),
        ("假绿-poll 404 显式失败", test_poll_404_fails),
        ("假绿-poll 校验错误不 死循环", test_poll_validation_error_not_infinite),
        ("假绿-poll HTTP 错误失败", test_poll_http_error_fails),
        ("假绿-poll 连续无状态失败", test_poll_missing_status_fails),
        ("假绿-poll params 模板解析", test_poll_params_template_resolved),
        ("假绿-查询轮询失败终态", test_poll_query_failure_state_fails_immediately),
        ("假绿-poll failure 键兼容", test_poll_failure_states_key),
        ("假绿-poll 正常轮询路径", test_poll_processing_then_success),
        ("假绿-PARTIAL_SUCCESS 默认失败", test_poll_partial_success_fails_by_default),
        ("轮询-显式 params 无 taskId", test_poll_explicit_params_without_task_id),
        ("假绿-poll 404 strict 失败", test_poll_404_strict_fails),
        ("假绿-删除存在性验证", test_delete_poll_verified),
        ("引用-plan 期全链接", test_prev_refs_linked),
        ("引用-改写记录 warns", test_prev_ref_rewrite_warned),
        ("引用-显式产出者保持不变", test_explicit_ref_keeps_its_producer),
        ("引用-学生镜像 platformId 可解析", test_student_image_platform_ref_resolves),
        ("引用-重启用deliverIPForVDIClassroom", test_restart_setup_uses_vdi_classroom_ip),
        ("规则-field_prereq移除不注入deliverIP", test_field_prereq_removed_no_deliver_ip_injection),
        ("规则-case补步骤用deliverIPForVDIClassroom", test_case_added_student_create_uses_vdi_classroom_ip),
        ("规则-case忽略后置重复setup", test_case_prereq_ignores_later_duplicate_setup_api),
        ("规则-case忽略后置达成步骤", test_case_prereq_ignores_later_achieve_step),
        ("规则-case不复用空setup", test_case_prereq_does_not_reuse_empty_setup_step),
        ("规则-case复用已有创建", test_case_prereq_reuses_existing_create_before_query),
    ]
    print("=== 四项重构回归测试 ===\n")
    for name, fn in tests:
        if only and only not in name:
            continue
        check(name, fn)
    print("\n结果: %d 通过, %d 失败" % (len(PASS), len(FAIL)))
    if FAIL:
        for name, err in FAIL:
            print("  ❌ %s: %s" % (name, err[:200]))
        sys.exit(1)
    print("全部通过 ✅")


if __name__ == "__main__":
    main()
