import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class CodeElementType(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    IMPORT = "import"


@dataclass
class SourceSpan:
    """Описывает местоположение элемента кода."""
    file_path: str
    start_line: int
    end_line: int


@dataclass
class BaseCodeElement:
    """Базовая модель для всех элементов кода."""
    name: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_span: Optional[SourceSpan] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)


@dataclass
class Parameter:
    """Модель для параметра функции."""
    name: str


@dataclass
class FunctionDefinition(BaseCodeElement):
    """Модель для описания функции."""
    element_type: CodeElementType = CodeElementType.FUNCTION
    parameters: List[Parameter] = field(default_factory=list)
    outgoing_calls: List[str] = field(default_factory=list)


@dataclass
class ClassDefinition(BaseCodeElement):
    """Модель для описания класса."""
    element_type: CodeElementType = CodeElementType.CLASS
    base_classes: Dict[str, str] = field(default_factory=dict)
    unresolved_base_classes: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Модель для информации об импорте."""
    module: Optional[str]
    name: Optional[str] = None
    alias: Optional[str] = None
    level: int = 0


@dataclass
class BaseCodeModule(BaseCodeElement):
    """Модель, представляющая анализируемый файл."""
    element_type: CodeElementType = CodeElementType.MODULE
    imports: List[ImportInfo] = field(default_factory=list)
