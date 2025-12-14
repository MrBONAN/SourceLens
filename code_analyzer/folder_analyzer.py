from pathlib import Path
from typing import Optional
from code_analyzer.folder_reader import FolderReader
from .data_models import BaseCodeElement, BaseCodeModule, ClassDefinition, FunctionDefinition, JsonElement
from .hierarchy_resolver import HierarchyResolver


class FolderAnalyzer:
    def __init__(self, config: dict[str, list[str]]):
        self.config = config
        self.all_models: dict[str, JsonElement] = {}
        self.module_mapping: dict[str, str] = {}

    def analyze_folder(self, folder_path: Path) -> dict[str, JsonElement]:
        reader = FolderReader(self.config)
        reader.read_folder(folder_path)

        self.all_models = reader.all_models
        self.module_mapping = reader.module_mapping

        self._resolve_cross_file_references()
        return self.all_models

    def _resolve_cross_file_references(self):
        resolver = HierarchyResolver(self.all_models)
        resolver.resolve_all()

        self._resolve_function_calls()

    def _resolve_function_calls(self):
        for model_id, model in self.all_models.items():
            if isinstance(model, FunctionDefinition):
                module = self._find_module_for_element(model)
                if not module:
                    continue

                resolved_ids = []

                for call_name in model.outgoing_calls:
                    target_id = self._resolve_single_call(call_name, model, module)
                    if target_id:
                        resolved_ids.append(target_id)

                model.outgoing_calls = sorted(list(set(resolved_ids)))

    def _resolve_single_call(self, call_name: str, current_func: FunctionDefinition, module: BaseCodeModule) -> \
            Optional[str]:

        if call_name.startswith("self."):
            method_name = call_name.split(".")[1]
            parent_class = self.all_models.get(current_func.parent_id)
            if isinstance(parent_class, ClassDefinition):
                return self._find_method_in_class_hierarchy(parent_class, method_name)
            return None
        local_id = self._find_in_module_children(module, call_name)
        if local_id:
            return local_id

        parts = call_name.split('.')
        base_name = parts[0]

        for imp in module.imports:
            import_alias = imp.alias or imp.name or imp.module

            if import_alias == base_name and imp.module_id:
                target_module = self.all_models.get(imp.module_id)
                if not isinstance(target_module, BaseCodeModule):
                    continue

                if len(parts) == 1:
                    if imp.name:
                        return self._find_in_module_children(target_module, imp.name)

                elif len(parts) > 1:
                    child_name = parts[1]
                    return self._find_in_module_children(target_module, child_name)

        return None

    def _find_method_in_class_hierarchy(self, class_def: ClassDefinition, method_name: str) -> Optional[str]:
        method_id = self._find_child_by_name(class_def, method_name)
        if method_id:
            return method_id

        for base_name, base_id in class_def.base_classes.items():
            base_class = self.all_models.get(base_id)
            if isinstance(base_class, ClassDefinition):
                found_id = self._find_method_in_class_hierarchy(base_class, method_name)
                if found_id:
                    return found_id
        return None

    def _find_in_module_children(self, module: BaseCodeModule, name: str) -> Optional[str]:
        return self._find_child_by_name(module, name)

    def _find_child_by_name(self, parent: JsonElement, name: str) -> Optional[str]:
        for child_id in parent.children_ids:
            child = self.all_models.get(child_id)
            if child and child.name == name:
                return child.id
        return None

    def _find_module_for_element(self, element: BaseCodeElement) -> Optional[BaseCodeModule]:
        current = element
        while current and current.parent_id:
            parent = self.all_models.get(current.parent_id)
            if isinstance(parent, BaseCodeModule):
                return parent
            current = parent
        return None