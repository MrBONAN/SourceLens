from utils import simple_helper
import utils
from classes import ChildService


def local_func():
    pass


def app_entry():
    # ТЕСТ 3: Вызов импортированной функции (from ... import)
    simple_helper()

    # ТЕСТ 4: Вызов функции через модуль (import ...)
    utils.another_helper()

    # ТЕСТ 5: Локальный вызов
    local_func()

    # ТЕСТ 6: Работа с классом (тут мы ожидаем, что анализатор увидит создание класса,
    # но outgoing_calls обычно смотрят внутри тела функции)
    service = ChildService()
    service.do_work()