import sys
sys.path.insert(0, 'D:/tools/autotest')

import requests, time
from app.core.aes_crypto import encrypt

resp = requests.post(
    'https://10.51.167.250:8443/rcdc/rco/admin/loginAdmin',
    json={
        'userName': 'admin9',
        'pwd': encrypt("Aa123456", "ADMINPASSWORDKEY"),
        'captchaCode': '',
        'captchaKey': '',
        'timestamp': int(time.time() * 1000),
    },
    verify=False
)
print('Login status:', resp.status_code)
print('Login response:', resp.text[:500])
