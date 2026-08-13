---
version: '2.0'
api:
  url: /space/strategy/tci/edit
  method: POST
  name: 修改 TCI 课程策略。默认先校验 id 非空，defaultEdit 走 SpaceStrategyGroupTCIValidation.validateBe
  controller: SpaceDeskStrategyGroupTCIController
  method_ref: edit
  permission: '@EnableAuthority'
  exec_mode: 异步任务流：更新平台策略组 → 更新本地策略+失效缓存
  async: true
  description: 修改 TCI 课程策略。默认先校验 id 非空，defaultEdit 走 SpaceStrategyGroupTCIValidation.validateBeforeUpdate：执行创建期全部校验（validStrategy + 名称查重 62100317/62100220），校验旧策略状态 AVAILABLE(62110005)，若策略已关联课程镜像则校验系统盘不得缩小(62110006)、
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: list_tci_strategy
  api: POST /space/strategy/tci/list
  extract:
    strategyId: $.content.itemArr[0].id
  purpose: 按策略名精确过滤（matchArr.fieldName=strategyName）
  request:
    body:
      matchArr:
      - fieldName: strategyName
        matchType: EQUAL
        value: ${param.strategy_name}
request:
  dto: SpaceDeskStrategyGroupTCI（继承 AbstractSpaceDeskStrategyGroup）
  body:
    id:
      type: UUID
      required: true
      constraint: 必填（Assert.notNull(id)）
      description: 待修改策略 id
    name:
      type: String
      required: true
      constraint: 非空、≤32、名称正则
      description: 策略名称（允许修改，需查重）
    pattern:
      type: CbbCloudDeskPattern
      required: true
      constraint: '@NotNull'
      description: 桌面类型
    strategyType:
      type: DeskVirtualizationType
      required: true
      constraint: 必须 VOI
      description: 策略类型
    systemSize:
      type: Integer
      required: true
      constraint: '@NotNull @Range(0,2048)'
      description: 系统盘大小（关联镜像时只可扩大）
    enableDiskConfig:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 数据盘开关（关联镜像时不可变化）
    diskSize:
      type: Integer
      required: false
      constraint: 开启数据盘时必填
      description: 数据盘大小（关联镜像时只可扩大）
    enableScheduleStrategy:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 磁盘定期策略开关
    diskRestoreStrategyArr:
      type: TCIDiskStrategyDTO[]
      required: false
      constraint: 开启定期时非空
      description: 还原周期设置
    enableAutoEdit:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 自动编辑
    enableForceAutoEdit:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 强制自动退出
    enableAdaptiveResolution:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 分辨率自适应
    platformStrategyGroup:
      type: PlatformStrategyGroup
      required: true
      constraint: '@NotNull'
      description: 平台策略组（更新时回填）
    enablePersonalConfig:
      type: Boolean
      required: false
      description: 浮动个性配置（enablePersonalConfig）
    deskPersonalConfigStrategyType:
      type: String
      required: false
      description: 浮动个性配置（deskPersonalConfigStrategyType）
    personalConfigDiskSize:
      type: Integer
      required: false
      description: 浮动个性配置（personalConfigDiskSize）
    enableInternet:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 联网
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: 'null'
      description: 修改成功返回空 content
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
- api: POST /space/strategy/tci/list
  produces: $.content.itemArr[*].id
  purpose: TCI课程策略ID，来源为策略列表
- api: POST /space/deskStrategy/getSupportUsbTyp
  produces: $.content.itemArr[*].id
  purpose: USB设备类型ID数组（推断）
downstream:
- api: POST /space/strategy/tci/list
  purpose: 修改后刷新策略列表
- api: POST /space/strategy/tci/condition/list
  purpose: 课程镜像编辑时重新选择策略
constraints:
- level: AUTH
  field: 接口
  rule: '@EnableAuthority 需操作权限'
  failure: 无权限 401/403
- level: BUSINESS
  field: state
  rule: 旧策略必须 AVAILABLE
  failure: '62110005'
- level: BUSINESS
  field: systemSize
  rule: 关联镜像时系统盘不得缩小
  failure: '62110006'
- level: BUSINESS
  field: enableDiskConfig
  rule: 关联镜像时数据盘开关不得变化
  failure: '62110007'
- level: BUSINESS
  field: diskSize
  rule: 关联镜像时数据盘不得缩小
  failure: '62110008'
- level: BUSINESS
  field: name
  rule: 名称不得重复
  failure: 62100317/62100220
assertions:
  success:
  - scenario: 入参合法且无关联镜像限制
    expect: $.status==SUCCESS
  - scenario: 关联镜像且规格只增不减
    expect: $.status==SUCCESS
  failure:
  - scenario: 关联镜像时缩小系统盘
    trigger: 系统盘由 100G 改 60G
    expect: $.status==ERROR 且 $.msgKey==62110006
  - scenario: 关联镜像时关闭数据盘
    trigger: enableDiskConfig true→false
    expect: $.status==ERROR 且 $.msgKey==62110007
  - scenario: 旧策略状态非 AVAILABLE
    trigger: 策略正在删除
    expect: $.status==ERROR 且 $.msgKey==62110005
cleanup:
- api: 无
  note: 无对应 HTTP 清理接口（编辑不创建资源，无回滚/undo）
idempotency:
  level: data_level
  note: 依赖乐观锁 version，重复提交相同数据会因版本冲突失败；相同内容重复提交结果一致
params:
  required:
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
---
# POST /space/strategy/tci/edit

> 修改 TCI 课程策略。默认先校验 id 非空，defaultEdit 走 SpaceStrategyGroupTCIValidation.validateBeforeUpdate：执行创建期全部校验（validStrategy + 名称查重 62100317/62100220），校验旧策略状态 AVAILABLE(62110005)，若策略已关联课程镜像则校验系统盘不得缩小(62110006)、数据盘开关不得变化(62110007)、数据盘不得缩小(62110008)，最后通过 SPI 校验策略变更合法；随后 AbstractSpaceDeskStrategyGroupAPIImpl.update 维护旧数据并转换平台策略组，执行 UpdateTciSpaceStrategyGroupTaskHandle（更新平台策略组 → 更新本地主数据+失效缓存）。 ｜ @EnableAuthority ｜ 异步任务流：更新平台策略组 → 更新本地策略+失效缓存

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /space/strategy/tci/list"]
        A2["POST /space/deskStrategy/getSupportUsbTyp"]
    end
    B["POST /space/strategy/tci/edit<br>修改 TCI 课程策略。默认先校验 id 非空，defaultEdit 走 Sp<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(spaceStrategyGroup) 与 Ass"]
        C2["Step2: super.defaultEdit(spaceStrategyGroup)（Ab"]
        C3["Step3: SpaceStrategyGroupTCIValidation.validate"]
        C4["Step4: AbstractSpaceDeskStrategyGroupAPIImpl.up"]
        C5["Step5: 执行 UpdateTciSpaceStrategyGroupTaskHandle"]
        C6["Step6: 返回成功响应"]
        C1 --> C2
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
| URL | /space/strategy/tci/edit |
| Controller | SpaceDeskStrategyGroupTCIController |
| 方法名 | edit |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步任务流：更新平台策略组 → 更新本地策略+失效缓存 |
| 业务含义 | 修改 TCI 课程策略。默认先校验 id 非空，defaultEdit 走 SpaceStrategyGroupTCIValidation.validateBeforeUpdate：执行创建期全部校验（validStrategy + 名称查重 62100317/62100220），校验旧策略状态 AVAILABLE(62110005)，若策略已关联课程镜像则校验系统盘不得缩小(62110006)、数据盘开关不得变化(62110007)、数据盘不得缩小(62110008)，最后通过 SPI 校验策略变更合法；随后 AbstractSpaceDeskStrategyGroupAPIImpl.update 维护旧数据并转换平台策略组，执行 UpdateTciSpaceStrategyGroupTaskHandle（更新平台策略组 → 更新本地主数据+失效缓存）。 |

## 入参详情

### SpaceDeskStrategyGroupTCI（继承 AbstractSpaceDeskStrategyGroup）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | 必填（Assert.notNull(id)） | 待修改策略 id |
| name | String | 是 | 非空、≤32、名称正则 | 策略名称（允许修改，需查重） |
| pattern | CbbCloudDeskPattern | 是 | @NotNull | 桌面类型 |
| strategyType | DeskVirtualizationType | 是 | 必须 VOI | 策略类型 |
| systemSize | Integer | 是 | @NotNull @Range(0,2048) | 系统盘大小（关联镜像时只可扩大） |
| enableDiskConfig | Boolean | 是 | @NotNull | 数据盘开关（关联镜像时不可变化） |
| diskSize | Integer | 否 | 开启数据盘时必填 | 数据盘大小（关联镜像时只可扩大） |
| enableScheduleStrategy | Boolean | 是 | @NotNull | 磁盘定期策略开关 |
| diskRestoreStrategyArr | TCIDiskStrategyDTO[] | 否 | 开启定期时非空 | 还原周期设置 |
| enableAutoEdit | Boolean | 是 | @NotNull | 自动编辑 |
| enableForceAutoEdit | Boolean | 是 | @NotNull | 强制自动退出 |
| enableAdaptiveResolution | Boolean | 是 | @NotNull | 分辨率自适应 |
| platformStrategyGroup | PlatformStrategyGroup | 是 | @NotNull | 平台策略组（更新时回填） |
| enableInternet | Boolean | 是 | @NotNull | 联网 |
| enablePersonalConfig | Boolean | 否 |  | 浮动个性配置（enablePersonalConfig） |
| deskPersonalConfigStrategyType | String | 否 |  | 浮动个性配置（deskPersonalConfigStrategyType） |
| personalConfigDiskSize | Integer | 否 |  | 浮动个性配置（personalConfigDiskSize） |## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | null | 修改成功返回空 content |

## 上游前置业务

### 前置1：POST /space/strategy/tci/list

TCI课程策略ID，来源为策略列表（由 field_map 契约映射）

### 前置2：POST /space/deskStrategy/getSupportUsbTyp

USB设备类型ID数组（推断）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：UpdateTciSpaceStrategyGroupTaskHandle（StateTaskHandle，同步状态机）

| 步骤 | 说明 |
|---|---|
| 1 | UpdatePlatformStrategyGroupProcessor：platformStrategyGroupAPI.update 更新平台策略组（失败不 undo） |
| 2 | UpdateLocalStrategyGroupProcessor：repository.update 更新本地主数据并失效 SpaceStrategyGroupCaches 缓存 |

### 处理流程

1. Assert.notNull(spaceStrategyGroup) 与 Assert.notNull(id)
2. super.defaultEdit(spaceStrategyGroup)（AbstractSpaceDeskStrategyGroupController → 框架 defaultEdit）
3. SpaceStrategyGroupTCIValidation.validateBeforeUpdate：先 validateBeforeCreate（validStrategy + 名称查重），再 validState(62110005)，关联课程镜像时 validDisk（系统盘 62110006、数据盘开关 62110007、数据盘 62110008），最后 validateBeforeLessonStrategyChange（SPI）
4. AbstractSpaceDeskStrategyGroupAPIImpl.update：findById 取旧策略维护旧数据；convertPlatformStrategyGroup 回填平台策略组
5. 执行 UpdateTciSpaceStrategyGroupTaskHandle：a) UpdatePlatformStrategyGroupProcessor（平台更新，无 undo）b) UpdateLocalStrategyGroupProcessor（本地更新 + invalidateCache 失效缓存）
6. 返回成功响应

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| AUTH | 接口 | @EnableAuthority 需操作权限 | 无权限 401/403 |
| BUSINESS | state | 旧策略必须 AVAILABLE | 62110005 |
| BUSINESS | systemSize | 关联镜像时系统盘不得缩小 | 62110006 |
| BUSINESS | enableDiskConfig | 关联镜像时数据盘开关不得变化 | 62110007 |
| BUSINESS | diskSize | 关联镜像时数据盘不得缩小 | 62110008 |
| BUSINESS | name | 名称不得重复 | 62100317/62100220 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |
| name | user_input/from_query | 按业务构造 |
| pattern | user_input/from_query | 按业务构造 |
| strategyType | user_input/from_query | 按业务构造 |
| systemSize | user_input/from_query | 按业务构造 |
| enableDiskConfig | user_input/from_query | 按业务构造 |
| diskSize | user_input/from_query | 按业务构造 |
| enableScheduleStrategy | user_input/from_query | 按业务构造 |
| diskRestoreStrategyArr | user_input/from_query | 按业务构造 |
| enableAutoEdit | user_input/from_query | 按业务构造 |
| enableForceAutoEdit | user_input/from_query | 按业务构造 |
| enableAdaptiveResolution | user_input/from_query | 按业务构造 |
| platformStrategyGroup | user_input/from_query | 按业务构造 |
| enablePersonalConfig/deskPersonalConfigStrategyType/personalConfigDiskSize | user_input/from_query | 按业务构造 |
| enableInternet | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 入参合法且无关联镜像限制 | $.status==SUCCESS |
| 关联镜像且规格只增不减 | $.status==SUCCESS |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 关联镜像时缩小系统盘 | 系统盘由 100G 改 60G | $.status==ERROR 且 $.msgKey==62110006 |
| 关联镜像时关闭数据盘 | enableDiskConfig true→false | $.status==ERROR 且 $.msgKey==62110007 |
| 旧策略状态非 AVAILABLE | 策略正在删除 | $.status==ERROR 且 $.msgKey==62110005 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无 | 更新状态机不实现 undo（平台与本地无耦合，失败由乐观锁/重试处理） |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 依赖乐观锁 version，重复提交相同数据会因版本冲突失败；相同内容重复提交结果一致 |
