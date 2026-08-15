---
version: '2.0'
api:
  url: /rcc/admin/dataPermission/query
  method: POST
  name: 查询指定管理员的实训空间、VDI/TCI桌面策略数据权限，返回带ID与名称的分组条目
  controller: RccAdminDataPermissionController
  method_ref: queryPermission
  permission: 无
  exec_mode: sync
  async: false
  description: 查询指定管理员的实训空间、VDI/TCI桌面策略数据权限，返回带ID与名称的分组条目
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: listAdmin
  api: POST /rco/admin/list
  purpose: 查询管理员ID（⚠️ jsonpath 待验证：出参 DTO 在外部模块）；取第一条（无名称过滤）
  extract:
    adminId: $.content.itemArr[0].id
request:
  dto: IdRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 管理员ID
      value: ${prev.listAdmin.output.adminId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    lessonDeskStrategyArr:
      type: GroupIdLabelEntry[]
      description: VDI桌面策略授权项（id+label）
    tciDeskStrategyIdArr:
      type: GroupIdLabelEntry[]
      description: TCI桌面策略授权项（id+label）
    spaceArr:
      type: GroupIdLabelEntry[]
      description: 实训空间授权项（id+label）
upstream:
- api: 内部调用:PlatformAdminDataPermissionAPI
  purpose: 查询策略组与桌面池类型下的授权数据ID
- api: 内部调用:SpaceDeskStrategyGroupVDIAPI
  purpose: VDI策略ID转名称label
- api: 内部调用:SpaceDeskStrategyGroupTCIAPI
  purpose: TCI策略ID转名称label
- api: 内部调用:RccSpaceAPI
  purpose: 桌面池权限ID映射回空间ID与名称
downstream: []
constraints:
- level: request
  field: id
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 管理员存在且已配置权限
    expect: $.status==SUCCESS；$.content != null（AdminDataPermissionInfoDTO；spaceArr/lessonDeskStrategyArr/tciDeskStrategyIdArr 为 GroupIdLabelEntry[]，未授权为 null）
  - scenario: 管理员无任何权限
    expect: $.status==SUCCESS；$.content 为对象且对应数组字段为 null/空
  failure:
  - scenario: 策略批量查询失败
    trigger: findByIds 抛 BusinessException
    expect: $.status==SUCCESS；对应数组为空（findByIds 抛 BusinessException 被 catch 吞掉，接口仍成功）
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为纯查询接口，不创建可清理资源；无对应 HTTP 删除接口
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
---
# POST /rcc/admin/dataPermission/query

> 查询指定管理员的实训空间、VDI/TCI桌面策略数据权限，返回带ID与名称的分组条目 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/admin/dataPermission/query<br>查询指定管理员的实训空间、VDI/TCI桌面策略数据权限，返回带ID与名称的分组<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert idRequest/sessionContext 非空"]
        C2["Step2: getDeskStrategyIdLabelEntryArr：按 PERMISS"]
        C3["Step3: getTciDeskStrategyIdLabelEntryArr：同类型权限I"]
        C4["Step4: getSpaceIdLabelEntryArr：按 PERMISSION_TYP"]
        C5["Step5: 返回 AdminDataPermissionInfoDTO"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
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
| URL | /rcc/admin/dataPermission/query |
| Controller | RccAdminDataPermissionController |
| 方法名 | queryPermission |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 查询指定管理员的实训空间、VDI/TCI桌面策略数据权限，返回带ID与名称的分组条目 |

## 入参详情

### IdRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull 非空 | 管理员ID |

## 出参详情

| 返回类型 | DefaultWebResponse<AdminDataPermissionInfoDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| lessonDeskStrategyArr | GroupIdLabelEntry[] | VDI桌面策略授权项（id+label） |
| tciDeskStrategyIdArr | GroupIdLabelEntry[] | TCI桌面策略授权项（id+label） |
| spaceArr | GroupIdLabelEntry[] | 实训空间授权项（id+label） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert idRequest/sessionContext 非空
2. getDeskStrategyIdLabelEntryArr：按 PERMISSION_TYPE_STRATEGY_GROUP 查权限ID，VDI查名称组装 lessonDeskStrategyArr
3. getTciDeskStrategyIdLabelEntryArr：同类型权限ID经TCI API组装 tciDeskStrategyIdArr
4. getSpaceIdLabelEntryArr：按 PERMISSION_TYPE_DESKTOP_POOL 查权限ID，遍历 findAllSpace 组装 spaceArr
5. 返回 AdminDataPermissionInfoDTO

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | id | @NotNull 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 管理员存在且已配置权限 | $.status==SUCCESS；$.content != null（AdminDataPermissionInfoDTO 对象） |
| 管理员无任何权限 | $.status==SUCCESS；对应数组字段为 null/空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略批量查询失败 | findByIds 抛 BusinessException | 捕获并返回空列表 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为纯查询接口，不创建可清理资源；无对应 HTTP 删除接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯查询接口，无副作用 |
