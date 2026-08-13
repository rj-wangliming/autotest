---
version: '2.0'
api:
  url: /rcc/classroom/desktop/tci/collectLog
  method: POST
  name: 收集TCI桌面日志：权限校验后向指定TCI桌面下发日志收集请求。
  controller: TCIDesktopOperateController
  method_ref: collectTCIDesktopLog
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 收集TCI桌面日志：权限校验后向指定TCI桌面下发日志收集请求。
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
        value: ${param.desktop_name}
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: TCI云桌面ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: Object
      description: 纯操作接口：content 为空（Builder.success() 无参）
upstream:
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[0].desktopId
  purpose: 桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream:
- api: 内部调用:PlatformGuestToolLogAPI
  purpose: 内部调用（非 HTTP 端点）
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
  - scenario: 用户有权限且桌面在线
    expect: $.status=="SUCCESS"（content 为空，Builder.success() 无参）
  failure:
  - scenario: 无终端分组权限
    trigger: 桌面不在用户所属终端分组
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
cleanup: []
idempotency:
  level: data_level
  note: 重复下发产生多次收集任务，结果以最新为准
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/desktop/tci/collectLog

> 收集TCI桌面日志：权限校验后向指定TCI桌面下发日志收集请求。 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/tci/collectLog<br>收集TCI桌面日志：权限校验后向指定TCI桌面下发日志收集请求。<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 session 非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: cbbGuestToolLogAPI.collectLog(request.ge"]
        C4["Step4: 返回 success"]
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
| URL | /rcc/classroom/desktop/tci/collectLog |
| Controller | TCIDesktopOperateController |
| 方法名 | collectTCIDesktopLog |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 收集TCI桌面日志：权限校验后向指定TCI桌面下发日志收集请求。 |

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

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 与 session 非空
2. rccPermissionChecker.checkTerminalGroupPermissionByDeskId 权限校验
3. cbbGuestToolLogAPI.collectLog(request.getId()) 下发日志收集
4. 返回 success

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
| 用户有权限且桌面在线 | $.status=="SUCCESS"（content 为空，Builder.success() 无参） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无终端分组权限 | 桌面不在用户所属终端分组 | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复下发产生多次收集任务，结果以最新为准 |
