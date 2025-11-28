import json
import yaml
from pathlib import Path
from enum import Enum
from code_analyzer.folder_analyzer import FolderAnalyzer
from code_analyzer.folder_reader import FolderReader
from code_analyzer.json_converter import JsonConverter
import sys

# import ast
# a = ast.parse("""
# obj = Caller()
# obj.call1().call2(1)
# simple()
# """)
# print(ast.dump(a, indent=4))
# exit(0)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Для работы программы необходимо передать путь к папке")
        exit(0)

    test_folder = sys.argv[1]
    output_file = test_folder + "_output.json"

    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    config_path = project_root / "code_analyzer" / "config.yaml"
    folder_path = project_root / "code_analyzer"
    output_path = project_root / "tests" / "temp" / output_file

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    analyzer = FolderAnalyzer(config)
    result = analyzer.analyze_folder(folder_path)
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Enum):
                return o.value
            if hasattr(o, '__dict__'):
                return o.__dict__
            return str(o)


    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, indent=2, cls=CustomJSONEncoder))
