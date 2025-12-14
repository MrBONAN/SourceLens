from utils import simple_helper as renamed_helper  # Алиас


def my_decorator(func):
    return func


@my_decorator  # Декоратор (должен попасть в calls)
def recursive_function(n):
    if n > 0:
        # Рекурсия (должна найти саму себя)
        recursive_function(n - 1)
        # Вызов алиаса (должен найти simple_helper из utils)
        renamed_helper()


class WorkerA:
    def execute(self):
        print("A")

    def run(self):
        self.execute()  # Локальный метод A


class WorkerB:
    def execute(self):
        print("B")

    def run(self):
        self.execute()  # Локальный метод B (имя такое же, но ID должен быть другой!)