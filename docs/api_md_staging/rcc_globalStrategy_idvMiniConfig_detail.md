---
version: '2.0'
api:
  url: /rcc/globalStrategy/idvMiniConfig/detail
  method: POST
  name: 查询IDV MINI服务器的全局策略配置（终端日志保留天数）
  controller: RccGlobalStrategyController
  method_ref: getIdvMiniConfigDetail
  permission: 无
  exec_mode: sync
  async: false
  description: 查询IDV MINI服务器的全局策略配置（终端日志保留天数）
request: {}
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    expireCleanDay:
      type: Integer
      description: 终端日志保留天数（到期自动清理）
upstream:
- api: 内部调用:RccGlobalStrategyAPI
  purpose: 查询终端日志保留配置（必须存在）
downstream: []
assertions:
  success:
  - scenario: 终端日志配置存在
    expect: $.content.expireCleanDay 非空
  failure:
  - scenario: 配置缺失
    trigger: 数据库无终端日志配置记录
    expect: $.status==SUCCESS（findRccTerminalLogConfigMustPrescent 配置缺失返回默认值，不抛异常）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
---
# POST /rcc/globalStrategy/idvMiniConfig/detail

> 查询IDV MINI服务器的全局策略配置（终端日志保留天数） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/globalStrategy/idvMiniConfig/detail<br>查询IDV MINI服务器的全局策略配置（终端日志保留天数）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: rccGlobalStrategyAPI.findRccTerminalLogC"]
        C2["Step2: 设置 expireCleanDay 并返回"]
        C1 --> C2
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
| URL | /rcc/globalStrategy/idvMiniConfig/detail |
| Controller | RccGlobalStrategyController |
| 方法名 | getIdvMiniConfigDetail |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 查询IDV MINI服务器的全局策略配置（终端日志保留天数） |

## 入参详情

### 

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页页码 | 当前页（框架自动注入） |
| limit | Integer | 否 | 分页行数 | 每页条数（框架自动注入） |
## 出参详情

| 返回类型 | DefaultWebResponse<RccGlobalStrategyIdvMiniResponse> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| expireCleanDay | Integer | 终端日志保留天数（到期自动清理） |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. rccGlobalStrategyAPI.findRccTerminalLogConfigMustPrescent() 取配置
2. 设置 expireCleanDay 并返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| （本接口无请求体参数约束） | | | |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 终端日志配置存在 | $.content.expireCleanDay 非空 |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 配置缺失 | 数据库无终端日志配置记录 | $.status==SUCCESS（findRccTerminalLogConfigMustPrescent 配置缺失返回默认值，不抛异常） |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯查询接口 |
