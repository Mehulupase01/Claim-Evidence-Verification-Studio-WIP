from pathlib import Path

from scripts.evaluate_retrieval import evaluate


ROOT = Path(__file__).resolve().parents[1]


def test_retrieval_evaluation_corpus_is_perfect_at_top_one() -> None:
    result = evaluate(ROOT / "evaluation" / "retrieval_corpus.json", iterations=10)

    assert result["queries"] == 5
    assert result["top_1_accuracy"] == 1.0
    assert result["top_3_accuracy"] == 1.0
