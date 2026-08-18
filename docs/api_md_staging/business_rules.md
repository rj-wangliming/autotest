---
version: '1.0'
# ============================================================
# 业务规则库（跨接口通用规则，编排器加载后全用例生效）
# 用途：资源依赖链(造数顺序)、操作前置状态、用例前置状态达成途径
#       资源缺失自动创建（幂等复用）、强制新建（先删后建）
# 编排器 orchestrator.validate_plan() 读取本文件的 front-matter
# ============================================================

# ============================================================
# 自动造数规则：查询返回空时的自动处理策略
# ============================================================
auto_provision:
  # 规则 1：幂等复用 — "缺少则创建同名"
  # 当查询步骤返回空时，按 resource_type 从 global_params.yaml 检查同名配置
  # 有则自动调创建接口；无则记录 warn，用例正常执行（后续步骤自然报错）
  # 适用资源：VDI/TCI 课程策略、教室策略（网络/存储池/集群/镜像一定存在，不在此列）
  idempotent_create:
    - resource_type: vdi_strategy
      query_api: POST /space/strategygroup/vdi/list
      create_api: POST /space/strategygroup/vdi/create
      param_key: strategy_name_vdi
      param_required_fields: [name, strategyType, cpu, memory, systemSize, pattern, business, enableInternet, enablePersonalConfig, enableSoftwareDecode, enableShowLocalDisk, platformStrategyGroup]
      note: VDI 课程策略不存在时自动创建（策略名来自 param_key）
    - resource_type: tci_strategy
      query_api: POST /space/strategygroup/tci/list
      create_api: POST /space/strategygroup/tci/create
      param_key: strategy_name_tci
      param_required_fields: [name, strategyType, cpu, memory, systemSize, pattern, business, enableInternet, enablePersonalConfig, platformStrategyGroup]
      note: TCI 课程策略不存在时自动创建（策略名来自 param_key）
    - resource_type: classroom_strategy
      query_api: POST /rcc/classroom/strategy/list
      create_api: POST /rcc/classroom/strategy/create
      param_key: classroom_strategy_name
      param_required_fields: [classroomStrategyName, linkShutdown, startPolicy, defaultEnterImageSwitch, defaultDisplayDeskType, reservedStoragePolicy]
      note: 教室策略不存在时自动创建（策略名来自 param_key）

  # 规则 2：强制新建 — "先删同名再创建"
  # 当用例声明 idempotent=recreate 且资源类型属于需要清理的类别时
  # 前置先删除同名资源，再创建新资源
  force_create:
    - resource_type: classroom_strategy
      query_api: POST /rcc/classroom/strategy/list
      delete_api: POST /rcc/classroom/strategy/delete
      match_field: classroomStrategyName
      note: 教室策略强制新建：先删同名策略再创建
    - resource_type: vdi_strategy
      query_api: POST /space/strategygroup/vdi/list
      delete_api: POST /space/strategygroup/vdi/delete
      match_field: strategyName
      note: VDI 课程策略强制新建：先删同名策略再创建
    - resource_type: tci_strategy
      query_api: POST /space/strategygroup/tci/list
      delete_api: POST /space/strategygroup/tci/delete
      match_field: strategyName
      note: TCI 课程策略强制新建：先删同名策略再创建

# ============================================================
# 资源依赖链：资源类型 -> 按顺序执行的接口链（造数/数据就绪顺序）
# ============================================================
resource_chains:
  classroom:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
      - POST /space/strategygroup/vdi/create
      - POST /rcc/classroom/image/student/create
      - POST /rcc/classroom/image/teacher/create
    note: 教室 → 座位 → VDI 课程策略（幂等创建）→ 分配学生机/教师机镜像；座位创建后无桌面，分配镜像后桌面才存在
  vdi_desktop:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
      - POST /space/strategygroup/vdi/create
      - POST /rcc/classroom/image/student/create
    note: 学生机 VDI 桌面由「座位 + 镜像分配」生成；desktop/list 查询的数据源即该链产物；镜像分配依赖 VDI 课程策略（不存在时由 create 步骤幂等创建，规则补链兜底）
  tci_desktop:
    order:
      - POST /rcc/classroom/create
      - POST /spacetci/lessonImage/student/create
      - POST /spacetci/lessonImage/teacher/create
    note: TCI 桌面由「教室 + 课程镜像分配」生成（无独立座位环节）
  strategy:
    order:
      - POST /rcc/classroom/strategy/create
      - POST /space/strategygroup/vdi/create
      - POST /space/strategy/tci/create
    note: 策略独立创建（请求 DTO 无资源外键依赖）；教室创建与镜像分配依赖策略
  seat:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
    note: 座位创建依赖教室+集群+网络+平台（BatchCreateSeatWebRequest 外键推导）
  lesson_image:
    order:
      - POST /rcc/classroom/create
      - POST /space/strategygroup/vdi/create
      - POST /spacetci/lessonImage/student/create
    note: 学生机课程镜像分配依赖教室+策略+镜像模板+集群+网络+存储池+平台（请求 DTO 外键推导）
  classroom_cleanup:
    order:
      - POST /rcc/classroom/lesson/end
      - POST /rcc/classroom/desktop/powerOff
      - POST /rcc/classroom/seat/delete
      - POST /rcc/classroom/delete
    note: >-
      删除教室的清理链：下课 → 桌面关机 → 删除座位 → 删除教室
      （desktop/delete 接口当前环境不存在（404），删除教室时座位随教室级联清理）。
      每步均为异步批任务，必须轮询等待完成后再进行下一步：
      下课 taskId 轮询成功后还须等待所有桌面进入 CLOSE 关闭态；
      seat/delete、desktop/powerOff、desktop/delete 返回 taskId 须等待完成，
      否则「座位还在删除中/桌面未关机」时删除教室会失败。
    source: 业务语义（删除教室前提：先下课且所有桌面关机；executor finally 清理按本链执行）

# 操作前置状态：资源+动作 模式 -> 目标状态 + 达成途径
# （模式匹配：URL 同时含 resource 段与 action 段即命中，覆盖所有域的同类操作，无需逐接口列举）
state_prereq:
  - resource: desktop
    action: restart
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: shutdown
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: poweroff
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: forcewakeup
    required_state: SLEEP
    resource_optional: true
    source: 源码推导（RccSpaceDesktopForceWakeUpBatchTaskHandler 校验 deskState==SLEEP，STATE_NOT_SATISFIED，classroom 与 space 两域同校验）
    achieve_via: []
    note: 唤醒仅对睡眠(SLEEP)状态桌面生效；非睡眠桌面唤醒直接失败，无补步骤途径
  - resource: desktop
    action: restore
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: start
    required_state: CLOSE
    source: 源码推导（StartDesktopSPIImpl 校验桌面 CLOSE 状态）
    achieve_via: []
    note: 开机要求桌面处于关机(CLOSE)状态
  - resource: classroom
    action: lesson_start
    required_state: NONE_CLASS
    chain: false
    forbidden: [STARTING_CLASS, IN_CLASS]
    source: 源码推导（LessonService：STARTING_CLASS 重复上课禁止；IN_CLASS 同镜像禁止；IN_CLASS 不同镜像先下课再上课）
    achieve_via: []
    note: 上课要求教室非上课中；若 IN_CLASS 不同镜像需先下课
  - resource: classroom
    action: lesson_end
    required_state: IN_CLASS
    chain: false
    source: 源码语义（下课需上课中）
    achieve_via: []
    note: 下课要求教室处于上课中(IN_CLASS)
  - resource: strategy
    action: edit
    required_state: AVAILABLE
    source: 源码推导（SpaceStrategyGroupVDIValidationUtil 校验 state==AVAILABLE）
    achieve_via: []
    note: 策略编辑要求策略可用(AVAILABLE)
  - resource: strategy
    action: delete
    required_state: AVAILABLE
    source: 源码推导（删除流程先置 DELETING，操作要求 AVAILABLE）
    achieve_via: []
    note: 策略删除要求策略可用(AVAILABLE)
  - resource: classroom
    action: delete
    api: /rcc/classroom/delete
    required_state: NONE_CLASS
    forbidden: [STARTING_CLASS, IN_CLASS, ENDING_CLASS]
    source: 源码推导（ClassroomServiceImpl.checkClassroomCanDelete：非上课中才可删除；NONE_CLASS/ERROR 允许，上课状态禁止）
    chain: false
    achieve_via:
      - api: POST /rcc/classroom/lesson/end
        note: 教室上课中需先下课(lesson/end)才能删除
  - resource: teacher
    action: start
    required_state: CLOSE
    source: 业务语义（教师桌面启动类似桌面开机，要求关机状态；开机途径与桌面一致）
    achieve_via: []
    note: 教师桌面启动要求桌面处于关机(CLOSE)状态
  - resource: teacher
    action: end
    required_state: RUNNING
    source: 业务语义（关闭教师桌面要求桌面运行中）
    achieve_via: []
    note: 教师桌面关闭要求桌面运行中(RUNNING)
  - resource: terminal
    action: unlock
    required_state: ONLINE
    source: 源码推导（UnlockTerminalBatchTaskHandler 校验终端 OFFLINE 禁止，TERMINAL_UNLOCK_TERMINAL_OFFLINE）
    chain: false
    achieve_via: []
    note: 终端解锁要求终端在线(ONLINE)；离线终端操作直接失败，无接口可达成上线
  - resource: terminal
    action: shutdown
    required_state: ONLINE
    source: 业务语义（终端关机/重启/唤醒要求终端在线，参照解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线
  - resource: terminal
    action: wake
    required_state: ONLINE
    source: 业务语义（参照终端解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线
  - resource: terminal
    action: restart
    required_state: ONLINE
    source: 业务语义（参照终端解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线

# 语义匹配修正规则：_semantic_match 基础打分（动作+2/实体+2）后叠加 delta
# 字段：if_entities=用例句须命中的实体词（URL 段）；url_any/name_any=接口 URL/名称含任一词才命中；
#       name_none=名称含任一词则排除（例外条件）；delta=命中加减分
# 新增反规则只需在此追加条目，无需修改编排器代码
semantic_rules:
  - if_entities: [cluster]
    name_any: [存储池, StoragePool, storagePool]
    delta: -10
    note: 集群语义不匹配存储池接口（语义冲突重罚）
  - if_entities: [storagePool]
    name_any: [集群, Cluster, cluster]
    delta: -10
    note: 存储池语义不匹配集群接口（语义冲突重罚）
  - if_entities: [network]
    name_any: [镜像, Image, image]
    name_none: [Assigned]
    delta: -10
    note: 网络语义不匹配镜像接口（getAssignedClusterAndNetwork 例外）
  - url_any: [/dashboard/statistics/]
    delta: -10
    note: 统计接口不是业务查询
  - if_entities: [cluster]
    url_any: [/rco/user/obtainComputeClusterList]
    delta: 5
    note: 集群优先 RDCD 侧接口（不穿透 CBB，更稳定）
  - if_entities: [cluster]
    url_any: [/space/cluster/]
    delta: -3
    note: Space 侧集群接口穿透 CBB，降权
  - if_entities: [storagePool]
    url_any: [/rcc/]
    delta: 3
    note: 存储池优先 RCC 侧接口
  - if_entities: [storagePool]
    url_any: [/space/storagePool/]
    delta: -3
    note: Space 侧存储池接口穿透 CBB，降权

# 用例前置条件：前置步骤关键词 -> 需满足的资源状态 + 达成途径
# （校验用例前置声明是否被编排步骤覆盖，不满足时自动补达成步骤）
case_prereq:
  - keyword: 运行中
    resource: desktop
    required_state: RUNNING
    achieve_via:
      - api: POST /rcc/classroom/lesson/start
        note: 前置要求桌面运行中；若已分配镜像但处于关机，先上课开机
  - keyword: 已分配
    resource: desktop
    required_state: ASSIGNED
    achieve_via:
      - api: POST /rcc/classroom/image/student/create
        note: 前置要求已分配镜像；若只有教室/座位而无镜像，先分配学生机镜像

# ============================================================
# 编排参数引用规则：跨步骤参数继承
# ============================================================
# 编排期参数继承：当某个步骤需要依赖其他步骤的输入或全局参数时，
# 必须从已存在的 param 或前序步骤产出中获取，禁止编造不存在的 param
param_ref_rules:
  - name: cloud_desk_type_from_student_mode
    description: cloudDeskType/desktopType 等云桌面类型字段应等于 studentModeArr（如 VDI），从 param.student_mode_arr 取值
    source_param: student_mode_arr
    target_interfaces:
      - /space/deskStrategy/getSupportUsbType  # cloudDeskType：查询 USB 设备类型
      - /rcc/classroom/desktop/list            # desktopType：查询桌面列表过滤
      - /rcc/classroom/desktop/tci/list        # desktopType：查询 TCI 桌面列表过滤
    target_fields:
      - cloudDeskType  # 云桌面类型枚举，决定查询范围
      - desktopType    # 云桌面类型枚举，桌面查询过滤
    note: 云桌面类型与创建教室的 studentModeArr 同义；若 param 中有 student_mode_arr，cloudDeskType/desktopType = student_mode_arr[0]
  - name: desktop_id_list_from_running_query
    description: desktop/restart 等桌面批量操作 idArr 应引用运行中桌面查询（query_running_vdi_desktops）的 desktopIdList，禁止用不存在的 param.id_arr（用例参数未提供会致 body 清空）
    source_prev: query_running_vdi_desktops.output.desktopIdList
    target_interfaces:
      - /rcc/classroom/desktop/restart  # 批量重启选中的 VDI 桌面
    target_fields:
      - idArr
    note: 桌面操作对象来自「前置条件：获取运行中的VDI云桌面」查询产出的 desktopIdList；param 中不存在 id_arr
---
# 业务规则库（Business Rules）

本文件是**跨接口通用业务规则**的集中定义，供编排器（`orchestrator.validate_plan`）加载，用于：
1. **依赖顺序校验**：操作/查询某资源前，其资源依赖链（`resource_chains`）中的前置接口必须先执行
2. **前置状态校验**：操作接口（`state_prereq`）要求目标资源处于特定状态（如桌面 RUNNING），不满足时按 `achieve_via` 自动补步骤
3. **用例前置覆盖校验**：用例前置条件（`case_prereq`）声明的状态必须被编排步骤达成，否则自动补

## 通用规则要点

### 资源依赖链（造数顺序）
- **教室 → 座位(batchCreate) → 分配镜像(image/student|teacher/create) → 桌面可用**
- 座位本身**不含桌面**，桌面由「座位 + 镜像分配」生成——`desktop/list` 的查询结果依赖该链完成
- TCI 桌面由「教室 + 课程镜像分配」生成（无座位环节）

### 桌面生命周期状态机
```
教室创建 → 座位创建 → 分配镜像 → 桌面存在(关机 OFF)
                                    ↓ 上课(lesson/start)
                                 桌面运行中(RUNNING) → 重启/关机/唤醒/取消报障
```
- 学生桌面**无独立开机接口**，只能通过上课（`lesson/start`）批量开机
- 教师桌面可经 `teacher/terminal/wake` 唤醒

### 操作前置状态
| 操作 | 前置状态 | 达成途径 |
|---|---|---|
| desktop/restart、shutdown、powerOff、forceWakeUp、restoreVDIImage | 桌面 RUNNING | 上课 lesson/start |
| desktop/tci/restart、tci/shutdown | 桌面 RUNNING | 上课 lesson/start |

### 维护约定
- 新增资源类型/操作前置状态时，在 front-matter 对应节追加即可，**无需修改编排器代码**
- 编排器自动补的步骤会标记 `_auto_by_rules: true`，可在编排计划中人工确认
