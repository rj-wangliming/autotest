---
version: '2.0'
api:
  url: /rcc/classroom/image/student/strategy/edit
  method: POST
  name: 学生机课程镜像编辑课程云桌面策略；可选同步变更镜像版本（提交镜像版本变更批任务）
  controller: RccClassroomImageController
  method_ref: editStudentStrategy
  permission: '@EnableAuthority'
  exec_mode: sync（指定 targetImageId 变更镜像版本时提交 ChangeImageVersionBatchTaskHandler 批任务）
  async: true
  description: 学生机课程镜像编辑课程云桌面策略；可选同步变更镜像版本（提交镜像版本变更批任务）
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批任务，需轮询批任务完成后再查询教室）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  request:
    body:
      searchKeyword: ${param.classroom_name}
- name: get_image
  api: POST /rcc/classroom/image/list
  extract:
    imageId: $.content.itemArr[0].id
  purpose: 按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）
  request:
    body:
      searchKeyword: ${param.student_image_name}
      matchArr:
      - fieldName: imageName
        matchType: EQUAL
        value: ${param.student_image_name}
- name: get_strategy
  api: POST /rcc/classroom/strategy/list
  extract:
    deskStrategyId: $.content.itemArr[0].classroomStrategyId
  purpose: 按策略名精确过滤（matchArr.fieldName=classroomStrategyName）
  request:
    body:
      matchArr:
      - fieldName: classroomStrategyName
        matchType: EQUAL
        value: ${param.strategy_name}
request:
  dto: UpdateImageStrategyWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 课程镜像ID
    oldImageId:
      type: UUID
      required: false
      constraint: 可空（变更版本时必填）
      description: 变更前的镜像版本id
    targetImageId:
      type: UUID
      required: false
      constraint: 可空（有值则触发版本变更批任务）
      description: 变更后的镜像版本id
    deskStrategyId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 课程云桌面策略Id
    clusterId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 计算节点ID
    platformId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 云平台ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: BatchTaskSubmitResult|空
      description: 版本变更批任务提交结果或 CLASSROOM_OPERATE_TIP_SUCCESS
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
    failure:
    - FAILURE
    - PARTIAL_SUCCESS
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
- api: POST /rcc/classroom/image/list
  produces: $.content.itemArr[0].id
  purpose: 课程镜像ID
- api: POST /rcc/classroom/strategy/list
  produces: $.content.itemArr[0].classroomStrategyId
  purpose: 策略ID；controller 经 rccDeskStrategyAPI.findById 读取（推断为 VDI 策略组 space/strategygroup/vdi/create 产物）
downstream:
- api: 内部调用:rcc/ClassroomImageAPI#updateStudentImageStrategy
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:rcc/ClassroomImageAPI#changeImageVersion
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId/imageId/deskStrategyId/clust
  rule: '@NotNull'
  failure: 参数缺失校验失败
- level: BIZ
  field: deskStrategyId
  rule: 策略需为课程策略且与镜像匹配
  failure: 抛 RCDC_RCC_IMAGE_DESK_STRATEGY_NOT_RCC / RCDC_RCC_IMAGE_STRA
- level: BIZ
  field: targetImageId
  rule: 变更镜像版本时 oldImageId 必填、镜像需支持版本变更
  failure: 抛 RCDC_RCC_IMAGE_VERSION_ID_IS_NOT_NULL(62100226) / RCDC_RCC
- level: CONCURRENCY
  field: 版本变更任务
  rule: crossStorageImageTaskLockKeyUtil.buildBatchTaskLockKey 唯一锁防并
  failure: 同教室同镜像并发版本变更被唯一锁拦截
assertions:
  success:
  - scenario: 仅修改策略
    expect: $.status==SUCCESS（content 为空，msgKey==rcdc_classroom_operate_tip_success）
  - scenario: 修改策略并变更版本
    expect: $.status==SUCCESS && $.content.taskId 非空（ChangeImageVersionBatchTaskHandler 批任务）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 非课程策略
    trigger: deskStrategyId 为个人桌面策略
    expect: $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 rcdc_rcc_image_bind_classroom_personal_desk_strategy）
  - scenario: 镜像不支持版本变更
    trigger: targetImageId 传入但镜像为单镜像
    expect: $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 62100224/62100225）
  - scenario: 策略与镜像类型不一致
    trigger: VDI镜像配TCI策略
    expect: $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 rcdc_rcc_image_strategy_not_same_type）
cleanup: []
idempotency:
  level: data_level
  note: '@OneTimeTokenRequired 一次性Token防重复提交；版本变更批任务带唯一锁；策略更新本身可重放'
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/image/student/strategy/edit

> 学生机课程镜像编辑课程云桌面策略；可选同步变更镜像版本（提交镜像版本变更批任务） ｜ @EnableAuthority ｜ sync（指定 targetImageId 变更镜像版本时提交 ChangeImageVersionBatchTaskHandler 批任务）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
        A2["POST /rcc/classroom/image/list"]
        A3["POST /rcc/classroom/strategy/list"]
    end
    B["POST /rcc/classroom/image/student/strategy/edit<br>学生机课程镜像编辑课程云桌面策略；可选同步变更镜像版本（提交镜像版本变更批任务）<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 webRequest/builder"]
        C2["Step2: request = webRequest.buildStuRequest()（e"]
        C3["Step3: 获取教室名/镜像名/策略名（classroomAPI.getClassroomN"]
        C4["Step4: classroomImageAPI.updateStudentImageStra"]
        C5["Step5: 记录 RCDC_RCC_CLASSROOM_STU_IMAGE_STRATEGY"]
        C6["Step6: handleImageVersionChange(webRequest, fal"]
        C1 --> C2
        C7["Step7: 若 targetImageId 为 null 直接返回 null（无批任务）"]
        C8["Step8: 构建 ClassroomImageDetailRequest（oldImageI"]
        C9["Step9: buildChangeVersionRequest 构造 ChangeImage"]
        C10["Step10: classroomImageAPI.validCanChangeClassroo"]
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
        D1["（无 HTTP 下游）"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/image/student/strategy/edit |
| Controller | RccClassroomImageController |
| 方法名 | editStudentStrategy |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync（指定 targetImageId 变更镜像版本时提交 ChangeImageVersionBatchTaskHandler 批任务） |
| 业务含义 | 学生机课程镜像编辑课程云桌面策略；可选同步变更镜像版本（提交镜像版本变更批任务） |

## 入参详情

### UpdateImageStrategyWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| imageId | UUID | 是 | @NotNull | 课程镜像ID |
| oldImageId | UUID | 否 | 可空（变更版本时必填） | 变更前的镜像版本id |
| targetImageId | UUID | 否 | 可空（有值则触发版本变更批任务） | 变更后的镜像版本id |
| deskStrategyId | UUID | 是 | @NotNull | 课程云桌面策略Id |
| clusterId | UUID | 是 | @NotNull | 计算节点ID |
| platformId | UUID | 是 | @NotNull | 云平台ID |

## 出参详情

| 返回类型 | DefaultWebResponse（成功或 BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult|空 | 版本变更批任务提交结果或 CLASSROOM_OPERATE_TIP_SUCCESS |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/image/list

课程镜像ID（由 field_map 契约映射）

### 前置3：POST /rcc/classroom/strategy/list

策略ID；controller 经 rccDeskStrategyAPI.findById 读取（推断为 VDI 策略组 space/strategygroup/vdi/create 产物）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：ChangeImageVersionBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem：classroomImageAPI.changeImageVersion(request) 执行版本变更 |
| 2 | 成功：记录 RCDC_CHANGE_CLASSROOM_STUDENT_IMAGE_VERSION_LOG 审计，返回 SUCCESS（RCDC_RCC_CLASSROOM_CHANGE_STUDENT_IMAGE_VERSION_SUCCESS_LOG） |
| 3 | 失败：记录 RCDC_RCC_CHANGE_CLASSROOM_STUDENT_IMAGE_VERSION_FAIL_LOG 审计，返回 FAILURE |
| 4 | onFinish：failCount==0 返回 SUCCESS 否则 FAILURE |

### 处理流程

1. Assert.notNull 校验 webRequest/builder
2. request = webRequest.buildStuRequest()（enableTeacher=false）
3. 获取教室名/镜像名/策略名（classroomAPI.getClassroomName、classroomImageAPI.getImageName、rccDeskStrategyAPI.findById）
4. classroomImageAPI.updateStudentImageStrategy(request) 更新策略
5. 记录 RCDC_RCC_CLASSROOM_STU_IMAGE_STRATEGY_EDIT_SUCCESS_LOG 审计
6. handleImageVersionChange(webRequest, false, builder)：
7.   若 targetImageId 为 null 直接返回 null（无批任务）
8.   构建 ClassroomImageDetailRequest（oldImageId）→ getClassroomImageDetail 获取旧镜像详情
9.   buildChangeVersionRequest 构造 ChangeImageVersionRequest（含 crId/plusImageId/enableHide/clusterId/platformId/strategyId/networkId/rootImageId/oldImageId/storagePoolIdList/changeImageVersion=true/副本存储池，VDI数据盘开启时设置 vdiDiskStorageId）
10.   classroomImageAPI.validCanChangeClassroomImageVersion 校验
11.   startImageVersionChangeBatchTask 提交 ChangeImageVersionBatchTaskHandler 批任务（带唯一锁 uniqueId）
12.   失败：记录 RCDC_RCC_CHANGE_CLASSROOM_STUDENT_IMAGE_VERSION_FAIL_LOG 审计并重抛
13. BusinessException：记录 RCDC_RCC_CLASSROOM_STU_IMAGE_STRATEGY_EDIT_FAIL_LOG 审计并返回 fail

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId/imageId/deskStrategyId/clusterId/platformId | @NotNull | 参数缺失校验失败 |
| BIZ | deskStrategyId | 策略需为课程策略且与镜像匹配 | 抛 RCDC_RCC_IMAGE_DESK_STRATEGY_NOT_RCC / RCDC_RCC_IMAGE_STRATEGY_NOT_SAME_TYPE / RCDC_RCC_IMAGE_BIND_CLASSROOM_PERSONAL_DESK_STRATEGY |
| BIZ | targetImageId | 变更镜像版本时 oldImageId 必填、镜像需支持版本变更 | 抛 RCDC_RCC_IMAGE_VERSION_ID_IS_NOT_NULL(62100226) / RCDC_RCC_IMAGE_VERSION_ONLY_CHANGED_BY_RECOVERABLE(62100225) / RCDC_RCC_IMAGE_SINGLE_IMAGE_CAN_NOT_SELECT_TO_OTHER_PLATFORM(62100223) / RCDC_RCC_IMAGE_SINGLE_IMAGE_NOT_SUPPORT(62100224) / RCDC_RCC_TCI_IMAGE_NO_SUPPORT_ARM(62100231) / RCDC_RCC_CLASSROOM_IMAGE_IN_EXTERNAL_STORAGE(62100238) / RCC_IMAGE_VERSION_REPLICATION_NOT_FIND_ERROR_CODE(62100239) |
| CONCURRENCY | 版本变更任务 | crossStorageImageTaskLockKeyUtil.buildBatchTaskLockKey 唯一锁防并发变更 | 同教室同镜像并发版本变更被唯一锁拦截 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |
| oldImageId | user_input/from_query | 按业务构造 |
| targetImageId | user_input/from_query | 按业务构造 |
| deskStrategyId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 仅修改策略 | $.status==SUCCESS（content 为空，msgKey==rcdc_classroom_operate_tip_success） |
| 修改策略并变更版本 | $.status==SUCCESS && $.content.taskId 非空（ChangeImageVersionBatchTaskHandler 批任务）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 非课程策略 | deskStrategyId 为个人桌面策略 | $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 rcdc_rcc_image_bind_classroom_personal_desk_strategy） |
| 镜像不支持版本变更 | targetImageId 传入但镜像为单镜像 | $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 62100224/62100225） |
| 策略与镜像类型不一致 | VDI镜像配TCI策略 | $.status==ERROR && $.msgKey==rcdc_classroom_operate_tip_failed（底层抛 rcdc_rcc_image_strategy_not_same_type） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | @OneTimeTokenRequired 一次性Token防重复提交；版本变更批任务带唯一锁；策略更新本身可重放 |
