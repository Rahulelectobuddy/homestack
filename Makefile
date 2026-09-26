# Homelab Data Platform Control Makefile

REGISTRY ?= localhost:5000

.PHONY: help build-all deploy-platform deploy-apps status

help:
	@echo "Homelab Data Platform Helper Commands:"
	@echo "  make build-all        Build and push all container images to local registry"
	@echo "  make deploy-platform  Deploy platform containers on 8GB VM"
	@echo "  make deploy-apps      Pull and start app containers on 4GB VM"
	@echo "  make status           Check platform container status"

build-all:
	@chmod +x scripts/build-and-push-all.sh
	./scripts/build-and-push-all.sh $(REGISTRY)

deploy-platform:
	cd infra/platform && docker compose up -d

deploy-apps:
	cd infra/apps && docker compose pull && docker compose up -d

status:
	cd infra/platform && docker compose ps
