---
version: '2.0'
api:
  url: /rcc/classroom/terminal/log/download
  method: GET
  name: 按日志文件名下载终端日志文件
  controller: RccClassroomManageController
  method_ref: downloadLog
  permission: 无
  exec_mode: sync
  async: false
  description: 按日志文件名下载终端日志文件
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
  dto: TerminalLogDownLoadWebRequest
  body:
    logName:
      type: String
      required: true
      constraint: '@NotBlank 非空'
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
    logName:
      type: String
      description: 下载文件名
    suffix:
      type: String
      description: 文件后缀
    file:
      type: File
      description: 日志文件内容流
upstream:
- api: POST /rcc/classroom/terminal/log/list
  produces: $.content.logName
  purpose: 推断：日志文件名来自终端日志列表查询出参（TerminalLogDTO.logName），字段名为推断
downstream: []
constraints:
- level: request
  field: logName
  rule: '@NotBlank 非空'
  failure: webmvc 参数校验异常
- level: business
  field: file
  rule: 日志文件不能为空
  failure: rcdc_rcc_terminal_shine_error_get_shine_log_fail
assertions:
  success:
  - scenario: 日志文件存在且非空
    expect: HTTP 200，返回文件流（DownloadWebResponse 文件下载响应）
  failure:
  - scenario: 日志文件为空
    trigger: 文件长度0
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_terminal_shine_error_get_shine_log_fail
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯下载操作
params:
  required:
  - name: classroom_name
  - name: log_name
    desc: ''
    used_by: 见 setup/request
---
# GET /rcc/classroom/terminal/log/download

> 按日志文件名下载终端日志文件 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/log/list"]
    end
    B["GET /rcc/classroom/terminal/log/download<br>按日志文件名下载终端日志文件<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request 非空"]
        C2["Step2: cbbTerminalLogAPI.getTerminalLogFileInfo"]
        C3["Step3: 文件长度==0 → 抛 RCDC_RCC_TERMINAL_SHINE_ERRO"]
        C4["Step4: 构造 DownloadWebResponse 返回文件下载"]
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
| URL | /rcc/classroom/terminal/log/download |
| Controller | RccClassroomManageController |
| 方法名 | downloadLog |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 按日志文件名下载终端日志文件 |

## 入参详情

### TerminalLogDownLoadWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| logName | String | 是 | @NotBlank 非空 | 日志文件名 |

## 出参详情

| 返回类型 | DownloadWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| logName | String | 下载文件名 |
| suffix | String | 文件后缀 |
| file | File | 日志文件内容流 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/log/list

推断：日志文件名来自终端日志列表查询出参（TerminalLogDTO.logName），字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert request 非空
2. cbbTerminalLogAPI.getTerminalLogFileInfo(logName) 取文件信息
3. 文件长度==0 → 抛 RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL
4. 构造 DownloadWebResponse 返回文件下载

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | logName | @NotBlank 非空 | webmvc 参数校验异常 |
| business | file | 日志文件不能为空 | rcdc_rcc_terminal_shine_error_get_shine_log_fail |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| logName | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 日志文件存在且非空 | HTTP 200，返回文件流（DownloadWebResponse 文件下载响应） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 日志文件为空 | 文件长度0 | $.status==ERROR && $.msgKey==rcdc_rcc_terminal_shine_error_get_shine_log_fail |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯下载操作 |
