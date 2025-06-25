"""
BENSON v2.0 - FIXED UI Manager - Compact Version
Reduced from 400+ lines to ~200 lines while maintaining all functionality
"""

import tkinter as tk
from tkinter import messagebox, ttk


class UIManager:
    """Compact UI manager with essential functionality"""

    def __init__(self, app_ref):
        self.app = app_ref
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.console_expanded = False

    def setup_header(self):
        """Setup header with title and search"""
        header = tk.Frame(self.app, bg="#0a0e16", height=70)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)

        # Draggable title
        self._create_title_section(header)
        
        # Search bar
        self._create_search_section(header)
        
        # Window controls
        self._create_window_controls(header)

    def _create_title_section(self, parent):
        """Create draggable title section"""
        title_frame = tk.Frame(parent, bg="#0a0e16")
        title_frame.pack(side="left", fill="y")

        title = tk.Label(title_frame, text="BENSON v2.0", bg="#0a0e16", fg="#f0f6fc",
                        font=("Segoe UI", 18, "bold"), cursor="fleur")
        title.pack(side="left")

        subtitle = tk.Label(title_frame, text="benson.gg", bg="#0a0e16", fg="#00d4ff",
                           font=("Segoe UI", 10, "bold"), cursor="fleur")
        subtitle.pack(side="left", padx=(10, 0))

        # Make draggable
        for widget in [title, subtitle]:
            self._make_draggable(widget)

    def _create_search_section(self, parent):
        """Create search bar section"""
        search_frame = tk.Frame(parent, bg="#0a0e16")
        search_frame.pack(side="left", fill="x", expand=True, padx=(30, 30))

        search_container = tk.Frame(search_frame, bg="#1e2329", relief="solid", bd=1)
        search_container.pack(fill="x")

        tk.Label(search_container, text="🔍", bg="#1e2329", fg="#8b949e", 
                font=("Segoe UI", 10)).pack(side="left", padx=(6, 3))

        self.app.search_var = tk.StringVar()
        self.app.search_var.trace("w", self.app.on_search_change_debounced)

        self.app.search_entry = tk.Entry(search_container, textvariable=self.app.search_var, 
                                         bg="#1e2329", fg="#ffffff", font=("Segoe UI", 10), 
                                         relief="flat", bd=0, insertbackground="#00d4ff", width=20)
        self.app.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
        self.app.search_entry.insert(0, "Search instances...")
        self.app.search_entry.configure(fg="#8b949e")
        self.app.search_entry.bind("<FocusIn>", self.app.on_search_focus_in)
        self.app.search_entry.bind("<FocusOut>", self.app.on_search_focus_out)

    def _create_window_controls(self, parent):
        """Create window control buttons"""
        controls_frame = tk.Frame(parent, bg="#0a0e16")
        controls_frame.pack(side="right")

        buttons = [("−", "#8b949e", self.minimize_window), ("×", "#ff6b6b", self.close_window)]
        for text, color, command in buttons:
            btn = tk.Button(controls_frame, text=text, bg="#1a1f2e", fg=color, relief="flat", bd=0,
                           font=("Segoe UI", 12, "bold"), cursor="hand2", width=3, height=1, command=command)
            btn.pack(side="left", padx=(0, 2))
            
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.configure(bg=c, fg="#ffffff"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg="#1a1f2e", fg=c))

    def setup_controls(self):
        """Setup control buttons"""
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)

        # Instance header (clickable for select all)
        self.app.instances_header = tk.Label(controls, text="Instances (0)", bg="#0a0e16", fg="#00ff88",
                                            font=("Segoe UI", 16, "bold"), cursor="hand2")
        self.app.instances_header.pack(side="left")
        self.app.instances_header.bind("<Button-1>", lambda e: self.app.instance_ops.toggle_select_all())

        # Control buttons
        self._create_control_buttons(controls)

    def _create_control_buttons(self, parent):
        """Create main control buttons"""
        # Left side buttons
        bulk_frame = tk.Frame(parent, bg="#0a0e16")
        bulk_frame.pack(side="left", padx=(40, 0))

        buttons = [
            ("➕ Create", "#00ff88", self.create_instance_dialog),
            ("▶ Start All", "#00e676", self.app.instance_ops.start_selected_instances),
            ("⏹ Stop All", "#ff6b6b", self.app.instance_ops.stop_selected_instances)
        ]

        for text, bg, command in buttons:
            btn = self._create_styled_button(bulk_frame, text, bg, command)
            btn.pack(side="left", padx=(0, 8))

        # Right side refresh button
        refresh_btn = self._create_styled_button(parent, "⟳ Refresh", "#1a1f2e", 
                                                 self.app.instance_ops.refresh_instances)
        refresh_btn.pack(side="right")

    def _create_styled_button(self, parent, text, bg, command):
        """Create styled button with hover effect"""
        fg = "#ffffff" if bg != "#1a1f2e" else "#00d4ff"
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), 
                       relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=command)
        
        # Hover colors
        hover_map = {"#00ff88": "#00ff99", "#00e676": "#33ea88", "#ff6b6b": "#ff8888", "#1a1f2e": "#252a39"}
        hover_bg = hover_map.get(bg, bg)
        
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        
        return btn

    def setup_main_content(self):
        """Setup scrollable main content area"""
        main_frame = tk.Frame(self.app, bg="#0a0e16")
        main_frame.pack(fill="both", expand=True, padx=10)
        
        # Create scrollable canvas
        scroll_container = tk.Frame(main_frame, bg="#0a0e16")
        scroll_container.pack(fill="both", expand=True)

        self.instances_canvas = tk.Canvas(scroll_container, bg="#0a0e16", highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.instances_canvas.yview)
        self.instances_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.instances_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create content frame
        self.instances_frame = tk.Frame(self.instances_canvas, bg="#0a0e16")
        self.canvas_window = self.instances_canvas.create_window(0, 0, anchor="nw", window=self.instances_frame)
        self.app.instances_container = self.instances_frame

        # Configure grid and bindings
        self.instances_frame.grid_columnconfigure(0, weight=1, minsize=580)
        self.instances_frame.grid_columnconfigure(1, weight=1, minsize=580)
        self._bind_scroll_events()

    def _bind_scroll_events(self):
        """Bind canvas scroll events"""
        def update_scroll_region(event):
            self.instances_canvas.configure(scrollregion=self.instances_canvas.bbox("all"))

        def update_canvas_width(event):
            canvas_width = self.instances_canvas.winfo_width()
            self.instances_canvas.itemconfig(self.canvas_window, width=canvas_width)

        def on_mousewheel(event):
            if self.instances_canvas.bbox("all"):
                bbox = self.instances_canvas.bbox("all")
                if bbox[3] - bbox[1] > self.instances_canvas.winfo_height():
                    self.instances_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.instances_frame.bind("<Configure>", update_scroll_region)
        self.instances_canvas.bind("<Configure>", update_canvas_width)
        self.instances_canvas.bind("<MouseWheel>", on_mousewheel)

    def setup_console(self):
        """Setup activity console"""
        self.console_main_frame = tk.Frame(self.app, bg="#0a0e16")
        self.console_main_frame.pack(fill="x", padx=10, pady=(10, 0))

        # Console header with controls
        header = tk.Frame(self.console_main_frame, bg="#0a0e16")
        header.pack(fill="x", pady=(0, 5))

        tk.Label(header, text="Activity Console", bg="#0a0e16", fg="#f0f6fc",
                font=("Segoe UI", 12, "bold")).pack(side="left")

        # Console controls
        resize_btn = self._create_styled_button(header, "⇕", "#1a1f2e", self.toggle_console_size)
        resize_btn.configure(cursor="sb_v_double_arrow")
        resize_btn.pack(side="right")
        
        clear_btn = self._create_styled_button(header, "🗑 Clear", "#1a1f2e", self.app.clear_console)
        clear_btn.pack(side="right", padx=(0, 5))

        # Console text area
        self.console_container = tk.Frame(self.console_main_frame, bg="#161b22", relief="solid", bd=1, height=120)
        self.console_container.pack(fill="both", expand=False)
        self.console_container.pack_propagate(False)

        self.app.console_text = tk.Text(self.console_container, bg="#0a0e16", fg="#58a6ff", 
                                       font=("Consolas", 9), relief="flat", bd=0, wrap="word", 
                                       state="disabled", padx=8, pady=4)
        self.app.console_text.pack(fill="both", expand=True)

    def setup_footer(self):
        """Setup footer with shortcuts"""
        footer = tk.Frame(self.app, bg="#0a0e16", height=20)
        footer.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        footer.pack_propagate(False)

        tk.Label(footer, text="Shortcuts: Ctrl+R (Refresh) | Ctrl+A (Select All) | Mouse Wheel (Scroll)",
                bg="#0a0e16", fg="#7d8590", font=("Segoe UI", 8)).pack()

    # Helper methods
    def update_scroll_region(self):
        """Update canvas scroll region"""
        try:
            if self.instances_canvas and self.instances_canvas.winfo_exists():
                self.instances_canvas.update_idletasks()
                self.instances_canvas.configure(scrollregion=self.instances_canvas.bbox("all"))
        except: pass

    def scroll_to_bottom(self):
        """Scroll canvas to bottom"""
        try:
            if self.instances_canvas:
                self.instances_canvas.update_idletasks()
                self.instances_canvas.yview_moveto(1.0)
        except: pass

    def toggle_console_size(self):
        """Toggle console between normal and expanded size"""
        try:
            height = 300 if not self.console_expanded else 120
            self.console_container.configure(height=height)
            self.console_expanded = not self.console_expanded
            self.app.update_idletasks()
        except Exception as e:
            print(f"[UIManager] Error toggling console: {e}")

    # Window controls
    def minimize_window(self):
        try: self.app.iconify()
        except: pass

    def close_window(self):
        try: self.app.destroy()
        except: pass

    def _make_draggable(self, widget):
        """Make widget draggable for window movement"""
        def start_drag(event):
            if event.num != 1: return
            self.dragging = True
            self.start_x = event.x_root - self.app.winfo_x()
            self.start_y = event.y_root - self.app.winfo_y()

        def drag_window(event):
            if not self.dragging: return
            new_x = max(0, min(event.x_root - self.start_x, self.app.winfo_screenwidth() - 100))
            new_y = max(0, min(event.y_root - self.start_y, self.app.winfo_screenheight() - 50))
            self.app.geometry(f"{self.app.winfo_width()}x{self.app.winfo_height()}+{new_x}+{new_y}")

        def stop_drag(event):
            self.dragging = False

        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", drag_window)
        widget.bind("<ButtonRelease-1>", stop_drag)

    # Dialog methods
    def create_instance_dialog(self):
        """Show create instance dialog"""
        try:
            from gui.dialogs.create_instance_dialog import show_create_instance_dialog
            instance_name = show_create_instance_dialog(self.app, self.app)
            if instance_name:
                self.app.instance_ops.create_instance_with_name(instance_name)
        except ImportError:
            # Fallback to simple dialog
            from tkinter import simpledialog
            name = simpledialog.askstring("Create Instance", "Enter instance name:", parent=self.app)
            if name:
                self.app.instance_ops.create_instance_with_name(name)

    def show_modules(self, instance_name):
        """Show module settings window"""
        try:
            self.app.add_console_message(f"🔧 Opening module configuration for: {instance_name}")
            self.app.update_idletasks()
            
            # Import and show modules_settings
            from gui.dialogs.modules_settings import show_slim_module_settings
            settings_window = show_slim_module_settings(self.app, instance_name, app_ref=self.app)
            
            if settings_window:
                self.app.add_console_message(f"✅ Module configuration opened for: {instance_name}")
                return settings_window
            else:
                self.app.add_console_message(f"❌ Failed to open module configuration for: {instance_name}")
                    
        except ImportError as e:
            print(f"[UIManager] modules_settings import failed: {e}")
            messagebox.showerror("Import Error", f"Could not import modules_settings: {str(e)}")
        except Exception as e:
            print(f"[UIManager] Error showing modules: {e}")
            messagebox.showerror("Error", f"Could not open modules: {str(e)}")
            return None

    def create_instance_card(self, name, status):
        """Create instance card widget"""
        try:
            # Try to import the proper instance card
            from core.components.instance_card import InstanceCard
            card = InstanceCard(self.app.instances_container, name=name, status=status, app_ref=self.app)
            self.app.after_idle(self.update_scroll_region)
            return card
        except ImportError:
            # Fallback to simple card
            return self._create_simple_card(name, status)

    def _create_simple_card(self, name, status):
        """Create simple fallback card"""
        card = tk.Frame(self.app.instances_container, bg="#1e2329", relief="solid", bd=1, width=580, height=85)
        card.pack_propagate(False)
        card.name = name
        card.status = status
        card.selected = False

        content = tk.Frame(card, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(content, text=name, bg="#1e2329", fg="#ffffff", 
                font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(content, text=f"Status: {status}", bg="#1e2329", fg="#8b949e", 
                font=("Segoe UI", 10)).pack(side="left", padx=(20, 0))

        def toggle(): 
            card.selected = not card.selected
            card.configure(bg="#00d4ff" if card.selected else "#1e2329")

        def update_status(new_status):
            card.status = new_status

        card.toggle_checkbox = toggle
        card.update_status = update_status
        card.bind("<Button-1>", lambda e: toggle())

        return card