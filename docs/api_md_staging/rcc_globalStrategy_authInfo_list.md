---
version: '2.0'
api:
  url: /rcc/globalStrategy/authInfo/list
  method: POST
  name: 获取全部授权信息（License 列表）
  controller: RccGlobalStrategyController
  method_ref: obtainAuthInfoList
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 获取全部授权信息（License 列表）
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
    itemArr:
      type: CbbAuthInfoDTO[]
      description: 授权信息列表
    total:
      type: Long
      description: 授权信息总数
    itemArr[]_authType:
      type: String
      description: 授权类型
    itemArr[]_licenseDurationType:
      type: String
      description: 授权持续时间类型
    itemArr[]_total:
      type: Integer
      description: 总授权数
    itemArr[]_used:
      type: Integer
      description: 已使用授权数
    itemArr[]_tip:
      type: String
      description: 提示信息
    itemArr[]_classifyOccupiedNumMap:
      type: Map<String,Integer>
      description: 按分类统计的授权占用数
    itemArr[]_trailRemainder:
      type: Long
      description: 试用剩余天数
    itemArr[]_hasExpired:
      type: Boolean
      description: 是否已过期
upstream:
- api: 内部调用:RccLicenseAPI
  purpose: 查询全部License授权信息
downstream: []
assertions:
  success:
  - scenario: 正常查询
    expect: $.content.itemArr 非空
  failure:
  - scenario: 无权限
    trigger: 非管理员调用
    expect: status==ERROR（权限类 msgKey）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
---
# POST /rcc/globalStrategy/authInfo/list

> 获取全部授权信息（License 列表） ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/globalStrategy/authInfo/list<br>获取全部授权信息（License 列表）<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: rccLicenseAPI.obtainAllLicenseInfo() 获取全"]
        C2["Step2: 封装 DefaultPageResponse 返回"]
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
| URL | /rcc/globalStrategy/authInfo/list |
| Controller | RccGlobalStrategyController |
| 方法名 | obtainAuthInfoList |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 获取全部授权信息（License 列表） |

## 入参详情

### 

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页页码 | 当前页（框架自动注入） |
| limit | Integer | 否 | 分页行数 | 每页条数（框架自动注入） |
## 出参详情

| 返回类型 | DefaultWebResponse<DefaultPageResponse<CbbAuthInfoDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CbbAuthInfoDTO[] | 授权信息列表 |
| total | Long | 授权信息总数 |
| itemArr[].authType | String | 授权类型 |
| itemArr[].licenseDurationType | String | 授权持续时间类型 |
| itemArr[].total | Integer | 总授权数 |
| itemArr[].used | Integer | 已使用授权数 |
| itemArr[].tip | String | 提示信息 |
| itemArr[].classifyOccupiedNumMap | Map<String,Integer> | 按分类统计的授权占用数 |
| itemArr[].trailRemainder | Long | 试用剩余天数 |
| itemArr[].hasExpired | Boolean | 是否已过期 |
## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. rccLicenseAPI.obtainAllLicenseInfo() 获取全部授权信息
2. 封装 DefaultPageResponse 返回

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
| 正常查询 | $.content.itemArr 非空 |
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
| 说明 | 纯查询接口 |
