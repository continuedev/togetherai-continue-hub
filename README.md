# Together.ai Model Generator for Continue Hub

This repository contains scripts to automatically generate YAML configurations for Together.ai models to use with [Continue](https://continue.dev/).

## Overview

The main script `together_models.py` fetches model information from the Together.ai API and generates YAML configuration files for use with Continue 1.0 blocks. It assigns appropriate roles to models based on their capabilities and characteristics, while excluding image, audio, and moderation models that aren't typically needed for development assistance.

## Model Role Logic

Models are assigned roles based on:

1. **Model type**: chat, language, embedding, or rerank (image, audio, and moderation models are excluded)
2. **Context length**: Models with context length >= 8192 are assigned the 'apply' role for more complex tasks
3. **Autocomplete role**: Only assigned to models in a curated list (AUTOCOMPLETE_MODELS) to ensure fast performance

## Autocomplete Role Configuration

The `AUTOCOMPLETE_MODELS` list in `together_models.py` defines which models get the autocomplete role. Criteria for inclusion:

1. Should be fast (generally <8B parameters)
2. Must have sufficient context window (>= 8192 tokens for larger code samples)
3. Good performance on code completion and general assistance tasks

Current autocomplete friendly models include:
- **Phi-3 series (Microsoft)**: Fast and efficient models
- **CodeLlama models (Meta)**: Specialized for code completion tasks
- **Meta Llama 3 models (8B variants only)**: Good balance of capabilities and speed
- **Google Gemma models (2B/9B)**: Lightweight models for quick responses
- **Mistral models (7B variants)**: Efficient open models with good performance
- **Other small but capable models**: TinyLlama, Qwen variants, etc.

## Usage

```bash
# Fetch models from Together.ai API and generate YAML files
python together_models.py --api-key YOUR_API_KEY [options]

# Or use a previously downloaded JSON file
python together_models.py --input-file together_api_response.json [options]

# Run tests on model role assignment
python run_test.py
```

### Options

- `--api-key KEY`: Together.ai API key (can also use TOGETHER_API_KEY env var)
- `--input-file FILE`: Input JSON file with Together.ai models data (optional)
- `--output-dir DIR`: Output directory for YAML files (default: ./blocks/public)
- `--skip-free`: Skip free models (models with zero pricing)
- `--summary`: Print summary statistics
- `--help`: Show help message and exit

Note: Image, audio, and moderation models are automatically excluded regardless of other options.

## Testing

Run the included test script to validate model role assignments:

```bash
python run_test.py
```

You can also run a simplified test specifically for autocomplete model assignment:

```bash
python run_final.py
```

These tests check that:
- Only models in the AUTOCOMPLETE_MODELS list get the autocomplete role
- Models with context length < 8192 don't get the 'apply' role
- Image, audio, and moderation models are correctly identified for exclusion
- Verify which models from your list are available in the data
- Display statistics about role distributions
