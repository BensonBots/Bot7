import tkinter as tk

class UIManager:
    def __init__(self, app_ref):
        self.app = app_ref
    
    def setup_header(self):
        header = tk.Frame(self.app, bg="#0a0e16", height=70)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#0a0e16")
        title_frame.pack(side="left", fill="y")
        
        title_label = tk.Label(title_frame, text="BENSON v2.0", bg="#0a0e16", fg="#f0f6fc", font=("Segoe UI", 18, "bold"))
        title_label.pack(side="left")
        
        subtitle = tk.Label(title_frame, text="Streamlined", bg="#0a0e16", fg="#00d4ff", font=("Segoe UI", 10, "bold"))
        subtitle.pack(side="left", padx=(10, 0), pady=(2, 0))
        
        search_frame = tk.Frame(header, bg="#0a0e16")
        search_frame.pack(side="left", fill="x", expand=True, padx=(50, 50))
        self.setup_search_bar(search_frame)
        
        status_frame = tk.Frame(header, bg="#0a0e16")
        status_frame.pack(side="right")
        
        memu_status = "Connected" if self.app.instance_manager._is_memu_available() else "Disconnected"
        status_color = "#00ff88" if memu_status == "Connected" else "#ff6b6b"
        status_label = tk.Label(status_frame, text=f"MEmu: {memu_status}", bg="#0a0e16", fg=status_color, font=("Segoe UI", 10))
        status_label.pack(side="right")
    
    def setup_search_bar(self, parent):
        search_container = tk.Frame(parent, bg="#1e2329", relief="solid", bd=1)
        search_container.pack(fill="x")
        
        search_icon = tk.Label(search_container, text="🔍", bg="#1e2329", fg="#8b949e", font=("Segoe UI", 12))
        search_icon.pack(side="left", padx=(8, 4))
        
        self.app.search_var = tk.StringVar()
        self.app.search_var.trace("w", self.app.on_search_change_debounced)
        
        self.app.search_entry = tk.Entry(search_container, textvariable=self.app.search_var, bg="#1e2329", fg="#ffffff", font=("Segoe UI", 11), relief="flat", bd=0, insertbackground="#00d4ff", width=30)
        self.app.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        self.app.search_entry.insert(0, "Search instances...")
        self.app.search_entry.configure(fg="#8b949e")
        self.app.search_entry.bind("<FocusIn>", self.app.on_search_focus_in)
        self.app.search_entry.bind("<FocusOut>", self.app.on_search_focus_out)
    
    def setup_controls(self):
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)
        
        left_frame = tk.Frame(controls, bg="#0a0e16")
        left_frame.pack(side="left")
        
        current_instances = self.app.instance_manager.get_instances()
        instances_count = len(current_instances)
        
        self.app.instances_header = tk.Label(left_frame, text=f"⚡ MEmu Instances ({instances_count})", bg="#0a0e16", fg="#00ff88", font=("Segoe UI", 16, "bold"), cursor="hand2")
        self.app.instances_header.pack(side="left")
        self.app.instances_header.bind("<Button-1>", lambda e: self.app.instance_ops.toggle_select_all())
        
        bulk_frame = tk.Frame(controls, bg="#0a0e16")
        bulk_frame.pack(side="left", padx=(40, 0))
        
        buttons = [("➕ Create", "#00ff88", "#000000", self.app.instance_ops.create_instance), ("📋 Clone", "#00d4ff", "#000000", self.app.instance_ops.clone_selected_instance), ("▶ Start All", "#00e676", "#000000", self.app.instance_ops.start_selected_instances), ("⏹ Stop All", "#ff6b6b", "#ffffff", self.app.instance_ops.stop_selected_instances)]
        
        for text, bg, fg, command in buttons:
            btn = tk.Button(bulk_frame, text=text, bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=command)
            btn.pack(side="left", padx=(0, 8))
        
        refresh_btn = tk.Button(controls, text="⟳ Refresh", bg="#1a1f2e", fg="#00d4ff", font=("Segoe UI", 10, "bold"), relief="flat", bd=0, cursor="hand2", padx=16, pady=8, command=self.app.instance_ops.refresh_instances)
        refresh_btn.pack(side="right")
    
    def setup_main_content(self):
        main_frame = tk.Frame(self.app, bg="#0a0e16")
        main_frame.pack(fill="both", expand=True, padx=10)
        
        self.app.instances_container = tk.Frame(main_frame, bg="#0a0e16")
        self.app.instances_container.pack(fill="both", expand=True)
        
        self.app.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
        self.app.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
    
    def setup_console(self):
        console_frame = tk.Frame(self.app, bg="#0a0e16", height=120)
        console_frame.pack(fill="x", padx=10, pady=(10, 0))
        console_frame.pack_propagate(False)
        
        console_header = tk.Frame(console_frame, bg="#0a0e16")
        console_header.pack(fill="x", pady=(0, 5))
        
        header_label = tk.Label(console_header, text="Activity Console", bg="#0a0e16", fg="#f0f6fc", font=("Segoe UI", 12, "bold"))
        header_label.pack(side="left")
        
        if hasattr(self.app, 'module_manager'):
            module_status = self.app.module_manager.get_module_status()
            if module_status['currently_running'] > 0:
                status_text = f"Modules: {module_status['currently_running']}"
                status_label = tk.Label(console_header, text=status_text, bg="#0a0e16", fg="#00ff88", font=("Segoe UI", 9))
                status_label.pack(side="left", padx=(20, 0))
        
        clear_btn = tk.Button(console_header, text="🗑 Clear", bg="#1a1f2e", fg="#ff6b6b", relief="flat", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=8, pady=4, command=self.app.clear_console)
        clear_btn.pack(side="right")
        
        console_container = tk.Frame(console_frame, bg="#161b22", relief="solid", bd=1)
        console_container.pack(fill="both", expand=True)
        
        self.app.console_text = tk.Text(console_container, bg="#0a0e16", fg="#58a6ff", font=("Consolas", 9), relief="flat", bd=0, wrap="word", state="disabled", padx=8, pady=4)
        self.app.console_text.pack(fill="both", expand=True)
    
    def setup_footer(self):
        footer = tk.Frame(self.app, bg="#0a0e16", height=20)
        footer.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        footer.pack_propagate(False)
        
        footer_text = tk.Label(footer, text="Ctrl+R (Refresh) | Ctrl+A (Select All) | Del (Delete)", bg="#0a0e16", fg="#7d8590", font=("Segoe UI", 8))
        footer_text.pack()
    
    def show_modules(self, instance_name):
        from gui.dialogs.modules_window import ModulesWindow
        ModulesWindow(self.app, instance_name, app_ref=self.app)