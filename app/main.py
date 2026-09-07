import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.api.documents import router as documents_router
from app.config import get_settings
from app.errors import AppError
from app.logging import configure_logging, request_id_context
from app.models import HealthResponse


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
logger = logging.getLogger("claim_verifier")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("application started", extra={"operation": "startup"})
    yield
    logger.info("application stopped", extra={"operation": "shutdown"})


def create_app() -> FastAPI:
    application = FastAPI(
        title="Claim Evidence Verifier",
        version="1.0.0",
        description="Grounded, human-reviewable claim verification.",
        lifespan=lifespan,
    )
    application.include_router(documents_router)

    @application.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        from fastapi.responses import JSONResponse

        logger.warning(
            "request failed safely",
            extra={
                "operation": "error_mapping",
                "status_code": exc.status_code,
                "error_type": exc.code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.public_message,
                    "request_id": request_id_context.get(),
                }
            },
        )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_id)
            else uuid.uuid4().hex
        )
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            return response
        finally:
            logger.info(
                "request completed",
                extra={
                    "operation": "http_request",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            request_id_context.reset(token)

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        return HealthResponse()

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root() -> str:
        return """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Claim Evidence Verifier</title></head><body><main><h1>Claim Evidence Verifier</h1><p>The reviewer workspace is being prepared.</p></main></body></html>"""

    return application


app = create_app()
