# TCI 课程策略（space/strategy/tci）错误码对照表

> 来源：Java 工程 `TCILessonStrategyErrorCode.java`（space-tci-module-def）+ 校验实现 `SpaceStrategyGroupTCIValidationUtil.java` / `SpaceStrategyGroupTCIValidation.java` 源码核对。
> 用途：自动化测试**脱离 Java 代码**即可将响应 `$.msgKey` 对应到具体业务含义与触发条件。
> 生成日期：2026-08（以工程 RCC-Space_V1.1_R1 为准）。

## 错误码总表

| 错误码 | 常量名 | 业务含义 | 触发条件（源码） |
|---|---|---|---|
| 62110001 | SPACETCI_LESSONSTRATEGY_STRATEGY_TYPE_ERROR | 策略类型错误 | `strategyType != VOI`（validStrategyType） |
| 62110002 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_NOT_MATCH_SPECIFICATION | 策略名称不符合命名规范 | `name` 不匹配正则 `^[0-9a-zA-Z\u4e00-\u9fa5\.\-@]{1}[0-9a-zA-Z\u4e00-\u9fa5\.\-_@]*`（允许数字/字母/中文/./-/_/@，首字符不能是 `_`） |
| 62110003 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_EXIST | 策略名称已存在 | 同名本地策略已存在（本地查重） |
| 62110004 | SPACETCI_LESSONSTRATEGY_STRATEGY_TYPE_CAN_NOT_UPDATE | 策略类型不可修改 | 编辑时修改 strategyType |
| 62110005 | SPACETCI_LESSONSTRATEGY_STRATEGY_STATE_NOT_AVAILABLE | 策略状态不可用 | 编辑时策略状态非可用态（validState） |
| 62110006 | SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE | 系统盘小于原值 | 编辑时 systemDisk 小于原策略值 |
| 62110007 | SPACETCI_LESSONSTRATEGY_DATA_DISK_STATUS_NOT_SAME | 数据盘状态不一致 | 编辑时数据盘开关状态变化 |
| 62110008 | SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE | 数据盘小于原值 | 编辑时数据盘大小小于原值 |
| 62110009 | SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM | 策略被教室使用 | 删除时策略已关联教室 |
| 62110010 | SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY_BY_LESSON_IMAGE | 无法按课程镜像找到策略 | 课程镜像关联查询失败 |
| 62110011 | SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY | 找不到课程策略 | 策略 id 不存在 |
| **62110012** | SPACETCI_LESSONSTRATEGY_DISK_STRATEGY_EMPTY | 磁盘策略为空 | **两种触发**：① `enableScheduleStrategy=true` 但 `diskRestoreStrategyArr` 为空数组（checkStrategyRestoreDiskInfo:115）；② `enableDiskConfig=true` 但 `diskSize==null`（validDiskSize:115）⚠️ **注意：数据盘开启但 diskSize 为 null 实际返回 62110012，不是 62110019** |
| 62110013 | SPACETCI_LESSONSTRATEGY_SCHEDULE_TYPE_EMPTY | 还原调度类型为空 | diskRestoreStrategyArr 元素 `scheduleType` 为空 |
| 62110014 | SPACETCI_LESSONSTRATEGY_SCHEDULE_EXECUTE_TIME_EMPTY | 还原调度执行时间为空 | diskRestoreStrategyArr 元素 `scheduleExecuteTime` 为空 |
| 62110015 | SPACETCI_LESSONSTRATEGY_PERIOD_EMPTY | 还原周期为空 | diskRestoreStrategyArr 元素 `resolvePeriod()` 为空（按 scheduleType 解析周期失败） |
| 62110016 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_LENGTH_NOT_EMPTY | 策略名称不能为空 | `name` 为空/null（validStrategyName） |
| 62110017 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_LENGTH_TOO_LONG | 策略名称超长 | `name.length() > 32`（STRATEGY_NAME_MAX_LENGTH=32） |
| 62110018 | SPACETCI_LESSONSTRATEGY_AUTO_EDIT_DISABLED | 自动编辑被禁用 | pattern != RECOVERABLE 且 `enableAutoEdit=true`（validAutoEdit） |
| 62110019 | SPACETCI_LESSONSTRATEGY_DISK_SIZE_EMPTY | 数据盘大小为 null（**定义存在但工程未抛**） | ⚠️ 全工程无抛法（仅 ErrorCode 定义），实际 diskSize==null 走 62110012 |
| 62110050 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_FORBID_SET | 个性配置盘大小禁止设置 | 个性配置相关校验 |
| 62110051 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_STRATEGY_TYPE_ERROR | 个性配置策略类型错误 | 个性配置相关校验 |
| 62110052 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_EMPTY | 个性配置盘大小为空 | 个性配置相关校验 |
| 62110053 | SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE_WHEN_CREATE | 创建时系统盘小于原值 | 创建场景校验 |
| 62110054 | SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE_WHEN_CREATE | 创建时数据盘小于原值 | 创建场景校验 |

## 重名校验错误码（validateNameDuplication）

| 错误码 | 业务含义 | 触发条件 |
|---|---|---|
| 62100317 | 本地策略名称重复 | 本地同名策略已存在 |
| 62100220 | 平台策略组名称重复 | 平台侧策略组重名 |

## 校验执行顺序（validateBeforeCreate）

```
validateBeforeCreate:
  1. validStrategyType  (62110001)        策略类型必须 VOI
  2. validStrategyName  (62110016/17/02)  名称规则（空→62110016，超32→62110017，格式→62110002）
  3. checkStrategyRestoreDiskInfo (62110012~15)  磁盘还原策略（enableScheduleStrategy=true 时）
  4. validAutoEdit      (62110018)        非还原模式禁止自动编辑
  5. validDiskSize      (62110012)        enableDiskConfig=true 时 diskSize 必填（抛 62110012）
  6. validateNameDuplication (62100317 本地 + 62100220 平台)  名称查重
```

⚠️ 自动化提示：
- 校验**按序执行、第一个失败决定 msgKey**。如同时传空 name + 非 VOI 类型，先报 62110001（类型校验最前）。
- **62110019 文档标注错误**：数据盘开启但 diskSize 为 null 实际返回 **62110012**（validDiskSize 抛 DISK_STRATEGY_EMPTY），62110019 虽定义但全工程未抛。
- 创建与编辑共用 validStrategy，编辑额外走 validState/validDisk/validateBeforeLessonStrategyChange（62110004~08）。
