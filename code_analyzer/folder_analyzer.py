from pathlib import Path
from typing import Dict, List, Optional
from .ast_parser.processor import AstProcessor
from .data_models import BaseCodeElement, BaseCodeModule, ClassDefinition, FunctionDefinition, ImportInfo


class FolderAnalyzer:
    def __init__(self, config: Dict[str, List[str]]):
        self.config = config
        self.all_models: Dict[str, BaseCodeElement] = {}
        self.module_mapping: Dict[str, str] = {}

    def analyze_folder(self, folder_path: str,
                       include_patterns: Optional[List[str]] = None,
                       exclude_patterns: Optional[List[str]] = None) -> Dict[str, BaseCodeElement]:
        if include_patterns is None:
            include_patterns = ['*.py']
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '*.pyc', '*.pyo', '*.pyd']

        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Папка {folder_path} не найдена")

        root_module = BaseCodeModule(
            name=folder_path.name,
            source_span=None
        )
        self.all_models[root_module.id] = root_module

        python_files = self._find_python_files(folder_path, include_patterns, exclude_patterns)

        for file_path in python_files:
            try:
                self._analyze_file(file_path, root_module.id)
            except Exception:
                continue

        self._resolve_cross_file_references()

        return self.all_models

    def _find_python_files(self, folder_path: Path,
                           include_patterns: List[str],
                           exclude_patterns: List[str]) -> List[Path]:
        python_files = []

        for pattern in include_patterns:
            for file_path in folder_path.rglob(pattern):
                if not self._should_exclude_file(file_path, exclude_patterns):
                    python_files.append(file_path)

        return sorted(python_files)

    def _should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        file_str = str(file_path)
        for pattern in exclude_patterns:
            if pattern in file_str or file_path.match(pattern):
                return True
        return False

    def _analyze_file(self, file_path: Path, parent_module_id: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    source_code = f.read()
            except UnicodeDecodeError:
                return

        processor = AstProcessor(str(file_path), self.config.get('process_nodes', {}))
        file_models = processor.process_file(source_code)

        for model_id, model in file_models.items():
            if isinstance(model, BaseCodeModule):
                model.parent_id = parent_module_id
                self.all_models[parent_module_id].children_ids.append(model_id)

            self.all_models[model_id] = model

        module_id = next(iter(file_models.keys()))
        self.module_mapping[str(file_path)] = module_id

    def get_file_dependencies(self) -> Dict[str, List[str]]:
        dependencies = {}

        for file_path, module_id in self.module_mapping.items():
            module = self.all_models.get(module_id)
            if not isinstance(module, BaseCodeModule):
                continue

            imported_files = []
            for import_info in module.imports:
                if import_info.module:
                    imported_file = self._find_imported_file(import_info.module)
                    if imported_file:
                        imported_files.append(imported_file)

            dependencies[file_path] = imported_files

        return dependencies

    def _find_imported_file(self, module_name: str) -> Optional[str]:
        for file_path in self.module_mapping.keys():
            if module_name in file_path or file_path.endswith(f"{module_name}.py"):
                return file_path
        return None

    def _resolve_cross_file_references(self):
        global_class_map = self._build_global_class_map()

        self._resolve_base_classes(global_class_map)

        self._resolve_function_calls(global_class_map)

    def _build_global_class_map(self) -> Dict[str, str]:
        class_map = {}
        for model_id, model in self.all_models.items():
            if isinstance(model, ClassDefinition):
                class_map[model.name] = model_id

                module = self._find_module_for_element(model)
                if module:
                    full_name = f"{module.name}.{model.name}"
                    class_map[full_name] = model_id

                if model.source_span and model.source_span.file_path:
                    file_name = Path(model.source_span.file_path).stem
                    file_class_name = f"{file_name}.{model.name}"
                    class_map[file_class_name] = model_id

        return class_map

    def _find_module_for_element(self, element: BaseCodeElement) -> Optional[BaseCodeModule]:
        current = element
        while current.parent_id:
            parent = self.all_models.get(current.parent_id)
            if isinstance(parent, BaseCodeModule):
                return parent
            current = parent
        return None

    def _resolve_base_classes(self, global_class_map: Dict[str, str]):
        for model_id, model in self.all_models.items():
            if isinstance(model, ClassDefinition):
                resolved_bases = []
                for base_name in model.unresolved_base_classes:
                    base_id = self._find_base_class_id(base_name, global_class_map, model)
                    if base_id:
                        model.base_classes[base_name] = base_id
                        resolved_bases.append(base_name)

                for base_name in resolved_bases:
                    model.unresolved_base_classes.remove(base_name)

    def _find_base_class_id(self, base_name: str, global_class_map: Dict[str, str],
                            current_class: ClassDefinition) -> Optional[str]:
        if base_name in global_class_map:
            return global_class_map[base_name]

        module = self._find_module_for_element(current_class)
        if module:
            for import_info in module.imports:
                if import_info.name == base_name:
                    imported_module_id = self._find_imported_module_id(import_info)
                    if imported_module_id:
                        imported_module = self.all_models.get(imported_module_id)
                        if isinstance(imported_module, BaseCodeModule):
                            for child_id in imported_module.children_ids:
                                child = self.all_models.get(child_id)
                                if isinstance(child, ClassDefinition) and child.name == base_name:
                                    return child_id

        if '.' in base_name:
            parts = base_name.split('.')
            if len(parts) == 2:
                module_name, class_name = parts
                full_name = f"{module_name}.{class_name}"
                if full_name in global_class_map:
                    return global_class_map[full_name]

        return None

    def _find_imported_module_id(self, import_info: ImportInfo) -> Optional[str]:
        if not import_info.module:
            return None

        for file_path, module_id in self.module_mapping.items():
            if import_info.module in file_path or file_path.endswith(f"{import_info.module}.py"):
                return module_id
        return None

    def _resolve_function_calls(self, global_class_map: Dict[str, str]):
        global_function_map = self._build_global_function_map()

        for model_id, model in self.all_models.items():
            if isinstance(model, FunctionDefinition):
                resolved_calls = []
                for call_name in model.outgoing_calls:
                    resolved_id = self._find_function_id(call_name, global_function_map, model)
                    if resolved_id:
                        resolved_calls.append(resolved_id)
                model.outgoing_calls = sorted(list(set(resolved_calls)))

    def _build_global_function_map(self) -> Dict[str, str]:
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

    def _find_function_id(self, call_name: str, global_function_map: Dict[str, str],
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
