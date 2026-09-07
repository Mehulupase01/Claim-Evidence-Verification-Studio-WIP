from collections import Counter
import math
import re
from typing import Protocol

from app.models import EvidenceChunk, RankedChunk


TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


class RetrievalService(Protocol):
    def retrieve(
        self, claim: str, chunks: list[EvidenceChunk], *, top_k: int
    ) -> list[RankedChunk]: ...


class BM25Retriever:
    """Small deterministic BM25 implementation for a single-document corpus."""

    k1 = 1.5
    b = 0.75

    def retrieve(
        self, claim: str, chunks: list[EvidenceChunk], *, top_k: int
    ) -> list[RankedChunk]:
        if not chunks or top_k < 1:
            return []

        documents = [tokenize(chunk.text) for chunk in chunks]
        query_terms = list(dict.fromkeys(tokenize(claim)))
        average_length = sum(map(len, documents)) / len(documents) or 1.0
        document_frequency = Counter(
            term for document in documents for term in set(document)
        )

        ranked: list[tuple[float, int, EvidenceChunk]] = []
        for position, (chunk, tokens) in enumerate(zip(chunks, documents, strict=True)):
            frequencies = Counter(tokens)
            score = 0.0
            for term in query_terms:
                frequency = frequencies[term]
                if not frequency:
                    continue
                containing = document_frequency[term]
                inverse_frequency = math.log(
                    1 + (len(documents) - containing + 0.5) / (containing + 0.5)
                )
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * len(tokens) / average_length
                )
                score += inverse_frequency * frequency * (self.k1 + 1) / denominator
            ranked.append((score, position, chunk))

        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            RankedChunk(**chunk.model_dump(), retrieval_score=round(max(score, 0.0), 6))
            for score, _, chunk in ranked[: min(top_k, len(ranked))]
        ]


def tokenize(text: str) -> list[str]:
    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text)]
