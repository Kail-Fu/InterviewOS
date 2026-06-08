.PHONY: dev dev-full down

dev:
	docker compose up --build

dev-full:
	REPORT_GRADER_PROVIDER=worker docker compose --profile full up --build

down:
	docker compose down
