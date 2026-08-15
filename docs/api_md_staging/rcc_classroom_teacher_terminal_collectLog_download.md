---
version: '2.0'
api:
  url: /rcc/classroom/teacher/terminal/collectLog/download
  method: GET
  name: 下载教师机终端收集日志：按日志名获取文件信息，文件为空时报错，否则返回文件流。
  controller: RccTeacherManageController
  method_ref: downloadLog
  permission: 无
  exec_mode: sync
  async: false
  description: 下载教师机终端收集日志：按日志名获取文件信息，文件为空时报错，否则返回文件流。
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
request:
  dto: TerminalLogDownLoadWebRequest (GET 查询参数)
  body:
    logName:
      type: String
      required: true
      constraint: '@NotBlank 非空白'
      description: 日志文件名
      value: ${param.log_name}
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
      description: 日志文件流
    fileName/suffix:
      type: String
      description: 取自 CbbTerminalLogFileInfoDTO.logFileName/suffix
upstream:
- api: POST /rcc/classroom/teacher/terminal/collectLog
  produces: $.content.logName
  purpose: 推断：日志文件名由教师机日志收集接口产出，需先collectLog再get状态后下载，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: logName
  rule: 非空白
  failure: 参数校验失败（@NotBlank）
- level: BIZ
  field: logName
  rule: 日志文件必须存在且非空
  failure: 文件不存在抛业务异常；文件长度为0抛 rcdc_rcc_terminal_shine_error_get_shine_l
assertions:
  success:
  - scenario: 日志文件存在且非空
    expect: 'HTTP 200；响应为文件流（Content-Disposition: attachment，fileName/suffix 取自 CbbTerminalLogFileInfoDTO）'
  failure:
  - scenario: 日志文件为空
    trigger: 收集的日志文件长度为0
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_shine_error_get_shine_log_fail"
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读下载接口
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# GET /rcc/classroom/teacher/terminal/collectLog/download

> 下载教师机终端收集日志：按日志名获取文件信息，文件为空时报错，否则返回文件流。 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/teacher/terminal/collectLog"]
    end
    B["GET /rcc/classroom/teacher/terminal/collectLog/download<br>下载教师机终端收集日志：按日志名获取文件信息，文件为空时报错，否则返回文件流。<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 非空"]
        C2["Step2: cbbTerminalLogAPI.getTerminalLogFileInfo"]
        C3["Step3: File.length()==0 时抛 RCDC_RCC_TERMINAL_SH"]
        C4["Step4: 构造 DownloadWebResponse 返回文件"]
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
| URL | /rcc/classroom/teacher/terminal/collectLog/download |
| Controller | RccTeacherManageController |
| 方法名 | downloadLog |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 下载教师机终端收集日志：按日志名获取文件信息，文件为空时报错，否则返回文件流。 |

## 入参详情

### TerminalLogDownLoadWebRequest (GET 查询参数)

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| logName | String | 是 | @NotBlank 非空白 | 日志文件名 |

## 出参详情

| 返回类型 | DownloadWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| file | File | 日志文件流 |
| contentType | String | application/octet-stream |
| fileName | String | 日志文件名（取自 CbbTerminalLogFileInfoDTO.logFileName） |
| suffix | String | 文件后缀（取自 CbbTerminalLogFileInfoDTO.suffix） |

## 上游前置业务

### 前置1：POST /rcc/classroom/teacher/terminal/collectLog

推断：日志文件名由教师机日志收集接口产出，需先collectLog再get状态后下载，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 非空
2. cbbTerminalLogAPI.getTerminalLogFileInfo(logName) 获取文件信息
3. File.length()==0 时抛 RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL
4. 构造 DownloadWebResponse 返回文件

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | logName | 非空白 | 参数校验失败（@NotBlank） |
| BIZ | logName | 日志文件必须存在且非空 | 文件不存在抛业务异常；文件长度为0抛 rcdc_rcc_terminal_shine_error_get_shine_log_fail |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| logName | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 日志文件存在且非空 | HTTP 200；响应为文件流（Content-Disposition: attachment，fileName/suffix 取自 CbbTerminalLogFileInfoDTO） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 日志文件为空 | 收集的日志文件长度为0 | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_shine_error_get_shine_log_fail" |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读下载接口 |
