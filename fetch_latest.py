"""SpaceX API'den en son fırlatma verilerini çeken modül."""

import json
import requests

resp = requests.get('https://api.spacexdata.com/v5/launches', timeout=30)
resp.raise_for_status()
with open('latest_launch.json', 'w', encoding='utf-8') as f:
    json.dump(resp.json(), f, ensure_ascii=False, indent=2)
print('latest_launch.json oluşturuldu.')
