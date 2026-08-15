---
version: '2.0'
api:
  url: /rcc/admin/dataPermission/edit
  method: POST
  name: 保存指定管理员（CDC子系统）在实训空间、VDI课堂桌面策略、TCI桌面策略上的数据权限，全量覆盖更新
  controller: RccAdminDataPermissionController
  method_ref: editDataPermission
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 保存指定管理员（CDC子系统）在实训空间、VDI课堂桌面策略、TCI桌面策略上的数据权限，全量覆盖更新
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: listSpace
  api: POST /rcc/space/list
  purpose: 按空间名精确过滤（exactMatchArr.fieldName=spaceName）
  extract:
    spaceId: $.content.itemArr[0].spaceId
  request:
    body:
      exactMatchArr:
      - type: EXACT
        fieldName: spaceName
        valueArr:
        - ${param.space_name}
        matchRule: EQ
- name: listVdiStrategy
  api: POST /space/strategygroup/vdi/list
  purpose: 按策略名精确过滤（matchArr.fieldName=strategyName）
  extract:
    vdiStrategyId: $.content.itemArr[0].id
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: strategyName
        valueArr:
        - ${param.strategy_name}
        matchRule: EQ
- name: listTciStrategy
  api: POST /space/strategy/tci/list
  purpose: 按策略名精确过滤（matchArr.fieldName=strategyName）
  extract:
    tciStrategyId: $.content.itemArr[0].id
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: strategyName
        valueArr:
        - ${param.strategy_name}
        matchRule: EQ
request:
  dto: AdminDataPermissionRequest
  body:
    userName:
      type: String
      required: true
      constraint: '@NotBlank 非空'
      description: 目标管理员用户名
      value: ${param.user_name}
    spaceArr:
      type: UUID[]
      required: false
      constraint: '@Nullable 可为空'
      description: 授予权限的实训空间ID数组
    lessonDeskStrategyArr:
      type: UUID[]
      required: false
      constraint: '@Nullable 可为空'
      description: VDI课堂桌面策略ID数组
    tciDeskStrategyIdArr:
      type: UUID[]
      required: false
      constraint: '@Nullable 可为空'
      description: TCI课程桌面策略ID数组
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
upstream:
- api: 内部调用:IacAdminMgmtAPI
  purpose: 按用户名+子系统CDC查询管理员，不存在则报错
- api: 内部调用:RccSpaceAPI
  purpose: 将spaceArr映射为桌面池ID列表（空间-桌面池关联）
- api: 内部调用:PlatformAdminDataPermissionAPI
  purpose: 按管理员ID全量更新数据权限（新增+删除指定权限）
- api: 内部调用:SpaceDeskStrategyGroupVDIAPI
  purpose: 删除前回查VDI策略组权限并转ID列表
downstream:
- api: 内部调用:PlatformAdminDataPermissionAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: userName
  rule: '@NotBlank 非空'
  failure: webmvc 参数校验异常
- level: business
  field: userName
  rule: 管理员必须存在于CDC子系统
  failure: rcdc_rcc_admin_not_exist
assertions:
  success:
  - scenario: 管理员存在且空间/策略有效
    expect: $.status==SUCCESS；content 为空（Builder.success() 无参，纯操作接口）；updateAdminDataPermission 全量更新完成
  failure:
  - scenario: 管理员不存在
    trigger: userName 对应用户在CDC不存在
    expect: $.status==ERROR；$.msgKey==rcdc_rcc_admin_not_exist（BusinessException key：DataPermissionBusinessKey.RCDC_RCC_ADMIN_NOT_EXIST）
  - scenario: 参数为空
    trigger: request/sessionContext 为 null
    expect: $.status==ERROR（参数校验，无固定 msgKey）
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为授权操作接口，不创建可清理资源；无对应 HTTP 删除接口
idempotency:
  level: data_level
  note: 每次提交都全量重建权限集；重复提交相同参数结果一致，但实现上先删后增，存在瞬时中间态
params:
  required:
  - name: space_name
    desc: ''
    used_by: 见 setup/request
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/admin/dataPermission/edit

> 保存指定管理员（CDC子系统）在实训空间、VDI课堂桌面策略、TCI桌面策略上的数据权限，全量覆盖更新 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/admin/dataPermission/edit<br>保存指定管理员（CDC子系统）在实训空间、VDI课堂桌面策略、TCI桌面策略上的<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/sessionContext 非空"]
        C2["Step2: baseAdminMgmtAPI.getAdminByUserName(user"]
        C3["Step3: getDeskPoolIdList(spaceArr)：遍历 rccSpaceA"]
        C4["Step4: addAdminDataPermission 组装 DESKTOP_POOL（桌"]
        C5["Step5: 计算待删除权限：getSpacePermission(桌面池权限ID) + ge"]
        C6["Step6: adminDataPermissionAPI.updateAdminDataPe"]
        C1 --> C2
        C7["Step7: 返回 DefaultWebResponse.success()"]
        C6 --> C7
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
| URL | /rcc/admin/dataPermission/edit |
| Controller | RccAdminDataPermissionController |
| 方法名 | editDataPermission |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 保存指定管理员（CDC子系统）在实训空间、VDI课堂桌面策略、TCI桌面策略上的数据权限，全量覆盖更新 |

## 入参详情

### AdminDataPermissionRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| userName | String | 是 | @NotBlank 非空 | 目标管理员用户名 |
| spaceArr | UUID[] | 否 | @Nullable 可为空 | 授予权限的实训空间ID数组 |
| lessonDeskStrategyArr | UUID[] | 否 | @Nullable 可为空 | VDI课堂桌面策略ID数组 |
| tciDeskStrategyIdArr | UUID[] | 否 | @Nullable 可为空 | TCI课程桌面策略ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|
| 说明 | 成功返回 SUCCESS；失败返回 status/msgKey |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert request/sessionContext 非空
2. baseAdminMgmtAPI.getAdminByUserName(userName, SubSystem.CDC) 查管理员，为 null 抛 DataPermissionBusinessKey.RCDC_RCC_ADMIN_NOT_EXIST
3. getDeskPoolIdList(spaceArr)：遍历 rccSpaceAPI.findAllSpace()，过滤出 spaceId 在 spaceArr 中的桌面池ID
4. addAdminDataPermission 组装 DESKTOP_POOL（桌面池）、DESKTOP_STRATEGY（lessonDeskStrategyArr、tciDeskStrategyIdArr）三类 CreateAdminDataPermissionRequest
5. 计算待删除权限：getSpacePermission(桌面池权限ID) + getDeskStrategyPermission(策略组权限ID)
6. adminDataPermissionAPI.updateAdminDataPermission(adminId, 新增列表, 删除列表) 全量覆盖
7. 返回 DefaultWebResponse.success()

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | userName | @NotBlank 非空 | webmvc 参数校验异常 |
| business | userName | 管理员必须存在于CDC子系统 | rcdc_rcc_admin_not_exist |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| userName | user_input/from_query | 按业务构造 |
| spaceArr | user_input/from_query | 按业务构造 |
| lessonDeskStrategyArr | user_input/from_query | 按业务构造 |
| tciDeskStrategyIdArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> 该接口为纯操作接口（Builder.success() 无 content body），断言以 HTTP 响应为准：status==SUCCESS + content 为空。无 content body（数据权限全量更新）


### 成功场景

| 场景 | 断言点 |
|---|---|
| 管理员存在且spaceArr/策略数组包含有效ID | $.status==SUCCESS；content 为空；权限按新增+删除全量更新完成 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 管理员不存在 | userName 对应用户在CDC不存在 | $.status==ERROR；$.msgKey==rcdc_rcc_admin_not_exist，不执行任何更新 |
| spaceArr 中空间无对应桌面池 | findAllSpace 结果不含该空间或桌面池为null | 该空间被跳过（返回null整体被忽略） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为授权操作接口，不创建可清理资源；无对应 HTTP 删除接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 每次提交都全量重建权限集；重复提交相同参数结果一致，但实现上先删后增，存在瞬时中间态 |
