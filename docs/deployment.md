## Deployment

Use Docker images for backend and frontend. For production, deploy on Kubernetes using manifests in `k8s/` or the Helm chart skeleton in `helm/`.

- Use managed Postgres (RDS/CloudSQL), S3 for artifacts, Redis for queues
- Set `SECRET_KEY` and use HTTPS/TLS at ingress
- Scale Celery workers and API separately

