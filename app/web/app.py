# -*- coding: utf-8 -*-
"""autotest - Flask 入口
4 个可视化：
  1. 用例输入（结构化模板 + 参数配置）
  2. 接口列表/详情
  3. 用例执行过程（实时日志）
  4. 模型配置（LLM API）
"""
import json
import os
import sys
import threading
import time

from flask import Flask, jsonify, render_template, request, Response

# 项目根目录（app/web/app.py 的上级两级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "app", "templates")
STATIC_DIR = os.path.join(PROJECT_ROOT, "app", "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config["JSON_AS_ASCII"] = False

from app.core import get_index, Executor, Orchestrator, ScriptRunner

index = get_index()
executor = Executor()  # 默认执行器（实际执行走 ScriptRunner 隔离）
orchestrator = Orchestrator(index)

# 执行状态（实时日志）
exec_sessions = {}


# ---------- 页面 ----------
@app.route("/")
def page_home():
    return render_template("index.html", active="home")


@app.route("/use-case")
def page_use_case():
    return render_template("use_case.html", active="use_case")


@app.route("/apis")
def page_apis():
    return render_template("apis.html", active="apis")


@app.route("/execution")
def page_execution():
    return render_template("execution.html", active="execution")


@app.route("/model")
def page_model():
    return render_template("model.html", active="model")


# ---------- API ----------
@app.route("/api/index")
def api_index():
    data = index.load()
    return jsonify({"total": len(data), "apis": [{
        "url": m["url"], "name": m["name"], "method": m["method"],
        "async": m["async"], "file": m["file"],
    } for m in sorted(data.values(), key=lambda x: x["url"])]})


@app.route("/api/apis/<path:url>")
def api_detail(url):
    meta = index.get("/" + url)
    if not meta:
        return jsonify({"error": "not found"}), 404
    return jsonify(meta)


@app.route("/api/apis/search")
def api_search():
    kw = request.args.get("q", "")
    results = index.search(kw)
    return jsonify({"results": [{
        "url": m["url"], "name": m["name"], "method": m["method"],
    } for m in results]})


@app.route("/api/settings")
def api_settings():
    """返回全局配置（base_url 等），供前端回填"""
    global_params = _load_global_params()
    return jsonify({"base_url": global_params.get("base_url", "")})


def _load_global_params():
    """读取全局参数文件（yaml 优先，回退 json）；作为默认参数基线，请求参数覆盖之"""
    base = os.path.join(PROJECT_ROOT, "app", "data")
    for name in ("global_params.yaml", "global_params.yml", "global_params.json"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            try:
                if p.endswith(".json"):
                    return json.load(open(p, encoding="utf-8"))
                import yaml
                return yaml.safe_load(open(p, encoding="utf-8")) or {}
            except Exception:
                return {}
    return {}


def _build_plan_with_mode(use_case, params):
    """主通道 B（AI 编排）；无 LLM 配置直接报错，不再降级到通道 A"""
    cfg = _load_model_config()
    if cfg and cfg.get("base_url") and cfg.get("api_key") and cfg.get("model"):
        plan = orchestrator.build_plan_ai(use_case, params, cfg)
        plan["_channel"] = "B"
        return plan
    print("[ERROR] LLM 未配置或配置不完整, cfg=%s" % repr(cfg))
    raise RuntimeError("通道 B 需要 LLM 配置：请在「模型配置」页填写 provider/base_url/api_key/model")


@app.route("/api/plan", methods=["POST"])
def api_plan():
    """dry-run 预览：编排用例返回计划（不执行，AI 编排优先，降级规则）"""
    data = request.get_json() or {}
    use_case = data.get("use_case", "")
    params = data.get("params", {})
    merged = dict(_load_global_params()); merged.update(params or {})
    plan = _build_plan_with_mode(use_case, merged)
    return jsonify({
        "channel": plan.get("_channel"),
        "rule_added": plan.get("rule_added", []),
        "warns": plan.get("warns", []),
        "steps": [{
            "step_name": s.get("step_name", ""), "name": s.get("name", ""),
            "api": s.get("api", ""), "section": s.get("section", ""),
            "body_fields": list(s.get("body", {}).keys()),
            "extract": list(s.get("extract", {}).keys()),
            "poll": bool(s.get("poll")), "idempotent": s.get("idempotent"),
            "auto_by_rules": bool(s.get("_auto_by_rules")),
            "warn": s.get("_warn"),
        } for s in plan.get("steps", [])],
        "assertions": plan.get("assertions", []),
    })


@app.route("/api/execute", methods=["POST"])
def api_execute():
    """执行用例：{use_case, params} → 实时执行"""
    data = request.get_json() or {}
    use_case = data.get("use_case", "")
    params = data.get("params", {})
    base_url = data.get("base_url") or _load_global_params().get("base_url") or "http://127.0.0.1:8080"

    session_id = _new_session()
    thread = threading.Thread(
        target=_run_use_case,
        args=(session_id, use_case, params, base_url),
        daemon=True,
    )
    thread.start()
    return jsonify({"session_id": session_id})


def _new_session():
    import uuid
    _cleanup_sessions()
    sid = str(uuid.uuid4())[:8]
    exec_sessions[sid] = {"logs": [], "status": "running", "result": None, "created": time.time()}
    return sid


def _cleanup_sessions():
    """清理过期（>30 分钟）与超量（>50）会话，防内存泄漏"""
    now = time.time()
    expired = [sid for sid, s in exec_sessions.items()
               if now - s.get("created", 0) > 1800]
    for sid in expired:
        del exec_sessions[sid]
    if len(exec_sessions) > 50:
        # 保留最近 50 个
        for sid in sorted(exec_sessions, key=lambda x: exec_sessions[x].get("created", 0))[:len(exec_sessions) - 50]:
            del exec_sessions[sid]


def _run_use_case(sid, use_case, params, base_url):
    from app.core.logger import new_case_log, CaseFileLogger
    first_line = (use_case.strip().splitlines()[0][:30] if use_case.strip() else "case")
    # 用执行开始时的精确时间戳命名（秒级），避免并发同用例冲突
    ts_name = time.strftime("%H%M%S")
    log_path = new_case_log("web_" + ts_name)
    flog = CaseFileLogger(log_path)
    exec_sessions[sid]["log_file"] = log_path
    exec_sessions[sid]["log_path"] = log_path  # 供外部获取

    def log(level, msg):
        exec_sessions[sid]["logs"].append({"level": level, "msg": msg, "ts": _ts()})
        flog.write(level, msg)

    try:
        merged = dict(_load_global_params()); merged.update(params or {})
        try:
            plan = _build_plan_with_mode(use_case, merged)
            log("info", "用例编排完成：%d 个步骤（通道 %s）→ 隔离执行" % (len(plan["steps"]), plan.get("_channel", "?")))
        except Exception as e:
            log("error", "用例编排失败: %s" % e)
            exec_sessions[sid]["status"] = "ERROR"
            exec_sessions[sid]["result"] = {"status": "ERROR", "error": str(e)}
            # 编排失败也要落盘结果摘要
            _write_summary(flog, sid, use_case, base_url, params, {"status": "ERROR", "error": str(e)})
            return
        # subprocess 隔离执行（executor.run_plan 方法调用，无字符串拼装）
        runner = ScriptRunner()
        try:
            exec_sessions[sid]["script"] = json.dumps(plan, ensure_ascii=False, indent=1)  # 供前端查看编排计划
            exec_sessions[sid]["plan_meta"] = {
                "channel": plan.get("_channel", ""),
                "rule_added": plan.get("rule_added", []),
                "warns": plan.get("warns", []),
                "steps": [{"step_name": s.get("step_name", ""), "api": s.get("api", ""),
                           "section": s.get("section", ""), "auto_by_rules": bool(s.get("_auto_by_rules"))}
                          for s in plan.get("steps", [])],
            }
            result = runner.run_isolated(plan, merged, base_url, timeout=300,
                                         log_cb=lambda l, m: log(_map_log_level(m), m))
            exec_sessions[sid]["result"] = result
            exec_sessions[sid]["status"] = result["status"]
            log("info", "执行完成：%s (exit=%s)" % (result["status"], result["exit_code"]))
            # 结果落盘摘要
            _write_summary(flog, sid, use_case, base_url, params, result)
            # 完整 result JSON 落盘
            _save_result_json(log_path, result)
        except Exception as e:
            log("error", "执行异常: %s" % e)
            exec_sessions[sid]["status"] = "ERROR"
            exec_sessions[sid]["result"] = {"status": "ERROR", "error": str(e)}
            _write_summary(flog, sid, use_case, base_url, params, {"status": "ERROR", "error": str(e)})
            _save_result_json(log_path, {"status": "ERROR", "error": str(e)})
    finally:
        flog.close()


def _save_result_json(log_path, result):
    """将完整 result JSON 保存到日志文件同目录下（HHMMSS_result.json）"""
    try:
        result_path = log_path.replace(".log", "_result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_summary(flog, sid, use_case, base_url, params, result):
    """将执行摘要写入日志文件（便于事后回溯，不污染实时滚动日志）"""
    flog.write("info", "=" * 60)
    flog.write("info", "[summary] session=%s 用例='%s' 环境=%s 参数=%s"
               % (sid, use_case.strip().splitlines()[0][:50], base_url,
                  json.dumps(params, ensure_ascii=False, default=str)[:200]))
    flog.write("info", "[summary] 最终结果: %s" % result.get("status", "?"))
    if result.get("error"):
        flog.write("error", "[summary] 错误: %s" % result["error"])
    steps = result.get("steps", [])
    if steps:
        pass_count = sum(1 for s in steps if s.get("status") == "PASS")
        fail_count = sum(1 for s in steps if s.get("status") != "PASS")
        flog.write("info", "[summary] 步骤: 共%d 通过%d 失败%d" % (len(steps), pass_count, fail_count))
    duration = result.get("duration_ms", 0)
    if duration:
        flog.write("info", "[summary] 耗时: %dms (%.1fs)" % (duration, duration / 1000))
    if result.get("exit_code") is not None:
        flog.write("info", "[summary] exit_code=%s" % result["exit_code"])
    if result.get("script"):
        flog.write("info", "[summary] 编排计划已记录在 log 文件中")
    flog.write("info", "=" * 60)
    flog.write("info", "")


def _map_log_level(line):
    """子进程日志行前缀 → 前端分级 level"""
    if line.startswith("[Step"):
        return "step"
    if line.startswith("[req]"):
        return "req"
    if line.startswith("[resp]"):
        return "resp"
    if line.startswith("[poll]"):
        return "info"
    if line.startswith("[extract]"):
        return "info"
    if line.startswith("[error]") or "Error" in line or "Traceback" in line:
        return "error"
    if line.startswith("[result]"):
        return "step"
    return "info"


def _ts():
    import time
    return time.strftime("%H:%M:%S")


@app.route("/api/execution/<sid>")
def api_execution(sid):
    s = exec_sessions.get(sid)
    if not s:
        return jsonify({"error": "session not found"}), 404
    return jsonify({
        "status": s["status"],
        "logs": s["logs"],
        "result": s.get("result"),
        "script": s.get("script"),
        "plan_meta": s.get("plan_meta"),
        "log_file": s.get("log_file"),
    })


def _load_model_config():
    """读取模型配置（通道 B 用）；未配置返回空壳（configured=False 触发明确报错）"""
    cfg_path = os.path.join(PROJECT_ROOT, "app", "data", "model_config.json")
    if os.path.exists(cfg_path):
        return json.load(open(cfg_path, encoding="utf-8"))
    return {
        "provider": "openai",
        "base_url": "",
        "api_key": "",
        "model": "",
        "temperature": 0.1,
        "max_tokens": 2048,
    }


@app.route("/api/model-config", methods=["GET", "POST"])
def api_model_config():
    cfg_path = os.path.join(PROJECT_ROOT, "app", "data", "model_config.json")
    if request.method == "POST":
        cfg = request.get_json() or {}
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    return jsonify(_load_model_config())


@app.route("/api/model-test", methods=["POST"])
def api_model_test():
    """真实测试 LLM 连通性：发一个最小 chat 请求"""
    cfg = request.get_json() or _load_model_config()
    try:
        from app.core.llm import LlmClient
        client = LlmClient(cfg)
        reply = client.chat("你是连通性测试助手", "回复 OK")
        return jsonify({"ok": True, "reply": (reply or "")[:100]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/model-chat", methods=["POST"])
def api_model_chat():
    """配置页对话验证：用表单当前填写的配置多轮对话（无需先保存）"""
    body = request.get_json() or {}
    cfg = body.get("config") or {}
    messages = body.get("messages") or []
    if not messages:
        return jsonify({"ok": False, "error": "messages 为空"}), 400
    try:
        from app.core.llm import LlmClient
        reply = LlmClient(cfg).chat_messages(messages)
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


if __name__ == "__main__":
    print("加载接口索引...")
    n = len(index.load())
    print(f"✅ 已加载 {n} 个接口")
    print("启动平台: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
