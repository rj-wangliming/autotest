---
version: '2.0'
api:
  url: /space/adGroup/pool/realBindAdGroup/page
  method: POST
  name: 分页查询教室中真实绑定的 AD 安全组（仅已分配）
  controller: SpaceAdUserController
  method_ref: pageDesktopPoolRealBindUser
  permission: 无
  exec_mode: sync
  async: false
  description: 分页查询教室中真实绑定的 AD 安全组（仅已分配）
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室产生 classroomId
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: select_classroom_id
  api: POST /rcc/classroom/select
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  extract:
    classroomId: $.content[0].classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
request:
  dto: PageQueryRequest
  body:
    page:
      type: Integer
      required: true
      constraint: pagekit 分页参数
      description: 页码
    limit:
      type: Integer
      required: true
      constraint: pagekit 分页参数
      description: 每页条数
    matchArr:
      type: Match[]
      required: true
      constraint: 需含 classroomId 匹配条件
      description: 查询条件
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: AdGroupListDTO[]
      description: 真实绑定的AD安全组列表
    total:
      type: Long
      description: 总数
    itemArr[]_id:
      type: UUID
      description: 安全组ID
    itemArr[]_name:
      type: String
      description: 安全组名称
    itemArr[]_email:
      type: String
      description: 邮箱
    itemArr[]_domain:
      type: String
      description: 域（如 ruijiead.com.cn）
    itemArr[]_remark:
      type: String
      description: 备注
    itemArr[]_ou:
      type: String
      description: 所在文件夹（部门1/部门2）
    itemArr[]_objectGuid:
      type: String
      description: AD域组主键ID
    itemArr[]_serverType:
      type: DomainServerType
      description: 域服务器类型
    itemArr[]_createTime:
      type: Date
      description: 创建时间
    itemArr[]_updateTime:
      type: Date
      description: 更新时间
    itemArr[]_isAssigned:
      type: Boolean
      description: 是否已分配
    itemArr[]_disabled:
      type: Boolean
      description: 是否需要禁用
upstream:
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID（通过 exact match 字段 classroomId 传入），来源为教室创建返回
downstream: []
constraints:
- level: request
  field: request
  rule: 非空且需含 classroomId 匹配条件
  failure: 缺少classroomId时 Assert 失败
assertions:
  success:
  - scenario: 正常查询
    expect: $.content.itemArr 非空
  failure: []
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /space/adGroup/pool/realBindAdGroup/page

> 分页查询教室中真实绑定的 AD 安全组（仅已分配） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /space/adGroup/pool/realBindAdGroup/page<br>分页查询教室中真实绑定的 AD 安全组（仅已分配）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/sessionContext 非空"]
        C2["Step2: 解析 classroomId 与 matchList"]
        C3["Step3: pageQueryPoolAdGroup(request, matchList,"]
        C4["Step4: 返回 AdGroupListDTO 分页"]
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
| URL | /space/adGroup/pool/realBindAdGroup/page |
| Controller | SpaceAdUserController |
| 方法名 | pageDesktopPoolRealBindUser |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 分页查询教室中真实绑定的 AD 安全组（仅已分配） |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | pagekit 分页参数 | 页码 |
| limit | Integer | 是 | pagekit 分页参数 | 每页条数 |
| matchArr | Match[] | 是 | 需含 classroomId 匹配条件 | 查询条件 |

## 出参详情

| 返回类型 | CommonWebResponse<DefaultPageResponse<AdGroupListDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | AdGroupListDTO[] | 真实绑定的AD安全组列表 |
| total | Long | 总数 |
| itemArr[].id | UUID | 安全组ID |
| itemArr[].name | String | 安全组名称 |
| itemArr[].email | String | 邮箱 |
| itemArr[].domain | String | 域（如 ruijiead.com.cn） |
| itemArr[].remark | String | 备注 |
| itemArr[].ou | String | 所在文件夹（部门1/部门2） |
| itemArr[].objectGuid | String | AD域组主键ID |
| itemArr[].serverType | DomainServerType | 域服务器类型 |
| itemArr[].createTime | Date | 创建时间 |
| itemArr[].updateTime | Date | 更新时间 |
| itemArr[].isAssigned | Boolean | 是否已分配 |
| itemArr[].disabled | Boolean | 是否需要禁用 |
## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID（通过 exact match 字段 classroomId 传入），来源为教室创建返回（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert request/sessionContext 非空
2. 解析 classroomId 与 matchList
3. pageQueryPoolAdGroup(request, matchList, classroomId, assigned=true, page)
4. 返回 AdGroupListDTO 分页

## 下游消费方

### 消费1：POST /space/adGroup/pool/realBindAdGroup/page

真实绑定AD安全组ID列表（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | request | 非空且需含 classroomId 匹配条件 | 缺少classroomId时 Assert 失败 |

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
