# -*- coding: utf-8 -*-
import yaml, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from transform_setup import transform_frontmatter

STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
samples = sys.argv[1:] if len(sys.argv) > 1 else [
    'rcc_classroom_desktop_restart.md',
    'rcc_classroom_network_disable.md',
    'rcc_classroom_lesson_start.md',
    'rcc_classroom_editStudentInfo.md',
    'rcc_classroom_select.md',
    'rcc_classroom_list.md',
    'rcc_classroom_create.md',
]
for f in samples:
    txt = open(os.path.join(STAGE, f), encoding='utf-8').read()
    new_txt, a, b, notes, changed = transform_frontmatter(txt)
    if not changed:
        print('##### %s (unchanged)' % f)
        continue
    idx2 = new_txt.index('\n---')
    d = yaml.safe_load(new_txt[3:idx2])
    print('##### %s  A=%d B=%d' % (f, a, b))
    print(yaml.safe_dump(d.get('setup'), allow_unicode=True, sort_keys=False))
