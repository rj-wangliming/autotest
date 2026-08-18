---
version: '2.0'
api:
  url: /rcc/classroom/terminal/log/delete
  method: POST
  name: 删除终端日志：多条走批处理，单条直接删除并记录审计
  controller: RccClassroomManageController
  method_ref: deleteTerminalLog
  permission: 无
  exec_mode: async_batch
  async: false
  description: 删除终端日志：多条走批处理，单条直接删除并记录审计
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批处理任务，出参BatchTaskSubmitResult）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
request:
  dto: TerminalLogIdRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    logIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 待删除的日志ID列表
      value: ${param.log_id_arr}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskId:
      type: UUID
      description: 多条删除时的批处理任务ID
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  optional_when_no_correlation: true
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success: [SUCCESS]
    failure: [FAILURE, PARTIAL_SUCCESS]
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
- api: POST /rcc/classroom/terminal/log/list
  produces: $.content.itemArr[*].id
  purpose: 推断：终端日志ID数组来自终端日志列表查询出参（TerminalLogDTO.id），字段名为推断
downstream:
- api: 内部调用:PlatformTerminalLogAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomId
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: logIdArr
  rule: '@NotEmpty 非空'
  failure: webmvc 参数校验异常
- level: business
  field: classroomId
  rule: 管理员需具备该教室终端组数据权限
  failure: rccPermissionChecker 抛出权限异常
assertions:
  success:
  - scenario: 日志存在且删除成功
    expect: 多条：$.status==SUCCESS && $.content.taskId 非空（批处理任务）；单条：$.status==SUCCESS（content 为空）
  failure:
  - scenario: 单条日志删除失败
    trigger: 日志不存在/文件被占用
    expect: $.status==ERROR（记录 RCDC_RCC_TERMINAL_LOG_DELETE_SINGLE_FAIL_LOG 后抛出，msgKey 为底层日志删除异常）
  - scenario: 多条中部分失败
    trigger: 部分日志无效
    expect: $.status==SUCCESS && $.content.taskId 非空（批任务终态 PARTIAL_SUCCESS）
cleanup: []
idempotency:
  level: data_level
  note: 重复删除已删除的日志会失败（幂等性弱）；批处理逐条执行
params:
  required:
  - name: classroom_name
  - name: log_id_arr
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/terminal/log/delete

> 删除终端日志：多条走批处理，单条直接删除并记录审计 ｜ 无特殊权限 ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
        A2["POST /rcc/classroom/terminal/log/list"]
    end
    B["POST /rcc/classroom/terminal/log/delete<br>删除终端日志：多条走批处理，单条直接删除并记录审计<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/builder/sessionContext 非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: isBatch = logIdArr.length > 1：多条 → getBa"]
        C4["Step4: 单条 → deleteOneTerminalLog：getLogById 取日志"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["（无 HTTP 下游）"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/terminal/log/delete |
| Controller | RccClassroomManageController |
| 方法名 | deleteTerminalLog |
| 权限注解 | 无 |
| 执行方式 | async_batch |
| 业务含义 | 删除终端日志：多条走批处理，单条直接删除并记录审计 |

## 入参详情

### TerminalLogIdRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| logIdArr | UUID[] | 是 | @NotEmpty 非空 | 待删除的日志ID列表 |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult|String> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 多条删除时的批处理任务ID |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/terminal/log/list

推断：终端日志ID数组来自终端日志列表查询出参（TerminalLogDTO.id），字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：DeleteTerminalLogBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem：getLogById 取日志名 → deleteTerminalLog(logId)，记录成功/失败审计 |
| 2 | onFinish：全成功返回成功、全失败返回失败、否则部分成功 |

### 处理流程

1. Assert request/builder/sessionContext 非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(单教室) 校验权限
3. isBatch = logIdArr.length > 1：多条 → getBatchDeleteLogDefaultWebResponse 构造 DeleteTerminalLogBatchTaskHandler 提交批处理
4. 单条 → deleteOneTerminalLog：getLogById 取日志名 → deleteTerminalLog → 记录成功审计；异常记录失败审计并抛出

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId | @NotNull 非空 | webmvc 参数校验异常 |
| request | logIdArr | @NotEmpty 非空 | webmvc 参数校验异常 |
| business | classroomId | 管理员需具备该教室终端组数据权限 | rccPermissionChecker 抛出权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| logIdArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 日志存在且删除成功 | 多条：$.status==SUCCESS && $.content.taskId 非空（批处理任务）；单条：$.status==SUCCESS（content 为空） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 单条日志删除失败 | 日志不存在/文件被占用 | $.status==ERROR（记录 RCDC_RCC_TERMINAL_LOG_DELETE_SINGLE_FAIL_LOG 后抛出，msgKey 为底层日志删除异常） |
| 多条中部分失败 | 部分日志无效 | $.status==SUCCESS && $.content.taskId 非空（批任务终态 PARTIAL_SUCCESS） |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复删除已删除的日志会失败（幂等性弱）；批处理逐条执行 |
