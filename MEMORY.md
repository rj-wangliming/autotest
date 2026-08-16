# 记忆文件

## 🔍 快速索引

| 关键词 | 内容摘要 | 文件/位置 |
|--------|----------|-----------|
| 幂等策略 | recreate 模式：删除失败 → 降级复用已有资源 | executor.py `_recreate` |
| 座位名重复 | desktopPreName 从 "vd" 改为 "vdaaa"（5字符） | `_run_test_case.py` |
| resolve_body None 清理 | `_clean_none` 递归过滤 None 值 | params.py |
| 教室 delete | 需要 oneTimeToken，无法自动获取 | executor.py `_recreate` |
| 测试参数 | classroom=a_classroom_01, desktopPreName=vdaaa, desktopNameStartNum=1, seatNum=1 | `_run_test_case.py` |

## 项目结构

```
D:\tools\autotest\autotest\
├── app/
│   ├── api/
│   │   └── run.py          # FastAPI 入口（Web UI + API）
│   ├── core/
│   │   ├── executor.py     # 用例执行器
│   │   ├── params.py       # 参数解析（resolve_body, _clean_none）
│   │   └── orchestrator.py # 编排生成
│   └── ...
├── docs/api_md_staging/    # 接口文档（api_md 格式）
├── logs/cases/             # 测试日志和结果
└── _run_test_case.py       # CLI 测试入口
```

## 关键决策

### 幂等策略（idempotent=recreate）
- 先通过 select 查询同名资源
- 调用 delete_api 删除
- 删除失败（oneTimeToken 问题）→ 降级为复用已有资源（skip 创建）
- 删除成功 → 继续执行创建

### 参数清理
- `resolve_body` 调用 `_clean_none` 递归清理 None 值
- 避免 `valueArr: [null]` 导致服务端校验失败

### 测试环境
- base_url: `https://10.51.167.250:8443/rcdc`
- 用户: `admin9`
- 教室名: `a_classroom_01`
- 桌面前缀: `vdaaa`
- 桌面名起始号: `1`
- 座位数: `1`
