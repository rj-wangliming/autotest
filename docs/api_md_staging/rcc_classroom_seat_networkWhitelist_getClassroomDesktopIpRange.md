---
version: '2.0'
api:
  url: /rcc/classroom/seat/networkWhitelist/getClassroomDesktopIpRange
  method: POST
  name: 获取教室下云桌面 IP 的使用情况（VDI 与 IDV IP 区间列表），供前端网络白名单配置展示
  controller: RccSeatManageController
  method_ref: getClassroomDesktopIpRange
  permission: 无
  exec_mode: 同步
  async: false
  description: 获取教室下云桌面 IP 的使用情况（VDI 与 IDV IP 区间列表），供前端网络白名单配置展示
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
  dto: ClassroomIdRequest
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
    vdiIpList:
      type: List<IpIntervalDTO>
      description: VDI 云桌面 IP 区间使用列表（元素字段见下，IpIntervalDTO）
    ipStart:
      type: String
      description: 起始IP（IpIntervalDTO 元素字段）
    ipEnd:
      type: String
      description: 结束IP（IpIntervalDTO 元素字段）
    idvIpList:
      type: List<IpIntervalDTO>
      description: IDV 云桌面 IP 区间使用列表（元素字段同 vdiIpList）
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
downstream: []
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 为空时参数校验失败
- level: PERM
  field: classroomId
  rule: 教室终端组权限
  failure: 无权限抛业务异常
assertions:
  success:
  - scenario: 传入有效教室ID
    expect: $.status=="SUCCESS" 且（$.content.vdiIpList 或 $.content.idvIpList 非空）
  failure:
  - scenario: classroomId 为空
    trigger: 请求缺参
    expect: $.status=="ERROR"（参数校验失败，Assert.notNull）
  - scenario: 无教室权限
    trigger: 权限校验抛错
    expect: $.status=="ERROR"（数据权限校验失败）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/networkWhitelist/getClassroomDesktopIpRange

> 获取教室下云桌面 IP 的使用情况（VDI 与 IDV IP 区间列表），供前端网络白名单配置展示 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/seat/networkWhitelist/getClassroomDesktopIpRange<br>获取教室下云桌面 IP 的使用情况（VDI 与 IDV IP 区间列表），供前端<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/sessionContext"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: networkWhiteListAPI.getClassroomDesktopI"]
        C4["Step4: 返回 DefaultWebResponse.success(desktopIpD"]
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
| URL | /rcc/classroom/seat/networkWhitelist/getClassroomDesktopIpRange |
| Controller | RccSeatManageController |
| 方法名 | getClassroomDesktopIpRange |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 获取教室下云桌面 IP 的使用情况（VDI 与 IDV IP 区间列表），供前端网络白名单配置展示 |

## 入参详情

### ClassroomIdRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ClassroomDesktopIpDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| vdiIpList | List<IpIntervalDTO> | VDI 云桌面 IP 区间使用列表（元素字段见下，IpIntervalDTO） |
| ipStart | String | 起始IP（IpIntervalDTO 元素字段） |
| ipEnd | String | 结束IP（IpIntervalDTO 元素字段） |
| idvIpList | List<IpIntervalDTO> | IDV 云桌面 IP 区间使用列表（元素字段同 vdiIpList） |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 request/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(classroomId) 校验权限
3. networkWhiteListAPI.getClassroomDesktopIpRange(classroomId) 查询 IP 使用情况
4. 返回 DefaultWebResponse.success(desktopIpDTO)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 为空时参数校验失败 |
| PERM | classroomId | 教室终端组权限 | 无权限抛业务异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效教室ID | $.status=="SUCCESS" 且（$.content.vdiIpList 或 $.content.idvIpList 非空） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| classroomId 为空 | 请求缺参 | $.status=="ERROR"（参数校验失败，Assert.notNull） |
| 无教室权限 | 权限校验抛错 | $.status=="ERROR"（数据权限校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询，无副作用 |
