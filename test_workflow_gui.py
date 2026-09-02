#!/usr/bin/env python3
"""Test the workflow mode GUI implementation"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import tkinter as tk
from tkinter import ttk
from app.gui import SubtitlesApp


def test_workflow_mode_initialization():
    """Test that workflow mode is initialized correctly"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()  # Allow GUI to update
    
    # Initially should be "subtitle_files"
    assert app.workflow_mode.get() == "subtitle_files", "Initial workflow mode should be 'subtitle_files'"
    
    # Check that folder frame is hidden and subtitle frame is visible
    print(f"Folder frame mapped: {app.folder_frame.winfo_ismapped()}")
    print(f"Subtitle frame mapped: {app.subtitle_frame.winfo_ismapped()}")
    
    assert not app.folder_frame.winfo_ismapped(), "Folder frame should be hidden initially"
    assert app.subtitle_frame.winfo_ismapped(), "Subtitle frame should be visible initially"
    print("✓ Workflow mode initialization correct")
    
    root.destroy()


def test_workflow_mode_switching():
    """Test that workflow mode can be switched"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.update()
    
    # Switch to MKV folder mode
    app.workflow_mode.set("mkv_folder")
    app._update_workflow_display()
    root.update()  # Let GUI update
    
    # Now folder frame should be visible and subtitle frame hidden
    print(f"After switching to MKV mode:")
    print(f"  Folder frame mapped: {app.folder_frame.winfo_ismapped()}")
    print(f"  Subtitle frame mapped: {app.subtitle_frame.winfo_ismapped()}")
    
    assert app.folder_frame.winfo_ismapped(), "Folder frame should be visible in MKV mode"
    assert not app.subtitle_frame.winfo_ismapped(), "Subtitle frame should be hidden in MKV mode"
    print("✓ Workflow mode switching to MKV folder works")
    
    # Switch back to subtitle files mode
    app.workflow_mode.set("subtitle_files")
    app._update_workflow_display()
    root.update()
    
    print(f"After switching back to subtitle files mode:")
    print(f"  Folder frame mapped: {app.folder_frame.winfo_ismapped()}")
    print(f"  Subtitle frame mapped: {app.subtitle_frame.winfo_ismapped()}")
    
    # Folder frame should be hidden again
    assert not app.folder_frame.winfo_ismapped(), "Folder frame should be hidden in subtitle files mode"
    assert app.subtitle_frame.winfo_ismapped(), "Subtitle frame should be visible in subtitle files mode"
    print("✓ Workflow mode switching to subtitle files works")
    
    root.destroy()


def test_start_processing_workflow_check():
    """Test that _start_processing checks workflow mode"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    # Try to start processing in subtitle files mode (should fail)
    app.workflow_mode.set("subtitle_files")
    app.selected_folder.set("C:\\test")  # Set folder anyway
    
    # Capture log messages
    log_entries = []
    original_log = app._log_message
    app._log_message = lambda msg: log_entries.append(msg)
    
    # This should fail due to workflow mode check
    app._start_processing()
    
    # Check that error message was logged
    assert any("Töötlemist saab alustada ainult MKV-failide töörežiimis" in msg for msg in log_entries), \
        "Should reject processing in subtitle files mode"
    print("✓ _start_processing correctly checks workflow mode")
    
    app._log_message = original_log
    root.destroy()


def test_start_translation_workflow_logic():
    """Test that _start_translation checks files based on workflow mode"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    app.api_key.set("test-key")
    
    # Test subtitle files workflow
    app.workflow_mode.set("subtitle_files")
    
    log_entries = []
    original_log = app._log_message
    app._log_message = lambda msg: log_entries.append(msg)
    
    # Without selected files, should error
    app._start_translation()
    assert any("Palun valige alustuseks subtiitrifailid" in msg for msg in log_entries), \
        "Should require selected files in subtitle files mode"
    print("✓ _start_translation correctly checks for files in subtitle files mode")
    
    # Test MKV folder workflow
    app.workflow_mode.set("mkv_folder")
    log_entries.clear()
    
    # Without folder, should error
    app.selected_folder.set("")
    app._start_translation()
    assert any("Palun valige kaust" in msg for msg in log_entries), \
        "Should require folder in MKV folder mode"
    print("✓ _start_translation correctly checks for folder in MKV folder mode")
    
    app._log_message = original_log
    root.destroy()


if __name__ == "__main__":
    print("Testing GUI workflow implementation...\n")
    
    try:
        test_workflow_mode_initialization()
        test_workflow_mode_switching()
        test_start_processing_workflow_check()
        test_start_translation_workflow_logic()
        
        print("\n✓ All workflow GUI tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
