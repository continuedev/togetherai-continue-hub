#!/usr/bin/env python3
"""
Comprehensive test script for Together.ai model role assignment

This script verifies that model roles are correctly assigned based on:
1. Model type (chat, language, embedding, etc.)
2. Context length (for 'apply' role)
3. Membership in AUTOCOMPLETE_MODELS list (for 'autocomplete' role)
4. Exclusion of image, audio, and moderation models

It combines both unit tests (TestModelRoles class) and functional tests with detailed reporting.
"""

import json
import sys
import argparse
import unittest
from collections import Counter
from together_models import determine_roles_and_capabilities, AUTOCOMPLETE_MODELS


def load_test_data(file_path):
    """Load the test data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{file_path}'", file=sys.stderr)
        sys.exit(1)


class TestModelRoles(unittest.TestCase):
    """Test cases for model role assignment."""

    def setUp(self):
        """Load the example models data for testing."""
        try:
            with open('example-list.json', 'r') as f:
                self.models_data = json.load(f)
            print(f"Loaded {len(self.models_data)} models for testing")
        except FileNotFoundError:
            print("Error: example-list.json not found", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in example-list.json", file=sys.stderr)
            sys.exit(1)

    def test_autocomplete_role_assignment(self):
        """Test that only models in the AUTOCOMPLETE_MODELS list get the autocomplete role."""
        autocomplete_models = []
        non_autocomplete_models = []

        # Process all models
        for model_data in self.models_data:
            model_type = model_data.get('type', '')
            if model_type in ['image', 'audio', 'moderation']:
                continue  # Skip image, audio, and moderation models
                
            roles, _ = determine_roles_and_capabilities(model_data)
            display_name = model_data.get('display_name', '')
            model_id = model_data.get('id', '')
            
            # Check if model is assigned autocomplete role
            if 'autocomplete' in roles:
                autocomplete_models.append((display_name, model_id))
            else:
                non_autocomplete_models.append((display_name, model_id))
        
        # Check that only models in AUTOCOMPLETE_MODELS list have autocomplete role
        for name, model_id in autocomplete_models:
            # The model should be in the allowed list (by name or ID)
            self.assertTrue(
                name in AUTOCOMPLETE_MODELS or model_id in AUTOCOMPLETE_MODELS,
                f"Model '{name}' was assigned autocomplete role but is not in AUTOCOMPLETE_MODELS list"
            )

        # Report on missing models (for informational purposes, not a test failure)
        found_models = set([m[0] for m in autocomplete_models] + [m[1] for m in autocomplete_models])
        missing_models = [m for m in AUTOCOMPLETE_MODELS if m not in found_models]
        if missing_models:
            print("\nWarning: The following models from AUTOCOMPLETE_MODELS were not found in the test data:")
            for model in missing_models:
                print(f"  - {model}")

    def test_context_window_requirement(self):
        """Test that models with context length < 8192 don't get 'apply' role."""
        for model_data in self.models_data:
            model_type = model_data.get('type', '')
            if model_type in ['image', 'audio', 'moderation']:
                continue  # Skip image, audio, and moderation models
                
            roles, _ = determine_roles_and_capabilities(model_data)
            context_length = model_data.get('context_length', 0)
            display_name = model_data.get('display_name', '')
            
            if context_length < 8192 and 'apply' in roles:
                self.fail(f"Model '{display_name}' has context_length {context_length} < 8192 but was assigned 'apply' role")

    def test_image_audio_moderation_exclusion(self):
        """Test that image, audio, and moderation models are identified."""
        excluded_models = []
        
        for model_data in self.models_data:
            model_type = model_data.get('type', '')
            display_name = model_data.get('display_name', '')
            
            if model_type in ['image', 'audio', 'moderation']:
                excluded_models.append((display_name, model_type))
        
        # This is an informational test, not a pass/fail test
        if excluded_models:
            print(f"\nFound {len(excluded_models)} image, audio, and moderation models that will be excluded")
            # We don't need to print all of them in the unit test
        else:
            print("\nNo image, audio, or moderation models found in the test data")


def test_autocomplete_role(models_data):
    """Test that autocomplete role is only assigned to whitelisted models."""
    autocomplete_models = []
    violations = []

    for model_data in models_data:
        model_type = model_data.get('type', '')
        if model_type in ['image', 'audio', 'moderation']:
            continue  # Skip image, audio, and moderation models

        roles, _ = determine_roles_and_capabilities(model_data)
        display_name = model_data.get('display_name', '')
        model_id = model_data.get('id', '')
        
        if 'autocomplete' in roles:
            autocomplete_models.append(display_name)
            
            # Check if the model is in the whitelist
            if display_name not in AUTOCOMPLETE_MODELS and model_id not in AUTOCOMPLETE_MODELS:
                violations.append(display_name)
    
    if violations:
        print("\nERROR: The following models were assigned autocomplete role but are not in AUTOCOMPLETE_MODELS list:")
        for model in violations:
            print(f"  - {model}")
        return False
    
    print(f"\n✓ All {len(autocomplete_models)} models with autocomplete role are in the whitelist")
    return True


def test_context_window_requirement(models_data):
    """Test that models with small context windows don't get 'apply' role."""
    violations = []
    
    for model_data in models_data:
        model_type = model_data.get('type', '')
        if model_type in ['image', 'audio', 'moderation']:
            continue  # Skip image, audio, and moderation models
            
        roles, _ = determine_roles_and_capabilities(model_data)
        context_length = model_data.get('context_length', 0)
        display_name = model_data.get('display_name', '')
        
        if context_length < 8192 and 'apply' in roles:
            violations.append((display_name, context_length))
    
    if violations:
        print("\nERROR: The following models with context length < 8192 were assigned 'apply' role:")
        for model, ctx_len in violations:
            print(f"  - {model} (context: {ctx_len})")
        return False
    
    print("\n✓ No models with context length < 8192 were assigned 'apply' role")
    return True


def test_image_audio_moderation_exclusion(models_data):
    """Test that image, audio, and moderation models are identified for exclusion."""
    excluded_models = []
    
    for model_data in models_data:
        model_type = model_data.get('type', '')
        display_name = model_data.get('display_name', '')
        
        if model_type in ['image', 'audio', 'moderation']:
            excluded_models.append((display_name, model_type))
    
    if excluded_models:
        print(f"\nFound {len(excluded_models)} image, audio, and moderation models that will be excluded:")
        for model, model_type in sorted(excluded_models, key=lambda x: x[1]):
            print(f"  - {model} ({model_type})")
        print("✓ These models will be excluded when generating YAML files")
    else:
        print("\nNo image, audio, or moderation models found in the test data")
    
    return True  # This test is informational only


def check_missing_models(models_data):
    """Check which models from our autocomplete list are not in the data."""
    found_models = set()
    
    for model_data in models_data:
        display_name = model_data.get('display_name', '')
        model_id = model_data.get('id', '')
        if display_name in AUTOCOMPLETE_MODELS or model_id in AUTOCOMPLETE_MODELS:
            found_models.add(display_name if display_name in AUTOCOMPLETE_MODELS else model_id)
    
    missing_models = [m for m in AUTOCOMPLETE_MODELS if m not in found_models]
    
    if missing_models:
        print(f"\nNote: {len(missing_models)} models from AUTOCOMPLETE_MODELS were not found in the test data:")
        for model in sorted(missing_models):
            print(f"  - {model}")
    else:
        print("\n✓ All models in AUTOCOMPLETE_MODELS were found in the test data")
    
    return missing_models


def print_role_statistics(models_data):
    """Print statistics about role distributions."""
    role_counter = Counter()
    model_types = Counter()
    models_by_role = {}
    
    # Count excluded models separately
    excluded_models = []
    
    for model_data in models_data:
        model_type = model_data.get('type', 'unknown')
        display_name = model_data.get('display_name', '')
        
        # Track excluded models
        if model_type in ['image', 'audio', 'moderation']:
            excluded_models.append((display_name, model_type))
            model_types[model_type] += 1
            continue
        
        # Process roles for non-image, non-audio models
        roles, _ = determine_roles_and_capabilities(model_data)
        model_types[model_type] += 1
        for role in roles:
            role_counter[role] += 1
            if role not in models_by_role:
                models_by_role[role] = []
            models_by_role[role].append(display_name)
    
    print("\n=== Role Distribution Statistics ===")
    print(f"\nTotal models: {len(models_data)}")
    print(f"Excluded models (image, audio, moderation): {len(excluded_models)}")
    print(f"Included models: {len(models_data) - len(excluded_models)}")
    
    print("\nModel types:")
    for model_type, count in model_types.most_common():
        print(f"  {model_type}: {count} models")
    
    print("\nRoles distribution:")
    for role, count in role_counter.most_common():
        print(f"  {role}: {count} models")
        # Always show all models for autocomplete role
        if role == 'autocomplete':
            for model in sorted(models_by_role[role]):
                print(f"    - {model}")
        elif len(models_by_role[role]) <= 5:  # Show all if <= 5 models
            for model in sorted(models_by_role[role]):
                print(f"    - {model}")
        else:
            for model in sorted(models_by_role[role])[:3]:  # Show first 3
                print(f"    - {model}")
            print(f"    - ... and {count-3} more")


def run_unit_tests(test_file=None):
    """Run the unittest-based tests."""
    # Use a custom test loader to run tests with our custom arguments
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestModelRoles)
    
    # Run the tests
    result = unittest.TextTestRunner().run(suite)
    
    # Return True if all tests passed, False otherwise
    return result.wasSuccessful()


def main():
    """Main function to run tests on model role assignments."""
    parser = argparse.ArgumentParser(description='Test Together.ai model role assignments')
    parser.add_argument('-f', '--file', default='example-list.json',
                        help='Path to JSON file with model data (default: example-list.json)')
    parser.add_argument('--unit-tests', action='store_true',
                        help='Run unittest-based tests')
    parser.add_argument('--autocomplete-only', action='store_true',
                        help='Only test autocomplete role assignment')
    parser.add_argument('--exclusion-only', action='store_true',
                        help='Only test exclusion of image and audio models')
    parser.add_argument('--stats-only', action='store_true',
                        help='Only show statistics without running tests')
    
    args = parser.parse_args()
    
    # Load model data
    models_data = load_test_data(args.file)
    print(f"Loaded {len(models_data)} models for testing")
    
    if args.unit_tests:
        # Run the unittest-based tests
        tests_passed = run_unit_tests()
        return 0 if tests_passed else 1
    
    if args.stats_only:
        print_role_statistics(models_data)
        check_missing_models(models_data)
        return 0
    
    # Run tests
    tests_passed = True
    
    if args.autocomplete_only:
        # Only run autocomplete tests
        autocomplete_test = test_autocomplete_role(models_data)
        missing_models = check_missing_models(models_data)
        print_role_statistics(models_data)
        return 0 if autocomplete_test else 1
    elif args.exclusion_only:
        # Only run exclusion tests
        exclusion_test = test_image_audio_moderation_exclusion(models_data)
        print_role_statistics(models_data)
        return 0
    else:
        # Run all tests
        autocomplete_test = test_autocomplete_role(models_data)
        context_test = test_context_window_requirement(models_data)
        exclusion_test = test_image_audio_moderation_exclusion(models_data)
        missing_models = check_missing_models(models_data)
        
        tests_passed = autocomplete_test and context_test
        
        # Print statistics
        print_role_statistics(models_data)
        
        return 0 if tests_passed else 1


if __name__ == "__main__":
    sys.exit(main())
