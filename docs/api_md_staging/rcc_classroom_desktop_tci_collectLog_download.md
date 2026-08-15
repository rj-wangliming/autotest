---
version: '2.0'
api:
  url: /rcc/classroom/desktop/tci/collectLog/download
  method: GET
  name: 下载TCI桌面日志文件：权限校验后按日志文件名返回二进制文件流（文件名插入 _tci_deskIp）。
  controller: TCIDesktopOperateController
  method_ref: download
  permission: 无
  exec_mode: sync
  async: false
  description: 下载TCI桌面日志文件：权限校验后按日志文件名返回二进制文件流（文件名插入 _tci_deskIp）。
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
  dto: TCIDownloadGtLogWebRequest (GET 查询参数)
  body:
    logFileName:
      type: String
      required: true
      constraint: '@NotBlank 非空白'
      description: 日志文件名（带后缀）
    deskId:
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
    file:
      type: File
      description: 日志文件二进制流
    contentType:
      type: String
      description: application/octet-stream
upstream:
- api: POST /rcc/classroom/desktop/tci/collectLog
  produces: $.content.logFileName
  purpose: 推断：日志文件名由TCI日志收集接口产出，字段名为推断
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[0].desktopId
  purpose: 桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream: []
constraints:
- level: PARAM
  field: logFileName
  rule: 非空白
  failure: 参数校验失败（@NotBlank）
- level: PERM
  field: session
  rule: 当前用户需有对应终端分组权限
  failure: 权限不足抛异常
- level: BIZ
  field: logFileName
  rule: 日志文件必须存在
  failure: rcdc_clouddesktop_gt_log_download_file_not_exist
assertions:
  success:
  - scenario: 日志文件存在且有权限
    expect: 'HTTP 200，返回文件流（content-type: application/octet-stream）'
  failure:
  - scenario: 日志文件不存在
    trigger: getLogFilePath 抛 BusinessException
    expect: status==ERROR；msgKey==rcdc_clouddesktop_gt_log_download_file_not_exist
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读下载接口
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
# GET /rcc/classroom/desktop/tci/collectLog/download

> 下载TCI桌面日志文件：权限校验后按日志文件名返回二进制文件流（文件名插入 _tci_deskIp）。 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/tci/collectLog"]
        A2["POST /rcc/classroom/desktop/list"]
    end
    B["GET /rcc/classroom/desktop/tci/collectLog/download<br>下载TCI桌面日志文件：权限校验后按日志文件名返回二进制文件流（文件名插入 _t<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 session 非空"]
        C2["Step2: 权限校验（deskId）"]
        C3["Step3: cbbGuestToolLogAPI.getLogFilePath(logFil"]
        C4["Step4: 文件名插入 _tci_deskIp 重命名"]
        C5["Step5: 构造 DownloadWebResponse 返回文件"]
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
| URL | /rcc/classroom/desktop/tci/collectLog/download |
| Controller | TCIDesktopOperateController |
| 方法名 | download |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 下载TCI桌面日志文件：权限校验后按日志文件名返回二进制文件流（文件名插入 _tci_deskIp）。 |

## 入参详情

### TCIDownloadGtLogWebRequest (GET 查询参数)

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| logFileName | String | 是 | @NotBlank 非空白 | 日志文件名（带后缀） |
| deskId | UUID | 是 | @NotNull 非空 | TCI云桌面ID |

## 出参详情

| 返回类型 | DownloadWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| file | File | 日志文件二进制流 |
| contentType | String | application/octet-stream |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/tci/collectLog

推断：日志文件名由TCI日志收集接口产出，字段名为推断（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/desktop/list

桌面ID来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 与 session 非空
2. 权限校验（deskId）
3. cbbGuestToolLogAPI.getLogFilePath(logFileName) 取文件路径
4. 文件名插入 _tci_deskIp 重命名
5. 构造 DownloadWebResponse 返回文件

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | logFileName | 非空白 | 参数校验失败（@NotBlank） |
| PERM | session | 当前用户需有对应终端分组权限 | 权限不足抛异常 |
| BIZ | logFileName | 日志文件必须存在 | rcdc_clouddesktop_gt_log_download_file_not_exist |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| logFileName | user_input/from_query | 按业务构造 |
| deskId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 日志文件存在且有权限 | HTTP 200，返回文件流（content-type: application/octet-stream） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 日志文件不存在 | getLogFilePath 抛 BusinessException | status==ERROR；msgKey==rcdc_clouddesktop_gt_log_download_file_not_exist |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读下载接口 |
