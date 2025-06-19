"""
BENSON v2.0 - Enhanced UI Manager with Separate Dialog Integration
Safe window dragging without crashes and modern dialog system
"""

import tkinter as tk
from tkinter import messagebox


class UIManager:
    """Enhanced UI manager with safe draggable windows and modern dialogs"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
    
    def setup_header(self):
        """Setup header with safer custom window controls"""
        header = tk.Frame(self.app, bg="#0a0e16", height=70)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)
        
        # Left - Title section
        title_frame = tk.Frame(header, bg="#0a0e16")
        title_frame.pack(side="left", fill="y")
        
        title_label = tk.Label(
            title_frame,
            text="BENSON v2.0",
            bg="#0a0e16",
            fg="#f0f6fc",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(side="left")
        
        subtitle = tk.Label(
            title_frame,
            text="benson.gg",
            bg="#0a0e16",
            fg="#00d4ff",
            font=("Segoe UI", 10, "bold")
        )
        subtitle.pack(side="left", padx=(10, 0), pady=(2, 0))
        
        # Center - Smaller search bar
        search_frame = tk.Frame(header, bg="#0a0e16")
        search_frame.pack(side="left", fill="x", expand=True, padx=(30, 30))
        
        self.setup_search_bar(search_frame)
        
        # Right - Custom window controls
        controls_frame = tk.Frame(header, bg="#0a0e16")
        controls_frame.pack(side="right")
        
        # Minimize button
        minimize_btn = tk.Button(
            controls_frame,
            text="−",
            bg="#1a1f2e",
            fg="#8b949e",
            relief="flat",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            width=3,
            height=1,
            command=self.minimize_window
        )
        minimize_btn.pack(side="left", padx=(0, 2))
        
        # Close button
        close_btn = tk.Button(
            controls_frame,
            text="×",
            bg="#1a1f2e",
            fg="#ff6b6b",
            relief="flat",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            width=3,
            height=1,
            command=self.close_window
        )
        close_btn.pack(side="left")
        
        # SAFER: Only try to make draggable without overrideredirect for main window
        try:
            # Make window draggable but keep default controls as fallback
            self.make_draggable_safe(title_frame)
        except Exception as e:
            print(f"[UIManager] Could not setup dragging: {e}")
    
    def setup_search_bar(self, parent):
        """Setup smaller search bar"""
        search_container = tk.Frame(parent, bg="#1e2329", relief="solid", bd=1)
        search_container.pack(fill="x")
        
        # Search icon
        search_icon = tk.Label(
            search_container,
            text="🔍",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10)
        )
        search_icon.pack(side="left", padx=(6, 3))
        
        # Smaller search entry
        self.app.search_var = tk.StringVar()
        self.app.search_var.trace("w", self.app.on_search_change_debounced)
        
        self.app.search_entry = tk.Entry(
            search_container,
            textvariable=self.app.search_var,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            insertbackground="#00d4ff",
            width=20  # Smaller width
        )
        self.app.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
        self.app.search_entry.insert(0, "Search instances...")
        self.app.search_entry.configure(fg="#8b949e")
        self.app.search_entry.bind("<FocusIn>", self.app.on_search_focus_in)
        self.app.search_entry.bind("<FocusOut>", self.app.on_search_focus_out)
    
    def setup_controls(self):
        """Setup control section with enhanced buttons"""
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)
        
        # Left side - instances header
        left_frame = tk.Frame(controls, bg="#0a0e16")
        left_frame.pack(side="left")
        
        # Simple "Instances" header without count
        self.app.instances_header = tk.Label(
            left_frame,
            text="Instances",
            bg="#0a0e16",
            fg="#00ff88",
            font=("Segoe UI", 16, "bold"),
            cursor="hand2"
        )
        self.app.instances_header.pack(side="left")
        self.app.instances_header.bind("<Button-1>", lambda e: self.app.instance_ops.toggle_select_all())
        
        # Center - Enhanced bulk operations with hover effects
        bulk_frame = tk.Frame(controls, bg="#0a0e16")
        bulk_frame.pack(side="left", padx=(40, 0))
        
        buttons = [
            ("➕ Create", "#00ff88", "#000000", self.create_instance_with_enhanced_dialog),
            ("📋 Clone", "#00d4ff", "#000000", self.app.instance_ops.clone_selected_instance),
            ("▶ Start All", "#00e676", "#000000", self.app.instance_ops.start_selected_instances),
            ("⏹ Stop All", "#ff6b6b", "#ffffff", self.app.instance_ops.stop_selected_instances)
        ]
        
        for text, bg, fg, command in buttons:
            btn = self._create_enhanced_button(bulk_frame, text, bg, fg, command)
            btn.pack(side="left", padx=(0, 8))
        
        # Right side - enhanced refresh button
        refresh_btn = self._create_enhanced_button(
            controls, "⟳ Refresh", "#1a1f2e", "#00d4ff", 
            self.app.instance_ops.refresh_instances, side="right"
        )
        refresh_btn.pack(side="right")
    
    def _create_enhanced_button(self, parent, text, bg, fg, command, side=None):
        """Create a button with enhanced hover effects"""
        btn = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=command
        )
        
        # Add hover effects
        original_bg = bg
        hover_bg = self._get_hover_color(bg)
        
        def on_enter(e):
            btn.configure(bg=hover_bg, relief="raised", bd=1)
        
        def on_leave(e):
            btn.configure(bg=original_bg, relief="flat", bd=0)
        
        def on_click(e):
            btn.configure(bg=self._get_click_color(bg))
            btn.after(100, lambda: btn.configure(bg=original_bg))
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
        
        return btn
    
    def _get_hover_color(self, color):
        """Get hover color for a given color"""
        hover_map = {
            "#00ff88": "#00ff99",
            "#00d4ff": "#33ddff",
            "#00e676": "#33ea88",
            "#ff6b6b": "#ff8888",
            "#1a1f2e": "#252a39"
        }
        return hover_map.get(color, color)
    
    def _get_click_color(self, color):
        """Get click color for a given color"""
        click_map = {
            "#00ff88": "#00dd77",
            "#00d4ff": "#00aacc",
            "#00e676": "#00cc55",
            "#ff6b6b": "#ff4444",
            "#1a1f2e": "#0f141d"
        }
        return click_map.get(color, color)
    
    def setup_main_content(self):
        """Setup the main content area"""
        # Main content frame
        main_frame = tk.Frame(self.app, bg="#0a0e16")
        main_frame.pack(fill="both", expand=True, padx=10)
        
        # Create a container for instances
        self.app.instances_container = tk.Frame(main_frame, bg="#0a0e16")
        self.app.instances_container.pack(fill="both", expand=True)
        
        # Configure grid columns for 2-column layout with equal width
        self.app.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
        self.app.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
    
    def setup_console(self):
        """Setup resizable console section"""
        # Main console frame with proper resizing
        self.console_main_frame = tk.Frame(self.app, bg="#0a0e16")
        self.console_main_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Console header
        console_header = tk.Frame(self.console_main_frame, bg="#0a0e16")
        console_header.pack(fill="x", pady=(0, 5))
        
        header_label = tk.Label(
            console_header,
            text="Activity Console",
            bg="#0a0e16",
            fg="#f0f6fc",
            font=("Segoe UI", 12, "bold")
        )
        header_label.pack(side="left")
        
        # Console buttons with hover effects
        clear_btn = self._create_enhanced_button(
            console_header, "🗑 Clear", "#1a1f2e", "#ff6b6b", 
            self.app.clear_console
        )
        clear_btn.configure(font=("Segoe UI", 8, "bold"), padx=8, pady=4)
        clear_btn.pack(side="right")
        
        # Resize handle
        resize_btn = self._create_enhanced_button(
            console_header, "⇕", "#1a1f2e", "#8b949e", 
            self.toggle_console_size
        )
        resize_btn.configure(font=("Segoe UI", 8, "bold"), padx=8, pady=4, cursor="sb_v_double_arrow")
        resize_btn.pack(side="right", padx=(0, 5))
        
        # Console text container with initial height
        self.console_container = tk.Frame(self.console_main_frame, bg="#161b22", relief="solid", bd=1, height=120)
        self.console_container.pack(fill="both", expand=False)
        self.console_container.pack_propagate(False)
        
        self.app.console_text = tk.Text(
            self.console_container,
            bg="#0a0e16",
            fg="#58a6ff",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            padx=8,
            pady=4
        )
        self.app.console_text.pack(fill="both", expand=True)
        
        # Console size state
        self.console_expanded = False
    
    def setup_footer(self):
        """Setup the footer"""
        footer = tk.Frame(self.app, bg="#0a0e16", height=20)
        footer.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        footer.pack_propagate(False)
        
        footer_text = tk.Label(
            footer,
            text="Shortcuts: Ctrl+R (Refresh) | Ctrl+A (Select All) | Del (Delete Selected)",
            bg="#0a0e16",
            fg="#7d8590",
            font=("Segoe UI", 8)
        )
        footer_text.pack()
    
    # Window control methods
    def minimize_window(self):
        """Minimize the window"""
        try:
            self.app.iconify()
        except Exception as e:
            print(f"[UIManager] Error minimizing: {e}")
    
    def close_window(self):
        """Close the window"""
        try:
            self.app.destroy()
        except Exception as e:
            print(f"[UIManager] Error closing: {e}")
    
    def make_draggable_safe(self, widget):
        """Safer draggable implementation without overrideredirect"""
        def start_drag(event):
            try:
                self.dragging = True
                self.start_x = event.x_root - self.app.winfo_x()
                self.start_y = event.y_root - self.app.winfo_y()
                widget.configure(cursor="fleur")  # Change cursor to indicate dragging
            except Exception as e:
                print(f"[UIManager] Error starting drag: {e}")
                self.dragging = False
        
        def drag_window(event):
            try:
                if self.dragging:
                    x = event.x_root - self.start_x
                    y = event.y_root - self.start_y
                    
                    # Constrain to screen bounds
                    screen_width = self.app.winfo_screenwidth()
                    screen_height = self.app.winfo_screenheight()
                    window_width = self.app.winfo_width()
                    window_height = self.app.winfo_height()
                    
                    # Keep window on screen
                    x = max(0, min(x, screen_width - window_width))
                    y = max(0, min(y, screen_height - window_height))
                    
                    self.app.geometry(f"+{x}+{y}")
            except Exception as e:
                print(f"[UIManager] Error during drag: {e}")
                self.dragging = False
        
        def stop_drag(event):
            try:
                self.dragging = False
                widget.configure(cursor="")  # Reset cursor
            except Exception as e:
                print(f"[UIManager] Error stopping drag: {e}")
        
        # Bind events with error handling
        try:
            widget.bind("<Button-1>", start_drag)
            widget.bind("<B1-Motion>", drag_window)
            widget.bind("<ButtonRelease-1>", stop_drag)
            
            # Also bind to the main window for safety
            self.app.bind("<ButtonRelease-1>", stop_drag)
        except Exception as e:
            print(f"[UIManager] Error binding drag events: {e}")
    
    def toggle_console_size(self):
        """Toggle console between small and large size"""
        try:
            if self.console_expanded:
                # Shrink console
                self.console_container.configure(height=120)
                self.console_expanded = False
            else:
                # Expand console
                self.console_container.configure(height=300)
                self.console_expanded = True
            
            # Force update
            self.app.update_idletasks()
        except Exception as e:
            print(f"[UIManager] Error toggling console: {e}")
    
    def create_instance_with_enhanced_dialog(self):
        """Create instance using the separate dialog file"""
        try:
            # Import the dialog
            from gui.dialogs.create_instance_dialog import show_create_instance_dialog
            
            # Show dialog and get result
            instance_name = show_create_instance_dialog(self.app, self.app)
            
            # If user provided a name, create the instance
            if instance_name:
                self.app.instance_ops.create_instance_with_name(instance_name)
            else:
                self.app.add_console_message("Instance creation cancelled")
                
        except ImportError as e:
            print(f"[UIManager] Could not import create dialog: {e}")
            # Fallback to simple dialog
            self._create_instance_fallback()
        except Exception as e:
            print(f"[UIManager] Error with create dialog: {e}")
            messagebox.showerror("Error", f"Could not create instance: {str(e)}")
    
    def _create_instance_fallback(self):
        """Fallback simple dialog if the main one fails"""
        from tkinter import simpledialog
        
        name = simpledialog.askstring(
            "Create MEmu Instance", 
            "Enter MEmu instance name:",
            parent=self.app
        )
        
        if name:
            self.app.instance_ops.create_instance_with_name(name)
        else:
            self.app.add_console_message("Instance creation cancelled")
    
    def create_instance_with_dialog(self):
        """Legacy method - redirects to enhanced dialog"""
        self.create_instance_with_enhanced_dialog()
    
    def show_modules(self, instance_name):
        """Show modules window for an instance"""
        try:
            self.app.add_console_message(f"Opening module configuration for: {instance_name}")
            
            from gui.dialogs.modules_window import ModulesWindow
            ModulesWindow(self.app, instance_name, app_ref=self.app)
        except Exception as e:
            print(f"[UIManager] Error showing modules: {e}")
            messagebox.showerror("Error", f"Could not open modules: {str(e)}")

    def create_instance_card(self, name, status):
        """Create a new instance card with enhanced version"""
        try:
            from gui.components.instance_card import InstanceCard
            
            # Create the card without immediate UI updates
            card = InstanceCard(
                self.app.instances_container,
                name=name,
                status=status,
                cpu_usage=0,
                memory_usage=0,
                app_ref=self.app
            )
            
            # Schedule UI updates for next event loop
            def update_ui():
                try:
                    # Position all cards
                    self.app.reposition_all_cards()
                    
                    # Force counter update
                    self.app.force_counter_update()
                    
                    # Refresh modules when instances change
                    if hasattr(self.app, 'module_manager'):
                        self.app.module_manager.refresh_modules()
                except Exception as e:
                    print(f"[UIManager] Error updating UI: {e}")
            
            # Schedule UI updates for next event loop
            self.app.after(1, update_ui)
                
            return card
        except Exception as e:
            print(f"[UIManager] Error creating instance card: {e}")
            return None