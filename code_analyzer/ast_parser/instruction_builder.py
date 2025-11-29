import ast
from code_analyzer.data_models import Instruction, OperationType


class InstructionBuilder(ast.NodeVisitor):
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.temp_count = 0

    def _new_temp(self) -> str:
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def build(self, nodes: list[ast.AST]) -> list[Instruction]:
        self.instructions = []
        self.temp_count = 0
        for node in nodes:
            self.visit(node)
        return self.instructions

    def visit(self, node: ast.AST) -> str:
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> str:
        arg_vars = []
        for arg in node.args:
            arg_vars.append(self.visit(arg))

        target_var = self._new_temp()

        if isinstance(node.func, ast.Attribute):
            base_var = self.visit(node.func.value)
            self.instructions.append(Instruction(
                target=target_var,
                op=OperationType.CALL_METHOD,
                name=node.func.attr,
                base_object=base_var,
                arguments=arg_vars
            ))
        elif isinstance(node.func, ast.Name):
            self.instructions.append(Instruction(
                target=target_var,
                op=OperationType.CALL_FUNCTION,
                name=node.func.id,
                base_object=None,
                arguments=arg_vars
            ))

        return target_var

    def visit_Name(self, node: ast.Name) -> str:
        return node.id

    def visit_Constant(self, node: ast.Constant) -> str:
        return repr(node.value)

    def visit_Assign(self, node: ast.Assign):
        value_var = self.visit(node.value)

        for target in node.targets:
            if isinstance(target, ast.Name):
                self.instructions.append(Instruction(
                    target=target.id,
                    op=OperationType.ASSIGN,
                    arguments=[value_var]
                ))

    def visit_Expr(self, node: ast.Expr):
        self.visit(node.value)

    # Блокируем спуск во вложенные функции и классы
    def visit_FunctionDef(self, node: ast.FunctionDef):
        return

    def visit_ClassDef(self, node: ast.ClassDef):
        return
