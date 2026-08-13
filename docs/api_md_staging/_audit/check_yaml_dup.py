#!/usr/bin/env python3
"""Detect duplicate keys in md front-matter YAML at any nesting level."""
import sys, re, yaml

class DupLoader(yaml.SafeLoader):
    pass

FOUND = []

def check_dup(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            FOUND.append(f"line {key_node.start_mark.line + 1}: duplicate key '{key}'")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping

DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, check_dup)

for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        print(f"{path}: NO FRONT-MATTER FOUND")
        continue
    FOUND.clear()
    try:
        yaml.load(m.group(1), Loader=DupLoader)
    except Exception as e:
        print(f"{path}: YAML PARSE ERROR: {e}")
        continue
    if FOUND:
        print(f"{path}:")
        for f in FOUND:
            print(f"  ❌ {f}")
    else:
        print(f"{path}: OK (no duplicate keys)")
