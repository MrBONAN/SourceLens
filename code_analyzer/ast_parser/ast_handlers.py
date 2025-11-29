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
        return BaseCodeElement(
            name=getattr(node, 'name', 'unknown'),
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=getattr(node, 'end_lineno', node.lineno)
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

        if 'parameters' in self.attributes_to_process:
            func_def.parameters = [Parameter(name=arg.arg) for arg in node.args.args]

        if 'outgoing_calls' in self.attributes_to_process:
            calls = []
            for stmt in node.body:
                calls.extend(self._extract_calls_from_node(stmt))
            func_def.outgoing_calls = sorted(list(set(calls)))

        return func_def

    def _extract_calls_from_node(self, node: ast.AST) -> list[str]:
        calls = []
        # TODO может быть такая ситуация, что вызов внутри другого вызова. Было бы славно это "умно" обрабатывать
        # например,
        if isinstance(node, ast.Call):
            call_info = self._analyze_call_context(node)
            calls.extend(call_info)
        for child in ast.iter_child_nodes(node):
            calls.extend(self._extract_calls_from_node(child))
        return calls

    def _analyze_call_context(self, call_node: ast.Call) -> list[str]:
        calls = []
        func = call_node.func

        if isinstance(func, ast.Name):
            calls.append(func.id)

        elif isinstance(func, ast.Attribute):
            calls.append(func.attr)
            calls.append(f"{self._get_object_name(func.value)}.{func.attr}")

            if isinstance(func.value, ast.Name) and func.value.id == 'self':
                calls.append(f"self.{func.attr}")

        elif isinstance(func, ast.Call):
            calls.append(self._get_full_name(func))

        return calls

    def _get_object_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_object_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return f"{self._get_object_name(node.func)}()"
        else:
            return "unknown"


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
        relative_path = os.path.join(*parts)

        for base_dir in search_dirs:
            candidate_base = str(os.path.join(base_dir, relative_path))

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
        if getattr(node, 'decorator_list', None) is None:
            return []
        decorator_list = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_list.append(decorator.id)
        return decorator_list
