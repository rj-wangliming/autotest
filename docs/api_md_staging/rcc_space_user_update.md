---
version: '2.0'
api:
  url: /rcc/space/user/update
  method: POST
  name: 编辑教学桌面池分配的用户/用户组（全量覆盖）。流程：rccSpaceAPI.getBaseDTOByClassroomId 校验空间存在（失败审计并返回 RCD
  controller: RccSpaceController
  method_ref: updatePoolBindObject
  permission: '@EnableAuthority'
  exec_mode: 批量异步（BatchTask）
  async: true
  description: 编辑教学桌面池分配的用户/用户组（全量覆盖）。流程：rccSpaceAPI.getBaseDTOByClassroomId 校验空间存在（失败审计并返回 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL）；BeanUtils.copyProperties → SpaceUpdatePoolBindObjectDTO；非超管时 getUserGroupIdAr
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
  purpose: 发布空间
request:
  dto: UpdatePoolBindObjectWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
      value: ${prev.select_classroom_id.output.classroomId}
    addUserByIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 新增用户ID列表
    deleteUserByIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 删除用户ID列表
    deleteUserByGroupIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 删除用户组下所有用户的用户组列表
    exceptList:
      type: List<GroupExceptUserDTO>
      required: false
      constraint: '@Nullable'
      description: 新增用户组下用户时排除的用户列表
    selectedGroupIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 全量桌面池分配的用户组列表
    selectedAdGroupIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 全量桌面池分配的 AD 安全组列表
    selectedLdapGroupIdList:
      type: List<UUID>
      required: false
      constraint: '@Nullable'
      description: 全量桌面池分配的 LDAP 组列表
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
      description: 批量任务ID
    taskStatus:
      type: String
      description: 任务状态
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
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
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID，来源为教室创建返回
- api: POST /space/user/listWithAssignment
  produces: $.content.itemArr[*].userId
  purpose: 新增用户ID列表，来源为用户分配信息列表（推断字段名 userId/id）
- api: POST /space/user/group/list
  produces: $.content.id
  purpose: 全量分配的用户组ID列表，来源为用户组树（推断字段名 id/groupId）
- api: POST /space/adGroup/listWithAssignment
  produces: $.content.itemArr[*].adGroupId
  purpose: 全量分配的AD安全组ID列表（推断字段名 adGroupId/id）
downstream:
- api: 内部调用:rcc/SpaceClassroomPoolUserMgmtAPI#updatePoolBindObject
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: Assert 失败
- level: BUSINESS
  field: classroomId
  rule: 空间必须存在
  failure: getBaseDTOByClassroomId 失败返回 RCDC_RCC_CLASSROOM_POOL_UPDATE_
- level: BUSINESS
  field: selectedGroupIdList/涉及用户组
  rule: 非超管涉及的用户组必须在权限内
  failure: 抛 RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH（62100120）
- level: BUSINESS
  field: 涉及用户
  rule: 非超管涉及用户的所属组必须在权限内
  failure: 抛 RCDC_RCC_CLASSROOM_POOL_NO_USER_AUTH（62100121）
assertions:
  success:
  - scenario: 超管更新绑定用户/用户组
    expect: 提交任务并返回 BatchTaskSubmitResult，任务成功更新绑定关系；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 非超管更新
    expect: 权限外已绑定用户组被保留，仅更新权限内部分；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 空间不存在
    trigger: classroomId 无效
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL
  - scenario: 越权操作用户组
    trigger: selectedGroupIdList 含权限外组
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH
cleanup: []
idempotency:
  level: data_level
  note: BatchTask uniqueId=classroomId 防止同教室并发重复任务；全量覆盖式更新，相同入参重复执行结果幂等但审计日志重复
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/user/update

> 编辑教学桌面池分配的用户/用户组（全量覆盖）。流程：rccSpaceAPI.getBaseDTOByClassroomId 校验空间存在（失败审计并返回 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL）；BeanUtils.copyProperties → SpaceUpdatePoolBindObjectDTO；非超管时 getUserGroupIdArr 获取管理员用户组权限并 desktopPoolWebHelper.checkGroupPermission 校验（RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH/NO_USER_AUTH）；构造单任务项注册 SpaceUpdateDesktopPoolUserBatchHandler 提交（setUniqueId=classroomId）。Handler 执行 updatePoolBindObject 更新绑定关系（非超管会把权限外已绑定的用户组加回 selectedGroupIdList 防止误删）。 ｜ @EnableAuthority ｜ 批量异步（BatchTask）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
        A2["POST /space/user/listWithAssignment"]
        A3["POST /space/user/group/list"]
        A4["POST /space/adGroup/listWithAssignment"]
    end
    B["POST /rcc/space/user/update<br>编辑教学桌面池分配的用户/用户组（全量覆盖）。流程：rccSpaceAPI.ge<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    A4 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/builder/sessionCo"]
        C2["Step2: rccSpaceAPI.getBaseDTOByClassroomId(clas"]
        C3["Step3: BeanUtils.copyProperties(request, bindOb"]
        C4["Step4: 非超管：permissionHelper.getUserGroupIdArr(u"]
        C5["Step5: 构造单任务 DefaultBatchTaskItem（itemName=RCDC"]
        C6["Step6: 构造 SpaceUpdateDesktopPoolUserBatchHandle"]
        C1 --> C2
        C7["Step7: builder.setTaskName(RCDC_RCC_CLASSROOM_P"]
        C8["Step8: 返回 CommonWebResponse.success(result)"]
        C6 --> C7
        C7 --> C8
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
| URL | /rcc/space/user/update |
| Controller | RccSpaceController |
| 方法名 | updatePoolBindObject |
| 权限注解 | @EnableAuthority |
| 执行方式 | 批量异步（BatchTask） |
| 业务含义 | 编辑教学桌面池分配的用户/用户组（全量覆盖）。流程：rccSpaceAPI.getBaseDTOByClassroomId 校验空间存在（失败审计并返回 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL）；BeanUtils.copyProperties → SpaceUpdatePoolBindObjectDTO；非超管时 getUserGroupIdArr 获取管理员用户组权限并 desktopPoolWebHelper.checkGroupPermission 校验（RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH/NO_USER_AUTH）；构造单任务项注册 SpaceUpdateDesktopPoolUserBatchHandler 提交（setUniqueId=classroomId）。Handler 执行 updatePoolBindObject 更新绑定关系（非超管会把权限外已绑定的用户组加回 selectedGroupIdList 防止误删）。 |

## 入参详情

### UpdatePoolBindObjectWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| addUserByIdList | List<UUID> | 否 | @Nullable | 新增用户ID列表 |
| deleteUserByIdList | List<UUID> | 否 | @Nullable | 删除用户ID列表 |
| deleteUserByGroupIdList | List<UUID> | 否 | @Nullable | 删除用户组下所有用户的用户组列表 |
| exceptList | List<GroupExceptUserDTO> | 否 | @Nullable | 新增用户组下用户时排除的用户列表 |
| selectedGroupIdList | List<UUID> | 否 | @Nullable | 全量桌面池分配的用户组列表 |
| selectedAdGroupIdList | List<UUID> | 否 | @Nullable | 全量桌面池分配的 AD 安全组列表 |
| selectedLdapGroupIdList | List<UUID> | 否 | @Nullable | 全量桌面池分配的 LDAP 组列表 |

## 出参详情

| 返回类型 | CommonWebResponse<?>（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批量任务ID |
| taskStatus | String | 任务状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID，来源为教室创建返回（由 field_map 契约映射）

### 前置2：POST /space/user/listWithAssignment

新增用户ID列表，来源为用户分配信息列表（推断字段名 userId/id）（由 field_map 契约映射）

### 前置3：POST /space/user/group/list

全量分配的用户组ID列表，来源为用户组树（推断字段名 id/groupId）（由 field_map 契约映射）

### 前置4：POST /space/adGroup/listWithAssignment

全量分配的AD安全组ID列表（推断字段名 adGroupId/id）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：SpaceUpdateDesktopPoolUserBatchHandler

| 步骤 | 说明 |
|---|---|
| 1 | rccSpaceAPI.getBaseDTOByClassroomId(classroomId) 取名称 |
| 2 | checkGroupAuthAndAddDefaultGroup：非超管时把权限外的已绑定用户组（listClassroomPoolUser 中 relatedId 不在 groupIdArr 的组）追加回 selectedGroupIdList |
| 3 | spaceClassroomPoolUserMgmtAPI.updatePoolBindObject(bindObjectDTO) 全量更新绑定关系 |
| 4 | 成功：auditLogAPI.recordLog(RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_ITEM_SUCCESS_DESC) |
| 5 | 失败：recordLog(ITEM_FAIL_DESC) 并抛 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_ITEM_FAIL_DESC |
| 6 | onFinish：RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_TASK_SUCCESS/FAIL |

### 处理流程

1. Assert.notNull(request/builder/sessionContext)
2. rccSpaceAPI.getBaseDTOByClassroomId(classroomId) 查空间；失败审计 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL_LOG 并返回 fail RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL
3. BeanUtils.copyProperties(request, bindObjectDTO)，setClassroomId
4. 非超管：permissionHelper.getUserGroupIdArr(userId)；desktopPoolWebHelper.checkGroupPermission(bindObjectDTO, groupIdArr)
5. 构造单任务 DefaultBatchTaskItem（itemName=RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ）
6. 构造 SpaceUpdateDesktopPoolUserBatchHandler 注入 rccSpaceAPI/auditLogAPI/spaceClassroomPoolUserMgmtAPI
7. builder.setTaskName(RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_TASK_NAME).setTaskDesc(...).setUniqueId(classroomId).registerHandler(handler).start()
8. 返回 CommonWebResponse.success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | Assert 失败 |
| BUSINESS | classroomId | 空间必须存在 | getBaseDTOByClassroomId 失败返回 RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL |
| BUSINESS | selectedGroupIdList/涉及用户组 | 非超管涉及的用户组必须在权限内 | 抛 RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH（62100120） |
| BUSINESS | 涉及用户 | 非超管涉及用户的所属组必须在权限内 | 抛 RCDC_RCC_CLASSROOM_POOL_NO_USER_AUTH（62100121） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| addUserByIdList | user_input/from_query | 按业务构造 |
| deleteUserByIdList | user_input/from_query | 按业务构造 |
| deleteUserByGroupIdList | user_input/from_query | 按业务构造 |
| exceptList | user_input/from_query | 按业务构造 |
| selectedGroupIdList | user_input/from_query | 按业务构造 |
| selectedAdGroupIdList | user_input/from_query | 按业务构造 |
| selectedLdapGroupIdList | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 超管更新绑定用户/用户组 | 提交任务并返回 BatchTaskSubmitResult，任务成功更新绑定关系 |
| 非超管更新 | 权限外已绑定用户组被保留，仅更新权限内部分 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 空间不存在 | classroomId 无效 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL |
| 越权操作用户组 | selectedGroupIdList 含权限外组 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | BatchTask uniqueId=classroomId 防止同教室并发重复任务；全量覆盖式更新，相同入参重复执行结果幂等但审计日志重复 |
