---
version: '2.0'
api:
  url: /rcc/classroom/getTeacherConfig
  method: POST
  name: '获取教室教师机配置信息（模式、IP、主机名前缀、VLAN、本地磁盘、策略等）。先校验终端组数据权限，调 classroomAPI.getTeacherInfo '
  controller: RccClassroomConfigController
  method_ref: getTeacherConfig
  permission: 无
  exec_mode: 同步
  async: false
  description: 获取教室教师机配置信息（模式、IP、主机名前缀、VLAN、本地磁盘、策略等）。先校验终端组数据权限，调 classroomAPI.getTeacherInfo 返回 ClassroomTeacherConfigDTO。
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
request:
  dto: ClassroomQueryWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    classroomId:
      type: UUID
      description: 教室ID
    teacherMode:
      type: TerminalTypeEnum
      description: 教师机模式
    studentModeArr:
      type: TerminalTypeEnum[]
      description: 学生机模式数组（父类字段）
    classroomName:
      type: String
      description: 教室名称
    teacherIp:
      type: String
      description: 教师机终端IP
    teacherPreName:
      type: String
      description: 教师机主机名前缀
    teacherType:
      type: String
      description: 教师机类型
    teacherVlanId:
      type: Integer
      description: 教师机VLAN ID
    teacherTerminalId:
      type: String
      description: 教师机终端ID
    teacherVdiLocalDiskConfig:
      type: VdiLocalDiskConfig
      description: 教师VDI本地磁盘配置
    teacherTciLocalDiskConfig:
      type: TciLocalDiskConfig
      description: 教师TCI本地磁盘配置
    teacherClassroomStrategy:
      type: ClassroomStrategyDTO
      description: 教师机教室策略
    taskIdList:
      type: List<UUID>
      description: 关联任务ID列表
    vdiLocalDiskStoragePoolList:
      type: List<VdiLocalDiskStorageDTO>
      description: VDI本地磁盘存储池列表
    cmrId:
      type: UUID
      description: CMR关联ID
    shouldOnlyDeleteDataFromDb:
      type: Boolean
      description: 是否仅从数据库删除数据
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: 内部调用:rcc/ClassroomAPI#getTeacherInfo
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: classroomId
  rule: 教室存在且有数据权限
  failure: 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常
assertions:
  success:
  - scenario: 传入有效教室ID
    expect: 返回 HTTP 200，$.status==SUCCESS；$.content 含 teacherMode/teacherIp/teacherVdiLocalDiskConfig 等字段
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
# POST /rcc/classroom/getTeacherConfig

> 获取教室教师机配置信息（模式、IP、主机名前缀、VLAN、本地磁盘、策略等）。先校验终端组数据权限，调 classroomAPI.getTeacherInfo 返回 ClassroomTeacherConfigDTO。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/getTeacherConfig<br>获取教室教师机配置信息（模式、IP、主机名前缀、VLAN、本地磁盘、策略等）。先<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getTeacherInfo(request) 查询"]
        C4["Step4: return success(configDTO)"]
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
| URL | /rcc/classroom/getTeacherConfig |
| Controller | RccClassroomConfigController |
| 方法名 | getTeacherConfig |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 获取教室教师机配置信息（模式、IP、主机名前缀、VLAN、本地磁盘、策略等）。先校验终端组数据权限，调 classroomAPI.getTeacherInfo 返回 ClassroomTeacherConfigDTO。 |

## 入参详情

### ClassroomQueryWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ClassroomTeacherConfigDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomId | UUID | 教室ID |
| teacherMode | TerminalTypeEnum | 教师机模式 |
| studentModeArr | TerminalTypeEnum[] | 学生机模式数组（父类字段） |
| classroomName | String | 教室名称 |
| teacherIp | String | 教师机终端IP |
| teacherPreName | String | 教师机主机名前缀 |
| teacherType | String | 教师机类型 |
| teacherVlanId | Integer | 教师机VLAN ID |
| teacherTerminalId | String | 教师机终端ID |
| teacherVdiLocalDiskConfig | VdiLocalDiskConfig | 教师VDI本地磁盘配置 |
| teacherTciLocalDiskConfig | TciLocalDiskConfig | 教师TCI本地磁盘配置 |
| teacherClassroomStrategy | ClassroomStrategyDTO | 教师机教室策略 |
| taskIdList | List<UUID> | 关联任务ID列表 |
| vdiLocalDiskStoragePoolList | List<VdiLocalDiskStorageDTO> | VDI本地磁盘存储池列表 |
| cmrId | UUID | CMR关联ID |
| shouldOnlyDeleteDataFromDb | Boolean | 是否仅从数据库删除数据 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.getTeacherInfo(request) 查询
4. return success(configDTO)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| BUSINESS | classroomId | 教室存在且有数据权限 | 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效教室ID | 返回 HTTP 200，data 含教师机配置全部字段 |

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
