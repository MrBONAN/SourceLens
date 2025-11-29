from pathlib import Path
from typing import Optional
from code_analyzer.folder_reader import FolderReader
from .data_models import BaseCodeElement, BaseCodeModule, ClassDefinition, FunctionDefinition, ImportInfo, JsonElement
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

        # self._resolve_function_calls()

    def _find_module_for_element(self, element: BaseCodeElement) -> Optional[BaseCodeModule]:
        current = element
        while current.parent_id:
            parent = self.all_models.get(current.parent_id)
            if isinstance(parent, BaseCodeModule):
                return parent
            current = parent
        return None

    def _find_imported_module_id(self, import_info: ImportInfo) -> Optional[str]:
        if not import_info.module:
            return None

        for file_path, module_id in self.module_mapping.items():
            if import_info.module in file_path or file_path.endswith(f"{import_info.module}.py"):
                return module_id
        return None

    def _resolve_function_calls(self):
        global_function_map = self._build_global_function_map()

        for model_id, model in self.all_models.items():
            if isinstance(model, FunctionDefinition):
                resolved_calls = []
                for call_name in model.outgoing_calls:
                    resolved_id = self._find_function_id(call_name, global_function_map, model)
                    if resolved_id:
                        resolved_calls.append(resolved_id)
                model.outgoing_calls = sorted(list(set(resolved_calls)))

    def _build_global_function_map(self) -> dict[str, str]:
        function_map = {}
        for model_id, model in self.all_models.items():
            if isinstance(model, FunctionDefinition):
                function_map[model.name] = model_id

                parent = self.all_models.get(model.parent_id)
                if isinstance(parent, ClassDefinition):
                    class_method_name = f"{parent.name}.{model.name}"
                    function_map[class_method_name] = model_id
                    function_map[f"self.{model.name}"] = model_id

                module = self._find_module_for_element(model)
                if module:
                    full_name = f"{module.name}.{model.name}"
                    function_map[full_name] = model_id

        return function_map

    def _find_function_id(self, call_name: str, global_function_map: dict[str, str],
                          current_function: FunctionDefinition) -> Optional[str]:
        if call_name in global_function_map:
            return global_function_map[call_name]

        if call_name.startswith("self."):
            method_name = call_name[5:]
            current_class = self._find_class_for_function(current_function)
            if current_class:
                method_id = self._find_method_in_class(current_class, method_name)
                if method_id:
                    return method_id
                for base_name, base_id in current_class.base_classes.items():
                    base_class = self.all_models.get(base_id)
                    if isinstance(base_class, ClassDefinition):
                        method_id = self._find_method_in_class(base_class, method_name)
                        if method_id:
                            return method_id

        module = self._find_module_for_element(current_function)
        if module:
            for import_info in module.imports:
                if import_info.name == call_name:
                    return self._find_function_in_imported_module(import_info, call_name)

                if import_info.alias == call_name:
                    return self._find_function_in_imported_module(import_info, import_info.name)

        if '.' in call_name:
            parts = call_name.split('.')
            if len(parts) == 2:
                object_name, method_name = parts
                for model_id, model in self.all_models.items():
                    if isinstance(model, ClassDefinition) and model.name == object_name:
                        method_id = self._find_method_in_class(model, method_name)
                        if method_id:
                            return method_id

        return None

    def _find_class_for_function(self, function: FunctionDefinition) -> Optional[ClassDefinition]:
        parent = self.all_models.get(function.parent_id)
        if isinstance(parent, ClassDefinition):
            return parent
        return None

    def _find_method_in_class(self, class_def: ClassDefinition, method_name: str) -> Optional[str]:
        for child_id in class_def.children_ids:
            child = self.all_models.get(child_id)
            if isinstance(child, FunctionDefinition) and child.name == method_name:
                return child_id
        return None

    def _find_function_in_imported_module(self, import_info: ImportInfo, function_name: str) -> Optional[str]:
        imported_module_id = self._find_imported_module_id(import_info)
        if imported_module_id:
            imported_module = self.all_models.get(imported_module_id)
            if isinstance(imported_module, BaseCodeModule):
                for child_id in imported_module.children_ids:
                    child = self.all_models.get(child_id)
                    if isinstance(child, FunctionDefinition) and child.name == function_name:
                        return child_id
        return None
