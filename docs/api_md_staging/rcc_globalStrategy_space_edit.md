---
version: '2.0'
api:
  url: /rcc/globalStrategy/space/edit
  method: POST
  name: 设置VDI全局策略（终端日志保留、清理闲置桌面、亲和启动策略、还原镜像发布更新），并同步更新各镜像云平台亲和性规则
  controller: RccGlobalStrategyController
  method_ref: editVdiConfig
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 设置VDI全局策略（终端日志保留、清理闲置桌面、亲和启动策略、还原镜像发布更新），并同步更新各镜像云平台亲和性规则
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: detail
  api: POST /rcc/globalStrategy/space/detail
  purpose: 查询当前全局策略
  extract:
    interval: $.content.interval
    enableClear: $.content.enableClear
request:
  dto: RccGlobalStrategyRequest
  body:
    expireCleanDay:
      type: Integer
      required: true
      constraint: '@NotNull + @Range(1-200)'
      description: 终端日志保留天数
    enableClear:
      type: Boolean
      required: true
      constraint: '@NotNull 默认false'
      description: 是否启用清理闲置桌面
    interval:
      type: Double
      required: false
      constraint: '@Nullable 默认2.0'
      description: 闲置桌面清理间隔时长
    startStrategyType:
      type: RccDesktopStartStrategyType
      required: true
      constraint: '@NotNull 非空'
      description: VDI启动策略类型
    enableRecoverableImagePublishUpdate:
      type: Boolean
      required: true
      constraint: '@NotNull 非空'
      description: 是否启用还原镜像自动发布策略
    gatherRatio:
      type: Integer
      required: true
      constraint: '@NotNull + @Range(1-1000)'
      description: 聚集比例
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
      description: 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_MODULE_OPERATE_SUCCESS）
upstream:
- api: 内部调用:RccGlobalStrategyAPI
  purpose: 更新终端日志保留配置
- api: 内部调用:PlatformRcoGlobalParameterAPI
  purpose: 更新 CLEAR_INVALID_CLOUD_DESKTOP / RCC_VDI_START_STRATEGY / RCC_AFFINITY_GATHER_RATIO 参数
- api: 内部调用:TCIGlobalStrategyAPI
  purpose: 更新还原镜像自动发布策略
- api: 内部调用:RccAffinityAPI
  purpose: 列出全部亲和性规则
- api: 内部调用:ClassroomImageAPI
  purpose: 按镜像取关联云平台列表
- api: 内部调用:PlatformVDIDeskGroupMgmtAPI
  purpose: 按云平台更新RCCP亲和性规则
downstream:
- api: 内部调用:PlatformVDIDeskGroupMgmtAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: expireCleanDay
  rule: '@Range(1-200)'
  failure: webmvc 参数校验异常
- level: request
  field: gatherRatio
  rule: '@Range(1-1000)'
  failure: webmvc 参数校验异常
- level: request
  field: startStrategyType/enableClear/enableReco
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: VDI模型且存在变化
    expect: $.status==SUCCESS
  - scenario: 非VDI模型
    expect: $.status==SUCCESS
  - scenario: 无任何变化
    expect: $.status==SUCCESS
  failure:
  - scenario: 亲和规则更新异常
    trigger: 某平台更新失败
    expect: $.status==SUCCESS（亲和规则更新异常仅记录日志，接口仍成功）
cleanup: []
idempotency:
  level: data_level
  note: 每次提交都会重新遍历全部亲和性规则并逐平台更新（值相同也执行更新动作），参数本身有值对比；无事务回滚保护
---
# POST /rcc/globalStrategy/space/edit

> 设置VDI全局策略（终端日志保留、清理闲置桌面、亲和启动策略、还原镜像发布更新），并同步更新各镜像云平台亲和性规则 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/globalStrategy/space/edit<br>设置VDI全局策略（终端日志保留、清理闲置桌面、亲和启动策略、还原镜像发布更新）<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request 非空"]
        C2["Step2: editRccTerminalLogConfig：变化则更新+审计"]
        C3["Step3: 非VDI模型：无其他变更时记录统一成功审计并返回（仅终端日志配置生效）"]
        C4["Step4: VDI模型：editClearInvalidCloudDesktop（对比后 u"]
        C5["Step5: 四个维度均无变化 → 统一记录 RCDC_RCC_EDIT_GLOBAL_STR"]
        C6["Step6: 返回 success(RCDC_RCC_MODULE_OPERATE_SUCCE"]
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
| URL | /rcc/globalStrategy/space/edit |
| Controller | RccGlobalStrategyController |
| 方法名 | editVdiConfig |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 设置VDI全局策略（终端日志保留、清理闲置桌面、亲和启动策略、还原镜像发布更新），并同步更新各镜像云平台亲和性规则 |

## 入参详情

### RccGlobalStrategyRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| expireCleanDay | Integer | 是 | @NotNull + @Range(1-200) | 终端日志保留天数 |
| enableClear | Boolean | 是 | @NotNull 默认false | 是否启用清理闲置桌面 |
| interval | Double | 否 | @Nullable 默认2.0 | 闲置桌面清理间隔时长 |
| startStrategyType | RccDesktopStartStrategyType | 是 | @NotNull 非空 | VDI启动策略类型 |
| enableRecoverableImagePublishUpdate | Boolean | 是 | @NotNull 非空 | 是否启用还原镜像自动发布策略 |
| gatherRatio | Integer | 是 | @NotNull + @Range(1-1000) | 聚集比例 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | null | 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_MODULE_OPERATE_SUCCESS） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert request 非空
2. editRccTerminalLogConfig：变化则更新+审计
3. 非VDI模型：无其他变更时记录统一成功审计并返回（仅终端日志配置生效）
4. VDI模型：editClearInvalidCloudDesktop（对比后 updateParameter）+ editStartStrategy（更新启动策略参数 + updateRccpAffinityRule 遍历规则逐镜像逐平台 editDeskGroupAffinityRule，负载均衡时gatherRatio=1）+ editRecoverableImagePublishStrategy
5. 四个维度均无变化 → 统一记录 RCDC_RCC_EDIT_GLOBAL_STRATEGY_SUCCESS 审计
6. 返回 success(RCDC_RCC_MODULE_OPERATE_SUCCESS)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | expireCleanDay | @Range(1-200) | webmvc 参数校验异常 |
| request | gatherRatio | @Range(1-1000) | webmvc 参数校验异常 |
| request | startStrategyType/enableClear/enableRecoverableImagePublishUpdate | @NotNull 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| expireCleanDay | user_input/from_query | 按业务构造 |
| enableClear | user_input/from_query | 按业务构造 |
| interval | user_input/from_query | 按业务构造 |
| startStrategyType | user_input/from_query | 按业务构造 |
| enableRecoverableImagePublishUpdate | user_input/from_query | 按业务构造 |
| gatherRatio | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| VDI模型且存在变化 | $.status==SUCCESS |
| 非VDI模型 | $.status==SUCCESS |
| 无任何变化 | $.status==SUCCESS |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 亲和规则更新异常 | 某平台更新失败 | $.status==SUCCESS（亲和规则更新异常仅记录日志，接口仍成功） |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 每次提交都会重新遍历全部亲和性规则并逐平台更新（值相同也执行更新动作），参数本身有值对比；无事务回滚保护 |
