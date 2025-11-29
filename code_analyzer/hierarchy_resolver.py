from typing import Optional
from code_analyzer.data_models import (
    BaseCodeElement, BaseCodeModule, ClassDefinition, CodeElementType, JsonElement
)


class HierarchyResolver:
    def __init__(self, all_models: dict[str, JsonElement]):
        self.all_models = all_models

    def resolve_all(self):
        for model in self.all_models.values():
            if isinstance(model, ClassDefinition):
                self._resolve_for_class(model)

    def _resolve_for_class(self, class_def: ClassDefinition):
        module = self._find_parent_module(class_def)
        if not module:
            return

        for base_name in list(class_def.unresolved_base_classes):
            base_id = self._find_base_class_id(base_name, module)

            if base_id:
                class_def.base_classes[base_name] = base_id
                class_def.unresolved_base_classes.remove(base_name)

    def _find_base_class_id(self, base_name: str, current_module: BaseCodeModule) -> Optional[str]:
        """
        Порядок поиска:
        Внутри текущего файла
        Среди явных импортов (from X import Y)
        Среди импортов модулей (import X)
        """

        local_id = self._find_class_in_module_children(current_module, base_name)
        if local_id:
            return local_id

        for imp in current_module.imports:
            target_name = imp.alias if imp.alias else imp.name

            if target_name == base_name:
                if imp.module_id and imp.is_local:
                    target_module = self.all_models.get(imp.module_id)
                    if isinstance(target_module, BaseCodeModule):
                        # Ищем именно imp.name (полное имя), а не алиас
                        found_id = self._find_class_in_module_children(target_module, imp.name)
                        if found_id:
                            return found_id

        if '.' in base_name:
            parts = base_name.split('.', 1)
            module_alias = parts[0]
            rest_of_path = parts[1]

            for imp in current_module.imports:
                current_import_name = imp.alias if imp.alias else imp.module

                match = (current_import_name == module_alias)

                if not match and imp.name == module_alias:
                    match = True

                if match:
                    if imp.module_id and imp.is_local:
                        target_module = self.all_models.get(imp.module_id)
                        if isinstance(target_module, BaseCodeModule):
                            found_id = self._find_class_deeply(target_module, rest_of_path)
                            if found_id:
                                return found_id

        return None

    def _find_class_deeply(self, start_element: JsonElement, name_chain: str) -> Optional[str]:
        if not name_chain:
            return start_element.id

        parts = name_chain.split('.', 1)
        current_name = parts[0]
        remaining_chain = parts[1] if len(parts) > 1 else None

        for child_id in start_element.children_ids:
            child = self.all_models.get(child_id)
            if child and child.name == current_name:
                if not remaining_chain:
                    if isinstance(child, ClassDefinition):
                        return child.id
                    return None
                return self._find_class_deeply(child, remaining_chain)

        if isinstance(start_element, BaseCodeModule):
            for imp in start_element.imports:
                check_name = imp.alias if imp.alias else imp.name

                if check_name == current_name and imp.module_id and imp.is_local:
                    target_module = self.all_models.get(imp.module_id)
                    if target_module:
                        if not remaining_chain:
                            # Путь закончился на модуле? Странно для базового класса,
                            # но теоретически возможно, если класс называется так же как модуль.
                            # Но скорее всего мы ищем Class внутри.
                            return None

                        return self._find_class_deeply(target_module, remaining_chain)

        return None

    def _find_class_in_module_children(self, module: BaseCodeModule, class_name: str) -> Optional[str]:
        for child_id in module.children_ids:
            child = self.all_models.get(child_id)
            if child and child.element_type == CodeElementType.CLASS and child.name == class_name:
                return child.id
        return None

    def _find_parent_module(self, element: BaseCodeElement) -> Optional[BaseCodeModule]:
        current_id = element.parent_id
        while current_id:
            parent = self.all_models.get(current_id)
            if not parent:
                return None
            if isinstance(parent, BaseCodeModule):
                return parent
            current_id = parent.parent_id
        return None
