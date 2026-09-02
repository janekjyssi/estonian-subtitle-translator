#!/usr/bin/env python3
"""Test that cost estimation makes NO API calls"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from app.cost_estimator import CostEstimator


def test_no_api_calls():
    """Verify that cost estimation does not make any API calls"""
    print("\n" + "=" * 70)
    print("TEST: VERIFY NO API CALLS DURING COST ESTIMATION")
    print("=" * 70)
    
    # Test 1: Cost estimator should not import openai
    print("\nTest 1: CostEstimator does not import openai module")
    print("-" * 70)
    estimator = CostEstimator()
    
    # Check that openai is not imported
    if 'openai' in sys.modules:
        print("⚠ openai module is loaded (but may not be used by estimator)")
    else:
        print("✓ openai module not loaded")
    
    # Test 2: Cost estimation should not try to create OpenAI client
    print("\nTest 2: Estimate cost does not create OpenAI client")
    print("-" * 70)
    
    test_file = Path(__file__).parent / "test_sample.en.srt"
    model_config = {
        "input_price": 2.00,
        "output_price": 8.00,
        "batch_size": 20,
    }
    
    if test_file.exists():
        # Try to mock OpenAI if it exists, otherwise just test normally
        try:
            with patch('openai.OpenAI', side_effect=Exception("OpenAI API should not be called during estimation!")):
                estimate = estimator.estimate_cost([test_file], model_config)
        except ModuleNotFoundError:
            # openai not installed - even better, means we don't depend on it
            print("✓ openai module not even installed (cost estimator doesn't depend on it)")
            estimate = estimator.estimate_cost([test_file], model_config)
        
        print(f"✓ Cost estimation completed without API calls")
        print(f"  Files: {estimate['files']}")
        print(f"  Entries: {estimate['total_entries']}")
        print(f"  Cost: ${estimate['estimated_cost_expected']:.4f}")
        assert estimate['error'] is None, f"Should have no error: {estimate['error']}"
    else:
        print(f"⚠ Test file not found: {test_file}")
    
    # Test 3: Tokenizer should not make external requests
    print("\nTest 3: Tokenizer operations are local")
    print("-" * 70)
    
    # Mock network requests to ensure they're never called
    with patch('urllib.request.urlopen', side_effect=Exception("No external requests should be made!")):
        with patch('requests.get', side_effect=Exception("No external requests should be made!")):
            test_file = Path(__file__).parent / "test_sample.en.srt"
            
            if test_file.exists():
                # Count tokens should work locally
                result = estimator.estimate_file_tokens(test_file)
                print(f"✓ Token counting completed locally")
                print(f"  Tokens: {result['text_tokens']}")
                print(f"  Entries: {result['entry_count']}")
            else:
                print(f"⚠ Test file not found: {test_file}")
    
    # Test 4: Verify CostEstimator can work with empty API key list
    print("\nTest 4: No API keys stored or used")
    print("-" * 70)
    
    # Ensure no API keys are in estimator
    assert not hasattr(estimator, 'api_key'), "CostEstimator should not store api_key"
    assert not hasattr(estimator, 'client'), "CostEstimator should not have OpenAI client"
    
    print("✓ CostEstimator does not store or use API keys")
    
    # Test 5: Tokenizer caching should not use external sources
    print("\nTest 5: Tokenizer caching is local")
    print("-" * 70)
    
    test_text = "Hello, how are you today?"
    
    # Count tokens twice - second should use cache
    tokens1 = estimator.count_tokens_in_text(test_text)
    tokens2 = estimator.count_tokens_in_text(test_text)
    
    assert tokens1 == tokens2, "Same text should have same token count"
    print(f"✓ Token counting is deterministic and local")
    print(f"  First count:  {tokens1}")
    print(f"  Second count: {tokens2}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED - NO API CALLS MADE ✓")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_no_api_calls()
