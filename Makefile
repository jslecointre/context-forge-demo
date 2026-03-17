#-include .env
-include ./.env
export $(shell sed 's/=.*//' ./.env)
# Override with: make build-mcp-server REPOSITORY=your-registry PLATFORM=linux/arm64
export REPOSITORY ?= us.icr.io/your-namespace
export PLATFORM ?= linux/amd64

export VERSION ?= 0.0.0
export PYTHON_VERSION ?= 3.12
export AGENT_ASSIST_NAME ?= agent-assist-app
export MCP_SERVER_NAME ?= mcp-server
export CONTEXT_FORGE_NAME ?= mcp-context-forge-plugin

# Tools
CONTAINER_CLI := docker
DOCKER_COMPOSE := docker compose

.DEFAULT_GOAL := help

.PHONY: run-mcp-server run-infra setup-context-forge stop-containers build-mcp-server build-mcp-context-forge-plugin tag-agent-assist-app-base push-agent-assist-app clean logs info

init-env:
	@touch .env
	@echo "PYTHON_VERSION=${PYTHON_VERSION}" >> .env

.PHONY: clean docker push run

build-mcp-server-base:
	$(CONTAINER_CLI) build --platform $(PLATFORM) --no-cache -t $(REPOSITORY)/$(MCP_SERVER_NAME)-base:$(VERSION) . -f ./mcp_servers/Dockerfile-mcp --build-arg VERSION=${VERSION} --build-arg REGISTRY=${REPOSITORY}

build-mcp-server:
	@test -f data/field-underwriting-manual-984e.pdf || wget -q -O data/field-underwriting-manual-984e.pdf https://www.bmo.com/advisor/PDFs/field-underwriting-manual-984e.pdf
	@test -f data/iaa.pdf || wget -q -O data/iaa.pdf https://iaa.secureweb.inalco.com/cw//cw/-/media/documents-repository/individual-insurance-savings-and-retirement/individual-insurance/2019/06/dev004399.pdf
	rm -rf store
	uv run .venv/bin/python mcp_servers/ingest.py --pdf field-underwriting-manual-984e.pdf --carrier BESAFE
	uv run .venv/bin/python mcp_servers/ingest.py --pdf iaa.pdf --carrier MOONLIFE
	$(CONTAINER_CLI) build --platform $(PLATFORM) --no-cache -t $(REPOSITORY)/$(MCP_SERVER_NAME):$(VERSION) . -f ./mcp_servers/Dockerfile-mcp --build-arg VERSION=${VERSION} --build-arg REGISTRY=${REPOSITORY}

build-base:
	$(CONTAINER_CLI) build --platform $(PLATFORM) --no-cache -t $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$(VERSION) . -f ./Dockerfile-base --build-arg VERSION=${VERSION}

build-agent-assist:
	$(CONTAINER_CLI) build --platform $(PLATFORM) --no-cache -t $(REPOSITORY)/$(AGENT_ASSIST_NAME):$(VERSION) . -f ./Dockerfile-agent-assist --build-arg VERSION=${VERSION} --build-arg REGISTRY=${REPOSITORY}

## build-mcp-context-forge-plugin: Build mcp-context-forge-plugin for IBM Code Engine (linux/amd64, registry tag)
build-context-forge-plugin:
	$(CONTAINER_CLI) build --platform linux/amd64 --no-cache \
		-t $(REPOSITORY)/$(CONTEXT_FORGE_NAME):$(VERSION) \
		-t mcp-context-forge-plugin \
		./context-forge-plugin -f ./context-forge-plugin/Dockerfile-context-forge-plugin


tag-agent-assist-app-base:
	@echo "Determining previous version..."
	@PREV_VERSION=$$(echo $(VERSION) | awk -F. '{print $$1"."$$2"."$$3-1}') && \
	echo "Previous version: $$PREV_VERSION" && \
	echo "Fetching Image ID for $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$$PREV_VERSION..." && \
	IMAGE_ID=$$($(CONTAINER_CLI) images --filter "reference=$(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$$PREV_VERSION" --format "{{.ID}}") && \
	if [ -n "$$IMAGE_ID" ]; then \
		echo "Image ID found: $$IMAGE_ID"; \
		echo "Tagging image $$IMAGE_ID as $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$(VERSION)"; \
		$(CONTAINER_CLI) tag $$IMAGE_ID $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$(VERSION); \
		echo "Successfully tagged $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$(VERSION)"; \
	else \
		echo "Error: No image found for $(REPOSITORY)/$(AGENT_ASSIST_NAME)-base:$$PREV_VERSION"; \
		exit 1; \
	fi

push:
	$(CONTAINER_CLI) push $(REPOSITORY)/$(MCP_SERVER_NAME):$(VERSION)

push-agent-assist-app:
	$(CONTAINER_CLI) push $(REPOSITORY)/$(AGENT_ASSIST_NAME):$(VERSION)

run-mcp-server:
	@echo "Starting MCP Server..."
	PROJECT_VERSION=${VERSION} REPOSITORY=${REPOSITORY} NAME=${NAME} $(DOCKER_COMPOSE) up -d underwriting_mcp_server health_mcp_server crm_mcp_server
	@echo "MCP Server is now running."

run-agent-assist:
	@echo "Starting AGENT ASSIST..."
	PROJECT_VERSION=${VERSION} REPOSITORY=${REPOSITORY} NAME=${AGENT_ASSIST_NAME} $(DOCKER_COMPOSE) up -d agent-assist
	@echo "AGENT ASSIST is now running."

run-infra:
	@echo "Starting infra and Context Forge..."
	$(DOCKER_COMPOSE) -f docker-compose-infra.yml --profile mcp up -d --build
	@echo "Infra and Context Forge are now running."


setup-context-forge:
	@echo "Running setup-context-forge..."
	PROJECT_VERSION=${VERSION} REPOSITORY=${REPOSITORY} NAME=${AGENT_ASSIST_NAME} $(DOCKER_COMPOSE) --profile mcp run --rm setup-context-forge
	@echo "setup-context-forge completed."

stop-containers:
	@echo "Stopping containers..."
	$(DOCKER_COMPOSE) down -v

clean: stop-containers
	@echo "Cleaning up existing containers and volumes..."
	-@$(CONTAINER_CLI) pod rm -f $$($(CONTAINER_CLI) pod ls -q) || true
	-@$(CONTAINER_CLI) rm -f $$($(CONTAINER_CLI) ps -aq) || true
	-@$(CONTAINER_CLI) volume prune -f || true
	-@$(CONTAINER_CLI) container prune -f || true
	rm -rf .pytest_cache .mypy_cache data volumes

logs:
	$(DOCKER_COMPOSE) logs -f
