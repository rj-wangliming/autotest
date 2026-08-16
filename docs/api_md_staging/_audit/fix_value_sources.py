#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add value/generated_by source to required request.body fields that lack one (skill rule #31)."""
import os

DOCS = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"

# (filename, field_name, old_description_line, new_block_tail)
# We insert the source line right after the description line.
FIXES = [
    # studentModeArr -> generated_by: config_generator
    ("rcc_classroom_batchCheckDesktopNameDuplicate.md", "studentModeArr",
     "      description: 学生机工作模式数组（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    ("rcc_classroom_editStudentInfo.md", "studentModeArr",
     "      description: 学生机类型数组（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    ("rcc_classroom_seat_batchCheckDesktopIpDuplicate.md", "studentModeArr",
     "      description: 学生机工作模式（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    ("rcc_classroom_seat_batchConfig.md", "studentModeArr",
     "      description: 学生机工作模式（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    ("rcc_classroom_seat_checkStudentDesktopIpDuplicate.md", "studentModeArr",
     "      description: 学生机工作模式（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    ("rcc_classroom_seat_edit.md", "studentModeArr",
     "      description: 学生机工作模式数组（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）",
     "      generated_by: config_generator"),
    # action -> fixed value
    ("rcc_classroom_image_student_delete.md", "action",
     "      description: 动作", "      value: 4"),
    ("rcc_classroom_image_student_hide.md", "action",
     "      description: 动作", "      value: 2"),
    ("rcc_classroom_image_student_show.md", "action",
     "      description: 动作", "      value: 3"),
    ("rcc_classroom_image_student_update.md", "action",
     "      description: 动作", "      value: 1"),
    ("rcc_classroom_image_teacher_delete.md", "action",
     "      description: 动作", "      value: 4"),
    ("rcc_classroom_image_teacher_hide.md", "action",
     "      description: 动作", "      value: 2"),
    ("rcc_classroom_image_teacher_show.md", "action",
     "      description: 动作", "      value: 3"),
    ("rcc_classroom_image_teacher_update.md", "action",
     "      description: 动作", "      value: 1"),
]

report = []
for fname, field, desc_line, src_line in FIXES:
    path = os.path.join(DOCS, fname)
    text = open(path, encoding="utf-8").read()
    if text.count(desc_line) != 1:
        report.append((fname, field, f"FAIL count={text.count(desc_line)}"))
        continue
    new = desc_line + "\n" + src_line
    text = text.replace(desc_line, new)
    open(path, "w", encoding="utf-8").write(text)
    report.append((fname, field, "OK"))

for fname, field, st in report:
    print(f"{st:6s} {fname} :: {field}")
