# Homelab Data Platform Unified Makefile

REGISTRY ?= localhost:5000

.PHONY: help build-all deploy status stop logs restart test

help:
	@echo "Homelab Data Platform Helper Commands:"
	@echo "  make build-all   Build and push all container images to local registry"
	@echo "  make deploy      Deploy full unified platform and app stack"
	@echo "  make test        Run automated post-deployment validation suite"
	@echo "  make status      Check running container status"
	@echo "  make stop        Stop all containers"
	@echo "  make restart     Restart all containers"
	@echo "  make logs        View live container logs"

build-all:
	@chmod +x scripts/build-and-push-all.sh
	./scripts/build-and-push-all.sh $(REGISTRY)

deploy:
	docker compose up -d
	@chmod +x scripts/test-stack.sh
	./scripts/test-stack.sh 192.168.1.29

test:
	@chmod +x scripts/test-stack.sh
	./scripts/test-stack.sh 192.168.1.29

status:
	docker compose ps

stop:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

