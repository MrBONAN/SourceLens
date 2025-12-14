import ast
import sys
import os

from code_analyzer.data_models import (
    BaseCodeElement, FunctionDefinition, ClassDefinition, BaseCodeModule,
    Parameter, ImportInfo, SourceSpan
)


class NodeHandler:
    def __init__(self, file_path: str, attributes: set[str]):
        self.file_path = file_path
        self.attributes_to_process = attributes

    def create_model(self, node: ast.AST, parent_id: str) -> BaseCodeElement:
        start_line = getattr(node, 'lineno', 1)
        end_line = getattr(node, 'end_lineno', start_line)

        return BaseCodeElement(
            name=getattr(node, 'name', 'unknown'),
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=start_line,
                end_line=end_line
            )
        )

    def process(self, node: ast.AST, parent_id: str, context: dict[str, BaseCodeElement]) -> BaseCodeElement:
        raise NotImplementedError

    @staticmethod
    def _get_full_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{NodeHandler._get_full_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{NodeHandler._get_full_name(node.value)}[]"
        elif isinstance(node, ast.Call):
            return f"{NodeHandler._get_full_name(node.func)}()"
        return "unknown_call"


class FunctionDefHandler(NodeHandler):
    def process(self, node: ast.FunctionDef, parent_id: str, context: dict[str, BaseCodeElement]) -> FunctionDefinition:
        func_def = FunctionDefinition(
            name=node.name,
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno
            )
        )
        if 'decorator_list' in self.attributes_to_process:
            func_def.decorator_list = DecoratorsHandler.handle(node)
            if 'outgoing_calls' in self.attributes_to_process:
                func_def.outgoing_calls.extend(func_def.decorator_list)

        if 'parameters' in self.attributes_to_process:
            func_def.parameters = [Parameter(name=arg.arg) for arg in node.args.args]

        if 'outgoing_calls' in self.attributes_to_process:
            self._collect_calls(node, func_def)

        return func_def

    def _collect_calls(self, node: ast.FunctionDef, func_model: FunctionDefinition):
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func

                if isinstance(func, ast.Name):
                    call_name = func.id
                    func_model.outgoing_calls.append(call_name)
                    func_model.outgoing_func_calls.append(call_name)


                elif isinstance(func, ast.Attribute):
                    full_name = self._get_full_name(func)

                    func_model.outgoing_calls.append(full_name)
                    func_model.outgoing_method_calls.append(full_name)

        func_model.outgoing_calls = sorted(list(set(func_model.outgoing_calls)))
        func_model.outgoing_func_calls = sorted(list(set(func_model.outgoing_func_calls)))
        func_model.outgoing_method_calls = sorted(list(set(func_model.outgoing_method_calls)))


class ClassDefHandler(NodeHandler):
    def process(self, node: ast.ClassDef, parent_id: str, context: dict[str, BaseCodeElement]) -> ClassDefinition:
        class_def = ClassDefinition(
            name=node.name,
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno
            )
        )

        if 'decorator_list' in self.attributes_to_process:
            class_def.decorator_list = DecoratorsHandler.handle(node)

        if 'base_classes' in self.attributes_to_process:
            class_def.unresolved_base_classes = [self._get_full_name(base) for base in node.bases]

        return class_def


class ImportHandler(NodeHandler):
    def __init__(self, project_root: str, file_path: str, attributes: set[str]):
        super().__init__(file_path, attributes)

        self.project_root = os.path.abspath(project_root)
        self.std_lib = sys.stdlib_module_names

    def process(self, node: ast.Import | ast.ImportFrom, parent_id: str, context: dict[str, BaseCodeElement]):
        module_model = context.get(parent_id)

        if isinstance(module_model, BaseCodeModule):
            current_path = module_model.source_span.file_path

            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_path = self._resolve_local_path(alias.name, 0, current_path)
                    module_model.imports.append(
                        ImportInfo(module=alias.name, alias=alias.asname, is_local=bool(local_path), path=local_path)
                    )
            elif isinstance(node, ast.ImportFrom):
                local_path = self._resolve_local_path(node.module, node.level, current_path)
                for alias in node.names:
                    module_model.imports.append(
                        ImportInfo(module=node.module, name=alias.name, alias=alias.asname, level=node.level,
                                   is_local=bool(local_path), path=local_path)
                    )
        return None

    def _resolve_local_path(self, module_name: str | None, level: int, current_file_path: str | None) -> str | None:
        if not module_name and level == 0:
            return None

        search_dirs = []

        if level == 0:
            root_module = module_name.split('.')[0]
            if root_module in self.std_lib:
                return None

            search_dirs.append(self.project_root)

            project_folder_name = os.path.basename(self.project_root)
            if root_module == project_folder_name:
                search_dirs.append(os.path.dirname(self.project_root))
        else:
            if not current_file_path:
                return None
            current_dir = os.path.dirname(current_file_path)
            for _ in range(level - 1):
                current_dir = os.path.dirname(current_dir)
            search_dirs.append(current_dir)

        parts = module_name.split('.') if module_name else []

        if not parts:
            relative_path = ""
        else:
            relative_path = os.path.join(*parts) # type: ignore

        for base_dir in search_dirs:
            candidate_base = str(os.path.join(base_dir, relative_path)) # type: ignore

            if os.path.isdir(candidate_base) and os.path.exists(os.path.join(candidate_base, "__init__.py")):
                return candidate_base

            candidate_file = candidate_base + ".py"
            if os.path.isfile(candidate_file):
                return candidate_file

            if os.path.isdir(candidate_base):
                return candidate_base

        return None


class DecoratorsHandler:
    @staticmethod
    def handle(node: ast.AST) -> list[str]:
        decorators = getattr(node, 'decorator_list', [])
        if not decorators:
            return []

        decorator_list = []
        for decorator in decorators:
            if isinstance(decorator, ast.Name):
                decorator_list.append(decorator.id)
        return decorator_list