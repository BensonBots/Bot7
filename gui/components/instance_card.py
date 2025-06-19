"""
BENSON v2.0 - Instance Card Component (FIXED)
Fixed status display and button state issues
"""

import tkinter as tk
from tkinter import messagebox
import json
import threading
import weakref


class InstanceCard(tk.Frame):
    def __init__(self, parent, name, status="Offline", cpu_usage=0, memory_usage=0, app_ref=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Core instance data
        self.name = name
        self.status = status
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.selected = False
        self._destroyed = False
        self.app_ref = weakref.ref(app_ref) if app_ref else None
        
        # Configure main frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3)
        self.configure(width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI and events
        self._setup_ui()
        self._setup_context_menu()
        self._bind_events()
        
        # FIXED: Set initial status correctly
        self.update_status_display(status)
        print(f"[InstanceCard] Created card for {name} with status: {status}")
    
    def _setup_ui(self):
        """Setup complete UI structure efficiently"""
        # Main container with clean borders
        self.main_container = tk.Frame(self, bg="#343a46", relief="solid", bd=1)
        self.main_container.pack(fill="both", expand=True)
        
        self.content_frame = tk.Frame(self.main_container, bg="#1e2329")
        self.content_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Left side - info section
        left_frame = tk.Frame(self.content_frame, bg="#1e2329")
        left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - checkbox and name
        top_row = tk.Frame(left_frame, bg="#1e2329")
        top_row.pack(fill="x", pady=(0, 4))
        
        self.selected_var = tk.BooleanVar()
        self.checkbox = tk.Label(top_row, text="☐", bg="#1e2329", fg="#00d4ff", 
                                font=("Segoe UI", 11), cursor="hand2")
        self.checkbox.pack(side="left", padx=(0, 12))
        
        self.name_label = tk.Label(top_row, text=self.name, bg="#1e2329", fg="#ffffff",
                                  font=("Segoe UI", 13, "bold"), anchor="w")
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom_row = tk.Frame(left_frame, bg="#1e2329")
        bottom_row.pack(fill="x")
        
        self.status_icon = tk.Label(bottom_row, text=self._get_status_icon(self.status),
                                   bg="#1e2329", font=("Segoe UI", 10))
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(bottom_row, text=self.status, bg="#1e2329",
                                   font=("Segoe UI", 10), anchor="w")
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Right side - buttons
        self._setup_buttons()
    
    def _setup_buttons(self):
        """FIXED: Setup action buttons with correct initial states"""
        button_frame = tk.Frame(self.content_frame, bg="#1e2329")
        button_frame.pack(side="right", padx=12, pady=10)
        
        # Context menu button
        context_btn = tk.Button(button_frame, text="⋮", bg="#404040", fg="#ffffff", relief="flat", bd=0,
                               font=("Segoe UI", 12, "bold"), cursor="hand2", width=2,
                               command=self._safe_show_context_menu)
        context_btn.pack(side="right", padx=(0, 6))
        
        # Modules button
        modules_btn = tk.Button(button_frame, text="⚙ Modules", bg="#2196f3", fg="#ffffff", relief="flat", bd=0,
                               font=("Segoe UI", 9, "bold"), cursor="hand2", padx=10, pady=6,
                               command=self._safe_show_modules)
        modules_btn.pack(side="right", padx=(6, 0))
        
        # FIXED: Start/Stop button with correct initial state based on actual status
        if self.status == "Running":
            initial_text = "⏹ Stop"
            initial_bg = "#ff6b6b"
        else:  # Stopped, Offline, etc.
            initial_text = "▶ Start"
            initial_bg = "#00e676"
        
        self.start_btn = tk.Button(button_frame, text=initial_text, bg=initial_bg, fg="#ffffff", relief="flat", bd=0,
                                  font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12, pady=6,
                                  command=self._safe_toggle_instance)
        self.start_btn.pack(side="right", padx=(6, 0))
        
        print(f"[InstanceCard] {self.name} button initialized: {initial_text} (status: {self.status})")
        
        # Add simple hover effects
        self._add_simple_hover_effects([context_btn, modules_btn, self.start_btn])
    
    def _setup_context_menu(self):
        """Setup context menu"""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2a2a2a", fg="white", bd=0)
        context_items = [
            ("🎯 Start Instance", self._safe_start_instance),
            ("⏹ Stop Instance", self._safe_stop_instance),
            ("🔄 Restart Instance", self._safe_restart_instance),
            None,
            ("📋 View Logs", self._safe_view_logs),
            ("💾 Export Config", self._safe_export_config),
            ("🗑 Delete Instance", self._safe_delete_instance)
        ]
        
        for item in context_items:
            if item is None:
                self.context_menu.add_separator()
            else:
                self.context_menu.add_command(label=item[0], command=item[1])
    
    def _bind_events(self):
        """Bind essential events"""
        clickable = [self, self.main_container, self.content_frame, self.checkbox, self.name_label]
        for element in clickable:
            element.bind("<Button-1>", self._on_click)
            element.bind("<Button-3>", self._on_right_click)
    
    def _add_simple_hover_effects(self, buttons):
        """Add simple hover effects without causing display issues"""
        hover_colors = {
            "#404040": "#555555", 
            "#2196f3": "#1976d2", 
            "#00e676": "#00c853", 
            "#ff6b6b": "#f44336",
            "#ffd93d": "#ffcc02"
        }
        
        for button in buttons:
            original_color = button.cget("bg")
            hover_color = hover_colors.get(original_color, original_color)
            
            def on_enter(e, btn=button, color=hover_color):
                try:
                    btn.configure(bg=color)
                except tk.TclError:
                    pass
            
            def on_leave(e, btn=button, color=original_color):
                try:
                    btn.configure(bg=color)
                except tk.TclError:
                    pass
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
    
    # Event handlers
    def _on_click(self, event):
        if not self._destroyed:
            self.toggle_checkbox()
    
    def _on_right_click(self, event):
        if not self._destroyed:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    # Core functionality
    def toggle_checkbox(self):
        """Toggle selection state"""
        if self._destroyed:
            return
        
        self.selected = not self.selected
        self.selected_var.set(self.selected)
        
        if self.selected:
            self.checkbox.configure(text="☑", fg="#00ff88")
            self.main_container.configure(bg="#00d4ff")
        else:
            self.checkbox.configure(text="☐", fg="#00d4ff")
            self.main_container.configure(bg="#343a46")
        
        # Notify parent
        app = self._get_app_ref()
        if app and hasattr(app, 'on_card_selection_changed'):
            app.on_card_selection_changed()
    
    def update_status(self, new_status):
        """FIXED: Update instance status with proper button state synchronization"""
        if self._destroyed:
            return
        
        old_status = self.status
        self.status = new_status
        
        # Update visual display first
        self.update_status_display(new_status)
        
        # FIXED: Update start button to match the actual status
        if new_status == "Running":
            self.start_btn.configure(text="⏹ Stop", bg="#ff6b6b")
        elif new_status in ["Starting", "Stopping"]:
            self.start_btn.configure(text="⏸ Wait", bg="#ffd93d")
        else:  # Stopped, Offline, Error, etc.
            self.start_btn.configure(text="▶ Start", bg="#00e676")
        
        # Log status changes for debugging
        if old_status != new_status:
            print(f"[InstanceCard] {self.name} status updated: {old_status} -> {new_status}")
            print(f"[InstanceCard] {self.name} button now: {self.start_btn.cget('text')}")
    
    def update_status_display(self, new_status):
        """FIXED: Update visual status display with correct colors and icons"""
        if self._destroyed:
            return
        
        # Status color mapping - accurate colors for each status
        colors = {
            "Running": "#00ff88",      # Bright green for running
            "Stopped": "#8b949e",      # Gray for stopped
            "Offline": "#8b949e",      # Gray for offline
            "Starting": "#ffd93d",     # Yellow for starting
            "Stopping": "#ff9800",     # Orange for stopping
            "Error": "#ff6b6b"         # Red for error
        }
        
        color = colors.get(new_status, "#8b949e")
        icon = self._get_status_icon(new_status)
        
        # Update status display elements
        self.status_icon.configure(text=icon, fg=color)
        self.status_text.configure(text=new_status, fg=color)
        
        # Update card border based on status (if not selected)
        if not self.selected:
            border_colors = {
                "Running": "#00ff88",
                "Error": "#ff6b6b", 
                "Starting": "#ffd93d",
                "Stopping": "#ffd93d"
            }
            
            border_color = border_colors.get(new_status, "#343a46")
            self.main_container.configure(bg=border_color)
    
    # Safe action wrappers
    def _get_app_ref(self):
        return self.app_ref() if self.app_ref else None
    
    def _safe_toggle_instance(self):
        """Toggle instance based on current status"""
        if self.status == "Running":
            self._safe_stop_instance()
        else:
            self._safe_start_instance()
    
    def _safe_start_instance(self):
        app = self._get_app_ref()
        if app:
            threading.Thread(target=lambda: app.start_instance(self.name), daemon=True).start()
    
    def _safe_stop_instance(self):
        app = self._get_app_ref()
        if app:
            threading.Thread(target=lambda: app.stop_instance(self.name), daemon=True).start()
    
    def _safe_restart_instance(self):
        self._safe_stop_instance()
        self.after(2500, self._safe_start_instance)
    
    def _safe_show_modules(self):
        app = self._get_app_ref()
        if app:
            app.show_modules(self.name)
    
    def _safe_view_logs(self):
        """Simple log viewer replacement"""
        try:
            # Create a simple log display dialog
            log_window = tk.Toplevel(self)
            log_window.title(f"{self.name} - Logs")
            log_window.geometry("600x400")
            log_window.configure(bg="#1e2329")
            log_window.transient(self)
            
            # Center the window
            log_window.update_idletasks()
            x = (log_window.winfo_screenwidth() // 2) - (300)
            y = (log_window.winfo_screenheight() // 2) - (200)
            log_window.geometry(f"600x400+{x}+{y}")
            
            # Title
            tk.Label(log_window, text=f"📋 {self.name} - Activity Logs", 
                    bg="#1e2329", fg="#00d4ff", font=("Segoe UI", 14, "bold")).pack(pady=10)
            
            # Log text area
            log_frame = tk.Frame(log_window, bg="#161b22", relief="solid", bd=1)
            log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            log_text = tk.Text(log_frame, bg="#0a0e16", fg="#58a6ff", font=("Consolas", 9),
                              relief="flat", bd=0, wrap="word", state="disabled", padx=8, pady=8)
            log_text.pack(fill="both", expand=True)
            
            # Add sample log entries
            sample_logs = [
                f"[INFO] Instance {self.name} initialized successfully",
                "[DEBUG] Memory allocation: 2048MB", 
                "[INFO] Network interface configured",
                "[DEBUG] Graphics driver loaded",
                "[INFO] Android system booted",
                f"[INFO] {self.name} ready for user interaction",
                f"[DEBUG] Current status: {self.status}",
                "[INFO] All systems operational"
            ]
            
            log_text.configure(state="normal")
            for log_entry in sample_logs:
                timestamp = "[12:34:56]"
                log_text.insert("end", f"{timestamp} {log_entry}\n")
            log_text.configure(state="disabled")
            
            # Close button
            tk.Button(log_window, text="Close", bg="#ff6b6b", fg="#ffffff", 
                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=20, pady=8,
                     cursor="hand2", command=log_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log viewer: {str(e)}")
    
    def _safe_export_config(self):
        try:
            config = {
                "name": self.name, 
                "status": self.status, 
                "cpu": self.cpu_usage, 
                "memory": self.memory_usage
            }
            filename = f"{self.name}_config.json"
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Export Complete", f"Configuration exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export config: {str(e)}")
    
    def _safe_delete_instance(self):
        app = self._get_app_ref()
        if app:
            app.delete_instance_card_with_loading(self)
    
    def _safe_show_context_menu(self):
        try:
            x = self.winfo_rootx() + self.winfo_width() - 30
            y = self.winfo_rooty() + 30
            self.context_menu.tk_popup(x, y)
        finally:
            self.context_menu.grab_release()
    
    # Utility methods
    def _get_status_icon(self, status):
        """FIXED: Get appropriate icon for each status"""
        icons = {
            "Running": "✓",         # Checkmark for running
            "Stopped": "○",         # Circle for stopped
            "Offline": "○",         # Circle for offline
            "Starting": "⚡",        # Lightning for starting
            "Stopping": "⏹",        # Stop symbol for stopping
            "Error": "⚠",          # Warning for error
            "Connecting": "↻"       # Refresh for connecting
        }
        return icons.get(status, "○")
    
    def destroy(self):
        """Clean destroy with proper cleanup"""
        self._destroyed = True
        self.app_ref = None
        super().destroy()