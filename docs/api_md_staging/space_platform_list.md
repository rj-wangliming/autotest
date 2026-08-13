---
version: '2.0'
api:
  url: /space/platform/list
  method: POST
  name: 分页查询云平台列表。调 platformServerMgmtAPI.pageQuery 查询 CloudPlatformDTO 分页，逐条转换为 CloudPl
  controller: SpacePlatformController
  method_ref: listPlatform
  permission: 无
  exec_mode: 同步分页：云平台分页查询 + extendConfig 脱敏（移除 password）+ DNS 域名补全
  async: false
  description: 分页查询云平台列表。调 platformServerMgmtAPI.pageQuery 查询 CloudPlatformDTO 分页，逐条转换为 CloudPlatformVO：拷贝基础字段；解析 extendConfig JSON 并移除 password 敏感字段，再按 address 调 dnsSdkAPI.getDomain 反查域名写入 extendConfig.domain；返回 Co
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: PageQueryRequest（框架类）
  body:
    page:
      type: Integer
      required: true
      constraint: 分页页码（0 基）
      description: pageQueryRequest.getPage()
    limit:
      type: Integer
      required: true
      constraint: 每页条数上限
      description: pageQueryRequest.getLimit()
    matchArr:
      type: Match[]
      required: false
      constraint: 精确匹配条件
      description: 框架 DMQL 视图过滤条件
    sortArr:
      type: Sort[]
      required: false
      constraint: 排序条件
      description: 框架透传
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: CloudPlatformVO[]
      description: 云平台列表
    total:
      type: long
      description: 总条数
    id:
      type: UUID
      description: 云平台 id
    name:
      type: String
      description: 云平台名称
    description:
      type: String
      description: 描述
    platformType:
      type: CloudPlatformType
      description: 平台类型
    status:
      type: CloudPlatformStatus
      description: 平台状态
    shouldDefault:
      type: Boolean
      description: 是否默认纳管
    connectMode:
      type: ConnectMode
      description: 连接方式
    createTime:
      type: Date
      description: 创建时间
    manageStatus:
      type: CloudPlatformManageStatus
      description: 管理状态
    cloudPlatformId:
      type: String
      description: 云平台 id（字符串）
    extendConfig:
      type: JSONObject
      description: 扩展配置（已移除 password 字段；按 address 反查并写入 domain 字段）
upstream:
- api: 内部调用:PlatformServerMgmtAPI
  purpose: 分页查询云平台
- api: 内部调用:DnsSdkAPI
  purpose: 按平台地址反查域名并写入 extendConfig.domain
downstream:
- api: POST /space/cluster/obtainComputeClusterList
  purpose: 内部调用（非 HTTP 端点）
- api: POST /space/storagePool/list
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: page/limit
  rule: 分页参数必填
  failure: Assert.notNull 异常（400）
- level: SECURITY
  field: extendConfig.password
  rule: 返回前端的扩展配置必须移除 password 字段
  failure: 密码泄露风险（代码显式 remove）
assertions:
  success:
  - scenario: 存在云平台
    expect: 返回 200，itemArr 为脱敏后的云平台列表
  - scenario: extendConfig 解析失败
    expect: $.status==SUCCESS；$.content.itemArr 非空（平台基础字段，extendConfig 可能为空），extendConfig 可能为空
  failure:
  - scenario: pageQueryRequest 为 null
    trigger: 请求体缺失
    expect: Assert.notNull 异常（400）
cleanup:
- api: 无
  note: 只读查询接口
idempotency:
  level: non_idempotent
  note: 只读查询，无副作用
---
# POST /space/platform/list

> 分页查询云平台列表。调 platformServerMgmtAPI.pageQuery 查询 CloudPlatformDTO 分页，逐条转换为 CloudPlatformVO：拷贝基础字段；解析 extendConfig JSON 并移除 password 敏感字段，再按 address 调 dnsSdkAPI.getDomain 反查域名写入 extendConfig.domain；返回 CommonWebResponse<PageQueryResponse<CloudPlatformVO>>。 ｜ 无特殊权限 ｜ 同步分页：云平台分页查询 + extendConfig 脱敏（移除 password）+ DNS 域名补全

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /space/platform/list<br>分页查询云平台列表。调 platformServerMgmtAPI.pageQu<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(pageQueryRequest)"]
        C2["Step2: platformServerMgmtAPI.pageQuery(pageQuer"]
        C3["Step3: 逐条 buildCloudPlatformVO：拷贝基础字段"]
        C4["Step4: 解析 extendConfig JSON；remove("password") "]
        C5["Step5: extendConfig 解析失败仅打 warn 日志不阻断"]
        C6["Step6: 返回 CommonWebResponse.success(PageQueryRe"]
        C1 --> C2
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
| URL | /space/platform/list |
| Controller | SpacePlatformController |
| 方法名 | listPlatform |
| 权限注解 | 无 |
| 执行方式 | 同步分页：云平台分页查询 + extendConfig 脱敏（移除 password）+ DNS 域名补全 |
| 业务含义 | 分页查询云平台列表。调 platformServerMgmtAPI.pageQuery 查询 CloudPlatformDTO 分页，逐条转换为 CloudPlatformVO：拷贝基础字段；解析 extendConfig JSON 并移除 password 敏感字段，再按 address 调 dnsSdkAPI.getDomain 反查域名写入 extendConfig.domain；返回 CommonWebResponse<PageQueryResponse<CloudPlatformVO>>。 |

## 入参详情

### PageQueryRequest（框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | 分页页码（0 基） | pageQueryRequest.getPage() |
| limit | Integer | 是 | 每页条数上限 | pageQueryRequest.getLimit() |
| matchArr | Match[] | 否 | 精确匹配条件 | 框架 DMQL 视图过滤条件 |
| sortArr | Sort[] | 否 | 排序条件 | 框架透传 |

## 出参详情

| 返回类型 | CommonWebResponse<PageQueryResponse<CloudPlatformVO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CloudPlatformVO[] | 云平台列表 |
| total | long | 总条数 |
| id | UUID | 云平台 id |
| name | String | 云平台名称 |
| description | String | 描述 |
| platformType | CloudPlatformType | 平台类型 |
| status | CloudPlatformStatus | 平台状态 |
| shouldDefault | Boolean | 是否默认纳管 |
| connectMode | ConnectMode | 连接方式 |
| createTime | Date | 创建时间 |
| manageStatus | CloudPlatformManageStatus | 管理状态 |
| cloudPlatformId | String | 云平台 id（字符串） |
| extendConfig | JSONObject | 扩展配置（已移除 password 字段；按 address 反查并写入 domain 字段） |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(pageQueryRequest)
2. platformServerMgmtAPI.pageQuery(pageQueryRequest) 分页查询云平台
3. 逐条 buildCloudPlatformVO：拷贝基础字段
4. 解析 extendConfig JSON；remove("password") 脱敏；按 address 调 dnsSdkAPI.getDomain 写入 domain
5. extendConfig 解析失败仅打 warn 日志不阻断
6. 返回 CommonWebResponse.success(PageQueryResponse<CloudPlatformVO>)

## 下游消费方

### 消费1：POST /space/platform/list

云平台ID，被 getClusterSupportEnablePersonalConfig 等消费（推断字段名 id/platformId）（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | page/limit | 分页参数必填 | Assert.notNull 异常（400） |
| SECURITY | extendConfig.password | 返回前端的扩展配置必须移除 password 字段 | 密码泄露风险（代码显式 remove） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 存在云平台 | 返回 200，itemArr 为脱敏后的云平台列表 |
| extendConfig 解析失败 | 仍返回平台基础字段，extendConfig 可能为空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| pageQueryRequest 为 null | 请求体缺失 | Assert.notNull 异常（400） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无 | 只读查询接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读查询，无副作用 |
