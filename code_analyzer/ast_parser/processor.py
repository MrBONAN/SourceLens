import ast
from code_analyzer.data_models import BaseCodeElement, BaseCodeModule, SourceSpan, ClassDefinition
from .ast_handlers import FunctionDefHandler, ClassDefHandler, ImportHandler
from .instruction_builder import InstructionBuilder


class AstProcessor(ast.NodeVisitor):
    def __init__(self, project_root: str, file_path: str, config: dict[str, list[str]]):
        self.file_path = file_path
        self.file_model_id: str = ""
        self.result_models: dict[str, BaseCodeElement] = {}
        self.context_stack: list[str] = []
        self._init_handlers(project_root, config)

    def _init_handlers(self, project_root: str, config: dict[str, list[str]]):
        self.class_handler = ClassDefHandler(self.file_path, set(config["ClassDef"]))
        self.func_handler = FunctionDefHandler(self.file_path, set(config["FunctionDef"]))
        self.import_handler = ImportHandler(project_root, self.file_path, set(config["Import"] + config["ImportFrom"]))

    def process_file(self, source_code: str) -> dict[str, BaseCodeElement]:
        tree = ast.parse(source_code)

        module_name = self.file_path.split('/')[-1].split('.')[0]
        module_element = BaseCodeModule(
            name=module_name,
            source_span=SourceSpan(file_path=self.file_path, start_line=1, end_line=len(source_code.splitlines()))
        )

        module_element.instructions = InstructionBuilder().build(tree.body)

        self.file_model_id = module_element.id
        self.result_models[module_element.id] = module_element
        self.context_stack.append(module_element.id)

        self.visit(tree)

        self.context_stack.pop()
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

        func_builder = InstructionBuilder()
        model.instructions = func_builder.build(node.body)

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
