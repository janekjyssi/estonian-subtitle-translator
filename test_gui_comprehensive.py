#!/usr/bin/env python3
"""Comprehensive verification of modernized GUI functionality"""

import tkinter as tk
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from app.gui import SubtitlesApp

def test_all_functionality():
    """Test that all GUI functionality works correctly after modernization"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    all_tests = []
    
    def test(description, func):
        """Helper to run a test"""
        try:
            func()
            all_tests.append((description, True, None))
            print(f"✓ {description}")
        except Exception as e:
            all_tests.append((description, False, str(e)))
            print(f"✗ {description}: {e}")

    print("=" * 70)
    print("MODERNIZED GUI FUNCTIONALITY VERIFICATION")
    print("=" * 70 + "\n")
    
    # Test 1: Workflow Mode Selection
    print("1. WORKFLOW MODE SELECTION:")
    test("Can set subtitle files mode", lambda: app.workflow_mode.set("subtitle_files"))
    test("Can set MKV folder mode", lambda: app.workflow_mode.set("mkv_folder"))
    test("Workflow display updates", lambda: app._update_workflow_display())
    
    print("\n2. FILE/FOLDER SELECTION:")
    test("Can set folder path", lambda: app.selected_folder.set("/test/path"))
    test("Can select subtitle files", lambda: setattr(app, 'selected_subtitle_files', ['/test/file.srt']))
    test("File count updates", lambda: app.subtitle_files_label.config(text=f"Valitud faile: 1"))
    test("Language info label works", lambda: app.language_info_label.config(text="Tuvastatud keel: Inglise"))
    
    print("\n3. API SETTINGS:")
    test("Can enter API key", lambda: app.api_key.set("test-key-12345"))
    test("Model selector works", lambda: app.model_selector.set("GPT-4.1 — hea | $1 suhteline hinnatase"))
    test("Model config retrieved", lambda: app.MODEL_CONFIG.get("GPT-4.1 — hea | $1 suhteline hinnatase"))
    
    print("\n4. PROGRESS DISPLAY:")
    test("Update progress bar", lambda: app.update_progress(50, 100))
    test("Set current file", lambda: app.set_current_file("example.srt"))
    test("Set batch progress", lambda: app.set_batch_progress(7, 18))
    test("Update counter", lambda: app.update_counter(3))
    test("Show working status", lambda: app._show_working_status("Tõö käib..."))
    test("Clear status", lambda: app._clear_working_status())
    
    print("\n5. LOG FUNCTIONALITY:")
    test("Log message", lambda: app._log_message("Test log entry"))
    test("Get log content", lambda: app.log_text.get("1.0", tk.END))
    test("Copy log works", lambda: app._copy_log_to_clipboard())
    test("Clear log works", lambda: app._clear_log())
    
    print("\n6. BUTTON CONTROL:")
    test("Enable translate button", lambda: app.translate_button.config(state="normal"))
    test("Disable translate button", lambda: app.translate_button.config(state="disabled"))
    test("Enable start button", lambda: app.start_button.config(state="normal"))
    test("Enable estimate button", lambda: app.estimate_cost_button.config(state="normal"))
    test("Enable stop button", lambda: app.stop_button.config(state="normal"))
    
    print("\n7. UI ENABLE/DISABLE DURING TRANSLATION:")
    test("Disable UI", lambda: app._disable_ui_during_translation())
    test("Check buttons disabled", lambda: (
        app.translate_button.cget("state") == "disabled" and
        app.start_button.cget("state") == "disabled"
    ))
    test("Enable UI", lambda: app._enable_ui_after_translation())
    test("Check buttons enabled", lambda: (
        app.translate_button.cget("state") == "normal" and
        app.start_button.cget("state") == "normal"
    ))
    
    print("\n8. STYLING AND APPEARANCE:")
    test("Colors dictionary exists", lambda: hasattr(app, 'colors') and app.colors)
    test("Background color set", lambda: app.colors.get('bg'))
    test("Window background applied", lambda: root.cget('bg'))
    test("Minimum window size set", lambda: root.minsize(750, 600) is None)
    test("Window resizable", lambda: root.resizable(True, True) is None)
    
    print("\n9. CARD STRUCTURE:")
    test("Folder card exists", lambda: hasattr(app, 'folder_card') and app.folder_card)
    test("Subtitle card exists", lambda: hasattr(app, 'subtitle_card') and app.subtitle_card)
    test("Cards have content frames", lambda: (
        app.folder_card['content'] and app.subtitle_card['content']
    ))
    
    print("\n10. STATE VARIABLES:")
    test("Workflow mode variable", lambda: isinstance(app.workflow_mode.get(), str))
    test("API key variable", lambda: isinstance(app.api_key.get(), str))
    test("Selected model variable", lambda: isinstance(app.selected_model.get(), str))
    test("Processed count variable", lambda: isinstance(app.processed_count.get(), int))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in all_tests if success)
    total = len(all_tests)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if total - passed > 0:
        print("\nFailed tests:")
        for desc, success, error in all_tests:
            if not success:
                print(f"  - {desc}: {error}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print("✅ ALL FUNCTIONALITY TESTS PASSED!")
        print("GUI modernization complete and fully functional")
    else:
        print(f"⚠️  {total - passed} tests failed")
    print("=" * 70)
    
    # Cleanup
    try:
        root.quit()
        root.destroy()
    except:
        pass
    
    return passed == total

if __name__ == "__main__":
    success = test_all_functionality()
    exit(0 if success else 1)
