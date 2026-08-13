---
version: '2.0'
api:
  url: /rcc/classroom/desktop/tci/list
  method: POST
  name: 查询课堂TCI云桌面列表：以教室ID精确匹配过滤，权限校验后分页返回TCI桌面视图。
  controller: RccClassroomTCIDesktopController
  method_ref: list
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 查询课堂TCI云桌面列表：以教室ID精确匹配过滤，权限校验后分页返回TCI桌面视图。
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
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
  request:
    body:
      matchArr:
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
request:
  dto: PageQueryRequest
  body:
    page:
      type: Integer
      required: false
      description: 页码与每页条数（page）
    limit:
      type: Integer
      required: false
      description: 页码与每页条数（limit）
    matchArr[0]:
      type: DefaultExactMatch
      required: true
      constraint: 首个match必须是classroomId的精确匹配
      description: 包含 classroomId 精确匹配条件
    sortArr:
      type: Sort[]
      required: false
      constraint: 可选
      description: 排序条件
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ViewTCIDesktopResultDTO[]
      description: TCI桌面列表项（元素字段见下）
    total:
      type: long
      description: 总记录数
    desktopId:
      type: UUID
      description: 云桌面ID
    computerName:
      type: String
      description: 云桌面主机名
    desktopPreName:
      type: String
      description: 主机名前缀（教师机名前缀或座位名）
    desktopState:
      type: CbbCloudDeskState
      description: 云桌面状态
    disableNetwork:
      type: Boolean
      description: 是否禁网
    desktopType:
      type: CbbCloudDeskType
      description: 云桌面类型（IDV/VDI）
    desktopRole:
      type: String
      description: 云桌面角色（学生机/教师机）
    desktopMac:
      type: String
      description: 云桌面MAC
    desktopIp:
      type: String
      description: 云桌面IP
    desktopImageName:
      type: String
      description: 镜像名称
    desktopRootImageName:
      type: String
      description: 根镜像名称
    imageType:
      type: CbbImageType
      description: 镜像类型
    osType:
      type: CbbOsType
      description: 操作系统类型
    osVersion:
      type: String
      description: 系统版本
    systemDisk:
      type: Integer
      description: 系统分区大小
    diskSize:
      type: Integer
      description: 数据盘大小
    desktopCategory:
      type: String
      description: 云桌面容量类型（PERSON/RESTORE）
    terminalIp:
      type: String
      description: 终端IP
    classroomId:
      type: UUID
      description: 教室ID
    seatNum:
      type: Integer
      description: 座位号
    hostName:
      type: String
      description: 主机名
    terminalState:
      type: CbbTerminalStateEnums
      description: 终端状态
    targetComputerName:
      type: String
      description: 目标计算机名称（计算机名不存在时的提示）
    registerState:
      type: CbbDeskRegisterState
      description: 云桌面注册状态
    desktopIpv6:
      type: String
      description: 云桌面IPv6地址
    guestToolVersion:
      type: String
      description: 云桌面安装的工具版本
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 推断：可选过滤条件：教室ID，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: pageQueryRequest
  rule: 非空，且 matchArr[0] 必须为 classroomId 精确匹配
  failure: 参数校验失败或matchArr为空时数组越界
- level: PERM
  field: classroomId
  rule: 当前用户需有该教室对应终端分组权限
  failure: 权限校验抛异常
assertions:
  success:
  - scenario: 用户有教室权限且分页参数合法
    expect: $.status=="SUCCESS"；$.content.itemArr 存在
  failure:
  - scenario: matchArr为空或非classroomId精确匹配
    trigger: 前端未传classroomId精确匹配条件
    expect: status==ERROR（参数校验，matchArr[0] 越界）
  - scenario: 无教室权限
    trigger: 用户终端分组不含该教室
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询接口
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/desktop/tci/list

> 查询课堂TCI云桌面列表：以教室ID精确匹配过滤，权限校验后分页返回TCI桌面视图。 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/desktop/tci/list<br>查询课堂TCI云桌面列表：以教室ID精确匹配过滤，权限校验后分页返回TCI桌面视<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 pageQueryRequest 与 sessionContext 非空"]
        C2["Step2: 从 matchArr[0] 解析 classroomId"]
        C3["Step3: rccPermissionChecker.checkTerminalGroupP"]
        C4["Step4: spaceTCIDesktopMgmtAPI.pageQuery(pageQue"]
        C5["Step5: 返回分页结果"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/desktop/tci/restart、/tci/shutdown、/tci/remoteAssist/assistRequest、/rcc/spacetci/desktop/restore"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/desktop/tci/list |
| Controller | RccClassroomTCIDesktopController |
| 方法名 | list |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 查询课堂TCI云桌面列表：以教室ID精确匹配过滤，权限校验后分页返回TCI桌面视图。 |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| matchArr[0] | DefaultExactMatch | 是 | 首个match必须是classroomId的精确匹配 | 包含 classroomId 精确匹配条件 |
| sortArr | Sort[] | 否 | 可选 | 排序条件 |
| limit | Integer | 否 |  | 页码与每页条数（limit） |
| page | Integer | 否 |  | 页码与每页条数（page） |## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<ViewTCIDesktopResultDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ViewTCIDesktopResultDTO[] | TCI桌面列表项（元素字段见下） |
| total | long | 总记录数 |
| desktopId | UUID | 云桌面ID |
| computerName | String | 云桌面主机名 |
| desktopPreName | String | 主机名前缀（教师机名前缀或座位名） |
| desktopState | CbbCloudDeskState | 云桌面状态 |
| disableNetwork | Boolean | 是否禁网 |
| desktopType | CbbCloudDeskType | 云桌面类型（IDV/VDI） |
| desktopRole | String | 云桌面角色（学生机/教师机） |
| desktopMac | String | 云桌面MAC |
| desktopIp | String | 云桌面IP |
| desktopImageName | String | 镜像名称 |
| desktopRootImageName | String | 根镜像名称 |
| imageType | CbbImageType | 镜像类型 |
| osType | CbbOsType | 操作系统类型 |
| osVersion | String | 系统版本 |
| systemDisk | Integer | 系统分区大小 |
| diskSize | Integer | 数据盘大小 |
| desktopCategory | String | 云桌面容量类型（PERSON/RESTORE） |
| terminalIp | String | 终端IP |
| classroomId | UUID | 教室ID |
| seatNum | Integer | 座位号 |
| hostName | String | 主机名 |
| terminalState | CbbTerminalStateEnums | 终端状态 |
| targetComputerName | String | 目标计算机名称（计算机名不存在时的提示） |
| registerState | CbbDeskRegisterState | 云桌面注册状态 |
| desktopIpv6 | String | 云桌面IPv6地址 |
| guestToolVersion | String | 云桌面安装的工具版本 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

推断：可选过滤条件：教室ID，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 pageQueryRequest 与 sessionContext 非空
2. 从 matchArr[0] 解析 classroomId
3. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(classroomId) 权限校验
4. spaceTCIDesktopMgmtAPI.pageQuery(pageQueryRequest) 分页查询
5. 返回分页结果

## 下游消费方

### 消费1：POST /rcc/classroom/desktop/tci/restart、/tci/shutdown、/tci/remoteAssist/assistRequest、/rcc/spacetci/desktop/restore

TCI桌面列表出参ViewDesktopResultDTO.desktopId（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | pageQueryRequest | 非空，且 matchArr[0] 必须为 classroomId 精确匹配 | 参数校验失败或matchArr为空时数组越界 |
| PERM | classroomId | 当前用户需有该教室对应终端分组权限 | 权限校验抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page/limit | user_input/from_query | 按业务构造 |
| matchArr[0] | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 用户有教室权限且分页参数合法 | $.status=="SUCCESS"；$.content.itemArr 存在 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| matchArr为空或非classroomId精确匹配 | 前端未传classroomId精确匹配条件 | status==ERROR（参数校验，matchArr[0] 越界） |
| 无教室权限 | 用户终端分组不含该教室 | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读查询接口 |
