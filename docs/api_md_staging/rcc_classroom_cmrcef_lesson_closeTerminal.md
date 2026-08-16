---
version: '2.0'
api:
  url: /rcc/classroom/cmrcef/lesson/closeTerminal
  method: POST
  name: CMR内嵌页面（CEF）下课场景下关闭教室学生机终端
  controller: RccClassroomCmrcefController
  method_ref: closeTerminalForCef
  permission: 无
  exec_mode: sync
  async: false
  description: CMR内嵌页面（CEF）下课场景下关闭教室学生机终端
setup:
- name: up_1
  api: 内部调用:seatAPI
  method: POST
  produces: void
  purpose: （内部调用）
request:
  dto: CefClassroomRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull，教室ID'
      description: 要关闭终端的教室
      value: ${param.classroom_id}
    token:
      type: String
      required: true
      constraint: '@NotNull，AES加密的TOKEN'
      description: AES加密后内容为classroomId，由@ClassroomCef拦截器校验
      value: ${param.token}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
upstream:
- api: 内部调用:seatAPI
  purpose: 向教室所有学生机终端下发关机指令
downstream:
- api: 内部调用:seatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: auth
  field: token
  rule: token需通过AES解密且等于classroomId
  failure: rcdc_rcc_classroom_cef_token_check_failure
- level: request
  field: classroomId
  rule: 可为空（为空时跳过关机）
  failure: 无，跳过关机直接返回成功
assertions:
  success:
  - scenario: 教室存在
    expect: $.status==SUCCESS（content 为空，Builder.success() 无参，纯操作接口）
  failure:
  - scenario: 参数为空
    trigger: webRequest 为 null
    expect: $.status==ERROR（参数校验，无固定 msgKey）
  - scenario: token非法
    trigger: token缺失/解密失败/与classroomId不一致
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure
cleanup: []
idempotency:
  level: data_level
  note: 关机指令重复下发无校验，非严格幂等
params:
  required:
  - name: classroom_id
  - name: token
---
# POST /rcc/classroom/cmrcef/lesson/closeTerminal

> CMR内嵌页面（CEF）下课场景下关闭教室学生机终端 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmrcef/lesson/closeTerminal<br>CMR内嵌页面（CEF）下课场景下关闭教室学生机终端<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) 校验入参"]
        C2["Step2: @ClassroomCef拦截器校验token：AES解密token与class"]
        C3["Step3: classroomId非空则调用seatAPI.shutdownTerminal"]
        C4["Step4: 返回DefaultWebResponse.success()"]
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
| URL | /rcc/classroom/cmrcef/lesson/closeTerminal |
| Controller | RccClassroomCmrcefController |
| 方法名 | closeTerminalForCef |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | CMR内嵌页面（CEF）下课场景下关闭教室学生机终端 |

## 入参详情

### CefClassroomRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull，教室ID | 要关闭终端的教室 |
| token | String | 是 | @NotNull，AES加密的TOKEN | AES加密后内容为classroomId，由@ClassroomCef拦截器校验 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|
| 说明 | 成功返回 SUCCESS；失败返回 status/msgKey |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(webRequest) 校验入参
2. @ClassroomCef拦截器校验token：AES解密token与classroomId一致，否则抛rcdc_rcc_classroom_cef_token_check_failure
3. classroomId非空则调用seatAPI.shutdownTerminal(classroomId)关闭学生机
4. 返回DefaultWebResponse.success()

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| auth | token | token需通过AES解密且等于classroomId | rcdc_rcc_classroom_cef_token_check_failure |
| request | classroomId | 可为空（为空时跳过关机） | 无，跳过关机直接返回成功 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| token | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> 该接口为纯操作接口（Builder.success() 无 content body），断言以 HTTP 响应为准：status==SUCCESS + content 为空。无 content body（CMR 教师端关闭学生机）


### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室存在 | $.status==SUCCESS（content 为空，Builder.success() 无参，纯操作接口） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 参数为空 | webRequest 为 null | $.status==ERROR（参数校验，无固定 msgKey） |
| token非法 | token缺失/解密失败/与classroomId不一致 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 关机指令重复下发无校验，非严格幂等 |
