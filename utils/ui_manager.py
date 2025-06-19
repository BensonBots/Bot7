"""
BENSON v2.0 - UI Management Utilities
Handles UI setup, layout management, and dialog creation with Settings integration
"""

import tkinter as tk
from tkinter import messagebox


class UIManager:
    """Manages UI setup and layout for the main application"""
    
    def __init__(self, app_ref):
        self.app = app_ref
    
    def setup_header(self):
        """Setup the header section"""
        header = tk.Frame(self.app, bg="#0a0e16", height=70)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)
        
        # Title
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
            text="Advanced Edition",
            bg="#0a0e16",
            fg="#00d4ff",
            font=("Segoe UI", 10, "bold")
        )
        subtitle.pack(side="left", padx=(10, 0), pady=(2, 0))
        
        # Search bar
        search_frame = tk.Frame(header, bg="#0a0e16")
        search_frame.pack(side="left", fill="x", expand=True, padx=(50, 50))
        
        self.setup_search_bar(search_frame)
        
        # Settings button
        settings_btn = tk.Button(
            header,
            text="⚙ Settings",
            bg="#1a1f2e",
            fg="#00ff88",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=16,
            pady=8,
            command=self.show_settings
        )
        settings_btn.pack(side="right")
    
    def setup_search_bar(self, parent):
        """Setup the search bar with responsive debouncing"""
        search_container = tk.Frame(parent, bg="#1e2329", relief="solid", bd=1)
        search_container.pack(fill="x")
        
        # Search icon
        search_icon = tk.Label(
            search_container,
            text="🔍",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 12)
        )
        search_icon.pack(side="left", padx=(8, 4))
        
        # Search entry
        self.app.search_var = tk.StringVar()
        self.app.search_var.trace("w", self.app.on_search_change_debounced)
        
        self.app.search_entry = tk.Entry(
            search_container,
            textvariable=self.app.search_var,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            insertbackground="#00d4ff",
            width=30
        )
        self.app.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        self.app.search_entry.insert(0, "Search instances...")
        self.app.search_entry.configure(fg="#8b949e")
        self.app.search_entry.bind("<FocusIn>", self.app.on_search_focus_in)
        self.app.search_entry.bind("<FocusOut>", self.app.on_search_focus_out)
    
    def setup_controls(self):
        """Setup the control section"""
        controls = tk.Frame(self.app, bg="#0a0e16")
        controls.pack(fill="x", padx=10, pady=10)
        
        # Left side - instances header
        left_frame = tk.Frame(controls, bg="#0a0e16")
        left_frame.pack(side="left")
        
        # Get the current instance count
        current_instances = self.app.instance_manager.get_instances()
        instances_count = len(current_instances)
        
        # Create header with correct count
        self.app.instances_header = tk.Label(
            left_frame,
            text=f"⚡ MEmu Instances ({instances_count})",
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
            ("➕ Create", "#00ff88", "#000000", self.app.instance_ops.create_instance),
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
        """Setup the console section"""
        console_frame = tk.Frame(self.app, bg="#0a0e16", height=120)
        console_frame.pack(fill="x", padx=10, pady=(10, 0))
        console_frame.pack_propagate(False)
        
        # Console header
        console_header = tk.Frame(console_frame, bg="#0a0e16")
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
        
        # Console text
        console_container = tk.Frame(console_frame, bg="#161b22", relief="solid", bd=1)
        console_container.pack(fill="both", expand=True)
        
        self.app.console_text = tk.Text(
            console_container,
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
    
    def show_analytics(self):
        """Show analytics window with enhanced stats"""
        analytics_window = tk.Toplevel(self.app)
        analytics_window.title("Instance Analytics")
        analytics_window.geometry("700x500")
        analytics_window.configure(bg="#1e2329")
        analytics_window.transient(self.app)
        
        # Center the window
        analytics_window.update_idletasks()
        x = (analytics_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (analytics_window.winfo_screenheight() // 2) - (500 // 2)
        analytics_window.geometry(f"700x500+{x}+{y}")
        
        # Title
        title = tk.Label(
            analytics_window, 
            text="📊 Instance Analytics Dashboard", 
            bg="#1e2329", 
            fg="#00ff88", 
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=20)
        
        # Create main content frame
        content_frame = tk.Frame(analytics_window, bg="#1e2329")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Instance Statistics
        stats_section = tk.Frame(content_frame, bg="#0a0e16", relief="solid", bd=1)
        stats_section.pack(fill="x", pady=(0, 15))
        
        stats_title = tk.Label(
            stats_section,
            text="Instance Overview",
            bg="#0a0e16",
            fg="#00d4ff",
            font=("Segoe UI", 12, "bold")
        )
        stats_title.pack(pady=(10, 5))
        
        # Get statistics
        instances = self.app.instance_manager.get_instances()
        manager_stats = self.app.instance_manager.get_manager_stats()
        
        total = len(instances)
        running = sum(1 for i in instances if i["status"] == "Running")
        offline = sum(1 for i in instances if i["status"] in ["Offline", "Stopped"])
        
        avg_cpu = sum(i['cpu'] for i in instances) / total if total > 0 else 0
        avg_memory = sum(i['memory'] for i in instances) / total if total > 0 else 0
        
        # OCR info
        ocr_status = "Available" if self.app.ocr_helper else "Not Available"
        if self.app.ocr_helper:
            regions_count = len(self.app.ocr_helper.get_available_regions())
            ocr_info = f"{ocr_status} ({regions_count} regions)"
        else:
            ocr_info = ocr_status
        
        # Module info
        if hasattr(self.app, 'module_manager'):
            module_status = self.app.module_manager.get_module_status()
            modules_info = f"{module_status['available_modules']}/{module_status['total_instances']} available, {module_status['auto_startup_enabled']} auto-startup"
        else:
            modules_info = "Not initialized"
        
        # Optimization defaults
        opt_defaults = self.app.instance_manager.get_optimization_defaults()
        
        stats_text = f"""
Instance Statistics:
• Total Instances: {total}
• Running: {running}
• Offline/Stopped: {offline}
• Average CPU Usage: {avg_cpu:.1f}%
• Average Memory Usage: {avg_memory:.1f}%

System Information:
• OCR Status: {ocr_info}
• Modules: {modules_info}
• MEmu Available: {'Yes' if manager_stats['memu_available'] else 'No'}

Optimization Settings:
• Default RAM: {opt_defaults['default_ram_mb']}MB
• Default CPU Cores: {opt_defaults['default_cpu_cores']}
• Performance Mode: {opt_defaults['performance_mode'].title()}
        """
        
        stats_label = tk.Label(
            stats_section,
            text=stats_text,
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 10),
            justify="left"
        )
        stats_label.pack(pady=(5, 15), padx=20)
        
        # Performance Chart (Placeholder)
        chart_section = tk.Frame(content_frame, bg="#0a0e16", relief="solid", bd=1)
        chart_section.pack(fill="both", expand=True, pady=(0, 15))
        
        chart_title = tk.Label(
            chart_section,
            text="Performance Overview",
            bg="#0a0e16",
            fg="#00d4ff",
            font=("Segoe UI", 12, "bold")
        )
        chart_title.pack(pady=(10, 5))
        
        # Simple performance bars
        perf_frame = tk.Frame(chart_section, bg="#0a0e16")
        perf_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # CPU Usage Bar
        cpu_label = tk.Label(perf_frame, text=f"Average CPU: {avg_cpu:.1f}%", bg="#0a0e16", fg="#ffffff", font=("Segoe UI", 10))
        cpu_label.pack(anchor="w")
        
        cpu_bar_bg = tk.Frame(perf_frame, bg="#404040", height=20)
        cpu_bar_bg.pack(fill="x", pady=(2, 10))
        cpu_bar_bg.pack_propagate(False)
        
        cpu_bar_fill = tk.Frame(cpu_bar_bg, bg="#00ff88", height=20)
        cpu_bar_fill.place(x=0, y=0, relwidth=min(avg_cpu/100, 1.0), relheight=1.0)
        
        # Memory Usage Bar
        mem_label = tk.Label(perf_frame, text=f"Average Memory: {avg_memory:.1f}%", bg="#0a0e16", fg="#ffffff", font=("Segoe UI", 10))
        mem_label.pack(anchor="w")
        
        mem_bar_bg = tk.Frame(perf_frame, bg="#404040", height=20)
        mem_bar_bg.pack(fill="x", pady=(2, 10))
        mem_bar_bg.pack_propagate(False)
        
        mem_bar_fill = tk.Frame(mem_bar_bg, bg="#00d4ff", height=20)
        mem_bar_fill.place(x=0, y=0, relwidth=min(avg_memory/100, 1.0), relheight=1.0)
        
        # Instance Status Distribution
        status_label = tk.Label(perf_frame, text="Instance Status Distribution", bg="#0a0e16", fg="#ffffff", font=("Segoe UI", 10))
        status_label.pack(anchor="w", pady=(10, 2))
        
        status_frame = tk.Frame(perf_frame, bg="#0a0e16")
        status_frame.pack(fill="x")
        
        if total > 0:
            running_pct = (running / total) * 100
            offline_pct = (offline / total) * 100
            
            # Running instances
            running_info = tk.Label(status_frame, text=f"Running: {running} ({running_pct:.1f}%)", bg="#0a0e16", fg="#00ff88", font=("Segoe UI", 9))
            running_info.pack(side="left")
            
            # Offline instances
            offline_info = tk.Label(status_frame, text=f"Offline: {offline} ({offline_pct:.1f}%)", bg="#0a0e16", fg="#ff6b6b", font=("Segoe UI", 9))
            offline_info.pack(side="right")
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg="#1e2329")
        button_frame.pack(fill="x")
        
        # Refresh button
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 Refresh Data",
            bg="#2196f3",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=lambda: [self.app.instance_ops.refresh_instances(), analytics_window.destroy(), self.show_analytics()]
        )
        refresh_btn.pack(side="left")
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="✗ Close",
            bg="#ff6b6b",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=analytics_window.destroy
        )
        close_btn.pack(side="right")
    
    def show_settings(self):
        """Show settings window"""
        from gui.dialogs.settings_window import SettingsWindow
        SettingsWindow(self.app, app_ref=self.app)
    
    def show_modules(self, instance_name):
        """Show modules window for an instance with real AutoStartGame module"""
        self.app.add_console_message(f"Opening module configuration for: {instance_name}")
        
        # Import the enhanced modules window
        from gui.dialogs.modules_window import ModulesWindow
        
        # Create and show the modules window
        ModulesWindow(self.app, instance_name, app_ref=self.app)