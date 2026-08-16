---
version: '2.0'
api:
  url: /rcc/classroom/networkWhitelist/list
  method: POST
  name: 分页查询禁网白名单列表，按管理员终端组数据权限过滤
  controller: RccClassroomManageController
  method_ref: getNetworkWhiteList
  permission: 无
  exec_mode: sync
  async: false
  description: 分页查询禁网白名单列表，按管理员终端组数据权限过滤
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: PageWebRequest
  body:
    page:
      type: Integer
      required: false
      constraint: 分页参数
      description: 页码
    limit:
      type: Integer
      required: false
      constraint: 分页参数
      description: 每页条数
    matchArr:
      type: Match[]
      required: false
      constraint: 查询条件
      description: 匹配条件（含教室/IP等过滤）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: NetworkWhiteListDTO[]
      description: 白名单列表（元素字段见下）
    total:
      type: Long
      description: 总数
    id:
      type: UUID
      description: 白名单ID
    startIp:
      type: String
      description: 起始IP
    endIp:
      type: String
      description: 结束IP
    "itemArr[]_id":
      type: UUID
      description: 白名单ID
    "itemArr[]_startIp":
      type: String
      description: 起始IP
    "itemArr[]_endIp":
      type: String
      description: 结束IP
upstream:
- api: 内部调用:RccPermissionChecker
  purpose: 按管理员权限改写查询条件
- api: 内部调用:RccNetworkWhiteListAPI
  purpose: 分页查询白名单
downstream:
- api: POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList
  purpose: 出参 NetworkWhiteListDTO.id，白名单 ID 的唯一查询来源
constraints:
- level: request
  field: request/sessionContext
  rule: 非空
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 正常查询
    expect: $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空
  failure:
  - scenario: 权限不足
    trigger: 非授权管理员（checkTerminalGroupPermissionByQueryRequest 数据权限校验失败）
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
---
# POST /rcc/classroom/networkWhitelist/list

> 分页查询禁网白名单列表，按管理员终端组数据权限过滤 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/networkWhitelist/list<br>分页查询禁网白名单列表，按管理员终端组数据权限过滤<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/sessionContext 非空"]
        C2["Step2: 构造 NetworkWhiteListPageSearchRequest(req"]
        C3["Step3: rccPermissionChecker.checkTerminalGroupP"]
        C4["Step4: networkWhiteListAPI.pageQuery 分页查询并返回"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/networkWhitelist/list |
| Controller | RccClassroomManageController |
| 方法名 | getNetworkWhiteList |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 分页查询禁网白名单列表，按管理员终端组数据权限过滤 |

## 入参详情

### PageWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页参数 | 页码 |
| limit | Integer | 否 | 分页参数 | 每页条数 |
| matchArr | Match[] | 否 | 查询条件 | 匹配条件（含教室/IP等过滤） |

## 出参详情

| 返回类型 | DefaultWebResponse（data=DefaultPageResponse<NetworkWhiteListDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | NetworkWhiteListDTO[] | 白名单列表（元素字段见下） |
| total | Long | 总数 |
| id | UUID | 白名单ID |
| startIp | String | 起始IP |
| endIp | String | 结束IP |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert request/sessionContext 非空
2. 构造 NetworkWhiteListPageSearchRequest(request)
3. rccPermissionChecker.checkTerminalGroupPermissionByQueryRequest(apiRequest, sessionContext) 权限过滤
4. networkWhiteListAPI.pageQuery 分页查询并返回

## 下游消费方

### 消费1：POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList

出参 NetworkWhiteListDTO.id，白名单 ID 的唯一查询来源（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | request/sessionContext | 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常查询 | $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权（checkTerminalGroupPermissionByQueryRequest 校验失败） | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯查询接口 |
