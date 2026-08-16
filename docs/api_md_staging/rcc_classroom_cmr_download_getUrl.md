---
version: '2.0'
api:
  url: /rcc/classroom/cmr/download/getUrl
  method: POST
  name: 根据rpmName向updater服务请求CMR客户端bt安装包与exe安装包的下载地址及校验值，返回给CMR客户端进行下载
  controller: CmrDownloadController
  method_ref: getDownloadUrl
  permission: 无
  exec_mode: sync
  async: false
  description: 根据rpmName向updater服务请求CMR客户端bt安装包与exe安装包的下载地址及校验值，返回给CMR客户端进行下载
setup:
- name: up_1
  api: https://{cluster_virtual_ip}:9274/api (Index/Download/getBtU
  method: POST
  produces: UpdaterResponse.data{url,checkSum}
- name: up_2
  api: https://{cluster_virtual_ip}:9274/api (Index/Download/getIns
  method: POST
  produces: UpdaterResponse.data{url,checkSum}
- name: up_3
  api: 内部调用:globalParameterAPI
  method: POST
  produces: String
  purpose: （内部调用）
request:
  dto: CmrDownloadRequest
  body:
    rpmName:
      type: String
      required: true
      constraint: '@NotNull，rpm包名'
      description: 要查询下载地址的rpm包名称
      value: ${param.rpm_name}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    btUrl:
      type: String
      description: bt格式安装包下载地址
    btCheckSum:
      type: String
      description: bt文件校验值
    exeUrl:
      type: String
      description: 客户端exe文件下载地址
    exeCheckSum:
      type: String
      description: 客户端exe文件校验值
upstream:
- api: https://{cluster_virtual_ip}:9274/api (Index/Download/getBtUrl)
  produces: UpdaterResponse.data{url,checkSum}
  purpose: 获取bt下载地址与校验值
- api: https://{cluster_virtual_ip}:9274/api (Index/Download/getInstallUrl)
  produces: UpdaterResponse.data{url,checkSum}
  purpose: 获取exe下载地址与校验值
- api: 内部调用:globalParameterAPI
  purpose: 获取集群虚拟IP作为updater地址
downstream:
- api: https://{cluster_virtual_ip}:9274/api
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: rpmName
  rule: 必填非空
  failure: 参数校验失败
assertions:
  success:
  - scenario: updater正常返回bt和exe数据
    expect: $.status=="SUCCESS"；$.content.btUrl 非空；$.content.exeUrl 非空
  failure:
  - scenario: updater返回空或异常
    trigger: updater接口不可用或data为空
    expect: $.status=="SUCCESS"（content 字段为 null，接口仍返回成功）
cleanup: []
idempotency:
  level: fully_idempotent
  note: 纯查询，重复调用无副作用
params:
  required:
  - name: rpm_name
---
# POST /rcc/classroom/cmr/download/getUrl

> 根据rpmName向updater服务请求CMR客户端bt安装包与exe安装包的下载地址及校验值，返回给CMR客户端进行下载 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmr/download/getUrl<br>根据rpmName向updater服务请求CMR客户端bt安装包与exe安装包的<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(cmrDownloadRequest) 校验入参非"]
        C2["Step2: 读取全局参数 cluster_virtual_ip，拼接 https://{ip"]
        C3["Step3: 构造 UpdaterRequest{system.uri=Index/Downl"]
        C4["Step4: 构造 UpdaterRequest{system.uri=Index/Downl"]
        C5["Step5: 将updater返回的url与checkSum封装为CmrDownloadDTO"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
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
| URL | /rcc/classroom/cmr/download/getUrl |
| Controller | CmrDownloadController |
| 方法名 | getDownloadUrl |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 根据rpmName向updater服务请求CMR客户端bt安装包与exe安装包的下载地址及校验值，返回给CMR客户端进行下载 |

## 入参详情

### CmrDownloadRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| rpmName | String | 是 | @NotNull，rpm包名 | 要查询下载地址的rpm包名称 |

## 出参详情

| 返回类型 | DefaultWebResponse<CmrDownloadDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| btUrl | String | bt格式安装包下载地址 |
| btCheckSum | String | bt文件校验值 |
| exeUrl | String | 客户端exe文件下载地址 |
| exeCheckSum | String | 客户端exe文件校验值 |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(cmrDownloadRequest) 校验入参非空
2. 读取全局参数 cluster_virtual_ip，拼接 https://{ip}:9274/api 作为updater基础URL
3. 构造 UpdaterRequest{system.uri=Index/Download/getBtUrl, params=rpmName}，POST 请求updater获取bt下载地址
4. 构造 UpdaterRequest{system.uri=Index/Download/getInstallUrl, params=rpmName}，POST 请求updater获取exe下载地址
5. 将updater返回的url与checkSum封装为CmrDownloadDTO返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | rpmName | 必填非空 | 参数校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| rpmName | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| updater正常返回bt和exe数据 | $.status=="SUCCESS"；$.content.btUrl 非空；$.content.exeUrl 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| updater返回空或异常 | updater接口不可用或data为空 | $.status=="SUCCESS"（content 字段为 null，接口仍返回成功） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | readonly |
| 说明 | 纯查询，重复调用无副作用 |
