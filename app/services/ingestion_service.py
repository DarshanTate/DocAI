from pathlib import Path

from app.processors.factory import DocumentProcessorFactory
from app.processors.types import ParsedDocument
from app.services.chunking.text_chunker import TextChunk, TextChunker


class IngestionService:

    def __init__(self):
        self.processor_factory = DocumentProcessorFactory()
        self.chunker = TextChunker(
            chunk_size=1000,
            chunk_overlap=200,
        )

    def process(
        self,
        file_path: str,
    ) -> ParsedDocument:

        path = Path(file_path)

        processor = self.processor_factory.get_processor(
            path
        )

        return processor.process(path)

    def process_and_chunk(
        self,
        file_path: str,
    ) -> list[TextChunk]:

        parsed_document = self.process(
            file_path
        )

        return self.chunker.chunk_elements(
            parsed_document.elements
        )