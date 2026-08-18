import yaml

text = open('docs/api_md_staging/business_rules.md', encoding='utf-8').read()
parts = text.split("---\n", 2)
print('Parts count:', len(parts))
fm_text = parts[1]
print('Front-matter starts with:', fm_text[:100])
fm = yaml.safe_load(fm_text)
print('auto_provision in fm:', 'auto_provision' in fm)
print('resource_chains in fm:', 'resource_chains' in fm)

if 'auto_provision' in fm:
    print('\nidempotent_create:')
    for item in fm['auto_provision']['idempotent_create']:
        print('  ', item['resource_type'])
    print('force_create:')
    for item in fm['auto_provision']['force_create']:
        print('  ', item['resource_type'])
