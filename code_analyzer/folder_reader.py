from pathlib import Path
from typing import Dict, List, Optional
from .ast_parser.processor import AstProcessor
from .data_models import (
    Folder,
    BaseCodeElement,
    BaseCodeModule,
    CodeElementType
)


class FolderReader:
    def __init__(self, config: Dict[str, List[str]]):
        self.config = config
        self.all_models: Dict[str, BaseCodeElement] = {}
        self.module_mapping: Dict[str, str] = {}

        self.include_patterns = ['*.py']
        self.exclude_patterns = ['__pycache__', '*.pyc', '*.pyo', '*.pyd']

    def read_folder(self, folder_path: Path, parent_id: str = None) -> Optional[str]:
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Папка {folder_path} не найдена")

        folder_model = Folder(
            name=str(folder_path),
            parent_id=parent_id,
            element_type=CodeElementType.FOLDER
        )

        children_ids = []

        python_files = self._find_python_files(folder_path)
        for python_file in python_files:
            children_id = self._analyze_file(python_file, folder_model.id)
            if children_id is not None:
                children_ids.append(children_id)

        for folder in folder_path.iterdir():
            if folder.is_dir():
                children_ids.append(self.read_folder(folder, folder_model.id))

        if any(children_ids):
            self.all_models[folder_model.id] = folder_model
            folder_model.children_ids = children_ids
            return folder_model.id

        return None

    def _find_python_files(self, folder_path: Path) -> List[Path]:
        python_files = []

        for pattern in self.include_patterns:
            for python_file in folder_path.glob(pattern):
                if not self._should_exclude(python_file):
                    python_files.append(python_file)
        return python_files

    def _should_exclude(self, file_path: Path) -> bool:
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in file_str or file_path.match(pattern):
                return True
        return False

    def _analyze_file(self, file_path: Path, parent_module_id: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    source_code = f.read()
            except UnicodeDecodeError:
                return None

        processor = AstProcessor(str(file_path), self.config.get('process_nodes', {}))
        file_models = processor.process_file(source_code)

        for model_id, model in file_models.items():
            if isinstance(model, BaseCodeModule):
                model.parent_id = parent_module_id

            self.all_models[model_id] = model

        module_id = next(iter(file_models.keys()))
        self.module_mapping[str(file_path)] = module_id

        return module_id
