.PHONY: setup run run-file clean help test test-all test-unit test-models test-autocomplete test-exclusion stats lint-yaml fix-yaml

# Configuration
VENV_NAME := venv
PYTHON := python3
PIP := $(VENV_NAME)/bin/pip
PYTHON_VENV := $(VENV_NAME)/bin/python
OUTPUT_DIR := ./blocks/public
FILE := ./example-list.json

# Directory configuration
BLOCK_DIRS := blocks/public blocks/private
ASSISTANT_DIRS := assistants/public assistants/private
ALL_DIRS := $(BLOCK_DIRS) $(ASSISTANT_DIRS)

help:
	@echo "Together.ai Models Generator Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup            Create virtual environment and install requirements"
	@echo "  make run              Run the generator with the TOGETHER_API_KEY environment variable"
	@echo "  make run-file         Run the generator with a local JSON file (FILE=path/to/file.json)"
	@echo "  make test             Test the script with a --help flag to verify it works"
	@echo "  make test-all         Run all model role assignment tests (merged test file)"
	@echo "  make test-unit        Run unit tests (TestModelRoles class)"
	@echo "  make test-models      Run comprehensive model role assignment tests (legacy)"
	@echo "  make test-autocomplete Run tests focusing only on autocomplete role assignment"
	@echo "  make test-exclusion   Test exclusion of image, audio, and moderation models"
	@echo "  make stats            Show model role statistics without running tests"
	@echo "  make lint-yaml        Run YAML linter on all generated block files"
	@echo "  make fix-yaml         Fix indentation in all YAML files to meet linting rules"
	@echo "  make clean            Remove virtual environment and cached files"
	@echo "  make help             Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  TOGETHER_API_KEY      Your Together.ai API key (required for 'make run')"
	@echo "  FILE                  Path to a JSON file with model data (default: example-list.json)"
	@echo "  SKIP_FREE             Set to 1 to skip free models"

# Check for virtual environment
check-venv:
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi

setup:
	@echo "Setting up virtual environment..."
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "Installing requirements..."
	$(PIP) install -r requirements.txt
	@echo "Setup complete. You can now run 'make run' to generate YAML files."

run: check-venv | $(OUTPUT_DIR)
	@if [ -z "$(TOGETHER_API_KEY)" ]; then \
		echo "Error: TOGETHER_API_KEY environment variable is required."; \
		echo "Usage: TOGETHER_API_KEY=your_api_key make run"; \
		exit 1; \
	fi
	@echo "Running generator with API key..."
	$(PYTHON_VENV) together_models.py --api-key $(TOGETHER_API_KEY) -o $(OUTPUT_DIR) $(if $(SKIP_FREE),--skip-free,) --summary

run-file: check-venv | $(OUTPUT_DIR)
	@echo "Running generator with file: $(FILE)..."
	$(PYTHON_VENV) together_models.py --input-file "$(FILE)" -o $(OUTPUT_DIR) $(if $(SKIP_FREE),--skip-free,) --summary

# Create output directory if it doesn't exist
$(OUTPUT_DIR):
	@mkdir -p $@

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_NAME)
	rm -rf __pycache__
	find . -name "*.pyc" -delete
	@echo "Cleanup complete."

# Primary test target
test: check-venv
	@echo "Running all model role tests (merged test file)..."
	$(PYTHON_VENV) test_all.py -f "$(FILE)"

# Unit tests using the TestModelRoles class
test-unit: check-venv
	@echo "Running unit tests..."
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --unit-tests

test-exclusion: check-venv
	@echo "Testing exclusion of image, audio, and moderation models..."
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --exclusion-only

stats: check-venv
	@echo "Generating model role statistics..."
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --stats-only

lint-yaml: check-venv
	@echo "Running YAML linter on all generated block files..."
	@success=true; \
	for dir in $(BLOCK_DIRS) $(ASSISTANT_DIRS); do \
		if [ -d "$$dir" ]; then \
			echo "Linting YAML files in $$dir directory..."; \
			$(VENV_NAME)/bin/yamllint -c .yamllint.yml $$dir || success=false; \
		else \
			echo "No $$dir directory found."; \
		fi; \
	done; \
	$$success && echo "YAML linting passed." || (echo "YAML linting failed." && exit 1)
