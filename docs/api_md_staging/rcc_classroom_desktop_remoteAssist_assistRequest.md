---
version: '2.0'
api:
  url: /rcc/classroom/desktop/remoteAssist/assistRequest
  method: POST
  name: 发起课堂云桌面远程协助请求：构造 RemoteAssistRequest 提交远程协助（课堂桌面自动同意），成功后清理协助缓存。
  controller: RccClassroomDesktopController
  method_ref: assistRequest
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 发起课堂云桌面远程协助请求：构造 RemoteAssistRequest 提交远程协助（课堂桌面自动同意），成功后清理协助缓存。
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
      description: 云桌面ID
      value: ${prev.query_desktop.output.desktopId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    msg:
      type: String
      description: 失败原因（i18n消息）
upstream:
- api: POST /rcc/classroom/desktop/list
  purpose: 桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream:
- api: 内部调用:PlatformRemoteAssistMgmtAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: id
  rule: 非空
  failure: 参数校验失败（@NotNull）
- level: BIZ
  field: desktop
  rule: 桌面必须存在
  failure: 桌面不存在时 applyRemoteAssist 抛异常，返回 rcdc_rcc_desktop_remote_assi
assertions:
  success:
  - scenario: 桌面存在且协助申请成功
    expect: $.status=="SUCCESS"（content 为空，Builder.success() 无参）
  failure:
  - scenario: 桌面不存在或协助申请失败
    trigger: getDesktopById 或 applyRemoteAssist 抛 BusinessException
    expect: status==ERROR；msgKey==rcdc_rcc_desktop_remote_assist_fail
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为纯操作接口，不创建可清理资源；无对应 HTTP 删除/回滚接口
idempotency:
  level: data_level
  note: 重复调用会重复发起协助申请，可能产生多个协助会话
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
# POST /rcc/classroom/desktop/remoteAssist/assistRequest

> 发起课堂云桌面远程协助请求：构造 RemoteAssistRequest 提交远程协助（课堂桌面自动同意），成功后清理协助缓存。 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/remoteAssist/assistRequest<br>发起课堂云桌面远程协助请求：构造 RemoteAssistRequest 提交远<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 session 非空"]
        C2["Step2: obtainDesktopName(id) 取桌面名"]
        C3["Step3: 构造 RemoteAssistRequest(id, session.userI"]
        C4["Step4: desktopMgmtAPI.getDesktopById 设置 resourc"]
        C5["Step5: remoteAssistInquire.applyRemoteAssist(re"]
        C6["Step6: userLoginRecordAPI.deleteRemoteAssistanc"]
        C1 --> C2
        C7["Step7: 记录成功审计并返回 success；catch BusinessExceptio"]
        C6 --> C7
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
| URL | /rcc/classroom/desktop/remoteAssist/assistRequest |
| Controller | RccClassroomDesktopController |
| 方法名 | assistRequest |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 发起课堂云桌面远程协助请求：构造 RemoteAssistRequest 提交远程协助（课堂桌面自动同意），成功后清理协助缓存。 |

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
| msg | String | 失败原因（i18n消息） |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 与 session 非空
2. obtainDesktopName(id) 取桌面名
3. 构造 RemoteAssistRequest(id, session.userId, session.userName)
4. desktopMgmtAPI.getDesktopById 设置 resourceId 与 deskType
5. remoteAssistInquire.applyRemoteAssist(remoteAssistRequest) 发起协助
6. userLoginRecordAPI.deleteRemoteAssistanceCache(resourceId) 清理缓存
7. 记录成功审计并返回 success；catch BusinessException 记录失败审计并返回 fail

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | 非空 | 参数校验失败（@NotNull） |
| BIZ | desktop | 桌面必须存在 | 桌面不存在时 applyRemoteAssist 抛异常，返回 rcdc_rcc_desktop_remote_assist_fail |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 桌面存在且协助申请成功 | $.status=="SUCCESS"（content 为空，Builder.success() 无参） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 桌面不存在或协助申请失败 | getDesktopById 或 applyRemoteAssist 抛 BusinessException | status==ERROR；msgKey==rcdc_rcc_desktop_remote_assist_fail |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为纯操作接口，不创建可清理资源；无对应 HTTP 删除/回滚接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 重复调用会重复发起协助申请，可能产生多个协助会话 |
