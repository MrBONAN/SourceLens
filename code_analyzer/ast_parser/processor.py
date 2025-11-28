import ast
from typing import Dict, Type, List
from code_analyzer.data_models import BaseCodeElement, BaseCodeModule, SourceSpan, ClassDefinition, FunctionDefinition
from .handlers import NodeHandler, FunctionDefHandler, ClassDefHandler, ImportHandler


class AstProcessor(ast.NodeVisitor):
    def __init__(self, file_path: str, config: Dict[str, List[str]]):
        self.file_path = file_path
        self.result_models: Dict[str, BaseCodeElement] = {}
        self.context_stack: List[str] = []
        self.handler_factory = self._create_handler_factory(config)

    def _create_handler_factory(self, config: Dict[str, List[str]]) -> Dict[Type[ast.AST], NodeHandler]:
        factory = {}
        node_map = {
            "ClassDef": (ast.ClassDef, ClassDefHandler),
            "FunctionDef": (ast.FunctionDef, FunctionDefHandler),
            "Import": (ast.Import, ImportHandler),
            "ImportFrom": (ast.ImportFrom, ImportHandler),
        }
        for node_name, attributes in config.items():
            if node_name in node_map:
                ast_class, handler_class = node_map[node_name]
                factory[ast_class] = handler_class(self.file_path, set(attributes))
        return factory

    def process_file(self, source_code: str) -> Dict[str, BaseCodeElement]:
        tree = ast.parse(source_code)

        module_name = self.file_path.split('/')[-1].split('.')[0]
        module_element = BaseCodeModule(
            name=module_name,
            source_span=SourceSpan(file_path=self.file_path, start_line=1, end_line=len(source_code.splitlines()))
        )
        self.result_models[module_element.id] = module_element
        self.context_stack.append(module_element.id)

        self.visit(tree)

        self.context_stack.pop()
        self._post_process()
        return self.result_models

    def generic_visit(self, node: ast.AST):
        node_type = type(node)
        handler = self.handler_factory.get(node_type)

        is_new_context = False

        if handler:
            parent_id = self.context_stack[-1]
            new_model = handler.process(node, parent_id, self.result_models)

            if new_model:
                self.result_models[new_model.id] = new_model
                parent_model = self.result_models[parent_id]
                parent_model.children_ids.append(new_model.id)

                if isinstance(new_model, (ClassDefinition, FunctionDefinition)):
                    self.context_stack.append(new_model.id)
                    is_new_context = True

        super().generic_visit(node)

        if is_new_context:
            self.context_stack.pop()

    def _post_process(self):
        class_name_to_id_map: Dict[str, str] = {
            model.name: model.id
            for model in self.result_models.values()
            if isinstance(model, ClassDefinition)
        }

        for model_id, model in self.result_models.items():
            if isinstance(model, ClassDefinition):
                handler_config = self.handler_factory.get(ast.ClassDef)

                if handler_config and 'base_classes' in handler_config.attributes_to_process:
                    resolved_bases = []
                    for base_name in model.unresolved_base_classes:
                        base_id = class_name_to_id_map.get(base_name)
                        if base_id:
                            model.base_classes[base_name] = base_id
                            resolved_bases.append(base_name)
                    
                    for base_name in resolved_bases:
                        model.unresolved_base_classes.remove(base_name)
