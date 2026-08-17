---
version: '2.0'
api:
  url: /rco/msgct/msg/detail
  method: POST
  name: 批任务消息详情查询（异步批任务轮询公共接口，编排节点名 common_get_msgct_detail_info）
  controller: Msg Ctrl（消息中心，RCO 框架公共模块；swagger tag "Msg Ctrl"）
  method_ref: msgDetail
  permission: 登录后调用（swagger 未标注独立权限注解；引擎在登录后自动携带会话凭证）
  exec_mode: sync
  async: false
  description: 按 msgRelationId + msgType 查询批任务（BATCH_MSG）消息详情，返回任务状态供轮询判定终态。真实接口地址为 POST /rco/msgct/msg/detail；编排中以节点名 common_get_msgct_detail_info 引用，由引擎在异步批任务接口返回 taskId 后轮询调用。
request:
  dto: 无（query 参数，swagger 定义）
  query:
    msgRelationId:
      type: UUID
      required: true
      constraint: query 必填
      description: 消息关联 ID（即批任务 taskId）
    msgType:
      type: String
      required: true
      constraint: 枚举 [BATCH_MSG]
      description: 消息类型（批任务消息固定 BATCH_MSG）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: Object（DefaultWebResponse 未展开，响应 DTO 在外部 RCO jar）
      description: 批任务消息详情；轮询引擎读取 $.content.taskStatus（兼容 $.content.status）判定终态
upstream:
- api: 各异步批任务接口（create/delete/edit 等）
  produces: $.content.taskId
  purpose: 批任务提交后返回 taskId，作为 msgRelationId 传入本接口轮询
downstream:
- api: 无 HTTP 下游
  purpose: 仅作为轮询判定节点，不产出业务数据供后续步骤使用
constraints:
- level: PARAM
  field: msgRelationId
  rule: query 必填（引擎以 ${content.taskId} 注入）
  failure: 缺失时后端参数校验失败
- level: PARAM
  field: msgType
  rule: query 必填，枚举 BATCH_MSG
  failure: 缺失/非法时后端参数校验失败（引擎已默认补充 msgType=BATCH_MSG，缺失会导致 sk_validation_NotNull）
assertions:
  success:
  - scenario: 任务已成功
    trigger: 轮询到 $.content.taskStatus == SUCCESS（或 PARTIAL_SUCCESS，视引用文档 terminal_states）
    expect: 轮询结束，用例继续
  failure:
  - scenario: 任务失败
    trigger: $.content.taskStatus == FAILURE（或 PARTIAL_SUCCESS，视引用文档 terminal_states）
    expect: '抛 AssertionError("轮询任务失败: taskId=...")'
  - scenario: 轮询超时
    trigger: 超过 timeout_ms 未到终态
    expect: '抛 AssertionError("轮询超时: taskId=...")'
cleanup:
- api: 无
  note: 只读查询接口
idempotency:
  level: non_idempotent
  note: 纯查询，无副作用
---
# POST /rco/msgct/msg/detail（编排节点 common_get_msgct_detail_info）

> 批任务消息详情查询：按 msgRelationId + msgType 查询批任务（BATCH_MSG）消息详情，返回任务状态供轮询判定终态 ｜ 登录后调用 ｜ sync

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rco/msgct/msg/detail |
| Controller | Msg Ctrl（消息中心，RCO 框架公共模块） |
| 方法名 | msgDetail |
| 权限 | 登录后调用（swagger 未标注独立权限注解；引擎自动携带会话凭证） |
| 业务含义 | 按 msgRelationId + msgType 查询批任务消息详情；异步批任务接口提交后返回 taskId，本接口以该 taskId 作为 msgRelationId 轮询任务终态 |

## 入参详情

### query 参数（swagger 定义，非 body）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| msgRelationId | UUID | 是 | query 必填 | 消息关联 ID（批任务 taskId，引擎以 `${content.taskId}` 注入） |
| msgType | String | 是 | 枚举 `[BATCH_MSG]` | 消息类型；批任务消息固定 `BATCH_MSG` |

> 编排兼容说明：引用文档 polling 段参数写为 `msgrelationid`（全小写，引擎透传），真实接口参数名为 `msgRelationId`（驼峰）。若后端严格区分大小写需以真实参数名调整。

## 出参详情

| 返回类型 | DefaultWebResponse（content 具体结构在外部 RCO jar，swagger 未展开） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content.taskStatus | String | 批任务状态（轮询引擎读取路径；兼容读取 $.content.status） |
| content.taskId / taskName / taskDesc | String/UUID | 批任务信息（与 BatchTaskSubmitResult 对齐，swagger 未在 msg/detail 展开） |

## 编排轮询用法（63 个异步接口文档引用）

引用文档 polling 段标准格式：

```yaml
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    - PARTIAL_SUCCESS
    failure:
    - FAILURE
```

- `msgrelationid` 取值：多数文档 `${content.taskId}`；`rcc_classroom_cmrcef_lesson_start/end` 为 `${content.lessonTaskId}`
- `terminal_states` 以各引用文档自身为准（autotest 现行为 success 含 PARTIAL_SUCCESS；setup_polling.json 旧版为 failure 含 PARTIAL_SUCCESS）

## 引擎实现行为（app/core/executor.py _poll）

1. `api` 字段支持节点名（orchestrator 经索引别名解析为 `/rco/msgct/msg/detail`）或直接写真实路径
2. 请求体：文档 `polling.params` 模板优先（`${content.X}` 引用触发步骤响应，如 lesson 的 `lessonTaskId`）；兜底 `{"msgrelationid": taskId, "msgType": "BATCH_MSG"}`（两参数均必填，缺 msgType 后端报 sk_validation_NotNull）
3. 轮询间隔 `interval_ms`（默认 2000ms）、超时 `timeout_ms`（默认 240000ms）；`terminal_states.failure`（兼容旧键 `fail`）
4. 连续 3 次 HTTP 404 或 响应无 taskStatus（含参数校验错误）→ 记 warning（poll_api_missing）后按通过处理；strict 模式判失败
5. 有 `$.status` 但无 taskStatus（content 有值）→ 同步响应，跳过轮询
6. 任务终态 FAILURE → 抛 `AssertionError("轮询任务失败: ...")`；超时未到终态 → 抛 `AssertionError("轮询超时: ...")`

## 上游/下游

| 方向 | 接口 | 说明 |
|---|---|---|
| 上游 | 各异步批任务接口（classroom create/delete、desktop 操作、seat 批量等） | 提交后返回 `$.content.taskId` |
| 下游 | 无 | 仅轮询判定，不产出业务数据 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
