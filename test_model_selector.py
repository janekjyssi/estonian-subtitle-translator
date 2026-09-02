"""
Script to verify that model selector dropdown is created and configured correctly
"""
import tkinter as tk
from app.gui import SubtitlesApp


def test_model_selector():
    """Test if model selector exists and is properly configured"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    
    print("Testing Model Selector Implementation\n")
    print("=" * 60)
    
    # Check if model selector exists
    if hasattr(app, 'model_selector'):
        print("✓ model_selector widget exists")
        
        # Check the selected value
        current_value = app.model_selector.get()
        print(f"✓ Current selection: '{current_value}'")
        
        if current_value == "GPT-4.1 – parem kvaliteet":
            print("✓ Default model is correct (GPT-4.1 – parem kvaliteet)")
        else:
            print(f"✗ Default model is wrong: {current_value}")
            return False
    else:
        print("✗ model_selector widget MISSING!")
        return False
    
    # Check if model mappings exist
    if hasattr(app, 'model_display_to_api'):
        print("\n✓ model_display_to_api mapping exists")
        
        mapping = app.model_display_to_api
        print(f"\nModel Mapping:")
        for display_name, api_id in mapping.items():
            print(f"  {display_name} -> {api_id}")
        
        # Verify correct mappings
        expected_mappings = {
            "GPT-4.1 – parem kvaliteet": "gpt-4.1",
            "GPT-4.1 mini – odavam ja kiirem": "gpt-4.1-mini",
        }
        
        if mapping == expected_mappings:
            print("\n✓ Model mappings are correct")
        else:
            print("\n✗ Model mappings are incorrect!")
            print(f"Expected: {expected_mappings}")
            print(f"Got: {mapping}")
            return False
    else:
        print("\n✗ model_display_to_api mapping MISSING!")
        return False
    
    # Check if display names exist
    if hasattr(app, 'model_display_names'):
        print(f"\n✓ model_display_names exists")
        print(f"Available options:")
        for name in app.model_display_names:
            print(f"  - {name}")
        
        expected_names = [
            "GPT-4.1 – parem kvaliteet",
            "GPT-4.1 mini – odavam ja kiirem",
        ]
        
        if app.model_display_names == expected_names:
            print("\n✓ Display names are correct")
        else:
            print("\n✗ Display names are incorrect!")
            return False
    else:
        print("\n✗ model_display_names MISSING!")
        return False
    
    # Check if selected_model StringVar exists
    if hasattr(app, 'selected_model'):
        print(f"\n✓ selected_model StringVar exists")
        value = app.selected_model.get()
        print(f"  Current value: '{value}'")
    else:
        print("\n✗ selected_model StringVar MISSING!")
        return False
    
    # Check if current_model_name exists
    if hasattr(app, 'current_model_name'):
        print(f"\n✓ current_model_name exists")
        print(f"  Value: '{app.current_model_name}'")
    else:
        print("\n✗ current_model_name MISSING!")
        return False
    
    # Check widget hierarchy
    print("\n" + "=" * 60)
    print("Widget Hierarchy Check:")
    
    found_selector = False
    for child in root.winfo_children():
        for grandchild in child.winfo_children():
            for ggchild in grandchild.winfo_children():
                if hasattr(ggchild, 'winfo_class'):
                    if 'Combobox' in ggchild.winfo_class():
                        found_selector = True
                        print(f"✓ Found Combobox widget in hierarchy")
    
    if not found_selector:
        print("✗ Combobox not found in widget hierarchy!")
        return False
    
    # Test switching models
    print("\n" + "=" * 60)
    print("Testing Model Switching:")
    
    app.model_selector.set("GPT-4.1 mini – odavam ja kiirem")
    new_value = app.model_selector.get()
    print(f"✓ Switched to: '{new_value}'")
    
    if new_value == "GPT-4.1 mini – odavam ja kiirem":
        print("✓ Model switching works correctly")
    else:
        print("✗ Model switching failed!")
        return False
    
    # Switch back to default
    app.model_selector.set("GPT-4.1 – parem kvaliteet")
    print(f"✓ Switched back to default: '{app.model_selector.get()}'")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    
    root.withdraw()
    root.destroy()
    
    return True


if __name__ == "__main__":
    success = test_model_selector()
    exit(0 if success else 1)
