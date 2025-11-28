from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from enum import Enum


class OutputFormat(Enum):
    JSON = "json"
    YAML = "yaml"
    CONSOLE = "console"


@dataclass
class OutputConfig:
    output_format: OutputFormat = OutputFormat.JSON
    output_file: Optional[str] = None
    output_directory: Optional[str] = None

    indent: int = 2
    ensure_ascii: bool = False
    sort_keys: bool = False

    include_types: Optional[List[str]] = None
    exclude_types: Optional[List[str]] = None
    include_files: Optional[List[str]] = None
    exclude_files: Optional[List[str]] = None

    include_source_span: bool = True
    include_children: bool = True
    include_parent: bool = True
    include_imports: bool = True
    include_methods: bool = True
    include_base_classes: bool = True
    include_outgoing_calls: bool = True

    validate_references: bool = True
    show_unresolved: bool = True
    show_statistics: bool = True

    def __post_init__(self):
        if self.output_file and self.output_directory:
            self.output_file = str(Path(self.output_directory) / self.output_file)
        elif self.output_directory and not self.output_file:
            self.output_file = str(Path(self.output_directory) / "analysis_result.json")

    def should_include_element(self, element: Any) -> bool:
        if hasattr(element, 'element_type'):
            element_type = element.element_type.value
            if self.include_types and element_type not in self.include_types:
                return False
            if self.exclude_types and element_type in self.exclude_types:
                return False

        if hasattr(element, 'source_span') and element.source_span:
            file_path = element.source_span.file_path
            if self.include_files and not any(pattern in file_path for pattern in self.include_files):
                return False
            if self.exclude_files and any(pattern in file_path for pattern in self.exclude_files):
                return False

        return True

    def filter_element_data(self, element: Any) -> Dict[str, Any]:
        if not hasattr(element, '__dict__'):
            return {}

        data = element.__dict__.copy()

        if not self.include_source_span and 'source_span' in data:
            data.pop('source_span')

        if not self.include_children and 'children_ids' in data:
            data.pop('children_ids')

        if not self.include_parent and 'parent_id' in data:
            data.pop('parent_id')

        if not self.include_imports and 'imports' in data:
            data.pop('imports')

        if not self.include_base_classes and 'base_classes' in data:
            data.pop('base_classes')
        if not self.include_base_classes and 'unresolved_base_classes' in data:
            data.pop('unresolved_base_classes')

        if not self.include_outgoing_calls and 'outgoing_calls' in data:
            data.pop('outgoing_calls')

        return data

    def get_output_path(self, suffix: str = "") -> str:
        if not self.output_file:
            return f"analysis_result{suffix}.json"

        path = Path(self.output_file)
        if suffix:
            stem = path.stem
            suffix = suffix
            path = path.parent / f"{stem}{suffix}{path.suffix}"

        return str(path)

    def create_json_encoder(self):
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, Enum):
                    return o.value
                if hasattr(o, '__dict__'):
                    return o.__dict__
                return str(o)

        return CustomJSONEncoder


class OutputManager:

    def __init__(self, config: OutputConfig):
        self.config = config

    def save_analysis_results(self, results: Dict[str, Any]) -> List[str]:
        saved_files = []

        filtered_results = self._filter_results(results)

        if self.config.output_format == OutputFormat.JSON:
            saved_files.append(self._save_json(filtered_results, "analysis"))

        return saved_files

    def _filter_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        filtered = {}

        for element_id, element in results.items():
            if self.config.should_include_element(element):
                filtered[element_id] = self.config.filter_element_data(element)

        return filtered

    def _save_json(self, data: Any, suffix: str = "") -> str:
        output_path = self.config.get_output_path(suffix)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        encoder = self.config.create_json_encoder()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self.config.indent,
                      cls=encoder, ensure_ascii=self.config.ensure_ascii,
                      sort_keys=self.config.sort_keys)

        return output_path

    def print_to_console(self, data: Any, title: str = "Results"):
        print(f"\n=== {title} ===")

        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        else:
            print(data)
