---
version: '2.0'
api:
  url: /rcc/globalStrategy/idvMiniConfig/edit
  method: POST
  name: 设置IDV MINI全局策略（终端日志保留天数），有变化时更新并记录审计
  controller: RccGlobalStrategyController
  method_ref: editIdvMiniConfig
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 设置IDV MINI全局策略（终端日志保留天数），有变化时更新并记录审计
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: detail
  api: POST /rcc/globalStrategy/idvMiniConfig/detail
  purpose: 查询当前配置
  extract:
    expireCleanDay: $.content.expireCleanDay
request:
  dto: RccGlobalStrategyIdvMiniRequest
  body:
    expireCleanDay:
      type: Integer
      required: true
      constraint: '@NotNull 非空 + @Range(min=1,max=200)'
      description: 终端日志保留天数
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: 'null'
      description: 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_MODULE_OPERATE_SUCCESS）
upstream:
- api: 内部调用:RccGlobalStrategyAPI
  purpose: 取当前保留天数对比变化
downstream:
- api: 内部调用:RccGlobalStrategyAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: expireCleanDay
  rule: '@NotNull + @Range(1-200)'
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 保留天数有变化
    expect: $.status==SUCCESS
  - scenario: 保留天数无变化
    expect: $.status==SUCCESS
  failure: []
cleanup: []
idempotency:
  level: non_idempotent
  note: 值相同时跳过更新，重复提交幂等
---
# POST /rcc/globalStrategy/idvMiniConfig/edit

> 设置IDV MINI全局策略（终端日志保留天数），有变化时更新并记录审计 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/globalStrategy/idvMiniConfig/edit<br>设置IDV MINI全局策略（终端日志保留天数），有变化时更新并记录审计<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request 非空"]
        C2["Step2: editRccTerminalLogConfig：与当前配置对比，不同则 edi"]
        C3["Step3: 返回 success(RCDC_RCC_MODULE_OPERATE_SUCCE"]
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
| URL | /rcc/globalStrategy/idvMiniConfig/edit |
| Controller | RccGlobalStrategyController |
| 方法名 | editIdvMiniConfig |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 设置IDV MINI全局策略（终端日志保留天数），有变化时更新并记录审计 |

## 入参详情

### RccGlobalStrategyIdvMiniRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| expireCleanDay | Integer | 是 | @NotNull 非空 + @Range(min=1,max=200) | 终端日志保留天数 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | null | 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_MODULE_OPERATE_SUCCESS） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert request 非空
2. editRccTerminalLogConfig：与当前配置对比，不同则 editRccTerminalLogConfig(buildTerminalLogConfigDTO()) 并记录 RCDC_RCC_GLOBAL_STRATEGY_TERMINAL_LOG_CONFIG_SUCCESS 审计
3. 返回 success(RCDC_RCC_MODULE_OPERATE_SUCCESS)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | expireCleanDay | @NotNull + @Range(1-200) | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| expireCleanDay | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 保留天数有变化 | $.status==SUCCESS |
| 保留天数无变化 | $.status==SUCCESS |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 值相同时跳过更新，重复提交幂等 |
