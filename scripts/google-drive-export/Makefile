IMAGE_NAME ?= google-drive-export-bundles
CONTAINER_FNAME ?= Containerfile
KEY_FILE ?=
OUTPUT_DIR ?= $(PWD)/output
SUBDIR ?=
ARGS ?= --help
PODMAN_FLAGS ?= -it

# If SUBDIR is set, write into OUTPUT_DIR/SUBDIR; otherwise write directly into OUTPUT_DIR
ifdef SUBDIR
_TARGET_DIR = $(OUTPUT_DIR)/$(SUBDIR)
else
_TARGET_DIR = $(OUTPUT_DIR)
endif

.PHONY: help podman-build podman-build-force podman-run

help:
	@echo "make podman-build       - Build the local image"
	@echo "make podman-build-force - Rebuild without cache"
	@echo "make podman-run         - Run the tool in the container"
	@echo ""
	@echo "Required vars:"
	@echo "  KEY_FILE=/path/to/service-account.json"
	@echo ""
	@echo "Optional vars:"
	@echo "  OUTPUT_DIR=$(PWD)/output   base output directory"
	@echo "  SUBDIR=ds100-sum26         creates and uses OUTPUT_DIR/SUBDIR as target"
	@echo "  ARGS='--label ds100-sum26 --folder <url-or-id>'"
	@echo "  PODMAN_FLAGS='-it' (set empty for non-interactive runs)"
	@echo ""
	@echo "Examples:"
	@echo "  make podman-run KEY_FILE=~/key.json SUBDIR=ds100-sum26 ARGS='--folder <id>'"

podman-build:
	@podman build -t $(IMAGE_NAME) --file=$(CONTAINER_FNAME) .

podman-build-force:
	@podman build -t $(IMAGE_NAME) --file=$(CONTAINER_FNAME) --no-cache .

podman-run:
	@if [ -z "$(KEY_FILE)" ]; then \
		echo "KEY_FILE is required"; \
		exit 1; \
	fi
	@mkdir -p "$(_TARGET_DIR)"
	@echo "Output target: $(_TARGET_DIR)"
	@podman run --rm $(PODMAN_FLAGS) \
		-v $(KEY_FILE):/secrets/service_account.json:ro,Z \
		-v $(_TARGET_DIR):/output:Z \
		-e GOOGLE_APPLICATION_CREDENTIALS=/secrets/service_account.json \
		$(IMAGE_NAME) $(ARGS) --output-dir /output
