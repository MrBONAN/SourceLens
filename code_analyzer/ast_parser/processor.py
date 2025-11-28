import ast
from typing import Dict, Type, List
from code_analyzer.data_models import BaseCodeElement, BaseCodeModule, SourceSpan, ClassDefinition, FunctionDefinition
from .handlers import FunctionDefHandler, ClassDefHandler, ImportHandler


class AstProcessor(ast.NodeVisitor):
    def __init__(self, file_path: str, config: Dict[str, List[str]]):
        self.file_path = file_path
        self.result_models: Dict[str, BaseCodeElement] = {}
        self.context_stack: List[str] = []
        self._init_handlers(config)

    def _init_handlers(self, config: Dict[str, List[str]]):
        self.class_handler = ClassDefHandler(self.file_path, set(config["ClassDef"]))
        self.func_handler = FunctionDefHandler(self.file_path, set(config["FunctionDef"]))
        self.import_handler = ImportHandler(self.file_path, set(config["Import"] + config["ImportFrom"]))

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
        # self._post_process() # TODO сделать потом?
        return self.result_models

    def visit_ClassDef(self, node: ast.ClassDef):
        parend_id = self.context_stack[-1]
        model = self.class_handler.process(node, parend_id, self.result_models)

        self._add_model(parend_id, model)
        self.context_stack.append(model.id)
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parend_id = self.context_stack[-1]
        model = self.func_handler.process(node, parend_id, self.result_models)

        self._add_model(parend_id, model)
        self.context_stack.append(model.id)
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_Import(self, node: ast.Import):
        parend_id = self.context_stack[-1]
        self.import_handler.process(node, parend_id, self.result_models)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        parend_id = self.context_stack[-1]
        self.import_handler.process(node, parend_id, self.result_models)
        self.generic_visit(node)

    def _add_model(self, parent_id: str, model: BaseCodeElement):
        self.result_models[model.id] = model
        self.result_models[parent_id].children_ids.append(model.id)

    def _post_process(self):
        class_name_to_id_map: Dict[str, str] = {
            model.name: model.id
            for model in self.result_models.values()
            if isinstance(model, ClassDefinition)
        }

        for model_id, model in self.result_models.items():
            if isinstance(model, ClassDefinition):
                if 'base_classes' in self.class_handler.attributes_to_process:
                    resolved_bases = []
                    for base_name in model.unresolved_base_classes:
                        base_id = class_name_to_id_map.get(base_name)
                        if base_id:
                            model.base_classes[base_name] = base_id
                            resolved_bases.append(base_name)

                    for base_name in resolved_bases:
                        model.unresolved_base_classes.remove(base_name)
