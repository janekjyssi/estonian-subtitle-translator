#!/usr/bin/env python3
"""Integration test for complete workflow GUI"""

import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent))


def test_complete_workflow():
    """Test complete workflow initialization and state"""
    import tkinter as tk
    from app.gui import SubtitlesApp
    
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    # Test 1: Initial state
    print("Test 1: Initial state")
    assert app.workflow_mode.get() == "subtitle_files"
    assert len(app.selected_subtitle_files) == 0
    assert app.selected_folder.get() == ""
    assert app.api_key.get() == ""
    print("  ✓ Initial state correct")
    
    # Test 2: Set subtitle files
    print("\nTest 2: Subtitle file selection")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.srt"
        test_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nTest")
        
        app.selected_subtitle_files = [str(test_file)]
        app.subtitle_files_label.config(text=f"Valitud failid: {len(app.selected_subtitle_files)}")
        assert len(app.selected_subtitle_files) == 1
        print("  ✓ Can select subtitle files")
    
    # Test 3: Switch to MKV mode
    print("\nTest 3: Switch to MKV folder mode")
    app.workflow_mode.set("mkv_folder")
    app._update_workflow_display()
    root.update()
    
    assert app.workflow_mode.get() == "mkv_folder"
    assert app.folder_frame.winfo_ismapped()  # Visible
    assert not app.subtitle_frame.winfo_ismapped()  # Hidden
    print("  ✓ MKV mode displays folder frame")
    
    # Test 4: Set folder
    print("\nTest 4: Folder selection in MKV mode")
    with tempfile.TemporaryDirectory() as tmpdir:
        app.selected_folder.set(tmpdir)
        assert app.selected_folder.get() == tmpdir
        print("  ✓ Can select folder in MKV mode")
    
    # Test 5: API key
    print("\nTest 5: API key configuration")
    test_key = "sk-test1234567890"
    app.api_key.set(test_key)
    assert app.api_key.get() == test_key
    print("  ✓ Can set API key")
    
    # Test 6: Model selection
    print("\nTest 6: Model selection")
    app.model_selector.set("GPT-4.1 mini – odavam ja kiirem")
    selected = app.selected_model.get()
    assert selected in app.model_display_to_api
    mapped = app.model_display_to_api[selected]
    print(f"  ✓ Model '{selected}' maps to '{mapped}'")
    
    # Test 7: Switch back to subtitle mode
    print("\nTest 7: Switch back to subtitle file mode")
    app.workflow_mode.set("subtitle_files")
    app._update_workflow_display()
    root.update()
    
    assert app.workflow_mode.get() == "subtitle_files"
    assert not app.folder_frame.winfo_ismapped()  # Hidden
    assert app.subtitle_frame.winfo_ismapped()  # Visible
    print("  ✓ Subtitle mode displays subtitle frame")
    
    root.destroy()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Integration Test: Complete Workflow GUI")
    print("=" * 60)
    
    try:
        if test_complete_workflow():
            print("\n" + "=" * 60)
            print("✓ ALL INTEGRATION TESTS PASSED")
            print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error during integration test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
