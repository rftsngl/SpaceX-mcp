"""JSON şemasını MCP formatına dönüştüren modül."""

import json

schema = json.load(open('latest_launch_schema.json', encoding='utf-8'))

mcp = {
  "endpoints": [
    {
      "name": "get_latest_launch",
      "method": "GET",
      "path": "/v5/launches/latest",
      "requestSchema": {},
      "responseSchema": schema
    }
  ]
}

with open('mcp_latest_launch.json', 'w', encoding='utf-8') as f:
    json.dump(mcp, f, ensure_ascii=False, indent=2)
print('mcp_latest_launch.json oluşturuldu.')
