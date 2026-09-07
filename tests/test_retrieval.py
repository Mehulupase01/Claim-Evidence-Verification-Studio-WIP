from app.models import EvidenceChunk
from app.services.retrieval import BM25Retriever, tokenize


def chunk(number: int, text: str, page: int = 1) -> EvidenceChunk:
    return EvidenceChunk(
        evidence_id=f"chunk_{number:04d}",
        page=page,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_bm25_ranks_known_evidence_first() -> None:
    chunks = [
        chunk(1, "The report covers hiring plans and office leases."),
        chunk(2, "Revenue increased by 27 percent during the second quarter.", page=2),
        chunk(3, "Customer retention remained stable throughout the period."),
    ]

    results = BM25Retriever().retrieve(
        "Revenue increased 27 percent in Q2", chunks, top_k=2
    )

    assert results[0].evidence_id == "chunk_0002"
    assert results[0].page == 2
    assert results[0].retrieval_score > results[1].retrieval_score


def test_bm25_has_deterministic_tie_breaking() -> None:
    chunks = [chunk(1, "Alpha"), chunk(2, "Beta")]

    results = BM25Retriever().retrieve("unmatched words", chunks, top_k=2)

    assert [result.evidence_id for result in results] == ["chunk_0001", "chunk_0002"]
    assert tokenize("Q2-growth_growth") == ["q2", "growth", "growth"]
