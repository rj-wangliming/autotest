---
version: '2.0'
api:
  url: /rcc/classroom/desktop/gtlog/getState
  method: POST
  name: 获取云桌面GT日志收集状态：返回当前收集状态（DOING/DONE/FAULT），DONE/FAULT 时记录审计日志。
  controller: RccClassroomDesktopController
  method_ref: getState
  permission: 无
  exec_mode: sync
  async: false
  description: 获取云桌面GT日志收集状态：返回当前收集状态（DOING/DONE/FAULT），DONE/FAULT 时记录审计日志。
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
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
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
- name: query_desktop
  api: POST /rcc/classroom/desktop/list
  extract:
    desktopId: $.content.itemArr[0].desktopId
  purpose: 按桌面名过滤（matchArr.fieldName=computerName）
  request:
    body:
      matchArr:
      - fieldName: computerName
        matchType: LIKE
        value: ${param.computer_name}
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 云桌面ID
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
      description: 日志收集状态
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
assertions:
  success:
  - scenario: 日志收集完成
    expect: $.status=="SUCCESS"；$.content.state==DONE
  failure:
  - scenario: 日志收集失败
    trigger: 桌面收集日志过程中出现异常
    expect: $.status=="SUCCESS"；$.content.state==FAULT（审计 rcdc_rcc_desktop_collect_log_error）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询，可重复轮询
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
  - name: computer_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/desktop/gtlog/getState

> 获取云桌面GT日志收集状态：返回当前收集状态（DOING/DONE/FAULT），DONE/FAULT 时记录审计日志。 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/gtlog/getState<br>获取云桌面GT日志收集状态：返回当前收集状态（DOING/DONE/FAULT）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 非空"]
        C2["Step2: obtainDesktopName(id) 获取桌面名（失败时回退为UUID）"]
        C3["Step3: cbbGuestToolLogAPI.getLogCollectState(id"]
        C4["Step4: DONE 记成功审计；FAULT 记失败审计（含错误信息）"]
        C5["Step5: 返回状态响应"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
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
| URL | /rcc/classroom/desktop/gtlog/getState |
| Controller | RccClassroomDesktopController |
| 方法名 | getState |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 获取云桌面GT日志收集状态：返回当前收集状态（DOING/DONE/FAULT），DONE/FAULT 时记录审计日志。 |

## 入参详情

### IdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull 非空 | 云桌面ID |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | CbbGtLogCollectStateDTO | 日志收集状态 |
| content.deskId | UUID | 云桌面ID |
| content.state | GtLogCollectState | 收集状态：DOING/DONE/FAULT |
| content.logFileName | String | 日志文件名 |
| content.message | String | 失败时的错误信息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 非空
2. obtainDesktopName(id) 获取桌面名（失败时回退为UUID）
3. cbbGuestToolLogAPI.getLogCollectState(id) 查询状态
4. DONE 记成功审计；FAULT 记失败审计（含错误信息）
5. 返回状态响应

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | 非空 | 参数校验失败（@NotNull） |

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
| 日志收集失败 | 桌面收集日志过程中出现异常 | $.status=="SUCCESS"；$.content.state==FAULT（审计 rcdc_rcc_desktop_collect_log_error） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读查询，可重复轮询 |
