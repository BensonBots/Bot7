"""
BENSON v2.0 - Enhanced Modules Window
Simple list-based module configuration
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import threading


class ModulesWindow:
    def __init__(self, parent, instance_name, app_ref=None):
        self.parent = parent
        self.instance_name = instance_name
        self.app_ref = app_ref
        self.modules = {}  # Store module instances
        
        # Load settings first (fast operation)
        self.settings_file = f"settings_{instance_name}.json"
        self.settings = self._load_settings()
        
        # Create window immediately
        self._create_window()
        
        # Load modules in background to prevent UI freeze
        threading.Thread(target=self._load_modules, daemon=True).start()
    
    def _create_window(self):
        """Create the modules window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Modules - {self.instance_name}")
        self.window.geometry("600x400")
        self.window.configure(bg="#1e2329")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"600x400+{x}+{y}")
        
        # Create main content frame
        self.content = tk.Frame(self.window, bg="#1e2329")
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            self.content,
            text=f"⚙ Modules Configuration",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=(0, 20))
        
        # Loading indicator
        self.loading_label = tk.Label(
            self.content,
            text="Loading modules...",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 11)
        )
        self.loading_label.pack(pady=10)
        
        # Modules list frame
        self.modules_frame = tk.Frame(self.content, bg="#1e2329")
        self.modules_frame.pack(fill="both", expand=True)
        
        # Bottom buttons
        button_frame = tk.Frame(self.content, bg="#1e2329")
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Settings",
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._save_and_close
        )
        save_btn.pack(side="left")
        
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
            command=self.window.destroy
        )
        close_btn.pack(side="right")
    
    def _load_modules(self):
        """Load available modules in background"""
        try:
            # Initialize AutoStartGame module if available
            if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
                try:
                    from modules.autostart_game import AutoStartGameModule
                    self.modules["autostart_game"] = {
                        "name": "AutoStartGame",
                        "instance": AutoStartGameModule(
                            self.app_ref.instance_manager,
                            console_callback=self.app_ref.add_console_message if hasattr(self.app_ref, 'add_console_message') else None
                        ),
                        "description": "Automatically starts the game using image detection",
                        "icon": "🎮"
                    }
                except ImportError:
                    pass
            
            # Update UI in main thread
            self.window.after(0, self._create_modules_list)
            
        except Exception as e:
            print(f"Error loading modules: {e}")
            self.window.after(0, lambda: self.loading_label.configure(
                text="Error loading modules", fg="#ff6b6b"
            ))
    
    def _create_modules_list(self):
        """Create the modules list UI"""
        # Remove loading label
        self.loading_label.destroy()
        
        # Create header
        header_frame = tk.Frame(self.modules_frame, bg="#1e2329")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="Module Name",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(10, 0))
        
        tk.Label(
            header_frame,
            text="Settings",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10, "bold")
        ).pack(side="right", padx=(0, 120))
        
        tk.Label(
            header_frame,
            text="Enabled",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10, "bold")
        ).pack(side="right", padx=(0, 40))
        
        # Add separator
        ttk.Separator(self.modules_frame, orient="horizontal").pack(fill="x", pady=(0, 10))
        
        if not self.modules:
            # Show no modules message
            tk.Label(
                self.modules_frame,
                text="No modules available",
                bg="#1e2329",
                fg="#8b949e",
                font=("Segoe UI", 11)
            ).pack(pady=10)
            return
        
        # Create module entries
        for module_id, module_info in self.modules.items():
            # Module frame
            module_frame = tk.Frame(self.modules_frame, bg="#1e2329")
            module_frame.pack(fill="x", pady=5)
            
            # Left side - Icon and name
            name_frame = tk.Frame(module_frame, bg="#1e2329")
            name_frame.pack(side="left", padx=10)
            
            tk.Label(
                name_frame,
                text=f"{module_info['icon']} {module_info['name']}",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 11)
            ).pack(side="left")
            
            # Right side - Settings and Enable/Disable
            controls_frame = tk.Frame(module_frame, bg="#1e2329")
            controls_frame.pack(side="right", padx=10)
            
            # Settings button
            settings_btn = tk.Button(
                controls_frame,
                text="⚙",
                bg="#2196f3",
                fg="#ffffff",
                font=("Segoe UI", 10),
                relief="flat",
                bd=0,
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda mid=module_id: self._show_module_settings(mid)
            )
            settings_btn.pack(side="right", padx=(10, 0))
            
            # Enable/Disable checkbox
            enabled_var = tk.BooleanVar(value=self.settings[module_id]["enabled"])
            enabled_check = tk.Checkbutton(
                controls_frame,
                variable=enabled_var,
                bg="#1e2329",
                activebackground="#1e2329",
                selectcolor="#1e2329",
                command=lambda mid=module_id, var=enabled_var: self._toggle_module(mid, var)
            )
            enabled_check.pack(side="right", padx=(0, 30))
            
            # Add separator
            ttk.Separator(self.modules_frame, orient="horizontal").pack(fill="x", pady=(5, 0))
            
        # Save button at bottom
        save_frame = tk.Frame(self.modules_frame, bg="#1e2329")
        save_frame.pack(fill="x", pady=(20, 0))
        
        save_btn = tk.Button(
            save_frame,
            text="✓ Save Changes",
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._save_and_close
        )
        save_btn.pack(side="right")
    
    def _show_module_settings(self, module_id):
        """Show settings dialog for a module"""
        if module_id == "autostart_game":
            settings = self.settings[module_id]
            
            # Create settings dialog
            dialog = tk.Toplevel(self.window)
            dialog.title("AutoStartGame Settings")
            dialog.geometry("400x300")
            dialog.configure(bg="#1e2329")
            dialog.transient(self.window)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"400x300+{x}+{y}")
            
            content = tk.Frame(dialog, bg="#1e2329")
            content.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Auto-startup setting
            auto_startup_var = tk.BooleanVar(value=settings.get("auto_startup", False))
            auto_check = tk.Checkbutton(
                content,
                text="Auto-start on application startup",
                variable=auto_startup_var,
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 10),
                selectcolor="#1e2329",
                activebackground="#1e2329",
                activeforeground="#ffffff"
            )
            auto_check.pack(anchor="w", pady=10)
            
            # Max retries setting
            retry_frame = tk.Frame(content, bg="#1e2329")
            retry_frame.pack(fill="x", pady=10)
            
            tk.Label(
                retry_frame,
                text="Max Retries:",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 10)
            ).pack(side="left")
            
            retry_var = tk.StringVar(value=str(settings.get("max_retries", 3)))
            retry_entry = tk.Entry(
                retry_frame,
                textvariable=retry_var,
                bg="#0a0e16",
                fg="#ffffff",
                font=("Segoe UI", 10),
                width=5
            )
            retry_entry.pack(side="left", padx=10)
            
            # Retry delay setting
            delay_frame = tk.Frame(content, bg="#1e2329")
            delay_frame.pack(fill="x", pady=10)
            
            tk.Label(
                delay_frame,
                text="Retry Delay (seconds):",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 10)
            ).pack(side="left")
            
            delay_var = tk.StringVar(value=str(settings.get("retry_delay", 10)))
            delay_entry = tk.Entry(
                delay_frame,
                textvariable=delay_var,
                bg="#0a0e16",
                fg="#ffffff",
                font=("Segoe UI", 10),
                width=5
            )
            delay_entry.pack(side="left", padx=10)
            
            # Save button
            save_frame = tk.Frame(content, bg="#1e2329")
            save_frame.pack(side="bottom", fill="x", pady=(20, 0))
            
            def save_settings():
                try:
                    self.settings["autostart_game"].update({
                        "auto_startup": auto_startup_var.get(),
                        "max_retries": int(retry_var.get()),
                        "retry_delay": int(delay_var.get())
                    })
                    dialog.destroy()
                except ValueError:
                    pass
            
            save_btn = tk.Button(
                save_frame,
                text="Save",
                bg="#00ff88",
                fg="#000000",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                bd=0,
                padx=20,
                pady=6,
                cursor="hand2",
                command=save_settings
            )
            save_btn.pack(side="right")
            
            cancel_btn = tk.Button(
                save_frame,
                text="Cancel",
                bg="#ff6b6b",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                bd=0,
                padx=20,
                pady=6,
                cursor="hand2",
                command=dialog.destroy
            )
            cancel_btn.pack(side="right", padx=10)
    
    def _toggle_module(self, module_id, enabled_var):
        """Toggle module enabled state"""
        self.settings[module_id]["enabled"] = enabled_var.get()
    
    def _load_settings(self):
        """Load module settings from file"""
        default_settings = {
            "autostart_game": {
                "enabled": True,
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10
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
                    else:
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def _save_and_close(self):
        """Save settings and close window"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            if self.app_ref:
                self.app_ref.add_console_message("✓ Module settings saved")
            
            self.window.destroy()
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _on_closing(self):
        """Handle window closing"""
        self.window.destroy()