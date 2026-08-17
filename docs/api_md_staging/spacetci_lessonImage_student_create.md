---
version: '2.0'
api:
  url: /spacetci/lessonImage/student/create
  method: POST
  name: 分配新的学生机课程镜像给教室：落库课程镜像记录，首个镜像时批量创建学生座位云桌面，否则推送镜像列表到座位
  controller: TCILessonImageController
  method_ref: assignStudentImage
  permission: '@EnableAuthority'
  exec_mode: async_batch（条件性：首次镜像且座位非空时异步批量建桌面）
  async: true
  description: 分配新的学生机课程镜像给教室：落库课程镜像记录，首个镜像时批量创建学生座位云桌面，否则推送镜像列表到座位
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
- name: create_tci_strategy
  api: POST /space/strategy/tci/create
  extract:
    lessonStrategyId: $.content.id
  purpose: 创建TCI策略（已有同名策略则直接复用，不重新创建）
  request:
    body:
      name: ${param.strategy_name}
  idempotent: reuse
  reuse_query:
    api: POST /space/strategy/tci/list
    body:
      page: 0
      limit: 20
      matchArr:
      - type: EXACT
        fieldName: strategyName
        valueArr:
        - ${param.strategy_name}
        matchRule: EQ
    extract:
      lessonStrategyId: $.content.itemArr[0].id
- name: list_lesson_image
  api: POST /spacetci/lessonImage/getLessonImageList
  extract:
    imageId: $.content.itemArr[0].imageId
  purpose: 按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）
  request:
    body:
      searchKeyword: ${param.student_image_name}
      matchArr:
      - type: EXACT
        fieldName: imageName
        valueArr:
        - ${param.image_name}
        matchRule: EQ
- name: get_cluster
  api: POST /space/cluster/obtainComputeClusterList
  extract:
    clusterId: $.content.itemArr[0].computerClusterId
    platformId: $.content.itemArr[0].platformId
  purpose: 获取计算集群ID与云平台ID（取第一条，无名称过滤）
- name: get_storage_pool
  api: POST /space/storagePool/list
  extract:
    storagePoolId: $.content.itemArr[0].storagePoolId
  purpose: 获取存储池ID（镜像分配用）（取第一条，无名称过滤）
- name: get_network
  api: POST /space/clouddesktop/deskNetwork/list
  extract:
    networkId: $.content.itemArr[0].id
  purpose: 获取网络ID（镜像分配用）（取第一条，无名称过滤）
request:
  dto: TCIAssignImageWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull，教室ID'
      description: 目标教室；ID 来自前置步骤 setup 产出（${prev.*}）
      value: ${prev.select_classroom_id.output.classroomId}
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull，镜像模板ID，需已发布且为TCI类型'
      description: 分配的镜像模板；ID 来自前置步骤 setup 产出（${prev.*}）
      value: ${prev.list_lesson_image.output.imageId}
    hide:
      type: Boolean
      required: true
      constraint: '@NotNull，是否隐藏'
      description: 初始隐藏状态（默认 false 不隐藏）
      value: false
    lessonStrategyId:
      type: UUID
      required: true
      constraint: '@NotNull，课程策略ID'
      description: 关联的课程策略；ID 来自前置步骤 setup 产出（${prev.*}）
      value: ${prev.create_tci_strategy.output.lessonStrategyId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    msgKey:
      type: String
      description: spacetci_lessonimage_assign_student_image_success_log（座位为空/非
    taskId:
      type: UUID
      description: 首镜像时返回创建云桌面批处理任务ID（BatchTaskSubmitResult）
upstream:
- api: POST /rcc/classroom/create
  purpose: 教室ID，来源为教室创建返回
- api: POST /spacetci/lessonImage/getLessonImageList
  purpose: TCI课程镜像模板ID，来源为课程镜像列表（或 /rcc/deskStrategy/getClassroomImageList）
- api: POST /space/strategy/tci/list
  purpose: TCI课程策略ID，来源为策略列表
downstream:
- api: 内部调用:seatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: data
  field: admin
  rule: 需拥有教室/镜像/桌面策略数据权限
  failure: spacetci_lessonimage_permission_denied
- level: concurrency
  field: classroomId
  rule: 同一教室操作互斥
  failure: spacetci_lessonimage_operate_running
- level: business
  field: imageId
  rule: 镜像必须存在且为TCI类型
  failure: 62110021/62110022
- level: business
  field: imageId
  rule: 仅允许已发布镜像
  failure: 62110023 SPACETCI_LESSONIMAGE_IMAGE_STATE_NOT_AVAILABLE
- level: business
  field: lessonStrategyId
  rule: 镜像系统盘不得大于策略配置
  failure: 62110024 SPACETCI_LESSONIMAGE_SYSTEM_DISK_BIG_LESSONSTRTEGY
- level: business
  field: lessonStrategyId
  rule: 数据盘配置需一致
  failure: 62110025 SPACETCI_LESSONIMAGE_DATA_DISK_STATE_NOT_SAME
- level: business
  field: lessonStrategyId
  rule: 数据盘不得大于策略配置
  failure: 62110026 SPACETCI_LESSONIMAGE_DATA_DISK_BIG_LESSONSTRTEGY
- level: business
  field: imageId
  rule: 同一教室镜像不可重复添加
  failure: 62110027 SPACETCI_LESSONIMAGE_ADD_REPEAT / 62110028 SPACETCI
assertions:
  success:
  - scenario: 教室无座位
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_assign_student_image_success_log）
  - scenario: 首个镜像且有座位
    expect: $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 非首镜像
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_assign_student_image_success_log）
  failure:
  - scenario: 数据权限不足
    trigger: checkLessonImageDataPermission抛异常
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_permission_denied
  - scenario: 教室操作进行中
    trigger: tryLock失败
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_operate_running
  - scenario: 重复分配同一镜像
    trigger: createLessonImage抛62110027
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_assign_student_image_fail_log
cleanup:
- api: POST /spacetci/lessonImage/student/delete
  note: 清理本接口分配的课程镜像（学生课程镜像删除接口）
idempotency:
  level: data_level
  note: 重复分配同一镜像被62110027拦截；不同镜像重复调用会新增记录，非幂等
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
  condition: 仅首次镜像（isFirstImage=true）且座位非空时返回 BatchTaskSubmitResult 需轮询；其余同步成功（content 空）
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: image_name
    desc: ''
    used_by: setup/request
---
# POST /spacetci/lessonImage/student/create

> 分配新的学生机课程镜像给教室：落库课程镜像记录，首个镜像时批量创建学生座位云桌面，否则推送镜像列表到座位 ｜ @EnableAuthority ｜ async

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
        A2["POST /spacetci/lessonImage/getLessonImageList"]
        A3["POST /space/strategy/tci/list"]
    end
    B["POST /spacetci/lessonImage/student/create<br>分配新的学生机课程镜像给教室：落库课程镜像记录，首个镜像时批量创建学生座位云桌面<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest/builder/sessio"]
        C2["Step2: BeanUtils.copyProperties转TCILessonImageD"]
        C3["Step3: checkLessonImageDataPermission校验教室/镜像/桌面"]
        C4["Step4: getLock(classroomId).tryLock() 加教室级互斥锁，失"]
        C5["Step5: classroomAPI.createLessonImage 落库课程镜像记录（"]
        C6["Step6: 获取座位列表；座位为空直接返回成功"]
        C1 --> C2
        C7["Step7: isFirstImage为true→TCICreateSeatDesktopBa"]
        C8["Step8: 记录审计日志并返回"]
        C6 --> C7
        C7 --> C8
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["delete/hide/show/update/strategy/edit"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /spacetci/lessonImage/student/create |
| Controller | TCILessonImageController |
| 方法名 | assignStudentImage |
| 权限注解 | @EnableAuthority |
| 执行方式 | async |
| 业务含义 | 分配新的学生机课程镜像给教室：落库课程镜像记录，首个镜像时批量创建学生座位云桌面，否则推送镜像列表到座位 |

## 入参详情

### TCIAssignImageWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull，教室ID | 目标教室 |
| imageId | UUID | 是 | @NotNull，镜像模板ID，需已发布且为TCI类型 | 分配的镜像模板 |
| hide | Boolean | 是 | @NotNull，是否隐藏 | 初始隐藏状态 |
| lessonStrategyId | UUID | 是 | @NotNull，课程策略ID | 关联的课程策略 |

## 出参详情

| 返回类型 | DefaultWebResponse（成功消息key或BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| msgKey | String | spacetci_lessonimage_assign_student_image_success_log（座位为空/非首镜像时） |
| taskId | UUID | 首镜像时返回创建云桌面批处理任务ID（BatchTaskSubmitResult） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID，来源为教室创建返回（由 field_map 契约映射）

### 前置2：POST /spacetci/lessonImage/getLessonImageList

TCI课程镜像模板ID，来源为课程镜像列表（或 /rcc/deskStrategy/getClassroomImageList）（由 field_map 契约映射）

### 前置3：POST /space/strategy/tci/list

TCI课程策略ID，来源为策略列表（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：TCICreateSeatDesktopBatchTaskHandler(AbstractBatchTaskHandler) 或 PushImageListBatchTaskHandler(AbstractBatchTaskHandler)

| 步骤 | 说明 |
|---|---|
| 1 | TCICreateSeatDesktopBatchTaskHandler.processItem：seatAPI.createTCIDesktop(dto,seatId)逐座位创建云桌面，失败记录审计日志返回FAILURE |
| 2 | PushImageListBatchTaskHandler.processItem：seatAPI.pushClassroomImageList2Seat(seatId)逐座位推送镜像列表 |
| 3 | onFinish：seatAPI.refreshDeskInfo(classroomId)刷新桌面信息，按成功/失败数量返回SUCCESS/FAILURE/PARTIAL_SUCCESS |

### 处理流程

1. Assert.notNull(webRequest/builder/sessionContext) 校验入参
2. BeanUtils.copyProperties转TCILessonImageDTO并setTeacherImage=false
3. checkLessonImageDataPermission校验教室/镜像/桌面策略数据权限，失败返回spacetci_lessonimage_permission_denied
4. getLock(classroomId).tryLock() 加教室级互斥锁，失败返回spacetci_lessonimage_operate_running
5. classroomAPI.createLessonImage 落库课程镜像记录（重复/磁盘超限等校验62110021-62110028）
6. 获取座位列表；座位为空直接返回成功
7. isFirstImage为true→TCICreateSeatDesktopBatchTaskHandler批量创建座位云桌面（异步）；否则dealBatchPushImageList推送镜像列表（异步）
8. 记录审计日志并返回

## 下游消费方

### 消费1：POST /spacetci/lessonImage/student/create

分配产出学生课程镜像ID（经 getLessonImageList 查询），被 delete/hide/show/update/strategy/edit 消费（由 field_map 契约映射）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| data | admin | 需拥有教室/镜像/桌面策略数据权限 | spacetci_lessonimage_permission_denied |
| concurrency | classroomId | 同一教室操作互斥 | spacetci_lessonimage_operate_running |
| business | imageId | 镜像必须存在且为TCI类型 | 62110021/62110022 |
| business | imageId | 仅允许已发布镜像 | 62110023 SPACETCI_LESSONIMAGE_IMAGE_STATE_NOT_AVAILABLE |
| business | lessonStrategyId | 镜像系统盘不得大于策略配置 | 62110024 SPACETCI_LESSONIMAGE_SYSTEM_DISK_BIG_LESSONSTRTEGY |
| business | lessonStrategyId | 数据盘配置需一致 | 62110025 SPACETCI_LESSONIMAGE_DATA_DISK_STATE_NOT_SAME |
| business | lessonStrategyId | 数据盘不得大于策略配置 | 62110026 SPACETCI_LESSONIMAGE_DATA_DISK_BIG_LESSONSTRTEGY |
| business | imageId | 同一教室镜像不可重复添加 | 62110027 SPACETCI_LESSONIMAGE_ADD_REPEAT / 62110028 SPACETCI_LESSONIMAGE_ALREADY_EXIST_LESSON_IMAGE |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |
| hide | user_input/from_query | 按业务构造 |
| lessonStrategyId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室无座位 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_assign_student_image_success_log） |
| 首个镜像且有座位 | $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |
| 非首镜像 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_assign_student_image_success_log） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 数据权限不足 | checkLessonImageDataPermission抛异常 | $.status==ERROR && $.msgKey==spacetci_lessonimage_permission_denied |
| 教室操作进行中 | tryLock失败 | $.status==ERROR && $.msgKey==spacetci_lessonimage_operate_running |
| 重复分配同一镜像 | createLessonImage抛62110027 | $.status==ERROR && $.msgKey==spacetci_lessonimage_assign_student_image_fail_log |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| POST /spacetci/lessonImage/student/delete | 清理本接口分配的课程镜像（学生课程镜像删除接口） |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 重复分配同一镜像被62110027拦截；不同镜像重复调用会新增记录，非幂等 |
