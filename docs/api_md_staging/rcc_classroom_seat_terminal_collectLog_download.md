---
version: '2.0'
api:
  url: /rcc/classroom/seat/terminal/collectLog/download
  method: GET
  name: 按日志文件名下载已收集的终端日志文件，文件为空时报错；返回 DownloadWebResponse 流式下载
  controller: RccSeatManageController
  method_ref: downloadLog
  permission: 无
  exec_mode: 同步（GET 下载）
  async: false
  description: 按日志文件名下载已收集的终端日志文件，文件为空时报错；返回 DownloadWebResponse 流式下载
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
request:
  dto: TerminalLogDownLoadWebRequest
  body:
    logName:
      type: String
      required: true
      constraint: '@NotBlank'
      description: 已收集的日志文件名
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    logFileName:
      type: String
      description: 带后缀的日志文件名
    suffix:
      type: String
      description: 文件后缀（如 zip/log）
upstream:
- api: POST /rcc/classroom/seat/terminal/collectLog
  produces: $.content.logName
  purpose: 推断：日志文件名由日志收集接口产出，需先collectLog再get状态后下载，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: logName
  rule: '@NotBlank'
  failure: 为空时参数校验失败
- level: BIZ
  field: logFilePath
  rule: 日志文件必须存在且非空
  failure: 文件不存在/为空抛 RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL
assertions:
  success:
  - scenario: 传入已生成的非空日志文件名
    expect: 'HTTP 200；响应为文件流（Content-Disposition: attachment，fileName/suffix 取自 CbbTerminalLogFileInfoDTO）'
  failure:
  - scenario: 日志文件为空
    trigger: shineLog.length()==0
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_shine_error_get_shine_log_fail"
  - scenario: logName 为空
    trigger: 请求缺参
    expect: $.status=="ERROR"（参数校验失败，Assert.notNull）
cleanup: []
idempotency:
  level: non_idempotent
  note: GET 下载操作，重复下载无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# GET /rcc/classroom/seat/terminal/collectLog/download

> 按日志文件名下载已收集的终端日志文件，文件为空时报错；返回 DownloadWebResponse 流式下载 ｜ 无特殊权限 ｜ 同步（GET 下载）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/terminal/collectLog"]
    end
    B["GET /rcc/classroom/seat/terminal/collectLog/download<br>按日志文件名下载已收集的终端日志文件，文件为空时报错；返回 DownloadWe<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request"]
        C2["Step2: cbbTerminalLogAPI.getTerminalLogFileInfo"]
        C3["Step3: new File(logFilePath) 若文件长度为 0 则抛 RCDC_R"]
        C4["Step4: 构造 DownloadWebResponse（setName(logFileNa"]
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
| URL | /rcc/classroom/seat/terminal/collectLog/download |
| Controller | RccSeatManageController |
| 方法名 | downloadLog |
| 权限注解 | 无 |
| 执行方式 | 同步（GET 下载） |
| 业务含义 | 按日志文件名下载已收集的终端日志文件，文件为空时报错；返回 DownloadWebResponse 流式下载 |

## 入参详情

### TerminalLogDownLoadWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| logName | String | 是 | @NotBlank | 已收集的日志文件名 |

## 出参详情

| 返回类型 | DownloadWebResponse（文件流下载） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| logFileName | String | 带后缀的日志文件名 |
| suffix | String | 文件后缀（如 zip/log） |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/terminal/collectLog

推断：日志文件名由日志收集接口产出，需先collectLog再get状态后下载，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 request
2. cbbTerminalLogAPI.getTerminalLogFileInfo(logName) 查询日志文件信息
3. new File(logFilePath) 若文件长度为 0 则抛 RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL
4. 构造 DownloadWebResponse（setName(logFileName, suffix).setFile(file)）返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | logName | @NotBlank | 为空时参数校验失败 |
| BIZ | logFilePath | 日志文件必须存在且非空 | 文件不存在/为空抛 RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| logName | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入已生成的非空日志文件名 | HTTP 200；响应为文件流（Content-Disposition: attachment，fileName/suffix 取自 CbbTerminalLogFileInfoDTO） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 日志文件为空 | shineLog.length()==0 | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_shine_error_get_shine_log_fail" |
| logName 为空 | 请求缺参 | $.status=="ERROR"（参数校验失败，Assert.notNull） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | GET 下载操作，重复下载无副作用 |
