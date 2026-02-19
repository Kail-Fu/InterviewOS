.PHONY: dev down

dev:
	docker compose up --build

down:
	docker compose down
