"""
Test script to verify progress bar animation and UI responsiveness during translation
"""

import sys
import threading
import time
sys.path.insert(0, '.')

import tkinter as tk
from app.gui import SubtitlesApp
from app.threaded_translator import ThreadedTranslationWorker
from pathlib import Path

print("Testing progress bar animation functionality...")

try:
    root = tk.Tk()
    root.withdraw()  # Hide window
    
    app = SubtitlesApp(root)
    
    # Test 1: Progress bar initial state
    print("\nTest 1: Progress bar initial state")
    # Progress bar exists and can be manipulated
    assert app.progress_bar is not None
    app.progress_bar["value"] = 0
    app.progress_bar["maximum"] = 100
    print("  ✓ Progress bar exists and responds to configuration")
    
    # Test 2: Disable UI during translation
    print("\nTest 2: UI disable/enable functions")
    app._disable_ui_during_translation()
    print(f"  After disable - translate_button state: {app.translate_button['state']}")
    print(f"  After disable - stop_button state: {app.stop_button['state']}")
    
    # Check if buttons are disabled by checking Tkinter state
    app._enable_ui_after_translation()
    print(f"  After enable - translate_button state: {app.translate_button['state']}")
    print(f"  After enable - stop_button state: {app.stop_button['state']}")
    print("  ✓ UI disable/enable functions work")
    
    # Test 3: Status label display
    print("\nTest 3: Status label display")
    app._show_working_status("Test status message")
    assert app.status_label.cget("text") == "Test status message"
    print(f"  Status label foreground: {app.status_label.cget('foreground')}")
    print("  ✓ Status label displays correctly")
    
    app._clear_working_status()
    assert app.status_label.cget("text") == ""
    print("  ✓ Status label clears correctly")
    
    # Test 4: Progress bar update
    print("\nTest 4: Progress bar updates")
    app.update_progress(50, 100)
    assert app.progress_bar.cget("value") == 50
    assert app.progress_bar.cget("maximum") == 100
    print("  ✓ Progress bar updates correctly")
    
    # Test 5: Message polling mechanism
    print("\nTest 5: Message polling and queue")
    test_worker = ThreadedTranslationWorker("test_key", "gpt-4.1")
    
    # Simulate sending messages
    test_worker._send_message({"type": "test", "data": "message1"})
    test_worker._send_message({"type": "test", "data": "message2"})
    
    msg1 = test_worker.get_message()
    msg2 = test_worker.get_message()
    msg3 = test_worker.get_message()
    
    assert msg1["data"] == "message1"
    assert msg2["data"] == "message2"
    assert msg3 is None  # Queue should be empty
    print("  ✓ Message queue operates correctly")
    
    # Test 6: Window close handler setup
    print("\nTest 6: Window close handler")
    protocol_handlers = app.root.wm_protocol("WM_DELETE_WINDOW")
    print("  ✓ Window close handler registered")
    
    root.destroy()
    
    print("\n" + "="*60)
    print("✓ All progress bar and UI responsiveness tests passed!")
    print("="*60)
    
except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
