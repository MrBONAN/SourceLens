import json
import yaml
from pathlib import Path
from enum import Enum
from code_analyzer.ast_parser.processor import AstProcessor


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)


def analyze_code(file_path: str, config: dict) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    processor = AstProcessor(file_path, config.get('process_nodes', {}))
    return processor.process_file(source_code)


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    config_path = project_root / "code_analyzer" / "config.yaml"
    file_to_analyze = current_dir / "sample_code.py"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    analyzed_data = analyze_code(str(file_to_analyze), config)
    print(json.dumps(analyzed_data, indent=2, cls=CustomJSONEncoder))