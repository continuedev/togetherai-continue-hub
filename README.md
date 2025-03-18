# Together.ai Model Generator for Continue Hub

This repository contains scripts to automatically generate YAML configurations for Together.ai models to use with [Continue](https://continue.dev/).

## Overview

The main script `together_models.py` fetches model information from the Together.ai API and generates YAML configuration files for use with Continue 1.0 blocks. It assigns appropriate roles to models based on their capabilities and characteristics, while excluding image, audio, and moderation models that aren't typically needed for development assistance.

## Key Features

- 🔄 **Automatic Updates**: Runs nightly to capture new models as they become available
- 📊 **Version Tracking**: Maintains semantic versioning for each model YAML file
- 🔍 **Change Detection**: Only updates YAMLs when model configuration changes
- 🛠️ **Role Assignment**: Intelligently assigns appropriate roles based on model capabilities
- 📝 **Pull Request Generation**: Automatically creates PRs for model updates

## Model Role Logic

Models are assigned roles based on:

1. **Model type**: chat, language, embedding, or rerank (image, audio, and moderation models are excluded)
2. **Context length**: Models with context length >= 8192 are assigned the 'apply' role for more complex tasks
3. **Autocomplete role**: Only assigned to models in a curated list (AUTOCOMPLETE_MODELS) to ensure fast performance

## Versioning

The generator maintains semantic versioning for each YAML configuration:

- **Major version**: Incremented for backward-incompatible changes
- **Minor version**: Incremented when model properties change (roles, context window, etc.)
- **Patch version**: Incremented for minor fixes or updates

When a model's configuration changes (different roles, context length, etc.), the minor version is automatically incremented.

## Usage

```bash
# Fetch models from Together.ai API and generate YAML files
python together_models.py --api-key YOUR_API_KEY [options]

# Or use a previously downloaded JSON file
python together_models.py --input-file together_api_response.json [options]

# Run with summary statistics
python together_models.py --summary
```

### Options

- `--api-key KEY`: Together.ai API key (can also use TOGETHER_API_KEY env var)
- `--input-file FILE`: Input JSON file with Together.ai models data (optional)
- `--output-dir DIR`: Output directory for YAML files (default: ./blocks/public)
- `--skip-free`: Skip free models (models with zero pricing)
- `--summary`: Print summary statistics
- `--force-regenerate`: Force regeneration of all YAML files
- `--help`: Show help message and exit

## GitHub Workflow

A GitHub Actions workflow is set up to run the script nightly:

1. Fetches the latest model data from Together.ai
2. Updates YAML configurations as needed
3. Increments version numbers for changed models
4. Creates a pull request with the changes

## Testing

Use the included test script to validate model role assignments:

```bash
python test_all.py
```

This tests that:
- Only models in the AUTOCOMPLETE_MODELS list get the autocomplete role
- Models with context length < 8192 don't get the 'apply' role
- Image, audio, and moderation models are correctly identified for exclusion

## Contributing

To contribute or modify the model role logic:

1. Update the `AUTOCOMPLETE_MODELS` list in `together_models.py` to add or remove models eligible for the autocomplete role
2. Modify the `determine_roles` function to change how roles are assigned
3. Run the script locally to test your changes
4. Submit a PR with the updated script and YAML files