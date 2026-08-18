import requests, json

# Use Flask to run a simple plan that queries VDI strategies
plan = {
    "steps": [
        {
            "step_name": "login",
            "name": "login",
            "api": "/rco/admin/loginAdmin",
            "method": "POST",
            "body": {"userName": {"value": "${param.userName}"}, "pwd": {"value": "${param.pwd}"}},
            "extract": {"token": "$.content.token"},
            "_section": "pre"
        },
        {
            "step_name": "get_vdi_strategy",
            "api": "/space/strategygroup/vdi/list",
            "method": "POST",
            "body": {"page": {"value": 0}, "limit": {"value": 20}},
            "extract": {"vdiStrategyId": "$.content.itemArr[0].id"}
        }
    ],
    "assertions": [{"type": "status", "expect": "SUCCESS"}]
}

resp = requests.post(
    'http://127.0.0.1:5001/api/cases/run',
    json={
        "plan": plan,
        "params": {"userName": "admin9", "pwd": "Aa123456"},
        "use_case": "test",
        "env": "https://10.51.167.250:8443/rcdc"
    },
    timeout=30
)

print(json.dumps(resp.json(), indent=2, ensure_ascii=False)[:2000])
