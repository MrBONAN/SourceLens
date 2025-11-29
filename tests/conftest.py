import pytest
import yaml
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code_analyzer.folder_analyzer import FolderAnalyzer


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    return project_root / "tests"


@pytest.fixture(scope="session")
def analyzer_config(project_root):
    config_path = project_root / "code_analyzer" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def analyzer(analyzer_config):
    return FolderAnalyzer(analyzer_config)
