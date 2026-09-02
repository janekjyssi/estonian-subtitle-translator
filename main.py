"""
Subtiitrite programm - Main entry point

A Windows desktop application for processing subtitles in MKV files.
"""

import tkinter as tk
from app.gui import SubtitlesApp


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = SubtitlesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
