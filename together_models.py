#!/usr/bin/env python3
"""
Together.ai Models Utility Script

Fetches model information from Together.ai API and generates YAML configuration files
for use with Continue 1.0 blocks.

Usage:
    python together_models.py [options]

Options:
    --api-key KEY     Together.ai API key (can also use TOGETHER_API_KEY env var)
    --input-file FILE Input JSON file with Together.ai models data (optional)
    --output-dir DIR  Output directory for YAML files (default: ./blocks/public)
    --skip-free       Skip free models (models with zero pricing)
    --summary         Print summary statistics
    --help            Show this help message and exit
"""

import argparse
import json
import os
import re
import sys
import yaml
from collections import Counter, defaultdict
from datetime import datetime
import requests

# Configuration
DEFAULT_OUTPUT_DIR = "./blocks/public"
TOGETHER_API_URL = "https://api.together.xyz/v1/models"

# Models configuration
# Models that should be assigned the autocomplete role
# Criteria for inclusion:
#  1. Should be fast (generally <8B parameters)
#  2. Must have sufficient context window (>= 8192 tokens for larger code samples)
#  3. Good performance on code completion and general assistance tasks
AUTOCOMPLETE_MODELS = [

    
    # Meta Llama 3 models (8B variants only)
    "Meta Llama 3 8B Instruct Lite",
    "Meta Llama 3 8B Instruct Turbo",
    "Meta Llama 3.1 8B Instruct Turbo",
    "Meta Llama 3 8B Instruct Reference",
    
    # Google models
    "Gemma Instruct (2B)",
    "Gemma-2 Instruct (9B)",
    
    # Mistral models
    "Mistral (7B) Instruct v0.2",
    "Mistral (7B)",
    
    # Add more models as needed
]

def sanitize_filename(name):
    """Convert the model name to a safe filename."""
    # Replace spaces with hyphens
    result = name.lower().replace(' ', '-')

    # Remove brackets, braces, and parentheses without replacement
    result = re.sub(r'[\[\]{}()]', '', result)

    # Replace any remaining unsafe characters with underscores
    # Keep hyphens (-) and underscores (_) intact
    result = re.sub(r'[^\w\-\.]', '_', result)

    # Reduce repeated underscores or hyphens to single instances
    result = re.sub(r'_+', '_', result)
    result = re.sub(r'-+', '-', result)

    # Strip trailing hyphens or underscores before .yaml extension
    result = re.sub(r'-+(\.yaml)$', r'\1', result)
    result = re.sub(r'_+(\.yaml)$', r'\1', result)

    return result

def determine_roles(model_data):
    """Determine appropriate roles based on model type and capabilities."""
    model_type = model_data.get('type', '')
    roles = []
    
    # Type-to-role mapping (based on analysis of Together's model catalog)
    type_to_role = {
        'chat': ['chat', 'edit'],
        'language': ['chat', 'edit'],  # Removed apply and autocomplete as defaults
        'embedding': ['embed'],
        'rerank': ['rerank'],
        'image': ['image'],
        'audio': ['audio'],
        'moderation': ['moderation']
    }
    
    # Add default roles based on type
    if model_type in type_to_role:
        roles.extend(type_to_role[model_type])
    
    # Additional roles based on context length
    if model_type in ['chat', 'language']:
        # Models with larger context are better for complex tasks like 'apply'
        context_length = model_data.get('context_length', 0)
        if context_length >= 8192 and 'apply' not in roles:  
            roles.append('apply')
    
    # Add autocomplete role based on the predefined list
    model_id = model_data.get('id', '')
    display_name = model_data.get('display_name', '')
    
    # Check if this model is in our autocomplete models list
    # Match by either display name or model ID
    if display_name in AUTOCOMPLETE_MODELS or model_id in AUTOCOMPLETE_MODELS:
        if 'autocomplete' not in roles:
            roles.append('autocomplete')
    
    # Remove duplicates and return sorted roles
    return sorted(list(set(roles)))

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


def create_yaml_file(model_data, output_dir=DEFAULT_OUTPUT_DIR):
    """Create a YAML file for a single model."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get model display name
    display_name = model_data.get('display_name', '')
    if not display_name:
        return None  # Skip if no display name
    
    # Get model ID
    model_id = model_data.get('id', '')
    if not model_id:
        return None  # Skip if no model ID
    
    # Determine roles
    roles = determine_roles(model_data)
    
    # Create YAML content
    yaml_content = {
        'name': display_name,
        'version': '1.0.0',
        'schema': 'v1',
        'models': [
            {
                'name': display_name,
                'provider': 'together',
                'model': model_id,
                'apiKey': '${{ inputs.TOGETHER_API_KEY }}',
                'roles': roles
            }
        ]
    }
    
    # Generate filename
    filename = sanitize_filename(display_name) + '.yaml'
    filepath = os.path.join(output_dir, filename)
    
    # Write YAML file with frontmatter, handling indentation manually
    with open(filepath, 'w') as file:
        file.write('---\n')  # Start frontmatter
        # Configure the YAML dumper to use 2-space indentation
        yaml.dump(yaml_content, file, Dumper=IndentDumper, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"Created YAML for {display_name}")
    return filepath, display_name, roles, model_data.get('type', 'unknown')


def fetch_models_data(api_key):
    """Fetch models data directly from the Together.ai API."""
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    
    try:
        print(f"Fetching models data from {TOGETHER_API_URL}...")
        response = requests.get(TOGETHER_API_URL, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}", file=sys.stderr)
        return None


def main():
    """Main function to parse arguments and generate YAML files."""
    parser = argparse.ArgumentParser(description='Generate YAML files for Together.ai models')
    parser.add_argument('-f', '--input-file', help='Input JSON file with Together.ai models data')
    parser.add_argument('-k', '--api-key', help='Together.ai API key')
    parser.add_argument('-o', '--output-dir', default=DEFAULT_OUTPUT_DIR, 
                        help='Output directory for YAML files')
    parser.add_argument('--skip-free', action='store_true',
                        help='Skip free models (models with zero pricing)')
    parser.add_argument('--summary', action='store_true',
                        help='Print summary statistics')
    
    args = parser.parse_args()
    
    # Determine API key (priority: command line, environment variable)
    api_key = args.api_key or os.environ.get('TOGETHER_API_KEY')
    
    # Get models data from API or file
    models_data = None
    
    if args.input_file:
        # Load from file
        try:
            with open(args.input_file, 'r') as file:
                models_data = json.load(file)
            print(f"Loaded {len(models_data)} models from {args.input_file}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading input file: {e}", file=sys.stderr)
            return 1
    elif api_key:
        # Fetch from API
        models_data = fetch_models_data(api_key)
        if not models_data:
            print("Failed to fetch models data from API.", file=sys.stderr)
            return 1
        print(f"Successfully fetched {len(models_data)} models from API")
    else:
        print("Error: Either --input-file or --api-key (or TOGETHER_API_KEY environment variable) must be provided", 
              file=sys.stderr)
        return 1
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save API response to file for reference if we fetched data
    if api_key and not args.input_file:
        output_file = os.path.join(args.output_dir, "together_api_response.json")
        try:
            with open(output_file, 'w') as file:
                json.dump(models_data, file, indent=2)
            print(f"Saved API response to {output_file}")
        except Exception as e:
            print(f"Warning: Could not save API response to file: {e}", file=sys.stderr)
    
    # Process models
    created_files = []
    skipped_models = []
    role_counter = Counter()
    model_types = Counter()
    model_by_role = defaultdict(list)
    
    for model_data in models_data:
        # Check if we should skip this model
        skip = False
        display_name = model_data.get('display_name', '')
        model_type = model_data.get('type', '')
        
        # Skip audio, image, and moderation models
        if model_type in ['audio', 'image', 'moderation']:
            skipped_models.append(f"{display_name} ({model_type})")
            skip = True
        
        # Check if it's a free model
        if args.skip_free and not skip:
            pricing = model_data.get('pricing', {})
            if pricing and pricing.get('input', 0) == 0 and pricing.get('output', 0) == 0:
                skipped_models.append(f"{display_name} (free)")
                skip = True
        
        if skip:
            continue
        
        # Create YAML file
        result = create_yaml_file(model_data, args.output_dir)
        if result:
            filepath, name, roles, model_type = result
            created_files.append((filepath, name))
            
            # Update statistics
            for role in roles:
                role_counter[role] += 1
                model_by_role[role].append(name)
            
            model_types[model_type] += 1
    
    # Print summary
    print(f"\nCreated {len(created_files)} YAML files in {args.output_dir}")
    if skipped_models:
        print(f"Skipped {len(skipped_models)} models")
    
    if args.summary:
        print("\n=== Summary Statistics ===")
        
        print("\nModel types:")
        for model_type, count in model_types.most_common():
            print(f"  {model_type}: {count} models")
        
        print("\nRoles distribution:")
        for role, count in role_counter.most_common():
            print(f"  {role}: {count} models")
            # Always show all models for autocomplete role
            if role == 'autocomplete' or len(model_by_role[role]) <= 5:
                for model in model_by_role[role]:
                    print(f"    - {model}")
            else:
                for model in model_by_role[role][:3]:  # Show first 3
                    print(f"    - {model}")
                print(f"    - ... and {count-3} more")
        
        # Print autocomplete eligibility statistics
        print("\nAutocomplete configuration:")
        print(f"  Predefined autocomplete models: {len(AUTOCOMPLETE_MODELS)}")
        print("  Models in predefined list:")
        for model in AUTOCOMPLETE_MODELS:
            print(f"    - {model}")
            
        # Check for models in the list that weren't found in the API
        found_models = set(model_by_role['autocomplete'])
        missing_models = [m for m in AUTOCOMPLETE_MODELS if m not in found_models]
        if missing_models:
            print("\n  Warning: The following models from AUTOCOMPLETE_MODELS were not found in the API data:")
            for model in missing_models:
                print(f"    - {model}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
