"""
BENSON v2.0 - FIXED Beautiful King Shot Module Settings Window
FIXED: Removed empty bg="" that caused color errors
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class KingShotModuleSettings:
    """Fixed beautiful module settings window"""
    
    def __init__(self, parent, instance_name, app_ref=None):
        self.parent = parent
        self.instance_name = instance_name
        self.app_ref = app_ref
        
        # Load current settings
        self.settings_file = f"settings_{instance_name}.json"
        self.settings = self._load_settings()
        
        # Current selection
        self.current_module = "autostart_game"
        
        # Create window
        self._create_window()
        
        # Setup layout
        self._setup_header()
        self._setup_main_content()
        self._setup_footer()
        
        # Load initial module
        self._show_module_settings("autostart_game")
    
    def _create_window(self):
        """Create the main settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"King Shot Modules - {self.instance_name}")
        self.window.geometry("1000x700")
        self.window.configure(bg="#0f0f23")
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.resizable(True, True)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500)
        y = (self.window.winfo_screenheight() // 2) - (350)
        self.window.geometry(f"1000x700+{x}+{y}")
    
    def _setup_header(self):
        """Setup beautiful header"""
        header = tk.Frame(self.window, bg="#1a1a3a", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header, bg="#1a1a3a")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Left side - Title
        title_frame = tk.Frame(header_content, bg="#1a1a3a")
        title_frame.pack(side="left", fill="y")
        
        tk.Label(
            title_frame,
            text="🎯 King Shot Automation",
            bg="#1a1a3a",
            fg="#ffffff",
            font=("Segoe UI", 16, "bold")
        ).pack(side="top", anchor="w")
        
        tk.Label(
            title_frame,
            text=f"✨ Instance: {self.instance_name}",
            bg="#1a1a3a",
            fg="#64b5f6",
            font=("Segoe UI", 11)
        ).pack(side="top", anchor="w", pady=(5, 0))
        
        # Right side - Status and controls
        right_frame = tk.Frame(header_content, bg="#1a1a3a")
        right_frame.pack(side="right", fill="y")
        
        # Instance status
        if self.app_ref:
            instance = self.app_ref.instance_manager.get_instance(self.instance_name)
            status = instance["status"] if instance else "Unknown"
            status_colors = {
                "Running": "#4caf50",
                "Stopped": "#757575",
                "Starting": "#ff9800",
                "Stopping": "#f44336"
            }
            status_color = status_colors.get(status, "#757575")
            
            tk.Label(
                right_frame,
                text=f"● {status}",
                bg="#1a1a3a",
                fg=status_color,
                font=("Segoe UI", 12, "bold")
            ).pack(side="top", anchor="e")
        
        # Close button
        close_btn = tk.Button(
            right_frame,
            text="✕",
            bg="#1a1a3a",
            fg="#ff5252",
            relief="flat",
            bd=0,
            font=("Segoe UI", 18, "bold"),
            cursor="hand2",
            width=3,
            command=self._close_window
        )
        close_btn.pack(side="top", anchor="e", pady=(10, 0))
        
        # Hover effects
        def on_enter(e): close_btn.configure(fg="#ff8a80")
        def on_leave(e): close_btn.configure(fg="#ff5252")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)
    
    def _setup_main_content(self):
        """Setup main content"""
        main_container = tk.Frame(self.window, bg="#0f0f23")
        main_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Sidebar
        self._setup_sidebar(main_container)
        
        # Content area
        self._setup_content_area(main_container)
    
    def _setup_sidebar(self, parent):
        """Setup sidebar"""
        sidebar_container = tk.Frame(parent, bg="#1a1a3a", width=250, relief="solid", bd=1)
        sidebar_container.pack(side="left", fill="y", padx=(0, 15))
        sidebar_container.pack_propagate(False)
        
        # Sidebar header
        header_frame = tk.Frame(sidebar_container, bg="#2d2d5a", height=50)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔧 Game Modules",
            bg="#2d2d5a",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=15)
        
        # Separator
        tk.Frame(sidebar_container, bg="#4a90e2", height=2).pack(fill="x")
        
        # Create module cards
        self._create_module_cards(sidebar_container)
    
    def _create_module_cards(self, parent):
        """Create module cards"""
        # Module definitions
        self.modules = [
            {
                "id": "autostart_game",
                "name": "AutoStart Game",
                "icon": "🎮",
                "color": "#4caf50",
                "description": "Automatically launches King Shot",
                "required": True
            },
            {
                "id": "auto_gather",
                "name": "AutoGather",
                "icon": "⛏️",
                "color": "#ff9800",
                "description": "Smart resource gathering",
                "required": False
            },
            {
                "id": "auto_train",
                "name": "AutoTrain",
                "icon": "🏋️",
                "color": "#e91e63",
                "description": "Automated troop training",
                "required": False
            },
            {
                "id": "auto_mail",
                "name": "AutoMail",
                "icon": "📬",
                "color": "#2196f3",
                "description": "Mail and rewards collector",
                "required": False
            },
            {
                "id": "march_assignment",
                "name": "March Queues",
                "icon": "⚔️",
                "color": "#9c27b0",
                "description": "Manage army march slots",
                "required": False
            }
        ]
        
        # Cards container
        cards_container = tk.Frame(parent, bg="#1a1a3a")
        cards_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.module_cards = {}
        for module in self.modules:
            self._create_module_card(cards_container, module)
    
    def _create_module_card(self, parent, module):
        """Create a module card"""
        module_id = module["id"]
        is_enabled = self.settings.get(module_id, {}).get("enabled", True)
        
        # Card
        card = tk.Frame(parent, bg="#1e1e3f", relief="solid", bd=1)
        card.pack(fill="x", pady=3)
        
        # Colored border
        border_frame = tk.Frame(card, bg=module["color"], height=3)
        border_frame.pack(fill="x")
        
        # Content
        content = tk.Frame(card, bg="#1e1e3f")
        content.pack(fill="x", padx=15, pady=12)
        
        # Top row
        top_row = tk.Frame(content, bg="#1e1e3f")
        top_row.pack(fill="x")
        
        # Icon
        tk.Label(
            top_row,
            text=module['icon'],
            bg="#1e1e3f",
            fg=module["color"],
            font=("Segoe UI", 16),
            width=3
        ).pack(side="left")
        
        # Text
        text_frame = tk.Frame(top_row, bg="#1e1e3f")
        text_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        tk.Label(
            text_frame,
            text=module['name'],
            bg="#1e1e3f",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).pack(fill="x")
        
        tk.Label(
            text_frame,
            text=module['description'],
            bg="#1e1e3f",
            fg="#b0b0b0",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(fill="x")
        
        # Status
        if module.get("required"):
            status_text = "REQ"
            status_color = "#4caf50"
        elif is_enabled:
            status_text = "ON"
            status_color = "#2196f3"
        else:
            status_text = "OFF"
            status_color = "#757575"
        
        tk.Label(
            top_row,
            text=status_text,
            bg="#1e1e3f",
            fg=status_color,
            font=("Segoe UI", 8, "bold")
        ).pack(side="right", padx=(10, 0))
        
        # Click handler
        def on_click(event):
            self._show_module_settings(module_id)
            self._update_card_selection(module_id)
        
        # Hover effects
        def on_enter(event):
            card.configure(bg="#252550")
            content.configure(bg="#252550")
            
        def on_leave(event):
            if module_id != self.current_module:
                card.configure(bg="#1e1e3f")
                content.configure(bg="#1e1e3f")
        
        # Bind events
        for widget in [card, content, top_row, text_frame]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        self.module_cards[module_id] = {
            "card": card,
            "content": content,
            "color": module["color"]
        }
    
    def _update_card_selection(self, module_id):
        """Update card selection"""
        for mid, card_info in self.module_cards.items():
            if mid == module_id:
                card_info["card"].configure(bg="#2d2d5a")
                card_info["content"].configure(bg="#2d2d5a")
            else:
                card_info["card"].configure(bg="#1e1e3f")
                card_info["content"].configure(bg="#1e1e3f")
    
    def _setup_content_area(self, parent):
        """Setup content area"""
        self.content_area = tk.Frame(parent, bg="#1a1a3a", relief="solid", bd=1)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Header
        self.content_header = tk.Frame(self.content_area, bg="#2d2d5a", height=60)
        self.content_header.pack(fill="x")
        self.content_header.pack_propagate(False)
        
        # Scrollable content
        self._setup_scrollable_content()
    
    def _setup_scrollable_content(self):
        """Setup scrollable content"""
        canvas_frame = tk.Frame(self.content_area, bg="#1a1a3a")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.content_canvas = tk.Canvas(
            canvas_frame, 
            bg="#0f0f23", 
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            canvas_frame, 
            orient="vertical", 
            command=self.content_canvas.yview
        )
        
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.content_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.content_frame = tk.Frame(self.content_canvas, bg="#0f0f23")
        self.content_window = self.content_canvas.create_window(0, 0, anchor="nw", window=self.content_frame)
        
        # Bind scroll events
        def configure_scroll_region(event):
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        
        def configure_canvas_width(event):
            canvas_width = self.content_canvas.winfo_width()
            self.content_canvas.itemconfig(self.content_window, width=canvas_width)
        
        self.content_frame.bind("<Configure>", configure_scroll_region)
        self.content_canvas.bind("<Configure>", configure_canvas_width)
        
        # Mouse wheel
        def _on_mousewheel(event):
            self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.content_canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _show_module_settings(self, module_id):
        """Show settings for module"""
        self.current_module = module_id
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        for widget in self.content_header.winfo_children():
            widget.destroy()
        
        # Header
        module_info = next((m for m in self.modules if m["id"] == module_id), None)
        if module_info:
            header_content = tk.Frame(self.content_header, bg="#2d2d5a")
            header_content.pack(fill="both", expand=True, padx=20, pady=15)
            
            tk.Label(
                header_content,
                text=f"{module_info['icon']} {module_info['name']}",
                bg="#2d2d5a",
                fg="#ffffff",
                font=("Segoe UI", 16, "bold")
            ).pack(side="left")
        
        # Show settings
        if module_id == "autostart_game":
            self._show_autostart_settings()
        elif module_id == "auto_gather":
            self._show_gather_settings()
        elif module_id == "auto_train":
            self._show_train_settings()
        elif module_id == "auto_mail":
            self._show_mail_settings()
        elif module_id == "march_assignment":
            self._show_march_settings()
    
    def _show_autostart_settings(self):
        """AutoStart settings"""
        settings = self.settings.get("autostart_game", {})
        
        # Enable section
        enable_section = self._create_section("Module Control", "⚙️", "#4caf50")
        
        self.autostart_enabled_var = tk.BooleanVar(value=settings.get("enabled", True))
        tk.Checkbutton(
            enable_section,
            text="🎮 Enable AutoStart Module",
            variable=self.autostart_enabled_var,
            bg="#0f0f23",
            fg="#4caf50",
            selectcolor="#1a1a3a",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        # Auto-startup
        startup_section = self._create_section("Auto-Startup", "🚀", "#2196f3")
        
        self.auto_startup_var = tk.BooleanVar(value=settings.get("auto_startup", False))
        tk.Checkbutton(
            startup_section,
            text="🎮 Auto-start when instance becomes running",
            variable=self.auto_startup_var,
            bg="#0f0f23",
            fg="#2196f3",
            selectcolor="#1a1a3a",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        # Retry settings
        retry_section = self._create_section("Retry Configuration", "🔄", "#ff9800")
        
        retry_frame = tk.Frame(retry_section, bg="#0f0f23")
        retry_frame.pack(fill="x", pady=5)
        
        tk.Label(
            retry_frame,
            text="Max retries:",
            bg="#0f0f23",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.max_retries_var = tk.StringVar(value=str(settings.get("max_retries", 3)))
        tk.Spinbox(
            retry_frame,
            from_=1, to=10,
            textvariable=self.max_retries_var,
            bg="#1a1a3a",
            fg="#ffffff",
            width=5
        ).pack(side="left", padx=(10, 0))
        
        delay_frame = tk.Frame(retry_section, bg="#0f0f23")
        delay_frame.pack(fill="x", pady=5)
        
        tk.Label(
            delay_frame,
            text="Retry delay (seconds):",
            bg="#0f0f23",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.retry_delay_var = tk.StringVar(value=str(settings.get("retry_delay", 10)))
        tk.Spinbox(
            delay_frame,
            from_=5, to=60,
            textvariable=self.retry_delay_var,
            bg="#1a1a3a",
            fg="#ffffff",
            width=5
        ).pack(side="left", padx=(10, 0))
    
    def _show_gather_settings(self):
        """Gather settings"""
        settings = self.settings.get("auto_gather", {})
        
        enable_section = self._create_section("Module Control", "⚙️", "#ff9800")
        
        self.gather_enabled_var = tk.BooleanVar(value=settings.get("enabled", True))
        tk.Checkbutton(
            enable_section,
            text="⛏️ Enable AutoGather Module",
            variable=self.gather_enabled_var,
            bg="#0f0f23",
            fg="#ff9800",
            selectcolor="#1a1a3a",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        # Resource types
        resource_section = self._create_section("Resource Types", "🏗️", "#4caf50")
        
        self.resource_vars = {}
        resources = [
            ("food", "🌾 Food", "#ffeb3b"),
            ("wood", "🪵 Wood", "#8bc34a"),
            ("iron", "⛏️ Iron", "#607d8b"),
            ("stone", "🗿 Stone", "#795548")
        ]
        
        resource_list = settings.get("resource_types", ["food", "wood", "iron", "stone"])
        
        for resource_id, resource_name, color in resources:
            var = tk.BooleanVar(value=resource_id in resource_list)
            self.resource_vars[resource_id] = var
            
            tk.Checkbutton(
                resource_section,
                text=resource_name,
                variable=var,
                bg="#0f0f23",
                fg=color,
                selectcolor="#1a1a3a",
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w", pady=2)
    
    def _show_train_settings(self):
        """Train settings"""
        settings = self.settings.get("auto_train", {})
        
        enable_section = self._create_section("Module Control", "⚙️", "#e91e63")
        
        self.train_enabled_var = tk.BooleanVar(value=settings.get("enabled", True))
        tk.Checkbutton(
            enable_section,
            text="🏋️ Enable AutoTrain Module",
            variable=self.train_enabled_var,
            bg="#0f0f23",
            fg="#e91e63",
            selectcolor="#1a1a3a",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
    
    def _show_mail_settings(self):
        """Mail settings"""
        settings = self.settings.get("auto_mail", {})
        
        enable_section = self._create_section("Module Control", "⚙️", "#2196f3")
        
        self.mail_enabled_var = tk.BooleanVar(value=settings.get("enabled", True))
        tk.Checkbutton(
            enable_section,
            text="📬 Enable AutoMail Module",
            variable=self.mail_enabled_var,
            bg="#0f0f23",
            fg="#2196f3",
            selectcolor="#1a1a3a",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
    
    def _show_march_settings(self):
        """March assignment settings"""
        settings = self.settings.get("march_assignment", {})
        
        # Info section
        info_section = self._create_section("March Queue System", "⚔️", "#9c27b0")
        
        info_frame = tk.Frame(info_section, bg="#1a1a3a", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=5)
        
        tk.Label(
            info_frame,
            text="🏰 March queues are army slots for gathering and rallies.\n" +
                 "⚡ Most players have 2-6 slots depending on VIP level.\n" +
                 "🎯 Configure how BENSON uses your march slots.",
            bg="#1a1a3a",
            fg="#e0e0e0",
            font=("Segoe UI", 10),
            justify="left",
            padx=15,
            pady=12
        ).pack(fill="x")
        
        # Queue config
        queue_section = self._create_section("Queue Configuration", "📋", "#2196f3")
        
        queue_frame = tk.Frame(queue_section, bg="#0f0f23")
        queue_frame.pack(fill="x", pady=5)
        
        tk.Label(
            queue_frame,
            text="Unlocked march queues:",
            bg="#0f0f23",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.unlocked_queues_var = tk.StringVar(value=str(settings.get("unlocked_queues", 2)))
        tk.Spinbox(
            queue_frame,
            from_=1, to=6,
            textvariable=self.unlocked_queues_var,
            bg="#1a1a3a",
            fg="#ffffff",
            width=5
        ).pack(side="left", padx=(10, 0))
    
    def _create_section(self, title, icon, color):
        """Create a section"""
        section = tk.Frame(self.content_frame, bg="#1a1a3a", relief="solid", bd=1)
        section.pack(fill="x", pady=(0, 15))
        
        header = tk.Frame(section, bg=color, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{icon} {title}",
            bg=color,
            fg="#ffffff",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=20, pady=10)
        
        content = tk.Frame(section, bg="#0f0f23")
        content.pack(fill="x", padx=20, pady=15)
        
        return content
    
    def _setup_footer(self):
        """Setup footer"""
        footer = tk.Frame(self.window, bg="#1a1a3a", height=70)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_content = tk.Frame(footer, bg="#1a1a3a")
        footer_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Status
        self.status_label = tk.Label(
            footer_content,
            text="",
            bg="#1a1a3a",
            fg="#b0b0b0",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(side="left")
        
        # Buttons
        btn_frame = tk.Frame(footer_content, bg="#1a1a3a")
        btn_frame.pack(side="right")
        
        # Cancel
        cancel_btn = tk.Button(
            btn_frame,
            text="✕ Cancel",
            bg="#f44336",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._close_window
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Save
        save_btn = tk.Button(
            btn_frame,
            text="💾 Save Settings",
            bg="#4caf50",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._save_settings
        )
        save_btn.pack(side="left")
        
        # Hover effects
        def cancel_enter(e): cancel_btn.configure(bg="#ff6659")
        def cancel_leave(e): cancel_btn.configure(bg="#f44336")
        def save_enter(e): save_btn.configure(bg="#66bb6a")
        def save_leave(e): save_btn.configure(bg="#4caf50")
        
        cancel_btn.bind("<Enter>", cancel_enter)
        cancel_btn.bind("<Leave>", cancel_leave)
        save_btn.bind("<Enter>", save_enter)
        save_btn.bind("<Leave>", save_leave)
    
    def _load_settings(self):
        """Load settings"""
        default_settings = {
            "autostart_game": {
                "enabled": True,
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10
            },
            "auto_gather": {
                "enabled": True,
                "check_interval": 30,
                "resource_types": ["food", "wood", "iron", "stone"],
                "max_concurrent_gathers": 5
            },
            "auto_train": {
                "enabled": True,
                "check_interval": 60,
                "training_priority": ["infantry", "ranged", "cavalry", "siege"]
            },
            "auto_mail": {
                "enabled": True,
                "check_interval": 120,
                "claim_resources": True,
                "claim_items": True,
                "claim_speedups": True,
                "claim_gems": True
            },
            "march_assignment": {
                "enabled": True,
                "unlocked_queues": 2,
                "auto_gather_queues": 1,
                "rally_queues": 1
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                for module_key, module_defaults in default_settings.items():
                    if module_key not in settings:
                        settings[module_key] = module_defaults.copy()
                    else:
                        for setting_key, default_value in module_defaults.items():
                            if setting_key not in settings[module_key]:
                                settings[module_key][setting_key] = default_value
                
                return settings
                
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save settings"""
        try:
            # AutoStart
            if hasattr(self, 'autostart_enabled_var'):
                self.settings["autostart_game"] = {
                    "enabled": self.autostart_enabled_var.get(),
                    "auto_startup": self.auto_startup_var.get(),
                    "max_retries": int(self.max_retries_var.get()),
                    "retry_delay": int(self.retry_delay_var.get())
                }
            
            # AutoGather
            if hasattr(self, 'gather_enabled_var'):
                resource_types = []
                for resource_id, var in self.resource_vars.items():
                    if var.get():
                        resource_types.append(resource_id)
                
                self.settings["auto_gather"] = {
                    "enabled": self.gather_enabled_var.get(),
                    "check_interval": 30,
                    "resource_types": resource_types,
                    "max_concurrent_gathers": 5
                }
            
            # AutoTrain
            if hasattr(self, 'train_enabled_var'):
                self.settings["auto_train"] = {
                    "enabled": self.train_enabled_var.get(),
                    "check_interval": 60,
                    "training_priority": ["infantry", "ranged", "cavalry", "siege"],
                    "max_training_queues": 4,
                    "min_resource_threshold": 50000
                }
            
            # AutoMail
            if hasattr(self, 'mail_enabled_var'):
                self.settings["auto_mail"] = {
                    "enabled": self.mail_enabled_var.get(),
                    "check_interval": 120,
                    "claim_resources": True,
                    "claim_items": True,
                    "claim_speedups": True,
                    "claim_gems": True,
                    "delete_read_mail": False
                }
            
            # March Assignment
            if hasattr(self, 'unlocked_queues_var'):
                self.settings["march_assignment"] = {
                    "enabled": True,
                    "unlocked_queues": int(self.unlocked_queues_var.get()),
                    "auto_gather_queues": 1,
                    "rally_queues": 1,
                    "manual_queues": 0
                }
            
            # Save to file
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            # Show success
            self.status_label.configure(text="✅ Settings saved successfully!", fg="#4caf50")
            self.window.after(3000, lambda: self.status_label.configure(text=""))
            
            # Notify app
            if self.app_ref:
                self.app_ref.add_console_message(f"✅ Saved King Shot module settings for {self.instance_name}")
                
                if hasattr(self.app_ref, 'module_manager'):
                    self.app_ref.module_manager.reload_instance_settings(self.instance_name)
            
            print(f"Settings saved for {self.instance_name}")
            
        except Exception as e:
            error_msg = f"❌ Error saving: {str(e)}"
            self.status_label.configure(text=error_msg, fg="#f44336")
            print(f"Save error: {e}")
    
    def _close_window(self):
        """Close window"""
        self.window.destroy()


# Convenience functions
def show_king_shot_module_settings(parent, instance_name, app_ref=None):
    """Show the King Shot module settings window"""
    try:
        window = KingShotModuleSettings(parent, instance_name, app_ref)
        return window
    except Exception as e:
        messagebox.showerror("Error", f"Could not open King Shot module settings: {str(e)}")
        return None


# Legacy compatibility
def show_modules_window(parent, instance_name, app_ref=None):
    """Legacy function name"""
    return show_king_shot_module_settings(parent, instance_name, app_ref)


# Exports
__all__ = [
    'KingShotModuleSettings',
    'show_king_shot_module_settings', 
    'show_modules_window'
]