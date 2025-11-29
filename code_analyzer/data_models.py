import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CodeElementType(str, Enum):
    UNKNOWN = "unknown"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    IMPORT = "import"
    FOLDER = "folder"


@dataclass
class SourceSpan:
    """Описывает местоположение элемента кода."""
    file_path: str
    start_line: int
    end_line: int


@dataclass
class JsonElement:
    """Базовая модель для всех элементов в выходном Json"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    element_type: CodeElementType = field(default_factory=lambda: CodeElementType.UNKNOWN)
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)


@dataclass
class BaseCodeElement(JsonElement):
    """Базовая модель для всех элементов кода."""
    source_span: Optional[SourceSpan] = None


@dataclass
class Parameter:
    """Модель для параметра функции."""
    name: str


@dataclass
class FunctionDefinition(BaseCodeElement):
    """Модель для описания функции."""
    element_type: CodeElementType = CodeElementType.FUNCTION
    decorator_list: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    outgoing_calls: list[str] = field(default_factory=list)
    outgoing_func_calls: list[str] = field(default_factory=list)
    outgoing_method_calls: list[str] = field(default_factory=list)


@dataclass
class ClassDefinition(BaseCodeElement):
    """Модель для описания класса."""
    element_type: CodeElementType = CodeElementType.CLASS
    decorator_list: list[str] = field(default_factory=list)
    base_classes: dict[str, str] = field(default_factory=dict)
    unresolved_base_classes: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Модель для информации об импорте."""
    module: Optional[str]
    element_type: CodeElementType = CodeElementType.IMPORT
    name: Optional[str] = None
    alias: Optional[str] = None
    level: int = 0


@dataclass
class Folder(JsonElement):
    """Модель для папки"""
    element_type: CodeElementType = CodeElementType.FOLDER


@dataclass
class BaseCodeModule(BaseCodeElement):
    """Модель, представляющая анализируемый файл."""
    element_type: CodeElementType = CodeElementType.FILE
    imports: list[ImportInfo] = field(default_factory=list)
