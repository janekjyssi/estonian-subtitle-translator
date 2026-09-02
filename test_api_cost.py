#!/usr/bin/env python3
"""Test API cost calculation feature"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_api_cost_calculation():
    """Test API cost calculation for both models"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    print("API Cost Calculation Tests")
    print("=" * 60)
    
    # Test 1: gpt-4.1 cost calculation
    print("\nTest 1: GPT-4.1 cost calculation")
    app.current_model_api_id = "gpt-4.1"
    
    # Example from user request: 40593 input, 25263 output
    input_tokens = 40593
    output_tokens = 25263
    
    cost = app._calculate_api_cost(input_tokens, output_tokens)
    
    # Manual calculation:
    # input: (40593 / 1000000) * 2.00 = 0.081186
    # output: (25263 / 1000000) * 8.00 = 0.202104
    # total: 0.283290
    expected_cost = 0.2833
    
    print(f"  Input tokens: {input_tokens}")
    print(f"  Output tokens: {output_tokens}")
    print(f"  Calculated cost: ${cost:.4f}")
    print(f"  Expected cost: ${expected_cost:.4f}")
    assert cost == expected_cost, f"Expected ${expected_cost:.4f}, got ${cost:.4f}"
    print("  ✓ GPT-4.1 cost calculation correct")
    
    # Test 2: gpt-4.1-mini cost calculation
    print("\nTest 2: GPT-4.1-mini cost calculation")
    app.current_model_api_id = "gpt-4.1-mini"
    
    cost = app._calculate_api_cost(input_tokens, output_tokens)
    
    # Manual calculation:
    # input: (40593 / 1000000) * 0.40 = 0.0162372
    # output: (25263 / 1000000) * 1.60 = 0.0404208
    # total: 0.056658
    expected_cost = 0.0567
    
    print(f"  Input tokens: {input_tokens}")
    print(f"  Output tokens: {output_tokens}")
    print(f"  Calculated cost: ${cost:.4f}")
    print(f"  Expected cost: ${expected_cost:.4f}")
    assert cost == expected_cost, f"Expected ${expected_cost:.4f}, got ${cost:.4f}"
    print("  ✓ GPT-4.1-mini cost calculation correct")
    
    # Test 3: Zero tokens
    print("\nTest 3: Zero token cost")
    cost = app._calculate_api_cost(0, 0)
    assert cost == 0.0000, f"Expected $0.0000, got ${cost:.4f}"
    print(f"  Zero tokens: ${cost:.4f}")
    print("  ✓ Zero token cost correct")
    
    # Test 4: Large token amounts
    print("\nTest 4: Large token amounts (1M tokens)")
    app.current_model_api_id = "gpt-4.1"
    cost = app._calculate_api_cost(1_000_000, 1_000_000)
    
    # input: 1000000 / 1000000 * 2.00 = 2.00
    # output: 1000000 / 1000000 * 8.00 = 8.00
    # total: 10.00
    expected_cost = 10.0000
    
    print(f"  Input: 1,000,000 tokens at $2.00/1M = $2.00")
    print(f"  Output: 1,000,000 tokens at $8.00/1M = $8.00")
    print(f"  Total: ${cost:.4f}")
    assert cost == expected_cost, f"Expected ${expected_cost:.4f}, got ${cost:.4f}"
    print("  ✓ Large token cost correct")
    
    # Test 5: Verify pricing table is present
    print("\nTest 5: Pricing table verification")
    assert "gpt-4.1" in app.MODEL_PRICING, "gpt-4.1 pricing missing"
    assert "gpt-4.1-mini" in app.MODEL_PRICING, "gpt-4.1-mini pricing missing"
    
    pricing_4_1 = app.MODEL_PRICING["gpt-4.1"]
    assert pricing_4_1["input"] == 2.00, f"gpt-4.1 input price should be $2.00"
    assert pricing_4_1["output"] == 8.00, f"gpt-4.1 output price should be $8.00"
    
    pricing_mini = app.MODEL_PRICING["gpt-4.1-mini"]
    assert pricing_mini["input"] == 0.40, f"gpt-4.1-mini input price should be $0.40"
    assert pricing_mini["output"] == 1.60, f"gpt-4.1-mini output price should be $1.60"
    
    print("  ✓ Pricing table correct")
    
    # Test 6: Verify model_api_id is stored
    print("\nTest 6: Model API ID storage")
    app.current_model_api_id = "gpt-4.1-mini"
    assert app.current_model_api_id == "gpt-4.1-mini", "Model API ID not stored correctly"
    print("  ✓ Model API ID stored correctly")
    
    # Test 7: Unknown model defaults to gpt-4.1
    print("\nTest 7: Unknown model defaults to gpt-4.1")
    app.current_model_api_id = "unknown-model"
    cost = app._calculate_api_cost(1_000_000, 1_000_000)
    expected_cost = 10.0000  # Should use gpt-4.1 pricing
    assert cost == expected_cost, f"Unknown model should default to gpt-4.1, expected ${expected_cost:.4f}, got ${cost:.4f}"
    print("  ✓ Unknown model defaults to gpt-4.1")
    
    root.destroy()
    return True


def test_summary_display():
    """Test that summary displays the cost correctly (mock test)"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    print("\nSummary Display Test")
    print("=" * 60)
    
    # Mock translation results
    app.processing_stats = {
        "en_srt_files": 1,
        "translated": 1,
        "skipped_translated": 0,
        "translation_errors": 0,
    }
    
    app.current_model_api_id = "gpt-4.1"
    app.current_model_name = "GPT-4.1 – parem kvaliteet"
    
    # Mock translation worker with token data
    class MockTranslationWorker:
        def get_token_usage(self):
            return {
                "input_tokens": 40593,
                "output_tokens": 25263,
                "total_tokens": 65856,
            }
    
    app.translation_worker = MockTranslationWorker()
    
    # Capture log messages
    log_messages = []
    original_log = app._log_message
    app._log_message = lambda msg: log_messages.append(msg)
    
    # Show summary
    app._show_translation_summary()
    
    # Check that cost line is in the log
    cost_lines = [msg for msg in log_messages if "Hinnanguline API kulu" in msg]
    assert len(cost_lines) > 0, "Cost summary not displayed"
    print(f"  Cost summary line: '{cost_lines[0]}'")
    print("  ✓ Cost summary displayed")
    
    # Check that the actual cost is displayed
    dollar_lines = [msg for msg in log_messages if msg.strip().startswith("$")]
    assert len(dollar_lines) > 0, "Cost value not displayed"
    print(f"  Cost value: '{dollar_lines[0].strip()}'")
    assert "$" in dollar_lines[0], "Cost should include $ sign"
    print("  ✓ Cost value displayed with currency sign")
    
    app._log_message = original_log
    root.destroy()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("API COST CALCULATION FEATURE TESTS")
    print("=" * 60)
    
    try:
        if test_api_cost_calculation():
            print("\n" + "✓ All cost calculation tests passed!")
        
        if test_summary_display():
            print("✓ Summary display test passed!")
        
        print("\n" + "=" * 60)
        print("✓ ALL API COST TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
