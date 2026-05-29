.PHONY: build up down run-tests shell

build:
	docker compose build

up:
	docker compose up app

down:
	docker compose down

run-tests:
	docker compose run --rm --profile test test

shell:
	docker compose run --rm app bash
