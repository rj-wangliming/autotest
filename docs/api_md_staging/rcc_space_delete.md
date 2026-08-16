---
version: '2.0'
api:
  url: /rcc/space/delete
  method: POST
  name: 删除实训桌面池（办公实训空间/教学桌面池）。入参 idArr 为空间ID数组（去重），shouldOnlyDeleteDataFromDb 为是否仅从数据库删除
  controller: RccSpaceController
  method_ref: deleteRccSpace
  permission: '@EnableAuthority'
  exec_mode: 批量异步（BatchTask）
  async: true
  description: 删除实训桌面池（办公实训空间/教学桌面池）。入参 idArr 为空间ID数组（去重），shouldOnlyDeleteDataFromDb 为是否仅从数据库删除（平台不可用时的强制删除）；先 rccSpaceAPI.findByIdIn 校验空间均存在，再构造 RccDeleteSpacePoolBatchHandler 提交批量任务（setUniqueId=idArr[0]，enablePara
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
- name: publish_space
  api: POST /rcc/space/publish
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按空间名过滤（name=${param.space_name}）
  request:
    body:
      name: ${param.space_name}
- name: list_space
  api: POST /rcc/space/list
  extract:
    spaceId: $.content.itemArr[0].id
  purpose: 按空间名精确过滤（exactMatchArr.fieldName=spaceName）
  request:
    body:
      exactMatchArr:
      - type: EXACT
        fieldName: spaceName
        valueArr:
        - ${param.space_name}
        matchRule: EQ
request:
  dto: RccDeleteSpaceRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty'
      description: 实训空间ID数组（删除对象，去重后逐项删除）
      value: ${param.id_arr}
    shouldOnlyDeleteDataFromDb:
      type: Boolean
      required: false
      constraint: '@Nullable'
      description: 是否仅从数据库删除数据（平台不可用时强制删除，跳过占用校验）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskId:
      type: UUID
      description: 批量删除任务ID
    taskStatus:
      type: String
      description: 任务状态
polling:
  api: common_get_msgct_detail_info
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    - PARTIAL_SUCCESS
    failure:
    - FAILURE
upstream:
- api: POST /rcc/space/list
  produces: $.content.id
  purpose: 实训空间ID数组，来源为 space list（publish 后产生）
downstream:
- api: 内部调用:rcc/RccSpaceAPI#deleteDesktopPoolAndSpaceInfo
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:pa/PlatformAdminDataPermissionAPI#deleteByPermissionDataId
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:rcc/SpaceClassroomPoolUserMgmtAPI#checkIsDesktopInUse
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: '@NotEmpty，不能为空'
  failure: Assert.notEmpty 失败
- level: BUSINESS
  field: idArr
  rule: 待删除空间必须存在
  failure: rccSpaceAPI.findByIdIn 抛 RCDC_RCC_SPACE_NOT_FOUND
- level: BUSINESS
  field: classroomId
  rule: 非强制删除时空间桌面未被使用
  failure: 使用中抛 RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL
- level: BUSINESS
  field: platformId
  rule: 强制删除时云平台不可用才允许（canForceDeleteIfUnavailable）
  failure: 平台可用状态下强制删除抛 RCDC_RCC_SPACE_POOL_UNAVAILABLE_DELETE_FAIL
assertions:
  success:
  - scenario: 删除未被使用的空间（多个）
    expect: 提交 enableParallel 批量删除任务，返回 BatchTaskSubmitResult；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 平台不可用且 shouldOnlyDeleteDataFromDb=true
    expect: 跳过占用校验直接删除数据库记录；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 空间正在被使用
    trigger: 教室桌面被用户/座位使用
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项 msgKey==RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL
  - scenario: 空间不存在
    trigger: idArr 含无效空间ID
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_POOL_NOT_FOUND
  - scenario: 平台可用但强删
    trigger: shouldOnlyDeleteDataFromDb=true 且平台在线
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]
cleanup: []
idempotency:
  level: data_level
  note: 批量任务 uniqueId=idArr[0] 防止同批重复提交；已删除的空间再次删除会因空间不存在而失败
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: space_name
  - name: id_arr
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/delete

> 删除实训桌面池（办公实训空间/教学桌面池）。入参 idArr 为空间ID数组（去重），shouldOnlyDeleteDataFromDb 为是否仅从数据库删除（平台不可用时的强制删除）；先 rccSpaceAPI.findByIdIn 校验空间均存在，再构造 RccDeleteSpacePoolBatchHandler 提交批量任务（setUniqueId=idArr[0]，enableParallel）。Handler 单条依次校验（强制删除时校验平台可强制删除；否则校验空间是否被使用，使用中抛 RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL）、删除云桌面/关联/空间/镜像记录、删除数据权限，并写审计日志。 ｜ @EnableAuthority ｜ 批量异步（BatchTask）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/space/list"]
    end
    B["POST /rcc/space/delete<br>删除实训桌面池（办公实训空间/教学桌面池）。入参 idArr 为空间ID数组（去<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/builder)，Assert.n"]
        C2["Step2: rccSpaceAPI.findByIdIn(idArr) 校验空间存在"]
        C3["Step3: 按 idArr 去重构造 DefaultBatchTaskItem 列表（ite"]
        C4["Step4: 构造 RccDeleteSpacePoolBatchHandler 并注入 ad"]
        C5["Step5: handler.setShouldOnlyDeleteDataFromDb(re"]
        C6["Step6: builder.setTaskName(RCDC_RCC_SPACE_POOL_"]
        C1 --> C2
        C7["Step7: 返回 BatchTaskSubmitResult"]
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
| URL | /rcc/space/delete |
| Controller | RccSpaceController |
| 方法名 | deleteRccSpace |
| 权限注解 | @EnableAuthority |
| 执行方式 | 批量异步（BatchTask） |
| 业务含义 | 删除实训桌面池（办公实训空间/教学桌面池）。入参 idArr 为空间ID数组（去重），shouldOnlyDeleteDataFromDb 为是否仅从数据库删除（平台不可用时的强制删除）；先 rccSpaceAPI.findByIdIn 校验空间均存在，再构造 RccDeleteSpacePoolBatchHandler 提交批量任务（setUniqueId=idArr[0]，enableParallel）。Handler 单条依次校验（强制删除时校验平台可强制删除；否则校验空间是否被使用，使用中抛 RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL）、删除云桌面/关联/空间/镜像记录、删除数据权限，并写审计日志。 |

## 入参详情

### RccDeleteSpaceRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotEmpty | 实训空间ID数组（删除对象，去重后逐项删除） |
| shouldOnlyDeleteDataFromDb | Boolean | 否 | @Nullable | 是否仅从数据库删除数据（平台不可用时强制删除，跳过占用校验） |

## 出参详情

| 返回类型 | CommonWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批量删除任务ID |
| taskStatus | String | 任务状态 |

## 上游前置业务

### 前置1：POST /rcc/space/list

实训空间ID数组，来源为 space list（publish 后产生）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RccDeleteSpacePoolBatchHandler

| 步骤 | 说明 |
|---|---|
| 1 | getSpaceDetailById(itemId) 获取空间详情并取空间名（区分办公实训空间/教室实训空间日志） |
| 2 | checkPoolBeforeDelete：shouldOnlyDeleteDataFromDb=true 时 classroomImageAPI.getClassroomPlatformId + platformStatusHelper.canForceDeleteIfUnavailable(platformId) 校验平台可强制删除；否则 spaceClassroomPoolUserMgmtAPI.checkIsDesktopInUse(classroomId)，使用中抛 RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL |
| 3 | rccSpaceAPI.deleteDesktopPoolAndSpaceInfo(spaceId) 删除云桌面、云桌面关联记录、实训空间记录、实训空间镜像记录 |
| 4 | adminDataPermissionAPI.deleteByPermissionDataId(spaceId) 删除该空间数据权限 |
| 5 | auditLogAPI.recordLog(删除成功日志)，返回 SUCCESS；BusinessException 时记录失败日志返回 FAILURE |
| 6 | onFinish：单条 RCDC_RCC_SPACE_POOL_DELETE_SINGLE_TASK_SUCCESS/FAIL，多条 RCDC_RCC_SPACE_POOL_DELETE_TASK_SUCCESS/FAIL |

### 处理流程

1. Assert.notNull(request/builder)，Assert.notEmpty(idArr)
2. rccSpaceAPI.findByIdIn(idArr) 校验空间存在
3. 按 idArr 去重构造 DefaultBatchTaskItem 列表（itemName=RCDC_RCC_SPACE_POOL_DELETE）
4. 构造 RccDeleteSpacePoolBatchHandler 并注入 adminDataPermissionAPI/rccSpaceAPI/auditLogAPI/spaceDeskVDIAPI/spaceClassroomPoolUserMgmtAPI/classroomImageAPI/platformStatusHelper
5. handler.setShouldOnlyDeleteDataFromDb(request.getShouldOnlyDeleteDataFromDb())
6. builder.setTaskName(RCDC_RCC_SPACE_POOL_DELETE).setTaskDesc(RCDC_RCC_SPACE_POOL_BATCH_DELETE_TASK_DESC).setUniqueId(idArr[0]).enableParallel().registerHandler(handler).start()
7. 返回 BatchTaskSubmitResult

## 下游消费方

### 消费1：POST /rcc/space/delete

删除后空间记录消失，detail/list 将查不到该 spaceId（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotEmpty，不能为空 | Assert.notEmpty 失败 |
| BUSINESS | idArr | 待删除空间必须存在 | rccSpaceAPI.findByIdIn 抛 RCDC_RCC_SPACE_NOT_FOUND |
| BUSINESS | classroomId | 非强制删除时空间桌面未被使用 | 使用中抛 RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL |
| BUSINESS | platformId | 强制删除时云平台不可用才允许（canForceDeleteIfUnavailable） | 平台可用状态下强制删除抛 RCDC_RCC_SPACE_POOL_UNAVAILABLE_DELETE_FAIL |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |
| shouldOnlyDeleteDataFromDb | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 删除未被使用的空间（多个） | 提交 enableParallel 批量删除任务，返回 BatchTaskSubmitResult |
| 平台不可用且 shouldOnlyDeleteDataFromDb=true | 跳过占用校验直接删除数据库记录 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 空间正在被使用 | 教室桌面被用户/座位使用 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项 msgKey==RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL |
| 空间不存在 | idArr 含无效空间ID | $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_POOL_NOT_FOUND |
| 平台可用但强删 | shouldOnlyDeleteDataFromDb=true 且平台在线 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"] |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 批量任务 uniqueId=idArr[0] 防止同批重复提交；已删除的空间再次删除会因空间不存在而失败 |
