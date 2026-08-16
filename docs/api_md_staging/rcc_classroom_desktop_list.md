---
version: '2.0'
api:
  url: /rcc/classroom/desktop/list
  method: POST
  name: 查询课堂云桌面列表：通用分页查询，返回VDI课堂桌面视图数据。
  controller: RccClassroomDesktopController
  method_ref: list
  permission: 无
  exec_mode: sync
  async: false
  description: 查询课堂云桌面列表：通用分页查询，返回VDI课堂桌面视图数据。
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
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
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
    searchKeyword:
      type: String
      required: false
      description: 搜索关键字（模糊搜索）
    matchArr:
      type: Match[]
      required: false
      constraint: 可选，精确/模糊匹配条件
      description: 查询过滤条件数组
      value:
      - type: EXACT
        fieldName: classroomId
        valueArr:
        - ${param.classroom_id}
        matchRule: EQ
    sortArr:
      type: Sort[]
      required: false
      constraint: 可选
      description: 排序条件
    exactMatchArr:
      type: ExactMatch[]
      required: false
      constraint: 可选（旧格式，name+valueArr）
      description: 精确匹配条件数组（与 matchArr 并行，真实请求同时携带）
    needForceRefresh:
      type: Boolean
      required: false
      constraint: '@Nullable，默认 false'
      description: 是否强制刷新
    isAutomaticRefresh:
      type: Boolean
      required: false
      constraint: '@Nullable，默认 true'
      description: 是否自动刷新
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ViewDesktopResultDTO[]
      description: 桌面列表项（元素字段见下）
    total:
      type: long
      description: 总记录数
    desktopId:
      type: UUID
      description: 云桌面ID
    strategyId:
      type: UUID
      description: 云桌面策略ID
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
      type: DesktopRoleEnum
      description: 云桌面角色（学生机/教师机）
    desktopMac:
      type: String
      description: 云桌面MAC
    desktopIp:
      type: String
      description: 云桌面IP
    desktopIpv6:
      type: String
      description: 云桌面IPv6地址
    guestToolVersion:
      type: String
      description: 云桌面安装的工具版本
    vgpuType:
      type: VgpuType
      description: vGPU类型
    vgpuExtraInfo:
      type: String
      description: vGPU附加信息
    osVersion:
      type: String
      description: 系统版本
    desktopImageName:
      type: String
      description: 镜像名称
    desktopRootImageName:
      type: String
      description: 根镜像模板名称
    desktopImageRoleType:
      type: ImageRoleType
      description: 镜像角色类型
    imageType:
      type: CbbImageType
      description: 镜像类型
    osType:
      type: CbbOsType
      description: 操作系统类型
    cpu:
      type: Integer
      description: CPU核数
    memory:
      type: Double
      description: 内存大小（GB）
    systemDisk:
      type: Integer
      description: 系统分区大小
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
    targetComputerName:
      type: String
      description: 目标计算机名称（计算机名不存在时的提示）
    faultState:
      type: Boolean
      description: 云桌面报障状态
    faultDescription:
      type: String
      description: 云桌面报障内容
    version:
      type: Integer
      description: 版本号
    registerState:
      type: CbbDeskRegisterState
      description: 云桌面注册状态
    platformId:
      type: UUID
      description: 云平台ID
    platformType:
      type: CloudPlatformType
      description: 云平台类型
    platformName:
      type: String
      description: 云平台名称
    platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态
    vgpuDesktop:
      type: Boolean
      description: 是否vGPU桌面
    vgpuModel:
      type: String
      description: vGPU型号
    "itemArr[]_desktopId":
      type: UUID
      description: 云桌面ID
    "itemArr[]_strategyId":
      type: UUID
      description: 云桌面策略ID
    "itemArr[]_computerName":
      type: String
      description: 云桌面主机名
    "itemArr[]_desktopPreName":
      type: String
      description: 主机名前缀（教师机名前缀或座位名）
    "itemArr[]_desktopState":
      type: CbbCloudDeskState
      description: 云桌面状态
    "itemArr[]_disableNetwork":
      type: Boolean
      description: 是否禁网
    "itemArr[]_desktopType":
      type: CbbCloudDeskType
      description: 云桌面类型（IDV/VDI）
    "itemArr[]_desktopRole":
      type: DesktopRoleEnum
      description: 云桌面角色（学生机/教师机）
    "itemArr[]_desktopMac":
      type: String
      description: 云桌面MAC
    "itemArr[]_desktopIp":
      type: String
      description: 云桌面IP
    "itemArr[]_desktopIpv6":
      type: String
      description: 云桌面IPv6地址
    "itemArr[]_guestToolVersion":
      type: String
      description: 云桌面安装的工具版本
    "itemArr[]_vgpuType":
      type: VgpuType
      description: vGPU类型
    "itemArr[]_vgpuExtraInfo":
      type: String
      description: vGPU附加信息
    "itemArr[]_osVersion":
      type: String
      description: 系统版本
    "itemArr[]_desktopImageName":
      type: String
      description: 镜像名称
    "itemArr[]_desktopRootImageName":
      type: String
      description: 根镜像模板名称
    "itemArr[]_desktopImageRoleType":
      type: ImageRoleType
      description: 镜像角色类型
    "itemArr[]_imageType":
      type: CbbImageType
      description: 镜像类型
    "itemArr[]_osType":
      type: CbbOsType
      description: 操作系统类型
    "itemArr[]_cpu":
      type: Integer
      description: CPU核数
    "itemArr[]_memory":
      type: Double
      description: 内存大小（GB）
    "itemArr[]_systemDisk":
      type: Integer
      description: 系统分区大小
    "itemArr[]_desktopCategory":
      type: String
      description: 云桌面容量类型（PERSON/RESTORE）
    "itemArr[]_terminalIp":
      type: String
      description: 终端IP
    "itemArr[]_classroomId":
      type: UUID
      description: 教室ID
    "itemArr[]_seatNum":
      type: Integer
      description: 座位号
    "itemArr[]_targetComputerName":
      type: String
      description: 目标计算机名称（计算机名不存在时的提示）
    "itemArr[]_faultState":
      type: Boolean
      description: 云桌面报障状态
    "itemArr[]_faultDescription":
      type: String
      description: 云桌面报障内容
    "itemArr[]_version":
      type: Integer
      description: 版本号
    "itemArr[]_registerState":
      type: CbbDeskRegisterState
      description: 云桌面注册状态
    "itemArr[]_platformId":
      type: UUID
      description: 云平台ID
    "itemArr[]_platformType":
      type: CloudPlatformType
      description: 云平台类型
    "itemArr[]_platformName":
      type: String
      description: 云平台名称
    "itemArr[]_platformStatus":
      type: CloudPlatformStatus
      description: 云平台状态
    "itemArr[]_vgpuDesktop":
      type: Boolean
      description: 是否vGPU桌面
    "itemArr[]_vgpuModel":
      type: String
      description: vGPU型号
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 推断：可选过滤条件：教室ID，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: pageQueryRequest
  rule: 非空且分页参数合法
  failure: 参数校验失败
assertions:
  success:
  - scenario: 分页参数合法
    expect: $.status=="SUCCESS"；$.content.itemArr 存在
  failure:
  - scenario: 分页参数不合法
    trigger: page/limit非法或dmql解析失败
    expect: status==ERROR（查询异常）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询接口，天然幂等
params:
  required:
  - name: classroom_name
  - name: classroom_id
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/desktop/list

> 查询课堂云桌面列表：通用分页查询，返回VDI课堂桌面视图数据。 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/desktop/list<br>查询课堂云桌面列表：通用分页查询，返回VDI课堂桌面视图数据。<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 pageQueryRequest 非空"]
        C2["Step2: desktopMgmtAPI.pageQuery(pageQueryReques"]
        C3["Step3: 返回 PageQueryResponse"]
        C1 --> C2
        C2 --> C3
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/desktop/shutdown、/restart、/powerOff、/forceWakeUp、/cancelFault、/gtlog/collectLog、/remoteAssist/assistRequest"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/desktop/list |
| Controller | RccClassroomDesktopController |
| 方法名 | list |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 查询课堂云桌面列表：通用分页查询，返回VDI课堂桌面视图数据。 |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| matchArr | Match[] | 否 | 可选，精确/模糊匹配条件 | 查询过滤条件数组 |
| sortArr | Sort[] | 否 | 可选 | 排序条件 |
| limit | Integer | 否 |  | 页码与每页条数（limit） |
| page | Integer | 否 |  | 页码与每页条数（page） |
## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<ViewDesktopResultDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ViewDesktopResultDTO[] | 桌面列表项（元素字段见下） |
| total | long | 总记录数 |
| desktopId | UUID | 云桌面ID |
| strategyId | UUID | 云桌面策略ID |
| computerName | String | 云桌面主机名 |
| desktopPreName | String | 主机名前缀（教师机名前缀或座位名） |
| desktopState | CbbCloudDeskState | 云桌面状态 |
| disableNetwork | Boolean | 是否禁网 |
| desktopType | CbbCloudDeskType | 云桌面类型（IDV/VDI） |
| desktopRole | DesktopRoleEnum | 云桌面角色（学生机/教师机） |
| desktopMac | String | 云桌面MAC |
| desktopIp | String | 云桌面IP |
| desktopIpv6 | String | 云桌面IPv6地址 |
| guestToolVersion | String | 云桌面安装的工具版本 |
| vgpuType | VgpuType | vGPU类型 |
| vgpuExtraInfo | String | vGPU附加信息 |
| osVersion | String | 系统版本 |
| desktopImageName | String | 镜像名称 |
| desktopRootImageName | String | 根镜像模板名称 |
| desktopImageRoleType | ImageRoleType | 镜像角色类型 |
| imageType | CbbImageType | 镜像类型 |
| osType | CbbOsType | 操作系统类型 |
| cpu | Integer | CPU核数 |
| memory | Double | 内存大小（GB） |
| systemDisk | Integer | 系统分区大小 |
| desktopCategory | String | 云桌面容量类型（PERSON/RESTORE） |
| terminalIp | String | 终端IP |
| classroomId | UUID | 教室ID |
| seatNum | Integer | 座位号 |
| targetComputerName | String | 目标计算机名称（计算机名不存在时的提示） |
| faultState | Boolean | 云桌面报障状态 |
| faultDescription | String | 云桌面报障内容 |
| version | Integer | 版本号 |
| registerState | CbbDeskRegisterState | 云桌面注册状态 |
| platformId | UUID | 云平台ID |
| platformType | CloudPlatformType | 云平台类型 |
| platformName | String | 云平台名称 |
| platformStatus | CloudPlatformStatus | 云平台状态 |
| vgpuDesktop | Boolean | 是否vGPU桌面 |
| vgpuModel | String | vGPU型号 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

推断：可选过滤条件：教室ID，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 pageQueryRequest 非空
2. desktopMgmtAPI.pageQuery(pageQueryRequest) 分页查询
3. 返回 PageQueryResponse

## 下游消费方

### 消费1：POST /rcc/classroom/desktop/shutdown、/restart、/powerOff、/forceWakeUp、/cancelFault、/gtlog/collectLog、/remoteAssist/assistRequest

桌面列表出参ViewDesktopResultDTO.desktopId（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | pageQueryRequest | 非空且分页参数合法 | 参数校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page/limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 分页参数合法 | $.status=="SUCCESS"；$.content.itemArr 存在 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 分页参数不合法 | page/limit非法或dmql解析失败 | status==ERROR（查询异常） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读查询接口，天然幂等 |
