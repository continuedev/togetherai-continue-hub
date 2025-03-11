.PHONY: setup run run-file clean help test test-all test-unit test-models test-autocomplete test-exclusion stats lint-yaml fix-yaml

VENV_NAME := venv
PYTHON := python3
PIP := $(VENV_NAME)/bin/pip
PYTHON_VENV := $(VENV_NAME)/bin/python
OUTPUT_DIR := ./blocks/public
FILE := ./example-list.json

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

setup:
	@echo "Setting up virtual environment..."
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "Installing requirements..."
	$(PIP) install -r requirements.txt
	@echo "Setup complete. You can now run 'make run' to generate YAML files."

run:
	@if [ -z "$(TOGETHER_API_KEY)" ]; then \
		echo "Error: TOGETHER_API_KEY environment variable is required."; \
		echo "Usage: TOGETHER_API_KEY=your_api_key make run"; \
		exit 1; \
	fi
	@echo "Running generator with API key..."
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON_VENV) together_models.py --api-key $(TOGETHER_API_KEY) -o $(OUTPUT_DIR) $(if $(SKIP_FREE),--skip-free,) --summary

run-file:
	@echo "Running generator with file: $(FILE)..."
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON_VENV) together_models.py --input-file "$(FILE)" -o $(OUTPUT_DIR) $(if $(SKIP_FREE),--skip-free,) --summary

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_NAME)
	rm -rf __pycache__
	@echo "Cleanup complete."

# Primary test target 
test:
	@echo "Running all model role tests (merged test file)..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: Test data file '$(FILE)' not found."; \
		exit 1; \
	fi
	$(PYTHON_VENV) test_all.py -f "$(FILE)"

# Unit tests using the TestModelRoles class
test-unit:
	@echo "Running unit tests..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: Test data file '$(FILE)' not found."; \
		exit 1; \
	fi
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --unit-tests


test-exclusion:
	@echo "Testing exclusion of image, audio, and moderation models..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: Test data file '$(FILE)' not found."; \
		exit 1; \
	fi
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --exclusion-only

stats:
	@echo "Generating model role statistics..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: Test data file '$(FILE)' not found."; \
		exit 1; \
	fi
	$(PYTHON_VENV) test_all.py -f "$(FILE)" --stats-only

lint-yaml: 
	@echo "Running YAML linter on all generated block files..."

	@if [ -d "blocks/public" ]; then \
		echo "Linting YAML files in blocks/public directory..."; \
		$(VENV_NAME)/bin/yamllint -c .yamllint.yml blocks/public || true; \
	else \
		echo "No blocks/public directory found."; \
	fi
	@if [ -d "blocks/private" ]; then \
		echo "Linting YAML files in blocks/private directory..."; \
		$(VENV_NAME)/bin/yamllint -c .yamllint.yml blocks/private || true; \
	else \
		echo "No blocks/private directory found."; \
	fi
	@if [ -d "assistants/public" ]; then \
		echo "Linting YAML files in assistants/public directory..."; \
		$(VENV_NAME)/bin/yamllint -c .yamllint.yml assistants/public || true; \
	else \
		echo "No assistants/public directory found."; \
	fi
	@if [ -d "assistants/private" ]; then \
		echo "Linting YAML files in assistants/private directory..."; \
		$(VENV_NAME)/bin/yamllint -c .yamllint.yml assistants/private || true; \
	else \
		echo "No assistants/private directory found."; \
	fi
	@echo "YAML linting complete."