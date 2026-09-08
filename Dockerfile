FROM python:3.12.13-slim-bookworm

LABEL org.opencontainers.image.title="Claim Evidence Verifier" \
      org.opencontainers.image.description="Grounded document claim verification" \
      org.opencontainers.image.source="https://github.com/Mehulupase01/Claim-Evidence-Verification-Studio-WIP"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

COPY requirements.lock ./requirements.lock
RUN python -m pip install --no-cache-dir --requirement requirements.lock

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser samples ./samples

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

CMD ["python", "-m", "app"]
