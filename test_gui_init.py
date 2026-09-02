#!/usr/bin/env python3
"""Test GUI initialization with translation components"""

from app.gui import SubtitlesApp
import tkinter as tk

root = tk.Tk()
app = SubtitlesApp(root)

print("✓ GUI initialized successfully")
print(f"  - Has translate button: {hasattr(app, 'translate_button')}")
print(f"  - Has api_key field: {hasattr(app, 'api_key')}")
print(f"  - API key value: {repr(app.api_key.get())}")
print(f"  - Translation worker: {app.translation_worker}")
print(f"\nProcessing stats keys:")
for key in app.processing_stats.keys():
    print(f"  - {key}: {app.processing_stats[key]}")

root.destroy()
print("\n✓ GUI test passed!")
