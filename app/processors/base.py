from abc import ABC, abstractmethod
from pathlib import Path

from app.processors.types import ParsedDocument


class BaseDocumentProcessor(ABC):

    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        pass

    @abstractmethod
    def process(self, file_path: Path) -> ParsedDocument:
        pass