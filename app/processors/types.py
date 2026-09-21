from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentElement:
    content: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    elements: list[DocumentElement]
    metadata: dict[str, Any] = field(default_factory=dict)