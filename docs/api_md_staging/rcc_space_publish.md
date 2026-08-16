---
version: '2.0'
api:
  url: /rcc/space/publish
  method: POST
  name: 教学桌面池-发布（将教室发布为实训空间）。流程：先校验教室未发布（findByClassroomId 非空抛 RCDC_RCC_SPACE_PUBLISH_FA
  controller: RccSpaceController
  method_ref: publish
  permission: '@EnableAuthority'
  exec_mode: 同步
  async: false
  description: 教学桌面池-发布（将教室发布为实训空间）。流程：先校验教室未发布（findByClassroomId 非空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH）、无运行中的删除状态机（stateMachineFactory.findByResourceId 存在抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_
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
- name: list_image
  api: POST /rcc/space/image/list
  extract:
    imageTemplateIdArr: $.content.itemArr[*].id
  purpose: 获取可用镜像ID数组（⚠️ jsonpath 待验证：出参 DTO 在外部模块）
- name: publish_space
  api: POST /rcc/space/publish
  purpose: 发布教学桌面池
request:
  dto: RccPublicClassroomSpaceWebRequest
  body:
    name:
      type: String
      required: true
      constraint: '@NotBlank @TextShort @TextName'
      description: 实训空间名称
      value: ${param.name}
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 绑定的教室ID
      value: ${prev.select_classroom_id.output.classroomId}
    imageTemplateIdArr:
      type: UUID[]
      required: true
      constraint: '@NotNull（逻辑上不能为空数组）'
      description: 绑定的镜像ID数组
      value: ${prev.list_image.output.imageTemplateIdArr}
    idleDesktopRecover:
      type: Integer
      required: false
      constraint: '@Nullable @Range(0-99999999)'
      description: 空闲桌面自动回收时间（分钟）
    enableAllowMaxUseTime:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 是否开启单次允许接入最大时间配置
      value: false
    allowMaxUseTime:
      type: Integer
      required: false
      constraint: '@Nullable @Range(30-144000)'
      description: 单次允许接入最大时间
    beforeRecycleNotifyTime:
      type: Integer
      required: false
      constraint: '@Nullable @Range(1-144000)'
      description: 断开连接前提示时间
    enableAllowUseTimeInfo:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 是否开启云桌面允许登录时间
      value: false
    allowUseTimeInfoArr:
      type: RccAllowUseTimeInfoDTO[]
      required: false
      constraint: '@Nullable'
      description: 云桌面允许登录时间段数组
    description:
      type: String
      required: false
      constraint: '@Nullable @TextMedium'
      description: 描述
    enableSpecifiedIpRange:
      type: Boolean
      required: false
      constraint: '@Nullable（默认 false）'
      description: 是否开启指定终端IP访问
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    data:
      type: String
      description: 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_SUCCESS）（源码：CommonWebResponse.success(msgKey,args)，content 为空）
upstream:
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID，来源为教室创建返回
- api: POST /rcc/space/image/list
  produces: $.content.itemArr[*].id
  purpose: 绑定镜像ID数组，来源为本地镜像模板列表（已过滤课堂镜像）
downstream:
- api: 内部调用:rcc/RccSpaceAPI#publishSpace
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:rcc/AdminPermissionHelper#saveAdminGroupPermission
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: name
  rule: '@NotBlank @TextShort @TextName'
  failure: 名称校验失败
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: imageTemplateIdArr
  rule: '@NotNull 且非空数组'
  failure: 空数组抛 RCDC_RCC_SPACE_PUBLISH_FAIL_IMAGETEMPLATE_NOT_ALLOW_NUL
- level: BUSINESS
  field: classroomId
  rule: 教室未发布
  failure: 已发布抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH
- level: BUSINESS
  field: classroomId
  rule: 无运行中的删除/状态机任务
  failure: 存在抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_
- level: BUSINESS
  field: classroomId
  rule: 教室必须存在
  failure: 抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND
- level: BUSINESS
  field: imageTemplateIdArr
  rule: 镜像必须归属该教室且已发布
  failure: 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_IMAGE_NOT_BELONG_CLASSROOM
- level: BUSINESS
  field: name
  rule: 名称不得与已有空间重复
  failure: 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_NAME_HAS_EXIST
assertions:
  success:
  - scenario: 教室未发布且镜像已分配给学生
    expect: $.status==SUCCESS
  - scenario: 允许登录时间/最大时长已配置
    expect: $.status==SUCCESS
  failure:
  - scenario: 教室已发布
    trigger: findByClassroomId 非空
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH
  - scenario: 教室不存在
    trigger: classroomId 无效
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND
  - scenario: 镜像不属于该教室
    trigger: imageTemplateIdArr 含未分配镜像
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_CLASSROOM_POOL_IMAGE_NOT_BELONG_CLASSROOM
cleanup: []
idempotency:
  level: data_level
  note: 重复发布同一教室会因 HAS_PUBLISH 失败；发布成功不可重复
params:
  required:
  - name: classroom_name
  - name: name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/publish

> 教学桌面池-发布（将教室发布为实训空间）。流程：先校验教室未发布（findByClassroomId 非空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH）、无运行中的删除状态机（stateMachineFactory.findByResourceId 存在抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_MACHINE）、教室存在（classroomAPI.findByClassroomIdIn 为空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND）；随后 validatePublishSpaceParam 校验名称重复/镜像非空/登录时间/访问时长/镜像归属教室，调 rccSpaceAPI.publishSpace 创建教学桌面池与用户桌面记录，saveAdminGroupPermission 添加 DESKTOP_POOL 数据权限，写成功审计并返回 i18n key；异常写失败审计并返回 fail key。 ｜ @EnableAuthority ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
        A2["POST /rcc/space/image/list"]
    end
    B["POST /rcc/space/publish<br>教学桌面池-发布（将教室发布为实训空间）。流程：先校验教室未发布（findByC<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/builder/sessionCo"]
        C2["Step2: rccSpaceAPI.findByClassroomId(classroomI"]
        C3["Step3: hasExistDeleteClassroomTask(classroomId)"]
        C4["Step4: classroomAPI.findByClassroomIdIn 为空抛 RCD"]
        C5["Step5: rccSpacePoolWebHelper.validatePublishSpa"]
        C6["Step6: BeanUtils.copyProperties → PublishSpaceR"]
        C1 --> C2
        C7["Step7: rccSpaceAPI.getBaseDTOByClassroomId(clas"]
        C8["Step8: auditLogAPI.recordLog(RCDC_RCC_SPACE_CLA"]
        C9["Step9: 返回 success(RCDC_RCC_SPACE_CLASSROOM_POOL"]
        C10["Step10: catch：auditLogAPI.recordLog(PUBLISH_FAIL"]
        C6 --> C7
        C7 --> C8
        C8 --> C9
        C9 --> C10
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/space/detail"]
        D2["POST /rcc/space/edit"]
        D3["POST /rcc/space/delete"]
        D4["POST /rcc/space/forceWakeUp"]
        D5["POST /rcc/space/user/update"]
    end
    B -->|数据| D1
    B -->|数据| D2
    B -->|数据| D3
    B -->|数据| D4
    B -->|数据| D5
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/space/publish |
| Controller | RccSpaceController |
| 方法名 | publish |
| 权限注解 | @EnableAuthority |
| 执行方式 | 同步 |
| 业务含义 | 教学桌面池-发布（将教室发布为实训空间）。流程：先校验教室未发布（findByClassroomId 非空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH）、无运行中的删除状态机（stateMachineFactory.findByResourceId 存在抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_MACHINE）、教室存在（classroomAPI.findByClassroomIdIn 为空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND）；随后 validatePublishSpaceParam 校验名称重复/镜像非空/登录时间/访问时长/镜像归属教室，调 rccSpaceAPI.publishSpace 创建教学桌面池与用户桌面记录，saveAdminGroupPermission 添加 DESKTOP_POOL 数据权限，写成功审计并返回 i18n key；异常写失败审计并返回 fail key。 |

## 入参详情

### RccPublicClassroomSpaceWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| name | String | 是 | @NotBlank @TextShort @TextName | 实训空间名称 |
| classroomId | UUID | 是 | @NotNull | 绑定的教室ID |
| imageTemplateIdArr | UUID[] | 是 | @NotNull（逻辑上不能为空数组） | 绑定的镜像ID数组 |
| idleDesktopRecover | Integer | 否 | @Nullable @Range(0-99999999) | 空闲桌面自动回收时间（分钟） |
| enableAllowMaxUseTime | Boolean | 是 | @NotNull | 是否开启单次允许接入最大时间配置 |
| allowMaxUseTime | Integer | 否 | @Nullable @Range(30-144000) | 单次允许接入最大时间 |
| beforeRecycleNotifyTime | Integer | 否 | @Nullable @Range(1-144000) | 断开连接前提示时间 |
| enableAllowUseTimeInfo | Boolean | 是 | @NotNull | 是否开启云桌面允许登录时间 |
| allowUseTimeInfoArr | RccAllowUseTimeInfoDTO[] | 否 | @Nullable | 云桌面允许登录时间段数组 |
| description | String | 否 | @Nullable @TextMedium | 描述 |
| enableSpecifiedIpRange | Boolean | 否 | @Nullable（默认 false） | 是否开启指定终端IP访问 |

## 出参详情

| 返回类型 | CommonWebResponse<?>（data 为 i18n key 字符串） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| data | String | 纯操作接口：content 为空（成功 RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_SUCCESS / 失败 RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_FAIL） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID，来源为教室创建返回（由 field_map 契约映射）

### 前置2：POST /rcc/space/image/list

绑定镜像ID数组，来源为本地镜像模板列表（已过滤课堂镜像）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/builder/sessionContext)
2. rccSpaceAPI.findByClassroomId(classroomId) 非空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH
3. hasExistDeleteClassroomTask(classroomId)：stateMachineFactory.findByResourceId 存在则抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_MACHINE
4. classroomAPI.findByClassroomIdIn 为空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND
5. rccSpacePoolWebHelper.validatePublishSpaceParam(request)：名称重复抛 RCDC_RCC_SPACE_CLASSROOM_POOL_NAME_HAS_EXIST；镜像数组空抛 RCDC_RCC_SPACE_PUBLISH_FAIL_IMAGETEMPLATE_NOT_ALLOW_NULL；登录时间/访问时长/镜像归属教室校验
6. BeanUtils.copyProperties → PublishSpaceRequest；rccSpaceAPI.publishSpace(publishSpaceRequest)
7. rccSpaceAPI.getBaseDTOByClassroomId(classroomId)；permissionHelper.saveAdminGroupPermission(desktopPoolId, DESKTOP_POOL) 添加数据权限
8. auditLogAPI.recordLog(RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_SUCCESS_LOG)
9. 返回 success(RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_SUCCESS)
10. catch：auditLogAPI.recordLog(PUBLISH_FAIL_LOG)，返回 fail(PUBLISH_OPERATE_FAIL)

## 下游消费方

### 消费1：POST /rcc/space/publish

发布产出教学桌面池空间ID（经 /rcc/space/list 按 classroomId 查询获得），被 detail/edit/delete/forceWakeUp/user/update 消费（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | name | @NotBlank @TextShort @TextName | 名称校验失败 |
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| PARAM | imageTemplateIdArr | @NotNull 且非空数组 | 空数组抛 RCDC_RCC_SPACE_PUBLISH_FAIL_IMAGETEMPLATE_NOT_ALLOW_NULL |
| BUSINESS | classroomId | 教室未发布 | 已发布抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH |
| BUSINESS | classroomId | 无运行中的删除/状态机任务 | 存在抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_MACHINE |
| BUSINESS | classroomId | 教室必须存在 | 抛 RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND |
| BUSINESS | imageTemplateIdArr | 镜像必须归属该教室且已发布 | 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_IMAGE_NOT_BELONG_CLASSROOM |
| BUSINESS | name | 名称不得与已有空间重复 | 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_NAME_HAS_EXIST |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| name | user_input/from_query | 按业务构造 |
| classroomId | user_input/from_query | 按业务构造 |
| imageTemplateIdArr | user_input/from_query | 按业务构造 |
| idleDesktopRecover | user_input/from_query | 按业务构造 |
| enableAllowMaxUseTime | user_input/from_query | 按业务构造 |
| allowMaxUseTime | user_input/from_query | 按业务构造 |
| beforeRecycleNotifyTime | user_input/from_query | 按业务构造 |
| enableAllowUseTimeInfo | user_input/from_query | 按业务构造 |
| allowUseTimeInfoArr | user_input/from_query | 按业务构造 |
| description | user_input/from_query | 按业务构造 |
| enableSpecifiedIpRange | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室未发布且镜像已分配给学生 | $.status==SUCCESS |
| 允许登录时间/最大时长已配置 | $.status==SUCCESS |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室已发布 | findByClassroomId 非空 | $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH |
| 教室不存在 | classroomId 无效 | $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND |
| 镜像不属于该教室 | imageTemplateIdArr 含未分配镜像 | $.status==ERROR 且 $.msgKey==RCDC_RCC_SPACE_CLASSROOM_POOL_IMAGE_NOT_BELONG_CLASSROOM |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复发布同一教室会因 HAS_PUBLISH 失败；发布成功不可重复 |
