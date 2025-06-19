"""
BENSON v2.0 - Simplified Settings Window
Optimization settings only
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os


class SettingsWindow:
    def __init__(self, parent, app_ref=None):
        self.parent = parent
        self.app_ref = app_ref
        self.settings_file = "benson_settings.json"
        
        # Load current settings
        self.settings = self._load_settings()
        
        self._create_window()
        self._setup_content()
    
    def _load_settings(self):
        """Load global BENSON settings"""
        default_settings = {
            "optimization": {
                "default_ram_mb": 2048,
                "default_cpu_cores": 2,
                "auto_optimize_new_instances": True,
                "performance_mode": "balanced"  # balanced, performance, battery
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults
                if "optimization" not in settings:
                    settings["optimization"] = default_settings["optimization"]
                else:
                    for key, value in default_settings["optimization"].items():
                        if key not in settings["optimization"]:
                            settings["optimization"][key] = value
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            if self.app_ref:
                self.app_ref.add_console_message("💾 Settings saved successfully")
            
            return True
        except Exception as e:
            if self.app_ref:
                self.app_ref.add_console_message(f"❌ Failed to save settings: {e}")
            else:
                print(f"Error saving settings: {e}")
            return False
    
    def _create_window(self):
        """Create the settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("BENSON Optimization Settings")
        self.window.geometry("600x500")
        self.window.configure(bg="#1e2329")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_content(self):
        """Setup the window content"""
        # Main content frame
        content = tk.Frame(self.window, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            content,
            text="⚙ Optimization Settings",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(0, 30))
        
        # Create scrollable frame for settings
        self._create_optimization_settings(content)
        
        # Buttons
        self._create_buttons(content)
    
    def _create_optimization_settings(self, parent):
        """Create optimization settings section"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg="#1e2329", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e2329")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True, pady=(0, 20))
        scrollbar.pack(side="right", fill="y", pady=(0, 20))
        
        # Current Optimization Status
        if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
            status_section = self._create_section(scrollable_frame, "📊 Optimization Status")
            
            instances = self.app_ref.instance_manager.get_instances()
            needs_optimization = []
            already_optimized = []
            
            for instance in instances:
                info = self.app_ref.instance_manager.get_instance_optimization_info(instance["name"])
                if info:
                    if info["needs_optimization"]:
                        needs_optimization.append(info)
                    else:
                        already_optimized.append(info)
            
            # Status summary
            status_frame = tk.Frame(status_section, bg="#0a0e16")
            status_frame.pack(fill="x", padx=15, pady=10)
            
            if needs_optimization:
                status_label = tk.Label(
                    status_frame,
                    text=f"⚠ {len(needs_optimization)} instance(s) need optimization:",
                    bg="#0a0e16",
                    fg="#ff9800",
                    font=("Segoe UI", 11)
                )
                status_label.pack(anchor="w")
                
                for info in needs_optimization:
                    instance_frame = tk.Frame(status_frame, bg="#0a0e16")
                    instance_frame.pack(fill="x", pady=2)
                    
                    current_settings = f"Current: {info['current_ram']}MB RAM, {info['current_cpu']} CPU" if info['current_ram'] else "Not optimized"
                    target_settings = f"Target: {info['recommended_ram']}MB RAM, {info['recommended_cpu']} CPU"
                    
                    tk.Label(
                        instance_frame,
                        text=f"• {info['instance_name']}",
                        bg="#0a0e16",
                        fg="#ffffff",
                        font=("Segoe UI", 10)
                    ).pack(side="left")
                    
                    tk.Label(
                        instance_frame,
                        text=f"{current_settings} → {target_settings}",
                        bg="#0a0e16",
                        fg="#8b949e",
                        font=("Segoe UI", 9)
                    ).pack(side="right")
            else:
                status_label = tk.Label(
                    status_frame,
                    text="✓ All instances are optimized",
                    bg="#0a0e16",
                    fg="#00ff88",
                    font=("Segoe UI", 11)
                )
                status_label.pack(anchor="w")
            
            # Add optimize all button if needed
            if needs_optimization:
                optimize_btn = tk.Button(
                    status_frame,
                    text="🚀 Optimize All",
                    bg="#00ff88",
                    fg="#000000",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat",
                    bd=0,
                    padx=15,
                    pady=5,
                    cursor="hand2",
                    command=self._optimize_all_instances
                )
                optimize_btn.pack(pady=(10, 0))
        
        # RAM Settings
        ram_section = self._create_section(scrollable_frame, "💾 Default RAM Settings")
        
        ram_frame = tk.Frame(ram_section, bg="#0a0e16")
        ram_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            ram_frame,
            text="Default RAM per instance (MB):",
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.ram_var = tk.StringVar(value=str(self.settings["optimization"]["default_ram_mb"]))
        ram_spinbox = tk.Spinbox(
            ram_frame,
            from_=512,
            to=8192,
            increment=512,
            textvariable=self.ram_var,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 11),
            width=10,
            buttonbackground="#404040",
            relief="flat",
            bd=1
        )
        ram_spinbox.pack(side="right")
        
        # CPU Settings
        cpu_section = self._create_section(scrollable_frame, "🖥 Default CPU Settings")
        
        cpu_frame = tk.Frame(cpu_section, bg="#0a0e16")
        cpu_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            cpu_frame,
            text="Default CPU cores per instance:",
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.cpu_var = tk.StringVar(value=str(self.settings["optimization"]["default_cpu_cores"]))
        cpu_spinbox = tk.Spinbox(
            cpu_frame,
            from_=1,
            to=8,
            increment=1,
            textvariable=self.cpu_var,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 11),
            width=10,
            buttonbackground="#404040",
            relief="flat",
            bd=1
        )
        cpu_spinbox.pack(side="right")
        
        # Performance Mode
        perf_section = self._create_section(scrollable_frame, "⚡ Performance Mode")
        
        perf_frame = tk.Frame(perf_section, bg="#0a0e16")
        perf_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            perf_frame,
            text="Optimization mode:",
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.perf_var = tk.StringVar(value=self.settings["optimization"]["performance_mode"])
        
        # Style the combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TCombobox', 
                       fieldbackground='#1e2329',
                       background='#404040',
                       foreground='#ffffff',
                       borderwidth=1,
                       focuscolor='#00d4ff')
        
        perf_combo = ttk.Combobox(
            perf_frame,
            textvariable=self.perf_var,
            values=["battery", "balanced", "performance"],
            state="readonly",
            width=15,
            style='Custom.TCombobox',
            font=("Segoe UI", 10)
        )
        perf_combo.pack(side="right")
        
        # Performance mode descriptions
        perf_desc_frame = tk.Frame(perf_section, bg="#0a0e16")
        perf_desc_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        perf_descriptions = {
            "battery": "🔋 Battery Mode: Reduced resources for power saving",
            "balanced": "⚖️ Balanced Mode: Standard resource allocation", 
            "performance": "🚀 Performance Mode: Maximum resources for speed"
        }
        
        for mode, desc in perf_descriptions.items():
            desc_label = tk.Label(
                perf_desc_frame,
                text=desc,
                bg="#0a0e16",
                fg="#7d8590",
                font=("Segoe UI", 9),
                justify="left"
            )
            desc_label.pack(anchor="w", pady=1)
        
        # Auto Optimization Options
        auto_section = self._create_section(scrollable_frame, "🤖 Auto Optimization")
        
        self.auto_optimize_var = tk.BooleanVar(value=self.settings["optimization"]["auto_optimize_new_instances"])
        auto_check = tk.Checkbutton(
            auto_section,
            text="Auto-optimize new instances when created",
            variable=self.auto_optimize_var,
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 11),
            selectcolor="#0a0e16",
            activebackground="#0a0e16",
            activeforeground="#ffffff",
            relief="flat"
        )
        auto_check.pack(anchor="w", padx=15, pady=8)
        
        # Add info label about instance optimization
        info_label = tk.Label(
            auto_section,
            text="Note: Instances will be checked and optimized when started",
            bg="#0a0e16",
            fg="#8b949e",
            font=("Segoe UI", 10, "italic"),
            justify="left",
            wraplength=400
        )
        info_label.pack(anchor="w", padx=15, pady=(0, 8))
        
        # Performance presets
        presets_section = self._create_section(scrollable_frame, "🎯 Quick Presets")
        
        presets_desc = tk.Label(
            presets_section,
            text="Apply common optimization presets:",
            bg="#0a0e16",
            fg="#8b949e",
            font=("Segoe UI", 10)
        )
        presets_desc.pack(anchor="w", padx=15, pady=(5, 10))
        
        presets_frame = tk.Frame(presets_section, bg="#0a0e16")
        presets_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        presets = [
            ("Low End", 1024, 1, "#ff9800"),
            ("Balanced", 2048, 2, "#2196f3"),
            ("High Performance", 4096, 4, "#00ff88"),
            ("Maximum", 6144, 6, "#ff6b6b")
        ]
        
        for i, (name, ram, cpu, color) in enumerate(presets):
            row = i // 2
            col = i % 2
            
            btn = tk.Button(
                presets_frame,
                text=f"{name}\n{ram}MB, {cpu} cores",
                bg=color,
                fg="#000000" if color in ["#00ff88", "#ff9800"] else "#ffffff",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                bd=0,
                padx=15,
                pady=10,
                cursor="hand2",
                width=18,
                command=lambda r=ram, c=cpu: self._apply_preset(r, c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid columns
        presets_frame.grid_columnconfigure(0, weight=1)
        presets_frame.grid_columnconfigure(1, weight=1)
        
        # Current settings display
        current_section = self._create_section(scrollable_frame, "📊 Current Settings Summary")
        
        self.current_settings_label = tk.Label(
            current_section,
            text="",
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 10),
            justify="left"
        )
        self.current_settings_label.pack(anchor="w", padx=15, pady=10)
        
        # Update current settings display
        self._update_current_settings_display()
        
        # Bind events to update display
        self.ram_var.trace("w", lambda *args: self._update_current_settings_display())
        self.cpu_var.trace("w", lambda *args: self._update_current_settings_display())
        self.perf_var.trace("w", lambda *args: self._update_current_settings_display())
    
    def _create_section(self, parent, title):
        """Create a settings section with title"""
        section_frame = tk.Frame(parent, bg="#0a0e16", relief="solid", bd=1)
        section_frame.pack(fill="x", pady=10, padx=10)
        
        title_label = tk.Label(
            section_frame,
            text=title,
            bg="#0a0e16",
            fg="#00ff88",
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        return section_frame
    
    def _create_buttons(self, parent):
        """Create action buttons"""
        button_frame = tk.Frame(parent, bg="#1e2329")
        button_frame.pack(fill="x")
        
        # Apply button
        apply_btn = tk.Button(
            button_frame,
            text="✓ Apply",
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._apply_settings
        )
        apply_btn.pack(side="left")
        
        # Save & Close button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save & Close",
            bg="#2196f3",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._save_and_close
        )
        save_btn.pack(side="left", padx=(15, 0))
        
        # Reset to defaults button
        reset_btn = tk.Button(
            button_frame,
            text="🔄 Reset to Defaults",
            bg="#ff9800",
            fg="#000000",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._reset_to_defaults
        )
        reset_btn.pack(side="left", padx=(15, 0))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="✗ Cancel",
            bg="#ff6b6b",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self.window.destroy
        )
        cancel_btn.pack(side="right")
    
    def _apply_preset(self, ram, cpu):
        """Apply a performance preset"""
        self.ram_var.set(str(ram))
        self.cpu_var.set(str(cpu))
        
        if self.app_ref:
            self.app_ref.add_console_message(f"⚙ Applied preset: {ram}MB RAM, {cpu} CPU cores")
    
    def _update_current_settings_display(self):
        """Update the current settings display"""
        try:
            ram = int(self.ram_var.get())
            cpu = int(self.cpu_var.get())
            mode = self.perf_var.get()
            
            # Calculate actual values based on performance mode
            if mode == "performance":
                actual_ram = int(ram * 1.2)
                actual_cpu = min(cpu + 1, 8)
                modifier = " (+20% RAM, +1 CPU)"
            elif mode == "battery":
                actual_ram = int(ram * 0.8)
                actual_cpu = max(cpu - 1, 1)
                modifier = " (-20% RAM, -1 CPU)"
            else:
                actual_ram = ram
                actual_cpu = cpu
                modifier = ""
            
            settings_text = f"""Base Settings: {ram}MB RAM, {cpu} CPU cores
Performance Mode: {mode.title()}{modifier}
Actual Applied: {actual_ram}MB RAM, {actual_cpu} CPU cores

Auto-optimize new instances: {'Yes' if self.auto_optimize_var.get() else 'No'}
Optimize on startup: {'Yes' if self.startup_optimize_var.get() else 'No'}"""
            
            self.current_settings_label.configure(text=settings_text)
            
        except ValueError:
            self.current_settings_label.configure(text="Invalid settings values")
    
    def _apply_settings(self):
        """Apply settings without closing"""
        if self._save_current_settings():
            self._apply_to_app()
            messagebox.showinfo("Settings Applied", "Optimization settings have been applied successfully!")
    
    def _save_and_close(self):
        """Save settings and close window"""
        if self._save_current_settings():
            self._apply_to_app()
            self.window.destroy()
    
    def _save_current_settings(self):
        """Save current form values to settings"""
        try:
            # Optimization settings
            self.settings["optimization"]["default_ram_mb"] = int(self.ram_var.get())
            self.settings["optimization"]["default_cpu_cores"] = int(self.cpu_var.get())
            self.settings["optimization"]["performance_mode"] = self.perf_var.get()
            self.settings["optimization"]["auto_optimize_new_instances"] = self.auto_optimize_var.get()
            
            return self._save_settings()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your numeric inputs:\n{e}")
            return False
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{e}")
            return False
    
    def _apply_to_app(self):
        """Apply settings to the running application"""
        if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
            # Update optimization defaults in instance manager
            if hasattr(self.app_ref.instance_manager, 'update_optimization_defaults'):
                self.app_ref.instance_manager.update_optimization_defaults(
                    ram_mb=self.settings["optimization"]["default_ram_mb"],
                    cpu_cores=self.settings["optimization"]["default_cpu_cores"],
                    performance_mode=self.settings["optimization"]["performance_mode"]
                )
            
            self.app_ref.add_console_message("⚙ Optimization settings applied")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        result = messagebox.askyesno("Reset Settings", 
                                   "This will reset all optimization settings to their default values.\n\nAre you sure?")
        if result:
            # Reset to default values
            self.ram_var.set("2048")
            self.cpu_var.set("2")
            self.perf_var.set("balanced")
            self.auto_optimize_var.set(True)
            self.startup_optimize_var.set(True)
            
            if self.app_ref:
                self.app_ref.add_console_message("🔄 Optimization settings reset to defaults")
    
    def _on_closing(self):
        """Handle window closing"""
        self.window.destroy()

    def _optimize_all_instances(self):
        """Optimize all instances"""
        if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
            self.app_ref.instance_manager.optimize_all_instances()
            self.app_ref.add_console_message("🚀 Optimizing all instances")