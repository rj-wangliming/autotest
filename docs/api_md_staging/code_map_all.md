# RCC-Space 状态码/错误码全量对照表（code_map_all）

> 来源：RCC-Space_V1.1_R1 工程源码提取（ErrorCode 类 + BusinessKey 类 + 状态枚举类）。
> 用途：自动化测试**脱离 Java 代码**即可将响应 `$.msgKey` / `$.status` / 状态字段对应到业务含义。
> 生成日期：2026-08

## 统计

- 数字错误码：141 个
- 响应错误 key（字符串 msgKey）：500 个
- 成功 key：57 个
- 状态枚举值：95 个（19 个枚举类）
- 日志/审计 key（非响应）：213 个

## 目录
1. [数字错误码（ErrorCode / BusinessKey 数字码）](#1-数字错误码)
2. [响应错误 key（字符串 msgKey）](#2-响应错误-key)
3. [成功 key](#3-成功-key)
4. [状态枚举（业务状态）](#4-状态枚举)
5. [日志/审计 key（非响应，自动化不断言）](#5-日志审计-key)

---

## 1. 数字错误码

| 错误码 | 常量名 | 定义类 |
|---|---|---|
| 11011701 | CLUSTER_OVER_LOAD_CONFIG_NOT_EXIST | RccOffIoOverloadLimitQuartzTask |
| 11032002 | RCDC_AFFINITY_RULE_NOT_EXIST | PaConstants |
| 23200358 | RCDC_SPACE_SYSTEM_CMD_EXECUTE_FAIL | BusinessKey |
| 23250131 | RCDC_CLOUDDESKTOP_DESKINFO_EXIST | PlatformDeskVDIMgmtAPIImpl |
| 23251320 | RCDC_RCC_NETWORK_CHECK_IP_NOT_IN_NETWORK_POOL | RccNetworkBusinessKey |
| 23251321 | RCDC_RCC_NETWORK_CLUSTER_NOT_IDV_VDI_IMAGE_TEMPLATE | RccNetworkBusinessKey |
| 23251322 | RCDC_RCC_NETWORK_AND_CLUSTER_NOT_AGREEMENT | RccNetworkBusinessKey |
| 23251323 | RCDC_RCC_NETWORK_AND_STORAGE_POOL_CLUSTER_NOT_AGREEMENT | RccNetworkBusinessKey |
| 23251324 | RCDC_RCC_NETWORK_AND_IMAGE_TEMPLATE_CLUSTER_CPU_NOT_AGREEMENT | RccNetworkBusinessKey |
| 23310054 | RCDC_PLATFORM_OFFLINE_ERROR_CODE | ClassroomConstants |
| 23310244 | RCDC_RCC_CLUSTER_IMAGE_CPU_FRAMEWORK_NOT_AGREEMENT | ClusterBussinessKey |
| 23310245 | RCDC_RCC_CLUSTER_STORAGE_POOL_NOT_AGREEMENT | ClusterBussinessKey |
| 23310246 | RCDC_RCC_CLUSTER_NETWORK_NOT_CLUSTER | ClusterBussinessKey |
| 23310247 | RCDC_RCC_CLUSTER_TARGET_PLATFORM_EXIST_UNINSTALL_CPU | ClusterBussinessKey |
| 23310248 | RCDC_RCC_CLUSTER_OS_FILE_CLUSTER_CPU_ARCH_NOT_MATCH | ClusterBussinessKey |
| 62100001 | SPACETCI_LESSON_CANNOT_FIND_IMAGE | ClassroomLessonErrorCode |
| 62100002 | SPACETCI_LESSON_CANNOT_FIND_DESKTOP | ClassroomLessonErrorCode |
| 62100003 | SPACETCI_LESSON_SHUTDOWN_DESKTOP_TIMEOUT | ClassroomLessonErrorCode |
| 62100004 | SPACETCI_LESSON_START_DESKTOP_SEND_FAIL | ClassroomLessonErrorCode |
| 62100005 | SPACETCI_LESSON_SHUTDOWN_DESKTOP_SEND_FAIL | ClassroomLessonErrorCode |
| 62100006 | SPACETCI_LESSON_START_TEACHER_DESKTOP_FAIL | ClassroomLessonErrorCode |
| 62100022 | SPACE_LESSON_GET_TEACHING_CLASS_PARAM_FAIL | ClassroomLessonErrorCode |
| 62100023 | SPACE_LESSON_GET_TEACHING_CLASS_INFO_FAIL | ClassroomLessonErrorCode |
| 62100042 | RCDC_RCC_STORAGE_POOL_LIMIT_RAID1 | StoragePoolBussinessKey |
| 62100043 | RCDC_RCC_STORAGE_POOL_SAMBA_TYPE_NOT_SUPPORT | StoragePoolBussinessKey |
| 62100044 | RCDC_RCC_NETWORK_AND_STORAGE_POOL_CLUSTER_NOT_AGREEMENT | StoragePoolBussinessKey |
| 62100045 | RCDC_RCC_STORAGE_NOT_CLUSTER | StoragePoolBussinessKey |
| 62100046 | RCDC_RCC_STORAGE_POOL_CLUSTER_CPU_IMAGE_TEMPLATE_NOT_AGREEMENT | StoragePoolBussinessKey |
| 62100047 | RCDC_RCC_STORAGE_POOL_CLUSTER_NOT_SUPPORT_SELECT | StoragePoolBussinessKey |
| 62100048 | SPACE_DESK_NOT_MGMT_BY_SPACE | SpacePaErrorCodes |
| 62100049 | SPACE_DESK_NOT_MGMT_BY_RCO | SpacePaErrorCodes |
| 62100050 | SPACE_IMAGE_NOT_SUPPORT_OPERATION | SpacePaErrorCodes |
| 62100069 | SPACE_DISKPOOL_OPTER_FAIL | ClassroomResourceErrorCode |
| 62100070 | RCDC_SPACE_DESKTOP_BIND_USER_FAIL_USER_NOT_IN_POOL | SpaceDesktopBusinessKey |
| 62100071 | RCDC_SPACE_DESKTOP_BIND_USER_DESKTOP_INFO_ERROR | SpaceDesktopBusinessKey |
| 62100072 | RCDC_SPACE_DESKTOP_BIND_USER_ERROR_HAD_BIND_OTHER | SpaceDesktopBusinessKey |
| 62100073 | RCDC_SPACE_DESKTOP_UNBIND_USER_ALREADY_ASSOCIATED | SpaceDesktopBusinessKey |
| 62100074 | RCDC_SPACE_DESKTOP_POOL_NOT_EXIST | SpaceDesktopBusinessKey |
| 62100075 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_USER_NULL | SpaceDesktopBusinessKey |
| 62100076 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_VISITOR_FAIL | SpaceDesktopBusinessKey |
| 62100077 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_GROUP_NULL | SpaceDesktopBusinessKey |
| 62100078 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_AD_GROUP_NULL | SpaceDesktopBusinessKey |
| 62100079 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_LDAP_GROUP_NULL | SpaceDesktopBusinessKey |
| 62100080 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_USER_NOT_EXIST | SpaceDesktopBusinessKey |
| 62100081 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_TASK_REPEAT | SpaceDesktopBusinessKey |
| 62100082 | RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_ERROR | SpaceDesktopBusinessKey |
| 62100100 | RCDC_RCO_WATERMARK_DESKTOP_NOT_EXIST | SpaceDeskPaErrorCodes |
| 62100120 | RCDC_RCC_CLASSROOM_POOL_NO_USER_GROUP_AUTH | RccSpaceBusinessKey |
| 62100121 | RCDC_RCC_CLASSROOM_POOL_NO_USER_AUTH | RccSpaceBusinessKey |
| 62100122 | RCDC_RCC_CLASSROOM_POOL_DESKTOP_STARTING_FORBID_BINDUSER | RccSpaceBusinessKey |
| 62100220 | RCDC_STRAGETY_GROUP_EXIST | SpaceStrategyGroupErrorCodes |
| 62100223 | RCDC_RCC_IMAGE_SINGLE_IMAGE_CAN_NOT_SELECT_TO_OTHER_PLATFORM | ClassroomImageBusinessKey |
| 62100224 | RCDC_RCC_IMAGE_SINGLE_IMAGE_NOT_SUPPORT | ClassroomImageBusinessKey |
| 62100225 | RCDC_RCC_IMAGE_VERSION_ONLY_CHANGED_BY_RECOVERABLE | ClassroomImageBusinessKey |
| 62100226 | RCDC_RCC_IMAGE_VERSION_ID_IS_NOT_NULL | ClassroomImageBusinessKey |
| 62100227 | RCDC_CHANGE_CLASSROOM_STUDENT_IMAGE_VERSION_LOG | ClassroomImageBusinessKey |
| 62100228 | RCDC_CHANGE_CLASSROOM_TEACHER_IMAGE_VERSION_LOG | ClassroomImageBusinessKey |
| 62100229 | RCDC_RCC_CHANGE_CLASSROOM_STUDENT_IMAGE_VERSION_FAIL_LOG | ClassroomImageBusinessKey |
| 62100230 | RCDC_RCC_CHANGE_CLASSROOM_TEACHER_IMAGE_VERSION_FAIL_LOG | ClassroomImageBusinessKey |
| 62100231 | RCDC_RCC_TCI_IMAGE_NO_SUPPORT_ARM | ClassroomImageBusinessKey |
| 62100232 | RCDC_RCO_CLOUD_PLATFORM_IS_UN_AVAILABLE | ClassroomImageBusinessKey |
| 62100233 | RCDC_RCC_ASSIGN_IMAGE_DIFF_PLATFORM | ClassroomImageBusinessKey |
| 62100234 | RCDC_RCC_ASSIGN_IMAGE_DIFF_CLUSTER | ClassroomImageBusinessKey |
| 62100235 | RCDC_RCC_ASSIGN_IMAGE_DIFF_NET_STRATEGY | ClassroomImageBusinessKey |
| 62100236 | RCDC_RCC_ASSIGN_IMAGE_GET_PLATFORM_CLUSTER_FAIL | ClassroomImageBusinessKey |
| 62100237 | RCDC_RCC_STORAGE_POOL_EXTERNAL_TYPE_NOT_SUPPORT | StoragePoolBussinessKey |
| 62100238 | RCDC_RCC_CLASSROOM_IMAGE_IN_EXTERNAL_STORAGE | ClassroomImageBusinessKey |
| 62100239 | RCC_IMAGE_VERSION_REPLICATION_NOT_FIND_ERROR_CODE | ClassroomImageBusinessKey |
| 62100240 | RCDC_RCC_STORAGE_POOL_POS_TYPE_NOT_SUPPORT | StoragePoolBussinessKey |
| 62100241 | RCDC_RCC_CREATE_DATA_DISK_FAIL_PLATFORM_OFFLINE | ClassroomBusinessKey |
| 62100242 | RCDC_RCC_CAPACITY_DATA_DISK_FAIL_PLATFORM_OFFLINE | ClassroomBusinessKey |
| 62100243 | RCDC_RCC_DELETE_SEAT_FROM_DB_INCLUDE_TCI | ClassroomBusinessKey |
| 62100244 | RCDC_RCC_PLATFORM_UNAVAILABLE | ClassroomBusinessKey |
| 62100248 | SPACE_DESKTOP_OPERATE_FAIL | ClassroomResourceErrorCode |
| 62100300 | RCDC_RCC_CLASSROOM_CHECK_SUCCESS | SpaceImageErrorCodes |
| 62100301 | RCDC_RCC_DESKTOP_STRATEGY_IMAGE_INFO_CAN_NOT_FIND | SpaceImageErrorCodes |
| 62100302 | RCDC_RCC_DESKTOP_STRATEGY_CUSTOM_DESKTOP_STRATEGY_CAN_NOT_FIND | SpaceImageErrorCodes |
| 62100303 | RCDC_RCC_DESKTOP_STRATEGY_ENVIRONMENT_DESKTOP_RUNNING | SpaceImageErrorCodes |
| 62100304 | RCDC_RCC_DESKTOP_STRATEGY_ACCOUNT_CHECK_FAIL_TOO_LONG | SpaceImageErrorCodes |
| 62100305 | RCDC_RCC_DESKTOP_STRATEGY_ACCOUNT_CHECK_FAIL_UNAVAILABLE | SpaceImageErrorCodes |
| 62100306 | RCDC_RCC_DESKTOP_STRATEGY_GRAPHICS_ADDITION_EMPTY | SpaceImageErrorCodes |
| 62100307 | RCDC_RCC_DESKTOP_STRATEGY_SYSTEM_DISK_LESS_IMAGE_DISK | SpaceImageErrorCodes |
| 62100308 | RCDC_RCC_DESKTOP_STRATEGY_DATA_DISK_LESS_IMAGE_DISK | SpaceImageErrorCodes |
| 62100309 | RCDC_RCC_DESKTOP_STRATEGY_SYSTEM_DISK_LESS_BEFORE | SpaceImageErrorCodes |
| 62100310 | RCDC_RCC_DESKTOP_STRATEGY_DATA_DISK_LESS_BEFORE | SpaceImageErrorCodes |
| 62100311 | RCDC_RCC_DESKTOP_STRATEGY_IDV_SYSTEM_DISK_CAN_NOT_CHANGE | SpaceImageErrorCodes |
| 62100312 | RCDC_RCC_DESKTOP_STRATEGY_IDV_SYSTEM_DISK_CAN_NOT_CHANGE_DETAIL | SpaceImageErrorCodes |
| 62100313 | RCDC_RCC_DESKTOP_STRATEGY_CONFIG_FAULT_NULL | SpaceImageErrorCodes |
| 62100314 | RCDC_RCC_DESKTOP_STRATEGY_BASE_CONFIG_FAULT_CROSS_BORDER | SpaceImageErrorCodes |
| 62100315 | RCDC_RCC_DESKTOP_STRATEGY_OS_TYPE_NOT_SUPPORT | SpaceImageErrorCodes |
| 62100316 | RCDC_RCC_DESKTOP_STRATEGY_DATA_DISK_CAN_NOT_BE_NULL | SpaceImageErrorCodes |
| 62100317 | RCDC_SPACE_STRAGETY_GROUP_EXIST | SpaceImageErrorCodes |
| 62100318 | RCDC_RCC_CLOUDDESKTOP_RCC_STRATEGY_TYPE_CAN_NOT_UPDATE | SpaceImageErrorCodes |
| 62100319 | RCDC_RCC_CLOUDDESKTOP_DESK_PATTERN_CAN_NOT_UPDATE | SpaceImageErrorCodes |
| 62100320 | RCDC_CLOUDDESKTOP_RCC_STRATEGY_NOT_AVAILABLE | SpaceImageErrorCodes |
| 62100321 | RCDC_RCC_DESK_STRATEGY_CPU_HAS_MORETHEN_IMAGE_DETAIL | SpaceImageErrorCodes |
| 62100322 | RCDC_RCO_IMAGE_OS_TYPE_NOT_SUPPORT_GPU | SpaceImageErrorCodes |
| 62100323 | RCDC_DESK_STRATEGY_UPDATE_BIND_IMAGE_GPU_NOT_SUPPORT | SpaceImageErrorCodes |
| 62100324 | STRATEGY_GROUP_RELATED_BY_IMAGE | SpaceImageErrorCodes |
| 62100325 | RCDC_RCC_DESKTOP_STRATEGY_PASSWORD_CHECK_FAIL_UNAVAILABLE | SpaceImageErrorCodes |
| 62100326 | RCDC_RCC_DESKTOP_STRATEGY_ACCOUNT_PASSWORD_CHECK_FAIL_TOO_LONG | SpaceImageErrorCodes |
| 62100331 | RCDC_RCC_DESKTOP_STRATEGY_BASE_CONFIG_CPU_FAULT_CROSS_BORDER | SpaceImageErrorCodes |
| 62100332 | RCDC_RCC_DESKTOP_STRATEGY_BASE_CONFIG_MEMORY_FAULT_CROSS_BORDER | SpaceImageErrorCodes |
| 62100333 | RCDC_SPACE_STRAGETY_GROUP_NOT_EXIST | SpaceImageErrorCodes |
| 62110001 | SPACETCI_LESSONSTRATEGY_STRATEGY_TYPE_ERROR | TCILessonStrategyErrorCode |
| 62110002 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_NOT_MATCH_SPECIFICATION | TCILessonStrategyErrorCode |
| 62110003 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_EXIST | TCILessonStrategyErrorCode |
| 62110004 | SPACETCI_LESSONSTRATEGY_STRATEGY_TYPE_CAN_NOT_UPDATE | TCILessonStrategyErrorCode |
| 62110005 | SPACETCI_LESSONSTRATEGY_STRATEGY_STATE_NOT_AVAILABLE | TCILessonStrategyErrorCode |
| 62110006 | SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE | TCILessonStrategyErrorCode |
| 62110007 | SPACETCI_LESSONSTRATEGY_DATA_DISK_STATUS_NOT_SAME | TCILessonStrategyErrorCode |
| 62110008 | SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE | TCILessonStrategyErrorCode |
| 62110009 | SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM | TCILessonStrategyErrorCode |
| 62110010 | SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY_BY_LESSON_IMAGE | TCILessonStrategyErrorCode |
| 62110011 | SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY | TCILessonStrategyErrorCode |
| 62110012 | SPACETCI_LESSONSTRATEGY_DISK_STRATEGY_EMPTY | TCILessonStrategyErrorCode |
| 62110013 | SPACETCI_LESSONSTRATEGY_SCHEDULE_TYPE_EMPTY | TCILessonStrategyErrorCode |
| 62110014 | SPACETCI_LESSONSTRATEGY_SCHEDULE_EXECUTE_TIME_EMPTY | TCILessonStrategyErrorCode |
| 62110015 | SPACETCI_LESSONSTRATEGY_PERIOD_EMPTY | TCILessonStrategyErrorCode |
| 62110016 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_LENGTH_NOT_EMPTY | TCILessonStrategyErrorCode |
| 62110017 | SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_LENGTH_TOO_LONG | TCILessonStrategyErrorCode |
| 62110018 | SPACETCI_LESSONSTRATEGY_AUTO_EDIT_DISABLED | TCILessonStrategyErrorCode |
| 62110019 | SPACETCI_LESSONSTRATEGY_DISK_SIZE_EMPTY | TCILessonStrategyErrorCode |
| 62110021 | SPACETCI_LESSONIMAGE_CANNOT_FIND_LESSON_IMAGE | TCILessonImageErrorCode |
| 62110022 | SPACETCI_LESSONIMAGE_IMAGE_TYPE_ERROR | TCILessonImageErrorCode |
| 62110023 | SPACETCI_LESSONIMAGE_IMAGE_STATE_NOT_AVAILABLE | TCILessonImageErrorCode |
| 62110024 | SPACETCI_LESSONIMAGE_SYSTEM_DISK_BIG_LESSONSTRTEGY | TCILessonImageErrorCode |
| 62110025 | SPACETCI_LESSONIMAGE_DATA_DISK_STATE_NOT_SAME | TCILessonImageErrorCode |
| 62110026 | SPACETCI_LESSONIMAGE_DATA_DISK_BIG_LESSONSTRTEGY | TCILessonImageErrorCode |
| 62110027 | SPACETCI_LESSONIMAGE_ADD_REPEAT | TCILessonImageErrorCode |
| 62110028 | SPACETCI_LESSONIMAGE_ALREADY_EXIST_LESSON_IMAGE | TCILessonImageErrorCode |
| 62110029 | SPACETCI_LESSONIMAGE_CANNOT_FIND_TEACHER_IMAGE | TCILessonImageErrorCode |
| 62110030 | SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE | TCILessonImageErrorCode |
| 62110050 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_FORBID_SET | TCILessonStrategyErrorCode |
| 62110051 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_STRATEGY_TYPE_ERROR | TCILessonStrategyErrorCode |
| 62110052 | SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_EMPTY | TCILessonStrategyErrorCode |
| 62110053 | SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE_WHEN_CREATE | TCILessonStrategyErrorCode |
| 62110054 | SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE_WHEN_CREATE | TCILessonStrategyErrorCode |
| 63100001 | SPACE_CMR_VERSION_FILE_NOT_FIND | CmrErrorCode |
| 63100002 | SPACE_CMR_VERSION_FILE_NOT_EXIST_COMPONENT_INFO | CmrErrorCode |
| 63100003 | SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT | CmrErrorCode |
## 2. 响应错误 key

> 响应 `$.msgKey` 取值（失败场景）。按定义类分组。

### BusinessKey（7）

| 常量名 | key 值 |
|---|---|
| RCDC_CLOUDDESKTOP_DESKINFO_NOT_CLOSE_STATE_RESTORE_FORBID | rcdc-clouddesktop_deskinfo_not_close_state_restore_forbid |
| RCDC_CLOUDDESKTOP_DESK_ROLE_ERROR | rcdc-clouddesktop_desk_role_error |
| RCDC_CLOUDDESKTOP_INFO_IS_EMPTY | rcdc-clouddesktop_info_is_empty |
| RCDC_RCC_MODULE_OPERATE_FAIL | rcdc_rcc_module_operate_fail |
| RCDC_RCC_MODULE_OPERATE_SUCCESS | rcdc_rcc_module_operate_success |
| RCDC_SAPCE_DATA_PERMISSION_DENIED | rcdc_space_data_permission_denied |
| RCDC_SPACE_SYSTEM_CMD_EXECUTE_FAIL | 23200358 |

### ClassroomBusinessKey（122）

| 常量名 | key 值 |
|---|---|
| CHECK_SUCCESS | rcdc_classroom_check_success |
| CLASSROOM_DECODE_MESSAGE_ERROR_FROM_SHINE | rcdc_classroom_decode_message_error_from_shine |
| CLASSROOM_IP_CHECK_BROADCAST_ADDR | rcdc_classroom_ip_check_broadcast_addr |
| CLASSROOM_IP_CHECK_CONFLICT_WITH_CLASSROOM | rcdc_classroom_ip_check_conflict_with_classroom |
| CLASSROOM_IP_CHECK_CONFLICT_WITH_NETWORK_STRATEGY | rcdc_classroom_ip_check_conflict_with_network_strategy |
| CLASSROOM_IP_CHECK_CONFLICT_WITH_PHYSICAL_SERVER | rcdc_classroom_ip_check_conflict_with_physical_server |
| CLASSROOM_IP_CHECK_ILLEGAL | rcdc_classroom_ip_check_illegal |
| CLASSROOM_IP_CHECK_NETWORK_ADDR | rcdc_classroom_ip_check_network_addr |
| CLASSROOM_IP_CHECK_NOT_SAME_NETWORK | rcdc_classroom_ip_check_not_same_network |
| CLASSROOM_IP_CHECK_RANGE_LACK | rcdc_classroom_ip_check_range_lack |
| CLASSROOM_IP_CHECK_STUDENT_LOCAL_STORAGE_SIZE_NULL | rcdc_classroom_param_check_student_local_storage_size_null |
| CLASSROOM_IP_CHECK_STUDENT_VDI_NETWORK_NOT_ENOUGH | rcdc_classroom_param_check_student_vdi_network_not_enough |
| CLASSROOM_IP_CHECK_STUDENT_VDI_NETWORK_NULL | rcdc_classroom_param_check_student_vdi_network_null |
| CLASSROOM_IP_CHECK_TEACHER_DESKTOP_PARAM_INCOMPLETE | rcdc_classroom_teacher_desktop_param_incomplete |
| CLASSROOM_IP_CHECK_TEACHER_VDI_NETWORK_NOT_ENOUGH | rcdc_classroom_param_check_teacher_vdi_network_not_enough |
| CLASSROOM_OPERATE_TIP_FAILED | rcdc_classroom_operate_tip_failed |
| CLASSROOM_OPERATE_TIP_SUCCESS | rcdc_classroom_operate_tip_success |
| CLASSROOM_TIP_CLASSROOM_IMAGE_TYPE_LIST_FETCH_FAIL | rcdc_classroom_image_type_list_fetch_fail |
| CLASSROOM_TIP_CLASSROOM_WORK_MODE_CANNOT_CHANGE | rcdc_classroom_work_mode_cannot_change |
| CLASSROOM_TIP_TEACHER_PARAM_CHECK_TEACHER_STORAGE_SIZE_NOT_ENOUGH | rcdc_classroom_param_check_teacher_storage_not_enough |
| RCDC_CLASSROOM_IMAGE_NOT_FIND | rcdc_classroom_image_not_find |
| RCDC_CLASSROOM_NOT_FIND | rcdc_classroom_not_find |
| RCDC_CLASSROOM_STUDENT_CHECK_SPACE_NOT_FIND_IMAGE | rcdc_classroom_student_check_space_not_find_image |
| RCDC_CLASSROOM_TEACHER_CHECK_SPACE_NOT_FIND_IMAGE | rcdc_classroom_teacher_check_space_not_find_image |
| RCDC_GET_CLASSROOM_ERROR | rcdc_get_classroom_error |
| RCDC_GET_CLASSROOM_SPACE_FAIL | rcdc_get_classroom_sapce_fail |
| RCDC_RCC_ASSIGN_CLASSROOM_AFTER_CROSS_STORAGE_FAIL_NO_CLASSROOM | rcdc_rcc_assign_classroom_after_cross_storage_fail_no_classroom |
| RCDC_RCC_ASSIGN_CLASSROOM_AFTER_CROSS_STORAGE_FAIL_NO_RELATION | rcdc_rcc_assign_classroom_after_cross_storage_fail_no_relation |
| RCDC_RCC_ASSIGN_CLASSROOM_AFTER_CROSS_STORAGE_FAIL_NO_REQUEST | rcdc_rcc_assign_classroom_after_cross_storage_fail_no_request |
| RCDC_RCC_CAPACITY_DATA_DISK_FAIL_PLATFORM_OFFLINE | 62100242 |
| RCDC_RCC_CHANGE_CLASSROOM_AFTER_CROSS_STORAGE_FAIL_NO_CLASSROOM | rcdc_rcc_change_classroom_after_cross_storage_fail_no_classroom |
| RCDC_RCC_CHANGE_CLASSROOM_AFTER_CROSS_STORAGE_FAIL_NO_RELATION | rcdc_rcc_change_classroom_after_cross_storage_fail_no_relation |
| RCDC_RCC_CLASSROOM_CHANGE_STUDENT_IMAGE_VERSION_TASK_FAIL | rcdc_rcc_classroom_change_student_image_version_task_fail |
| RCDC_RCC_CLASSROOM_CHANGE_STUDENT_IMAGE_VERSION_TASK_SUCCESS | rcdc_rcc_classroom_change_student_image_version_task_success |
| RCDC_RCC_CLASSROOM_CHANGE_TEACHER_IMAGE_VERSION_TASK_FAIL | rcdc_rcc_classroom_change_teacher_image_version_task_fail |
| RCDC_RCC_CLASSROOM_CHANGE_TEACHER_IMAGE_VERSION_TASK_SUCCESS | rcdc_rcc_classroom_change_teacher_image_version_task_success |
| RCDC_RCC_CLASSROOM_COULD_NOT_FIND_VDI_DISK_STORAGE_POOL | rcdc_rcc_classroom_could_not_find_vdi_disk_storage_pool |
| RCDC_RCC_CLASSROOM_CREATE_TASK_FAIL | rcdc_rcc_classroom_create_task_fail |
| RCDC_RCC_CLASSROOM_CREATE_TASK_SUCCESS | rcdc_rcc_classroom_create_task_success |
| RCDC_RCC_CLASSROOM_DESKTOP_START_FAIL_WITH_VDI_DISK_DEATTACH_FAIL | rcdc_rcc_classroom_desktop_start_fail_with_vdi_disk_deattach_fail |
| RCDC_RCC_CLASSROOM_DESKTOP_USED | rcdc_rcc_classroom_desktop_used |
| RCDC_RCC_CLASSROOM_DISK_POOL_DETELE_FAIL | rcdc_rcc_classroom_disk_pool_detele_fail |
| RCDC_RCC_CLASSROOM_HAS_TERMINAL_GROUP_DUPLICATION | rcdc_rcc_classroom_has_terminal_group_duplication |
| RCDC_RCC_CLASSROOM_IMAGE_IP_HAS_USED | rcdc_rcc_classroom_image_ip_has_used |
| RCDC_RCC_CLASSROOM_IMAGE_NOT_EXIST | rcdc_rcc_classroom_image_not_exist |
| RCDC_RCC_CLASSROOM_IMAGE_NOT_EXIST_CLUSTER | rcdc_rcc_classroom_image_not_exist_cluster |
| RCDC_RCC_CLASSROOM_IMAGE_VDI_STORAGE_NOT_BE_USED | rcdc_rcc_classroom_image_vdi_storage_not_be_used |
| RCDC_RCC_CLASSROOM_IP_HAS_USED | rcdc_rcc_classroom_ip_has_used |
| RCDC_RCC_CLASSROOM_NAME_DUPLICATION | rcdc_rcc_classroom_name_duplication |
| RCDC_RCC_CLASSROOM_NOT_EXIST_IMAGE | rcdc_rcc_classroom_not_exit_image |
| RCDC_RCC_CLASSROOM_OPERATE_CLASSROOM_DELETE_FAIL_REASON | rcdc_rcc_classroom_operate_classroom_delete_fail_reason |
| RCDC_RCC_CLASSROOM_OPERATE_CLASSROOM_DELETE_SINGLE_FAIL | rcdc_rcc_classroom_operate_classroom_delete_single_fail |
| RCDC_RCC_CLASSROOM_OPERATE_DISABLE_NETWORK_SINGLE_FAIL | rcdc_rcc_classroom_operate_disable_network_single_fail |
| RCDC_RCC_CLASSROOM_OPERATE_ENABLE_NETWORK_SINGLE_FAIL | rcdc_rcc_classroom_operate_enable_network_single_fail |
| RCDC_RCC_CLASSROOM_OPERATE_TIP_TEACHER_DESKTOP_USED | rcdc_rcc_classroom_operate_tip_teacher_desktop_used |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_FOR_UPDATE_CLASSROOM_STATE | rcdc_rcc_classroom_starting_class_fail_for_update_classroom_state |
| RCDC_RCC_CLASSROOM_STUDENT_CONFIG_TASK_FAIL | rcdc_rcc_classroom_student_config_task_fail |
| RCDC_RCC_CLASSROOM_STUDENT_CONFIG_TASK_SUCCESS | rcdc_rcc_classroom_student_config_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_CONFIG_TASK_FAIL | rcdc_rcc_classroom_teacher_config_task_fail |
| RCDC_RCC_CLASSROOM_TEACHER_CONFIG_TASK_SUCCESS | rcdc_rcc_classroom_teacher_config_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_END_LESSON_TASK_FAIL | rcdc_rcc_classroom_teacher_end_lesson_task_fail |
| RCDC_RCC_CLASSROOM_TEACHER_END_LESSON_TASK_SUCCESS | rcdc_rcc_classroom_teacher_end_lesson_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_EXIST | rcdc_rcc_classroom_teacher_pre_name_exist |
| RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_NOT_EMPTY | rcdc_rcc_classroom_teacher_pre_name_not_empty |
| RCDC_RCC_CLASSROOM_TEACHER_START_LESSON_TASK_FAIL | rcdc_rcc_classroom_teacher_start_lesson_task_fail |
| RCDC_RCC_CLASSROOM_TEACHER_START_LESSON_TASK_SUCCESS | rcdc_rcc_classroom_teacher_start_lesson_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_START_MODE_ERROR | rcdc_rcc_classroom_teacher_start_mode_error |
| RCDC_RCC_CLASSROOM_TEACHER_VDI_DESK_NOT_EXIST | rcdc_rcc_classroom_teacher_vdi_desk_not_exist |
| RCDC_RCC_CLUSTER_NOT_EXIST | rcdc_rcc_cluster_not_exist |
| RCDC_RCC_CREATE_CLASSROOM_SEAT_NUM_ERROR | rcdc_rcc_create_classroom_seat_num_error |
| RCDC_RCC_CREATE_DATA_DISK_FAIL_PLATFORM_OFFLINE | 62100241 |
| RCDC_RCC_DO_IMAGE_CARD_ACTION_FAIL | rcdc_rcc_do_image_card_action_fail |
| RCDC_RCC_DO_IMAGE_CARD_ACTION_FAIL_NOT_FIND_IMAGE | rcdc_rcc_do_image_card_action_fail_not_find_image |
| RCDC_RCC_GET_IMAGE_DRIVER_ERROR | rcdc_rcc_get_image_driver_error |
| RCDC_RCC_IDV_CLOUD_DESKTOP_CONFIG_ERROR | rcdc_rcc_idv_cloud_desktop_config_error |
| RCDC_RCC_NOT_FIND_CLASSROOM_IMAGE | rcdc_rcc_not_find_classroom_image |
| RCDC_RCC_PART_IMAGE_IS_NOT_EXIST_BEFORE_ASSIGN | rcdc_rcc_part_image_is_not_exist_before_assign |
| RCDC_RCC_RESERVED_STORAGE_LOW_ERROR | rcdc_rcc_reserved_storage_low_error |
| RCDC_RCC_RESERVED_STORAGE_LOW_THAN_CLASSROOM_SIZE_ERROR | rcdc_rcc_reserved_storage_low_than_classroom_size_error |
| RCDC_RCC_SEAT_BATCH_CHECK_CLASSROOM_NOT_EXIST | rcdc_rcc_seat_batch_check_classroom_not_exist |
| RCDC_RCC_SEAT_BATCH_CHECK_IP_EXIST_NETWORK_NO_EXIST | rcdc_rcc_seat_batch_check_ip_exist_network_no_exist |
| RCDC_RCC_SEAT_BATCH_CHECK_IP_NOT_IN_NETWORK | rcdc_rcc_seat_batch_check_ip_not_in_network |
| RCDC_RCC_SEAT_BATCH_CHECK_NETWORK_NOT_ENOUGH | rcdc_rcc_seat_batch_check_network_not_enough |
| RCDC_RCC_SEAT_BATCH_CHECK_NETWORK_NOT_EXIST | rcdc_rcc_seat_batch_check_network_not_exist |
| RCDC_RCC_SEAT_BATCH_CHECK_STUDENT_IP_CONFLICT | rcdc_rcc_seat_batch_check_student_ip_conflict |
| RCDC_RCC_SEAT_BATCH_CHECK_TEACER_IP_CONFLICT | rcdc_rcc_seat_batch_check_teacer_ip_conflict |
| RCDC_RCC_SEAT_BATCH_CONFIG_ERROR | rcdc_rcc_seat_batch_config_error |
| RCDC_RCC_SEAT_BATCH_CONFIG_FAIL | rcdc_rcc_seat_batch_config_fail |
| RCDC_RCC_SEAT_CONFIG_START_MODE_FAIL | rcdc_rcc_seat_config_start_mode_fail |
| RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE | rcdc_rcc_seat_desktop_ip_duplicate |
| RCDC_RCC_SEAT_DESKTOP_NAME_DUPLICATE | rcdc_rcc_seat_desktop_name_duplicate |
| RCDC_RCC_SEAT_DESKTOP_NAME_INVALID | rcdc_rcc_seat_desktop_name_invalid |
| RCDC_RCC_SEAT_DESKTOP_PRENAME_INVALID | rcdc_rcc_seat_desktop_prename_invalid |
| RCDC_RCC_SEAT_DESKTOP_PRENAME_LENGTH_INVALID | rcdc_rcc_seat_desktop_prename_length_invalid |
| RCDC_RCC_SEAT_DNS_INVALID | rcdc_rcc_seat_dns_invalid |
| RCDC_RCC_SEAT_GATEWAY_INVALID | rcdc_rcc_seat_gateway_invalid |
| RCDC_RCC_SEAT_IP_INVALID | rcdc_rcc_seat_ip_invalid |
| RCDC_RCC_SEAT_IP_USED | rcdc_rcc_seat_ip_used |
| RCDC_RCC_SEAT_IP_USED_BY_UNKNOW_RESOURCE | rcdc_rcc_seat_ip_used_by_unknow_resource |
| RCDC_RCC_SEAT_IP_USED_TIP | rcdc_rcc_seat_ip_used_tip |
| RCDC_RCC_SEAT_MASK_INVALID | rcdc_rcc_seat_mask_invalid |
| RCDC_RCC_SEAT_OPERATE_DISABLE_NETWORK_SINGLE_FAIL | rcdc_rcc_seat_operate_disable_network_single_fail |
| RCDC_RCC_SEAT_OPERATE_ENABLE_NETWORK_SINGLE_FAIL | rcdc_rcc_seat_operate_enable_network_single_fail |
| RCDC_RCC_SEAT_OPERATE_SEAT_CHANGE_SINGLE_FAIL | rcdc_rcc_seat_operate_seat_change_single_fail |
| RCDC_RCC_SEAT_OPERATE_SEAT_CREATE_SINGLE_FAIL | rcdc_rcc_seat_operate_seat_create_single_fail |
| RCDC_RCC_SEAT_OPERATE_SEAT_DELETE_SINGLE_FAIL | rcdc_rcc_seat_operate_seat_delete_single_fail |
| RCDC_RCC_SEAT_REQUEST_TERMINAL_EMPTY | rcdc_rcc_seat_request_terminal_empty |
| RCDC_RCC_SEAT_REQUEST_TERMINAL_FAIL | rcdc_rcc_seat_request_terminal_fail |
| RCDC_RCC_STORAGE_POOL_NOT_EXIST | rcdc_rcc_storage_pool_not_exist |
| RCDC_RCC_TEACHER_DESKTOP_NOT_EXIST | rcdc_rcc_teacher_desktop_not_exist |
| RCDC_RCC_TEACHER_STORAGE_LOW_THAN_CLASSROOM_SIZE_ERROR | rcdc_rcc_teacher_storage_low_than_classroom_size_error |
| RCDC_RCC_TEACHER_VDI_CLEAR_LOCAL_DISK_NOT_CLOSE_TASK_FAIL | rcdc_rcc_teacher_vdi_clear_local_disk_not_close_task_fail |
| RCDC_RCC_TEACHER_VDI_CLEAR_LOCAL_DISK_TASK_FAIL | rcdc_rcc_teacher_vdi_clear_local_disk_task_fail |
| RCDC_RCC_VDI_CLEAR_LOCAL_DISK_NOT_CLOSE_TASK_FAIL | rcdc_rcc_vdi_clear_local_disk_not_close_task_fail |
| RCDC_RCC_VDI_CLEAR_LOCAL_DISK_STRATEGY_NO_EXIST | rcdc_rcc_vdi_clear_local_disk_strategy_no_exist |
| RCDC_RCC_VDI_CLEAR_LOCAL_DISK_TASK_FAIL | rcdc_rcc_vdi_clear_local_disk_task_fail |
| RCDC_RCC_VDI_CLOUD_DESKTOP_CONFIG_ERROR | rcdc_rcc_vdi_cloud_desktop_config_error |
| STRING_CHECK_CODE_AVAILABLE | rcdc_classroom_string_check_fail_available |
| STRING_CHECK_CODE_CONFLICT | rcdc_classroom_string_check_fail_conflict |
| STRING_CHECK_CODE_EXIST | rcdc_classroom_string_check_fail_exist |
| STRING_CHECK_CODE_TOO_LONG | rcdc_classroom_string_check_fail_long |
| STRING_CHECK_CODE_TOO_SHORT | rcdc_classroom_string_check_fail_short |

### ClassroomImageBusinessKey（14）

| 常量名 | key 值 |
|---|---|
| RCC_IMAGE_VERSION_REPLICATION_NOT_FIND_ERROR_CODE | 62100239 |
| RCDC_CLASSROOM_CLUSTER_RESOURCES_HAS_CLUSTER_CONFIG_FORBID_UPDATE | rcdc_classroom_cluster_resources_has_cluster_config_forbid_update |
| RCDC_CLASSROOM_CLUSTER_RESOURCES_HAS_NETOWRK_CONFIG_FORBID_UPDATE | rcdc_classroom_cluster_resources_has_netowrk_config_forbid_update |
| RCDC_RCC_ASSIGN_IMAGE_GET_PLATFORM_CLUSTER_FAIL | 62100236 |
| RCDC_RCC_CLASSROOM_CLUSTER_RESOURCES_CONFIG_DELETE_FORBID_FOR_IMAGE_EXIST | rcdc_rcc_classroom_cluster_resources_config_delete_forbid_for_image_exist |
| RCDC_RCC_CLASSROOM_CLUSTER_RESOURCES_CONFIG_DELETE_FORBID_FOR_SEAT_RELATION | rcdc_rcc_classroom_cluster_resources_config_delete_forbid_for_seat_relation |
| RCDC_RCC_CLASSROOM_CLUSTER_RESOURCES_CONFIG_DELETE_FORBID_FOR_TEACHER_RELATION | rcdc_rcc_classroom_cluster_resources_config_delete_forbid_for_teacher_relation |
| RCDC_RCC_CLASSROOM_TEACHER_NETWORK_STRATEGY_EDIT_TASK_FAIL | rcdc_rcc_classroom_teacher_network_strategy_edit_task_fail |
| RCDC_RCC_CLASSROOM_TEACHER_NETWORK_STRATEGY_EDIT_TASK_SUCCESS | rcdc_rcc_classroom_teacher_network_strategy_edit_task_success |
| RCDC_RCC_DESK_STRATEGY_SYSTEM_DISK_HAS_LESS_IMAGE | rcdc_rcc_desk_strategy_system_disk_has_less_image |
| RCDC_RCC_EXIST_CLASSROOM_USE_IMAGE | rcdc_rcc_exist_classroom_use_image |
| RCDC_RCC_EXIST_CLASSROOM_USE_NETWORK_STRATEGY | rcdc_rcc_exist_classroom_use_network_strategy |
| RCDC_RCC_IMAGE_DESK_STRATEGY_CONFIG_SYSTEM_SIZE_ERROR | rcdc_rcc_image_desk_strategy_config_system_size_error |
| RCDC_RCC_NOT_FIND_IMAGE_FILE | rcdc_rcc_not_find_image_file |

### ClassroomLessonBusinessKey（39）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_CEF_TOKEN_CHECK_FAILURE | rcdc_rcc_classroom_cef_token_check_failure |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC | rcdc_rcc_classroom_ending_class_fail_desc |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_CHANGE_LESSON | rcdc_rcc_classroom_ending_class_fail_desc_for_change_lesson |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_CLASSROOM_IMAGE_NOT_IN_CLASS | rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_CLASSROOM_NOT_IN_CLASS | rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_not_in_class |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_CLASSROOM_NO_SEAT | rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_no_seat |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_NO_CLASSROOM | rcdc_rcc_classroom_ending_class_fail_desc_for_no_classroom |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_NO_IMAGE | rcdc_rcc_classroom_ending_class_fail_desc_for_no_image |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_TEACHER_NOT_IN_CLASS | rcdc_rcc_classroom_ending_class_fail_desc_for_teacher_not_in_class |
| RCDC_RCC_CLASSROOM_GET_CLASS_PROGRESS_FAIL_DESC_FOR_NO_CLASSROOM | rcdc_rcc_classroom_get_class_progress_fail_desc_for_no_classroom |
| RCDC_RCC_CLASSROOM_GET_LESSON_PROGRESS_FAIL_NO_TASK | rcdc_rcc_classroom_get_lesson_progress_fail_no_task |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC | rcdc_rcc_classroom_starting_class_fail_desc |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_AUTO_CLASSROOM_OFF | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_auto_classroom_off |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_CREATING_DESK | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_creating_desk |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_EDITING_DESK | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_editing_desk |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_ENABLE_DESK | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_no_enable_desk |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_ENDING_CLASS | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_ending_class |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_NO_DESK | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_no_desk |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_NO_SEAT | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_no_seat |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_CLASSROOM_STATUS_FORBID | rcdc_rcc_classroom_starting_class_fail_desc_for_classroom_status_forbid |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_END_LAST_LESSON_FAILURE | rcdc_rcc_classroom_starting_class_fail_desc_for_end_last_lesson_failure |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_IMAGE_HIDDEN | rcdc_rcc_classroom_starting_class_fail_desc_for_image_hidden |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_IMAGE_NOT_ASSIGNED | rcdc_rcc_classroom_starting_class_fail_desc_for_image_not_assigned |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_IMAGE_VDI_NO_VGPU_OPTION | rcdc_rcc_classroom_starting_class_fail_desc_for_image_vdi_no_vgpu_option |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_NO_CLASSROOM | rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_NO_IMAGE | rcdc_rcc_classroom_starting_class_fail_desc_for_no_image |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_PLATFORM_UNAVAILABLE | rcdc_rcc_classroom_starting_class_fail_desc_for_platform_unavailable |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_REPEAT_STARTING | rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting |
| RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC_FOR_THE_SAME | rcdc_rcc_classroom_starting_class_fail_desc_for_the_same |
| RCDC_RCC_CLOUDDESKTOP_IMAGE_DELETE_ITEM_FAIL_EXIST_CLASSROOM_IMAGE_REASON | rcdc_rcc_clouddesktop_image_delete_item_fail_exist_classroom_image_reason |
| RCDC_RCC_DESKTOP_START_BATCH_RESULT_HAS_FAIL | rcdc_rcc_desktop_start_batch_result_has_fail |
| RCDC_RCC_DESKTOP_START_ITEM_FAIL_DESC | rcdc_rcc_desktop_start_item_fail_desc |
| RCDC_RCC_DESKTOP_START_ITEM_FAIL_DESC_FOR_NO_SEAT | rcdc_rcc_desktop_start_item_fail_desc_for_no_seat |
| RCDC_RCC_DESKTOP_START_ITEM_IDV_NOTIFY_FAIL_DESC | rcdc_rcc_desktop_start_item_idv_notify_fail_desc |
| RCDC_RCC_DESKTOP_STOP_BATCH_RESULT_HAS_FAIL | rcdc_rcc_desktop_stop_batch_result_has_fail |
| RCDC_RCC_DESKTOP_STOP_ITEM_FAIL_DESC | rcdc_rcc_desktop_stop_item_fail_desc |
| RCDC_RCC_DESKTOP_STOP_ITEM_FAIL_DESC_FOR_NO_SEAT | rcdc_rcc_desktop_stop_item_fail_desc_for_no_seat |
| RCDC_RCC_DESKTOP_STOP_VOI_LESSON_FAIL_DESC | rcdc_rcc_desktop_stop_voi_lesson_fail_desc |
| SPACE_LESSON_PERMISSION_DENIED | space_lesson_permission_denied |

### ClassroomLessonErrorCode（7）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSON_CANNOT_FIND_DESKTOP | 62100002 |
| SPACETCI_LESSON_CANNOT_FIND_IMAGE | 62100001 |
| SPACETCI_LESSON_SHUTDOWN_DESKTOP_SEND_FAIL | 62100005 |
| SPACETCI_LESSON_START_DESKTOP_SEND_FAIL | 62100004 |
| SPACETCI_LESSON_START_TEACHER_DESKTOP_FAIL | 62100006 |
| SPACE_LESSON_GET_TEACHING_CLASS_INFO_FAIL | 62100023 |
| SPACE_LESSON_GET_TEACHING_CLASS_PARAM_FAIL | 62100022 |

### ClassroomResourceErrorCode（2）

| 常量名 | key 值 |
|---|---|
| SPACE_DESKTOP_OPERATE_FAIL | 62100248 |
| SPACE_DISKPOOL_OPTER_FAIL | 62100069 |

### ClassroomStrategyBusinessKey（2）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_STRATEGY_HAS_CLASSROOM_USED | rcdc_rcc_classroom_strategy_has_classroom_used |
| RCDC_RCC_CLASSROOM_STRATEGY_NAME_DUPLICATE | rcdc_rcc_classroom_strategy_name_duplicate |

### CloudDesktopBusinessKey（43）

| 常量名 | key 值 |
|---|---|
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_DELETE_ITEM_FAIL_DESC | rcdc_clouddesktop_rcc_strategy_delete_item_fail_desc |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_DELETE_ITEM_SUCCESS_DESC | rcdc_clouddesktop_rcc_strategy_delete_item_success_desc |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_SINGLE_DELETE_FAIL | rcdc_clouddesktop_rcc_strategy_single_delete_fail |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_SINGLE_DELETE_SUCCESS | rcdc_clouddesktop_rcc_strategy_single_delete_success |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_USED_BY_CLASSROOM | rcdc_clouddesktop_rcc_strategy_used_by_classroom |
| RCDC_RCC_CLASSROOM_CONFIG_DELETE_VDI_DISK_ERROR | rcdc_rcc_classroom_config_delete_vdi_disk_error |
| RCDC_RCC_CLOUDDESKTOP_COMPUTER_NAME_UPDATE_FAIL_ALARM_NAME | rcdc_rcc_clouddesktop_computer_name_update_fail_alarm_name |
| RCDC_RCC_CLOUDDESKTOP_RCC_STRATEGY_NAME_EXIST | rcdc_rcc_clouddesktop_rcc_strategy_name_exist |
| RCDC_RCC_CLOUDDESKTOP_STRATEGY_CLIP_BOARD_SUPPORT_TYPE_NOT_EMPTY | rcdc_rcc_clouddesktop_strategy_clip_board_support_type_not_empty |
| RCDC_RCC_CLOUDDESKTOP_STRATEGY_NOT_EXIST | rcdc_rcc_clouddesktop_strategy_not_exist |
| RCDC_RCC_DELETE_STUDENT_DESK_POOL_ERROR | rcdc_rcc_delete_student_desk_pool_error |
| RCDC_RCC_DELETE_TEACHER_DESK_POOL_ERROR | rcdc_rcc_delete_teacher_desk_pool_error |
| RCDC_RCC_DESKTOP_CREATE_DISK_DESKTOP_TYPE_ERROR | rcdc_rcc_desktop_create_disk_desktop_type_error |
| RCDC_RCC_DESKTOP_CREATE_DISK_ERROR | rcdc_rcc_desktop_create_disk_error |
| RCDC_RCC_DESKTOP_CREATE_DISK_IMAGETEMPLATE_TYPE_ERROR | rcdc_rcc_desktop_create_disk_image_type_error |
| RCDC_RCC_DESKTOP_FORBID_OPTER_BY_BUSINESSTYPE_NOT_RCC | rcdc_rcc_desktop_forbid_opter_by_businesstype_not_rcc |
| RCDC_RCC_DESKTOP_FORCE_WAKE_UP_ITEM_FAIL_DESC | rcdc_rcc_desktop_force_wake_up_item_fail_desc |
| RCDC_RCC_DESKTOP_FORCE_WAKE_UP_SINGLE_FAIL | rcdc_rcc_desktop_force_wake_up_single_fail |
| RCDC_RCC_DESKTOP_OPLOG_USER_START_FAIL | rcdc_rcc_desktop_oplog_user_start_fail |
| RCDC_RCC_DESKTOP_OPLOG_USER_STOP_FAIL | rcdc_rcc_desktop_oplog_user_stop_fail |
| RCDC_RCC_DESKTOP_POWEROFF_ITEM_FAIL_DESC | rcdc_rcc_desktop_poweroff_item_fail_desc |
| RCDC_RCC_DESKTOP_POWEROFF_SINGLE_FAIL | rcdc_rcc_desktop_poweroff_single_fail |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_FAIL | rcdc_rcc_desktop_relieve_fault_fail |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_FAIL_RESULT | rcdc_rcc_desktop_relieve_fault_fail_result |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_SUCCESS | rcdc_rcc_desktop_relieve_fault_success |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_SUCCESS_RESULT | rcdc_rcc_desktop_relieve_fault_success_result |
| RCDC_RCC_DESKTOP_REMOTE_ASSIST_FAIL | rcdc_rcc_desktop_remote_assist_fail |
| RCDC_RCC_DESKTOP_RESTART_ITEM_FAIL_DESC | rcdc_rcc_desktop_restart_item_fail_desc |
| RCDC_RCC_DESKTOP_RESTART_SINGLE_FAIL | rcdc_rcc_desktop_restart_single_fail |
| RCDC_RCC_DESKTOP_RESTORE_FROM_SHINE_ERROR | rcdc_rcc_desktop_restore_from_shine_error |
| RCDC_RCC_DESKTOP_RESTORE_FROM_SHINE_ERROR_DONT_SUPPORT_RCO_DESKTOP | rcdc_rcc_desktop_restore_from_shine_error_dont_support_rco_desktop |
| RCDC_RCC_DESKTOP_REVERT_ITEM_FAIL_DESC | rcdc_rcc_desktop_revert_item_fail_desc |
| RCDC_RCC_DESKTOP_REVERT_SINGLE_FAIL | rcdc_rcc_desktop_revert_single_fail |
| RCDC_RCC_DESKTOP_SHUTDOWN_ITEM_FAIL_DESC | rcdc_rcc_desktop_shutdown_item_fail_desc |
| RCDC_RCC_DESKTOP_SHUTDOWN_SINGLE_FAIL | rcdc_rcc_desktop_shutdown_single_fail |
| RCDC_RCC_RESTORE_VDI_DESKTOP_TASK_FAIL_MSG | rcdc_rcc_restore_vdi_desktop_task_fail_msg |
| RCDC_RCC_RESTORE_VDI_DESKTOP_TASK_SUCCESS_MSG | rcdc_rcc_restore_vdi_desktop_task_success_msg |
| RCDC_RCC_START_DESKTOP_ERROR_DISK_STATE_INACTIVE | rcdc_rcc_start_desktop_error_disk_state_inactive |
| RCDC_RCC_STUDENT_CLOUDDESKTOP_COMPUTER_NAME_UPDATE_FAIL_CONTENT | rcdc_rcc_student_clouddesktop_computer_name_update_fail_content |
| RCDC_RCC_TEACHER_CLOUDDESKTOP_COMPUTER_NAME_UPDATE_FAIL_CONTENT | rcdc_rcc_teacher_clouddesktop_computer_name_update_fail_content |
| RCDC_RCC_USER_DESKTOP_OPLOG_USER_STOP_FAIL | rcdc_rcc_user_desktop_oplog_user_stop_fail |
| RCDC_RCC_VM_WAKE_ERROR_BY_RESOURCE_INSUFFICIENTLY | rcdc_rcc_vm_wake_error_by_resource_insufficiently |
| RCO_CLOUDDESKTOP_RCC_STRATEGY_SYSTEM_DISK_LESS_THEN_OLD | rco_clouddesktop_rcc_strategy_system_disk_less_then_old |

### CmrBusinessKey（12）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CMR_APPLY_LICENSE_FAIL_ALARM_CONTENT | rcdc_rcc_cmr_apply_license_fail_alarm_content |
| RCDC_RCC_CMR_APPLY_LICENSE_FAIL_ALARM_NAME | rcdc_rcc_cmr_apply_license_fail_alarm_name |
| RCDC_RCC_CMR_ERROR_CLASSROOM_IN_LESSON | rcdc_rcc_cmr_error_classroom_in_lesson |
| RCDC_RCC_CMR_ERROR_INFORMATION_FTP_DIR_IS_ILLEGAL | rcdc_rcc_cmr_error_information_ftp_dir_is_illegal |
| RCDC_RCC_CMR_ERROR_INFORMATION_FTP_DIR_IS_NOT_EXISTS | rcdc_rcc_cmr_error_information_ftp_dir_is_not_exists |
| RCDC_RCC_CMR_ERROR_INFORMATION_HAS_NO_CLASSROOM | rcdc_rcc_cmr_error_information_has_no_classroom |
| RCDC_RCC_CMR_ERROR_INFORMATION_IP_BETWEEN_TEACHER_AND_CMR_CHANGE | rcdc_rcc_cmr_error_information_ip_between_teacher_and_cmr_change |
| RCDC_RCC_CMR_ERROR_INFORMATION_SPI_ERROR | rcdc_rcc_cmr_error_information_spi_error |
| RCDC_RCC_FREE_CLASSROOM_ALREADY_EXIST | rcdc_rcc_free_classroom_already_exist |
| RCDC_RCC_FREE_CLASSROOM_NOT_EXIST | rcdc_rcc_free_classroom_not_exist |
| RCDC_RCC_HALO_CHECK_SCORES_NOT_PASSED | rcdc_rcc_halo_check_scores_not_passed |
| RCDC_RCC_NOT_FIND_HALO_CHECK_REPORT | rcdc_rcc_not_find_halo_check_report |

### CmrErrorCode（3）

| 常量名 | key 值 |
|---|---|
| SPACE_CMR_VERSION_FILE_NOT_EXIST_COMPONENT_INFO | 63100002 |
| SPACE_CMR_VERSION_FILE_NOT_FIND | 63100001 |
| SPACE_CMR_VERSION_FILE_NOT_FIND_COMPONENT | 63100003 |

### DataPermissionBusinessKey（1）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_ADMIN_NOT_EXIST | rcdc_rcc_admin_not_exist |

### DesktopStrategyBusinessKey（10）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_CHECK_SUCCESS | rcdc_rcc_classroom_check_success |
| RCDC_RCC_DESKTOP_STRATEGY_ACCOUNT_CHECK_FAIL_TOO_LONG | rcdc_rcc_desktop_strategy_string_check_too_long |
| RCDC_RCC_DESKTOP_STRATEGY_ACCOUNT_CHECK_FAIL_UNAVAILABLE | rcdc_rcc_desktop_strategy_string_check_unavailable |
| RCDC_RCC_DESKTOP_STRATEGY_CUSTOM_DESKTOP_STRATEGY_CAN_NOT_FIND | rcdc_rcc_desktop_strategy_custom_desktop_strategy_find_error |
| RCDC_RCC_DESKTOP_STRATEGY_DATA_DISK_LESS_BEFORE | rcdc_rcc_desktop_strategy_data_disk_less_before |
| RCDC_RCC_DESKTOP_STRATEGY_DATA_DISK_LESS_IMAGE_DISK | rcdc_rcc_desktop_strategy_data_disk_less_image_disk |
| RCDC_RCC_DESKTOP_STRATEGY_GRAPHICS_ADDITION_EMPTY | rcdc_rcc_desktop_strategy_graphics_addition_empty |
| RCDC_RCC_DESKTOP_STRATEGY_IMAGE_INFO_CAN_NOT_FIND | rcdc_rcc_desktop_strategy_image_info_find_error |
| RCDC_RCC_DESKTOP_STRATEGY_SYSTEM_DISK_LESS_BEFORE | rcdc_rcc_desktop_strategy_system_disk_less_before |
| RCDC_RCC_DESKTOP_STRATEGY_SYSTEM_DISK_LESS_IMAGE_DISK | rcdc_rcc_desktop_strategy_system_disk_less_image_disk |

### HaloBusinessKey（7）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CHECK_IMAGE_CMR_VERSION_FAIL | rcdc_rcc_check_image_cmr_version_fail |
| RCDC_RCC_CHECK_IMAGE_CMR_VERSION_FAIL_DUE_TO_NO_VERSION_FILE | rcdc_rcc_check_image_cmr_version_fail_due_to_no_version_file |
| RCDC_RCC_CHECK_SEAT_FAIL | rcdc_rcc_check_seat_msg_fail |
| RCDC_RCC_EXIST_SAME_REPORT | rcdc_rcc_exist_same_report |
| RCDC_RCC_GET_REPORT_SCORES_ERROR | rcdc_rcc_get_report_scores_error |
| RCDC_RCC_REPORT_FORMAT_ERROR | rcdc_rcc_report_format_error |
| RCDC_RCC_REPORT_GET_EMPTY_TEXT | rcdc_rcc_report_get_empty_text |

### HciBusinessKey（1）

| 常量名 | key 值 |
|---|---|
| RCDC_SPACE_CLUSTER_NOT_EXIST_GPU_RESOURCES | rcdc_space_cluster_not_exist_gpu_resources |

### RccGlobalStrategyBusinessKey（4）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_EDIT_GLOBAL_STRATEGY_SUCCESS | rcdc_rcc_edit_global_strategy_success |
| RCDC_RCC_GLOBAL_STRATEGY_ENABLE_CLOUDDESKTOP_OPEN_SUCCESS | rcdc_rcc_global_strategy_enable_clouddesktop_open_success |
| RCDC_RCC_GLOBAL_STRATEGY_IMAGE_AUTO_UPDATE_SUCCESS | rcdc_rcc_global_strategy_image_auto_update_success |
| RCDC_RCC_QUARTZ_CLEAR_INVALID_CLOUD_DESKTOP | rcdc_rcc_quartz_clear_invalid_cloud_desktop |

### RccNetworkBusinessKey（9）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_NETWORK_CHECK_IP_NOT_IN_NETWORK_POOL | 23251320 |
| RCDC_RCC_NETWORK_WHITELIST_END_IP_BROAD_INVALID | rcdc_rcc_network_whitelist_end_ip_broad_invalid |
| RCDC_RCC_NETWORK_WHITELIST_END_IP_NET_INVALID | rcdc_rcc_network_whitelist_end_ip_net_invalid |
| RCDC_RCC_NETWORK_WHITELIST_NOT_EXIST | rcdc_rcc_network_whitelist_not_exist |
| RCDC_RCC_NETWORK_WHITELIST_START_IP_BROAD_INVALID | rcdc_rcc_network_whitelist_start_ip_broad_invalid |
| RCDC_RCC_NETWORK_WHITELIST_START_IP_NET_INVALID | rcdc_rcc_network_whitelist_start_ip_net_invalid |
| RCDC_RCC_SEAT_OPERATE_NETWORK_CREATE_FAIL | rcdc_rcc_seat_operate_network_create_fail |
| RCDC_RCC_SEAT_OPERATE_NETWORK_DELETE_SINGLE_TASK_FAIL | rcdc_rcc_seat_operate_network_delete_single_task_fail |
| RCDC_RCC_SEAT_OPERATE_NETWORK_EDIT_FAIL | rcdc_rcc_seat_operate_network_edit_fail |

### RccSpaceBusinessKey（89）

| 常量名 | key 值 |
|---|---|
| RCC_RESTORE_TCI_DESKTOP_FAIL_NOT_FIND_TERMINAL | rcc_restore_tci_desktop_fail_not_find_terminal |
| RCC_RESTORE_TCI_DESKTOP_TASK_SUCCESS | rcc_restore_tci_desktop_task_success |
| RCDC_RCC_CLASSROOM_POOL_DESKTOP_STARTING_FORBID_BINDUSER | 62100122 |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_FAIL | rcdc_rcc_classroom_pool_update_bind_obj_fail |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_ITEM_FAIL_DESC | rcdc_rcc_classroom_pool_update_bind_obj_item_fail_desc |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_ITEM_SUCCESS_DESC | rcdc_rcc_classroom_pool_update_bind_obj_item_success_desc |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_TASK_FAIL | rcdc_rcc_classroom_pool_update_bind_obj_task_fail |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_TASK_SUCCESS | rcdc_rcc_classroom_pool_update_bind_obj_task_success |
| RCDC_RCC_OFF_IO_OVERLOAD_LIMIT_FAIL | rcdc_rcc_auto_off_io_overload_limit_fail |
| RCDC_RCC_OFF_IO_OVERLOAD_LIMIT_SUCCESS | rcdc_rcc_auto_off_io_overload_limit_success |
| RCDC_RCC_SAPCE_CLASSROOM_POOL_DELETE_ITEM_FAIL_DESC | rcdc_rcc_space_classroom_pool_delete_item_fail_desc |
| RCDC_RCC_SAPCE_CLASSROOM_POOL_FORCE_DELETE_ITEM_FAIL_DESC | rcdc_rcc_space_classroom_pool_force_delete_item_fail_desc |
| RCDC_RCC_SAPCE_POOL_DELETE_ITEM_FAIL_DESC | rcdc_rcc_space_pool_delete_item_fail_desc |
| RCDC_RCC_SAPCE_POOL_FORCE_DELETE_ITEM_FAIL_DESC | rcdc_rcc_space_pool_force_delete_item_fail_desc |
| RCDC_RCC_SPACE_CLASSROOM_POOL_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_classroom_pool_delete_item_success_desc |
| RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_classroom_pool_force_delete_item_success_desc |
| RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_WAKE_FAIL_DESKTOP_STATE_NOT_SATISFIED | rcdc_rcc_space_classroom_pool_force_wake_fail_desktop_state_not_satisfied |
| RCDC_RCC_SPACE_CLASSROOM_POOL_NAME_HAS_EXIST | rcdc_rcc_space_classroom_pool_name_has_exist |
| RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_FAIL_NOT_PUBLISH_IMAGE | rcdc_rcc_space_classroom_pool_publish_fail_not_publish_image |
| RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_FAIL | rcdc_rcc_space_classroom_pool_publish_operate_fail |
| RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_SUCCESS | rcdc_rcc_space_classroom_pool_publish_operate_success |
| RCDC_RCC_SPACE_DESKTOP_HAS_USED_BY_SEAT | rcdc_rcc_space_desktop_has_used_by_seat |
| RCDC_RCC_SPACE_DESKTOP_HAS_USED_BY_USER | rcdc_rcc_space_desktop_has_used_by_user |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_FAIL_DESC | rcdc_rcc_space_desktop_pool_close_maintenance_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_close_maintenance_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_SINGLE_TASK_FAIL | rcdc_rcc_space_desktop_pool_close_maintenance_single_task_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_close_maintenance_single_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_TASK_FAIL | rcdc_rcc_space_desktop_pool_close_maintenance_task_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_close_maintenance_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_SHUTDOWN_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_force_shutdown_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_SHUTDOWN_SINGLE_FAIL | rcdc_rcc_space_desktop_pool_force_shutdown_single_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_force_wake_up_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_FORCE_WAKE_UP_SINGLE_FAIL | rcdc_rcc_space_desktop_pool_force_wake_up_single_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_IN_USE_DELETE_FAIL | rcdc_rcc_space_desktop_pool_in_use_delete_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_FAIL_DESC | rcdc_rcc_space_desktop_pool_open_maintenance_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_open_maintenance_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_SINGLE_TASK_FAIL | rcdc_rcc_space_desktop_pool_open_maintenance_single_task_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_open_maintenance_single_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_TASK_FAIL | rcdc_rcc_space_desktop_pool_open_maintenance_task_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_open_maintenance_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_RESTART_FAIL_NOT_SUPPORT_DESKTOP_TYPE_BATCH_TASK | rcdc_rcc_space_desktop_pool_restart_fail_not_support_desktop_type_batch_task |
| RCDC_RCC_SPACE_DESKTOP_POOL_RESTART_FAIL_NOT_SUPPORT_SLEEP_DESKTOP | rcdc_rcc_space_desktop_pool_restart_fail_not_support_sleep_desktop |
| RCDC_RCC_SPACE_DESKTOP_POOL_RESTART_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_restart_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_RESTART_SINGLE_FAIL | rcdc_rcc_space_desktop_pool_restart_single_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_SHUTDOWN_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_shutdown_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_SHUTDOWN_SINGLE_FAIL | rcdc_rcc_space_desktop_pool_shutdown_single_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_START_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_start_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_START_SINGLE_FAIL | rcdc_rcc_space_desktop_pool_start_single_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_STATE_NOT_READY_DELETE_FAIL | rcdc_rcc_space_desktop_pool_state_not_ready_delete_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_SYNC_CONFIG_ITEM_FAIL_INFO_EMPTY | rcdc_rcc_space_desktop_pool_sync_config_item_fail_info_empty |
| RCDC_RCC_SPACE_DESKTOP_POOL_SYNC_CONFIG_RESULT_FAIL | rcdc_rcc_space_desktop_pool_sync_config_result_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_SYNC_CONFIG_SINGLE_RESULT_FAIL | rcdc_rcc_space_desktop_pool_sync_config_single_result_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_UNAVAILABLE_UPDATE_OBJ_FAIL | rcdc_rcc_space_desktop_pool_unavailable_update_obj_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_ITEM_FAIL_DESC | rcdc_rcc_space_desktop_pool_update_bind_obj_item_fail_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_update_bind_obj_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_TASK_FAIL | rcdc_rcc_space_desktop_pool_update_bind_obj_task_fail |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_update_bind_obj_task_success |
| RCDC_RCC_SPACE_EDIT_NETWORK_IP_INVALID | rcdc_rcc_space_edit_network_ip_invalid |
| RCDC_RCC_SPACE_EDIT_NETWORK_ITEM_FAIL_DESC | rcdc_rcc_space_edit_network_item_fail_desc |
| RCDC_RCC_SPACE_EDIT_NETWORK_SINGLE_RESULT_FAIL | rcdc_rcc_space_edit_network_single_result_fail |
| RCDC_RCC_SPACE_EDIT_STRATEGY_ITEM_FAIL_DESC | rcdc_rcc_space_edit_strategy_item_fail_desc |
| RCDC_RCC_SPACE_EDIT_STRATEGY_SINGLE_RESULT_FAIL | rcdc_rcc_space_edit_strategy_single_result_fail |
| RCDC_RCC_SPACE_POOL_CREATE_OPERATE_FAIL | rcdc_rcc_space_pool_create_operate_fail |
| RCDC_RCC_SPACE_POOL_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_pool_delete_item_success_desc |
| RCDC_RCC_SPACE_POOL_DELETE_SINGLE_TASK_FAIL | rcdc_rcc_space_pool_delete_single_task_fail |
| RCDC_RCC_SPACE_POOL_DELETE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_pool_delete_single_task_success |
| RCDC_RCC_SPACE_POOL_DELETE_TASK_FAIL | rcdc_rcc_space_pool_delete_task_fail |
| RCDC_RCC_SPACE_POOL_DELETE_TASK_SUCCESS | rcdc_rcc_space_pool_delete_task_success |
| RCDC_RCC_SPACE_POOL_EDIT_IMAGE_NOT_EXIST | rcdc_rcc_space_pool_edit_image_not_exist |
| RCDC_RCC_SPACE_POOL_EDIT_POOL_NETWORK_SINGLE_RESULT_FAIL | rcdc_rcc_space_pool_edit_pool_network_single_result_fail |
| RCDC_RCC_SPACE_POOL_EDIT_STRATEGY_FAIL | rcdc_rcc_space_pool_edit_strategy_fail |
| RCDC_RCC_SPACE_POOL_EDIT_STRATEGY_SINGLE_RESULT_FAIL | rcdc_rcc_space_pool_edit_pool_strategy_single_result_fail |
| RCDC_RCC_SPACE_POOL_EXIST_DESKTOP_NO_EDIT_VDI_CONFIG | rcdc_rcc_space_pool_exist_desktop_no_edit_vdi_config |
| RCDC_RCC_SPACE_POOL_FORCE_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_pool_force_delete_item_success_desc |
| RCDC_RCC_SPACE_POOL_IMAGE_EDIT_FAIL | rcdc_rcc_space_pool_image_edit_fail |
| RCDC_RCC_SPACE_POOL_IMAGE_EDIT_TASK_RESULT_FAIL | rcdc_rcc_space_pool_image_edit_task_result_fail |
| RCDC_RCC_SPACE_POOL_IN_USE_DELETE_FAIL | rcdc_rcc_space_pool_in_use_delete_fail |
| RCDC_RCC_SPACE_POOL_NAME_EXIST | rcdc_rcc_space_pool_name_exist |
| RCDC_RCC_SPACE_POOL_NAME_HAS_EXIST | rcdc_rcc_space_pool_name_has_exist |
| RCDC_RCC_SPACE_POOL_NETWORK_EDIT_FAIL | rcdc_rcc_space_pool_network_edit_fail |
| RCDC_RCC_SPACE_POOL_STATIC_EDIT_UPM_FAIL | rcdc_rcc_space_pool_static_edit_upm_fail |
| RCDC_RCC_SPACE_POOL_STATIC_HAS_DESKTOP_DELETE_FAIL | rcdc_rcc_space_pool_static_has_desktop_delete_fail |
| RCDC_RCC_SPACE_POOL_UNAVAILABLE_DELETE_FAIL | rcdc_rco_space_pool_unavailable_delete_fail |
| RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_PUBLISH | rcdc_rcc_space_publish_fail_classroom_has_publish |
| RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_HAS_RUNNING_STATE_MACHINE | rcdc_rcc_space_publish_fail_classroom_has_running_state_machine |
| RCDC_RCC_SPACE_PUBLISH_FAIL_CLASSROOM_NOT_FOUND | rcdc_rcc_space_publish_fail_classroom_not_find |
| RCDC_RCC_SPACE_PUBLISH_FAIL_IMAGETEMPLATE_NOT_ALLOW_NULL | rcdc_rcc_space_publish_fail_imagetemplate_not_allow_null |
| RCDC_RCC_SPACE_PUBLISH_FAIL_IMAGETEMPLATE_NOT_FOUND | rcdc_rcc_space_publish_fail_imagetemplate_not_found |
| RCDC_RCC_TIME_FORMAT_ERROR | rcdc_rcc_time_format_error |

### SeatBusinessKey（51）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_ALARM_TEACHER_TERMINAL_DISK_ERROR_FAIL | rcdc_rcc_alarm_when_teacher_terminal_disk_state_error |
| RCDC_RCC_ALARM_TERMINAL_DISK_ERROR_NAME | rcdc_rcc_alarm_terminal_disk_error_name |
| RCDC_RCC_ALARM_VDI_LOCAL_DISK_ERROR | rcdc_rcc_alarm_vdi_local_disk_error |
| RCDC_RCC_ALARM_VDI_LOCAL_DISK_ERROR_NAME | rcdc_rcc_alarm_vdi_local_disk_error_name |
| RCDC_RCC_ALARM_WHEN_STUDENT_TERMINAL_DISK_STATE_FAIL | rcdc_rcc_alarm_when_student_terminal_disk_state_error |
| RCDC_RCC_IMAGE_OPERATE_UPDATE_LIST_SINGLE_FAIL | rcdc_rcc_image_operate_update_list_single_fail |
| RCDC_RCC_IMAGE_SEAT_OPERATE_DESKTOP_CREATE_SINGLE_FAIL | rcdc_rcc_image_seat_operate_desktop_create_single_fail |
| RCDC_RCC_IMAGE_SEAT_OPERATE_DESKTOP_DELETE_SINGLE_FAIL | rcdc_rcc_image_seat_operate_desktop_delete_single_fail |
| RCDC_RCC_SEAT_CHECK_CAN_END_LESSON | rcdc_rcc_seat_check_can_end_lesson |
| RCDC_RCC_SEAT_CHECK_CLASSROOM_TEACHER_NAME_DUPLICATE | rcdc_rcc_seat_check_classroom_teacher_name_duplicate |
| RCDC_RCC_SEAT_CHECK_TEACHER_NAME_DUPLICATE | rcdc_rcc_seat_check_teacher_name_duplicate |
| RCDC_RCC_SEAT_CLOUDDESKTOP_EXIST_FORBID_DELETE_RELATION | rcdc_rcc_seat_clouddesktop_exist_forbid_delete_relation |
| RCDC_RCC_SEAT_CONFIG_TERMINAL_START_MODE_FAIL | rcdc_rcc_seat_config_terminal_start_mode_fail |
| RCDC_RCC_SEAT_DESK_NO_EXIST_OPTER_FORBID | rcdc_rcc_seat_desk_no_exist_opter_forbid |
| RCDC_RCC_SEAT_IDV_CHECK_EXIST_GATEWAY_CONFLICT | rcdc_rcc_seat_idv_check_exist_gateway_conflict |
| RCDC_RCC_SEAT_IDV_CHECK_GATEWAY_CONFLICT | rcdc_rcc_seat_idv_check_gateway_conflict |
| RCDC_RCC_SEAT_IDV_CHECK_GATEWAY_CONFLICT_WITH_TEACHERIP | rcdc_rcc_seat_idv_check_gateway_conflict_with_teacherip |
| RCDC_RCC_SEAT_KICK_OUT_FAIL | rcdc_rcc_seat_kick_out_fail |
| RCDC_RCC_SEAT_OPERATE_CLASSROOM_FORBID | rcdc_rcc_seat_operate_classroom_forbid |
| RCDC_RCC_SEAT_OPERATE_CREATE_SINGLE_FAIL | rcdc_rcc_seat_operate_create_single_fail |
| RCDC_RCC_SEAT_OPERATE_DESKTOP_CREATE_SINGLE_FAIL | rcdc_rcc_seat_operate_desktop_create_single_fail |
| RCDC_RCC_SEAT_OPERATE_DESKTOP_DELETE_SINGLE_FAIL | rcdc_rcc_seat_operate_desktop_delete_single_fail |
| RCDC_RCC_SEAT_OPERATE_DESKTOP_EDIT_SINGLE_FAIL | rcdc_rcc_seat_operate_desktop_edit_single_fail |
| RCDC_RCC_SEAT_OPERATE_DESKTOP_PROCESS_SINGLE_FAIL | rcdc_rcc_seat_operate_desktop_process_single_fail |
| RCDC_RCC_SEAT_OPERATE_DESKTOP_RESET_SINGLE_FAIL | rcdc_rcc_seat_operate_desktop_reset_single_fail |
| RCDC_RCC_SEAT_OPERATE_DISK_DELETE_SINGLE_FAIL | rcdc_rcc_seat_operate_disk_delete_single_fail |
| RCDC_RCC_SEAT_OPERATE_EDIT_SINGLE_FAIL | rcdc_rcc_seat_operate_edit_single_fail |
| RCDC_RCC_SEAT_OPERATE_SEAT_CREATE_CLASSROOM_FORBID | rcdc_rcc_seat_operate_seat_create_classroom_forbit |
| RCDC_RCC_SEAT_OPERATE_SEAT_DELETE_CLASSROOM_FORBID | rcdc_rcc_seat_operate_seat_delete_classroom_forbit |
| RCDC_RCC_SEAT_OPERATE_SEAT_DESKTOP_RUNNING_FORBID | rcdc_rcc_seat_operate_seat_desktop_running_forbid |
| RCDC_RCC_SEAT_OPERATE_SEAT_EDIT_CLASSROOM_FORBID | rcdc_rcc_seat_operate_seat_edit_classroom_forbit |
| RCDC_RCC_SEAT_ROLE_TYPE_ERROR | rcdc_rcc_seat_role_type_error |
| RCDC_RCC_SEAT_STATE_OPTER_FORBID | rcdc_rcc_seat_state_opter_forbid |
| RCDC_RCC_SEAT_TERMINAL_STATE_OPTRER_FORBID | rcdc_rcc_seat_terminal_state_optrer_forbid |
| RCDC_RCC_SEAT_WAKE_FAIL | rcdc_rcc_seat_wake_fail |
| RCDC_RCC_SEAT_WAKE_FAIL_NOT_FIND_SEAT | rcdc_rcc_seat_wake_fail_not_find_seat |
| RCDC_RCC_SEAT_WAKE_FAIL_NOT_FIND_TERMINAL_IP | rcdc_rcc_seat_wake_fail_not_find_terminal_ip |
| RCDC_RCC_SEAT_WAKE_FAIL_NOT_FIND_TERMINAL_MAC | rcdc_rcc_seat_wake_fail_not_find_terminal_mac |
| RCDC_RCC_SEAT_WAKE_PART_SUCCESS | rcdc_rcc_seat_wake_part_success |
| RCDC_RCC_SEAT_WAKE_SUCCESS | rcdc_rcc_seat_wake_success |
| RCDC_RCC_TEACHER_OPERATE_DESKTOP_CREATE_SINGLE_FAIL | rcdc_rcc_teacher_operate_desktop_create_single_fail |
| RCDC_RCC_TEACHER_OPERATE_DESKTOP_DELETE_SINGLE_FAIL | rcdc_rcc_teacher_operate_desktop_delete_single_fail |
| RCDC_RCC_TEACHER_OPERATE_DESKTOP_PROCESS_SINGLE_FAIL | rcdc_rcc_teacher_operate_desktop_process_single_fail |
| RCDC_RCC_TEACHER_OPERATE_DISK_DELETE_SINGLE_FAIL | rcdc_rcc_teacher_operate_disk_delete_single_fail |
| RCDC_RCC_TEACHER_WAKE_FAIL | rcdc_rcc_teacher_wake_fail |
| RCDC_RCC_TEACHER_WAKE_FAIL_NOT_FIND_TEACHER_IP | rcdc_rcc_teacher_wake_fail_not_find_teacher_ip |
| RCDC_RCC_TEACHER_WAKE_FAIL_NOT_FIND_TEACHER_MAC | rcdc_rcc_teacher_wake_fail_not_find_teacher_mac |
| RCDC_RCC_TEACHER_WAKE_FAIL_TYPE_ERROR | rcdc_rcc_teacher_wake_fail_type_error |
| RCDC_RCC_TEACHER_WAKE_PART_SUCCESS | rcdc_rcc_teacher_wake_part_success |
| RCDC_RCC_TEACHER_WAKE_SUCCESS | rcdc_rcc_teacher_wake_success |
| RCDC_SET_DISK_ALLOCATION_POLICY_FAIL | rcdc_set_disk_allocation_policy_fail |

### SpaceDesktopBusinessKey（9）

| 常量名 | key 值 |
|---|---|
| RCDC_SPACE_DESKTOP_BIND_USER_DESKTOP_INFO_ERROR | 62100071 |
| RCDC_SPACE_DESKTOP_BIND_USER_ERROR_HAD_BIND_OTHER | 62100072 |
| RCDC_SPACE_DESKTOP_BIND_USER_FAIL_USER_NOT_IN_POOL | 62100070 |
| RCDC_SPACE_DESKTOP_POOL_ASSIGN_FAIL | rcdc_space_desktop_pool_assign_fail |
| RCDC_SPACE_DESKTOP_POOL_ASSIGN_FAIL_NAME | rcdc_space_desktop_pool_assign_fail_name |
| RCDC_SPACE_DESKTOP_POOL_NOT_EXIST | 62100074 |
| RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_ERROR | 62100082 |
| RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_USER_NOT_EXIST | 62100080 |
| RCDC_SPACE_DESKTOP_POOL_UPDATE_BIND_VISITOR_FAIL | 62100076 |

### TCIDesktopBusinessKey（5）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_TCI_DESKTOP_REMOTE_ASSIST_FAIL | rcdc_rcc_tci_desktop_remote_assist_fail |
| RCDC_RCC_TCI_DESKTOP_RESTART_ITEM_FAIL_DESC | rcdc_rcc_tci_desktop_restart_item_fail_desc |
| RCDC_RCC_TCI_DESKTOP_RESTART_SINGLE_FAIL | rcdc_rcc_tci_desktop_restart_single_fail |
| RCDC_RCC_TCI_DESKTOP_SHUTDOWN_ITEM_FAIL_DESC | rcdc_rcc_tci_desktop_shutdown_item_fail_desc |
| RCDC_RCC_TCI_DESKTOP_SHUTDOWN_SINGLE_FAIL | rcdc_rcc_tci_desktop_shutdown_single_fail |

### TCILessonImageBusinessKey（3）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSONIMAGE_PERMISSION_DENIED | spacetci_lessonimage_permission_denied |
| SPACETCI_LESSONIMAGE_TEACHER_CREATE_DESKTOP_SINGLE_FAIL | spacetci_lessonimage_teacher_create_desktop_single_fail |
| SPACETCI_LESSONIMAGE_TEACHER_DELETE_DESKTOP_SINGLE_FAIL | spacetci_lessonimage_teacher_delete_desktop_single_fail |

### TCILessonImageErrorCode（5）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSONIMAGE_ALREADY_EXIST_LESSON_IMAGE | 62110028 |
| SPACETCI_LESSONIMAGE_CANNOT_FIND_LESSON_IMAGE | 62110021 |
| SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE | 62110030 |
| SPACETCI_LESSONIMAGE_CANNOT_FIND_TEACHER_IMAGE | 62110029 |
| SPACETCI_LESSONIMAGE_IMAGE_TYPE_ERROR | 62110022 |

### TCILessonStrategyBusinessKey（2）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE | spacetci_lessonstrategy_data_disk_less_before |
| SPACETCI_LESSONSTRATEGY_DATA_DISK_STATUS_NOT_SAME | spacetci_lessonstrategy_data_disk_status_not_same |

### TCILessonStrategyErrorCode（20）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY | 62110011 |
| SPACETCI_LESSONSTRATEGY_CANNOT_FIND_LESSON_STRATEGY_BY_LESSON_IMAGE | 62110010 |
| SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE | 62110008 |
| SPACETCI_LESSONSTRATEGY_DATA_DISK_LESS_BEFORE_WHEN_CREATE | 62110054 |
| SPACETCI_LESSONSTRATEGY_DATA_DISK_STATUS_NOT_SAME | 62110007 |
| SPACETCI_LESSONSTRATEGY_DISK_SIZE_EMPTY | 62110019 |
| SPACETCI_LESSONSTRATEGY_DISK_STRATEGY_EMPTY | 62110012 |
| SPACETCI_LESSONSTRATEGY_PERIOD_EMPTY | 62110015 |
| SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_EMPTY | 62110052 |
| SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_DISK_SIZE_FORBID_SET | 62110050 |
| SPACETCI_LESSONSTRATEGY_PERSONAL_CONFIG_STRATEGY_TYPE_ERROR | 62110051 |
| SPACETCI_LESSONSTRATEGY_SCHEDULE_EXECUTE_TIME_EMPTY | 62110014 |
| SPACETCI_LESSONSTRATEGY_SCHEDULE_TYPE_EMPTY | 62110013 |
| SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_EXIST | 62110003 |
| SPACETCI_LESSONSTRATEGY_STRATEGY_NAME_LENGTH_NOT_EMPTY | 62110016 |
| SPACETCI_LESSONSTRATEGY_STRATEGY_TYPE_ERROR | 62110001 |
| SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM | 62110009 |
| SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM | 62110009 |
| SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE | 62110006 |
| SPACETCI_LESSONSTRATEGY_SYSTEM_DISK_LESS_BEFORE_WHEN_CREATE | 62110053 |

### TeacherOperateBusinessKey（10）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_TEACHER_COMPUTER_NAME_EXIST | rcdc_rcc_classroom_teacher_computer_name_exist |
| RCDC_RCC_CLASSROOM_TEACHER_NOT_EXIST | rcdc_rcc_classroom_teacher_not_exist |
| RCDC_RCC_CMR_CHANGE_TEACHER_IP_SUCCESS | rcdc_rcc_cmr_change_teacher_ip_success |
| RCDC_RCC_TEACHER_CLOUDDESKTOP_EXIST_FORBID_DELETE_RELATION | rcdc_rcc_teacher_clouddesktop_exist_forbid_delete_relation |
| RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_FAIL | rcdc_rcc_teacher_operate_clear_disk_fail |
| RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_SUCCESS | rcdc_rcc_teacher_operate_clear_disk_success |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_CLOSE_FAIL | rcdc_rcc_teacher_operate_terminal_close_fail |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_CLOSE_SUCCESS | rcdc_rcc_teacher_operate_terminal_close_success |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_RESTART_FAIL | rcdc_rcc_teacher_operate_terminal_restart_fail |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_RESTART_SUCCESS | rcdc_rcc_teacher_operate_terminal_restart_success |

### TerminalBusinessKey（23）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_TERMINAL_COMMON_SIMPLE_FAIL | rcdc_rcc_classroom_terminal_common_simple_fail |
| RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND | rcdc_rcc_classroom_terminal_not_find |
| RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND_IP | rcdc_rcc_classroom_terminal_not_find_ip |
| RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND_MAC | rcdc_rcc_classroom_terminal_not_find_mac |
| RCDC_RCC_CLASSROOM_TERMINAL_WAKEUP_FAIL | rcdc_rcc_classroom_terminal_wakeup_fail |
| RCDC_RCC_CLASSROOM_TERMINAL_WAKEUP_TYPE_ERROR | rcdc_rcc_classroom_terminal_wakeup_type_error |
| RCDC_RCC_CLOSE_TERMINAL_UNDEPLOY_FAIL | rcdc_rcc_close_terminal_undeploy_fail |
| RCDC_RCC_ERROR_TERMINAL_PRODUCT | rcdc_rcc_error_terminal_product |
| RCDC_RCC_LOGIN_CANNOT_BE_TEACHER | rcdc_rcc_login_cannot_be_teacher |
| RCDC_RCC_LOGIN_EXPANSION_MODE_ERROR | rcdc_rcc_login_expansion_mode_error |
| RCDC_RCC_LOGIN_EXPANSION_STATE_ERROR | rcdc_rcc_login_expansion_state_error |
| RCDC_RCC_LOGIN_FAILED_NEED_RETRY | rcdc_rcc_login_failed_need_retry |
| RCDC_RCC_LOGIN_LOGIN_FAIL | rcdc_rcc_login_login_fail |
| RCDC_RCC_LOGIN_SUCCESS | rcdc_rcc_login_success |
| RCDC_RCC_LOGIN_TEACHER_STORAGE_ERROR | rcdc_rcc_login_teacher_storage_error |
| RCDC_RCC_LOGIN_UNKNOWN_ERROR | rcdc_rcc_login_unknown_error |
| RCDC_RCC_SEAT_TERMINAL_NOT_FIND_IP | rcdc_rcc_seat_terminal_not_find_ip |
| RCDC_RCC_TERMIANL_ERROR_DRIVER | rcdc_rcc_terminal_error_driver |
| RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL | rcdc_rcc_terminal_init_terminal_fail |
| RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS | rcdc_rcc_terminal_init_terminal_success |
| RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS_HAS_WARN | rcdc_rcc_terminal_init_terminal_success_has_warn |
| RCDC_RCC_TERMINAL_RESTART_SEND_FAIL | rcdc_rcc_terminal_restart_send_fail |
| RCDC_RCC_TERMINAL_RESTART_SEND_SUCCESS | rcdc_rcc_terminal_restart_send_success |

---

### ClassroomBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_ASSIGN_CLASSROOM_STUDENT_IMAGE_FAIL_LOG | rcdc_assign_classroom_student_image_fail_log |
| RCDC_ASSIGN_CLASSROOM_TEACHER_IMAGE_FAIL_NOT_FIND_IMAGE_LOG | rcdc_assign_classroom_teacher_image_fail_not_find_image_log |
| RCDC_RCC_CLASSROOM_DELETING_TEACHER_DESKTOP | rcdc_rcc_classroom_deleting_teacher_desktop |
| RCDC_RCC_CLASSROOM_SEAT_NOT_OPEN_LOCAL_DISK | rcdc_rcc_classroom_seat_not_open_local_disk |
| RCDC_RCC_CLASSROOM_TEACHER_NOT_OPEN_LOCAL_DISK | rcdc_rcc_classroom_teacher_not_open_local_disk |
| RCDC_RCC_SEAT_BATCH_CONFIG_TIME_OUT | rcdc_rcc_seat_batch_config_time_out |
| RCDC_RCC_SEAT_IN_LESSON | rcdc_rcc_seat_in_lesson |
| RCDC_RCC_SEAT_IN_RUNNING | rcdc_rcc_seat_in_running |

### ClassroomImageBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_CLASSROOM_IMAGE_NOT_FOUND | rcdc_rcc_classroom_image_not_found |
| RCDC_RCC_IMAGE_BIND_CLASSROOM_PERSONAL_DESK_STRATEGY | rcdc_rcc_image_bind_classroom_personal_desk_strategy |
| RCDC_RCC_IMAGE_HAS_BE_DELETE | rcdc_rcc_image_has_be_delete |
| RCDC_RCC_IMAGE_STRATEGY_NOT_SAME_TYPE | rcdc_rcc_image_strategy_not_same_type |

### ClassroomLessonBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_CLASSROOM_END_LESSOON_LIMIT_TIME | rcdc_classroom_end_lessoon_limit_time |
| RCDC_RCC_CLASSROOM_ENDING_CLASS_FORCE_DESC_FOR_CLASSROOM_NO_SEAT | rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_seat |
| RCDC_RCC_CLASSROOM_FORCE_ENDING_CLASS_DESC_FOR_PLATFORM_UNAVAILABLE | rcdc_rcc_classroom_force_ending_class_desc_for_platform_unavailable |
| RCDC_RCC_CLASSROOM_START_LESSON_IMAGE_STATE_NOT_ALLOWED | rcdc_rcc_classroom_start_lesson_image_state_not_allowed |
| RCDC_RCC_CLASSROOM_VALIDATE_FORCE_ENDING_CLASS_DESC_FOR_PLATFORM_UNAVAILABLE_CMR | rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_cmr |
| RCDC_RCC_CLASSROOM_VALIDATE_FORCE_ENDING_CLASS_DESC_FOR_PLATFORM_UNAVAILABLE_SERVER | rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_server |

### CloudDesktopBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_DESKTOP_BUSINESS_TYPE_OR_CREATE_SOURCE_NOT_SUPPORT | rcdc_rcc_desktop_business_type_or_create_source_not_support |
| RCDC_RCC_DESKTOP_COLLECT_LOG_ERROR | rcdc_rcc_desktop_collect_log_error |
| RCDC_RCC_DESKTOP_FAULT_NULL | rcdc_rcc_desktop_fault_null |
| RCDC_RCC_DESKTOP_FORCE_WAKE_UP_FAIL_LOG | rcdc_rcc_desktop_force_wake_up_fail_log |
| RCDC_RCC_DESKTOP_NETWORK_IP_CONFLICT_WITH_DESKTOP | rcdc_rcc_desktop_network_ip_conflict_with_desktop |
| RCDC_RCC_DESKTOP_POWEROFF_FAIL_LOG | rcdc_rcc_desktop_poweroff_fail_log |
| RCDC_RCC_DESKTOP_RESTART_FAIL_LOG | rcdc_rcc_desktop_restart_fail_log |
| RCDC_RCC_DESKTOP_SHUTDOWN_FAIL_LOG | rcdc_rcc_desktop_shutdown_fail_log |

### RccSpaceBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCC_RESTORE_TCI_DESKTOP_TASK_DEFAULT_FAIL_LOG | rcc_restore_tci_desktop_task_default_fail_log |

### TCIDesktopBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_TCI_DESKTOP_COLLECT_LOG_FAIL | rcdc_rcc_tci_desktop_collect_log_fail |
| RCDC_RCC_TCI_DESKTOP_RESTART_FAIL_LOG | rcdc_rcc_tci_desktop_restart_fail_log |

### TCILessonImageBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| SPACETCI_LESSONIMAGE_ASSIGN_STUDENT_IMAGE_FAIL_LOG | spacetci_lessonimage_assign_student_image_fail_log |
| SPACETCI_LESSONIMAGE_ASSIGN_STUDENT_IMAGE_SUCCESS_LOG | spacetci_lessonimage_assign_student_image_success_log |
| SPACETCI_LESSONIMAGE_ASSIGN_TEACHER_IMAGE_FAIL_LOG | spacetci_lessonimage_assign_teacher_image_fail_log |
| SPACETCI_LESSONIMAGE_ASSIGN_TEACHER_IMAGE_SUCCESS_LOG | spacetci_lessonimage_assign_teacher_image_success_log |
| SPACETCI_LESSONIMAGE_CHANGE_STUDENT_IMAGE_LESSONSTRATEGY_FAIL_LOG | spacetci_lessonimage_change_student_image_lessonstrategy_fail_log |
| SPACETCI_LESSONIMAGE_CHANGE_STUDENT_IMAGE_LESSONSTRATEGY_SUCCESS_LOG | spacetci_lessonimage_change_student_image_lessonstrategy_success_log |
| SPACETCI_LESSONIMAGE_CHANGE_TEACHER_IMAGE_LESSONSTRATEGY_FAIL_LOG | spacetci_lessonimage_change_teacher_image_lessonstrategy_fail_log |
| SPACETCI_LESSONIMAGE_CHANGE_TEACHER_IMAGE_LESSONSTRATEGY_SUCCESS_LOG | spacetci_lessonimage_change_teacher_image_lessonstrategy_success_log |
| SPACETCI_LESSONIMAGE_DELETE_STUDENT_IMAGE_SUCCESS_LOG | spacetci_lessonimage_delete_student_image_success_log |
| SPACETCI_LESSONIMAGE_DELETE_TEACHER_IMAGE_FAIL_LOG | spacetci_lessonimage_delete_teacher_image_fail_log |
| SPACETCI_LESSONIMAGE_DELETE_TEACHER_IMAGE_SUCCESS_LOG | spacetci_lessonimage_delete_teacher_image_success_log |
| SPACETCI_LESSONIMAGE_HIDE_STUDENT_IMAGE_FAIL_LOG | spacetci_lessonimage_hide_student_image_fail_log |
| SPACETCI_LESSONIMAGE_HIDE_STUDENT_IMAGE_SUCCESS_LOG | spacetci_lessonimage_hide_student_image_success_log |
| SPACETCI_LESSONIMAGE_HIDE_TEACHER_IMAGE_FAIL_LOG | spacetci_lessonimage_hide_teacher_image_fail_log |
| SPACETCI_LESSONIMAGE_HIDE_TEACHER_IMAGE_SUCCESS_LOG | spacetci_lessonimage_hide_teacher_image_success_log |
| SPACETCI_LESSONIMAGE_OPERATE_RUNNING | spacetci_lessonimage_operate_running |
| SPACETCI_LESSONIMAGE_SHOW_STUDENT_IMAGE_FAIL_LOG | spacetci_lessonimage_show_student_image_fail_log |
| SPACETCI_LESSONIMAGE_SHOW_STUDENT_IMAGE_SUCCESS_LOG | spacetci_lessonimage_show_student_image_success_log |
| SPACETCI_LESSONIMAGE_SHOW_TEACHER_IMAGE_FAIL_LOG | spacetci_lessonimage_show_teacher_image_fail_log |
| SPACETCI_LESSONIMAGE_SHOW_TEACHER_IMAGE_SUCCESS_LOG | spacetci_lessonimage_show_teacher_image_success_log |
| SPACETCI_LESSONIMAGE_UPDATE_STUDENT_IMAGE_FAIL_LOG | spacetci_lessonimage_update_student_image_fail_log |
| SPACETCI_LESSONIMAGE_UPDATE_STUDENT_IMAGE_SUCCESS_LOG | spacetci_lessonimage_update_student_image_success_log |
| SPACETCI_LESSONIMAGE_UPDATE_TEACHER_IMAGE_FAIL_LOG | spacetci_lessonimage_update_teacher_image_fail_log |
| SPACETCI_LESSONIMAGE_UPDATE_TEACHER_IMAGE_SUCCESS_LOG | spacetci_lessonimage_update_teacher_image_success_log |

### TeacherOperateBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_TEACHER_COLLECT_LOG_FAIL_LOG | rcdc_rcc_teacher_collect_log_fail_log |
| RCDC_RCC_TEACHER_OPERATE_CLASSROOM_NOT_FOUND | rcdc_rcc_teacher_operate_classroom_not_found |
| RCDC_RCC_TEACHER_OPERATE_CLASSROOM_TERCHER_TERMINAL_ID_IS_NULL | rcdc_rcc_teacher_operate_classroom_tercher_terminal_id_is_null |
| RCDC_RCC_TEACHER_OPERATE_TEACHER_CONFIG_NOT_FOUND | rcdc_rcc_teacher_operate_teacher_config_not_found |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_NOT_FOUND | rcdc_rcc_teacher_operate_terminal_not_found |

### TerminalBusinessKey（补全）

| 常量名 | key 值 |
|---|---|
| RCDC_RCC_TERMINAL_HAVE_NOT_CLOCK | rcdc_rcc_terminal_have_not_clock |
| RCDC_RCC_TERMINAL_NOT_SEAT | rcdc_rcc_terminal_not_seat |
| RCDC_RCC_TERMINAL_NOT_TEACHER | rcdc_rcc_terminal_not_teacher |
| RCDC_RCC_TERMINAL_SHINE_ERROR_GET_SHINE_LOG_FAIL | rcdc_rcc_terminal_shine_error_get_shine_log_fail |
| RCDC_RCC_TERMINAL_UNLOCK_FAIL_LOG | rcdc_rcc_terminal_unlock_fail_log |
| RCDC_RCC_TERMINAL_UNLOCK_TERMINAL_OFFLINE | rcdc_rcc_terminal_unlock_terminal_offline |

## 3. 成功 key

| 常量名 | key 值 |
|---|---|
| CHECK_SUCCESS | rcdc_classroom_check_success |
| CLASSROOM_OPERATE_TIP_SUCCESS | rcdc_classroom_operate_tip_success |
| RCC_RESTORE_TCI_DESKTOP_TASK_SUCCESS | rcc_restore_tci_desktop_task_success |
| RCDC_CLASSROOM_RECORD_LOG_CREATE_SUCCESS | rcdc_classroom_record_log_create_classroom_success |
| RCDC_CLASSROOM_RECORD_LOG_UPDATE_SUCCESS | rcdc_classroom_record_log_update_classroom_success |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_DELETE_ITEM_SUCCESS_DESC | rcdc_clouddesktop_rcc_strategy_delete_item_success_desc |
| RCDC_CLOUDDESKTOP_RCC_STRATEGY_SINGLE_DELETE_SUCCESS | rcdc_clouddesktop_rcc_strategy_single_delete_success |
| RCDC_RCC_CLASSROOM_CHANGE_STUDENT_IMAGE_VERSION_TASK_SUCCESS | rcdc_rcc_classroom_change_student_image_version_task_success |
| RCDC_RCC_CLASSROOM_CHANGE_TEACHER_IMAGE_VERSION_TASK_SUCCESS | rcdc_rcc_classroom_change_teacher_image_version_task_success |
| RCDC_RCC_CLASSROOM_CHECK_SUCCESS | rcdc_rcc_classroom_check_success |
| RCDC_RCC_CLASSROOM_CREATE_TASK_SUCCESS | rcdc_rcc_classroom_create_task_success |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_ITEM_SUCCESS_DESC | rcdc_rcc_classroom_pool_update_bind_obj_item_success_desc |
| RCDC_RCC_CLASSROOM_POOL_UPDATE_BIND_OBJ_TASK_SUCCESS | rcdc_rcc_classroom_pool_update_bind_obj_task_success |
| RCDC_RCC_CLASSROOM_STUDENT_CONFIG_TASK_SUCCESS | rcdc_rcc_classroom_student_config_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_CONFIG_TASK_SUCCESS | rcdc_rcc_classroom_teacher_config_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_END_LESSON_TASK_SUCCESS | rcdc_rcc_classroom_teacher_end_lesson_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_NETWORK_STRATEGY_EDIT_TASK_SUCCESS | rcdc_rcc_classroom_teacher_network_strategy_edit_task_success |
| RCDC_RCC_CLASSROOM_TEACHER_START_LESSON_TASK_SUCCESS | rcdc_rcc_classroom_teacher_start_lesson_task_success |
| RCDC_RCC_CMR_CHANGE_TEACHER_IP_SUCCESS | rcdc_rcc_cmr_change_teacher_ip_success |
| RCDC_RCC_DELETE_OVER_TIME_FREE_CLASSROOM_LOG_SUCCESS | rcdc_rcc_delete_over_time_free_classroom_log_success |
| RCDC_RCC_DESKTOP_COLLECT_LOG_SUCCESS | rcdc_rcc_desktop_collect_log_success |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_SUCCESS | rcdc_rcc_desktop_relieve_fault_success |
| RCDC_RCC_DESKTOP_RELIEVE_FAULT_SUCCESS_RESULT | rcdc_rcc_desktop_relieve_fault_success_result |
| RCDC_RCC_EDIT_GLOBAL_STRATEGY_SUCCESS | rcdc_rcc_edit_global_strategy_success |
| RCDC_RCC_GLOBAL_STRATEGY_ENABLE_CLOUDDESKTOP_OPEN_SUCCESS | rcdc_rcc_global_strategy_enable_clouddesktop_open_success |
| RCDC_RCC_GLOBAL_STRATEGY_IMAGE_AUTO_UPDATE_SUCCESS | rcdc_rcc_global_strategy_image_auto_update_success |
| RCDC_RCC_GLOBAL_STRATEGY_TERMINAL_LOG_CONFIG_SUCCESS | rcdc_rcc_global_strategy_terminal_log_config_success |
| RCDC_RCC_LOGIN_SUCCESS | rcdc_rcc_login_success |
| RCDC_RCC_MODULE_OPERATE_SUCCESS | rcdc_rcc_module_operate_success |
| RCDC_RCC_OFF_IO_OVERLOAD_LIMIT_SUCCESS | rcdc_rcc_auto_off_io_overload_limit_success |
| RCDC_RCC_RESTORE_VDI_DESKTOP_TASK_SUCCESS_MSG | rcdc_rcc_restore_vdi_desktop_task_success_msg |
| RCDC_RCC_SEAT_WAKE_PART_SUCCESS | rcdc_rcc_seat_wake_part_success |
| RCDC_RCC_SEAT_WAKE_SUCCESS | rcdc_rcc_seat_wake_success |
| RCDC_RCC_SPACE_CLASSROOM_POOL_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_classroom_pool_delete_item_success_desc |
| RCDC_RCC_SPACE_CLASSROOM_POOL_FORCE_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_classroom_pool_force_delete_item_success_desc |
| RCDC_RCC_SPACE_CLASSROOM_POOL_PUBLISH_OPERATE_SUCCESS | rcdc_rcc_space_classroom_pool_publish_operate_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_close_maintenance_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_close_maintenance_single_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_CLOSE_MAINTENANCE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_close_maintenance_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_open_maintenance_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_open_maintenance_single_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_OPEN_MAINTENANCE_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_open_maintenance_task_success |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_ITEM_SUCCESS_DESC | rcdc_rcc_space_desktop_pool_update_bind_obj_item_success_desc |
| RCDC_RCC_SPACE_DESKTOP_POOL_UPDATE_BIND_OBJ_TASK_SUCCESS | rcdc_rcc_space_desktop_pool_update_bind_obj_task_success |
| RCDC_RCC_SPACE_POOL_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_pool_delete_item_success_desc |
| RCDC_RCC_SPACE_POOL_DELETE_SINGLE_TASK_SUCCESS | rcdc_rcc_space_pool_delete_single_task_success |
| RCDC_RCC_SPACE_POOL_DELETE_TASK_SUCCESS | rcdc_rcc_space_pool_delete_task_success |
| RCDC_RCC_SPACE_POOL_FORCE_DELETE_ITEM_SUCCESS_DESC | rcdc_rcc_space_pool_force_delete_item_success_desc |
| RCDC_RCC_TCI_DESKTOP_COLLECT_LOG_SUCCESS | rcdc_rcc_tci_desktop_collect_log_success |
| RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_SUCCESS | rcdc_rcc_teacher_operate_clear_disk_success |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_CLOSE_SUCCESS | rcdc_rcc_teacher_operate_terminal_close_success |
| RCDC_RCC_TEACHER_OPERATE_TERMINAL_RESTART_SUCCESS | rcdc_rcc_teacher_operate_terminal_restart_success |
| RCDC_RCC_TEACHER_WAKE_PART_SUCCESS | rcdc_rcc_teacher_wake_part_success |
| RCDC_RCC_TEACHER_WAKE_SUCCESS | rcdc_rcc_teacher_wake_success |
| RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS | rcdc_rcc_terminal_init_terminal_success |
| RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS_HAS_WARN | rcdc_rcc_terminal_init_terminal_success_has_warn |
| RCDC_RCC_TERMINAL_RESTART_SEND_SUCCESS | rcdc_rcc_terminal_restart_send_success |

---

## 4. 状态枚举

> 业务状态字段取值（桌面状态/任务状态/终端状态/下载状态等）。

### ClassroomLessonStatusEnum

`CREATING`, `DELETING`, `EDITING`, `ENDING_CLASS`, `ERROR`, `IN_CLASS`, `NONE_CLASS`, `STARTING_CLASS`

### ClassroomModeEnum

`FREE`, `UNITY`

### ClassroomStrategyState

`AVAILABLE`, `DELETING`

### ClassroomTerminalStateEnum

`OFFLINE`, `ONLINE`

### ClassroomTypeEnum

`COMPUTER_CLASSROOM`, `MEDIA_CLASSROOM`

### DataDiskState

`DISABLE`, `ENABLE`

### DiskHealthState

`FAILED`, `PASSED`, `PREFAILURE`

### DiskState

`ERROR`, `NEW`, `READY`

### ImageDownloadStateEnum

`DOWNLOADING`, `FAIL`, `SUCCESS`, `WAIT_DOWNLOAD`

### LocalDiskTypeEnum

`PERSONAL`, `RECOVERABLE`

### MessageBoxDialogBtnTypeEnum

`CONFIRM`

### NetStateEnum

`DISABLE_NETWORK`, `ENABLE_NETWORK`

### RccDesktopPoolStatisticsTypeEnum

`AVG_USED_RATE`, `MAX_USED_RATE`

### SeatDownloadStateEnum

`FAIL`, `LOADING`, `SUCCESS`

### SeatPageQueryTypeEnum

`QUERY_BY_CLASSROOM`, `QUERY_BY_OVERVIEW`

### SpaceStrategyGroupState

`AVAILABLE`, `DELETING`

### TCIScheduleTypeEnum

`CUSTOM`, `DAY`, `EVERYTIME`, `MONTH`, `NO_RECOVER`, `WEEK`

### TerminalTypeEnum

`APP`, `IDV`, `NONE`, `PC`, `UNKNOWN`, `VDI`, `VOI`

### TerminalWhiteTypeEnum

`RG_CT3100C_G2`, `RG_CT3100L_G2`, `RG_CT5200`, `RG_CT5200C_G3`, `RG_CT5200C_G4`, `RG_CT5200S`, `RG_CT5300`, `RG_CT5300C`, `RG_CT5300C_CS`, `RG_CT5300C_G3`, `RG_CT5300C_G4`, `RG_CT5302C_G4`, `RG_CT5320`, `RG_CT5320S`, `RG_CT5330S`, `RG_CT5500C_CS`, `RG_CT5500C_G3`, `RG_CT5500C_G4`, `RG_CT5502C_G3`, `RG_CT5502C_G4`, `RG_CT5530S`, `RG_CT5702C_G3`, `RG_CT5702C_G4`, `RG_CT6200`, `RG_CT6200C_G3`, `RG_CT6200C_G4`, `RG_CT6300`, `RG_CT6300C_G3`, `RG_CT6300C_G4`, `RG_CT6300S`, `RG_CT6500`, `RG_CT6500C_G3`, `RG_CT6500C_G4`, `RG_RAIN305_256`, `RG_RAIN_305E`, `RG_RAIN_310E128`, `RG_RAIN_310E500HD`, `RG_RAIN_320T`, `RG_RAIN_410E128`, `RG_RAIN_410E500HD`

---

## 5. 日志/审计 key

> 审计日志记录用（`_LOG` 结尾），**非 HTTP 响应 msgKey**，自动化一般不断言。

共 213 个，按类分布：

- ClassroomBusinessKey: 59 个
- ClassroomImageBusinessKey: 10 个
- ClassroomLessonBusinessKey: 4 个
- ClassroomStrategyBusinessKey: 5 个
- CloudDesktopBusinessKey: 15 个
- CmrBusinessKey: 1 个
- RccGlobalStrategyBusinessKey: 2 个
- RccNetworkBusinessKey: 9 个
- RccSpaceBusinessKey: 24 个
- SeatBusinessKey: 21 个
- TCIDesktopBusinessKey: 5 个
- TCILessonImageBusinessKey: 32 个
- TeacherOperateBusinessKey: 8 个
- TerminalBusinessKey: 18 个
