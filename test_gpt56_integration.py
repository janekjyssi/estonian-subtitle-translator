#!/usr/bin/env python3
"""Test script to verify GPT-5.6 Terra model integration"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_model_configuration():
    """Test that MODEL_CONFIG is correctly set up"""
    print("TEST 1: Model Configuration")
    print("-" * 60)
    
    from app.gui import SubtitlesApp
    import tkinter as tk
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    # Verify MODEL_CONFIG has exactly 4 models
    assert len(app.MODEL_CONFIG) == 4, f"Expected 4 models, got {len(app.MODEL_CONFIG)}"
    print(f"✓ MODEL_CONFIG has 4 models")
    
    # Get the display names in order
    display_names = list(app.MODEL_CONFIG.keys())
    
    # Verify the order
    expected_order = [
        "GPT-4.1 mini — odav | $0.5 suhteline hinnatase",
        "GPT-4.1 — hea | $1 suhteline hinnatase",
        "GPT-5.6 Terra — väga hea | $2 suhteline hinnatase",
        "GPT-5.6 Luna — soodne / igapäevane ⭐",
    ]
    
    for i, (expected, actual) in enumerate(zip(expected_order, display_names)):
        assert expected == actual, f"Position {i}: expected '{expected}', got '{actual}'"
        print(f"✓ Model {i+1}: {actual}")
    
    # Verify each model has required fields
    for display_name, config in app.MODEL_CONFIG.items():
        assert "id" in config, f"Missing 'id' for {display_name}"
        assert "input_price" in config, f"Missing 'input_price' for {display_name}"
        assert "output_price" in config, f"Missing 'output_price' for {display_name}"
        assert "batch_size" in config, f"Missing 'batch_size' for {display_name}"
    print("✓ All models have required fields")
    
    # Verify mapping
    assert app.model_display_to_api["GPT-4.1 mini — odav | $0.5 suhteline hinnatase"] == "gpt-4.1-mini"
    assert app.model_display_to_api["GPT-4.1 — hea | $1 suhteline hinnatase"] == "gpt-4.1"
    assert app.model_display_to_api["GPT-5.6 Terra — väga hea | $2 suhteline hinnatase"] == "gpt-5.6-terra"
    assert app.model_display_to_api["GPT-5.6 Luna — soodne / igapäevane ⭐"] == "gpt-5.6-luna"
    print("✓ Model display-to-API mapping correct")
    
    # Verify default selection
    assert app.selected_model.get() == "GPT-4.1 — hea | $1 suhteline hinnatase"
    print("✓ Default model is GPT-4.1 — hea | $1")
    
    root.destroy()
    return True


def test_pricing():
    """Test that pricing is correctly configured"""
    print("\nTEST 2: API Pricing")
    print("-" * 60)
    
    from app.gui import SubtitlesApp
    import tkinter as tk
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    # Verify MODEL_PRICING has all models
    assert "gpt-4.1-mini" in app.MODEL_PRICING
    assert "gpt-4.1" in app.MODEL_PRICING
    assert "gpt-5.6-terra" in app.MODEL_PRICING
    assert "gpt-5.6-luna" in app.MODEL_PRICING
    print("✓ All models in MODEL_PRICING")
    
    # Verify pricing values
    assert app.MODEL_PRICING["gpt-4.1-mini"]["input"] == 0.40
    assert app.MODEL_PRICING["gpt-4.1-mini"]["output"] == 1.60
    print("✓ gpt-4.1-mini pricing correct: input $0.40, output $1.60")
    
    assert app.MODEL_PRICING["gpt-4.1"]["input"] == 2.00
    assert app.MODEL_PRICING["gpt-4.1"]["output"] == 8.00
    print("✓ gpt-4.1 pricing correct: input $2.00, output $8.00")
    
    assert app.MODEL_PRICING["gpt-5.6-terra"]["input"] == 2.50
    assert app.MODEL_PRICING["gpt-5.6-terra"]["output"] == 15.00
    print("✓ gpt-5.6-terra pricing correct: input $2.50, output $15.00")

    assert app.MODEL_PRICING["gpt-5.6-luna"]["input"] == 0.20
    assert app.MODEL_PRICING["gpt-5.6-luna"]["cached_input"] == 0.02
    assert app.MODEL_PRICING["gpt-5.6-luna"]["output"] == 1.20
    print("✓ gpt-5.6-luna pricing correct: input $0.20, cached input $0.02, output $1.20")
    
    root.destroy()
    return True


def test_cost_calculation():
    """Test cost calculation for all models"""
    print("\nTEST 3: Cost Calculation")
    print("-" * 60)
    
    from app.gui import SubtitlesApp
    import tkinter as tk
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    # Test with example tokens: 40593 input, 25263 output
    input_tokens = 40593
    output_tokens = 25263
    
    # Test gpt-4.1-mini
    app.current_model_api_id = "gpt-4.1-mini"
    cost_mini = app._calculate_api_cost(input_tokens, output_tokens)
    expected_mini = 0.0567
    assert cost_mini == expected_mini, f"Expected {expected_mini}, got {cost_mini}"
    print(f"✓ gpt-4.1-mini cost: ${cost_mini:.4f}")
    
    # Test gpt-4.1
    app.current_model_api_id = "gpt-4.1"
    cost_4_1 = app._calculate_api_cost(input_tokens, output_tokens)
    expected_4_1 = 0.2833
    assert cost_4_1 == expected_4_1, f"Expected {expected_4_1}, got {cost_4_1}"
    print(f"✓ gpt-4.1 cost: ${cost_4_1:.4f}")
    
    # Test gpt-5.6-terra
    app.current_model_api_id = "gpt-5.6-terra"
    cost_terra = app._calculate_api_cost(input_tokens, output_tokens)
    # Manual calculation:
    # input: (40593 / 1000000) * 2.50 = 0.1014825
    # output: (25263 / 1000000) * 15.00 = 0.378945
    # total: 0.4804275 -> 0.4804
    expected_terra = 0.4804
    assert cost_terra == expected_terra, f"Expected {expected_terra}, got {cost_terra}"
    print(f"✓ gpt-5.6-terra cost: ${cost_terra:.4f}")

    app.current_model_api_id = "gpt-5.6-luna"
    cost_luna = app._calculate_api_cost(input_tokens, output_tokens)
    expected_luna = 0.0384
    assert cost_luna == expected_luna, f"Expected {expected_luna}, got {cost_luna}"
    assert app._calculate_api_cost(1_000_000, 0, 1_000_000) == 0.02
    print(f"✓ gpt-5.6-luna cost: ${cost_luna:.4f}")
    
    root.destroy()
    return True


def test_batch_sizes():
    """Test that batch sizes are configured correctly"""
    print("\nTEST 4: Batch Sizes")
    print("-" * 60)
    
    from app.translator import OpenAITranslator
    
    # Check MODEL_BATCH_SIZES in translator
    assert OpenAITranslator.MODEL_BATCH_SIZES["gpt-4.1-mini"] == 8
    print("✓ gpt-4.1-mini batch size: 8")
    
    assert OpenAITranslator.MODEL_BATCH_SIZES["gpt-4.1"] == 20
    print("✓ gpt-4.1 batch size: 20")
    
    assert OpenAITranslator.MODEL_BATCH_SIZES["gpt-5.6-terra"] == 20
    print("✓ gpt-5.6-terra batch size: 20")

    assert OpenAITranslator.MODEL_BATCH_SIZES["gpt-5.6-luna"] == 20
    print("✓ gpt-5.6-luna batch size: 20")
    
    return True


def test_gui_fields():
    """Test that GUI fields have correct width"""
    print("\nTEST 5: GUI Field Widths")
    print("-" * 60)
    
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    # Check that model selector shows all options
    model_options = app.model_selector['values']
    assert len(model_options) == 4
    print(f"✓ Model dropdown has 4 options")
    
    for option in model_options:
        print(f"  - {option}")
    
    # Verify default selection shows correctly
    current = app.model_selector.get()
    assert current == "GPT-4.1 — hea | $1 suhteline hinnatase"
    print(f"✓ Default selection: {current}")
    
    root.destroy()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING GPT-5.6 TERRA MODEL INTEGRATION")
    print("=" * 60)
    
    try:
        test_model_configuration()
        test_pricing()
        test_cost_calculation()
        test_batch_sizes()
        test_gui_fields()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
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
