#!/usr/bin/make

USER=javipolo
NAME=caulk
VERSION=v0.1.0${SUFFIX}
IMAGE=${USER}/${NAME}:${VERSION}
LATEST=${USER}/${NAME}:latest

all: build

run: ## Run image
	docker run ${IMAGE}

shell: ## Run image and get a shell
	docker run -it ${IMAGE} sh

build: ## Build image
	docker build -t ${IMAGE} .
	docker tag ${IMAGE} ${LATEST}

push: ## Push image to docker
	docker push ${IMAGE}
	docker push ${LATEST}

help:   ## Shows this message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: all build publish help
