<div align="center">

# ai-bom

An auditable, verifiable AI Bill of Materials (AI-BOM) and lineage system for teams to document models, datasets, code, and evaluation artifacts; generate signed traceable manifests; and block PRs that ship untracked AI artifacts.

[![CI](https://img.shields.io/github/actions/workflow/status/your-org/ai-bom/ci.yml?branch=main)](https://github.com/your-org/ai-bom/actions)
[![PyPI](https://img.shields.io/pypi/v/ai-bom.svg)](https://pypi.org/project/ai-bom/)
[![Docker Pulls](https://img.shields.io/docker/pulls/your-org/ai-bom.svg)](https://hub.docker.com/r/your-org/ai-bom)

</div>

### Key features

- **CLI**: `ai-bom` to init, scan, sign, verify, export, and deploy-check
- **REST API**: FastAPI with JWT auth, versioned `/api/v1/*`
- **Frontend**: Next.js + Tailwind SPA dashboard
- **Signing**: ed25519 signatures, SHA-256 fingerprints
- **Compliance**: JSON-LD/C2PA export and compliance dossier (EU AI Act, NIST RMF, ISO 42001)
- **CI & GitHub**: GitHub Actions and pre-commit integration
- **Storage**: MinIO/S3 for artifacts (metadata-only by default)
- **Observability**: `/metrics` Prometheus endpoint and healthcheck `/health`

### Architecture

```
          +-------------+             +-------------+
          |  Frontend   |  HTTPS API  |   Backend   |
          | Next.js SPA | <---------> |  FastAPI    |
          +-------------+             +-------------+
                   |                         |\
                   |                         | \  Celery
                   |                         |  \  worker
                   v                         v   v
             Browser/Auth               Postgres  Redis
                                            |       \
                                            |        \
                                         MinIO/S3   Metrics
```

### Quickstart (Docker Compose)

```bash
git clone https://github.com/your-org/ai-bom.git
cd ai-bom
cp .env.example .env
docker compose -f backend/docker-compose.yml up --build
# API at http://localhost:8000, Docs at /docs, Frontend (if built separately)
```

### CLI examples

```bash
python -m ai_bom.cli init
python -m ai_bom.cli scan --dir . --output bom.json
python -m ai_bom.cli keygen --outdir .ai-bom/keys
python -m ai_bom.cli sign bom.json --key .ai-bom/keys/<key>.key
python -m ai_bom.cli verify bom.json
python -m ai_bom.cli export bom.json --format pdf
python -m ai_bom.cli deploy-check
```

### API examples

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"admin123"}'

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/health
```

### GitHub Action example

```yaml
name: ai-bom deploy check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          pip install -r backend/requirements.txt
          python -m ai_bom.cli deploy-check
```

### Security & privacy (production)

- Default is metadata-only: dataset content is never uploaded; only hashes and metadata are stored.
- Use ed25519 keys; generate with `ai-bom keygen`. Consider KMS/HSM in production.
- JWT secrets rotate via `SECRET_KEY`. Use HTTPS and secure cookies in production. Set `require_https=true` and configure ingress TLS.
- CORS tightened via `cors_origins`. Configure to your frontend domain.
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options.
- Rate limiting via Redis; Prometheus metrics and OpenTelemetry tracing enabled. Request/trace IDs included in logs.
- S3 uploads/downloads: presigned PUT/GET, multipart uploads, size/type limits, SSE (AES256 or KMS if `S3_KMS_KEY_ID` set), lifecycle policies.
- Alembic migrations manage schema; audit logs are append-only via DB trigger.
- CI adds coverage gate, Bandit SAST, Trivy image scan; Dependabot keeps dependencies current.

### Compliance mapping summary

- **Traceability/Lineage**: `components[*].origin`, `components[*].fingerprint`, `parent_bom`
- **Risk management**: `risk_assessment`, `evaluations`
- **Human oversight**: `evaluations[*].notes`, `created_by`
- **Transparency**: `description`, `license`, `metadata`
- **Monitoring**: `evaluations[*].run_at`, webhook logs

### Contributing & conduct

See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

### Roadmap
### Operations & observability

- Structured JSON logs (request_id, optional trace_id)
- Prometheus metrics: request counts and latency histogram
- OpenTelemetry tracing: set `OTLP_ENDPOINT` to enable export
- Dashboards/alerts: sample Grafana dashboard in `ops/grafana-dashboard.json`

### CI/CD & security hardening

- Coverage gate: backend `pytest --cov-fail-under=70`, frontend `jest --coverage`
- Bandit SAST, Trivy image scan (fails on HIGH/CRITICAL), SBOM via Syft
- Alembic migrations run during CI; ensure `alembic upgrade head` on deploy

### Kubernetes hardening

- Non-root, read-only root filesystem, seccomp `RuntimeDefault`
- Probes: `/health` readiness/liveness
- Resources: cpu/memory requests/limits set; HPA provided
- NetworkPolicy example and separate worker Deployment
- TLS Ingress manifest; set `require_https=true` and configure cert-manager/ACME

### RBAC & auth

- JWT auth with Argon2 password hashing
- RBAC enforced on project and BOM operations; roles: owner, editor, viewer
- Password policy enforced at signup/reset; SSO placeholder documented

### Webhook verification

- GitHub webhook signature verified using raw request body (`X-Hub-Signature-256`)

### S3 security & lifecycle

- SSE: AES256 by default; KMS when `S3_KMS_KEY_ID` is provided
- Bucket policy and lifecycle helper: `scripts/s3_setup_policy_lifecycle.py`
- Upload size/type limits via config; multipart upload support

### Deployment

1. Set environment variables (`.env`) including `SECRET_KEY`, `OTLP_ENDPOINT`, S3, DB, Redis
2. Apply DB migrations: `alembic upgrade head`
3. Configure S3 bucket policy/lifecycle: `python scripts/s3_setup_policy_lifecycle.py`
4. Deploy K8s manifests (backend, worker, service, ingress, hpa, networkpolicy)
5. Set `cors_origins` to your frontend domains; set `require_https=true`


See `ROADMAP.md` for the 4-week plan and stretch goals.

### Backups

- Backup DB: `scripts/db_backup.sh`
- Restore DB: `scripts/db_restore.sh`

### License

MIT

