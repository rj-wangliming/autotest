---
version: '2.0'
api:
  url: /rcc/classroom/teacher/getInfo
  method: POST
  name: 获取教师机详情信息（教师终端信息、桌面状态、系统配置等）。先校验终端组数据权限，调 classroomAPI.getTeacherDetailInfo(clas
  controller: RccClassroomConfigController
  method_ref: getTeacherDetailInfo
  permission: 无
  exec_mode: 同步
  async: false
  description: 获取教师机详情信息（教师终端信息、桌面状态、系统配置等）。先校验终端组数据权限，调 classroomAPI.getTeacherDetailInfo(classroomId) 返回 ClassroomTeacherDetailDTO。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批处理任务，出参BatchTaskSubmitResult）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/terminal/list
  extract:
    classroomId: $.content.itemArr[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
request:
  dto: ClassroomQueryWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
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
    teacherId:
      type: UUID
      description: 教师ID
    teacherName:
      type: String
      description: 教师名称
    teacherMode:
      type: TerminalTypeEnum
      description: 教师机模式
    teacherIp:
      type: String
      description: 教师机终端IP
    teacherDesktopState:
      type: CbbCloudDeskState
      description: 教师桌面状态
    teacherDesktopId:
      type: UUID
      description: 教师桌面ID
    teacherTerminalId:
      type: String
      description: 教师终端ID
    teacherTerminalState:
      type: CbbTerminalStateEnums
      description: 教师终端状态
    teacherMac/teacherCpuType/teacherMemory/teacherDiskSize/teacherSystemSize/teacherImageNum:
      type: String/Long/Integer
      description: 教师机硬件与镜像信息
    classroomName:
      type: String
      description: 教室名称
    classroomState:
      type: ClassroomLessonStatusEnum
      description: 教室授课状态
    disableNetwork:
      type: Boolean
      description: 是否禁网
    platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:rcc/ClassroomAPI#getTeacherDetailInfo
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
    expect: $.status=="SUCCESS"；$.content.teacherId 非空
  failure:
  - scenario: 教室不存在
    trigger: classroomId 无效
    expect: status==ERROR；msgKey==RCDC_CLASSROOM_NOT_FIND
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
# POST /rcc/classroom/teacher/getInfo

> 获取教师机详情信息（教师终端信息、桌面状态、系统配置等）。先校验终端组数据权限，调 classroomAPI.getTeacherDetailInfo(classroomId) 返回 ClassroomTeacherDetailDTO。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/getInfo<br>获取教师机详情信息（教师终端信息、桌面状态、系统配置等）。先校验终端组数据权限，<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getTeacherDetailInfo(classr"]
        C4["Step4: return success(teacherDetailInfo)"]
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
| URL | /rcc/classroom/teacher/getInfo |
| Controller | RccClassroomConfigController |
| 方法名 | getTeacherDetailInfo |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 获取教师机详情信息（教师终端信息、桌面状态、系统配置等）。先校验终端组数据权限，调 classroomAPI.getTeacherDetailInfo(classroomId) 返回 ClassroomTeacherDetailDTO。 |

## 入参详情

### ClassroomQueryWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ClassroomTeacherDetailDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomName | String | 教室名称 |
| classroomState | ClassroomLessonStatusEnum | 教室授课状态 |
| disableNetwork | Boolean | 是否禁网 |
| platformStatus | CloudPlatformStatus | 云平台状态 |
| classroomId | UUID | 教室ID（继承 ClassroomTeacherBasicDetailDTO） |
| teacherId | UUID | 教师ID |
| teacherName | String | 教师名称 |
| teacherDesktopState | CbbCloudDeskState | 教师桌面状态 |
| teacherDesktopIp | String | 教师桌面IP |
| teacherRainOsVersion | String | 教师终端 RainOS 版本 |
| teacherHardwareVersion | String | 教师终端硬件版本 |
| teacherUpgradeVersion | String | 教师终端升级版本 |
| teacherSerialNumber | String | 教师终端序列号 |
| teacherTerminalModel | String | 教师终端型号 |
| teacherCpuType | String | 教师机CPU型号 |
| teacherMemory | Long | 教师机内存大小 |
| teacherMac | String | 教师机MAC地址 |
| teacherIp | String | 教师机终端IP |
| teacherTerminalId | String | 教师终端ID |
| teacherOsType | String | 教师机操作系统类型 |
| teacherLockStatus | Boolean | 教师终端是否锁定 |
| teacherDesktopId | UUID | 教师桌面ID |
| teacherTerminalName | String | 教师终端名称 |
| teacherMode | TerminalTypeEnum | 教师机模式 |
| teacherTerminalState | CbbTerminalStateEnums | 教师终端状态 |
| teacherDiskSize | Long | 教师机磁盘大小 |
| teacherSystemSize | Long | 教师机系统盘大小 |
| teacherImageNum | Integer | 教师机镜像数量 |
| teacherTerminalDiskSize | Long | 教师终端磁盘大小 |
| teacherState | ClassroomLessonStatusEnum | 教师状态 |
| teacherClassroomStrategyName | String | 教师机教室策略名称 |
| terminalNeedUpgrade | Boolean | 终端是否需要升级 |
| canTerminalInit | Boolean | 是否支持终端初始化 |
| deployMode | String | 部署模式 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.getTeacherDetailInfo(classroomId) 查询
4. return success(teacherDetailInfo)

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
| 传入有效教室ID | $.status=="SUCCESS"；$.content.teacherId 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室不存在 | classroomId 无效 | status==ERROR；msgKey==RCDC_CLASSROOM_NOT_FIND |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
