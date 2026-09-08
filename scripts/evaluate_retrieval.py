import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import statistics
import time

from app.models import EvidenceChunk
from app.services.retrieval import BM25Retriever


ROOT = Path(__file__).resolve().parents[1]


def load_corpus(path: Path) -> tuple[list[EvidenceChunk], list[dict]]:
    corpus = json.loads(path.read_text(encoding="utf-8"))
    chunks = []
    offset = 0
    for item in corpus["chunks"]:
        text = item["text"]
        chunks.append(
            EvidenceChunk(
                **item,
                start_char=offset,
                end_char=offset + len(text),
            )
        )
        offset += len(text) + 1
    return chunks, corpus["queries"]


def evaluate(path: Path, iterations: int = 500) -> dict:
    chunks, queries = load_corpus(path)
    retriever = BM25Retriever()
    top_one_hits = 0
    top_three_hits = 0
    for query in queries:
        ranked = retriever.retrieve(query["claim"], chunks, top_k=3)
        ids = [item.evidence_id for item in ranked]
        top_one_hits += ids[0] == query["expected_evidence_id"]
        top_three_hits += query["expected_evidence_id"] in ids

    timings = []
    for index in range(iterations):
        query = queries[index % len(queries)]
        started = time.perf_counter_ns()
        retriever.retrieve(query["claim"], chunks, top_k=3)
        timings.append((time.perf_counter_ns() - started) / 1_000_000)

    ordered = sorted(timings)
    percentile_95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "corpus_chunks": len(chunks),
        "queries": len(queries),
        "iterations": iterations,
        "top_1_accuracy": round(top_one_hits / len(queries), 4),
        "top_3_accuracy": round(top_three_hits / len(queries), 4),
        "latency_ms": {
            "median": round(statistics.median(timings), 4),
            "p95": round(percentile_95, 4),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate deterministic retrieval.")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "evaluation" / "retrieval_corpus.json",
    )
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.corpus, args.iterations)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
