"""
BENSON v2.0 - Enhanced Instance Card Component with Smooth Hover Effects
Fixed status display and button state issues + Added beautiful hover animations
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
        
        # Hover state tracking
        self.is_hovering = False
        self.hover_animation_id = None
        
        # Configure main frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3)
        self.configure(width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI and events
        self._setup_ui()
        self._setup_context_menu()
        self._bind_events()
        
        # Set initial status correctly
        self.update_status_display(status)
        print(f"[InstanceCard] Created card for {name} with status: {status}")
    
    def _setup_ui(self):
        """Setup complete UI structure with hover-ready elements"""
        # Main container with clean borders and shadow
        self.shadow_frame = tk.Frame(self, bg="#000000", relief="flat", bd=0)
        self.shadow_frame.place(x=2, y=2, relwidth=1, relheight=1)
        
        self.main_container = tk.Frame(self, bg="#343a46", relief="solid", bd=1)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
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
        """Setup action buttons with enhanced hover effects"""
        button_frame = tk.Frame(self.content_frame, bg="#1e2329")
        button_frame.pack(side="right", padx=12, pady=10)
        
        # Context menu button with enhanced hover
        self.context_btn = tk.Button(
            button_frame, 
            text="⋮", 
            bg="#404040", 
            fg="#ffffff", 
            relief="flat", 
            bd=0,
            font=("Segoe UI", 12, "bold"), 
            cursor="hand2", 
            width=2,
            command=self._safe_show_context_menu
        )
        self.context_btn.pack(side="right", padx=(0, 6))
        
        # Modules button with enhanced hover
        self.modules_btn = tk.Button(
            button_frame, 
            text="⚙ Modules", 
            bg="#2196f3", 
            fg="#ffffff", 
            relief="flat", 
            bd=0,
            font=("Segoe UI", 9, "bold"), 
            cursor="hand2", 
            padx=10, 
            pady=6,
            command=self._safe_show_modules
        )
        self.modules_btn.pack(side="right", padx=(6, 0))
        
        # Start/Stop button with correct initial state based on actual status
        if self.status == "Running":
            initial_text = "⏹ Stop"
            initial_bg = "#ff6b6b"
        else:  # Stopped, Offline, etc.
            initial_text = "▶ Start"
            initial_bg = "#00e676"
        
        self.start_btn = tk.Button(
            button_frame, 
            text=initial_text, 
            bg=initial_bg, 
            fg="#ffffff", 
            relief="flat", 
            bd=0,
            font=("Segoe UI", 9, "bold"), 
            cursor="hand2", 
            padx=12, 
            pady=6,
            command=self._safe_toggle_instance
        )
        self.start_btn.pack(side="right", padx=(6, 0))
        
        print(f"[InstanceCard] {self.name} button initialized: {initial_text} (status: {self.status})")
        
        # Add enhanced hover effects to all buttons
        self._add_enhanced_hover_effects()
    
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
        """Bind events including enhanced hover effects"""
        # Clickable elements
        clickable = [self, self.main_container, self.content_frame, self.checkbox, self.name_label]
        for element in clickable:
            element.bind("<Button-1>", self._on_click)
            element.bind("<Button-3>", self._on_right_click)
        
        # Enhanced hover effects for the entire card
        hover_elements = [self, self.main_container, self.content_frame, self.checkbox, 
                         self.name_label, self.status_icon, self.status_text]
        
        for element in hover_elements:
            element.bind("<Enter>", self._on_hover_enter)
            element.bind("<Leave>", self._on_hover_leave)
    
    def _add_enhanced_hover_effects(self):
        """Add smooth hover effects with color transitions"""
        buttons = [
            (self.context_btn, "#404040", "#555555", "#606060"),
            (self.modules_btn, "#2196f3", "#42a5f5", "#1976d2"),
            (self.start_btn, None, None, None)  # Dynamic colors based on state
        ]
        
        for button, normal_color, hover_color, click_color in buttons:
            # Special handling for start button (dynamic colors)
            if button == self.start_btn:
                self._add_start_button_hover_effects()
            else:
                self._add_button_hover_effect(button, normal_color, hover_color, click_color)
    
    def _add_button_hover_effect(self, button, normal_color, hover_color, click_color):
        """Add smooth hover effect to a specific button"""
        def on_enter(e):
            if not self._destroyed:
                try:
                    button.configure(bg=hover_color)
                    # Subtle scale effect simulation with relief
                    button.configure(relief="raised", bd=1)
                except tk.TclError:
                    pass
        
        def on_leave(e):
            if not self._destroyed:
                try:
                    button.configure(bg=normal_color, relief="flat", bd=0)
                except tk.TclError:
                    pass
        
        def on_click(e):
            if not self._destroyed:
                try:
                    button.configure(bg=click_color)
                    # Reset after click
                    button.after(100, lambda: button.configure(bg=normal_color) if not self._destroyed else None)
                except tk.TclError:
                    pass
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)
    
    def _add_start_button_hover_effects(self):
        """Add special hover effects for start/stop button"""
        def on_enter(e):
            if not self._destroyed:
                try:
                    current_bg = self.start_btn.cget("bg")
                    current_text = self.start_btn.cget("text")
                    
                    if "Start" in current_text:
                        # Start button hover - brighter green
                        self.start_btn.configure(bg="#00ff88", relief="raised", bd=1)
                    else:
                        # Stop button hover - brighter red
                        self.start_btn.configure(bg="#ff8a80", relief="raised", bd=1)
                except tk.TclError:
                    pass
        
        def on_leave(e):
            if not self._destroyed:
                try:
                    current_text = self.start_btn.cget("text")
                    
                    if "Start" in current_text:
                        self.start_btn.configure(bg="#00e676", relief="flat", bd=0)
                    else:
                        self.start_btn.configure(bg="#ff6b6b", relief="flat", bd=0)
                except tk.TclError:
                    pass
        
        def on_click(e):
            if not self._destroyed:
                try:
                    current_text = self.start_btn.cget("text")
                    
                    if "Start" in current_text:
                        self.start_btn.configure(bg="#00c853")
                    else:
                        self.start_btn.configure(bg="#f44336")
                    
                    # Reset after 150ms
                    def reset_color():
                        if not self._destroyed:
                            try:
                                current_text = self.start_btn.cget("text")
                                if "Start" in current_text:
                                    self.start_btn.configure(bg="#00e676")
                                else:
                                    self.start_btn.configure(bg="#ff6b6b")
                            except tk.TclError:
                                pass
                    
                    self.start_btn.after(150, reset_color)
                except tk.TclError:
                    pass
        
        self.start_btn.bind("<Enter>", on_enter)
        self.start_btn.bind("<Leave>", on_leave)
        self.start_btn.bind("<Button-1>", on_click)
    
    # Enhanced hover effects for the card
    def _on_hover_enter(self, event):
        """Enhanced hover enter with smooth animation"""
        if self._destroyed or self.selected:
            return
        
        self.is_hovering = True
        
        try:
            # Smooth color transition
            self._animate_hover_in()
            
            # Subtle shadow enhancement
            self.shadow_frame.configure(bg="#111111")
            
            # Slight glow effect on border
            self.main_container.configure(bg="#404856")
            
        except tk.TclError:
            pass
    
    def _on_hover_leave(self, event):
        """Enhanced hover leave with smooth animation"""
        if self._destroyed or self.selected:
            return
        
        self.is_hovering = False
        
        try:
            # Smooth color transition back
            self._animate_hover_out()
            
            # Reset shadow
            self.shadow_frame.configure(bg="#000000")
            
            # Reset border based on status
            if self.status == "Running":
                self.main_container.configure(bg="#00ff88")
            elif self.status == "Error":
                self.main_container.configure(bg="#ff6b6b")
            elif self.status in ["Starting", "Stopping"]:
                self.main_container.configure(bg="#ffd93d")
            else:
                self.main_container.configure(bg="#343a46")
                
        except tk.TclError:
            pass
    
    def _animate_hover_in(self):
        """Animate background color change on hover enter"""
        if self._destroyed or not self.is_hovering:
            return
        
        # Color progression for smooth transition
        colors = ["#1e2329", "#252932", "#2a2f3b", "#2f3544"]
        self._animate_colors(colors, 0, self._update_hover_backgrounds)
    
    def _animate_hover_out(self):
        """Animate background color change on hover leave"""
        if self._destroyed or self.is_hovering:
            return
        
        # Color progression back to normal
        colors = ["#2f3544", "#2a2f3b", "#252932", "#1e2329"]
        self._animate_colors(colors, 0, self._update_hover_backgrounds)
    
    def _animate_colors(self, colors, index, callback):
        """Generic color animation helper"""
        if self._destroyed or index >= len(colors):
            return
        
        if callback:
            callback(colors[index])
        
        # Schedule next color
        self.after(30, lambda: self._animate_colors(colors, index + 1, callback))
    
    def _update_hover_backgrounds(self, color):
        """Update background colors during hover animation"""
        try:
            if not self._destroyed and not self.selected:
                self.content_frame.configure(bg=color)
                # Update child backgrounds
                self._update_child_backgrounds(color)
        except tk.TclError:
            pass
    
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
        """Toggle selection state with enhanced visual feedback"""
        if self._destroyed:
            return
        
        self.selected = not self.selected
        self.selected_var.set(self.selected)
        
        if self.selected:
            self.checkbox.configure(text="☑", fg="#00ff88")
            self.main_container.configure(bg="#00d4ff")
            self.shadow_frame.configure(bg="#004466")
            
            # Selected state background
            self.content_frame.configure(bg="#1a2838")
            self._update_child_backgrounds("#1a2838")
            
            # Pulse animation for selection
            self._animate_selection_pulse()
            
        else:
            self.checkbox.configure(text="☐", fg="#00d4ff")
            
            # Reset to status-based colors
            if self.status == "Running":
                self.main_container.configure(bg="#00ff88")
            elif self.status == "Error":
                self.main_container.configure(bg="#ff6b6b")
            elif self.status in ["Starting", "Stopping"]:
                self.main_container.configure(bg="#ffd93d")
            else:
                self.main_container.configure(bg="#343a46")
            
            self.shadow_frame.configure(bg="#000000")
            self.content_frame.configure(bg="#1e2329")
            self._update_child_backgrounds("#1e2329")
        
        # Notify parent
        app = self._get_app_ref()
        if app and hasattr(app, 'on_card_selection_changed'):
            app.on_card_selection_changed()
    
    def _animate_selection_pulse(self):
        """Pulse animation when selected"""
        if not self.selected or self._destroyed:
            return
        
        def pulse_step(step=0):
            if not self.selected or self._destroyed or step > 6:
                return
            
            try:
                pulse_colors = ["#00d4ff", "#0099cc", "#00d4ff"]
                color = pulse_colors[step % len(pulse_colors)]
                self.main_container.configure(bg=color)
                
                self.after(100, lambda: pulse_step(step + 1))
            except tk.TclError:
                pass
        
        pulse_step()
    
    def update_status(self, new_status):
        """Update instance status with proper button state synchronization"""
        if self._destroyed:
            return
        
        old_status = self.status
        self.status = new_status
        
        # Update visual display first
        self.update_status_display(new_status)
        
        # Update start button to match the actual status
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
        """Update visual status display with correct colors and icons"""
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
        """Get appropriate icon for each status"""
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
    
    def _update_child_backgrounds(self, color):
        """Update child element backgrounds recursively"""
        if self._destroyed:
            return
        
        def update_recursive(widget):
            try:
                if hasattr(widget, 'configure') and 'bg' in widget.configure():
                    # Skip buttons to preserve their colors
                    if not isinstance(widget, tk.Button):
                        widget.configure(bg=color)
                
                for child in widget.winfo_children():
                    if not isinstance(child, (tk.Button, tk.Canvas)):  # Preserve button colors
                        update_recursive(child)
            except tk.TclError:
                pass
        
        try:
            update_recursive(self.content_frame)
        except tk.TclError:
            pass
    
    def destroy(self):
        """Clean destroy with proper cleanup"""
        self._destroyed = True
        self.app_ref = None
        
        # Cancel any pending animations
        if self.hover_animation_id:
            try:
                self.after_cancel(self.hover_animation_id)
            except:
                pass
        
        super().destroy()