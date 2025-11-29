import ast

# from code_analyzer.ast_parser.decorators_handler import DecoratorsHandler
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
    def process(self, node: ast.Import | ast.ImportFrom, parent_id: str, context: dict[str, BaseCodeElement]):
        module_model = context.get(parent_id)
        if isinstance(module_model, BaseCodeModule):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_model.imports.append(
                        ImportInfo(module=alias.name, alias=alias.asname)
                    )
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    module_model.imports.append(
                        ImportInfo(module=node.module, name=alias.name, alias=alias.asname, level=node.level)
                    )
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
