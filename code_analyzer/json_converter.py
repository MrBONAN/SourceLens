from dataclasses import fields
from typing import Optional

from code_analyzer.data_models import JsonElement, Folder, BaseCodeModule, ClassDefinition, FunctionDefinition


class JsonConverter:
    @classmethod
    def dump(cls, all_models: dict[str, JsonElement], config) -> dict[str, dict[str, object]]:
        output: dict[str, dict[str, object]] = {}
        for id, element in all_models.items():
            type = cls._get_type(element)
            if type is not None:
                if "all" in config[type]:
                    output[id] = element
                    continue

                exclude = set(config[type].get("exclude") or [])
                fields_to_select = []
                for field_to_select in config[type]:
                    if field_to_select is str:
                        fields_to_select.append(field_to_select)
                if len(fields_to_select) == 0:
                    fields_to_select = list(pair.name for pair in fields(element))

                obj: dict[str, object] = {}
                for field in fields_to_select:
                    if field in exclude:
                        continue
                    value = getattr(element, field, None)
                    if value is not None:
                        obj[field] = value
                output[id] = obj
        return output

    @staticmethod
    def _get_type(element: JsonElement) -> Optional[str]:
        if isinstance(element, Folder):
            return "Folder"
        if isinstance(element, BaseCodeModule):
            return "File"
        if isinstance(element, ClassDefinition):
            return "Class"
        if isinstance(element, FunctionDefinition):
            return "Function"
        return None
