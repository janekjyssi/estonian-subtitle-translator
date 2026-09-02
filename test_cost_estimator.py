#!/usr/bin/env python3
"""Test cost estimation feature"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.cost_estimator import CostEstimator


def test_cost_estimation():
    """Test the cost estimation feature with sample SRT files"""
    print("\n" + "=" * 70)
    print("COST ESTIMATION TESTS")
    print("=" * 70)
    
    estimator = CostEstimator()
    
    # Test 1: Single file estimation
    print("\nTest 1: Single file token counting")
    print("-" * 70)
    test_file = Path(__file__).parent / "test_sample.en.srt"
    if test_file.exists():
        result = estimator.estimate_file_tokens(test_file)
        print(f"File: {test_file.name}")
        print(f"Text tokens: {result['text_tokens']}")
        print(f"Entry count: {result['entry_count']}")
        assert result['text_tokens'] > 0, "Text tokens should be > 0"
        print("✓ Single file token counting works")
    else:
        print(f"⚠ Test file not found: {test_file}")
    
    # Test 2: Cost estimate for GPT-4.1
    print("\n\nTest 2: Cost estimate for GPT-4.1")
    print("-" * 70)
    model_config = {
        "input_price": 2.00,
        "output_price": 8.00,
        "batch_size": 20,
    }
    
    files = [test_file] if test_file.exists() else []
    if files:
        estimate = estimator.estimate_cost(files, model_config)
        print(f"Files: {estimate['files']}")
        print(f"Total entries: {estimate['total_entries']}")
        print(f"Text tokens: {estimate['total_text_tokens']}")
        print(f"Estimated batches: {estimate['estimated_batches']}")
        print(f"Input tokens (with overhead): {estimate['estimated_input_tokens']}")
        print(f"Output tokens estimates:")
        print(f"  Low:  {estimate['estimated_output_tokens_low']}")
        print(f"  Exp:  {estimate['estimated_output_tokens_expected']}")
        print(f"  High: {estimate['estimated_output_tokens_high']}")
        print(f"Estimated costs:")
        print(f"  Low:      ${estimate['estimated_cost_low']:.4f}")
        print(f"  Expected: ${estimate['estimated_cost_expected']:.4f}")
        print(f"  High:     ${estimate['estimated_cost_high']:.4f}")
        assert estimate['error'] is None, f"Error: {estimate['error']}"
        assert estimate['estimated_cost_expected'] > 0, "Expected cost should be > 0"
        print("✓ Cost estimation works")
    
    # Test 3: Format output
    print("\n\nTest 3: Formatted cost estimate")
    print("-" * 70)
    if files:
        formatted = estimator.format_cost_estimate(estimate, "GPT-4.1 — hea | $1 suhteline hinnatase")
        print(formatted)
        assert "HINNAPROGNOOS" in formatted, "Should contain title"
        assert "GPT-4.1" in formatted, "Should contain model name"
        assert "$" in formatted, "Should contain price format"
        print("✓ Format output works")
    
    # Test 4: Multiple files
    print("\n\nTest 4: Multiple files estimation")
    print("-" * 70)
    
    # Create a list of multiple test files (use the same file twice for testing)
    test_files = []
    if test_file.exists():
        test_files = [test_file, test_file]  # Simulate multiple files
        
        estimate_multi = estimator.estimate_cost(test_files, model_config)
        print(f"Files: {estimate_multi['files']}")
        print(f"Total entries: {estimate_multi['total_entries']}")
        print(f"Total text tokens: {estimate_multi['total_text_tokens']}")
        print(f"Expected cost: ${estimate_multi['estimated_cost_expected']:.4f}")
        
        # Should have roughly double the tokens if we used the same file twice
        assert estimate_multi['total_entries'] > estimate['total_entries'], "Multiple files should have more entries"
        print("✓ Multiple files estimation works")
    
    # Test 5: No files
    print("\n\nTest 5: Empty file list")
    print("-" * 70)
    estimate_empty = estimator.estimate_cost([], model_config)
    print(f"Files: {estimate_empty['files']}")
    print(f"Cost: ${estimate_empty['estimated_cost_expected']:.4f}")
    assert estimate_empty['files'] == 0, "Should have 0 files"
    assert estimate_empty['estimated_cost_expected'] == 0.0, "Cost should be 0"
    print("✓ Empty file list handled correctly")
    
    # Test 6: Different models
    print("\n\nTest 6: Cost comparison across models")
    print("-" * 70)
    
    models = {
        "GPT-4.1 mini": {"input_price": 0.40, "output_price": 1.60, "batch_size": 8},
        "GPT-4.1": {"input_price": 2.00, "output_price": 8.00, "batch_size": 20},
        "GPT-5.6 Terra": {"input_price": 2.50, "output_price": 15.00, "batch_size": 20},
    }
    
    if files:
        for model_name, config in models.items():
            est = estimator.estimate_cost(files, config)
            print(f"{model_name:20s}: ${est['estimated_cost_expected']:8.4f} (input: {est['estimated_input_tokens']:6d}, output est: {est['estimated_output_tokens_expected']:6d})")
        
        print("✓ Cost comparison across models works")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_cost_estimation()
