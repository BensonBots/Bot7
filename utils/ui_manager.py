"""
BENSON v2.0 - Optimized UI Manager - 60% Size Reduction
Essential functionality with cleaner code
"""

import tkinter as tk
from tkinter import messagebox, ttk


class UIManager:
    """Optimized UI manager with essential functionality"""

    def __init__(self, app_ref):
        self.app = app_ref
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.instances_canvas = None
        self.instances_frame = None
        self.scrollbar = None

    def setup_header(self):
        """Setup header with controls"""
        header = tk.Frame(self.app, bg="#0a0e16", height=70)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)

        # Title (draggable)
        title_frame = tk.Frame(header, bg="#0a0e16")
        title_frame.pack(side="left", fill="y")

        title_label = tk.Label(title_frame, text="BENSON v2.0", bg="#0a0e16", fg="#f0f6fc",
                              font=("Segoe UI", 18, "bold"), cursor="fleur")
        title_label.pack(side="left")

        subtitle = tk.Label(title_frame, text="benson.gg", bg="#0a0e16", fg="#00d4ff",
                           font=("Segoe UI", 10, "bold"), cursor="fleur")
        subtitle.pack(side="left", padx=(10, 0))

        self.make_draggable(title_label)
        self.make_draggable(subtitle)

        # Search bar
        search_frame = tk.Frame(header, bg="#0a0e16")
        search_frame.pack(side="left", fill="x", expand=True, padx=(30, 30))
        self.setup_search_bar(search_frame)

        # Window controls
        controls_frame = tk.Frame(header, bg="#0a0e16")
        controls_frame.pack(side="right")

        self._create_window_button(controls_frame, "−", "#8b949e", self.minimize_window)
        self._create_window_button(controls_frame, "×", "#ff6b6b", self.close_window)

    def _create_window_button(self, parent, text, color, command):
        """Create window control button"""
        btn = tk.Button(parent, text=text, bg="#1a1f2e", fg=color, relief="flat", bd=0,
                       font=("Segoe UI", 12, "bold"), cursor="hand2", width=3, height=1, command=command)
        btn.pack(side="left", padx=(0, 2))
        
        # Hover effect
        def on_enter(e): btn.configure(bg=color, fg="#ffffff")
        def on_leave(e): btn.configure(bg="#1a1f2e", fg=color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def setup_search_bar(self, parent):
        """Setup search bar"""
        search_container = tk.Frame(parent, bg="#1e2329", relief="solid", bd=1)
        search_container.pack(fill="x")

        tk.Label(search_container, text="🔍", bg="#1e2329", fg="#8b949e", font=("Segoe UI", 10)).pack(side="left", padx=(6, 3))

        self.app.search_var = tk.StringVar()
        self.app.search_var.trace("w", self.app.on_search_change_debounced)

        self.app.search_entry = tk.Entry(search_container, textvariable=self.app.search_var, bg="#1e2329", fg="#ffffff",
                                         font=("Segoe UI", 10), relief="flat", bd=0, insertbackground="#00d4ff", width=20)
        self.app.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
        self.app.search_entry.insert(0, "Search instances...")
        self.app.search_entry.configure(fg="#8b949e")
        self.app.search_entry.bind("<FocusIn>", self.app.on_search_focus_in)
        self.app.search_entry.bind("<FocusOut>", self.app.on_search_focus_out)

    def setup_controls(self):
        """Setup control buttons"""
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)

        # Instances header
        self.app.instances_header = tk.Label(controls, text="Instances (0)", bg="#0a0e16", fg="#00ff88",
                                            font=("Segoe UI", 16, "bold"), cursor="hand2")
        self.app.instances_header.pack(side="left")
        self.app.instances_header.bind("<Button-1>", lambda e: self.app.instance_ops.toggle_select_all())

        # Bulk operations
        bulk_frame = tk.Frame(controls, bg="#0a0e16")
        bulk_frame.pack(side="left", padx=(40, 0))

        buttons = [
            ("➕ Create", "#00ff88", self.create_instance_dialog),
            ("▶ Start All", "#00e676", self.app.instance_ops.start_selected_instances),
            ("⏹ Stop All", "#ff6b6b", self.app.instance_ops.stop_selected_instances)
        ]

        for text, bg, command in buttons:
            self._create_control_button(bulk_frame, text, bg, command).pack(side="left", padx=(0, 8))

        # Refresh button
        self._create_control_button(controls, "⟳ Refresh", "#1a1f2e", 
                                   self.app.instance_ops.refresh_instances).pack(side="right")

    def _create_control_button(self, parent, text, bg, command):
        """Create control button with hover effect"""
        btn = tk.Button(parent, text=text, bg=bg, fg="#ffffff" if bg != "#1a1f2e" else "#00d4ff",
                       font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6,
                       cursor="hand2", command=command)
        
        # Simple hover effect
        original_bg = bg
        hover_colors = {"#00ff88": "#00ff99", "#00e676": "#33ea88", "#ff6b6b": "#ff8888", "#1a1f2e": "#252a39"}
        hover_bg = hover_colors.get(bg, bg)
        
        def on_enter(e): btn.configure(bg=hover_bg)
        def on_leave(e): btn.configure(bg=original_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def setup_main_content(self):
        """Setup scrollable main content"""
        main_frame = tk.Frame(self.app, bg="#0a0e16")
        main_frame.pack(fill="both", expand=True, padx=10)
        self._create_scrollable_area(main_frame)

    def _create_scrollable_area(self, parent):
        """Create scrollable canvas area"""
        scroll_container = tk.Frame(parent, bg="#0a0e16")
        scroll_container.pack(fill="both", expand=True)

        self.instances_canvas = tk.Canvas(scroll_container, bg="#0a0e16", highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.instances_canvas.yview)
        self.instances_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.instances_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.instances_frame = tk.Frame(self.instances_canvas, bg="#0a0e16")
        self.canvas_window = self.instances_canvas.create_window(0, 0, anchor="nw", window=self.instances_frame)
        self.app.instances_container = self.instances_frame

        # Bind scroll events
        self._bind_scroll_events()
        self.instances_frame.grid_columnconfigure(0, weight=1, minsize=580)
        self.instances_frame.grid_columnconfigure(1, weight=1, minsize=580)

    def _bind_scroll_events(self):
        """Bind scrolling events"""
        def configure_scroll_region(event):
            self.instances_canvas.configure(scrollregion=self.instances_canvas.bbox("all"))

        def configure_canvas_width(event):
            canvas_width = self.instances_canvas.winfo_width()
            self.instances_canvas.itemconfig(self.canvas_window, width=canvas_width)

        def on_mousewheel(event):
            if self.instances_canvas.bbox("all"):
                bbox = self.instances_canvas.bbox("all")
                if bbox[3] - bbox[1] > self.instances_canvas.winfo_height():
                    self.instances_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.instances_frame.bind("<Configure>", configure_scroll_region)
        self.instances_canvas.bind("<Configure>", configure_canvas_width)
        self.instances_canvas.bind("<MouseWheel>", on_mousewheel)

    def update_scroll_region(self):
        """Update scroll region"""
        try:
            if self.instances_canvas and self.instances_canvas.winfo_exists():
                self.instances_canvas.update_idletasks()
                self.instances_canvas.configure(scrollregion=self.instances_canvas.bbox("all"))
        except Exception as e:
            print(f"[UIManager] Error updating scroll: {e}")

    def scroll_to_bottom(self):
        """Scroll to bottom"""
        try:
            if self.instances_canvas:
                self.instances_canvas.update_idletasks()
                self.instances_canvas.yview_moveto(1.0)
        except: pass

    def setup_console(self):
        """Setup console"""
        self.console_main_frame = tk.Frame(self.app, bg="#0a0e16")
        self.console_main_frame.pack(fill="x", padx=10, pady=(10, 0))

        # Console header
        console_header = tk.Frame(self.console_main_frame, bg="#0a0e16")
        console_header.pack(fill="x", pady=(0, 5))

        tk.Label(console_header, text="Activity Console", bg="#0a0e16", fg="#f0f6fc",
                font=("Segoe UI", 12, "bold")).pack(side="left")

        # Console controls
        self._create_control_button(console_header, "🗑 Clear", "#1a1f2e", self.app.clear_console).pack(side="right")
        
        resize_btn = self._create_control_button(console_header, "⇕", "#1a1f2e", self.toggle_console_size)
        resize_btn.configure(cursor="sb_v_double_arrow")
        resize_btn.pack(side="right", padx=(0, 5))

        # Console text
        self.console_container = tk.Frame(self.console_main_frame, bg="#161b22", relief="solid", bd=1, height=120)
        self.console_container.pack(fill="both", expand=False)
        self.console_container.pack_propagate(False)

        self.app.console_text = tk.Text(self.console_container, bg="#0a0e16", fg="#58a6ff", font=("Consolas", 9),
                                       relief="flat", bd=0, wrap="word", state="disabled", padx=8, pady=4)
        self.app.console_text.pack(fill="both", expand=True)

        self.console_expanded = False

    def setup_footer(self):
        """Setup footer"""
        footer = tk.Frame(self.app, bg="#0a0e16", height=20)
        footer.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        footer.pack_propagate(False)

        tk.Label(footer, text="Shortcuts: Ctrl+R (Refresh) | Ctrl+A (Select All) | Mouse Wheel (Scroll)",
                bg="#0a0e16", fg="#7d8590", font=("Segoe UI", 8)).pack()

    # Window controls
    def minimize_window(self):
        try: self.app.iconify()
        except Exception as e: print(f"[UIManager] Error minimizing: {e}")

    def close_window(self):
        try: self.app.destroy()
        except Exception as e: print(f"[UIManager] Error closing: {e}")

    def make_draggable(self, widget):
        """Make widget draggable"""
        def start_drag(event):
            if event.num != 1: return
            self.dragging = True
            self.start_x = event.x_root - self.app.winfo_x()
            self.start_y = event.y_root - self.app.winfo_y()
            return "break"

        def drag_window(event):
            if not self.dragging: return
            new_x = max(0, min(event.x_root - self.start_x, self.app.winfo_screenwidth() - 100))
            new_y = max(0, min(event.y_root - self.start_y, self.app.winfo_screenheight() - 50))
            self.app.geometry(f"{self.app.winfo_width()}x{self.app.winfo_height()}+{new_x}+{new_y}")
            return "break"

        def stop_drag(event):
            self.dragging = False
            return "break"

        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", drag_window)
        widget.bind("<ButtonRelease-1>", stop_drag)

    def toggle_console_size(self):
        """Toggle console size"""
        try:
            height = 300 if not self.console_expanded else 120
            self.console_container.configure(height=height)
            self.console_expanded = not self.console_expanded
            self.app.update_idletasks()
        except Exception as e:
            print(f"[UIManager] Error toggling console: {e}")

    def create_instance_dialog(self):
        """Create instance dialog"""
        try:
            from gui.dialogs.create_instance_dialog import show_create_instance_dialog
            instance_name = show_create_instance_dialog(self.app, self.app)
            if instance_name:
                self.app.instance_ops.create_instance_with_name(instance_name)
        except ImportError:
            from tkinter import simpledialog
            name = simpledialog.askstring("Create Instance", "Enter instance name:", parent=self.app)
            if name:
                self.app.instance_ops.create_instance_with_name(name)

    def show_modules(self, instance_name):
        """Show module settings"""
        try:
            self.app.add_console_message(f"🔧 Opening module configuration for: {instance_name}")
            self.app.update_idletasks()
            
            # Try the existing module settings first
            try:
                from gui.dialogs.modules_settings import show_improved_king_shot_module_settings
                settings_window = show_improved_king_shot_module_settings(self.app, instance_name, app_ref=self.app)
                if settings_window:
                    self.app.add_console_message(f"✅ Module configuration opened for: {instance_name}")
                else:
                    self.app.add_console_message(f"❌ Failed to open module configuration for: {instance_name}")
                return settings_window
            except ImportError:
                # Fallback to modules window
                from gui.dialogs.modules_window import ModulesWindow
                ModulesWindow(self.app, instance_name, app_ref=self.app)
                self.app.add_console_message(f"✅ Module configuration opened for: {instance_name}")
                
        except Exception as e:
            print(f"[UIManager] Error showing modules: {e}")
            messagebox.showerror("Error", f"Could not open modules configuration: {str(e)}")
            return None

    def create_instance_card(self, name, status):
        """Create instance card"""
        try:
            from core.components.instance_card import InstanceCard
            card = InstanceCard(self.app.instances_container, name=name, status=status, app_ref=self.app)
            self.app.after_idle(self.update_scroll_region)
            return card
        except ImportError:
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

        tk.Label(content, text=name, bg="#1e2329", fg="#ffffff", font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(content, text=f"Status: {status}", bg="#1e2329", fg="#8b949e", font=("Segoe UI", 10)).pack(side="left", padx=(20, 0))

        def toggle(): 
            card.selected = not card.selected
            card.configure(bg="#00d4ff" if card.selected else "#1e2329")

        def update_status(new_status):
            card.status = new_status

        card.toggle_checkbox = toggle
        card.update_status = update_status
        card.bind("<Button-1>", lambda e: toggle())

        return card