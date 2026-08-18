import sys
sys.path.insert(0, 'D:/tools/autotest')
from app.core.orchestrator import Orchestrator

o = Orchestrator()
rules_text = o._build_auto_provision_rules_text()
print("=== auto_provision rules text ===")
print(rules_text)
