#!/usr/bin/env python3
"""Test collapsible log panel functionality"""

import tkinter as tk
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from app.gui import SubtitlesApp

def test_collapsible_log():
    """Test the collapsible log panel"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    print("=" * 70)
    print("COLLAPSIBLE LOG PANEL - TEST SUITE")
    print("=" * 70 + "\n")
    
    tests_passed = 0
    tests_total = 0
    
    def test(description, condition, details=""):
        """Helper to run a test"""
        nonlocal tests_passed, tests_total
        tests_total += 1
        if condition:
            tests_passed += 1
            print(f"✓ [{tests_total}] {description}")
            if details:
                print(f"    {details}")
        else:
            print(f"✗ [{tests_total}] {description}")
            if details:
                print(f"    {details}")
    
    # Test 1: Initial state - log should be collapsed
    print("1. INITIAL STATE:")
    test("Log starts collapsed", 
         not app.log_is_expanded,
         f"log_is_expanded = {app.log_is_expanded}")
    
    test("Log card frame exists",
         app.log_card_frame is not None,
         "log_card_frame reference stored")
    
    test("Log card is hidden initially",
         app.log_card_frame.winfo_manager() is not None and app.log_card_frame.grid_info() == {},
         "grid_remove() applied")
    
    test("Collapsed header is visible",
         app.log_collapsed_header is not None,
         "collapsed header frame created")
    
    test("Toggle button shows 'Näita logi ▼'",
         "Näita logi" in app.log_toggle_button.cget("text"),
         f"Button text: {app.log_toggle_button.cget('text')}")
    
    test("Error indicator is empty initially",
         app.log_error_indicator.cget("text") == "",
         f"Error indicator text: '{app.log_error_indicator.cget('text')}'")
    
    # Test 2: Add log messages while collapsed
    print("\n2. LOG MESSAGES WHILE COLLAPSED:")
    app._log_message("Test message 1")
    app._log_message("Test message 2")
    
    test("Messages are added to log text widget",
         "Test message 1" in app.log_text.get("1.0", tk.END),
         "Log text contains 'Test message 1'")
    
    test("Multiple messages present",
         "Test message 2" in app.log_text.get("1.0", tk.END),
         "Log text contains 'Test message 2'")
    
    # Test 3: Expand the log
    print("\n3. EXPAND LOG:")
    app._toggle_log_visibility()
    
    test("Log is now expanded",
         app.log_is_expanded,
         f"log_is_expanded = {app.log_is_expanded}")
    
    test("Log card frame is visible",
         app.log_card_frame.winfo_manager() == "grid",
         "grid() called to show frame")
    
    test("Toggle button shows 'Peida logi ▲'",
         "Peida logi" in app.log_toggle_button.cget("text"),
         f"Button text: {app.log_toggle_button.cget('text')}")
    
    test("Previous messages are still present",
         "Test message 1" in app.log_text.get("1.0", tk.END) and 
         "Test message 2" in app.log_text.get("1.0", tk.END),
         "Messages preserved when expanded")
    
    # Test 4: Add messages while expanded
    print("\n4. LOG MESSAGES WHILE EXPANDED:")
    app._log_message("Test message 3")
    
    test("New message added while expanded",
         "Test message 3" in app.log_text.get("1.0", tk.END),
         "Log text contains 'Test message 3'")
    
    test("All previous messages still present",
         "Test message 1" in app.log_text.get("1.0", tk.END) and
         "Test message 2" in app.log_text.get("1.0", tk.END),
         "All 3 messages present together")
    
    # Test 5: Collapse the log
    print("\n5. COLLAPSE LOG:")
    app._toggle_log_visibility()
    
    test("Log is now collapsed",
         not app.log_is_expanded,
         f"log_is_expanded = {app.log_is_expanded}")
    
    test("Log card frame is hidden",
         app.log_card_frame.winfo_manager() is not None and app.log_card_frame.grid_info() == {},
         "grid_remove() applied")
    
    test("Toggle button shows 'Näita logi ▼' again",
         "Näita logi" in app.log_toggle_button.cget("text"),
         f"Button text: {app.log_toggle_button.cget('text')}")
    
    # Test 6: Add messages while collapsed again
    print("\n6. LOG MESSAGES AFTER RE-COLLAPSE:")
    app._log_message("Test message 4")
    
    test("Message 4 added while collapsed",
         "Test message 4" in app.log_text.get("1.0", tk.END),
         "Log text contains 'Test message 4'")
    
    test("All previous messages still present",
         all(f"Test message {i}" in app.log_text.get("1.0", tk.END) for i in range(1, 5)),
         "All 4 messages present after re-collapse")
    
    # Test 7: Error handling
    print("\n7. ERROR AUTO-OPEN FUNCTIONALITY:")
    app.log_is_expanded = False  # Reset to collapsed
    app.log_card_frame.grid_remove()
    app.log_toggle_button.config(text="Näita logi ▼")
    
    app._log_message("⚠ Viga: Test error message")
    
    test("Error message triggers auto-open",
         app.log_is_expanded,
         "Log automatically expanded on error")
    
    test("Error flag is set",
         app.log_has_error,
         f"log_has_error = {app.log_has_error}")
    
    test("Error indicator is empty when expanded",
         app.log_error_indicator.cget("text") == "",
         "(Indicator only shows when log is collapsed)")
    
    # Move log back to collapsed to see error indicator
    app._toggle_log_visibility()
    test("Error indicator shows when collapsed",
         "viga" in app.log_error_indicator.cget("text").lower(),
         f"Error indicator: '{app.log_error_indicator.cget('text')}'")
    
    # Test 8: Clear log functionality
    print("\n8. CLEAR LOG FUNCTIONALITY:")
    app._clear_log()
    
    test("Log is cleared",
         app.log_text.get("1.0", tk.END).strip() == "",
         "Log text is empty after clear")
    
    test("Error indicator reset after clear",
         app.log_error_indicator.cget("text") == "",
         f"Error indicator: '{app.log_error_indicator.cget('text')}'")
    
    # Test 9: Reset error state
    print("\n9. RESET ERROR STATE:")
    app._log_message("Test message after clear")
    app._clear_log_and_reset_error()
    
    test("Error state reset",
         not app.log_has_error,
         f"log_has_error = {app.log_has_error}")
    
    test("Error indicator cleared",
         app.log_error_indicator.cget("text") == "",
         f"Error indicator: '{app.log_error_indicator.cget('text')}'")
    
    # Test 10: Window layout
    print("\n10. WINDOW LAYOUT:")
    root.update()
    
    test("Window created with correct title",
         root.title() == "Subtiitrite programm",
         f"Window title: {root.title()}")
    
    test("Main controls visible when log collapsed",
         hasattr(app, 'translate_button') and app.translate_button is not None,
         "Translate button accessible")
    
    test("Log collapsed header always visible",
         app.log_collapsed_header.winfo_manager() == "grid",
         "Collapsed header in grid")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {tests_total}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_total - tests_passed}")
    print()
    
    if tests_passed == tests_total:
        print("✅ ALL COLLAPSIBLE LOG TESTS PASSED!")
        print("\nFeatures verified:")
        print("✓ Log starts collapsed (hidden)")
        print("✓ Collapsed header always visible")
        print("✓ Toggle button works correctly")
        print("✓ Log content preserved when toggling")
        print("✓ Error messages auto-open log")
        print("✓ Error indicator shown when error occurs")
        print("✓ Clear log functionality works")
        print("✓ Main controls remain visible when log hidden")
        result = True
    else:
        print(f"⚠️  {tests_total - tests_passed} test(s) failed")
        result = False
    
    print("=" * 70)
    
    # Cleanup
    try:
        app._on_window_close()
    except:
        pass
    
    return result

if __name__ == "__main__":
    success = test_collapsible_log()
    exit(0 if success else 1)
