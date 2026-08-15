---
version: '2.0'
api:
  url: /rcc/classroom/desktop/tci/collectLog/getState
  method: POST
  name: 获取TCI桌面日志收集状态：权限校验后返回收集状态，DONE/FAULT 记录审计日志。
  controller: TCIDesktopOperateController
  method_ref: getCollectTCIDesktopLogState
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 获取TCI桌面日志收集状态：权限校验后返回收集状态，DONE/FAULT 记录审计日志。
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
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
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
  request:
    body:
      classroomId:
        value: ${prev.query_classroom.output.classroomId}
      desktopPreName:
        value: ${param.desktopPreName}
      desktopNameStartNum:
        value: ${param.desktopNameStartNum}
      seatNum:
        value: ${param.seatNum}
      studentModeArr:
        value: [VDI]
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
- name: query_desktop
  api: POST /rcc/classroom/desktop/list
  extract:
    desktopId: $.content.itemArr[0].desktopId
  purpose: 按桌面名过滤（matchArr.fieldName=computerName）
  request:
    body:
      matchArr:
      - type: FUZZY
        fieldNameArr:
        - computerName
        value: ${param.computer_name}
        matchRule: LIKE
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: TCI云桌面ID
      value: ${prev.query_classroom.output.classroomId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: CbbGtLogCollectStateDTO
      description: 日志收集状态（元素字段见下）
    content_deskId:
      type: UUID
      description: 云桌面ID
    content_state:
      type: GtLogCollectState
      description: 收集状态：DOING/DONE/FAULT
    content_logFileName:
      type: String
      description: 日志文件名
    content_message:
      type: String
      description: 失败时的错误信息
upstream:
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[0].desktopId
  purpose: 桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream: []
constraints:
- level: PARAM
  field: id
  rule: 非空
  failure: 参数校验失败（@NotNull）
- level: PERM
  field: session
  rule: 当前用户需有对应终端分组权限
  failure: 权限不足抛异常
assertions:
  success:
  - scenario: 日志收集完成
    expect: $.status=="SUCCESS"；$.content.state==DONE
  failure:
  - scenario: 日志收集失败
    trigger: 收集过程异常
    expect: $.status=="SUCCESS"；$.content.state==FAULT（审计 rcdc_rcc_tci_desktop_collect_log_fail）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询，可轮询
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
  - name: computer_name
  - name: desktopNameStartNum
    desc: ''
    used_by: 见 setup/request
  - name: desktopPreName
    desc: ''
    used_by: 见 setup/request
  - name: seatNum
    desc: ''
    used_by: 见 setup/request
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/desktop/tci/collectLog/getState

> 获取TCI桌面日志收集状态：权限校验后返回收集状态，DONE/FAULT 记录审计日志。 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/tci/collectLog/getState<br>获取TCI桌面日志收集状态：权限校验后返回收集状态，DONE/FAULT 记录审<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 session 非空"]
        C2["Step2: 权限校验（id）"]
        C3["Step3: obtainDesktopName(id) 取桌面名"]
        C4["Step4: cbbGuestToolLogAPI.getLogCollectState(id"]
        C5["Step5: DONE 记成功审计、FAULT 记失败审计（TCI专用key）"]
        C6["Step6: 返回状态"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
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
| URL | /rcc/classroom/desktop/tci/collectLog/getState |
| Controller | TCIDesktopOperateController |
| 方法名 | getCollectTCIDesktopLogState |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 获取TCI桌面日志收集状态：权限校验后返回收集状态，DONE/FAULT 记录审计日志。 |

## 入参详情

### IdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull 非空 | TCI云桌面ID |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | CbbGtLogCollectStateDTO | 日志收集状态（元素字段见下） |
| content.deskId | UUID | 云桌面ID |
| content.state | GtLogCollectState | 收集状态：DOING/DONE/FAULT |
| content.logFileName | String | 日志文件名 |
| content.message | String | 失败时的错误信息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 与 session 非空
2. 权限校验（id）
3. obtainDesktopName(id) 取桌面名
4. cbbGuestToolLogAPI.getLogCollectState(id) 查询状态
5. DONE 记成功审计、FAULT 记失败审计（TCI专用key）
6. 返回状态

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | 非空 | 参数校验失败（@NotNull） |
| PERM | session | 当前用户需有对应终端分组权限 | 权限不足抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 日志收集完成 | $.status=="SUCCESS"；$.content.state==DONE |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 日志收集失败 | 收集过程异常 | $.status=="SUCCESS"；$.content.state==FAULT（审计 rcdc_rcc_tci_desktop_collect_log_fail） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读查询，可轮询 |
