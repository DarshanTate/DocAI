from app.services.evaluation.metrics import RetrievalMetrics


def test_recall_at_k():

    retrieved = [
        "doc1",
        "doc2",
        "doc3",
    ]

    relevant = [
        "doc1",
        "doc3",
    ]

    score = RetrievalMetrics.recall_at_k(
        retrieved,
        relevant,
    )

    assert score == 1.0


def test_precision_at_k():

    retrieved = [
        "doc1",
        "doc2",
        "doc3",
    ]

    relevant = [
        "doc1",
    ]

    score = RetrievalMetrics.precision_at_k(
        retrieved,
        relevant,
    )

    assert score == 1 / 3


def test_mrr():

    retrieved = [
        "doc3",
        "doc1",
        "doc2",
    ]

    relevant = [
        "doc1",
    ]

    score = RetrievalMetrics.mrr(
        retrieved,
        relevant,
    )

    assert score == 0.5