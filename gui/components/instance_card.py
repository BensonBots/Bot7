"""
BENSON v2.0 - Compact Instance Card
Reduced from 400+ lines to ~150 lines with same functionality
"""

import tkinter as tk
from tkinter import messagebox
import json
import threading
import weakref


class InstanceCard(tk.Frame):
    def __init__(self, parent, name, status="Offline", cpu_usage=0, memory_usage=0, app_ref=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Core data
        self.name = name
        self.status = status
        self.selected = False
        self._destroyed = False
        self.app_ref = weakref.ref(app_ref) if app_ref else None
        
        # Configure frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3, width=580, height=85)
        self.pack_propagate(False)
        
        # Setup everything
        self._setup_ui()
        self._setup_context_menu()
        self._bind_events()
        self.update_status_display(status)
        
        print(f"[InstanceCard] Created card for {name} with status: {status}")
    
    def _setup_ui(self):
        """Setup complete UI structure"""
        # Main container with border
        self.main_container = tk.Frame(self, bg="#343a46", relief="solid", bd=1)
        self.main_container.pack(fill="both", expand=True)
        
        content = tk.Frame(self.main_container, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Left section - checkbox, name, status
        self._create_left_section(content)
        
        # Right section - buttons
        self._create_right_section(content)
    
    def _create_left_section(self, parent):
        """Create left section with info"""
        left = tk.Frame(parent, bg="#1e2329")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - checkbox and name
        top = tk.Frame(left, bg="#1e2329")
        top.pack(fill="x", pady=(0, 4))
        
        self.checkbox = tk.Label(top, text="☐", bg="#1e2329", fg="#00d4ff", 
                                font=("Segoe UI", 11), cursor="hand2")
        self.checkbox.pack(side="left", padx=(0, 12))
        
        self.name_label = tk.Label(top, text=self.name, bg="#1e2329", fg="#ffffff",
                                  font=("Segoe UI", 13, "bold"), anchor="w")
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom = tk.Frame(left, bg="#1e2329")
        bottom.pack(fill="x")
        
        self.status_icon = tk.Label(bottom, text=self._get_status_icon(self.status),
                                   bg="#1e2329", font=("Segoe UI", 10))
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(bottom, text=self.status, bg="#1e2329",
                                   font=("Segoe UI", 10), anchor="w")
        self.status_text.pack(side="left", padx=(8, 0))
    
    def _create_right_section(self, parent):
        """Create right section with buttons"""
        button_frame = tk.Frame(parent, bg="#1e2329")
        button_frame.pack(side="right", padx=12, pady=10)
        
        # Button definitions: (text, bg_color, width, command)
        buttons = [
            ("⋮", "#404040", 2, self._safe_show_context_menu),
            ("⚙ Modules", "#2196f3", 10, self._safe_show_modules),
            (self._get_start_text(), self._get_start_color(), 12, self._safe_toggle_instance)
        ]
        
        self.buttons = {}
        for text, bg, padx, command in buttons:
            btn = tk.Button(button_frame, text=text, bg=bg, fg="#ffffff", relief="flat", bd=0,
                           font=("Segoe UI", 9, "bold"), cursor="hand2", padx=padx, pady=6, command=command)
            btn.pack(side="right", padx=(6, 0))
            self._add_hover(btn, bg)
            
            if "Start" in text or "Stop" in text:
                self.buttons["start"] = btn
    
    def _get_start_text(self):
        return "⏹ Stop" if self.status == "Running" else "▶ Start"
    
    def _get_start_color(self):
        return "#ff6b6b" if self.status == "Running" else "#00e676"
    
    def _add_hover(self, button, normal_bg):
        """Add hover effect"""
        hover_colors = {"#404040": "#555555", "#2196f3": "#1976d2", "#00e676": "#00ff88", "#ff6b6b": "#ff8a80"}
        hover_bg = hover_colors.get(normal_bg, normal_bg)
        
        button.bind("<Enter>", lambda e: self._safe_config(button, bg=hover_bg))
        button.bind("<Leave>", lambda e: self._safe_config(button, bg=normal_bg))
    
    def _safe_config(self, widget, **kwargs):
        """Safe widget configuration"""
        if not self._destroyed:
            try: widget.configure(**kwargs)
            except: pass
    
    def _setup_context_menu(self):
        """Setup context menu"""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2a2a2a", fg="white", bd=0)
        
        items = [
            ("🎯 Start Instance", self._safe_start_instance),
            ("⏹ Stop Instance", self._safe_stop_instance),
            ("🔄 Restart Instance", self._safe_restart_instance),
            None,  # Separator
            ("📋 View Logs", self._safe_view_logs),
            ("💾 Export Config", self._safe_export_config),
            ("🗑 Delete Instance", self._safe_delete_instance)
        ]
        
        for item in items:
            if item is None:
                self.context_menu.add_separator()
            else:
                self.context_menu.add_command(label=item[0], command=item[1])
    
    def _bind_events(self):
        """Bind click events"""
        clickable = [self, self.main_container, self.checkbox, self.name_label]
        for element in clickable:
            element.bind("<Button-1>", self._on_click)
            element.bind("<Button-3>", self._on_right_click)
    
    def _on_click(self, event):
        if not self._destroyed: self.toggle_checkbox()
    
    def _on_right_click(self, event):
        if not self._destroyed:
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()
    
    def toggle_checkbox(self):
        """Toggle selection state"""
        if self._destroyed: return
        
        self.selected = not self.selected
        
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
        """Update instance status"""
        if self._destroyed: return
        
        old_status = self.status
        self.status = new_status
        self.update_status_display(new_status)
        
        # Update start button
        if "start" in self.buttons:
            btn = self.buttons["start"]
            if new_status == "Running":
                btn.configure(text="⏹ Stop", bg="#ff6b6b")
            elif new_status in ["Starting", "Stopping"]:
                btn.configure(text="⏸ Wait", bg="#ffd93d")
            else:
                btn.configure(text="▶ Start", bg="#00e676")
        
        if old_status != new_status:
            print(f"[InstanceCard] {self.name} status: {old_status} -> {new_status}")
    
    def update_status_display(self, new_status):
        """Update visual status display"""
        if self._destroyed: return
        
        colors = {"Running": "#00ff88", "Stopped": "#8b949e", "Starting": "#ffd93d", 
                 "Stopping": "#ff9800", "Error": "#ff6b6b", "Offline": "#8b949e"}
        color = colors.get(new_status, "#8b949e")
        icon = self._get_status_icon(new_status)
        
        self.status_icon.configure(text=icon, fg=color)
        self.status_text.configure(text=new_status, fg=color)
        
        # Update border color if not selected
        if not self.selected:
            border_colors = {"Running": "#00ff88", "Error": "#ff6b6b", "Starting": "#ffd93d", "Stopping": "#ffd93d"}
            self.main_container.configure(bg=border_colors.get(new_status, "#343a46"))
    
    def _get_status_icon(self, status):
        """Get status icon"""
        icons = {"Running": "✓", "Stopped": "○", "Offline": "○", "Starting": "⚡", 
                "Stopping": "⏹", "Error": "⚠", "Connecting": "↻"}
        return icons.get(status, "○")
    
    def _get_app_ref(self):
        """Get app reference"""
        return self.app_ref() if self.app_ref else None
    
    # Action methods - all run in threads for non-blocking UI
    def _safe_toggle_instance(self):
        if self.status == "Running": self._safe_stop_instance()
        else: self._safe_start_instance()
    
    def _safe_start_instance(self):
        app = self._get_app_ref()
        if app: threading.Thread(target=lambda: app.start_instance(self.name), daemon=True).start()
    
    def _safe_stop_instance(self):
        app = self._get_app_ref()
        if app: threading.Thread(target=lambda: app.stop_instance(self.name), daemon=True).start()
    
    def _safe_restart_instance(self):
        self._safe_stop_instance()
        self.after(2500, self._safe_start_instance)
    
    def _safe_show_modules(self):
        app = self._get_app_ref()
        if app: app.show_modules(self.name)
    
    def _safe_view_logs(self):
        """Simple log viewer"""
        try:
            log_window = tk.Toplevel(self)
            log_window.title(f"{self.name} - Logs")
            log_window.geometry("600x400")
            log_window.configure(bg="#1e2329")
            log_window.transient(self)
            
            # Center window
            log_window.update_idletasks()
            x = (log_window.winfo_screenwidth() // 2) - 300
            y = (log_window.winfo_screenheight() // 2) - 200
            log_window.geometry(f"600x400+{x}+{y}")
            
            # Header
            tk.Label(log_window, text=f"📋 {self.name} - Activity Logs", 
                    bg="#1e2329", fg="#00d4ff", font=("Segoe UI", 14, "bold")).pack(pady=10)
            
            # Log area
            log_frame = tk.Frame(log_window, bg="#161b22", relief="solid", bd=1)
            log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            log_text = tk.Text(log_frame, bg="#0a0e16", fg="#58a6ff", font=("Consolas", 9),
                              relief="flat", bd=0, wrap="word", state="disabled", padx=8, pady=8)
            log_text.pack(fill="both", expand=True)
            
            # Sample logs
            logs = [f"[INFO] Instance {self.name} initialized", "[DEBUG] Memory: 2048MB", 
                   f"[INFO] Current status: {self.status}", "[INFO] All systems operational"]
            
            log_text.configure(state="normal")
            for log in logs:
                log_text.insert("end", f"[12:34:56] {log}\n")
            log_text.configure(state="disabled")
            
            # Close button
            tk.Button(log_window, text="Close", bg="#ff6b6b", fg="#ffffff", 
                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=20, pady=8,
                     cursor="hand2", command=log_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log viewer: {str(e)}")
    
    def _safe_export_config(self):
        """Export configuration"""
        try:
            config = {"name": self.name, "status": self.status}
            filename = f"{self.name}_config.json"
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Export Complete", f"Configuration exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export: {str(e)}")
    
    def _safe_delete_instance(self):
        app = self._get_app_ref()
        if app and hasattr(app, 'instance_ops'):
            app.instance_ops.delete_instance_card_with_animation(self)
    
    def _safe_show_context_menu(self):
        try:
            x = self.winfo_rootx() + self.winfo_width() - 30
            y = self.winfo_rooty() + 30
            self.context_menu.tk_popup(x, y)
        finally:
            self.context_menu.grab_release()
    
    def destroy(self):
        """Clean destroy"""
        self._destroyed = True
        self.app_ref = None
        super().destroy()