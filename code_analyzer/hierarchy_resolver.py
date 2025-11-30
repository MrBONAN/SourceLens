from typing import Optional

from code_analyzer.data_models import ClassDefinition, CodeElementType, JsonElement, BaseCodeElement, BaseCodeModule
from code_analyzer.symbol_resolver import SymbolResolver


class HierarchyResolver:
    def __init__(self, all_models: dict[str, JsonElement]):
        self.all_models = all_models
        self.symbol_resolver = SymbolResolver(all_models)

    def resolve_all(self):
        for model in self.all_models.values():
            if isinstance(model, ClassDefinition):
                self._resolve_for_class(model)

    def _resolve_for_class(self, class_def: ClassDefinition):
        module = self._find_parent_module(class_def)
        if not module:
            return

        for base_name in list(class_def.unresolved_base_classes):
            base_id = self.symbol_resolver.resolve_symbol(
                name=base_name,
                context_file_id=module.id,
                expected_type=CodeElementType.CLASS
            )

            if base_id:
                class_def.base_classes[base_name] = base_id
                class_def.unresolved_base_classes.remove(base_name)

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
