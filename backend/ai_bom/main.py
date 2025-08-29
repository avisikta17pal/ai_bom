from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Any

import typer
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

from ai_bom.__init__ import __version__
from ai_bom.core.config import Settings, get_settings
from ai_bom.db.session import get_session
from ai_bom.api.v1.auth import router as auth_router
from ai_bom.api.v1.projects import router as projects_router
from ai_bom.api.v1.boms import router as boms_router
from ai_bom.api.v1.webhook import router as webhook_router
from ai_bom.api.v1.mappings import router as mappings_router
from ai_bom.api.v1.scan import router as scan_router
from ai_bom.core.logging import configure_logging, RequestContextMiddleware
from ai_bom.core.config import get_settings
import structlog
import time
import redis


metrics_registry = CollectorRegistry()
api_request_count = Counter(
    "api_request_count",
    "Total number of API requests",
    registry=metrics_registry,
)
bom_created_total = Counter(
    "bom_created_total",
    "Total number of BOMs created",
    registry=metrics_registry,
)
bom_signed_total = Counter(
    "bom_signed_total",
    "Total number of BOMs signed",
    registry=metrics_registry,
)
request_latency_seconds = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    registry=metrics_registry,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_client: redis.Redis, rpm: int) -> None:
        super().__init__(app)
        self.redis = redis_client
        self.rpm = rpm

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        key = f"rl:{request.client.host}:{int(time.time() // 60)}"
        try:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, 60)
            if count > self.rpm:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        except Exception:
            pass
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        request_latency_seconds.observe(duration)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if self.settings.require_https:
            response.headers["Strict-Transport-Security"] = f"max-age={self.settings.hsts_max_age}; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = self.settings.csp_policy
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()
    log = structlog.get_logger()
    app = FastAPI(title="ai-bom", version=__version__, openapi_url="/openapi.json")
    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    try:
        r = redis.Redis.from_url(settings.redis_url)
        app.add_middleware(RateLimitMiddleware, redis_client=r, rpm=120)
    except Exception:
        log.warning("rate_limit_disabled", reason="redis unavailable")

    @app.middleware("http")
    async def add_metrics(request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        api_request_count.inc()
        return response

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        data = generate_latest(metrics_registry)
        return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

    # Routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(projects_router, prefix="/api/v1", tags=["projects"])
    app.include_router(boms_router, prefix="/api/v1", tags=["boms"])
    app.include_router(webhook_router, prefix="/api/v1", tags=["webhook"])
    app.include_router(mappings_router, prefix="/api/v1", tags=["mappings"])
    app.include_router(scan_router, prefix="/api/v1", tags=["scan"])

    @app.on_event("startup")
    async def on_startup() -> None:  # pragma: no cover - side effects
        # Initialize tracing lazily
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            resource = Resource.create({"service.name": "ai-bom-backend"})
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(OTLPSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass

    return app


root_cli = typer.Typer(help="ai-bom orchestrator: API server, worker, and CLI entrypoints")


@root_cli.command()
def api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Run the FastAPI server."""
    uvicorn.run("ai_bom.main:create_app", host=host, port=port, reload=reload, factory=True)


@root_cli.command()
def worker(concurrency: int = 1) -> None:
    """Start Celery worker for background tasks."""
    # Lazy import to avoid importing celery on non-worker processes
    from ai_bom.tasks import celery_app

    def _shutdown(*_: Any) -> None:
        raise KeyboardInterrupt

    # Run a celery worker programmatically
    argv = [
        "worker",
        f"--concurrency={concurrency}",
        "--loglevel=INFO",
        "-Q",
        "ai_bom",
    ]
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _shutdown)
    celery_app.worker_main(argv)


@root_cli.command()
def cli() -> None:
    """Run the ai-bom CLI (delegates to ai_bom.cli)."""
    from ai_bom.cli import app as cli_app

    cli_app()


def main() -> None:  # pragma: no cover - entrypoint
    root_cli()


if __name__ == "__main__":  # pragma: no cover - script use
    main()

