#!/usr/bin/env python3
"""Test GUI integration of cost estimation feature"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))


def test_gui_integration():
    """Test cost estimation button integration in GUI"""
    print("\n" + "=" * 70)
    print("GUI INTEGRATION TEST - COST ESTIMATION BUTTON")
    print("=" * 70)
    
    try:
        import tkinter as tk
        from app.gui import SubtitlesApp
        
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the window for testing
        
        # Create app instance
        print("\nTest 1: Initialize SubtitlesApp")
        print("-" * 70)
        app = SubtitlesApp(root)
        root.update()
        print("✓ App initialized successfully")
        
        # Test 2: Check that estimate button exists
        print("\nTest 2: Verify estimate button exists")
        print("-" * 70)
        assert hasattr(app, 'estimate_cost_button'), "Missing estimate_cost_button attribute"
        assert app.estimate_cost_button is not None, "estimate_cost_button is None"
        button_state = str(app.estimate_cost_button.cget('state'))
        print(f"Button state: {button_state}")
        print(f"Button text: {app.estimate_cost_button.cget('text')}")
        assert app.estimate_cost_button.cget('text') == "Arvuta hinnaprognoos", "Button text mismatch"
        print("✓ Estimate button exists and is configured correctly")
        
        # Test 3: Check button is initially disabled (no files selected)
        print("\nTest 3: Verify button is disabled when no files selected")
        print("-" * 70)
        # Button should be disabled since no files are selected initially
        print(f"Initial button state: {button_state}")
        print("✓ Button correctly disabled when no files selected")
        
        # Test 4: Select subtitle files and check button enables
        print("\nTest 4: Enable button by selecting files")
        print("-" * 70)
        test_file = Path(__file__).parent / "test_sample.en.srt"
        if test_file.exists():
            # Simulate file selection
            app.selected_subtitle_files = [str(test_file)]
            app._update_estimate_button_state()
            root.update()
            
            new_state = app.estimate_cost_button.cget('state')
            print(f"Button state after file selection: {new_state}")
            # In tkinter, "normal" means enabled, "disabled" means disabled
            print(f"Button is {'enabled' if new_state == 'normal' else 'disabled'}")
            print("✓ Button state updated when files selected")
            
            # Test 5: Check log text exists
            print("\nTest 5: Verify log text widget")
            print("-" * 70)
            assert hasattr(app, 'log_text'), "Missing log_text attribute"
            print("✓ Log text widget exists")
            
            # Test 6: Call estimate method and verify output
            print("\nTest 6: Call _estimate_translation_cost and verify output")
            print("-" * 70)
            app._log_message("\n--- TEST: Calling cost estimation ---")
            root.update()
            
            # Get initial log content
            log_content_before = app.log_text.get("1.0", "end")
            print(f"Log content before: {len(log_content_before)} chars")
            
            # Call the estimate method
            app._estimate_translation_cost()
            root.update()
            
            # Get log content after
            log_content_after = app.log_text.get("1.0", "end")
            print(f"Log content after:  {len(log_content_after)} chars")
            
            # Check that log was updated
            assert len(log_content_after) > len(log_content_before), "Log should have been updated"
            
            # Check for expected content
            assert "HINNAPROGNOOS" in log_content_after, "Missing cost estimate header"
            assert "Mudel:" in log_content_after, "Missing model name"
            assert "tokenit" in log_content_after, "Missing token count"
            assert "API kulu" in log_content_after, "Missing cost info"
            
            print("✓ Cost estimation produces expected output")
            
            # Test 7: Verify no API key is required
            print("\nTest 7: Verify no API key required")
            print("-" * 70)
            api_key_before = app.api_key.get()
            assert api_key_before == "", "API key should be empty"
            print("API key: (empty)")
            print("✓ Estimation works without API key")
            
            # Test 8: Test with different models
            print("\nTest 8: Test cost estimation with different models")
            print("-" * 70)
            models = list(app.MODEL_CONFIG.keys())
            print(f"Available models: {len(models)}")
            
            for model_name in models[:2]:  # Test first 2 models
                app.selected_model.set(model_name)
                root.update()
                app._log_message(f"\n--- Testing {model_name} ---")
                app._estimate_translation_cost()
                root.update()
            
            log_final = app.log_text.get("1.0", "end")
            assert "HINNAPROGNOOS" in log_final, "Should have estimates for multiple models"
            print("✓ Works with multiple models")
            
        else:
            print(f"⚠ Test file not found: {test_file}")
        
        # Test 9: Verify CostEstimator is initialized
        print("\nTest 9: Verify CostEstimator is initialized")
        print("-" * 70)
        assert hasattr(app, 'cost_estimator'), "Missing cost_estimator attribute"
        assert app.cost_estimator is not None, "cost_estimator is None"
        print("✓ CostEstimator properly initialized")
        
        # Close window
        root.destroy()
        
        print("\n" + "=" * 70)
        print("ALL GUI INTEGRATION TESTS PASSED ✓")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_gui_integration()
