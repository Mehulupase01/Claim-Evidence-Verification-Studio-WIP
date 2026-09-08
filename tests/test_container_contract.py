from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_image_uses_non_root_runtime_and_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12.13-slim-bookworm" in dockerfile
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "COPY . " not in dockerfile
    assert "ARG " not in dockerfile
    assert ".env" not in dockerfile


def test_compose_has_one_health_checked_application_service() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("  app:") == 1
    assert "healthcheck:" in compose
    assert "required: false" in compose
    assert "GEMINI_API_KEY" not in compose
    assert "R2_SECRET_ACCESS_KEY" not in compose


def test_dockerignore_blocks_secret_and_local_state() -> None:
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in ignored
    assert ".git" in ignored
    assert "tmp" in ignored
    assert "uploads" in ignored
