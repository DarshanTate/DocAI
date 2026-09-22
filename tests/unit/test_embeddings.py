from app.services.embeddings.embedding_service import EmbeddingService


def test_embedding_generation():

    service = EmbeddingService()

    embedding = service.embed_text(
        "DocAI is a document intelligence platform."
    )

    assert len(embedding) == 384
    assert all(isinstance(value, float) for value in embedding)