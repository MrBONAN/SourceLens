import json
import yaml
from pathlib import Path
from enum import Enum
from code_analyzer.folder_analyzer import FolderAnalyzer

if __name__ == "__main__":
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    config_path = project_root / "code_analyzer" / "config.yaml"
    folder_path = project_root / "code_analyzer"
    output_path = project_root / "tests" / "temp" / "folder_test_output.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    analyzer = FolderAnalyzer(config)
    results = analyzer.analyze_folder(str(folder_path))
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Enum):
                return o.value
            if hasattr(o, '__dict__'):
                return o.__dict__
            return str(o)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(results, indent=2, cls=CustomJSONEncoder))
