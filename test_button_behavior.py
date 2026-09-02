#!/usr/bin/env python3
"""Test button behavior and error handling for workflows"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_button_behavior():
    """Test that buttons behave correctly based on workflow mode"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    print("Button Behavior Test")
    print("-" * 40)
    
    # Test 1: Subtitle file workflow - process button should be disabled
    print("\n1. Subtitle file workflow (default):")
    app.workflow_mode.set("subtitle_files")
    app._update_workflow_display()
    root.update()
    
    start_state = str(app.start_button.cget("state"))
    print(f"   'Alusta töötlemist' button state: '{start_state}'")
    assert start_state == "disabled", f"Start button should be disabled in subtitle workflow, got '{start_state}'"
    print("   ✓ Start button correctly disabled")
    
    # Test 2: MKV folder workflow - process button should be enabled
    print("\n2. MKV folder workflow:")
    app.workflow_mode.set("mkv_folder")
    app._update_workflow_display()
    root.update()
    
    start_state = str(app.start_button.cget("state"))
    print(f"   'Alusta töötlemist' button state: '{start_state}'")
    assert start_state == "normal", f"Start button should be enabled in MKV workflow, got '{start_state}'"
    print("   ✓ Start button correctly enabled")
    
    # Test 3: Error handling - no API key
    print("\n3. Error handling - no API key:")
    log_messages = []
    original_log = app._log_message
    app._log_message = lambda msg: log_messages.append(msg)
    
    app._start_translation()
    assert any("API võti" in msg for msg in log_messages), "Should require API key"
    print("   ✓ Translation correctly requires API key")
    
    # Test 4: Error handling - subtitle workflow without files
    print("\n4. Error handling - subtitle workflow without files:")
    app.api_key.set("test-key")
    app.workflow_mode.set("subtitle_files")
    app.selected_subtitle_files = []
    log_messages.clear()
    
    app._start_translation()
    assert any("subtiitrifailid" in msg for msg in log_messages), "Should require subtitle files"
    print("   ✓ Translation correctly requires files in subtitle mode")
    
    # Test 5: Error handling - MKV workflow without folder
    print("\n5. Error handling - MKV workflow without folder:")
    app.workflow_mode.set("mkv_folder")
    app.selected_folder.set("")
    log_messages.clear()
    
    app._start_translation()
    assert any("kaust" in msg for msg in log_messages), "Should require folder"
    print("   ✓ Translation correctly requires folder in MKV mode")
    
    # Test 6: Error handling - process button in subtitle workflow
    print("\n6. Error handling - process button in subtitle workflow:")
    app.workflow_mode.set("subtitle_files")
    app.selected_folder.set("C:\\test")  # Set folder anyway
    log_messages.clear()
    
    app._start_processing()
    assert any("MKV-failide töörežiimis" in msg for msg in log_messages), "Should reject processing in subtitle mode"
    print("   ✓ Processing correctly rejects subtitle workflow")
    
    app._log_message = original_log
    root.destroy()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Button Behavior & Error Handling Test")
    print("=" * 60)
    
    try:
        if test_button_behavior():
            print("\n" + "=" * 60)
            print("✓ ALL BEHAVIOR TESTS PASSED")
            print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Behavior test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
