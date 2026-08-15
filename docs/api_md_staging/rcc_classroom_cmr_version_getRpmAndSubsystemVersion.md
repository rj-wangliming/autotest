---
version: '2.0'
api:
  url: /rcc/classroom/cmr/version/getRpmAndSubsystemVersion
  method: POST
  name: 获取指定子系统的服务端版本信息，并可选对比rpm组件版本与客户端当前版本的差异
  controller: CmrVersionController
  method_ref: getRpmAndSubsystemVersion
  permission: 无
  exec_mode: sync
  async: false
  description: 获取指定子系统的服务端版本信息，并可选对比rpm组件版本与客户端当前版本的差异
setup:
- name: up_1
  api: 内部调用:configCenterKvAPI
  method: POST
  produces: PackageVersionDTO
  purpose: （内部调用）
- name: up_2
  api: file:///config/packet/{rpmName}.ini
  method: POST
  produces: Properties[version]
request:
  dto: CmrVersionRequest
  body:
    rpmName:
      type: String
      required: false
      constraint: '@Nullable，rpm包名'
      description: 可选，传入时额外返回rpm最新版本及对比结果
    curRpmVersion:
      type: String
      required: false
      constraint: '@Nullable，客户端当前版本'
      description: 客户端当前rpm版本，用于对比
    subSystem:
      type: String
      required: true
      constraint: '@NotNull，子系统标识'
      description: 子系统名称，用于定位version.json文件
      value: ${param.sub_system}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    latestRpmVersion:
      type: String
      description: 服务端最新rpm版本
    fullRpmVersion:
      type: String
      description: 服务端rpm完整版本号
    subSystemVersion:
      type: String
      description: 子系统版本
    subSystemInnerVersion:
      type: String
      description: 子系统内部版本
    rpmCompareResult:
      type: Integer
      description: rpm版本对比结果（>0服务端新，<0客户端新，0相同）
upstream:
- api: 内部调用:configCenterKvAPI
  purpose: 读取子系统版本信息文件
- api: file:///config/packet/{rpmName}.ini
  produces: Properties[version]
  purpose: 读取rpm组件最新版本
downstream: []
constraints:
- level: upstream
  field: subSystem
  rule: version.json必须存在且内容完整
  failure: 63100001 SPACE_CMR_VERSION_FILE_NOT_FIND
- level: upstream
  field: componentVersionList
  rule: 依赖组件信息不能为空
  failure: 63100002 SPACE_CMR_VERSION_FILE_NOT_EXIST_COMPONENT_INFO
- level: upstream
  field: rpmName
  rule: 对应.ini文件必须存在
  failure: 63100003 SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT
- level: security
  field: rpmName
  rule: 不能包含..或/，防止路径遍历
  failure: Assert isTrue抛异常
assertions:
  success:
  - scenario: 传入rpmName且curRpmVersion
    expect: $.status=="SUCCESS"；$.content.subSystemVersion 非空；$.content.latestRpmVersion 非空
  - scenario: 不传rpmName
    expect: $.status=="SUCCESS"；$.content.subSystemVersion 非空
  failure:
  - scenario: 配置中心无version.json
    trigger: configCenterKvAPI.get返回空
    expect: status==ERROR；msgKey==63100001（SPACE_CMR_VERSION_FILE_NOT_FIND）
  - scenario: .ini文件不存在
    trigger: rpmName对应文件缺失
    expect: status==ERROR；msgKey==63100003（SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT）
  - scenario: 文件名含路径穿越字符
    trigger: rpmName含../
    expect: status==ERROR（Assert 参数校验失败）
cleanup: []
idempotency:
  level: fully_idempotent
  note: 纯查询接口
---
# POST /rcc/classroom/cmr/version/getRpmAndSubsystemVersion

> 获取指定子系统的服务端版本信息，并可选对比rpm组件版本与客户端当前版本的差异 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmr/version/getRpmAndSubsystemVersion<br>获取指定子系统的服务端版本信息，并可选对比rpm组件版本与客户端当前版本的差异<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(cmrVersionRequest) 校验入参"]
        C2["Step2: 拼接 version.json 路径并通过配置中心读取，解析为PackageVe"]
        C3["Step3: 校验publicVersion/version非空且componentVersi"]
        C4["Step4: 组装CmrVersionDTO（subSystemVersion、subSyst"]
        C5["Step5: 若rpmName为空直接返回；否则读取本地/config/packet/{rpm"]
        C6["Step6: compareVersion(curRpmVersion, latestRpmV"]
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
| URL | /rcc/classroom/cmr/version/getRpmAndSubsystemVersion |
| Controller | CmrVersionController |
| 方法名 | getRpmAndSubsystemVersion |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 获取指定子系统的服务端版本信息，并可选对比rpm组件版本与客户端当前版本的差异 |

## 入参详情

### CmrVersionRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| rpmName | String | 否 | @Nullable，rpm包名 | 可选，传入时额外返回rpm最新版本及对比结果 |
| curRpmVersion | String | 否 | @Nullable，客户端当前版本 | 客户端当前rpm版本，用于对比 |
| subSystem | String | 是 | @NotNull，子系统标识 | 子系统名称，用于定位version.json文件 |

## 出参详情

| 返回类型 | DefaultWebResponse<CmrVersionDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| latestRpmVersion | String | 服务端最新rpm版本 |
| fullRpmVersion | String | 服务端rpm完整版本号 |
| subSystemVersion | String | 子系统版本 |
| subSystemInnerVersion | String | 子系统内部版本 |
| rpmCompareResult | Integer | rpm版本对比结果（>0服务端新，<0客户端新，0相同） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(cmrVersionRequest) 校验入参
2. 拼接 version.json 路径并通过配置中心读取，解析为PackageVersionDTO
3. 校验publicVersion/version非空且componentVersionList非空
4. 组装CmrVersionDTO（subSystemVersion、subSystemInnerVersion）
5. 若rpmName为空直接返回；否则读取本地/config/packet/{rpmName}.ini获取组件版本
6. compareVersion(curRpmVersion, latestRpmVersion) 计算版本对比结果并返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| upstream | subSystem | version.json必须存在且内容完整 | 63100001 SPACE_CMR_VERSION_FILE_NOT_FIND |
| upstream | componentVersionList | 依赖组件信息不能为空 | 63100002 SPACE_CMR_VERSION_FILE_NOT_EXIST_COMPONENT_INFO |
| upstream | rpmName | 对应.ini文件必须存在 | 63100003 SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT |
| security | rpmName | 不能包含..或/，防止路径遍历 | Assert isTrue抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| rpmName | user_input/from_query | 按业务构造 |
| curRpmVersion | user_input/from_query | 按业务构造 |
| subSystem | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入rpmName且curRpmVersion | $.status=="SUCCESS"；$.content.subSystemVersion 非空；$.content.latestRpmVersion 非空 |
| 不传rpmName | $.status=="SUCCESS"；$.content.subSystemVersion 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 配置中心无version.json | configCenterKvAPI.get返回空 | status==ERROR；msgKey==63100001（SPACE_CMR_VERSION_FILE_NOT_FIND） |
| .ini文件不存在 | rpmName对应文件缺失 | status==ERROR；msgKey==63100003（SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT） |
| 文件名含路径穿越字符 | rpmName含../ | status==ERROR（Assert 参数校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | readonly |
| 说明 | 纯查询接口 |
