from code_analyzer.data_models import BaseCodeModule


def get_element_by_name(models, name, file_name_part=None):
    """
    Вспомогательная функция для поиска элемента (функции/класса) по имени.
    Если передан file_name_part, проверяет, что элемент находится в файле,
    имя которого содержит эту часть.
    """
    for model in models.values():
        if model.name == name:
            if file_name_part:
                parent = models.get(model.parent_id)
                while parent and not isinstance(parent, BaseCodeModule):
                    parent = models.get(parent.parent_id)

                if parent and file_name_part in parent.name:
                    return model
            else:
                return model
    return None


def test_full_flow_analysis(analyzer, test_data_dir):
    """
    Интеграционный тест: проверяет построение графа вызовов на тестовом проекте.
    """
    project_path = test_data_dir / "test_project"
    all_models = analyzer.analyze_folder(project_path)

    assert all_models, "Результат анализа не должен быть пустым"

    run_logic = get_element_by_name(all_models, "run_logic", "classes")
    parent_method = get_element_by_name(all_models, "parent_method", "classes")

    assert run_logic is not None
    assert parent_method is not None

    assert parent_method.id in run_logic.outgoing_calls, \
        f"Функция run_logic должна вызывать parent_method (ID: {parent_method.id})"

    recursive_func = get_element_by_name(all_models, "recursive_function", "complex")
    simple_helper = get_element_by_name(all_models, "simple_helper", "utils")

    assert recursive_func is not None
    assert simple_helper is not None

    assert simple_helper.id in recursive_func.outgoing_calls, \
        "Вызов алиаса renamed_helper должен указывать на simple_helper"

    my_decorator = get_element_by_name(all_models, "my_decorator", "complex")
    assert my_decorator is not None

    assert recursive_func.id in recursive_func.outgoing_calls, \
        "Функция должна содержать вызов самой себя (рекурсия)"

    assert my_decorator.id in recursive_func.outgoing_calls, \
        "Декоратор должен быть добавлен в outgoing_calls"

    worker_a = get_element_by_name(all_models, "WorkerA", "complex")
    worker_b = get_element_by_name(all_models, "WorkerB", "complex")

    run_a_id = [child_id for child_id in worker_a.children_ids if all_models[child_id].name == "run"][0]
    run_b_id = [child_id for child_id in worker_b.children_ids if all_models[child_id].name == "run"][0]

    run_a = all_models[run_a_id]
    run_b = all_models[run_b_id]

    exec_a_id = [child_id for child_id in worker_a.children_ids if all_models[child_id].name == "execute"][0]
    exec_b_id = [child_id for child_id in worker_b.children_ids if all_models[child_id].name == "execute"][0]

    assert exec_a_id in run_a.outgoing_calls, "WorkerA.run должен вызывать WorkerA.execute"
    assert exec_b_id in run_b.outgoing_calls, "WorkerB.run должен вызывать WorkerB.execute"

    assert exec_a_id != exec_b_id, "Методы execute в разных классах должны иметь разные ID"