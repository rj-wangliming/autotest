---
version: '2.0'
api:
  url: /rcc/classroom/image/list
  method: POST
  name: 分页获取课程镜像列表（镜像卡片），VDI 类型镜像额外填充 GPU 选项列表
  controller: RccClassroomImageController
  method_ref: getClassroomImage
  permission: 无
  exec_mode: sync
  async: false
  description: 分页获取课程镜像列表（镜像卡片），VDI 类型镜像额外填充 GPU 选项列表
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
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  request:
    body:
      searchKeyword: ${param.classroom_name}
request:
  dto: GetClassroomImagePageWebRequest
  body:
    crId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 操作的教室ID
      value: ${param.cr_id}
    teaTerminal:
      type: Boolean
      required: false
      constraint: 默认 false
      description: 学生机或教师机
    imageTypeList:
      type: List<CbbImageType>
      required: false
      constraint: 可空
      description: 镜像类型过滤（VDI/TCI等）
    page:
      type: Integer
      required: false
      description: 分页、排序与筛选参数（page）
    limit:
      type: Integer
      required: false
      description: 分页、排序与筛选参数（limit）
    sortArr:
      type: Object
      required: false
      description: 分页、排序与筛选参数（sortArr）
    matchArr:
      type: Object
      required: false
      description: 分页、排序与筛选参数（matchArr）
    searchKeyword:
      type: String
      required: false
      description: 分页、排序与筛选参数（searchKeyword）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ClassroomImageCardInfoDTO[]
      description: 镜像卡片列表（位于 content 下：$.content.itemArr），元素含 id/imageName/teaImage/hide/canUpdate/cbbImageType
    total:
      type: Integer
      description: 总条数
    "itemArr[]_id":
      type: UUID
      description: 镜像ID
    "itemArr[]_imageName":
      type: String
      description: 镜像名称
    "itemArr[]_teaImage":
      type: Boolean
      description: 是否教师机镜像
    "itemArr[]_hide":
      type: Boolean
      description: 是否隐藏
    "itemArr[]_canUpdate":
      type: Boolean
      description: 是否能更新
    "itemArr[]_usage":
      type: String
      description: 用途
    "itemArr[]_classroomState":
      type: ClassroomLessonStatusEnum
      description: 当前教室状态
    "itemArr[]_beingUsedInLesson":
      type: Boolean
      description: 当前教室正使用该镜像且处于上课准备/上课中/下课准备中
    "itemArr[]_cbbImageType":
      type: CbbImageType
      description: 镜像类型（VDI/IDV/VOI）
    "itemArr[]_rootImageId":
      type: UUID
      description: 根镜像ID
    "itemArr[]_rootImageName":
      type: String
      description: 根镜像名称
    "itemArr[]_imageRoleType":
      type: ImageRoleType
      description: 镜像角色类型
    "itemArr[]_enableMultipleVersion":
      type: Boolean
      description: 是否开启多版本
    "itemArr[]_cpu":
      type: Integer
      description: CPU核数
    "itemArr[]_editErrorMessageArr":
      type: String[]
      description: 驱动未更新等错误提示
    "itemArr[]_imageSystemSize":
      type: Integer
      description: 系统盘大小（GB）
    "itemArr[]_memory":
      type: Double
      description: 内存大小（GB）
    "itemArr[]_osType":
      type: CbbOsType
      description: 操作系统类型
    "itemArr[]_supportGoldenImage":
      type: Boolean
      description: 是否黄金镜像
    "itemArr[]_downloadInfo":
      type: String
      description: 镜像下载总览
    "itemArr[]_bindDefaultEnter":
      type: Boolean
      description: 是否默认进入的镜像
    "itemArr[]_cbbCloudDeskPattern":
      type: CbbCloudDeskPattern
      description: 桌面模式
    "itemArr[]_imageTemplateState":
      type: ImageTemplateState
      description: 镜像模板状态
    "itemArr[]_classroomId":
      type: UUID
      description: 教室ID
    "itemArr[]_createTime":
      type: Date
      description: 创建时间
    "itemArr[]_imageDiskList":
      type: List<CbbImageDiskInfoDTO>
      description: 镜像磁盘信息列表
    "itemArr[]_dataDiskSize":
      type: Integer
      description: 数据盘大小
    "itemArr[]_enableGpu":
      type: Boolean
      description: 是否启用GPU
    "itemArr[]_vgpuType":
      type: VgpuType
      description: vGPU类型
    "itemArr[]_graphicsMemorySize":
      type: String
      description: 显存大小
    "itemArr[]_vgpuItem":
      type: String
      description: vGPU规格项
    "itemArr[]_vgpuModel":
      type: String
      description: vGPU型号
    "itemArr[]_classroomImageId":
      type: UUID
      description: 教室镜像ID
    "itemArr[]_gpuOptionList":
      type: List<VgpuDTO>
      description: GPU规格列表（仅VDI填充）
    "itemArr[]_clusterId":
      type: UUID
      description: 计算集群ID
    "itemArr[]_platformId":
      type: UUID
      description: 平台ID
    "itemArr[]_clusterName":
      type: String
      description: 计算集群名称
    "itemArr[]_strategyId":
      type: UUID
      description: 云桌面策略ID
    "itemArr[]_strategyName":
      type: String
      description: 云桌面策略名称
    "itemArr[]_networkId":
      type: UUID
      description: 网络策略ID
    "itemArr[]_networkName":
      type: String
      description: 网络策略名称
    "itemArr[]_storagePoolIds":
      type: String
      description: 存储池ID集合
    "itemArr[]_spaceImage":
      type: Boolean
      description: 是否在教学实训桌面池发布
    "itemArr[]_teacherDesktopState":
      type: CbbCloudDeskState
      description: 教师机桌面状态
    "itemArr[]_platformType":
      type: CloudPlatformType
      description: 云平台类型（继承 RccPlatformBaseInfoDTO）
    "itemArr[]_platformName":
      type: String
      description: 云平台名称（继承 RccPlatformBaseInfoDTO）
    "itemArr[]_platformStatus":
      type: CloudPlatformStatus
      description: 云平台状态（继承 RccPlatformBaseInfoDTO）
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: POST /rcc/classroom/image/getInfo|getInfoStoragePoolList|getStrategy|{student,teacher}/delete|hide|show|update
  purpose: 出参 ClassroomImageCardInfoDTO.id=课程镜像ID（镜像模板ID），是大量下游消费的主键
- api: POST /rcc/classroom/image/*
  purpose: 卡片自带 classroomId 回显
constraints:
- level: PARAM
  field: crId
  rule: '@NotNull'
  failure: 参数缺失校验失败
assertions:
  success:
  - scenario: 教室存在
    expect: $.status==SUCCESS && $.content.itemArr 非空（PageQueryResponse 分页框架字段为 itemArr/total）
  - scenario: 包含VDI镜像
    expect: $.status==SUCCESS && $.content.itemArr 中 VDI 卡片含 gpuOptionList 非空
  failure:
  - scenario: crId 缺失
    trigger: 请求体无 crId
    expect: $.status==ERROR（参数校验，无固定 msgKey）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
params:
  required:
  - name: classroom_name
  - name: cr_id
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/image/list

> 分页获取课程镜像列表（镜像卡片），VDI 类型镜像额外填充 GPU 选项列表 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/image/list<br>分页获取课程镜像列表（镜像卡片），VDI 类型镜像额外填充 GPU 选项列表<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 webRequest 与 sessionCo"]
        C2["Step2: BeanUtils.copyProperties 转换为 GetClassroo"]
        C3["Step3: userId = sessionContext.getUserId()"]
        C4["Step4: 调用 classroomImageAPI.getClassroomImageCa"]
        C5["Step5: 调用 setGpuOptionList：若 gpuOptionList 非空且卡"]
        C6["Step6: return success(pageQueryResponse)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/image/getInfo|getInfoStoragePoolList|getStrategy|{student,teacher}/delete|hide|show|update"]
        D2["POST /rcc/classroom/image/*"]
    end
    B -->|数据| D1
    B -->|数据| D2
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/image/list |
| Controller | RccClassroomImageController |
| 方法名 | getClassroomImage |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 分页获取课程镜像列表（镜像卡片），VDI 类型镜像额外填充 GPU 选项列表 |

## 入参详情

### GetClassroomImagePageWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| crId | UUID | 是 | @NotNull 非空 | 操作的教室ID |
| teaTerminal | Boolean | 否 | 默认 false | 学生机或教师机 |
| imageTypeList | List<CbbImageType> | 否 | 可空 | 镜像类型过滤（VDI/TCI等） |
| limit | Integer | 否 |  | 分页、排序与筛选参数（limit） |
| matchArr | Object | 否 |  | 分页、排序与筛选参数（matchArr） |
| searchKeyword | String | 否 |  | 分页、排序与筛选参数（searchKeyword） |
| sortArr | Object | 否 |  | 分页、排序与筛选参数（sortArr） |
| page | Integer | 否 |  | 分页、排序与筛选参数（page） |
## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<ClassroomImageCardInfoDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ClassroomImageCardInfoDTO[] | 镜像卡片列表（元素字段见下） |
| total | Integer | 总条数 |
| id | UUID | 镜像ID |
| imageName | String | 镜像名称 |
| teaImage | Boolean | 是否教师机镜像 |
| hide | Boolean | 是否隐藏 |
| canUpdate | Boolean | 是否能更新 |
| usage | String | 用途 |
| classroomState | ClassroomLessonStatusEnum | 当前教室状态 |
| beingUsedInLesson | Boolean | 当前教室正使用该镜像且处于上课准备/上课中/下课准备中 |
| cbbImageType | CbbImageType | 镜像类型（VDI/IDV/VOI） |
| rootImageId | UUID | 根镜像ID |
| rootImageName | String | 根镜像名称 |
| imageRoleType | ImageRoleType | 镜像角色类型 |
| enableMultipleVersion | Boolean | 是否开启多版本 |
| cpu | Integer | CPU核数 |
| editErrorMessageArr | String[] | 驱动未更新等错误提示 |
| imageSystemSize | Integer | 系统盘大小（GB） |
| memory | Double | 内存大小（GB） |
| osType | CbbOsType | 操作系统类型 |
| supportGoldenImage | Boolean | 是否黄金镜像 |
| downloadInfo | String | 镜像下载总览 |
| bindDefaultEnter | Boolean | 是否默认进入的镜像 |
| cbbCloudDeskPattern | CbbCloudDeskPattern | 桌面模式 |
| imageTemplateState | ImageTemplateState | 镜像模板状态 |
| classroomId | UUID | 教室ID |
| createTime | Date | 创建时间 |
| imageDiskList | List<CbbImageDiskInfoDTO> | 镜像磁盘信息列表 |
| dataDiskSize | Integer | 数据盘大小 |
| enableGpu | Boolean | 是否启用GPU |
| vgpuType | VgpuType | vGPU类型 |
| graphicsMemorySize | String | 显存大小 |
| vgpuItem | String | vGPU规格项 |
| vgpuModel | String | vGPU型号 |
| classroomImageId | UUID | 教室镜像ID |
| gpuOptionList | List<VgpuDTO> | GPU规格列表（仅VDI填充） |
| clusterId | UUID | 计算集群ID |
| platformId | UUID | 平台ID |
| clusterName | String | 计算集群名称 |
| strategyId | UUID | 云桌面策略ID |
| strategyName | String | 云桌面策略名称 |
| networkId | UUID | 网络策略ID |
| networkName | String | 网络策略名称 |
| storagePoolIds | String | 存储池ID集合 |
| spaceImage | Boolean | 是否在教学实训桌面池发布 |
| teacherDesktopState | CbbCloudDeskState | 教师机桌面状态 |
| platformType | CloudPlatformType | 云平台类型（继承 RccPlatformBaseInfoDTO） |
| platformName | String | 云平台名称（继承 RccPlatformBaseInfoDTO） |
| platformStatus | CloudPlatformStatus | 云平台状态（继承 RccPlatformBaseInfoDTO） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 webRequest 与 sessionContext
2. BeanUtils.copyProperties 转换为 GetClassroomImageRequest
3. userId = sessionContext.getUserId()
4. 调用 classroomImageAPI.getClassroomImageCardPageByCrIdAndTeaTerminal(request, userId) 分页查询
5. 调用 setGpuOptionList：若 gpuOptionList 非空且卡片为 CbbImageType.VDI 则 setGpuOptionDeepCopyList
6. return success(pageQueryResponse)

## 下游消费方

### 消费1：POST /rcc/classroom/image/getInfo|getInfoStoragePoolList|getStrategy|{student,teacher}/delete|hide|show|update

出参 ClassroomImageCardInfoDTO.id=课程镜像ID（镜像模板ID），是大量下游消费的主键（由 field_map 契约映射）

### 消费2：POST /rcc/classroom/image/*

卡片自带 classroomId 回显（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | crId | @NotNull | 参数缺失校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| crId | user_input/from_query | 按业务构造 |
| teaTerminal | user_input/from_query | 按业务构造 |
| imageTypeList | user_input/from_query | 按业务构造 |
| page/limit/sortArr/matchArr/searchKeyword | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室存在 | $.status==SUCCESS && $.content.itemArr 非空（PageQueryResponse 分页框架字段为 itemArr/total） |
| 包含VDI镜像 | $.status==SUCCESS && $.content.itemArr 中 VDI 卡片含 gpuOptionList 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| crId 缺失 | 请求体无 crId | $.status==ERROR（参数校验，无固定 msgKey） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口 |
