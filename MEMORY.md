# 记忆文件

## 🔍 快速索引

| 关键词 | 内容摘要 | 文件/位置 |
|--------|----------|-----------|
| 幂等策略 | recreate 模式：删除失败 → 降级复用已有资源 | executor.py `_recreate` |
| 座位名重复 | desktopPreName 从 "vd" 改为 "vdaaa"（5字符） | `_run_test_case.py` |
| resolve_body None 清理 | `_clean_none` 递归过滤 None 值 | params.py |
| 教室 delete | 需要 oneTimeToken，无法自动获取 | executor.py `_recreate` |
| 测试参数 | classroom=a_classroom_01, desktopPreName=vdaaa, desktopNameStartNum=1, seatNum=1 | `_run_test_case.py` |
| 语义匹配反规则 | 数据驱动（business_rules.md semantic_rules），不再硬编码 | orchestrator `_apply_semantic_rules` |
| 文档驱动补数 | 接口文档 front-matter `fill:` 声明，executor `_apply_fill` 通用引擎消费 | executor.py / docs front-matter |
| 假绿治理 | 「无法确认结果」→ warnings 进 result + strict 模式判失败 | executor `_unverified` / result.warnings |
| 引用链接 | plan 期 `${prev.*}` 改写到真实步骤名 + 唯一 step_name | orchestrator `_link_prev_refs` |

## 项目结构

```
D:\tools\autotest\
├── app/
│   ├── core/
│   │   ├── executor.py     # 用例执行器（fill 引擎/幂等/轮询/断言/cleanup）
│   │   ├── orchestrator.py # 编排（双通道 + validate_plan 修正 + 引用链接）
│   │   ├── params.py       # 参数解析（resolve_body, _clean_none, 模糊回退告警）
│   │   └── index.py        # 接口文档索引（meta 含 fill 声明）
│   └── web/app.py          # Flask Web UI + API
├── docs/api_md_staging/    # 接口文档（front-matter: setup/fill/polling…）
├── tests/                  # 回归测试（test_orchestration / test_refactor）
└── run_case.py / run.py    # CLI / Web 入口
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

### 语义匹配规则外置（2026-08-17 重构）
- 集群↔存储池惩罚、RDCD/Space 侧别偏好、dashboard 降权等打分修正
  全部移入 `business_rules.md` front-matter `semantic_rules:` 节
- orchestrator 只保留通用匹配器 `_apply_semantic_rules`（if_entities/url_any/name_any/name_none/delta）
- 新增反规则改文档即可，不再改代码

### 文档驱动补数 fill 声明（2026-08-17 重构）
- executor 不再硬编码 platformId 回查 / exactMatchArr 注入 / desktop-list 最小条件
  （原 `_fill_platform_id_for_image`、`_image_empty_list` 死代码等全部移除）
- 接口文档 front-matter `fill:` 声明：field/when/value/sources/append_item/cache_by，
  `${body.X}` 引用当前请求体、`${fill}` 引用 sources 取值
- 已落地：yetAssign/list（platformId 三级回查 + exactMatchArr+clusterId）、
  desktop/list（无过滤时按 classroomId 过滤）
- 新系统/新接口的补数需求写文档，executor 保持通用

### 假绿治理（2026-08-17 重构）
- `_poll` 404×3 / 响应无 taskStatus → 记 warning（poll_api_missing）后通过；
  strict 模式（Executor(strict=True) 或 params.strict=true）直接判失败
- `_poll_classroom_delete` 不再固定等 10 秒假设成功：分段等待后按
  select/seat-list 存在性验证删除；超时记 delete_timeout 并返回 False
  （_recreate 降级复用，不会误建重名）
- result JSON 新增 `warnings` 数组（poll_api_missing/delete_timeout/ref_fuzzy_fallback 等）

### 引用链接（2026-08-17 重构）
- 根因：`_infer_body_value` 曾生成缺 `.output.` 段的平铺引用；跨文档 setup
  步骤名不一致（select_classroom_id vs query_classroom）靠执行期模糊回退静默兜底
- validate_plan 末尾 `_link_prev_refs`：全步骤补唯一 step_name（URL 末段 + 去重）、
  `${prev.*}` 改写到「最近的前序产出步骤」、断裂引用记 plan.warns（ref_rewritten/ref_unresolved）
- params 模糊回退保留为最后兜底，命中记 ref_fuzzy_fallback warning

### 测试环境
- base_url: `https://10.51.167.250:8443/rcdc`
- 用户: `admin9`
- 教室名: `a_classroom_01`
- 桌面前缀: `vdaaa`
- 桌面名起始号: `1`
- 座位数: `1`
