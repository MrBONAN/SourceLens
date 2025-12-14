class BaseService:
    def parent_method(self):
        print("Parent")


class ChildService(BaseService):
    def run_logic(self):
        # ТЕСТ 1: Вызов метода родителя через self
        self.parent_method()

    def internal_method(self):
        print("Internal")

    def do_work(self):
        # ТЕСТ 2: Вызов своего метода через self
        self.internal_method()