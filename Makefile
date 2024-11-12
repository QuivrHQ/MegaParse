.DEFAULT_TARGET=help

## help: Display list of commands
.PHONY: help
help:
	@echo "Available commands:"
	@sed -n 's|^##||p' $(MAKEFILE_LIST) | column -t ':' | sed -e 's|^| |'

## dev: Start development environment
.PHONY: dev
dev:
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.dev.yml up --build

## dev-build: Build development environment without cache
.PHONY: dev-build
dev-build:
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.dev.yml build --no-cache
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.dev.yml up

## prod: Build and start production environment
.PHONY: prod
prod:
	docker compose -f docker-compose.yml up --build
