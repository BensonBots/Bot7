import tkinter as tk
from tkinter import messagebox
import json
import threading
import weakref

class InstanceCard(tk.Frame):
    def __init__(self, parent, name, status="Offline", cpu_usage=0, memory_usage=0, app_ref=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.name = name
        self.status = status
        self.selected = False
        self.app_ref = weakref.ref(app_ref) if app_ref else None
        self.configure(bg="#1e2329", width=580, height=85)
        self.pack_propagate(False)
        self._setup_ui()
        self._setup_context_menu()
        self._bind_events()
        self.update_status_display(status)
    
    def _setup_ui(self):
        container = tk.Frame(self, bg="#343a46", relief="solid", bd=1)
        container.place(x=0, y=0, relwidth=1, relheight=1)
        content = tk.Frame(container, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=1, pady=1)
        
        left = tk.Frame(content, bg="#1e2329")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        top = tk.Frame(left, bg="#1e2329")
        top.pack(fill="x", pady=(0, 4))
        
        self.selected_var = tk.BooleanVar()
        self.checkbox = tk.Label(top, text="☐", bg="#1e2329", fg="#00d4ff", font=("Segoe UI", 11), cursor="hand2")
        self.checkbox.pack(side="left", padx=(0, 12))
        
        self.name_label = tk.Label(top, text=self.name, bg="#1e2329", fg="#ffffff", font=("Segoe UI", 13, "bold"), anchor="w")
        self.name_label.pack(side="left", fill="x", expand=True)
        
        bottom = tk.Frame(left, bg="#1e2329")
        bottom.pack(fill="x")
        
        self.status_icon = tk.Label(bottom, text=self._get_status_icon(self.status), bg="#1e2329", fg="#8b949e", font=("Segoe UI", 10))
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(bottom, text=self.status, bg="#1e2329", fg="#8b949e", font=("Segoe UI", 10), anchor="w")
        self.status_text.pack(side="left", padx=(8, 0))
        
        buttons = tk.Frame(content, bg="#1e2329")
        buttons.pack(side="right", padx=12, pady=10)
        
        self.start_btn = tk.Button(buttons, text="▶ Start", bg="#00e676", fg="#ffffff", relief="flat", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12, pady=6, command=self._toggle_instance)
        self.start_btn.pack(side="right", padx=(6, 0))
        
        modules_btn = tk.Button(buttons, text="⚙ Modules", bg="#2196f3", fg="#ffffff", relief="flat", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=10, pady=6, command=self._show_modules)
        modules_btn.pack(side="right", padx=(6, 0))
        
        context_btn = tk.Button(buttons, text="⋮", bg="#404040", fg="#ffffff", relief="flat", bd=0, font=("Segoe UI", 12, "bold"), cursor="hand2", width=2, command=self._show_context_menu)
        context_btn.pack(side="right")
    
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2a2a2a", fg="white", bd=0)
        self.context_menu.add_command(label="🎯 Start", command=self._start_instance)
        self.context_menu.add_command(label="⏹ Stop", command=self._stop_instance)
        self.context_menu.add_command(label="🔄 Restart", command=self._restart_instance)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💾 Export", command=self._export_config)
        self.context_menu.add_command(label="🗑 Delete", command=self._delete_instance)
    
    def _bind_events(self):
        for element in [self, self.checkbox, self.name_label, self.status_icon, self.status_text]:
            element.bind("<Button-1>", self._on_click)
            element.bind("<Button-3>", self._on_right_click)
    
    def _on_click(self, event):
        self.toggle_checkbox()
    
    def _on_right_click(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except:
            pass
        finally:
            self.context_menu.grab_release()
    
    def _get_app_ref(self):
        if self.app_ref:
            app = self.app_ref()
            if app:
                return app
        return None
    
    def _toggle_instance(self):
        if self.status == "Running":
            self._stop_instance()
        else:
            self._start_instance()
    
    def _start_instance(self):
        app = self._get_app_ref()
        if app:
            threading.Thread(target=lambda: app.start_instance(self.name), daemon=True).start()
    
    def _stop_instance(self):
        app = self._get_app_ref()
        if app:
            threading.Thread(target=lambda: app.stop_instance(self.name), daemon=True).start()
    
    def _restart_instance(self):
        self._stop_instance()
        self.after(2500, self._start_instance)
    
    def _show_modules(self):
        app = self._get_app_ref()
        if app:
            app.show_modules(self.name)
    
    def _export_config(self):
        config = {"name": self.name, "status": self.status}
        filename = f"{self.name}_config.json"
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Export Complete", f"Config exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed: {str(e)}")
    
    def _delete_instance(self):
        app = self._get_app_ref()
        if app:
            app.delete_instance_card_with_loading(self)
    
    def _show_context_menu(self):
        try:
            x = self.winfo_rootx() + self.winfo_width() - 30
            y = self.winfo_rooty() + 30
            self.context_menu.tk_popup(x, y)
        except:
            pass
        finally:
            self.context_menu.grab_release()
    
    def toggle_checkbox(self):
        current = self.selected_var.get()
        self.selected_var.set(not current)
        self.selected = not current
        
        if self.selected:
            self.checkbox.configure(text="☑", fg="#00ff88")
        else:
            self.checkbox.configure(text="☐", fg="#00d4ff")
        
        app = self._get_app_ref()
        if app and hasattr(app, 'on_card_selection_changed'):
            app.on_card_selection_changed()
    
    def update_status_display(self, new_status):
        colors = {"Running": "#00ff88", "Stopped": "#8b949e", "Offline": "#8b949e", "Starting": "#ffd93d", "Stopping": "#ff9800", "Error": "#ff6b6b"}
        color = colors.get(new_status, "#8b949e")
        icon = self._get_status_icon(new_status)
        self.status_icon.configure(text=icon, fg=color)
        self.status_text.configure(text=new_status, fg=color)
    
    def update_status(self, new_status):
        self.status = new_status
        self.update_status_display(new_status)
        
        if new_status == "Running":
            self.start_btn.configure(text="⏹ Stop", bg="#ff6b6b")
        else:
            self.start_btn.configure(text="▶ Start", bg="#00e676")
    
    def _get_status_icon(self, status):
        icons = {"Running": "✓", "Stopped": "○", "Offline": "○", "Starting": "⚡", "Stopping": "⏹", "Error": "⚠"}
        return icons.get(status, "○")