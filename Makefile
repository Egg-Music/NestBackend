ENV_FILE=api/.env

.PHONY: up down logs rebuild shell test

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

rebuild:
	docker compose build --no-cache api

shell:
	docker compose exec api /bin/sh

test:
	curl -s localhost:8000/healthz && echo
	curl -s localhost:8000/readyz && echo
	curl -s -X POST localhost:8000/v1/chat -H "Content-Type: application/json" \
	  -d '{"messages":[{"role":"user","content":"Say hi in 3 words."}]}'


