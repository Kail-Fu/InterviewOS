.PHONY: dev dev-full down

dev:
	docker compose up --build

# Backward-compatible alias; the default stack now includes the grader.
dev-full: dev

down:
	docker compose down
