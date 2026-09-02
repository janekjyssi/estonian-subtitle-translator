"""
Script to verify that action buttons are created and visible in the GUI
"""
import tkinter as tk
from app.gui import SubtitlesApp


def test_buttons():
    """Test if buttons exist and are properly configured"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    # Check if buttons exist
    print("Checking button attributes...")
    
    buttons_to_check = [
        ('start_button', 'Alusta töötlemist'),
        ('stop_button', 'Lõpeta töö'),
        ('translate_button', 'Tõlgi eesti keelde'),
    ]
    
    all_ok = True
    for button_attr, expected_text in buttons_to_check:
        if hasattr(app, button_attr):
            button = getattr(app, button_attr)
            button_text = button.cget('text')
            button_state = button.cget('state')
            button_command = button.cget('command')
            
            print(f"\n✓ {button_attr} exists")
            print(f"  Text: {button_text}")
            print(f"  Expected: {expected_text}")
            print(f"  State: {button_state}")
            print(f"  Command bound: {'Yes' if button_command else 'No'}")
            
            if button_text != expected_text:
                print(f"  ⚠ TEXT MISMATCH!")
                all_ok = False
        else:
            print(f"\n✗ {button_attr} MISSING!")
            all_ok = False
    
    # Check widget hierarchy
    print("\n" + "="*60)
    print("Checking widget hierarchy...")
    
    def print_widgets(widget, level=0):
        indent = "  " * level
        try:
            class_name = widget.__class__.__name__
            # Try to get the text for buttons
            if 'Button' in class_name:
                text = widget.cget('text')
                print(f"{indent}{class_name}: '{text}'")
            elif 'Label' in class_name:
                text = widget.cget('text')
                print(f"{indent}{class_name}: '{text}'")
            elif 'Frame' in class_name:
                print(f"{indent}{class_name}")
            else:
                print(f"{indent}{class_name}")
            
            # Recursively print children
            for child in widget.winfo_children():
                print_widgets(child, level + 1)
        except Exception as e:
            print(f"{indent}Error: {e}")
    
    print("\nMain window widget tree:")
    print_widgets(root)
    
    # Check grid info for buttons
    print("\n" + "="*60)
    print("Checking grid geometry for buttons...")
    
    for button_attr, _ in buttons_to_check:
        if hasattr(app, button_attr):
            button = getattr(app, button_attr)
            grid_info = button.grid_info()
            if grid_info:
                print(f"\n{button_attr}:")
                print(f"  Row: {grid_info.get('row')}")
                print(f"  Column: {grid_info.get('column')}")
                print(f"  Sticky: {grid_info.get('sticky')}")
                print(f"  Padx: {grid_info.get('padx')}")
                print(f"  Pady: {grid_info.get('pady')}")
            else:
                print(f"\n{button_attr}: NOT GRIDDED!")
                all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✓ All buttons are properly created and configured!")
    else:
        print("✗ Some issues found with buttons")
    
    root.withdraw()  # Hide the window
    root.destroy()
    
    return all_ok


if __name__ == "__main__":
    success = test_buttons()
    exit(0 if success else 1)
