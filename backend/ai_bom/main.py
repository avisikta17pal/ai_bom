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
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest

from ai_bom.__init__ import __version__
from ai_bom.core.config import Settings, get_settings
from ai_bom.db.session import get_session, init_models
from ai_bom.api.v1.auth import router as auth_router
from ai_bom.api.v1.projects import router as projects_router
from ai_bom.api.v1.boms import router as boms_router
from ai_bom.api.v1.webhook import router as webhook_router
from ai_bom.api.v1.mappings import router as mappings_router
from ai_bom.api.v1.scan import router as scan_router


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


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="ai-bom", version=__version__, openapi_url="/openapi.json")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
        if settings.environment != "production":
            await init_models()

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

