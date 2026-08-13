---
version: '2.0'
api:
  url: /rcc/dashboard/statistics/classroomTerminalInfo
  method: POST
  name: 统计教室终端数量信息（在线终端数、终端总数）
  controller: RccDashboardStatisticsController
  method_ref: statisticsclassroomTerminalInfo
  permission: 无
  exec_mode: sync
  async: false
  description: 统计教室终端数量信息（在线终端数、终端总数）
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 造教室/终端数据使统计有值
  extract:
    classroomName: auto_classroom_<ts>
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    terminalOnlineNum:
      type: Integer
      description: 在线终端数（StatisticsTerminalInfoResponse.terminalOnlineNum）
    terminalTotalNum:
      type: Integer
      description: 终端总数（StatisticsTerminalInfoResponse.terminalTotalNum）
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 统计终端总数与在线数
downstream: []
constraints:
- level: request
  field: webRequest
  rule: 非空
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 正常统计
    expect: $.status==SUCCESS；$.content.terminalTotalNum 非空（>=0，StatisticsTerminalInfoResponse.terminalTotalNum）
  failure: []
cleanup:
- api: POST /rcc/classroom/delete
  purpose: 清理 setup 阶段创建用于造统计数据的教室（需先经 /rcc/classroom/list 获取 classroomId）；接口本身不创建资源
idempotency:
  level: non_idempotent
  note: 纯统计查询
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/dashboard/statistics/classroomTerminalInfo

> 统计教室终端数量信息（在线终端数、终端总数） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/dashboard/statistics/classroomTerminalInfo<br>统计教室终端数量信息（在线终端数、终端总数）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert webRequest 非空"]
        C2["Step2: classroomAPI.getStatisticssTerminalInfo("]
        C3["Step3: 返回 success(response)"]
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
| URL | /rcc/dashboard/statistics/classroomTerminalInfo |
| Controller | RccDashboardStatisticsController |
| 方法名 | statisticsclassroomTerminalInfo |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 统计教室终端数量信息（在线终端数、终端总数） |

## 入参详情

### DefaultWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页页码 | 当前页（框架自动注入） |
| limit | Integer | 否 | 分页行数 | 每页条数（框架自动注入） |
## 出参详情

| 返回类型 | DefaultWebResponse<StatisticsTerminalInfoResponse>（$.content 为 StatisticsTerminalInfoResponse） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| terminalOnlineNum | Integer | 在线终端数（StatisticsTerminalInfoResponse.terminalOnlineNum） |
| terminalTotalNum | Integer | 终端总数（StatisticsTerminalInfoResponse.terminalTotalNum） |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert webRequest 非空
2. classroomAPI.getStatisticssTerminalInfo() 统计
3. 返回 success(response)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | webRequest | 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常统计 | $.status==SUCCESS；$.content.terminalTotalNum 非空（>=0） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| POST /rcc/classroom/delete | 清理 setup 阶段创建用于造统计数据的教室（需先经 /rcc/classroom/list 获取 classroomId）；接口本身不创建资源 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯统计查询 |
