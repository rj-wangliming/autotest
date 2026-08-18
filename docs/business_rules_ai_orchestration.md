# autotest AI 编排参考文件

> 供 AI 编排时参考的业务规则补充说明。核心规则定义在 `docs/api_md_staging/business_rules.md`（front-matter 格式，orchestrator 自动加载）。

## 核心业务规则速查

### 一、教室删除规则

**前置条件：**
1. 教室必须处于下课状态（`NONE_CLASS`）— 上课中需先下课
2. 教室所有桌面必须处于关机状态 — 先关机再删除

**清理顺序：**
```
下课（/rcc/classroom/cmrcef/lesson/end）
  → 等待下课完成（轮询 /rcc/classroom/cmrcef/lesson/progress）
  → 查询所有桌面（/rcc/classroom/desktop/list）
  → 对每个桌面下发关机指令（/rcc/classroom/desktop/powerOff）
  → 等待关机完成（建议 10 秒）
  → 删除桌面（/rcc/classroom/desktop/delete）
  → 删除座位（/rcc/classroom/seat/delete）
  → 删除教室（/rcc/classroom/delete）
```

### 二、同名数据清理规则

当用例中有创建相关步骤时，前置步骤执行前必须先清理同名数据。

**实现方式：**
- `idempotent: recreate` — 先查后创建（查重失败降级复用）
- `idempotent: reuse` — 只查不建（通过 reuse_query 接口查询）
- 依赖顺序：桌面 → 座位 → 教室（反向依赖）

### 三、教室策略 vs 课程策略

| 策略类型 | 接口 | 用途 | 产出字段 |
|---------|------|------|---------|
| 教室策略 | `/rcc/classroom/strategy/list` | 创建教室时关联 | `classroomStrategyId` |
| 课程策略（VDI） | `/space/strategygroup/vdi/list` | 学生镜像分配 | `vdiStrategyId` / `id` |
| 课程策略（TCI） | `/space/strategygroup/tci/list` | 学生镜像分配 | `tciStrategyId` / `id` |

**重要：** `/rcc/classroom/image/student/create` 的 `strategyId` 需要的是**课程策略 ID**（VDI 课程策略），不是教室策略 ID。两者不能混用。

### 四、参数来源

所有参数定义在 `app/data/global_params.yaml`：

| 参数名 | 用途 |
|-------|------|
| `classroom_name` | 教室名称 |
| `classroom_strategy_name` | 教室策略名称 |
| `strategy_name_vdi` | VDI 课程策略名称 |
| `strategy_name_tci` | TCI 课程策略名称 |
| `network_id_arr` | 网络策略 ID 数组 |
| `image_name` | 镜像名称 |

## 文档补充注意事项

### YAML 解析安全

- `purpose` 字段的值如果包含中文括号加冒号 `（...: ...）`，必须用双引号包裹，否则 YAML 解析会失败
  - 错误：`purpose: 描述（idempotent: reuse）`
  - 正确：`purpose: "描述（idempotent: reuse）"`

### matchArr 格式

```yaml
matchArr:
- type: EXACT
  fieldName: <字段名>
  valueArr:
  - ${param.<参数名>}
  matchRule: EQ
```

