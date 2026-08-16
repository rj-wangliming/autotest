---
version: '2.0'
api:
  url: /rcc/space/forceWakeUp
  method: POST
  name: 教学桌面池强制唤醒。入参 idArr[0] 为空间ID；先 rccSpaceAPI.findSpaceBaseDTOBySpaceId 查询空间，若 class
  controller: RccSpaceController
  method_ref: desktopPoolForceWakeUp
  permission: '@EnableAuthority'
  exec_mode: 批量异步（BatchTask）
  async: true
  description: 教学桌面池强制唤醒。入参 idArr[0] 为空间ID；先 rccSpaceAPI.findSpaceBaseDTOBySpaceId 查询空间，若 classroomId 为空（非教学桌面池）抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND；再 seatAPI.findAllByClassroomId 获取教室座位列表，为每个座位构造 BatchTaskItem（
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: list_space
  api: POST /rcc/space/list
  extract:
    spaceId: $.content.itemArr[0].id
  purpose: 按空间名精确过滤（exactMatchArr.fieldName=spaceName）
  request:
    body:
      exactMatchArr:
      - type: EXACT
        fieldName: spaceName
        valueArr:
        - ${param.space_name}
        matchRule: EQ
request:
  dto: IdArrWebRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotNull'
      description: 桌面池/实训空间ID数组，取 idArr[0]
      value: ${param.id_arr}
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
      description: 批量唤醒任务ID
    taskStatus:
      type: String
      description: 任务状态
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
    - PARTIAL_SUCCESS
    failure:
    - FAILURE
upstream:
- api: POST /rcc/space/list
  produces: $.content.id
  purpose: 实训空间ID（IdArrWebRequest），来源为 space list
downstream:
- api: 内部调用:rcc/SeatAPI#wakeUpDesktop
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:pa/PlatformDeskVDIMgmtAPI#findById
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: '@NotNull，不能为 null'
  failure: Assert 失败
- level: BUSINESS
  field: idArr[0]
  rule: 目标空间必须是教学桌面池（classroomId 非空）
  failure: 办公实训空间抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND
- level: BUSINESS
  field: vdiDesktopState
  rule: 仅 SLEEP 状态桌面可强制唤醒
  failure: 非 SLEEP 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESK
assertions:
  success:
  - scenario: 教室下存在多台睡眠桌面
    expect: 提交批量唤醒任务，返回 BatchTaskSubmitResult；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 仅1台睡眠桌面
    expect: 提交单任务并返回 BatchTaskSubmitResult；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 空间非教学桌面池
    trigger: 办公实训空间ID
    expect: $.status==ERROR 且 $.msgKey==CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND
  - scenario: 桌面不在睡眠状态
    trigger: 桌面 RUNNING/CLOSE
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]
cleanup: []
prereq_state:
  resource: desktop
  required_state: SLEEP
  achieve_via: []

idempotency:
  level: data_level
  note: 重复提交重复下发唤醒命令
params:
  required:
  - name: space_name
  - name: id_arr
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/forceWakeUp

> 教学桌面池强制唤醒。入参 idArr[0] 为空间ID；先 rccSpaceAPI.findSpaceBaseDTOBySpaceId 查询空间，若 classroomId 为空（非教学桌面池）抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND；再 seatAPI.findAllByClassroomId 获取教室座位列表，为每个座位构造 BatchTaskItem（RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_ITEM_NAME）注册 RccSpaceDesktopForceWakeUpBatchTaskHandler 提交任务（1个座位单任务，多个 enableParallel）。Handler 中校验桌面状态必须为 SLEEP（否则抛 RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESKTOP_STATE_NOT_SATISFIED），然后 seatAPI.wakeUpDesktop 唤醒。 ｜ @EnableAuthority ｜ 批量异步（BatchTask）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/space/list"]
    end
    B["POST /rcc/space/forceWakeUp<br>教学桌面池强制唤醒。入参 idArr[0] 为空间ID；先 rccSpaceAP<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/builder)"]
        C2["Step2: rccSpaceAPI.findSpaceBaseDTOBySpaceId(id"]
        C3["Step3: seatAPI.findAllByClassroomId(classroomId"]
        C4["Step4: 为每个座位构造 DefaultBatchTaskItem（distinct，it"]
        C5["Step5: 构造 RccSpaceDesktopForceWakeUpBatchTaskHa"]
        C6["Step6: 1个座位单任务（SINGLE_FORCE_WAKE_UP_TASK_DESC），"]
        C1 --> C2
        C7["Step7: 返回 BatchTaskSubmitResult"]
        C6 --> C7
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
| URL | /rcc/space/forceWakeUp |
| Controller | RccSpaceController |
| 方法名 | desktopPoolForceWakeUp |
| 权限注解 | @EnableAuthority |
| 执行方式 | 批量异步（BatchTask） |
| 业务含义 | 教学桌面池强制唤醒。入参 idArr[0] 为空间ID；先 rccSpaceAPI.findSpaceBaseDTOBySpaceId 查询空间，若 classroomId 为空（非教学桌面池）抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND；再 seatAPI.findAllByClassroomId 获取教室座位列表，为每个座位构造 BatchTaskItem（RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_ITEM_NAME）注册 RccSpaceDesktopForceWakeUpBatchTaskHandler 提交任务（1个座位单任务，多个 enableParallel）。Handler 中校验桌面状态必须为 SLEEP（否则抛 RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESKTOP_STATE_NOT_SATISFIED），然后 seatAPI.wakeUpDesktop 唤醒。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotNull | 桌面池/实训空间ID数组，取 idArr[0] |

## 出参详情

| 返回类型 | CommonWebResponse<?>（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批量唤醒任务ID |
| taskStatus | String | 任务状态 |

## 上游前置业务

### 前置1：POST /rcc/space/list

实训空间ID（IdArrWebRequest），来源为 space list（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RccSpaceDesktopForceWakeUpBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | seatAPI.getSeatInfo(seatId) 查询座位 |
| 2 | cbbDeskMgmtAPI.findById(seatInfoDTO.getVdiDesktopId()) 查询 VDI 桌面 |
| 3 | 桌面状态非 SLEEP：抛 RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESKTOP_STATE_NOT_SATISFIED（带桌面名与状态） |
| 4 | seatAPI.wakeUpDesktop(seatId) 下发唤醒 |
| 5 | 成功：auditLogAPI.recordLog(RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_SUC_LOG) |
| 6 | 失败：recordLog(RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_FAIL_LOG)，返回 FAILURE |
| 7 | onFinish：单台 RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_SINGLE_SUC/FAIL，多台 RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_BATCH_RESULT |

### 处理流程

1. Assert.notNull(request/builder)
2. rccSpaceAPI.findSpaceBaseDTOBySpaceId(idArr[0])；classroomId==null 抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND
3. seatAPI.findAllByClassroomId(classroomId) 查询座位列表
4. 为每个座位构造 DefaultBatchTaskItem（distinct，itemName=RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_ITEM_NAME）
5. 构造 RccSpaceDesktopForceWakeUpBatchTaskHandler 注入 cbbDeskMgmtAPI/auditLogAPI/seatAPI
6. 1个座位单任务（SINGLE_FORCE_WAKE_UP_TASK_DESC），多个 enableParallel 批量任务（FORCE_WAKE_UP_TASK_DESC）
7. 返回 BatchTaskSubmitResult

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotNull，不能为 null | Assert 失败 |
| BUSINESS | idArr[0] | 目标空间必须是教学桌面池（classroomId 非空） | 办公实训空间抛 CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND |
| BUSINESS | vdiDesktopState | 仅 SLEEP 状态桌面可强制唤醒 | 非 SLEEP 抛 RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESKTOP_STATE_NOT_SATISFIED |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室下存在多台睡眠桌面 | 提交批量唤醒任务，返回 BatchTaskSubmitResult |
| 仅1台睡眠桌面 | 提交单任务并返回 BatchTaskSubmitResult |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 空间非教学桌面池 | 办公实训空间ID | $.status==ERROR 且 $.msgKey==CLASSROOM_TIP_RCDC_CLASSROOM_NOT_FOUND |
| 桌面不在睡眠状态 | 桌面 RUNNING/CLOSE | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"] |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复提交重复下发唤醒命令 |
