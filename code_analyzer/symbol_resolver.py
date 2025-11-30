from typing import Optional

from code_analyzer.data_models import (
    BaseCodeModule, CodeElementType, JsonElement
)


class SymbolResolver:
    def __init__(self, all_models: dict[str, JsonElement]):
        self.all_models = all_models

    def resolve_symbol(self, name: str, context_file_id: str, expected_type: Optional[CodeElementType] = None) -> \
            Optional[str]:
        context_module = self.all_models.get(context_file_id)
        if not isinstance(context_module, BaseCodeModule):
            return None

        if '.' in name:
            parts = name.split('.', 1)
            head = parts[0]
            tail = parts[1]
        else:
            head = name
            tail = None

        head_element_id = self._resolve_head(head, context_module)

        if not head_element_id:
            return None

        if tail:
            start_element = self.all_models.get(head_element_id)
            found_id = self._resolve_deeply(start_element, tail)
        else:
            found_id = head_element_id

        if found_id and expected_type:
            found_element = self.all_models.get(found_id)
            if not found_element or found_element.element_type != expected_type:
                return None

        return found_id

    def _resolve_head(self, name: str, context_module: BaseCodeModule) -> Optional[str]:
        local_child = self._find_child_by_name(context_module, name)
        if local_child:
            return local_child.id

        for imp in context_module.imports:
            current_import_name = imp.alias if imp.alias else imp.name

            if current_import_name == name:
                if imp.module_id and imp.is_local:
                    target_module = self.all_models.get(imp.module_id)
                    if isinstance(target_module, BaseCodeModule):
                        if imp.name:
                            child = self._find_child_by_name(target_module, imp.name)
                            if child:
                                return child.id
                        else:
                            return target_module.id

            if not imp.name and (imp.alias == name or imp.module == name):
                if imp.module_id:
                    return imp.module_id

        return None

    def _resolve_deeply(self, start_element: JsonElement, path: str) -> Optional[str]:
        if not path:
            return start_element.id

        parts = path.split('.', 1)
        current_step = parts[0]
        remaining_path = parts[1] if len(parts) > 1 else None

        child = self._find_child_by_name(start_element, current_step)
        if child:
            return self._resolve_deeply(child, remaining_path)

        if isinstance(start_element, BaseCodeModule):
            for imp in start_element.imports:
                import_name = imp.alias if imp.alias else imp.name
                check_name = import_name or imp.module
                if check_name == current_step and imp.module_id and imp.is_local:
                    target_module = self.all_models.get(imp.module_id)
                    if target_module:
                        return self._resolve_deeply(target_module, remaining_path)
        return None

    def _find_child_by_name(self, parent: JsonElement, name: str) -> Optional[JsonElement]:
        for child_id in parent.children_ids:
            child = self.all_models.get(child_id)
            if child and child.name == name:
                return child
        return None
