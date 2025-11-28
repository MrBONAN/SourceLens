import ast
from typing import Set, Dict, List, Set as TypingSet
from code_analyzer.data_models import (
    BaseCodeElement, FunctionDefinition, ClassDefinition, BaseCodeModule,
    Parameter, ImportInfo, SourceSpan, CallReference
)


class NodeHandler:
    def __init__(self, file_path: str, attributes: Set[str]):
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

    def process(self, node: ast.AST, parent_id: str, context: Dict[str, BaseCodeElement]) -> BaseCodeElement:
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
    def process(self, node: ast.FunctionDef, parent_id: str, context: Dict[str, BaseCodeElement]) -> FunctionDefinition:
        func_def = FunctionDefinition(
            name=node.name,
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno
            )
        )
        if 'parameters' in self.attributes_to_process:
            func_def.parameters = [Parameter(name=arg.arg) for arg in node.args.args]

        if 'outgoing_calls' in self.attributes_to_process:
            calls = []
            for stmt in node.body:
                calls.extend(self._extract_calls_from_node(stmt))
            func_def.outgoing_calls = sorted(list(set(calls)))
            call_sites = []
            for stmt in node.body:
                call_sites.extend(self._collect_call_sites(stmt))
            func_def.call_sites = call_sites

        parent_model = context.get(parent_id)
        if isinstance(parent_model, ClassDefinition):
            attribute_types = self._collect_self_attribute_types(node)
            for attr_name, types in attribute_types.items():
                existing = set(parent_model.attribute_types.get(attr_name, []))
                parent_model.attribute_types[attr_name] = sorted(existing.union(types))

        return func_def

    def _extract_calls_from_node(self, node: ast.AST) -> List[str]:
        calls = []
        if isinstance(node, ast.Call):
            call_info = self._analyze_call_context(node)
            calls.extend(call_info)
        for child in ast.iter_child_nodes(node):
            calls.extend(self._extract_calls_from_node(child))
        return calls

    def _analyze_call_context(self, call_node: ast.Call) -> List[str]:
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

    def _collect_call_sites(self, node: ast.AST) -> List[CallReference]:
        call_sites: List[CallReference] = []
        if isinstance(node, ast.Call):
            expression = self._describe_expression(node.func)
            line = getattr(node.func, 'lineno', node.lineno)
            column = getattr(node.func, 'col_offset', node.col_offset)
            call_sites.append(CallReference(expression=expression, line=line, column=column))
        for child in ast.iter_child_nodes(node):
            call_sites.extend(self._collect_call_sites(child))
        return call_sites

    def _describe_expression(self, node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return f"{self._describe_expression(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Call):
            return self._describe_expression(node.func)
        return self._get_full_name(node)

    def _collect_self_attribute_types(self, node: ast.FunctionDef) -> Dict[str, TypingSet[str]]:
        attribute_types: Dict[str, TypingSet[str]] = {}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                targets = child.targets
                value = child.value
            elif isinstance(child, ast.AnnAssign):
                targets = [child.target]
                value = child.value
            else:
                continue

            if value is None:
                continue

            inferred_types = self._infer_types_from_value(value)
            if not inferred_types:
                continue

            for target in targets:
                attr_name = self._extract_self_attribute_name(target)
                if not attr_name:
                    continue
                attribute_types.setdefault(attr_name, set()).update(inferred_types)

        return attribute_types

    def _extract_self_attribute_name(self, target: ast.AST) -> str | None:
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
            return target.attr
        return None

    def _infer_types_from_value(self, value: ast.AST) -> TypingSet[str]:
        inferred: TypingSet[str] = set()
        if isinstance(value, ast.Call):
            func = value.func
            if isinstance(func, ast.Name):
                inferred.add(func.id)
            elif isinstance(func, ast.Attribute):
                inferred.add(self._get_full_name(func))
        return inferred


class ClassDefHandler(NodeHandler):
    def process(self, node: ast.ClassDef, parent_id: str, context: Dict[str, BaseCodeElement]) -> ClassDefinition:
        class_def = ClassDefinition(
            name=node.name,
            parent_id=parent_id,
            source_span=SourceSpan(
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno
            )
        )
        if 'base_classes' in self.attributes_to_process:
            class_def.unresolved_base_classes = [self._get_full_name(base) for base in node.bases]

        return class_def


class ImportHandler(NodeHandler):
    def process(self, node: ast.Import | ast.ImportFrom, parent_id: str, context: Dict[str, BaseCodeElement]):
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
