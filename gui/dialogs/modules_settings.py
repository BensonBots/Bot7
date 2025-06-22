"""
BENSON v2.0 - FIXED King Shot Module Settings Window
Clean sidebar layout with proper module controls for King Shot
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class KingShotModuleSettings:
    """Fixed module settings window designed for King Shot"""
    
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
        self._setup_sidebar()
        self._setup_content_area()
        self._setup_footer()
        
        # Load initial module
        self._show_module_settings("autostart_game")
    
    def _create_window(self):
        """Create the main settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"King Shot Modules - {self.instance_name}")
        self.window.geometry("1000x700")
        self.window.configure(bg="#1e2329")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500)
        y = (self.window.winfo_screenheight() // 2) - (350)
        self.window.geometry(f"1000x700+{x}+{y}")
        
        # Main container
        self.main_frame = tk.Frame(self.window, bg="#1e2329")
        self.main_frame.pack(fill="both", expand=True)
        
        # Header
        self._setup_header()
    
    def _setup_header(self):
        """Setup header section"""
        header = tk.Frame(self.main_frame, bg="#2d3442", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header, bg="#2d3442")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Title with game icon
        title_frame = tk.Frame(header_content, bg="#2d3442")
        title_frame.pack(side="left")
        
        tk.Label(
            title_frame,
            text="🎯 King Shot Automation",
            bg="#2d3442",
            fg="#ffffff",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")
        
        tk.Label(
            title_frame,
            text=f"Instance: {self.instance_name}",
            bg="#2d3442",
            fg="#00d4ff",
            font=("Segoe UI", 12)
        ).pack(side="left", padx=(20, 0))
        
        # Instance status
        if self.app_ref:
            instance = self.app_ref.instance_manager.get_instance(self.instance_name)
            status = instance["status"] if instance else "Unknown"
            status_colors = {
                "Running": "#00ff88",
                "Stopped": "#8b949e",
                "Starting": "#ffd93d",
                "Stopping": "#ff9800"
            }
            status_color = status_colors.get(status, "#8b949e")
            
            tk.Label(
                header_content,
                text=f"● {status}",
                bg="#2d3442",
                fg=status_color,
                font=("Segoe UI", 12, "bold")
            ).pack(side="right")
        
        # Close button
        close_btn = tk.Button(
            header_content,
            text="×",
            bg="#2d3442",
            fg="#ff6b6b",
            relief="flat",
            bd=0,
            font=("Segoe UI", 16, "bold"),
            cursor="hand2",
            width=3,
            command=self._close_window
        )
        close_btn.pack(side="right", padx=(10, 0))
        
        # Hover effects for close button
        def on_enter(e): close_btn.configure(bg="#ff4444", fg="#ffffff")
        def on_leave(e): close_btn.configure(bg="#2d3442", fg="#ff6b6b")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)
    


    def _setup_sidebar(self):
        """Setup left sidebar with module list and scrolling, true horizontal split"""
        # Only create the container if not already created
        if not hasattr(self, 'content_container'):
            self.content_container = tk.Frame(self.main_frame, bg="#1e2329")
            self.content_container.pack(fill="both", expand=True)

        # Sidebar (with scroll)
        sidebar_outer = tk.Frame(self.content_container, bg="#161b22", width=280)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        # Scrollbar for sidebar
        sidebar_scrollbar = tk.Scrollbar(sidebar_outer, orient="vertical")
        sidebar_scrollbar.pack(side="right", fill="y")

        # Scrollable canvas for sidebar
        sidebar_canvas = tk.Canvas(sidebar_outer, bg="#161b22", highlightthickness=0, yscrollcommand=sidebar_scrollbar.set)
        sidebar_canvas.pack(side="left", fill="both", expand=True)

        sidebar_scrollbar.config(command=sidebar_canvas.yview)

        # Frame inside canvas
        self.sidebar = tk.Frame(sidebar_canvas, bg="#161b22")
        sidebar_window = sidebar_canvas.create_window((0,0), window=self.sidebar, anchor="nw")

        def _on_sidebar_configure(event):
            sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        self.sidebar.bind("<Configure>", _on_sidebar_configure)

        def _on_sidebar_resize(event):
            sidebar_canvas.itemconfig(sidebar_window, width=sidebar_outer.winfo_width())
        sidebar_canvas.bind("<Configure>", _on_sidebar_resize)

        # Sidebar header
        sidebar_header = tk.Frame(self.sidebar, bg="#0d1117", height=50)
        sidebar_header.pack(fill="x")
        sidebar_header.pack_propagate(False)

        tk.Label(
            sidebar_header,
            text="🔧 Game Modules",
            bg="#0d1117",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=15)

        # Module list
        self._create_module_list()
        def _on_sidebar_configure(event):
            sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        self.sidebar.bind("<Configure>", _on_sidebar_configure)

        def _on_sidebar_resize(event):
            sidebar_canvas.itemconfig(sidebar_window, width=sidebar_outer.winfo_width())
        sidebar_canvas.bind("<Configure>", _on_sidebar_resize)

        # Sidebar header
        sidebar_header = tk.Frame(self.sidebar, bg="#0d1117", height=50)
        sidebar_header.pack(fill="x")
        sidebar_header.pack_propagate(False)

        tk.Label(
            sidebar_header,
            text="🔧 Game Modules",
            bg="#0d1117",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=15)

        # Module list
        self._create_module_list()


    def _create_module_list(self):
        """Create the module selection list using only implemented modules"""
        self.modules = [
            {
                "id": "autostart_game",
                "name": "AutoStart Game",
                "icon": "🎮",
                "description": "Automatically starts King Shot",
                "required": True
            },
            {
                "id": "auto_collect",
                "name": "AutoCollect",
                "icon": "💎",
                "description": "Collect rewards and items",
                "required": False
            },
            {
                "id": "auto_gather",
                "name": "AutoGather",
                "icon": "⛏️",
                "description": "Automatically gather resources",
                "required": False
            },
            {
                "id": "auto_train",
                "name": "AutoTrain",
                "icon": "🏋️",
                "description": "Automate troop training",
                "required": False
            }
        ]
        # Create module cards
        self.module_cards = {}
        for module in self.modules:
            self._create_module_card(module)
    def _create_module_card(self, module):
        """Create a module selection card"""
        module_id = module["id"]
        is_enabled = self.settings.get(module_id, {}).get("enabled", not module.get("status"))
        is_coming_soon = module.get("status") == "Coming Soon"
        
        # Card frame
        card = tk.Frame(self.sidebar, bg="#21262d", relief="solid", bd=1)
        card.pack(fill="x", pady=2)
        
        # Card content
        content = tk.Frame(card, bg="#21262d")
        content.pack(fill="x", padx=15, pady=12)
        
        # Top row - icon, name, and enable/disable
        top_row = tk.Frame(content, bg="#21262d")
        top_row.pack(fill="x")
        
        # Icon and name
        name_frame = tk.Frame(top_row, bg="#21262d")
        name_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            name_frame,
            text=f"{module['icon']} {module['name']}",
            bg="#21262d",
            fg="#ffffff" if not is_coming_soon else "#8b949e",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(side="left")
        
        if is_coming_soon:
            tk.Label(
                name_frame,
                text="Coming Soon",
                bg="#21262d",
                fg="#ffd93d",
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            ).pack(side="left", padx=(10, 0))
        
        # Enable/disable controls
        control_frame = tk.Frame(top_row, bg="#21262d")
        control_frame.pack(side="right")
        
        if not is_coming_soon:
            # Enable/disable toggle
            enabled_var = tk.BooleanVar(value=is_enabled)
            
            def toggle_module():
                new_state = enabled_var.get()
                self.settings[module_id]["enabled"] = new_state
                self._update_card_appearance(card, module_id, new_state)
            
            if module.get("required"):
                # Required modules show status only
                tk.Label(
                    control_frame,
                    text="● Required",
                    bg="#21262d",
                    fg="#00ff88",
                    font=("Segoe UI", 9, "bold")
                ).pack(side="right")
            else:
                # Optional modules get toggle switch
                toggle_btn = tk.Checkbutton(
                    control_frame,
                    variable=enabled_var,
                    bg="#21262d",
                    fg="#ffffff",
                    selectcolor="#00d4ff",
                    activebackground="#21262d",
                    activeforeground="#ffffff",
                    cursor="hand2",
                    command=toggle_module
                )
                toggle_btn.pack(side="right")
        
        # Description
        tk.Label(
            content,
            text=module["description"],
            bg="#21262d",
            fg="#8b949e",
            font=("Segoe UI", 10),
            anchor="w"
        ).pack(fill="x", pady=(5, 0))
        
        # Click to configure
        if not is_coming_soon:
            def on_click(event):
                self._show_module_settings(module_id)
            
            # Make entire card clickable
            for widget in [card, content, name_frame]:
                widget.bind("<Button-1>", on_click)
                widget.bind("<Enter>", lambda e: card.configure(bg="#2d3440"))
                widget.bind("<Leave>", lambda e: self._update_card_appearance(card, module_id, is_enabled))
        
        self.module_cards[module_id] = card
        self._update_card_appearance(card, module_id, is_enabled)
    
    def _update_card_appearance(self, card, module_id, is_enabled):
        """Update card appearance based on state"""
        if module_id == self.current_module:
            card.configure(bg="#00d4ff")
        elif is_enabled:
            card.configure(bg="#21262d")
        else:
            card.configure(bg="#1c2128")
    

    def _setup_content_area(self):
        """Setup right content area, as sibling to sidebar in content_container"""
        # Content area (right pane)
        self.content_area = tk.Frame(self.content_container, bg="#1e2329")
        self.content_area.pack(side="left", fill="both", expand=True)

        # Content header
        self.content_header = tk.Frame(self.content_area, bg="#1e2329", height=60)
        self.content_header.pack(fill="x", padx=20, pady=(20, 0))
        self.content_header.pack_propagate(False)

        # Content body (scrollable)
        self._setup_scrollable_content()
    def _setup_scrollable_content(self):
        """Setup scrollable content area"""
        # Create canvas and scrollbar
        canvas_frame = tk.Frame(self.content_area, bg="#1e2329")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.content_canvas = tk.Canvas(canvas_frame, bg="#1e2329", highlightthickness=0)
        content_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.content_canvas.yview)
        
        self.content_canvas.configure(yscrollcommand=content_scrollbar.set)
        
        # Pack canvas and scrollbar
        self.content_canvas.pack(side="left", fill="both", expand=True)
        content_scrollbar.pack(side="right", fill="y")
        
        # Scrollable frame
        self.content_frame = tk.Frame(self.content_canvas, bg="#1e2329")
        self.content_window = self.content_canvas.create_window(0, 0, anchor="nw", window=self.content_frame)
        
        # Bind scroll events
        def configure_scroll_region(event):
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        
        def configure_canvas_width(event):
            canvas_width = self.content_canvas.winfo_width()
            self.content_canvas.itemconfig(self.content_window, width=canvas_width)
        
        self.content_frame.bind("<Configure>", configure_scroll_region)
        self.content_canvas.bind("<Configure>", configure_canvas_width)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.content_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.content_frame.bind("<MouseWheel>", _on_mousewheel)
    
    def _show_module_settings(self, module_id):
        """Show settings for specific module"""
        # Update selection
        old_module = self.current_module
        self.current_module = module_id
        
        # Update card appearances
        if old_module in self.module_cards:
            old_enabled = self.settings.get(old_module, {}).get("enabled", True)
            self._update_card_appearance(self.module_cards[old_module], old_module, old_enabled)
        
        if module_id in self.module_cards:
            current_enabled = self.settings.get(module_id, {}).get("enabled", True)
            self._update_card_appearance(self.module_cards[module_id], module_id, current_enabled)
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update header
        for widget in self.content_header.winfo_children():
            widget.destroy()
        
        module_info = next((m for m in self.modules if m["id"] == module_id), None)
        if module_info:
            tk.Label(
                self.content_header,
                text=f"{module_info['icon']} {module_info['name']} Configuration",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 16, "bold")
            ).pack(side="left", pady=20)
        

        # Show specific module settings
        if module_id == "autostart_game":
            self._show_autostart_settings()
        elif module_id == "auto_collect":
            self._show_collect_settings()
        elif module_id == "auto_gather":
            self._show_gather_settings()
        elif module_id == "auto_train":
            self._show_train_settings()
        else:
            self._show_coming_soon()
        if module_id == "autostart_game":
            self._show_autostart_settings()
        elif module_id == "auto_collect":
            self._show_collect_settings()
        else:
            self._show_coming_soon()
    
    def _show_autostart_settings(self):
        """Show AutoStart game settings"""
        settings = self.settings.get("autostart_game", {})
        
        # Info section
        info_frame = self._create_section("Game Detection", "🎯")
        
        tk.Label(
            info_frame,
            text="Automatically detects and starts King Shot when MEmu instance becomes running.",
            bg="#161b22",
            fg="#ffffff",
            font=("Segoe UI", 11),
            wraplength=500,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        tk.Label(
            info_frame,
            text="• Handles ads and pop-ups automatically\n• Detects main menu and battle screens\n• Retries on failure with configurable delays",
            bg="#161b22",
            fg="#8b949e",
            font=("Segoe UI", 10),
            justify="left"
        ).pack(anchor="w")
        
        # Auto-startup setting
        startup_frame = self._create_section("Auto-Startup Configuration", "🚀")
        
        self.auto_startup_var = tk.BooleanVar(value=settings.get("auto_startup", False))
        startup_check = tk.Checkbutton(
            startup_frame,
            text="🎮 Auto-start when instance becomes running",
            variable=self.auto_startup_var,
            bg="#161b22",
            fg="#ffffff",
            selectcolor="#161b22",
            activebackground="#161b22",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        startup_check.pack(anchor="w", pady=5)
        
        # Retry settings
        retry_frame = self._create_section("Retry Configuration", "🔄")
        
        # Max retries
        retry_row1 = tk.Frame(retry_frame, bg="#161b22")
        retry_row1.pack(fill="x", pady=5)
        
        tk.Label(retry_row1, text="Maximum retry attempts:", 
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 11)).pack(side="left")
        
        self.max_retries_var = tk.StringVar(value=str(settings.get("max_retries", 3)))
        retry_spin = tk.Spinbox(
            retry_row1,
            from_=1, to=10,
            textvariable=self.max_retries_var,
            bg="#0a0e16", fg="#ffffff",
            width=5, font=("Segoe UI", 11)
        )
        retry_spin.pack(side="left", padx=(10, 0))
        
        # Retry delay
        retry_row2 = tk.Frame(retry_frame, bg="#161b22")
        retry_row2.pack(fill="x", pady=5)
        
        tk.Label(retry_row2, text="Delay between retries (seconds):", 
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 11)).pack(side="left")
        
        self.retry_delay_var = tk.StringVar(value=str(settings.get("retry_delay", 10)))
        delay_spin = tk.Spinbox(
            retry_row2,
            from_=5, to=60,
            textvariable=self.retry_delay_var,
            bg="#0a0e16", fg="#ffffff",
            width=5, font=("Segoe UI", 11)
        )
        delay_spin.pack(side="left", padx=(10, 0))
    
    def _show_collect_settings(self):
        """Show auto-collect settings for King Shot"""
        settings = self.settings.get("auto_collect", {})
        
        # Info section
        info_frame = self._create_section("Reward Collection", "💎")
        
        tk.Label(
            info_frame,
            text="Automatically collects rewards from various sources in King Shot including daily bonuses, achievement rewards, and battle completion rewards.",
            bg="#161b22",
            fg="#ffffff",
            font=("Segoe UI", 11),
            wraplength=500,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        # Enable/disable
        enable_frame = self._create_section("Module Control", "⚙️")
        self.collect_enabled_var = tk.BooleanVar(value=settings.get("enabled", True))
        tk.Checkbutton(
            enable_frame,
            text="💎 Enable AutoCollect module",
            variable=self.collect_enabled_var,
            bg="#161b22", fg="#ffffff",
            selectcolor="#161b22",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        
        # Collection types
        collect_frame = self._create_section("Collection Types", "🎁")
        
        tk.Label(
            collect_frame,
            text="Automatically collect these reward types:",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(0, 10))
        
        self.collect_vars = {}
        collect_types = [
            ("daily_rewards", "📅 Daily Login Rewards", "#ffeb3b"),
            ("battle_rewards", "⚔️ Battle Completion Rewards", "#ff6b6b"),
            ("achievement_rewards", "🏆 Achievement Rewards", "#9c27b0"),
            ("mailbox_items", "📬 Mailbox Items", "#00bcd4"),
            ("free_chests", "📦 Free Chests", "#4caf50"),
            ("ad_rewards", "📺 Advertisement Rewards", "#ff9800")
        ]
        
        for collect_id, collect_name, color in collect_types:
            var = tk.BooleanVar(value=settings.get(collect_id, True))
            self.collect_vars[collect_id] = var
            
            tk.Checkbutton(
                collect_frame,
                text=collect_name,
                variable=var,
                bg="#161b22", fg=color,
                selectcolor="#161b22",
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=3)
        
        # Collection interval
        interval_frame = self._create_section("Collection Settings", "⏰")
        
        interval_row = tk.Frame(interval_frame, bg="#161b22")
        interval_row.pack(fill="x", pady=5)
        
        tk.Label(interval_row, text="Check interval (seconds):",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 11)).pack(side="left")
        
        self.collect_interval_var = tk.StringVar(value=str(settings.get("check_interval", 60)))
        tk.Spinbox(
            interval_row,
            from_=30, to=300,
            textvariable=self.collect_interval_var,
            bg="#0a0e16", fg="#ffffff",
            width=8, font=("Segoe UI", 11)
        ).pack(side="left", padx=(10, 0))
        
        # Auto-watch ads setting
        auto_ads_row = tk.Frame(interval_frame, bg="#161b22")
        auto_ads_row.pack(fill="x", pady=(15, 5))
        
        self.auto_ads_var = tk.BooleanVar(value=settings.get("auto_watch_ads", False))
        tk.Checkbutton(
            auto_ads_row,
            text="📺 Automatically watch ads for rewards (use with caution)",
            variable=self.auto_ads_var,
            bg="#161b22", fg="#ff9800",
            selectcolor="#161b22",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
    
    def _show_coming_soon(self):
        """Show coming soon message"""
        coming_frame = self._create_section("Coming Soon", "🚧")
        
        tk.Label(
            coming_frame,
            text="This module is currently under development and will be available in a future update.",
            bg="#161b22",
            fg="#8b949e",
            font=("Segoe UI", 12),
            wraplength=500,
            justify="center"
        ).pack(pady=50)
        
        tk.Label(
            coming_frame,
            text="Stay tuned for more King Shot automation features!",
            bg="#161b22",
            fg="#ffd93d",
            font=("Segoe UI", 11, "bold")
        ).pack()
    
    def _create_section(self, title, icon):
        """Create a settings section with header"""
        # Section container
        section = tk.Frame(self.content_frame, bg="#161b22", relief="solid", bd=1)
        section.pack(fill="x", pady=(0, 15))
        
        # Section header
        header = tk.Frame(section, bg="#21262d", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{icon} {title}",
            bg="#21262d", fg="#ffffff",
            font=("Segoe UI", 13, "bold")
        ).pack(side="left", padx=20, pady=10)
        
        # Section content
        content = tk.Frame(section, bg="#161b22")
        content.pack(fill="x", padx=20, pady=15)
        
        return content
    
    def _setup_footer(self):
        """Setup footer with save/cancel buttons"""
        footer = tk.Frame(self.main_frame, bg="#2d3442", height=70)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_content = tk.Frame(footer, bg="#2d3442")
        footer_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Status label
        self.status_label = tk.Label(
            footer_content,
            text="",
            bg="#2d3442", fg="#8b949e",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(side="left")
        
        # Buttons
        btn_frame = tk.Frame(footer_content, bg="#2d3442")
        btn_frame.pack(side="right")
        
        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="❌ Cancel",
            bg="#ff6b6b", fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0,
            padx=20, pady=10,
            cursor="hand2",
            command=self._close_window
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Save button
        save_btn = tk.Button(
            btn_frame,
            text="💾 Save Settings",
            bg="#00ff88", fg="#000000", 
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0,
            padx=20, pady=10,
            cursor="hand2",
            command=self._save_settings
        )
        save_btn.pack(side="left")
        
        # Add hover effects
        self._add_button_hover_effects(cancel_btn, "#ff6b6b", "#ff8888")
        self._add_button_hover_effects(save_btn, "#00ff88", "#00ff99")
    
    def _add_button_hover_effects(self, button, normal_color, hover_color):
        """Add hover effects to button"""
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _load_settings(self):
        """Load settings from file"""
        default_settings = {
            "autostart_game": {
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10,
                "enabled": True
            },
            "auto_collect": {
                "enabled": True,
                "check_interval": 60,
                "daily_rewards": True,
                "battle_rewards": True,
                "achievement_rewards": True,
                "mailbox_items": True,
                "free_chests": True,
                "ad_rewards": False,
                "auto_watch_ads": False
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Merge with defaults
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save all settings"""
        try:
            # Collect AutoStart settings
            if hasattr(self, 'auto_startup_var'):
                self.settings["autostart_game"] = {
                    "auto_startup": self.auto_startup_var.get(),
                    "max_retries": int(self.max_retries_var.get()),
                    "retry_delay": int(self.retry_delay_var.get()),
                    "enabled": True
                }
            
            # Collect AutoCollect settings
            if hasattr(self, 'collect_enabled_var'):
                collect_settings = {
                    "enabled": self.collect_enabled_var.get(),
                    "check_interval": int(self.collect_interval_var.get()),
                    "auto_watch_ads": self.auto_ads_var.get()
                }
                
                # Add collection type settings
                for collect_type, var in self.collect_vars.items():
                    collect_settings[collect_type] = var.get()
                
                self.settings["auto_collect"] = collect_settings
            
            # Save to file
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            # Notify app
            if self.app_ref:
                self.app_ref.add_console_message(f"✅ Saved King Shot module settings for {self.instance_name}")
                
                # Reload settings in module manager
                if hasattr(self.app_ref, 'module_manager'):
                    self.app_ref.module_manager.reload_instance_settings(self.instance_name)
            
            self.status_label.configure(text="✅ Settings saved successfully", fg="#00ff88")
            self.window.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            error_msg = f"❌ Error saving: {str(e)}"
            self.status_label.configure(text=error_msg, fg="#ff6b6b")
            print(error_msg)
    
    def _close_window(self):
        """Close the window"""
        self.window.destroy()


def show_king_shot_module_settings(parent, instance_name, app_ref=None):
    """Show the King Shot module settings window"""
    try:
        window = KingShotModuleSettings(parent, instance_name, app_ref)
        return window
    except Exception as e:
        messagebox.showerror("Error", f"Could not open King Shot module settings: {str(e)}")
        return None

