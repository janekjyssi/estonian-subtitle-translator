"""
GUI module for Subtiitrite programm
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict
import threading
from app.mkv_tools import MKVTools
from app.translator import TranslationWorker
from app.threaded_translator import ThreadedTranslationWorker
from app.cost_estimator import CostEstimator
from app.language_detector import LanguageDetector
from app.backup_manager import BackupManager
from app.checkpoint_manager import CheckpointManager


class SubtitlesApp:
    """Main application GUI class"""

    # Central model configuration
    # Display names include price level indicators (NOT actual cost)
    # Actual cost calculated from token usage and real API pricing
    MODEL_CONFIG = {
        "GPT-4.1 mini — odav | $0.5 suhteline hinnatase": {
            "id": "gpt-4.1-mini",
            "input_price": 0.40,      # $ per 1M tokens (actual API price)
            "output_price": 1.60,     # $ per 1M tokens (actual API price)
            "batch_size": 8,
        },
        "GPT-4.1 — hea | $1 suhteline hinnatase": {
            "id": "gpt-4.1",
            "input_price": 2.00,      # $ per 1M tokens (actual API price)
            "output_price": 8.00,     # $ per 1M tokens (actual API price)
            "batch_size": 20,
        },
        "GPT-5.6 Terra — väga hea | $2 suhteline hinnatase": {
            "id": "gpt-5.6-terra",
            "input_price": 2.50,      # $ per 1M tokens (actual API price)
            "output_price": 15.00,    # $ per 1M tokens (actual API price)
            "batch_size": 20,
        },
        "GPT-5.6 Luna — soodne / igapäevane ⭐": {
            "id": "gpt-5.6-luna",
            "input_price": 0.20,      # $ per 1M tokens (actual API price)
            "cached_input_price": 0.02, # $ per 1M cached tokens (actual API price)
            "output_price": 1.20,     # $ per 1M tokens (actual API price)
            "batch_size": 20,
        },
    }

    # Legacy pricing dict for backwards compatibility (kept for now)
    MODEL_PRICING = {
        "gpt-4.1": {
            "input": 2.00,
            "output": 8.00,
        },
        "gpt-4.1-mini": {
            "input": 0.40,
            "output": 1.60,
        },
        "gpt-5.6-terra": {
            "input": 2.50,
            "output": 15.00,
        },
        "gpt-5.6-luna": {
            "input": 0.20,
            "cached_input": 0.02,
            "output": 1.20,
        },
    }

    def __init__(self, root):
        """Initialize the application GUI"""
        self.root = root
        self.root.title("Subtiitrite programm")
        
        # Set window size based on available screen space
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Default size: 900x700, but limit height to available desktop space
        default_width = 900
        default_height = 700
        max_height = max(600, screen_height - 100)  # Leave room for taskbar
        actual_height = min(default_height, max_height)
        
        self.root.geometry(f"{default_width}x{actual_height}")
        self.root.resizable(True, True)

        # Set minimum window size
        self.root.minsize(750, 500)
        
        # Apply modern styling
        self._setup_modern_style()

        # Workflow mode selection
        self.workflow_mode = tk.StringVar(value="subtitle_files")

        # Selected folder path
        self.selected_folder = tk.StringVar()

        # Processed files counter
        self.processed_count = tk.IntVar(value=0)

        # API Key for translation
        self.api_key = tk.StringVar()

        # Selected model for translation
        self.selected_model = tk.StringVar(value="GPT-4.1 — hea | $1 suhteline hinnatase")

        # Selected subtitle files (for direct translation)
        self.selected_subtitle_files = []

        # Cancellation flag
        self.is_processing = False
        self.cancel_requested = False

        # Cost estimation
        self.cost_estimator = CostEstimator()

        # Language detection
        self.language_detector = LanguageDetector()
        self.detected_files_languages = {}  # Map of file_path -> detection result

        # Backup and checkpoint management
        self.backup_manager = BackupManager()
        self.checkpoint_manager = CheckpointManager()
        self.file_checkpoints = {}  # Map of file_path -> checkpoint data
        self.resume_mode = {}  # Map of file_path -> "new", "resume", or "restart"

        # MKV processing state
        self.mkv_tools = MKVTools()
        self.translation_worker = None
        self.threaded_translation_worker = None  # New: background thread worker
        self.translation_in_progress = False  # New: track if translation thread is running
        self.current_model_name = "GPT-4.1 – parem kvaliteet"  # Store current model for logging
        self.current_model_api_id = "gpt-4.1"  # Store current model API ID for cost calculation
        self.mkv_files = []
        self.current_file_index = 0
        
        # Collapsible log state
        self.log_is_expanded = False  # Log starts collapsed
        self.log_has_error = False  # Track if error occurred while log was collapsed
        self.log_card_frame = None  # Reference to full log card (to toggle visibility)
        self.log_collapsed_header = None  # Reference to collapsed header
        self.processing_stats = {
            "total": 0,
            "with_english": 0,
            "without_english": 0,
            "extracted": 0,
            "skipped_existing": 0,
            "extraction_errors": 0,
            "errors": 0,
            "en_srt_files": 0,
            "translated": 0,
            "skipped_translated": 0,
            "translation_errors": 0,
        }

        # Create the main frame with padding
        self.main_frame = ttk.Frame(root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(7, weight=1)

        # Store frame references for show/hide
        self.folder_frame = None
        self.subtitle_frame = None
        self.start_button = None

        # Handle window close event to gracefully cancel translation
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._create_widgets()

    def _setup_modern_style(self):
        """Set up modern ttk style with clean colors and fonts"""
        style = ttk.Style()
        
        # Color palette - modern, clean, professional
        BG_COLOR = "#F3F4F6"           # Light gray background
        CARD_COLOR = "#FFFFFF"          # White cards
        BORDER_COLOR = "#DADDE1"        # Subtle border
        PRIMARY_TEXT = "#1F2937"        # Dark gray text
        SECONDARY_TEXT = "#6B7280"      # Light gray text
        ACCENT_COLOR = "#2563EB"        # Blue accent
        SUCCESS_COLOR = "#15803D"       # Green
        ERROR_COLOR = "#B91C1C"         # Red
        WARNING_COLOR = "#B45309"       # Amber
        
        # Configure window background
        self.root.configure(bg=BG_COLOR)
        
        # Configure base ttk style
        style.theme_use('clam')
        
        # Configure general styles
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=PRIMARY_TEXT, font=('Segoe UI', 9))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=PRIMARY_TEXT)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 9), foreground=SECONDARY_TEXT)
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'), foreground=PRIMARY_TEXT)
        style.configure('Status.TLabel', font=('Segoe UI', 10, 'bold'), foreground=SUCCESS_COLOR)
        
        # Card frame style
        style.configure('Card.TFrame', background=CARD_COLOR, relief='solid', borderwidth=1)
        
        # Configure buttons
        style.configure('TButton', font=('Segoe UI', 9))
        style.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'))
        
        # Configure entry and combobox
        style.configure('TEntry', font=('Segoe UI', 9))
        style.configure('TCombobox', font=('Segoe UI', 9))
        
        # Configure scrollbar and other widgets
        style.configure('TScrollbar', background=BG_COLOR)
        style.configure('Treeview', font=('Consolas', 9), background=CARD_COLOR)
        
        # Store colors for reference
        self.colors = {
            'bg': BG_COLOR,
            'card': CARD_COLOR,
            'border': BORDER_COLOR,
            'primary': PRIMARY_TEXT,
            'secondary': SECONDARY_TEXT,
            'accent': ACCENT_COLOR,
            'success': SUCCESS_COLOR,
            'error': ERROR_COLOR,
            'warning': WARNING_COLOR,
        }

    def _create_widgets(self):
        """Create all GUI widgets with modern styling and card-based layout - SCROLLABLE"""
        # Main container frame for scrollbar management
        outer_frame = ttk.Frame(self.root)
        outer_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Configure grid for outer frame
        outer_frame.columnconfigure(0, weight=1)
        outer_frame.rowconfigure(0, weight=1)
        
        # Create Canvas for scrollable content
        self.canvas = tk.Canvas(outer_frame, bg=self.colors['bg'], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for canvas
        scrollbar = ttk.Scrollbar(outer_frame, orient='vertical', command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create the actual content frame inside canvas
        self.main_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(0, 0, window=self.main_frame, anchor='nw')
        
        # Bind canvas resize to update scroll region
        def on_main_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
        self.main_frame.bind('<Configure>', on_main_frame_configure)
        
        # Configure grid for main frame content
        self.main_frame.columnconfigure(0, weight=1)
        
        current_row = 0
        
        # ===== HEADER =====
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(16, 16), padx=16)
        header_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(
            header_frame,
            text="Subtiitrite programm",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        subtitle_label = ttk.Label(
            header_frame,
            text="MKV ja SRT subtiitrite töötlemine ning AI-tõlge",
            style='Subtitle.TLabel'
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        current_row += 1
        
        # ===== WORKFLOW MODE CARD (COMPACT) =====
        workflow_card = self._create_card(self.main_frame, "Töörežiim", current_row)
        workflow_frame = workflow_card['content']
        workflow_frame.columnconfigure(0, weight=1)
        
        # Two radio buttons side by side - compact
        radio_container = ttk.Frame(workflow_frame)
        radio_container.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        radio_container.columnconfigure(0, weight=1)
        radio_container.columnconfigure(1, weight=1)
        
        subtitle_radio = ttk.Radiobutton(
            radio_container,
            text="Tõlgin olemasolevaid subtiitrifaile",
            variable=self.workflow_mode,
            value="subtitle_files",
            command=self._update_workflow_display,
        )
        subtitle_radio.grid(row=0, column=0, sticky=tk.W, padx=(0, 16), pady=0)
        
        mkv_radio = ttk.Radiobutton(
            radio_container,
            text="Töötlen MKV-faile ja tõlgin subtiitrid",
            variable=self.workflow_mode,
            value="mkv_folder",
            command=self._update_workflow_display,
        )
        mkv_radio.grid(row=0, column=1, sticky=tk.W, pady=0)
        current_row += 1
        
        # ===== FOLDER SELECTION CARD (Workflow 2 only) =====
        self.folder_card = self._create_card(self.main_frame, "Kausta valik", current_row)
        self.folder_frame = self.folder_card['content']
        self.folder_frame.columnconfigure(0, weight=1)
        
        folder_entry = ttk.Entry(self.folder_frame, textvariable=self.selected_folder, width=50)
        folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=0)
        
        select_folder_button = ttk.Button(
            self.folder_frame, text="Vali kaust", command=self._select_folder
        )
        select_folder_button.grid(row=0, column=1, sticky=tk.E, pady=0)
        current_row += 1
        
        # ===== FILE SELECTION CARD (Workflow 1 only) =====
        self.subtitle_card = self._create_card(self.main_frame, "Subtiitrifailid", current_row)
        self.subtitle_frame = self.subtitle_card['content']
        self.subtitle_frame.columnconfigure(0, weight=1)
        
        # File count and button row
        file_button_frame = ttk.Frame(self.subtitle_frame)
        file_button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        file_button_frame.columnconfigure(0, weight=1)
        
        self.subtitle_files_label = ttk.Label(
            file_button_frame, text="Valitud faile: 0", style='Heading.TLabel'
        )
        self.subtitle_files_label.grid(row=0, column=0, sticky=tk.W, pady=0)
        
        select_subtitle_button = ttk.Button(
            file_button_frame, text="Vali subtiitrifailid", command=self._select_subtitle_files
        )
        select_subtitle_button.grid(row=0, column=1, sticky=tk.E, pady=0)
        
        # Language detection info (if available)
        self.language_info_label = ttk.Label(
            self.subtitle_frame, text="", style='Subtitle.TLabel'
        )
        self.language_info_label.grid(row=1, column=0, sticky=tk.W, pady=(4, 0))
        current_row += 1
        
        # ===== TRANSLATION SETTINGS CARD (COMPACT) =====
        settings_card = self._create_card(self.main_frame, "Tõlkimise seadistus", current_row)
        settings_frame = settings_card['content']
        settings_frame.columnconfigure(1, weight=1)
        
        # API Key
        api_label = ttk.Label(settings_frame, text="OpenAI API võti:", style='Heading.TLabel')
        api_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 12), pady=(0, 6))
        
        api_entry = ttk.Entry(settings_frame, textvariable=self.api_key, show="*", width=52)
        api_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 6))
        
        # Model selector
        model_label = ttk.Label(settings_frame, text="Mudel:", style='Heading.TLabel')
        model_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 12), pady=0)
        
        self.model_display_names = list(self.MODEL_CONFIG.keys())
        self.model_display_to_api = {
            display_name: config["id"] 
            for display_name, config in self.MODEL_CONFIG.items()
        }
        
        self.model_selector = ttk.Combobox(
            settings_frame,
            textvariable=self.selected_model,
            values=self.model_display_names,
            state="readonly",
            width=50,
        )
        self.model_selector.set("GPT-4.1 — hea | $1 suhteline hinnatase")
        self.model_selector.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=0)
        current_row += 1
        
        # ===== PROGRESS CARD (COMPACT) =====
        progress_card = self._create_card(self.main_frame, "Edenemine", current_row)
        progress_frame = progress_card['content']
        progress_frame.columnconfigure(0, weight=1)
        
        # Status label - prominent
        self.status_label = ttk.Label(
            progress_frame,
            text="Valmis töötamiseks",
            style='Status.TLabel'
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", length=400
        )
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Progress details grid - more compact
        details_frame = ttk.Frame(progress_frame)
        details_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        details_frame.columnconfigure(0, weight=0)
        details_frame.columnconfigure(1, weight=1)
        
        self.current_file_label = ttk.Label(
            details_frame,
            text="Jooksev fail: -",
            style='TLabel'
        )
        self.current_file_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20), pady=1)
        
        self.batch_label = ttk.Label(
            details_frame,
            text="Plokk: -",
            style='TLabel'
        )
        self.batch_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=1)
        
        self.counter_label = ttk.Label(
            details_frame,
            text="Töödeldud failid: 0",
            style='TLabel'
        )
        self.counter_label.grid(row=1, column=0, sticky=tk.W, pady=1)
        current_row += 1
        
        # ===== ACTION BUTTONS =====
        button_row = current_row
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=button_row, column=0, sticky=(tk.W, tk.E), pady=(10, 10), padx=16)
        
        # Configure columns: 0-2=buttons (left), 3=spacer, 4=button (right)
        button_frame.columnconfigure(0, weight=0)  # Alusta töötlemist
        button_frame.columnconfigure(1, weight=0)  # Arvuta hinnaprognoos
        button_frame.columnconfigure(2, weight=0)  # Lõpeta töö
        button_frame.columnconfigure(3, weight=1)  # Spacer (expands)
        button_frame.columnconfigure(4, weight=0)  # Tõlgi eesti keelde
        
        # Left-side buttons (grouped together)
        self.start_button = ttk.Button(
            button_frame,
            text="Alusta töötlemist",
            command=self._start_processing,
        )
        self.start_button.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.estimate_cost_button = ttk.Button(
            button_frame,
            text="Arvuta hinnaprognoos",
            command=self._estimate_translation_cost,
        )
        self.estimate_cost_button.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Lõpeta töö",
            command=self._cancel_processing,
            state="disabled",
        )
        self.stop_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 0))
        
        # Right-side button (principal action)
        self.translate_button = ttk.Button(
            button_frame,
            text="Tõlgi eesti keelde",
            command=self._start_translation,
            style='Primary.TButton'
        )
        self.translate_button.grid(row=0, column=4, sticky=tk.E, padx=(0, 0))
        
        current_row += 1
        
        # ===== LOG SECTION (COLLAPSIBLE) =====
        # Create collapsed header frame (always visible)
        self.log_collapsed_header = ttk.Frame(self.main_frame)
        self.log_collapsed_header.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(6, 8), padx=16)
        self.log_collapsed_header.columnconfigure(0, weight=1)
        
        # Collapsed header content
        collapsed_title = ttk.Label(
            self.log_collapsed_header,
            text="Tegevuste logi",
            style='Heading.TLabel'
        )
        collapsed_title.grid(row=0, column=0, sticky=tk.W)
        
        # Error indicator label
        self.log_error_indicator = ttk.Label(
            self.log_collapsed_header,
            text="",  # Will show "— ⚠ viga" or "— Viga" if error
            style='Subtitle.TLabel'
        )
        self.log_error_indicator.grid(row=0, column=0, sticky=tk.W, padx=(140, 0))
        
        # Toggle button
        self.log_toggle_button = ttk.Button(
            self.log_collapsed_header,
            text="Näita logi ▼",
            command=self._toggle_log_visibility,
            width=15
        )
        self.log_toggle_button.grid(row=0, column=1, sticky=tk.E, padx=0)
        
        # Create full log card (initially hidden)
        log_card = self._create_card(self.main_frame, "Tegevuste logi", current_row, has_header_buttons=True)
        self.log_card_frame = log_card['frame']  # Store reference to outer card frame
        log_frame = log_card['content']
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log header with buttons
        log_header = log_card['header_buttons']
        
        copy_log_button = ttk.Button(
            log_header,
            text="Kopeeri",
            command=self._copy_log_to_clipboard,
            width=8
        )
        copy_log_button.grid(row=0, column=0, sticky=tk.E, padx=(0, 4))
        
        clear_log_button = ttk.Button(
            log_header,
            text="Puhasta",
            command=self._clear_log,
            width=8
        )
        clear_log_button.grid(row=0, column=1, sticky=tk.E, padx=(0, 4))
        
        hide_log_button = ttk.Button(
            log_header,
            text="Peida logi ▲",
            command=self._toggle_log_visibility,
            width=12
        )
        hide_log_button.grid(row=0, column=2, sticky=tk.E)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Text widget for log - COMPACT SIZE (180-220 px as specified)
        self.log_text = tk.Text(
            log_frame,
            height=10,  # Approximately 180-200 pixels depending on font
            width=100,
            yscrollcommand=scrollbar.set,
            state="disabled",
            font=("Consolas", 9),
            wrap=tk.WORD,
            background=self.colors['card'],
            foreground=self.colors['primary'],
            relief=tk.FLAT,
            borderwidth=0
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.log_text.yview)
        
        # Initially hide the full log card
        self.log_card_frame.grid_remove()
        
        # Add padding frame at the bottom for scrolling comfort
        bottom_frame = ttk.Frame(self.main_frame)
        current_row += 1
        bottom_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 16), padx=16)
        
        # Update workflow display to show/hide appropriate sections
        self._update_workflow_display()
        self._log_message("Rakendus käivitatud valmis kasutamiseks.")
        
        # Add mouse wheel scrolling support (after all widgets created)
        self._setup_mouse_wheel_scrolling()

    def _setup_mouse_wheel_scrolling(self):
        """Set up mouse wheel scrolling support for the canvas"""
        def on_mousewheel(event):
            # Windows and Linux
            scroll_speed = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(scroll_speed, "units")
        
        def on_mousewheel_linux(event):
            # Linux mouse wheel (event.num: 4=up, 5=down)
            scroll_speed = -3 if event.num == 4 else 3
            self.canvas.yview_scroll(scroll_speed, "units")
        
        # Bind mouse wheel events
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Button-4>", on_mousewheel_linux)
        self.canvas.bind("<Button-5>", on_mousewheel_linux)
        
        # Also bind to child widgets when they get focus
        def bind_mousewheel_recursive(widget):
            if widget == self.log_text:
                # Don't bind to log text - let it use its own scrolling
                return
            if isinstance(widget, tk.Text):
                # Don't interfere with Text widget scrolling
                return
            
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel_linux)
            widget.bind("<Button-5>", on_mousewheel_linux)
            
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)
        
        bind_mousewheel_recursive(self.main_frame)
    
    def _create_card(self, parent, title, row, has_header_buttons=False):
        """
        Create a styled card (modern frame with title and subtle border).
        
        Returns a dict with:
        - 'frame': the outer card frame
        - 'content': the content frame inside the card
        - 'header_buttons': frame for header buttons (if has_header_buttons=True)
        """
        card_frame = ttk.Frame(parent, style='Card.TFrame', relief='solid', borderwidth=1)
        card_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10), padx=16, ipady=8, ipadx=12)
        card_frame.columnconfigure(0, weight=1)
        
        # Header row
        header_frame = ttk.Frame(card_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        header_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(header_frame, text=title, style='Heading.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Optional header buttons frame
        header_buttons_frame = None
        if has_header_buttons:
            header_buttons_frame = ttk.Frame(header_frame)
            header_buttons_frame.grid(row=0, column=1, sticky=tk.E)
        
        # Content frame
        content_frame = ttk.Frame(card_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        content_frame.columnconfigure(0, weight=1)
        
        return {
            'frame': card_frame,
            'content': content_frame,
            'header_buttons': header_buttons_frame,
        }
    
    def _copy_log_to_clipboard(self):
        """Copy log contents to clipboard"""
        try:
            log_content = self.log_text.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self._log_message("\n✓ Logi kopeeritud lõikepuhvrisse.")
        except Exception as e:
            self._log_message(f"\n⚠ Viga logi kopeerimisel: {e}")
    
    def _clear_log(self):
        """Clear log contents (does not delete any files)"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        
        # Reset error indicator when log is cleared
        self.log_has_error = False
        self._update_log_error_indicator()

    def _on_window_close(self):
        """Handle window close event - cancel any running translation"""
        if self.translation_in_progress and self.threaded_translation_worker:
            # Cancel translation thread
            self.threaded_translation_worker.cancel()
            self._log_message("\nAkna sulgemise tõttu katkestati tõlkimine.")
            # Give thread a moment to stop
            self.root.after(100, self._do_close_window)
        else:
            self._do_close_window()

    def _do_close_window(self):
        """Actually close the window"""
        self.root.destroy()

    def _update_workflow_display(self):
        """Show/hide GUI elements based on selected workflow mode"""
        if self.workflow_mode.get() == "subtitle_files":
            # Workflow 1: Direct subtitle file translation
            self.folder_card['frame'].grid_remove()
            self.subtitle_card['frame'].grid()
            self.start_button.config(text="Alusta töötlemist", state="disabled")
        else:
            # Workflow 2: MKV folder processing
            self.folder_card['frame'].grid()
            self.subtitle_card['frame'].grid_remove()
            self.start_button.config(text="Alusta töötlemist", state="normal")
        
        # Update estimate button state
        self._update_estimate_button_state()

    def _select_folder(self):
        """Open folder selection dialog"""
        folder_path = filedialog.askdirectory(
            title="Valige kausta, mis sisaldab MKV failidega...",
        )
        if folder_path:
            self.selected_folder.set(folder_path)
            self._log_message(f"Valitud kaust: {folder_path}")
            self._update_estimate_button_state()

    def _select_subtitle_files(self):
        """Open file selection dialog for subtitle files"""
        file_paths = filedialog.askopenfilenames(
            title="Valige subtiitrifailid",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")],
        )
        if file_paths:
            self.selected_subtitle_files = list(file_paths)
            count = len(self.selected_subtitle_files)
            self.subtitle_files_label.config(text=f"Valitud failid: {count}")
            self._log_message(f"Valitud {count} subtiitrifail(i): {', '.join(Path(f).name for f in self.selected_subtitle_files)}")
            
            # Check for existing checkpoints on each file
            self._check_for_interrupted_translations()
            
            # Detect languages in selected files
            self._detect_selected_file_languages()
            
            self._update_estimate_button_state()
    
    def _check_for_interrupted_translations(self):
        """Check for interrupted translations and offer resume option"""
        for file_path_str in self.selected_subtitle_files:
            file_path = Path(file_path_str)
            checkpoint = CheckpointManager.load_checkpoint(file_path)
            
            if checkpoint:
                # Validate checkpoint
                is_valid, validation_msg = CheckpointManager.validate_checkpoint(file_path, checkpoint)
                
                if is_valid:
                    # Store checkpoint data
                    self.file_checkpoints[file_path_str] = checkpoint
                    
                    # Check for model mismatch
                    has_mismatch, checkpoint_model = CheckpointManager.check_model_mismatch(
                        checkpoint, self.current_model_api_id
                    )
                    
                    # Get progress info
                    progress_info = CheckpointManager.get_progress_summary(checkpoint)
                    
                    self._log_message(f"⚠ Leiti pooleli jäänud tõlge: {file_path.name}")
                    self._log_message(f"  {progress_info}")
                    
                    if has_mismatch:
                        self._log_message(f"  ⚠ Hoiatus: Pooleli töö kasutab mudelit {checkpoint_model}")
                        self._show_model_mismatch_dialog(file_path_str, checkpoint_model)
                    else:
                        self._show_resume_dialog(file_path_str, checkpoint)
                else:
                    # Checkpoint is invalid
                    self._log_message(f"⚠ {validation_msg}")
                    self.resume_mode[file_path_str] = "new"
    
    def _show_resume_dialog(self, file_path_str: str, checkpoint: Dict):
        """Show dialog asking whether to resume interrupted translation"""
        file_path = Path(file_path_str)
        progress_info = CheckpointManager.get_progress_summary(checkpoint)
        
        dialog_msg = (
            f"Leiti pooleli jäänud tõlge: {file_path.name}\n"
            f"{progress_info}\n\n"
            f"Kas soovid jätkata pooleli jäänud kohast?"
        )
        
        result = messagebox.askyesnocancel(
            "Pooleli jäänud tõlge",
            dialog_msg,
            icon=messagebox.QUESTION
        )
        
        if result is True:
            # Yes - resume
            self.resume_mode[file_path_str] = "resume"
            self._log_message(f"✓ Jätkatakse pooleli jäänud tõlkest: {file_path.name}")
        elif result is False:
            # No - restart from beginning
            self.resume_mode[file_path_str] = "restart"
            self._log_message(f"ℹ Alustatakse algusest: {file_path.name}")
        else:
            # Cancel - don't translate
            self.resume_mode[file_path_str] = "cancel"
            self._log_message(f"⚠ Tõlkimine tühistatud: {file_path.name}")
    
    def _show_model_mismatch_dialog(self, file_path_str: str, checkpoint_model: str):
        """Show dialog for model mismatch in checkpoint"""
        file_path = Path(file_path_str)
        progress_info = CheckpointManager.get_progress_summary(self.file_checkpoints[file_path_str])
        
        current_model_name = self.selected_model.get().split("—")[0].strip()
        checkpoint_model_name = checkpoint_model
        
        dialog_msg = (
            f"Pooleli jäänud tõlge kasutab mudelit: {checkpoint_model_name}\n"
            f"Praegu valitud mudel: {current_model_name}\n"
            f"{progress_info}\n\n"
            f"Vali:",
        )
        
        response = messagebox.askyesnocancel(
            "Mudeli joonis",
            f"{dialog_msg}\n"
            f"Jah - Jätka vana mudeliga\n"
            f"Ei - Alusta uue mudeliga\n"
            f"Tühista - Jätka kantsutamata",
            icon=messagebox.WARNING
        )
        
        if response is True:
            # Yes - continue with old model
            self.resume_mode[file_path_str] = "resume"
            self._log_message(f"✓ Jätkatakse vana mudeliga: {checkpoint_model_name}")
        elif response is False:
            # No - restart with new model
            self.resume_mode[file_path_str] = "restart"
            self._log_message(f"ℹ Alustatakse uue mudeliga: {current_model_name}")
        else:
            # Cancel
            self.resume_mode[file_path_str] = "cancel"
            self._log_message(f"⚠ Tõlkimine tühistatud")

    
    def _update_estimate_button_state(self):
        """Enable/disable estimate button based on available files"""
        can_estimate = False
        
        if self.workflow_mode.get() == "subtitle_files":
            can_estimate = len(self.selected_subtitle_files) > 0
        else:
            # For MKV workflow, check if folder has .en.srt files
            folder_path = self.selected_folder.get()
            if folder_path:
                folder = Path(folder_path)
                if folder.exists():
                    en_srt_files = list(folder.glob("*.en.srt"))
                    can_estimate = len(en_srt_files) > 0
        
        state = "normal" if can_estimate else "disabled"
        self.estimate_cost_button.config(state=state)

    def _start_processing(self):
        """Handle start processing button click - MKV folder workflow only"""
        # Check workflow mode
        if self.workflow_mode.get() != "mkv_folder":
            self._log_message("⚠ Viga: Töötlemist saab alustada ainult MKV-failide töörežiimis!")
            return

        folder_path = self.selected_folder.get()
        if not folder_path:
            self._log_message("⚠ Viga: Palun valige esmalt kaust!")
            return

        folder = Path(folder_path)
        if not folder.exists():
            self._log_message(f"⚠ Viga: Kausta ei eksisteeri: {folder_path}")
            return

        # Check if mkvmerge is available
        error_msg = self.mkv_tools.get_error_message()
        if error_msg:
            self._log_message(f"⚠ {error_msg}")
            return

        # Find all MKV files
        self.mkv_files = sorted(folder.glob("*.mkv"))

        if not self.mkv_files:
            self._log_message(
                f"ℹ Informatsioon: Kaustast ei leitud MKV faile: {folder_path}"
            )
            return

        # Initialize processing state
        self.is_processing = True
        self.cancel_requested = False
        self.current_file_index = 0
        self.processing_stats = {
            "total": len(self.mkv_files),
            "with_english": 0,
            "without_english": 0,
            "extracted": 0,
            "skipped_existing": 0,
            "extraction_errors": 0,
            "errors": 0,
        }

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.update_progress(0, len(self.mkv_files))

        # Reset error state for new processing session
        self._clear_log_and_reset_error()

        self._log_message(
            f"Töötlemine alustatud. Leitud {len(self.mkv_files)} MKV faili."
        )

        # Start async processing
        self._process_next_file()

    def _process_next_file(self):
        """Process the next MKV file in the queue"""
        if self.cancel_requested or not self.is_processing:
            self._finish_processing()
            return

        if self.current_file_index >= len(self.mkv_files):
            # All files processed
            self._show_processing_summary()
            self._finish_processing()
            return

        mkv_file = self.mkv_files[self.current_file_index]

        try:
            self.set_current_file(mkv_file.name)
            self._log_message(f"\nTöötlemise all: {mkv_file.name}")

            # Identify subtitles
            mkv_info = self.mkv_tools.identify_subtitles(mkv_file)

            if mkv_info.error:
                self._log_message(f"  ⚠ Viga: {mkv_info.error}")
                self.processing_stats["errors"] += 1
            else:
                self._log_message(f"  Leitud {len(mkv_info.subtitles)} subtiitri rada")

                if mkv_info.subtitles:
                    for subtitle in mkv_info.subtitles:
                        self._log_message(f"    - {subtitle}")

                best_english = mkv_info.get_best_english_track()
                if best_english:
                    self._log_message(
                        f"  ✓ Parim inglise keelse subtiitri rada: {best_english}"
                    )
                    self.processing_stats["with_english"] += 1

                    # Try to extract the subtitle
                    success, result = self.mkv_tools.extract_subtitle(
                        mkv_file, best_english
                    )
                    if success:
                        output_file = Path(result)
                        self._log_message(
                            f"  ✓ Ekstraheeritud: {output_file.name}"
                        )
                        self.processing_stats["extracted"] += 1
                    else:
                        if result == "Juba olemas":
                            self._log_message(f"  ℹ Inglise subtiiter on juba olemas – jäeti vahele.")
                            self.processing_stats["skipped_existing"] += 1
                        else:
                            self._log_message(f"  ⚠ Ekstrakteerimine ebaõnnestus: {result}")
                            self.processing_stats["extraction_errors"] += 1
                else:
                    self._log_message("  - Inglise keelsed subtiitrid puuduvad")
                    self.processing_stats["without_english"] += 1

        except Exception as e:
            self._log_message(f"  ⚠ Pead viga töötlemise ajal: {e}")
            self.processing_stats["errors"] += 1

        # Update progress
        self.current_file_index += 1
        self.update_counter(self.current_file_index)
        self.update_progress(self.current_file_index, len(self.mkv_files))

        # Schedule next file processing
        self.root.after(100, self._process_next_file)

    def _cancel_processing(self):
        """Handle cancel processing button click - works for both MKV and translation"""
        # Check if translation is in progress
        if self.translation_in_progress and self.threaded_translation_worker:
            self._log_message("\nTöö katkestamise nõue saadetud...")
            self.threaded_translation_worker.cancel()
        else:
            # MKV processing cancellation
            self.cancel_requested = True
            self._log_message("\nTöötlemine katkestati kasutaja soovil.")

    def _finish_processing(self):
        """Clean up after processing finishes or is cancelled"""
        self.is_processing = False
        self.cancel_requested = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.set_current_file("-")

    def _show_processing_summary(self):
        """Show a summary of the processing results"""
        stats = self.processing_stats
        self._log_message("\n" + "=" * 60)
        self._log_message("TÖÖTLEMISE KOKKUVÕTE")
        self._log_message("=" * 60)
        self._log_message(f"MKV faile kokku: {stats['total']}")
        self._log_message(f"Inglise subtiitrid leitud: {stats['with_english']}")
        self._log_message(f"Subtiitrid ekstraheeritud: {stats['extracted']}")
        self._log_message(f"Juba olemasolevad (jäetud vahele): {stats['skipped_existing']}")
        self._log_message(f"Ilma inglise subtiitriteta: {stats['without_english']}")
        self._log_message(f"Ekstrakteerimisvead: {stats['extraction_errors']}")
        self._log_message(f"Muud vead: {stats['errors']}")
        self._log_message("=" * 60)

    def _start_translation(self):
        """Handle start translation button click - launches threaded worker"""
        api_key = self.api_key.get()
        if not api_key:
            self._log_message("⚠ Viga: Palun sisestage OpenAI API võti!")
            return

        # Determine which files to translate based on workflow mode
        files_to_translate = []
        
        if self.workflow_mode.get() == "subtitle_files":
            # Workflow 1: Direct subtitle file translation
            if not self.selected_subtitle_files:
                self._log_message("⚠ Viga: Palun valige alustuseks subtiitrifailid!")
                return
            
            files_to_translate = [Path(f) for f in self.selected_subtitle_files]
            self._log_message(f"ℹ Tõlgitakse valitud subtiitrifailid ({len(files_to_translate)} faili)")
        else:
            # Workflow 2: Folder-based (MKV-derived .en.srt files)
            folder_path = self.selected_folder.get()
            if not folder_path:
                self._log_message("⚠ Viga: Palun valige kaust!")
                return

            folder = Path(folder_path)
            if not folder.exists():
                self._log_message(f"⚠ Viga: Kausta ei eksisteeri: {folder_path}")
                return

            # Find all .en.srt files in the folder
            en_srt_files = sorted(folder.glob("*.en.srt"))

            if not en_srt_files:
                self._log_message(
                    f"ℹ Informatsioon: Kaustast ei leitud .en.srt faile: {folder_path}"
                )
                return

            files_to_translate = en_srt_files

        # Check language warnings before translation (for subtitle_files workflow)
        if self.workflow_mode.get() == "subtitle_files":
            if not self._check_translation_language_warning():
                self._log_message("⚠ Tõlkimine katkestati kasutaja valikule.")
                return
        
        # Check for cancelled resume
        for file_path_str in [str(f) for f in files_to_translate]:
            if self.resume_mode.get(file_path_str) == "cancel":
                self._log_message(f"⚠ Tõlkimine tühistatud: {Path(file_path_str).name}")
                return

        # Create backups before translation starts
        self._log_message("\nVarukoopiate loomine...")
        for file_path in files_to_translate:
            can_proceed, backup_msg = BackupManager.check_backup_before_translation(file_path)
            self._log_message(backup_msg)
            if not can_proceed:
                self._log_message(f"✗ Tõlkimine peatatud varukoopia loomine ebaõnnestus.")
                return

        # Get the selected model display name and map it to API model ID
        model_display_name = self.selected_model.get()
        model_api_id = self.model_display_to_api.get(model_display_name, "gpt-4.1")
        
        self.current_model_name = model_display_name
        self.current_model_api_id = model_api_id

        try:
            # Initialize threaded translation worker
            self.threaded_translation_worker = ThreadedTranslationWorker(api_key, model_api_id)
        except Exception as e:
            self._log_message(f"⚠ Viga OpenAI kliendi initsialiseerimisel: {e}")
            return

        # Reset stats for translation phase
        self.processing_stats["en_srt_files"] = len(files_to_translate)
        self.processing_stats["translated"] = 0
        self.processing_stats["skipped_translated"] = 0
        self.processing_stats["translation_errors"] = 0

        # Update UI state
        self._disable_ui_during_translation()
        self._show_working_status(f"Tõö käib... Palun oota.")
        
        # Reset error state for new translation session
        self._clear_log_and_reset_error()
        
        self._log_message(f"\nTõlkimine käivitatud...")
        self._log_message(f"Mudel: {model_display_name}")
        self._log_message(f"Leitud {len(files_to_translate)} subtiitrifaili.")
        
        # Switch progress bar to indeterminate mode for API calls
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(files_to_translate)
        
        # Store files and checkpoint info for translation worker
        self.files_with_checkpoints = {
            str(f): {
                "checkpoint": self.file_checkpoints.get(str(f)),
                "resume_mode": self.resume_mode.get(str(f), "new"),
            }
            for f in files_to_translate
        }
        
        # Start background translation thread
        self.translation_in_progress = True
        self.threaded_translation_worker.start_translation(
            files_to_translate,
            file_checkpoint_map=self.files_with_checkpoints
        )
        
        # Start polling for messages from the translation thread
        self._poll_translation_messages()

    def _estimate_translation_cost(self):
        """
        Estimate the API cost for translating selected files.
        
        Does NOT require API key and does NOT make any API calls.
        Shows detailed estimate in the activity log.
        """
        # Determine which files to estimate based on workflow mode
        files_to_estimate = []
        
        if self.workflow_mode.get() == "subtitle_files":
            # Workflow 1: Direct subtitle file translation
            if not self.selected_subtitle_files:
                self._log_message("⚠ Viga: Palun valige alustuseks subtiitrifailid!")
                return
            
            files_to_estimate = [Path(f) for f in self.selected_subtitle_files]
        else:
            # Workflow 2: Folder-based (MKV-derived .en.srt files)
            folder_path = self.selected_folder.get()
            if not folder_path:
                self._log_message("⚠ Viga: Palun valige kaust!")
                return

            folder = Path(folder_path)
            if not folder.exists():
                self._log_message(f"⚠ Viga: Kausta ei eksisteeri: {folder_path}")
                return

            # Find all .en.srt files in the folder
            en_srt_files = sorted(folder.glob("*.en.srt"))

            if not en_srt_files:
                self._log_message(
                    f"ℹ Informatsioon: Kaustast ei leitud .en.srt faile: {folder_path}"
                )
                return

            files_to_estimate = en_srt_files

        # Get the selected model display name and configuration
        model_display_name = self.selected_model.get()
        model_config = self.MODEL_CONFIG.get(model_display_name)
        
        if not model_config:
            self._log_message("⚠ Viga: Mudelit ei leitud!")
            return
        
        # Calculate the estimate
        estimate = self.cost_estimator.estimate_cost(files_to_estimate, model_config)
        
        # Format and display the result
        formatted_estimate = self.cost_estimator.format_cost_estimate(
            estimate, model_display_name
        )
        
        self._log_message(formatted_estimate)

    def _detect_selected_file_languages(self):
        """
        Detect languages in selected subtitle files and display results.
        
        Called when files are selected via file dialog.
        """
        if not self.selected_subtitle_files:
            self.detected_files_languages = {}
            return
        
        # Detect languages
        file_paths = [Path(f) for f in self.selected_subtitle_files]
        detections = self.language_detector.detect_languages_in_files(file_paths)
        
        # Store detected languages
        self.detected_files_languages = {
            Path(f).name: det for f, det in zip(self.selected_subtitle_files, detections)
        }
        
        # Display results in log
        if detections:
            formatted = self.language_detector.format_detections_for_log(detections)
            self._log_message(formatted)
            
            # Show summary if multiple languages
            summary = self.language_detector.summarize_detections(detections)
            if not summary["all_same"]:
                summary_text = self.language_detector.format_summary_for_log(summary)
                self._log_message(f"\n{summary_text}")

    def _check_translation_language_warning(self) -> bool:
        """
        Check detected languages and show warning if needed before translation.
        
        Returns:
            True if user wants to continue, False if cancelled
        """
        if not self.detected_files_languages:
            return True  # No detection data, allow translation
        
        # Summarize detections
        detections = list(self.detected_files_languages.values())
        summary = self.language_detector.summarize_detections(detections)
        
        # Check for Estonian files
        if summary["has_estonian"] and not summary["all_same"]:
            # Mixed languages including Estonian
            message = (
                "Valitud failides tuvastati erinevad keeled:\n\n"
                + self.language_detector.format_summary_for_log(summary).replace("Keeled:\n", "")
                + "\n\nJätkaS?"
            )
            response = messagebox.askyesno("Keele hoiatus", message, default=messagebox.NO)
            return response
        
        if summary["has_estonian"] and summary["all_same"] and len(detections) > 0:
            # All files are Estonian
            code = detections[0]["language_code"]
            if code == "et":
                message = (
                    "Fail tundub juba olevat eesti keeles.\n"
                    "Kas soovid selle siiski tõlkida?"
                )
                response = messagebox.askyesno(
                    "Keele hoiatus", message, default=messagebox.NO
                )
                return response
        
        # Check for non-English, non-Estonian languages
        if summary["has_other"]:
            language_names = [
                name for name in summary["by_display_name"].keys()
                if name != "Inglise" and name != "Eesti" and name != "Teadmata"
            ]
            
            if language_names:
                language = language_names[0]
                message = (
                    f"Faili tuvastatud keel on: {language}.\n"
                    "Programm on praegu optimeeritud inglise -> eesti tõlkeks.\n"
                    "Kas soovid siiski jätkata?"
                )
                response = messagebox.askyesno(
                    "Keele hoiatus", message, default=messagebox.NO
                )
                return response
        
        return True  # No warnings needed, proceed

    def _disable_ui_during_translation(self):
        """Disable UI elements while translation is in progress"""
        # Disable workflow selection
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                # Check if this is the workflow card by looking at its content
                try:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Radiobutton):
                            child.config(state="disabled")
                except:
                    pass
        
        # Disable file/folder selection
        if self.folder_card and self.folder_card['frame'].winfo_manager():
            for widget in self.folder_card['content'].winfo_children():
                self._disable_widget_tree(widget)
        if self.subtitle_card and self.subtitle_card['frame'].winfo_manager():
            for widget in self.subtitle_card['content'].winfo_children():
                self._disable_widget_tree(widget)
        
        # Disable API settings
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                # Try to disable entry fields and comboboxes
                try:
                    for child in widget.winfo_children():
                        if isinstance(child, (ttk.Entry, ttk.Combobox)):
                            child.config(state="disabled")
                except:
                    pass
        
        # Disable buttons
        self.translate_button.config(state="disabled")
        self.start_button.config(state="disabled")
        self.estimate_cost_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def _enable_ui_after_translation(self):
        """Re-enable UI elements after translation finishes"""
        # Enable workflow selection
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                try:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Radiobutton):
                            child.config(state="normal")
                except:
                    pass
        
        # Enable file/folder selection
        if self.folder_card and self.folder_card['frame'].winfo_manager():
            for widget in self.folder_card['content'].winfo_children():
                self._enable_widget_tree(widget)
        if self.subtitle_card and self.subtitle_card['frame'].winfo_manager():
            for widget in self.subtitle_card['content'].winfo_children():
                self._enable_widget_tree(widget)
        
        # Enable API settings
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                try:
                    for child in widget.winfo_children():
                        if isinstance(child, (ttk.Entry, ttk.Combobox)):
                            child.config(state="normal")
                except:
                    pass
        
        # Re-enable buttons
        self.translate_button.config(state="normal")
        self.start_button.config(state="normal")
        self.estimate_cost_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def _disable_widget_tree(self, widget):
        """Recursively disable a widget and its children"""
        try:
            widget.config(state="disabled")
        except:
            pass
        for child in widget.winfo_children():
            self._disable_widget_tree(child)
    
    def _enable_widget_tree(self, widget):
        """Recursively enable a widget and its children"""
        try:
            widget.config(state="normal")
        except:
            pass
        for child in widget.winfo_children():
            self._enable_widget_tree(child)

    def _show_working_status(self, message: str):
        """Show working status message"""
        self.status_label.config(text=message, foreground=self.colors['accent'])

    def _clear_working_status(self):
        """Clear working status message"""
        self.status_label.config(text="Valmis töötamiseks", foreground=self.colors['success'])

    def _poll_translation_messages(self):
        """Poll translation worker thread for messages"""
        if not self.translation_in_progress or not self.threaded_translation_worker:
            return
        
        # Get and process all available messages from the queue
        while True:
            msg = self.threaded_translation_worker.get_message(timeout=0)
            if msg is None:
                break
            
            msg_type = msg.get("type")
            
            if msg_type == ThreadedTranslationWorker.MSG_START:
                self._log_message("Alustatud faili tõlkimist...")
                
            elif msg_type == ThreadedTranslationWorker.MSG_FILE_START:
                file_name = msg.get("file_name", "-")
                file_num = msg.get("file_num", 0)
                total_files = msg.get("total_files", 0)
                self._log_message(f"\nTõlgin: {file_name}")
                if total_files > 1:
                    self._log_message(f"Fail {file_num} / {total_files}")
                
            elif msg_type == ThreadedTranslationWorker.MSG_BATCH_PROGRESS:
                log_msg = msg.get("log_message", "")
                self._log_message(log_msg)
                # Start indeterminate animation while waiting for API
                if self.progress_bar["value"] == 0 and self.current_file_index == 0:
                    try:
                        self.progress_bar.start(10)
                    except:
                        pass  # May already be started
                
            elif msg_type == ThreadedTranslationWorker.MSG_BATCH_COMPLETE:
                log_msg = msg.get("log_message", "")
                self._log_message(log_msg)
                
            elif msg_type == ThreadedTranslationWorker.MSG_FILE_COMPLETE:
                success = msg.get("success", False)
                message = msg.get("message", "")
                file_num = msg.get("file_num", 0)
                total_files = msg.get("total_files", 0)
                
                if success:
                    self._log_message(f"  ✓ Tõlgitud: {Path(msg.get('output_path', '')).name}")
                    self.processing_stats["translated"] += 1
                else:
                    if message == "Juba olemas":
                        self._log_message(f"  ℹ Eestikeelne subtiiter on juba olemas – jäeti vahele.")
                        self.processing_stats["skipped_translated"] += 1
                    else:
                        self._log_message(f"  ⚠ Tõlkimise viga: {message}")
                        self.processing_stats["translation_errors"] += 1
                
                # Update progress
                self.update_progress(file_num, total_files)
                self.update_counter(file_num)
                
            elif msg_type == ThreadedTranslationWorker.MSG_STATUS_UPDATE:
                log_msg = msg.get("log_message", "")
                self._log_message(log_msg)
                
            elif msg_type == ThreadedTranslationWorker.MSG_ERROR:
                error = msg.get("error", "")
                self._log_message(f"⚠ Viga: {error}")
                self.processing_stats["translation_errors"] += 1
                self._finish_translation_session("Tõlkimisel tekkis viga.")
                
            elif msg_type == ThreadedTranslationWorker.MSG_COMPLETE:
                # Stop progress bar animation
                try:
                    self.progress_bar.stop()
                except:
                    pass
                self.progress_bar["value"] = self.progress_bar["maximum"]
                self._show_working_status("Valmis!")
                self._show_translation_summary()
                self._finish_translation_session()
                return  # Stop polling
                
            elif msg_type == ThreadedTranslationWorker.MSG_CANCELLED:
                # Stop progress bar animation
                try:
                    self.progress_bar.stop()
                except:
                    pass
                self._show_working_status("Töö katkestatud.")
                self._finish_translation_session()
                return  # Stop polling
        
        # Schedule next poll
        if self.translation_in_progress:
            self.root.after(100, self._poll_translation_messages)

    def _finish_translation_session(self, error_status: str = None):
        """Clean up after translation session"""
        self.translation_in_progress = False
        
        # Stop progress bar animation if running
        try:
            self.progress_bar.stop()
        except:
            pass
        
        if error_status:
            self._show_working_status(error_status)
        
        self._enable_ui_after_translation()

    def _calculate_api_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
    ) -> float:
        """
        Calculate the estimated API cost based on token usage and current model.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            
        Returns:
            Estimated cost in USD (rounded to 4 decimal places)
        """
        # Get pricing for current model, default to gpt-4.1 if not found
        pricing = self.MODEL_PRICING.get(self.current_model_api_id, self.MODEL_PRICING["gpt-4.1"])
        
        # Calculate cost: (tokens / 1,000,000) * price_per_1m_tokens
        regular_input_tokens = max(0, input_tokens - cached_input_tokens)
        input_cost = (regular_input_tokens / 1_000_000) * pricing["input"]
        cached_input_cost = (
            cached_input_tokens / 1_000_000
        ) * pricing.get("cached_input", pricing["input"])
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        total_cost = input_cost + cached_input_cost + output_cost
        
        return round(total_cost, 4)

    def _show_translation_summary(self):
        """Show a summary of the translation results"""
        stats = self.processing_stats
        self._log_message("\n" + "=" * 60)
        self._log_message("TÕLKIMISE KOKKUVÕTE")
        self._log_message("=" * 60)
        self._log_message(f"Mudel: {self.current_model_name}")
        self._log_message(f".en.srt faile kokku: {stats['en_srt_files']}")
        self._log_message(f"Edukalt tõlgitud: {stats['translated']}")
        self._log_message(f"Juba olemasolevad (jäetud vahele): {stats['skipped_translated']}")
        self._log_message(f"Tõlkimisevead: {stats['translation_errors']}")
        
        # Display token usage if translation was performed
        if self.threaded_translation_worker:
            token_usage = self.threaded_translation_worker.get_token_usage()
            if token_usage["total_tokens"] > 0:
                self._log_message("\nMarkeritud tokenid:")
                self._log_message(f"  Sisendi tokenid: {token_usage['input_tokens']}")
                self._log_message(f"  Väljundi tokenid: {token_usage['output_tokens']}")
                self._log_message(f"  Kokku: {token_usage['total_tokens']}")
                
                # Calculate and display estimated API cost
                estimated_cost = self._calculate_api_cost(
                    token_usage['input_tokens'],
                    token_usage['output_tokens'],
                    token_usage.get('cached_input_tokens', 0),
                )
                self._log_message(f"\nHinnanguline API kulu:")
                self._log_message(f"  ${estimated_cost:.4f}")
        
        self._log_message("=" * 60)

    def _log_message(self, message: str):
        """Add a message to the log area"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")  # Auto-scroll to the end
        self.log_text.config(state="disabled")
        
        # Auto-open log for serious errors
        is_serious_error = any(error_marker in message for error_marker in [
            "⚠ Viga:",  # Error prefix
            "⚠",        # Warning symbol
            "✗ Viga:",  # Fatal error
            "OpenAI",   # API errors
            "Tõlkimise viga:",  # Translation error
            "Ekstrakteerimisel ebao",  # Extraction error
            "ei eksisteeri",  # File not found
            "ebaõnnestus",  # Failed
        ])
        
        if is_serious_error and not self.log_is_expanded:
            self._show_error_and_open_log(message)
    
    def _toggle_log_visibility(self):
        """Toggle between collapsed and expanded log view"""
        if self.log_is_expanded:
            # Collapse the log
            self.log_is_expanded = False
            self.log_card_frame.grid_remove()
            self.log_toggle_button.config(text="Näita logi ▼")
            # Clear error indicator when collapsing
            # (will re-appear if another error occurs)
            self._update_log_error_indicator()
        else:
            # Expand the log
            self.log_is_expanded = True
            self.log_card_frame.grid()
            self.log_toggle_button.config(text="Peida logi ▲")
            # Clear error indicator when expanded
            self.log_has_error = False
            self._update_log_error_indicator()
    
    def _show_error_and_open_log(self, error_message: str):
        """Automatically open log when a serious error occurs"""
        if not self.log_is_expanded:
            self.log_is_expanded = True
            self.log_card_frame.grid()
            self.log_toggle_button.config(text="Peida logi ▲")
        
        self.log_has_error = True
        self._update_log_error_indicator()
    
    def _update_log_error_indicator(self):
        """Update the error indicator in the collapsed header"""
        try:
            # Try Unicode warning symbol first
            if self.log_has_error and not self.log_is_expanded:
                self.log_error_indicator.config(text="— ⚠ viga")
            else:
                self.log_error_indicator.config(text="")
        except:
            # Fallback for fonts without Unicode support
            if self.log_has_error and not self.log_is_expanded:
                self.log_error_indicator.config(text="— Viga")
            else:
                self.log_error_indicator.config(text="")
    
    def _clear_log_and_reset_error(self):
        """Reset error state when starting a new job"""
        self.log_has_error = False
        self._update_log_error_indicator()

    def update_progress(self, value: int, maximum: int = 100):
        """Update the progress bar"""
        self.progress_bar["maximum"] = maximum
        self.progress_bar["value"] = value

    def set_current_file(self, filename: str):
        """Update the current file label"""
        self.current_file_label.config(text=f"Jooksev fail: {filename}")

    def update_counter(self, count: int):
        """Update the processed files counter"""
        self.processed_count.set(count)
        self.counter_label.config(text=f"Töödeldud failid: {count}")
    
    def set_batch_progress(self, batch_num: int, total_batches: int):
        """Update the batch progress display"""
        if total_batches > 0:
            self.batch_label.config(text=f"Plokk: {batch_num} / {total_batches}")
        else:
            self.batch_label.config(text="Plokk: -")
