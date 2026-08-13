---
version: '2.0'
api:
  url: /rcc/classroom/getClassroomVdiDiskStorage
  method: POST
  name: 查询教室VDI数据盘存储池信息（用于教师机/学生机配置弹窗展示）。先校验终端组数据权限，调 classroomAPI.getClassroomVdiDiskSt
  controller: RccClassroomConfigController
  method_ref: getClassroomTeacherVdiDiskStorage
  permission: 无
  exec_mode: 同步
  async: false
  description: 查询教室VDI数据盘存储池信息（用于教师机/学生机配置弹窗展示）。先校验终端组数据权限，调 classroomAPI.getClassroomVdiDiskStorage(classroomId, clusterId, enableTeacher, platformId) 返回教室VDI磁盘存储池及其集群/平台信息。
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
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}），获取 classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
- name: get_cluster_network
  api: POST /rcc/classroom/image/getAssignedClusterAndNetwork
  extract:
    clusterId: $.content.itemArr[0].clusterId
  purpose: 获取计算集群ID（推断）；取第一条（无名称过滤）
request:
  dto: GetClassroomVdiDiskStorageRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
    clusterId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 集群ID（用于确认存储池与集群绑定关系）
    platformId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 云平台ID
    enableTeacher:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 是否查询教师机VDI磁盘配置（true=教师机，false=学生机）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    hasOpenVdiDisk:
      type: Boolean
      description: 是否已开启VDI数据盘
    vdiDiskStorageId:
      type: UUID
      description: VDI磁盘存储池ID
    vdiDiskStorageName:
      type: String
      description: VDI磁盘存储池名称
    hasVdiDiskStorageBindCluster:
      type: Boolean
      description: 存储池是否绑定集群
    clusterId:
      type: UUID
      description: 集群ID
    platformId:
      type: UUID
      description: 云平台ID
    clusterName:
      type: String
      description: 集群名称
    platformName:
      type: String
      description: 云平台名称
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
- api: POST /rcc/classroom/image/getAssignedClusterAndNetwork
  produces: $.content.itemArr[0].clusterId
  purpose: 计算集群ID（推断）
downstream:
- api: POST /rcc/classroom/image/{student,teacher}/create
  purpose: 出参 ClassroomVdiDiskStorageDTO.vdiDiskStorageId，分配镜像时作为 VDI 数据盘存储池
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: enableTeacher
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: classroomId
  rule: 教室存在且有数据权限
  failure: 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常
assertions:
  success:
  - scenario: 传入有效教室ID
    expect: 返回 HTTP 200，$.status==SUCCESS；$.content.hasOpenVdiDisk/vdiDiskStorageId 等存储池信息非空/vdiDiskStorageId 等存储池信息
  failure:
  - scenario: 教室不存在
    trigger: classroomId 无效
    expect: 抛 RCDC_CLASSROOM_NOT_FIND
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/getClassroomVdiDiskStorage

> 查询教室VDI数据盘存储池信息（用于教师机/学生机配置弹窗展示）。先校验终端组数据权限，调 classroomAPI.getClassroomVdiDiskStorage(classroomId, clusterId, enableTeacher, platformId) 返回教室VDI磁盘存储池及其集群/平台信息。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
        A2["POST /rcc/classroom/image/getAssignedClusterAndNetwork"]
    end
    B["POST /rcc/classroom/getClassroomVdiDiskStorage<br>查询教室VDI数据盘存储池信息（用于教师机/学生机配置弹窗展示）。先校验终端组数<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getClassroomVdiDiskStorage("]
        C4["Step4: return success(classroomVdiDiskStorageDT"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/image/{student,teacher}/create"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/getClassroomVdiDiskStorage |
| Controller | RccClassroomConfigController |
| 方法名 | getClassroomTeacherVdiDiskStorage |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 查询教室VDI数据盘存储池信息（用于教师机/学生机配置弹窗展示）。先校验终端组数据权限，调 classroomAPI.getClassroomVdiDiskStorage(classroomId, clusterId, enableTeacher, platformId) 返回教室VDI磁盘存储池及其集群/平台信息。 |

## 入参详情

### GetClassroomVdiDiskStorageRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| clusterId | UUID | 否 | @Nullable | 集群ID（用于确认存储池与集群绑定关系） |
| platformId | UUID | 否 | @Nullable | 云平台ID |
| enableTeacher | Boolean | 是 | @NotNull | 是否查询教师机VDI磁盘配置（true=教师机，false=学生机） |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ClassroomVdiDiskStorageDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasOpenVdiDisk | Boolean | 是否已开启VDI数据盘 |
| vdiDiskStorageId | UUID | VDI磁盘存储池ID |
| vdiDiskStorageName | String | VDI磁盘存储池名称 |
| hasVdiDiskStorageBindCluster | Boolean | 存储池是否绑定集群 |
| clusterId | UUID | 集群ID |
| platformId | UUID | 云平台ID |
| clusterName | String | 集群名称 |
| platformName | String | 云平台名称 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/image/getAssignedClusterAndNetwork

计算集群ID（推断）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.getClassroomVdiDiskStorage(classroomId, clusterId, enableTeacher, platformId) 查询
4. return success(classroomVdiDiskStorageDTO)

## 下游消费方

### 消费1：POST /rcc/classroom/image/{student,teacher}/create

出参 ClassroomVdiDiskStorageDTO.vdiDiskStorageId，分配镜像时作为 VDI 数据盘存储池（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| PARAM | enableTeacher | @NotNull | 缺失校验失败 |
| BUSINESS | classroomId | 教室存在且有数据权限 | 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |
| enableTeacher | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效教室ID | 返回 HTTP 200，data 含 hasOpenVdiDisk/vdiDiskStorageId 等存储池信息 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室不存在 | classroomId 无效 | 抛 RCDC_CLASSROOM_NOT_FIND |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
