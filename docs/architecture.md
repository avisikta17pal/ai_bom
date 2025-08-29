## Architecture

FastAPI backend with async SQLAlchemy and Celery for background tasks. Next.js frontend communicates with REST API. MinIO/S3 for artifact storage, Postgres for persistence, Redis for queues. Prometheus metrics exposed at `/metrics`.

Key modules:
- API routers: `ai_bom/api/v1/*`
- Services: scanner, signer, exporter
- Compliance mapping: `ai_bom/compliance/mapping.py`
- CLI: `ai_bom/cli.py`

