import json
from dataclasses import is_dataclass
from enum import Enum

EXCLUDE_FIELDS = {
    'call_sites',
    'attribute_types'
}

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if is_dataclass(o):
            data = o.__dict__.copy()

            for field_name in EXCLUDE_FIELDS:
                data.pop(field_name, None)

            return data
        if hasattr(o, '__dict__'):
            return o.__dict__
        return super().default(o)