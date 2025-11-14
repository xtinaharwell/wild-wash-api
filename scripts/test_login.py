import requests
import json

URL = 'http://wildwash.kibeezy.com/users/login/'
PAYLOAD = {"username": "0769760460", "password": "collins879@"}

try:
    r = requests.post(URL, json=PAYLOAD, timeout=10)
    print('STATUS:', r.status_code)
    try:
        print('BODY:', json.dumps(r.json(), indent=2))
    except Exception:
        print('BODY:', r.text)
    print('HEADERS:', dict(r.headers))
except Exception as e:
    print('ERROR:', e)
