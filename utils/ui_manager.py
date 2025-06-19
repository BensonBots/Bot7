"""
BENSON v2.0 - Fixed UI Manager
All issues resolved: console resize, header text, search size, window controls
"""

import tkinter as tk
from tkinter import messagebox


class UIManager:
    """Fixed UI manager with all requested improvements"""
    
    def __init__(self, app_ref):
        self.app = app_ref
    
    def setup_header(self):
        """Setup header with custom window controls and smaller search"""
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
        
        # Hide default window controls
        try:
            self.app.overrideredirect(True)
            # Make window draggable
            self.make_draggable(header)
        except:
            # Fallback if override doesn't work
            pass
    
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
        """Setup control section with fixed instance counter"""
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)
        
        # Left side - instances header (just "Instances")
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
        
        # Center - Bulk operations
        bulk_frame = tk.Frame(controls, bg="#0a0e16")
        bulk_frame.pack(side="left", padx=(40, 0))
        
        buttons = [
            ("➕ Create", "#00ff88", "#000000", self.create_instance_with_dialog),
            ("📋 Clone", "#00d4ff", "#000000", self.app.instance_ops.clone_selected_instance),
            ("▶ Start All", "#00e676", "#000000", self.app.instance_ops.start_selected_instances),
            ("⏹ Stop All", "#ff6b6b", "#ffffff", self.app.instance_ops.stop_selected_instances)
        ]
        
        for text, bg, fg, command in buttons:
            btn = tk.Button(
                bulk_frame,
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
            btn.pack(side="left", padx=(0, 8))
        
        # Right side - refresh button
        refresh_btn = tk.Button(
            controls,
            text="⟳ Refresh",
            bg="#1a1f2e",
            fg="#00d4ff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=8,
            command=self.app.instance_ops.refresh_instances
        )
        refresh_btn.pack(side="right")
    
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
        
        # Console buttons
        clear_btn = tk.Button(
            console_header,
            text="🗑 Clear",
            bg="#1a1f2e",
            fg="#ff6b6b",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.app.clear_console
        )
        clear_btn.pack(side="right")
        
        # Resize handle
        resize_btn = tk.Button(
            console_header,
            text="⇕",
            bg="#1a1f2e",
            fg="#8b949e",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="sb_v_double_arrow",
            padx=8,
            pady=4,
            command=self.toggle_console_size
        )
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
        self.app.iconify()
    
    def close_window(self):
        """Close the window"""
        self.app.destroy()
    
    def make_draggable(self, widget):
        """Make the window draggable by clicking on header"""
        def start_drag(event):
            widget.start_x = event.x
            widget.start_y = event.y
        
        def drag_window(event):
            x = self.app.winfo_x() + (event.x - widget.start_x)
            y = self.app.winfo_y() + (event.y - widget.start_y)
            self.app.geometry(f"+{x}+{y}")
        
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", drag_window)
    
    def toggle_console_size(self):
        """Toggle console between small and large size"""
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
    
    def create_instance_with_dialog(self):
        """Create instance with better dialog"""
        # Create custom dialog
        dialog = tk.Toplevel(self.app)
        dialog.title("Create MEmu Instance")
        dialog.geometry("400x200")
        dialog.configure(bg="#1e2329")
        dialog.transient(self.app)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (100)
        dialog.geometry(f"400x200+{x}+{y}")
        
        # Title
        tk.Label(dialog, text="🆕 Create New Instance", bg="#1e2329", fg="#00d4ff",
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(dialog, bg="#1e2329")
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Instance Name:", bg="#1e2329", fg="#ffffff",
                font=("Segoe UI", 10)).pack(pady=(0, 5))
        
        name_var = tk.StringVar()
        name_entry = tk.Entry(input_frame, textvariable=name_var, bg="#0a0e16", fg="#ffffff",
                             font=("Segoe UI", 11), width=25, relief="solid", bd=1)
        name_entry.pack(pady=(0, 10))
        name_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(dialog, bg="#1e2329")
        button_frame.pack(pady=20)
        
        def create_instance():
            name = name_var.get().strip()
            if name:
                dialog.destroy()
                # Call the actual creation method with the name
                self.app.instance_ops.create_instance_with_name(name)
            else:
                messagebox.showerror("Error", "Please enter a valid instance name")
        
        def cancel():
            dialog.destroy()
        
        tk.Button(button_frame, text="✓ Create", bg="#00ff88", fg="#000000",
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=20, pady=8,
                 cursor="hand2", command=create_instance).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame, text="✗ Cancel", bg="#ff6b6b", fg="#ffffff",
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=20, pady=8,
                 cursor="hand2", command=cancel).pack(side="left")
        
        # Enter key binding
        dialog.bind('<Return>', lambda e: create_instance())
        name_entry.bind('<Return>', lambda e: create_instance())
    
    def show_modules(self, instance_name):
        """Show modules window for an instance"""
        self.app.add_console_message(f"Opening module configuration for: {instance_name}")
        
        from gui.dialogs.modules_window import ModulesWindow
        ModulesWindow(self.app, instance_name, app_ref=self.app)

    def create_instance_card(self, name, status):
        """Create a new instance card"""
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
            # Position all cards
            self.app.reposition_all_cards()
            
            # Force counter update
            self.app.force_counter_update()
            
            # Refresh modules when instances change
            if hasattr(self.app, 'module_manager'):
                self.app.module_manager.refresh_modules()
        
        # Schedule UI updates for next event loop
        self.app.after(1, update_ui)
            
        return card