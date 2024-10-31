# Makefile

# Image name
IMAGE_NAME = megaparse

# Dockerfile location
DOCKERFILE = Dockerfile

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) -f $(DOCKERFILE) .
dev:
	docker build -t $(IMAGE_NAME) . && docker run -p 8000:8000 $(IMAGE_NAME)
.PHONY: build
