IMAGE_NAME ?= google-drive-export-bundles
CONTAINER_FNAME ?= Containerfile
KEY_FILE ?=
OUTPUT_DIR ?= $(PWD)/output
ARGS ?= --help
PODMAN_FLAGS ?= -it

.PHONY: help podman-build podman-build-force podman-run

help:
	@echo "make podman-build       - Build the local image"
	@echo "make podman-build-force - Rebuild without cache"
	@echo "make podman-run         - Run the tool in the container"
	@echo ""
	@echo "Optional vars:"
	@echo "  KEY_FILE=/path/to/service-account.json"
	@echo "  OUTPUT_DIR=$(PWD)/output"
	@echo "  ARGS='--label ds551-202601-S26 --file <url-or-id>'"
	@echo "  PODMAN_FLAGS='-it' (set empty for non-interactive runs)"

podman-build:
	@podman build -t $(IMAGE_NAME) --file=$(CONTAINER_FNAME) .

podman-build-force:
	@podman build -t $(IMAGE_NAME) --file=$(CONTAINER_FNAME) --no-cache .

podman-run:
	@if [ -z "$(KEY_FILE)" ]; then \
		echo "KEY_FILE is required"; \
		exit 1; \
	fi
	@mkdir -p "$$(dirname "$(OUTPUT_DIR)")"
	@podman run --rm $(PODMAN_FLAGS) \
		-v $(KEY_FILE):/secrets/service_account.json:ro,Z \
		-v $(OUTPUT_DIR):/output:Z \
		-e GOOGLE_APPLICATION_CREDENTIALS=/secrets/service_account.json \
		$(IMAGE_NAME) $(ARGS) --output-dir /output
