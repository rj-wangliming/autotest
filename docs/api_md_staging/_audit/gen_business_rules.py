#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Java 源码推导业务规则（business_rules.md 的 state_prereq / resource_chains / 开机途径）

推导来源：
  1. 状态前置（state_prereq）：扫描 `CbbCloudDeskState.XXX != ...` / `... != CbbCloudDeskState.XXX`
     校验分支，从所在类名（*BatchTaskHandler / *APIImpl）提取"操作 -> 要求状态"
  2. 资源依赖链（resource_chains）：扫描请求 DTO 的外键字段（classroomId/seatId/lessonImageId/
     strategyId 等 UUID），从 create 类接口的请求 DTO 推导"接口依赖的资源"
  3. 开机途径：枚举桌面操作接口，若无独立开机接口且 lesson/start 的 Handler 启动桌面 → 上课开机

用法：
  python3 gen_business_rules.py [--src /path/to/java] [--rules business_rules.md]
  --diff  仅对比现有规则库，输出差异（不写文件）
"""
import os
import re
import sys
import glob
import argparse
import collections


# ---------- 状态枚举 ----------
DESK_STATES = ("RUNNING", "SLEEP", "OFF", "CLOSE", "IDV_STARTING", "VDI_STARTING",
               "STARTING", "SHUTDOWNING", "RESTARTING", "ERROR", "UNKNOWN")

# 各资源的状态枚举类（扫描状态校验用）
STATE_ENUMS = {
    "desktop": "CbbCloudDeskState",
    "classroom": "ClassroomLessonStatusEnum",
    "strategy": "SpaceStrategyGroupState",
}

# 桌面操作词 → 识别 Handler/API 类名中的操作
OP_WORDS = {
    "restart": "restart",
    "shutdown": "shutdown",
    "poweroff": "poweroff",
    "forcewakeup": "forcewakeup",
    "wake": "wake",
    "restore": "restore",
    "start": "start",
}

# 各资源的操作词（类名/方法名识别）
RESOURCE_OPS = {
    "desktop": ("restart", "shutdown", "poweroff", "forcewakeup", "wake", "restore", "start"),
    "classroom": ("start", "end", "edit", "delete", "create"),
    "strategy": ("edit", "delete", "create"),
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1")
    p.add_argument("--rules", default=None, help="现有 business_rules.md 路径（对比用）")
    p.add_argument("--diff", action="store_true", help="仅输出差异，不写文件")
    return p.parse_args()


# ---------- 1. 状态前置推导 ----------
def derive_state_prereq(src):
    """扫描多资源状态校验，提取 操作 -> 状态候选（== 要求 / != 禁止，启发式）"""
    found = []  # {cls, resource, op, state, mode(require/forbid), file, line}
    for resource, enum in STATE_ENUMS.items():
        pattern = re.compile(
            r'(?:%s\.(\w+))\s*(==|!=)\s*(?:\w+\(\)|get\w+\(\))'
            r'|(?:get\w+\(\))\s*(==|!=)\s*(?:%s\.(\w+))'
            r'|(?:!?%s\.(\w+)\.equals\([^)]*\))'
            % (enum, enum, enum)
        )
        for path in glob.glob(os.path.join(src, "**", "*.java"), recursive=True):
            try:
                content = open(path, encoding="utf-8").read()
            except Exception:
                continue
            cls_match = re.search(r'class\s+(\w+)', content)
            cls = cls_match.group(1) if cls_match else os.path.basename(path).replace(".java", "")
            ops = RESOURCE_OPS[resource]
            for m in pattern.finditer(content):
                # 统一解析：(state, op_char)；equals 形式按 forbid 候选
                state = op_char = None
                for g1, g2 in ((m.group(1), m.group(2)), (m.group(4), m.group(3))):
                    if g1 and g2:
                        state, op_char = g1, g2
                        break
                if not state and m.group(5):
                    state, op_char = m.group(5), "!="
                if not state:
                    continue
                # 操作类型：类名动作词，其次方法名动作词
                op = None
                for w in ops:
                    if w in cls.lower():
                        op = w
                        break
                if not op:
                    before = content[:m.start()]
                    meth = re.findall(r'\b(?:public|private|protected)\s+[\w<>\[\],\s]+\s+(\w+)\s*\(', before)
                    if meth:
                        for w in ops:
                            if w in meth[-1].lower():
                                op = w
                                break
                if not op:
                    continue
                # 启发式：!= → require（条件成立走 throw），== → forbid；equals 非 → require
                mode = "require" if op_char == "!=" else "forbid"
                found.append({"cls": cls, "resource": resource, "op": op,
                              "state": state, "mode": mode, "file": path.split("/")[-1]})
    return found


# ---------- 2. 资源依赖链推导 ----------
def derive_resource_chains(src):
    """扫描 create 类请求 DTO 的外键字段 → 接口依赖的资源"""
    # 外键字段 -> 资源类型
    FK_RESOURCE = {
        "classroomid": "classroom",
        "seatid": "seat",
        "lessonimageid": "image",
        "imageid": "image",
        "strategid": "strategy",
        "strategyid": "strategy",
        "networkid": "network",
        "clusterid": "cluster",
        "storagepoolid": "storage_pool",
        "platformid": "platform",
    }
    # 找所有请求 DTO 及其字段
    req_fks = {}  # DTO 类 -> set(资源)
    for path in glob.glob(os.path.join(src, "**", "*Request*.java"), recursive=True):
        try:
            content = open(path, encoding="utf-8").read()
        except Exception:
            continue
        cls = os.path.basename(path).replace(".java", "")
        fks = set()
        for m in re.finditer(r'private\s+UUID\s+(\w+);', content):
            fk = m.group(1).lower()
            for k, res in FK_RESOURCE.items():
                if fk == k or fk.endswith(k):
                    fks.add(res)
        if fks:
            req_fks[cls] = fks

    # create 类接口的请求 DTO：从 Controller 方法参数关联
    chain_deps = collections.defaultdict(set)  # 接口 url -> 依赖资源
    for path in glob.glob(os.path.join(src, "**", "*Controller.java"), recursive=True):
        try:
            content = open(path, encoding="utf-8").read()
        except Exception:
            continue
        # 类级 RequestMapping 前缀（类声明前的 @RequestMapping；允许中间有其他注解，如 @Api）
        cls_pre = ""
        m_cls = re.search(r'@RequestMapping\((?:value\s*=\s*)?("[^"]+")\)(?:(?!\bclass\b)[\s\S])*?\bclass\s+\w+', content)
        if m_cls:
            cls_pre = m_cls.group(1).strip('"').strip("/")
        # 方法级：value + 方法签名（允许中间有注解）
        for m in re.finditer(r'@RequestMapping\(value\s*=\s*"([^"]+)"(.*?)\bpublic\s+\w+\s+(\w+)\(([^)]*)\)', content, re.S):
            url = m.group(1)
            params = m.group(4)
            full = "/" + "/".join(p.strip("/") for p in (cls_pre, url) if p.strip("/"))
            # 找参数里的 Request 类型
            for req_cls in re.findall(r'(\w+Request)\s+\w+', params):
                if req_cls in req_fks:
                    for res in req_fks[req_cls]:
                        chain_deps[full].add(res)
    return chain_deps, req_fks


# ---------- 3. 开机途径推导 ----------
def derive_boot_path(src, doc_urls):
    """枚举桌面操作接口；若无学生桌面独立开机接口且 lesson/start 启动桌面 → 上课开机"""
    # lesson/start 的 Handler 是否启动桌面
    lesson_start_boots = False
    for path in glob.glob(os.path.join(src, "**", "*Lesson*Handler*.java"), recursive=True):
        try:
            content = open(path, encoding="utf-8").read()
        except Exception:
            continue
        if "startDesktopDTO" in content or "startDesktop" in content:
            lesson_start_boots = True
    # 学生桌面直接开机接口（desktop/start 无 student 前缀限制）
    has_desk_start = any("/start" in u and ("desktop" in u or "clouddesktop" in u) and "lesson" not in u
                         for u in doc_urls)
    return {
        "lesson_start_boots": lesson_start_boots,
        "has_desktop_start": has_desk_start,
        "conclusion": "上课开机" if (lesson_start_boots and not has_desk_start) else "（需人工确认）"
    }


def main():
    args = parse_args()
    src = args.src
    print(f"=== 源码目录: {src} ===\n")

    # 1. 状态前置
    print("【1. 状态前置推导（源码状态枚举校验）】")
    st = derive_state_prereq(src)
    # 按 资源+操作 聚合
    agg = collections.defaultdict(list)
    for f in st:
        agg[(f["resource"], f["op"])].append((f["state"], f["mode"], f["cls"]))
    for (res, op) in sorted(agg):
        items = sorted(set((s, m) for s, m, _ in agg[(res, op)]))
        desc = ", ".join(f"{'要求' if m=='require' else '禁止'}{s}" for s, m in items)
        print(f"  {res}[{op}]: {desc}")
        for s, m, cls in sorted(set(agg[(res, op)]))[:4]:
            print(f"      - {cls}: {'要求' if m=='require' else '禁止'}{s}")
    if not st:
        print("  （未提取到状态校验）")

    # 2. 资源依赖链
    print("\n【2. 资源依赖链推导（请求 DTO 外键参数）】")
    chains, req_fks = derive_resource_chains(src)
    print(f"  提取到 {len(req_fks)} 个含外键的请求 DTO")
    create_deps = {u: deps for u, deps in sorted(chains.items()) if u.endswith("create") or "batchCreate" in u}
    for u, deps in list(create_deps.items())[:15]:
        print(f"  {u}: 依赖 {sorted(deps)}")

    # 3. 开机途径
    print("\n【3. 开机途径推导】")
    doc_urls = set()
    if args.rules and os.path.isfile(args.rules):
        import yaml
        fm = yaml.safe_load(open(args.rules).read().split("---\n", 2)[1])
        for rc in (fm.get("resource_chains") or {}).values():
            for u in rc.get("order", []):
                doc_urls.add(u.replace("POST ", ""))
    boot = derive_boot_path(src, doc_urls)
    print(f"  lesson/start 启动桌面: {boot['lesson_start_boots']}")
    print(f"  存在学生桌面独立开机接口: {boot['has_desktop_start']}")
    print(f"  结论: 学生桌面开机途径 = {boot['conclusion']}")

    # 4. --diff：与现有规则库对比
    if args.diff:
        if not args.rules or not os.path.isfile(args.rules):
            print("\n⚠️ --diff 需要 --rules 指向现有 business_rules.md")
            return
        import yaml
        fm = yaml.safe_load(open(args.rules).read().split("---\n", 2)[1])
        print("\n【4. 与现有规则库对比 (--diff)】")
        # 4a. state_prereq 对比
        existing = {(sp.get("resource"), sp.get("action")) for sp in (fm.get("state_prereq") or [])}
        derived = {(f["resource"], f["op"]) for f in st}
        missing = sorted(derived - existing)          # 源码有、规则库无
        extra = sorted(existing - derived)            # 规则库有、源码未推导
        print(f"  state_prereq: 规则库 {len(existing)} 条 | 源码候选 {len(derived)} 组")
        if missing:
            print("  ⚠️ 源码推导但规则库缺失（建议补充）:")
            for r, a in missing:
                states = sorted({s for s, m, _ in agg[(r, a)]})
                print(f"      {r}[{a}] -> {states}")
        if extra:
            print("  ℹ️ 规则库有但源码未推导（人工规则/语义标注，确认保留）:")
            for r, a in extra:
                print(f"      {r}[{a}]")
        # 4b. resource_chains 对比（create 类接口依赖）
        print("\n  resource_chains: 源码 create 类接口依赖 vs 规则库:")
        rule_creates = set()
        for rc in (fm.get("resource_chains") or {}).values():
            for u in rc.get("order", []):
                rule_creates.add(u.replace("POST ", "").rstrip("/"))
        src_creates = set(create_deps.keys())
        print(f"     规则库链接口: {len(rule_creates)} | 源码 create 类: {len(src_creates)}")
        not_in_rule = sorted(src_creates - rule_creates)
        if not_in_rule:
            print("     ⚠️ 源码 create 类接口不在规则库链中:")
            for u in not_in_rule[:10]:
                print(f"        {u}")
        return

    print("\n=== 推导完成（--diff 查看与规则库差异）===")


if __name__ == "__main__":
    main()
