---
version: '2.0'
api:
  url: /rcc/classroom/seat/terminal/collectLog/get
  method: POST
  name: 查询终端日志收集状态（进行中/完成/失败），先做终端组权限校验
  controller: RccSeatManageController
  method_ref: getCollectLog
  permission: 无
  exec_mode: 同步
  async: false
  description: 查询终端日志收集状态（进行中/完成/失败），先做终端组权限校验
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
  api: POST /rcc/classroom/terminal/list
  extract:
    classroomId: $.content.itemArr[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
- name: create_seat
  api: POST /rcc/classroom/seat/batchCreate
  purpose: 批量创建座位（异步批处理任务）
  idempotent: recreate
  delete_api: /rcc/classroom/seat/delete
  delete_param: seatIdArr
- name: query_seat
  api: POST /rcc/classroom/seat/list
  extract:
    seatId: $.content.itemArr[0].id
    terminalId: $.content.itemArr[0].terminalId
  purpose: 按座位桌面名过滤（exactMatchArr.name=desktopName）
  request:
    body:
      exactMatchArr:
      - name: desktopName
        valueArr:
        - ${param.desktop_name}
request:
  dto: TerminalIdWebRequest
  body:
    terminalId:
      type: String
      required: true
      constraint: '@NotBlank'
      description: 终端ID（MAC 或终端SN）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    status:
      type: String
      description: 日志收集状态（待收集/收集中/完成等）
upstream:
- api: POST /rcc/classroom/seat/list
  produces: $.content.itemArr[0].terminalId
  purpose: 学生终端ID来自座位列表查询出参（SeatInfoDTO.terminalId）
downstream: []
constraints:
- level: PARAM
  field: terminalId
  rule: '@NotBlank'
  failure: 为空时参数校验失败
- level: PERM
  field: terminalId
  rule: 终端组数据权限
  failure: 无权限抛业务异常
assertions:
  success:
  - scenario: 传入已触发收集日志的终端ID
    expect: $.status=="SUCCESS" 且 $.content.status 非空
  failure:
  - scenario: terminalId 为空
    trigger: 请求体缺少字段
    expect: $.status=="ERROR"（参数校验失败，Assert.notNull）
  - scenario: 无终端组权限
    trigger: 权限校验抛错
    expect: $.status=="ERROR"（数据权限校验失败）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询，重复调用无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/terminal/collectLog/get

> 查询终端日志收集状态（进行中/完成/失败），先做终端组权限校验 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/terminal/collectLog/get<br>查询终端日志收集状态（进行中/完成/失败），先做终端组权限校验<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/sessionContext"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: cbbTerminalLogAPI.getCollectLog(terminal"]
        C4["Step4: 返回 DefaultWebResponse.success(response)"]
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
| URL | /rcc/classroom/seat/terminal/collectLog/get |
| Controller | RccSeatManageController |
| 方法名 | getCollectLog |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 查询终端日志收集状态（进行中/完成/失败），先做终端组权限校验 |

## 入参详情

### TerminalIdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| terminalId | String | 是 | @NotBlank | 终端ID（MAC 或终端SN） |

## 出参详情

| 返回类型 | DefaultWebResponse（data=CbbTerminalCollectLogStatusDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | 日志收集状态（待收集/收集中/完成等） |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

学生终端ID来自座位列表查询出参（SeatInfoDTO.terminalId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 request/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionByTerminalId 校验权限
3. cbbTerminalLogAPI.getCollectLog(terminalId) 查询收集状态
4. 返回 DefaultWebResponse.success(response)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | terminalId | @NotBlank | 为空时参数校验失败 |
| PERM | terminalId | 终端组数据权限 | 无权限抛业务异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| terminalId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入已触发收集日志的终端ID | $.status=="SUCCESS" 且 $.content.status 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| terminalId 为空 | 请求体缺少字段 | $.status=="ERROR"（参数校验失败，Assert.notNull） |
| 无终端组权限 | 权限校验抛错 | $.status=="ERROR"（数据权限校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询，重复调用无副作用 |
