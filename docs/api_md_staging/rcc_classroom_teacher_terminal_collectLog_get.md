---
version: '2.0'
api:
  url: /rcc/classroom/teacher/terminal/collectLog/get
  method: POST
  name: 查询教师机终端日志收集状态：按终端ID返回收集状态。
  controller: RccTeacherManageController
  method_ref: getCollectLog
  permission: 无
  exec_mode: sync
  async: false
  description: 查询教师机终端日志收集状态：按终端ID返回收集状态。
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
  dto: TerminalIdWebRequest
  body:
    terminalId:
      type: String
      required: true
      constraint: '@NotBlank 非空白'
      description: 教师终端ID（由 collectLog 接口返回）
      value: ${param.terminal_id}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: CbbTerminalCollectLogStatusDTO
      description: 终端日志收集状态
    content_terminalId:
      type: String
      description: 终端ID
    content_state:
      type: enum
      description: 收集状态
    content_message:
      type: String
      description: 失败信息
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].teacherTerminalId
  purpose: 教师终端ID来自教室终端列表查询出参（ViewClassroomInfoEntity.teacherTerminalId）
downstream: []
constraints:
- level: PARAM
  field: terminalId
  rule: 非空白
  failure: 参数校验失败（@NotBlank）
assertions:
  success:
  - scenario: 终端ID有效
    expect: $.status=="SUCCESS" 且 $.content.state 非空
  failure:
  - scenario: 终端ID无效
    trigger: 不存在的终端ID
    expect: $.status=="ERROR"（平台终端模块抛 BusinessException，msgKey 由终端模块决定）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询，可轮询
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/teacher/terminal/collectLog/get

> 查询教师机终端日志收集状态：按终端ID返回收集状态。 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/terminal/collectLog/get<br>查询教师机终端日志收集状态：按终端ID返回收集状态。<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 非空"]
        C2["Step2: cbbTerminalLogAPI.getCollectLog(request."]
        C3["Step3: 返回状态响应"]
        C1 --> C2
        C2 --> C3
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
| URL | /rcc/classroom/teacher/terminal/collectLog/get |
| Controller | RccTeacherManageController |
| 方法名 | getCollectLog |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 查询教师机终端日志收集状态：按终端ID返回收集状态。 |

## 入参详情

### TerminalIdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| terminalId | String | 是 | @NotBlank 非空白 | 教师终端ID（由 collectLog 接口返回） |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | CbbTerminalCollectLogStatusDTO | 终端日志收集状态 |
| content.terminalId | String | 终端ID |
| content.state | enum | 收集状态 |
| content.message | String | 失败信息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教师终端ID来自教室终端列表查询出参（ViewClassroomInfoEntity.teacherTerminalId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 非空
2. cbbTerminalLogAPI.getCollectLog(request.getTerminalId()) 查询状态
3. 返回状态响应

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | terminalId | 非空白 | 参数校验失败（@NotBlank） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| terminalId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 终端ID有效 | $.status=="SUCCESS" 且 $.content.state 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 终端ID无效 | 不存在的终端ID | $.status=="ERROR"（平台终端模块抛 BusinessException，msgKey 由终端模块决定） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读查询，可轮询 |
