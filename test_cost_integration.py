#!/usr/bin/env python3
"""Integration test for API cost calculation feature"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_end_to_end_cost_display():
    """Test that cost is calculated and displayed correctly in translation summary"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    print("End-to-End API Cost Integration Test")
    print("=" * 60)
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    # Verify that pricing table is initialized
    print("\n1. Verify pricing table initialization")
    assert hasattr(app, 'MODEL_PRICING'), "MODEL_PRICING attribute missing"
    assert "gpt-4.1" in app.MODEL_PRICING, "gpt-4.1 pricing missing"
    assert "gpt-4.1-mini" in app.MODEL_PRICING, "gpt-4.1-mini pricing missing"
    print("   ✓ Pricing table properly initialized")
    
    # Verify that model_api_id is stored
    print("\n2. Verify model API ID initialization")
    assert hasattr(app, 'current_model_api_id'), "current_model_api_id attribute missing"
    assert app.current_model_api_id == "gpt-4.1", f"Default model should be gpt-4.1, got {app.current_model_api_id}"
    print(f"   ✓ Model API ID initialized to: {app.current_model_api_id}")
    
    # Test cost calculation method exists and works
    print("\n3. Verify cost calculation method")
    assert hasattr(app, '_calculate_api_cost'), "_calculate_api_cost method missing"
    cost = app._calculate_api_cost(40593, 25263)
    assert isinstance(cost, float), f"Cost should be float, got {type(cost)}"
    assert cost == 0.2833, f"Expected $0.2833, got ${cost:.4f}"
    print(f"   ✓ Cost calculation method works: ${cost:.4f}")
    
    # Test with different model
    print("\n4. Test cost with gpt-4.1-mini model")
    app.current_model_api_id = "gpt-4.1-mini"
    cost_mini = app._calculate_api_cost(40593, 25263)
    assert cost_mini == 0.0567, f"Expected $0.0567, got ${cost_mini:.4f}"
    assert cost_mini < cost, "gpt-4.1-mini should be cheaper than gpt-4.1"
    print(f"   ✓ gpt-4.1-mini cost: ${cost_mini:.4f} (cheaper than $0.2833)")
    
    # Test summary method with mock data
    print("\n5. Test summary display with mock data")
    app.current_model_api_id = "gpt-4.1"
    app.processing_stats = {
        "en_srt_files": 5,
        "translated": 5,
        "skipped_translated": 0,
        "translation_errors": 0,
    }
    app.current_model_name = "GPT-4.1 – parem kvaliteet"
    
    # Mock translation worker
    class MockWorker:
        def get_token_usage(self):
            return {
                "input_tokens": 40593,
                "output_tokens": 25263,
                "total_tokens": 65856,
            }
    
    app.translation_worker = MockWorker()
    
    # Capture output
    output_messages = []
    original_log = app._log_message
    app._log_message = lambda msg: output_messages.append(msg)
    
    # Call summary
    app._show_translation_summary()
    
    # Verify output contains cost information
    all_text = "\n".join(output_messages)
    assert "Hinnanguline API kulu" in all_text, "Cost label not in summary"
    assert "$0.2833" in all_text, "Cost value not in summary"
    assert "Markeritud tokenid" in all_text, "Token section not in summary"
    assert "40593" in all_text, "Input tokens not in summary"
    assert "25263" in all_text, "Output tokens not in summary"
    print("   ✓ Summary contains all required information:")
    for line in output_messages:
        if line.strip() and ("Hinnanguline" in line or (line.strip().startswith("$") and "." in line)):
            print(f"      {line}")
    
    app._log_message = original_log
    root.destroy()
    
    return True


def test_model_switching():
    """Test that cost calculation adapts when model is switched"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    print("\nModel Switching Test")
    print("=" * 60)
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    # Test gpt-4.1
    app.current_model_api_id = "gpt-4.1"
    cost_4_1 = app._calculate_api_cost(100000, 100000)
    print(f"\n1. GPT-4.1 cost for 100k input + 100k output: ${cost_4_1:.4f}")
    
    # Test gpt-4.1-mini
    app.current_model_api_id = "gpt-4.1-mini"
    cost_mini = app._calculate_api_cost(100000, 100000)
    print(f"2. GPT-4.1-mini cost for 100k input + 100k output: ${cost_mini:.4f}")
    
    # Verify prices are different
    assert cost_4_1 != cost_mini, "Costs should differ between models"
    assert cost_mini < cost_4_1, "gpt-4.1-mini should always be cheaper"
    
    # Calculate expected ratio
    ratio = cost_mini / cost_4_1
    print(f"\n✓ Mini model is {(1-ratio)*100:.1f}% cheaper than standard model")
    
    root.destroy()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("API COST CALCULATION - INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        if test_end_to_end_cost_display():
            print("\n✓ End-to-end test passed")
        
        if test_model_switching():
            print("\n✓ Model switching test passed")
        
        print("\n" + "=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED")
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
