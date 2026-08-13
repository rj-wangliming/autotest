# 用例参数集说明（自动测试输入）

> 对应用例：VDI教师机镜像列表中，选择课程镜像进行变更课程云桌面策略
> 参数以 python 变量 / json / yaml 格式提供，接口文档 setup 用 `${param.xxx}` 引用。

## 用例所需参数

| 参数 | 示例值 | 用途 | 被哪些接口引用 |
|---|---|---|---|
| `test_name` | `test_047` | 用例标识（前缀） | 组合生成各名称 |
| `classroom_name` | `test_047` | 教室名称 | create/select/terminal/list |
| `student_image_name` | `TEST_WIN10_64_VDI_P` | 课程镜像名（**已存在**，不创建） | image/assignImage 列表、teacher/create |
| `strategy_name` | `test_047_strategy` | VDI 课程云桌面策略名（**待创建**） | strategygroup/vdi/create、vdi/list、teacher/create、teacher/strategy/edit |
| `class_strategy_name` | `test_047_class_strategy` | 教室策略名（可选，前置） | classroom/strategy/list |
| `target_network_name` | `172` | 网络名（可选，镜像网络） | image/list 网络过滤 |
| `cluster_name` | （环境既有集群名） | 计算节点集群名 | cluster/obtainComputeClusterList（执行接口取 clusterId/platformId） |
| `initial_strategy_name` | 默认 VDI 策略名 | 镜像A**初始关联**策略（分配时用，可=默认策略，**必须与 strategy_name 不同**才能验证变更） | teacher/create 的 get_strategy |

## 用例 → 接口映射（数据流）

```
参数: classroom_name, student_image_name, strategy_name, cluster_name

前置1: POST /rcc/classroom/create        classroomName=${param.classroom_name} → 轮询
前置1b: POST /rcc/classroom/select       searchKeyword=${param.classroom_name} → classroomId
前置2: POST /rcc/classroom/image/teacher/create
         crId=${classroomId}, plusImageId=${镜像A id}, strategyId=${初始VDI策略 id}
         → 分配镜像A到教师终端（异步轮询）
前置3: POST /space/strategygroup/vdi/create  name=${param.strategy_name}（cpu/memory/systemSize 与镜像A不同）→ deskStrategyId
执行:  POST /rcc/classroom/image/teacher/strategy/edit
         imageId=${镜像A id}, deskStrategyId=${策略B id}, classroomId, clusterId, platformId
验证:  POST /rcc/space/classroom/cloudDesktop/list  classroomId → 断言 cpu/memory/systemSize == 策略B

预测结果断言:
  1) 变更成功: $.status==SUCCESS（teacher/strategy/edit）
  2) 配置一致: cloudDesktop/list 的 $.content.itemArr[0].cpu/memory/systemSize == 策略B 配置
```

## 注意

- `student_image_name` 是**已存在镜像**（用例不创建，直接用名称查 ID）
- `strategy_name` 是**用例创建**（前置3），创建时指定与镜像A不同的 cpu/memory/systemSize（保证变更可验证）
- `cluster_name` 依赖测试环境既有集群（若为空，执行接口 get_cluster 用"取第一条"）
- 镜像A初始策略：`initial_strategy_name`（**≠ strategy_name**）——前置2 分配时关联，执行时改为 strategy_name，保证预测结果2可验证（变更前配置≠变更后）
