start:
	cd backend && uvicorn ai_bom.main:create_app --factory --host 0.0.0.0 --port 8000

build:
	docker compose -f backend/docker-compose.yml build

up:
	docker compose -f backend/docker-compose.yml up

down:
	docker compose -f backend/docker-compose.yml down

lint:
	cd backend && ruff . && black --check . && isort --check-only .

format:
	cd backend && black . && isort .

test:
	cd backend && pytest -q

deploy-local:
	bash scripts/deploy.sh