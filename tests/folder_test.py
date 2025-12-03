import yaml
from pathlib import Path
from code_analyzer.folder_analyzer import FolderAnalyzer
from code_analyzer.json_converter import JsonConverter
import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Для работы программы необходимо передать путь к папке")
        exit(0)

    test_folder = sys.argv[1]
    output_file = test_folder + "_output.json"

    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    config_path = project_root / "code_analyzer" / "config.yaml"
    folder_path = project_root / "tests" / test_folder
    output_path = project_root / "tests" / "temp" / output_file

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    analyzer = FolderAnalyzer(config)
    result = analyzer.analyze_folder(folder_path)
    json_converter = JsonConverter()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_converter.dump(result, config["json_output"]))
