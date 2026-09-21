from pathlib import Path

from app.processors.factory import DocumentProcessorFactory


def test_processor_factory_rejects_unsupported_file():
    factory = DocumentProcessorFactory()

    file_path = Path("example.exe")

    try:
        factory.get_processor(file_path)
        assert False
    except ValueError:
        assert True