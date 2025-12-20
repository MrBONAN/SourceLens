import json
from dataclasses import fields
from enum import Enum
from typing import Optional

from code_analyzer.data_models import JsonElement, Folder, BaseCodeModule, ClassDefinition, FunctionDefinition, \
    ErrorsList, AstParsingError


class JsonConverter:
    @classmethod
    def dump(cls, all_models: dict[str, JsonElement], config) -> str:
        output: dict[str, dict[str, object]] = {}
        for element in all_models.values():
            output[element.id] = cls._dump_obj(element, config)

        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, Enum):
                    return o.value
                if hasattr(o, '__dict__'):
                    return o.__dict__
                return str(o)

        return json.dumps(output, indent=2, cls=CustomJSONEncoder)

    @classmethod
    def _dump_obj(cls, element: JsonElement, config) -> JsonElement | dict:
        element_type = cls._get_type(element)
        settings = config.get(element_type, {})
        if element_type is None or "all" in settings:
            return element

        exclude = set(settings.get("exclude") or []) if type(settings) is dict else []
        fields_to_select = []
        for field_to_select in settings:
            if type(field_to_select) is str and field_to_select != 'exclude':
                fields_to_select.append(field_to_select)
        if len(fields_to_select) == 0:
            fields_to_select = [pair.name
                                for pair in fields(element)
                                if pair.name not in exclude]

        obj: dict[str, object] = {}
        for field in fields_to_select:
            value = getattr(element, field, None)
            if value is not None:
                if type(value) is list:
                    obj[field] = [cls._dump_obj(item, config) for item in value]
                elif cls._get_type(value):
                    obj[field] = cls._dump_obj(value, config)
                else:
                    obj[field] = value
        return obj

    @classmethod
    def _get_type(cls, element: JsonElement) -> Optional[str]:
        if isinstance(element, Folder):
            return "Folder"
        if isinstance(element, BaseCodeModule):
            return "File"
        if isinstance(element, ClassDefinition):
            return "Class"
        if isinstance(element, FunctionDefinition):
            return "Function"
        if isinstance(element, ErrorsList):
            return "ErrorsList"
        if isinstance(element, AstParsingError):
            return "AstParsingError"
        return None
