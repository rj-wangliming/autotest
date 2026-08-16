#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split merged response.body fields (name with '/') into per-field entries."""
import os

DOCS = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"

def fld(name, type_, desc):
    return f"    {name}:\n      type: {type_}\n      description: {desc}"

RULES = {
"rcc_classroom_getInfo.md": [
("""    terminalTotalNum/terminalOnlineNum:
      type: Integer
      description: 终端总数/在线数""",
 fld("terminalTotalNum","Integer","终端总数") + "\n" + fld("terminalOnlineNum","Integer","终端在线数")),
("""    desktopTotalNum/desktopOnlineNum:
      type: Integer
      description: 桌面总数/在线数""",
 fld("desktopTotalNum","Integer","桌面总数") + "\n" + fld("desktopOnlineNum","Integer","桌面在线数")),
("""    studentImageNum/studentImageStorageSize:
      type: Integer
      description: 学生机镜像数量/镜像存储大小""",
 fld("studentImageNum","Integer","学生机镜像数量") + "\n" + fld("studentImageStorageSize","Integer","学生机镜像存储大小")),
],
"rcc_classroom_image_list.md": [
("""    itemArr/items:
      type: ClassroomImageCardInfoDTO[]
      description: 镜像卡片列表，元素含 id/imageName/teaImage/hide/canUpdate/cbbImageType""",
 fld("itemArr","ClassroomImageCardInfoDTO[]","镜像卡片列表（位于 content 下：$.content.itemArr），元素含 id/imageName/teaImage/hide/canUpdate/cbbImageType")),
],
"rcc_classroom_teacher_getInfo.md": [
("""    teacherMac/teacherCpuType/teacherMemory/teacherDiskSize/teacherSystemSize/teacherImageNum:
      type: String/Long/Integer
      description: 教师机硬件与镜像信息""",
 fld("teacherMac","String","教师机MAC") + "\n" + fld("teacherCpuType","String","教师机CPU型号") + "\n" +
 fld("teacherMemory","Long","教师机内存") + "\n" + fld("teacherDiskSize","Long","教师机磁盘大小") + "\n" +
 fld("teacherSystemSize","Long","教师机系统盘大小") + "\n" + fld("teacherImageNum","Integer","教师机镜像数量")),
],
"rcc_classroom_teacher_terminal_collectLog_download.md": [
("""    fileName/suffix:
      type: String
      description: 取自 CbbTerminalLogFileInfoDTO.logFileName/suffix""",
 fld("fileName","String","取自 CbbTerminalLogFileInfoDTO.logFileName") + "\n" + fld("suffix","String","取自 CbbTerminalLogFileInfoDTO.suffix")),
],
"rcc_space_desktop_detail.md": [
("""    desktopName/computerName/desktopState/desktopType/ip:
      type: 多种
      description: 继承 CloudDesktopDetailDTO 的桌面基础详情""",
 fld("desktopName","String","桌面名称（继承 CloudDesktopDetailDTO）") + "\n" + fld("computerName","String","计算机名（继承 CloudDesktopDetailDTO）") + "\n" +
 fld("desktopState","CbbCloudDeskState","桌面状态（继承 CloudDesktopDetailDTO）") + "\n" + fld("desktopType","CbbCloudDeskPattern","桌面类型（继承 CloudDesktopDetailDTO）") + "\n" +
 fld("desktopIp","String","桌面IP（继承 CloudDesktopDetailDTO）")),
],
"space_cluster_obtainComputeClusterList.md": [
("""    totalCpu/usedCpu:
      type: long
      description: 总/已用 CPU 核数""",
 fld("totalCpu","long","总 CPU 核数") + "\n" + fld("usedCpu","long","已用 CPU 核数")),
("""    totalMemory/usedMemory:
      type: long
      description: 总/已用内存 MB""",
 fld("totalMemory","long","总内存 MB") + "\n" + fld("usedMemory","long","已用内存 MB")),
("""    platformId/platformName/platformType/platformStatus:
      type: mixed
      description: 所属平台信息""",
 fld("platformId","UUID","所属平台ID") + "\n" + fld("platformName","String","所属平台名称") + "\n" +
 fld("platformType","String","所属平台类型") + "\n" + fld("platformStatus","String","所属平台状态")),
],
"space_storagePool_list.md": [
("""    id/storagePoolId:
      type: UUID
      description: 存储池 id""",
 fld("id","UUID","存储池 id") + "\n" + fld("storagePoolId","UUID","存储池 id（storagePoolId）")),
("""    totalCapacity/usedCapacity:
      type: Long
      description: 总/已用容量""",
 fld("totalCapacity","Long","总容量") + "\n" + fld("usedCapacity","Long","已用容量")),
("""    storagePoolMgmtState/storagePoolHealthState:
      type: enum
      description: 管理/健康状态""",
 fld("storagePoolMgmtState","enum","存储池管理状态") + "\n" + fld("storagePoolHealthState","enum","存储池健康状态")),
("""    platformId/platformName/platformType/platformStatus:
      type: mixed
      description: 所属平台信息""",
 fld("platformId","UUID","所属平台ID") + "\n" + fld("platformName","String","所属平台名称") + "\n" +
 fld("platformType","String","所属平台类型") + "\n" + fld("platformStatus","String","所属平台状态")),
],
"space_strategygroup_vdi_condition_list.md": [
("""    cpu/memory:
      type: Integer
      description: CPU 核数/内存 MB""",
 fld("cpu","Integer","CPU 核数") + "\n" + fld("memory","Integer","内存 MB")),
("""    vgpuType/vgpuExtraInfo:
      type: VgpuType/String
      description: vGPU 配置""",
 fld("vgpuType","VgpuType","vGPU 类型") + "\n" + fld("vgpuExtraInfo","String","vGPU 额外信息")),
],
}

for fname, rules in RULES.items():
    path = os.path.join(DOCS, fname)
    text = open(path, encoding="utf-8").read()
    for old, new in rules:
        cnt = text.count(old)
        if cnt != 1:
            print(f"FAIL count={cnt} {fname} :: {old.split(chr(10))[0][:40]}")
            continue
        text = text.replace(old, new)
    open(path, "w", encoding="utf-8").write(text)
    print(f"OK {fname}")
