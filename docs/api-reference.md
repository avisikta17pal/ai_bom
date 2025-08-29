## API Reference

Base URL: `/api/v1`

- POST `/auth/login` -> JWT
- POST `/projects` -> create project
- GET `/projects/{id}` -> project detail
- POST `/projects/{id}/boms` -> upload BOM
- GET `/boms/{version_id}` -> get BOM version
- GET `/boms/{version_id}/export?format=json|jsonld|pdf` -> export
- POST `/webhook/github` -> GitHub webhook

OpenAPI docs available at `/docs` and `/redoc`.

