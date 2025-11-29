import pytest
from code_analyzer.data_models import CodeElementType


def find_class_model(models, class_name):
    for model in models.values():
        if model.element_type == CodeElementType.CLASS and model.name == class_name:
            return model
    return None


class TestInheritance:
    @pytest.mark.parametrize("folder_name, child_name, expected_parent_name", [
        # папка теста, класса-наследник, ожидаемый родитель
        ("test_inheritance_simple", "Child", "Parent"),
        ("test_inheritance_alias", "MyClass", "OriginalBase"),
        ("test_inheritance_module_dot", "Service", "Helper"),
        ("test_inheritance_local_priority", "AppConfig", "Config"),
        ("test_inheritance_nested_pkg", "MyPlugin", "CoreObject"),
    ])
    def test_inheritance_resolution(self, analyzer, test_data_dir, folder_name, child_name, expected_parent_name):
        target_folder = test_data_dir / folder_name

        results = analyzer.analyze_folder(target_folder)

        child_model = find_class_model(results, child_name)
        assert child_model is not None, f"Класс '{child_name}' не найден в результатах анализа"

        assert child_model.base_classes, f"У класса '{child_name}' не найдены базовые классы"

        found_parent = False
        found_parent_ids = list(child_model.base_classes.values())

        for parent_id in found_parent_ids:
            parent_model = results.get(parent_id)
            if parent_model and parent_model.name == expected_parent_name:
                found_parent = True
                break

        assert found_parent, (
            f"Ожидалось, что '{child_name}' наследуется от '{expected_parent_name}'. "
            f"Найденные родители (ID): {found_parent_ids}"
        )
