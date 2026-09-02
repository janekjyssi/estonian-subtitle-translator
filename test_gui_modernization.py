#!/usr/bin/env python3
"""Test modernized GUI initialization"""

import tkinter as tk
from app.gui import SubtitlesApp

def test_gui_modernization():
    """Test that the modernized GUI loads correctly"""
    root = tk.Tk()
    
    try:
        # Initialize GUI
        app = SubtitlesApp(root)
        
        # Check that key widgets exist
        assert hasattr(app, 'log_text'), 'Log text widget not found'
        assert hasattr(app, 'progress_bar'), 'Progress bar not found'
        assert hasattr(app, 'model_selector'), 'Model selector not found'
        assert hasattr(app, 'translate_button'), 'Translate button not found'
        assert hasattr(app, 'status_label'), 'Status label not found'
        assert hasattr(app, 'batch_label'), 'Batch label not found'
        
        # Check that styles are set up
        assert hasattr(app, 'colors'), 'Colors dictionary not set up'
        assert 'bg' in app.colors, 'Background color not set'
        assert 'card' in app.colors, 'Card color not set'
        assert 'accent' in app.colors, 'Accent color not set'
        
        # Check colors
        print(f"✓ Colors loaded: {app.colors}")
        
        # Try to perform basic operations
        app._log_message('✓ Test log message 1')
        print("✓ Log message works")
        
        app.update_progress(50, 100)
        print("✓ Progress update works")
        
        app.set_current_file('test_file.srt')
        print("✓ Current file label works")
        
        app.update_counter(5)
        print("✓ Counter update works")
        
        app.set_batch_progress(7, 18)
        print("✓ Batch progress works")
        
        app._show_working_status("Töö käib...")
        print("✓ Status label works")
        
        # Check window dimensions
        root.update()
        width = root.winfo_width()
        height = root.winfo_height()
        print(f"✓ Window size: {width}x{height}")
        
        # Verify card structure
        assert hasattr(app, 'folder_card'), 'Folder card missing'
        assert hasattr(app, 'subtitle_card'), 'Subtitle card missing'
        print("✓ Card structure initialized")
        
        # Clean up
        app._on_window_close()
        print("\n✅ ALL TESTS PASSED - GUI modernization successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    success = test_gui_modernization()
    exit(0 if success else 1)
