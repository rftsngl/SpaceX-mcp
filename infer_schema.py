"""JSON verilerinden şema çıkaran modül."""

import json
from genson import SchemaBuilder

with open('latest_launch.json', encoding='utf-8') as f:
    example = json.load(f)

builder = SchemaBuilder()
builder.add_object(example)
schema = builder.to_schema()

with open('latest_launch_schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)
print('latest_launch_schema.json oluşturuldu.')
