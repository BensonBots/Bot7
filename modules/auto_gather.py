"""
BENSON v2.0 - Improved AutoGather Settings with Custom Resource Loop
Allows easy customization of resource gathering order with duplicates
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class ImprovedModuleSettings:
    """Enhanced module settings with custom resource loop editor"""
    
    def __init__(self, parent, instance_name, app_ref=None):
        self.parent = parent
        self.instance_name = instance_name
        self.app_ref = app_ref
        self.instance_running = self._check_instance_running()
        self.settings_file = f"settings_{instance_name}.json"
        self.settings = self._load_settings()
        self.current_module = "autostart_game"
        
        # Variables for form inputs
        self.form_vars = {}
        
        # Resource loop management
        self.resource_loop = []
        self.loop_listbox = None
        self.available_resources = [
            {"id": "food", "name": "🌾 Food", "color": "#4caf50"},
            {"id": "wood", "name": "🪵 Wood", "color": "#8bc34a"},
            {"id": "iron", "name": "⛏️ Iron", "color": "#607d8b"},
            {"id": "stone", "name": "🗿 Stone", "color": "#795548"}
        ]
        
        # Create window and setup UI
        self._create_window()
        self._setup_complete_ui()
        self._show_module_settings("autostart_game")
    
    def _check_instance_running(self):
        """Check if instance is running"""
        try:
            if self.app_ref:
                instance = self.app_ref.instance_manager.get_instance(self.instance_name)
                return instance and instance["status"] == "Running"
        except:
            pass
        return False
    
    def _create_window(self):
        """Create main window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Modules - {self.instance_name}")
        self.window.geometry("1000x700")  # Increased size for better layout
        self.window.configure(bg="#0f0f23")
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.resizable(True, True)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 500
        y = (self.window.winfo_screenheight() // 2) - 350
        self.window.geometry(f"1000x700+{x}+{y}")
    
    def _setup_complete_ui(self):
        """Setup complete UI"""
        # Header
        header = tk.Frame(self.window, bg="#1a1a3a", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg="#1a1a3a")
        header_content.pack(fill="both", expand=True, padx=15, pady=10)
        
        tk.Label(header_content, text=f"⚙️ {self.instance_name} Modules", bg="#1a1a3a", fg="#ffffff",
                font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Status indicator
        status_color = "#4caf50" if self.instance_running else "#757575"
        status_text = "Running" if self.instance_running else "Stopped"
        tk.Label(header_content, text=f"● {status_text}", bg="#1a1a3a", fg=status_color,
                font=("Segoe UI", 10, "bold")).pack(side="left", padx=(20, 0))
        
        # Close button
        close_btn = tk.Button(header_content, text="✕", bg="#1a1a3a", fg="#ff5252", relief="flat", bd=0,
                             font=("Segoe UI", 14, "bold"), cursor="hand2", width=2, command=self._close_window)
        close_btn.pack(side="right")
        
        # Main container
        main_container = tk.Frame(self.window, bg="#0f0f23")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Sidebar and content
        self._setup_sidebar_and_content(main_container)
        
        # Footer
        self._setup_footer()
    
    def _setup_sidebar_and_content(self, parent):
        """Setup sidebar and content areas"""
        # Sidebar
        sidebar = tk.Frame(parent, bg="#1a1a3a", width=220, relief="solid", bd=1)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Sidebar header
        header_frame = tk.Frame(sidebar, bg="#2d2d5a", height=35)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🔧 Modules", bg="#2d2d5a", fg="#ffffff",
                font=("Segoe UI", 12, "bold")).pack(pady=8)
        
        # Module list
        self._create_module_list(sidebar)
        
        # Content area
        self.content_area = tk.Frame(parent, bg="#1a1a3a", relief="solid", bd=1)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Content header
        self.content_header = tk.Frame(self.content_area, bg="#2d2d5a", height=40)
        self.content_header.pack(fill="x")
        self.content_header.pack_propagate(False)
        
        # Scrollable content
        self._setup_scrollable_content()
    
    def _create_module_list(self, parent):
        """Create module list with toggles"""
        # Module definitions
        self.modules = [
            {"id": "autostart_game", "name": "AutoStart", "icon": "🎮", "color": "#4caf50", "required": True},
            {"id": "auto_gather", "name": "AutoGather", "icon": "⛏️", "color": "#ff9800", "required": False},
            {"id": "march_assignment", "name": "March Queues", "icon": "⚔️", "color": "#9c27b0", "required": False}
        ]
        
        list_container = tk.Frame(parent, bg="#1a1a3a")
        list_container.pack(fill="both", expand=True, padx=8, pady=5)
        
        self.module_vars = {}
        self.module_frames = {}
        
        for module in self.modules:
            self._create_module_item(list_container, module)
    
    def _create_module_item(self, parent, module):
        """Create individual module item"""
        module_id = module["id"]
        is_enabled = self.settings.get(module_id, {}).get("enabled", True)
        
        # Item frame
        item_frame = tk.Frame(parent, bg="#1e1e3f", relief="solid", bd=1, height=50)
        item_frame.pack(fill="x", pady=2)
        item_frame.pack_propagate(False)
        
        content = tk.Frame(item_frame, bg="#1e1e3f")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Left side - icon and name
        left = tk.Frame(content, bg="#1e1e3f")
        left.pack(side="left", fill="both", expand=True)
        
        icon_label = tk.Label(left, text=module['icon'], bg="#1e1e3f", fg=module["color"],
                             font=("Segoe UI", 14), cursor="hand2")
        icon_label.pack(side="left")
        
        name_label = tk.Label(left, text=module['name'], bg="#1e1e3f", fg="#ffffff",
                             font=("Segoe UI", 10, "bold"), anchor="w", cursor="hand2")
        name_label.pack(side="left", padx=(8, 0), fill="x", expand=True)
        
        # Right side - toggle or status
        right = tk.Frame(content, bg="#1e1e3f")
        right.pack(side="right")
        
        if module.get("required"):
            tk.Label(right, text="REQ", bg="#1e1e3f", fg="#4caf50", font=("Segoe UI", 8, "bold")).pack()
            self.module_vars[module_id] = None
        else:
            toggle_var = tk.BooleanVar(value=is_enabled)
            self.module_vars[module_id] = toggle_var
            toggle = tk.Checkbutton(right, variable=toggle_var, bg="#1e1e3f", activebackground="#1e1e3f",
                                   selectcolor="#2d2d5a", relief="flat", command=lambda: self._on_toggle_change(module_id))
            toggle.pack()
        
        # Click handler
        def on_click(event):
            self._show_module_settings(module_id)
            self._update_selection(module_id)
        
        # Hover effects
        def on_enter(event):
            if module_id != self.current_module:
                self._set_item_colors(item_frame, content, left, right, [icon_label, name_label], "#252550")
        
        def on_leave(event):
            if module_id != self.current_module:
                self._set_item_colors(item_frame, content, left, right, [icon_label, name_label], "#1e1e3f")
        
        # Bind events
        widgets = [item_frame, content, left, icon_label, name_label]
        for widget in widgets:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        self.module_frames[module_id] = {"frame": item_frame, "widgets": widgets + [right]}
    
    def _set_item_colors(self, frame, content, left, right, labels, color):
        """Set colors for module item"""
        for widget in [frame, content, left, right] + labels:
            widget.configure(bg=color)
    
    def _on_toggle_change(self, module_id):
        """Handle toggle change"""
        if module_id in self.module_vars and self.module_vars[module_id]:
            enabled = self.module_vars[module_id].get()
            print(f"[ModuleSettings] {module_id} toggled to: {enabled}")
            
            # Update settings immediately
            if module_id not in self.settings:
                self.settings[module_id] = {}
            self.settings[module_id]["enabled"] = enabled
    
    def _update_selection(self, module_id):
        """Update visual selection"""
        for mid, frame_info in self.module_frames.items():
            color = "#2d2d5a" if mid == module_id else "#1e1e3f"
            frame_info["frame"].configure(bg=color)
            for widget in frame_info["widgets"]:
                widget.configure(bg=color)
    
    def _setup_scrollable_content(self):
        """Setup scrollable content area"""
        canvas_frame = tk.Frame(self.content_area, bg="#1a1a3a")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.content_canvas = tk.Canvas(canvas_frame, bg="#0f0f23", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.content_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.content_frame = tk.Frame(self.content_canvas, bg="#0f0f23")
        self.content_window = self.content_canvas.create_window(0, 0, anchor="nw", window=self.content_frame)
        
        # Bind events
        self.content_frame.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.bind("<Configure>", lambda e: self.content_canvas.itemconfig(self.content_window, width=self.content_canvas.winfo_width()))
        self.content_canvas.bind("<MouseWheel>", lambda e: self.content_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    def _show_module_settings(self, module_id):
        """Show settings for specific module"""
        self.current_module = module_id
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        for widget in self.content_header.winfo_children():
            widget.destroy()
        
        # Clear form variables
        self.form_vars.clear()
        
        # Update header
        module_info = next((m for m in self.modules if m["id"] == module_id), None)
        if module_info:
            header_content = tk.Frame(self.content_header, bg="#2d2d5a")
            header_content.pack(fill="both", expand=True, padx=15, pady=10)
            tk.Label(header_content, text=f"{module_info['icon']} {module_info['name']}", bg="#2d2d5a", fg="#ffffff",
                    font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Show appropriate settings
        if module_id == "autostart_game":
            self._show_autostart_settings()
        elif module_id == "auto_gather":
            self._show_enhanced_gather_settings()
        elif module_id == "march_assignment":
            self._show_march_settings()
    
    def _show_autostart_settings(self):
        """Show AutoStart settings"""
        settings = self.settings.get("autostart_game", {})
        
        # Auto-startup section
        startup_section = self._create_section("Auto-Startup", "🚀", "#2196f3")
        
        self.form_vars['auto_startup'] = tk.BooleanVar(value=settings.get("auto_startup", False))
        
        if self.instance_running:
            tk.Label(startup_section, text="🔒 Auto-startup cannot be changed while instance is running", bg="#0f0f23", fg="#ff9800",
                    font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
            current_state = "Enabled" if self.form_vars['auto_startup'].get() else "Disabled"
            tk.Label(startup_section, text=f"Current setting: {current_state}", bg="#0f0f23", fg="#ffffff",
                    font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        else:
            startup_check = tk.Checkbutton(startup_section, text="🎮 Auto-start game when instance starts", variable=self.form_vars['auto_startup'],
                                          bg="#0f0f23", fg="#2196f3", selectcolor="#1a1a3a", font=("Segoe UI", 10, "bold"), activebackground="#0f0f23")
            startup_check.pack(anchor="w", pady=5)
        
        # Retry settings
        retry_section = self._create_section("Retry Settings", "🔄", "#ff9800")
        retry_grid = tk.Frame(retry_section, bg="#0f0f23")
        retry_grid.pack(fill="x", pady=5)
        
        # Max retries
        tk.Label(retry_grid, text="Max retries:", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.form_vars['max_retries'] = tk.StringVar(value=str(settings.get("max_retries", 3)))
        tk.Spinbox(retry_grid, from_=1, to=10, textvariable=self.form_vars['max_retries'], bg="#1a1a3a", fg="#ffffff", width=5, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w")
        
        # Retry delay
        tk.Label(retry_grid, text="Delay (sec):", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(20, 10))
        self.form_vars['retry_delay'] = tk.StringVar(value=str(settings.get("retry_delay", 10)))
        tk.Spinbox(retry_grid, from_=5, to=60, textvariable=self.form_vars['retry_delay'], bg="#1a1a3a", fg="#ffffff", width=5, font=("Segoe UI", 10)).grid(row=0, column=3, sticky="w")
    
    def _show_enhanced_gather_settings(self):
        """Show enhanced AutoGather settings with custom loop editor"""
        settings = self.settings.get("auto_gather", {})
        
        # Status section
        status_section = self._create_section("Module Status", "📊", "#4caf50")
        
        # Get current module status if available
        status_text = "Unknown"
        if self.app_ref and hasattr(self.app_ref, 'module_manager') and self.app_ref.module_manager:
            module_status = self.app_ref.module_manager.get_module_status(self.instance_name)
            gather_status = module_status.get("AutoGather", {})
            if gather_status.get("running", False):
                status_text = "✅ Running"
            elif gather_status.get("available", False):
                status_text = "⏸️ Available but stopped"
            else:
                status_text = "❌ Not available"
        
        tk.Label(status_section, text=f"Current Status: {status_text}", bg="#0f0f23", fg="#ffffff",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
        
        # Custom Resource Loop Editor
        loop_section = self._create_section("Custom Resource Gathering Order", "🔄", "#2196f3")
        
        # Instructions
        instruction_text = ("Create your custom gathering order by adding resources below.\n"
                           "You can add the same resource multiple times for priority gathering.\n"
                           "Example: Food, Food, Iron, Food = gather mostly food with some iron")
        
        tk.Label(loop_section, text=instruction_text, bg="#0f0f23", fg="#8b949e",
                font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(0, 10))
        
        # Load current resource loop
        current_loop = settings.get("resource_loop", ["food", "wood", "iron", "stone"])
        if isinstance(current_loop, str):
            current_loop = [r.strip() for r in current_loop.split(',') if r.strip()]
        self.resource_loop = current_loop.copy()
        
        # Resource loop editor
        self._create_resource_loop_editor(loop_section)
        
        # Advanced settings section
        advanced_section = self._create_section("Advanced Settings", "⚙️", "#9c27b0")
        
        # Max queues
        max_queues_frame = tk.Frame(advanced_section, bg="#0f0f23")
        max_queues_frame.pack(fill="x", pady=5)
        
        tk.Label(max_queues_frame, text="Max march queues to use:", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 10)).pack(side="left")
        self.form_vars['max_queues'] = tk.StringVar(value=str(settings.get("max_queues", 6)))
        queue_spin = tk.Spinbox(max_queues_frame, from_=1, to=6, textvariable=self.form_vars['max_queues'], bg="#1a1a3a", fg="#ffffff",
                               width=3, font=("Segoe UI", 10))
        queue_spin.pack(side="left", padx=(10, 0))
        
        # Check interval
        interval_frame = tk.Frame(advanced_section, bg="#0f0f23")
        interval_frame.pack(fill="x", pady=5)
        
        tk.Label(interval_frame, text="Check interval (seconds):", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 10)).pack(side="left")
        self.form_vars['check_interval'] = tk.StringVar(value=str(settings.get("check_interval", 60)))
        interval_spin = tk.Spinbox(interval_frame, from_=30, to=300, textvariable=self.form_vars['check_interval'], bg="#1a1a3a", fg="#ffffff",
                                  width=5, font=("Segoe UI", 10))
        interval_spin.pack(side="left", padx=(10, 0))
    
    def _create_resource_loop_editor(self, parent):
        """Create the enhanced resource loop editor"""
        editor_frame = tk.Frame(parent, bg="#0f0f23")
        editor_frame.pack(fill="x", pady=5)
        
        # Left side - Available resources to add
        left_frame = tk.Frame(editor_frame, bg="#161b22", relief="solid", bd=1)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        tk.Label(left_frame, text="📦 Available Resources", bg="#161b22", fg="#ffffff",
                font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        # Resource buttons
        for resource in self.available_resources:
            btn = tk.Button(left_frame, text=resource["name"], bg=resource["color"], fg="#ffffff",
                           font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=10, pady=5,
                           cursor="hand2", command=lambda r=resource["id"]: self._add_resource_to_loop(r))
            btn.pack(fill="x", padx=5, pady=2)
            
            # Hover effect
            def on_enter(event, b=btn, c=resource["color"]):
                b.configure(bg=self._lighten_color(c))
            def on_leave(event, b=btn, c=resource["color"]):
                b.configure(bg=c)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Right side - Current loop and controls
        right_frame = tk.Frame(editor_frame, bg="#0f0f23")
        right_frame.pack(side="left", fill="both", expand=True)
        
        # Current loop header with controls
        loop_header = tk.Frame(right_frame, bg="#0f0f23")
        loop_header.pack(fill="x", pady=(0, 5))
        
        tk.Label(loop_header, text="🔄 Current Gathering Order", bg="#0f0f23", fg="#ffffff",
                font=("Segoe UI", 10, "bold")).pack(side="left")
        
        # Quick action buttons
        quick_frame = tk.Frame(loop_header, bg="#0f0f23")
        quick_frame.pack(side="right")
        
        clear_btn = tk.Button(quick_frame, text="🗑 Clear", bg="#ff6b6b", fg="#ffffff",
                             font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
                             cursor="hand2", command=self._clear_resource_loop)
        clear_btn.pack(side="left", padx=(0, 5))
        
        preset_btn = tk.Button(quick_frame, text="⚡ Presets", bg="#9c27b0", fg="#ffffff",
                              font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
                              cursor="hand2", command=self._show_preset_menu)
        preset_btn.pack(side="left")
        
        # Loop display and controls
        loop_container = tk.Frame(right_frame, bg="#161b22", relief="solid", bd=1)
        loop_container.pack(fill="both", expand=True)
        
        # Listbox for current loop
        listbox_frame = tk.Frame(loop_container, bg="#161b22")
        listbox_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.loop_listbox = tk.Listbox(listbox_frame, bg="#0a0e16", fg="#ffffff", font=("Segoe UI", 10),
                                      relief="flat", bd=0, selectbackground="#2d2d5a", height=8)
        scrollbar_loop = tk.Scrollbar(listbox_frame, orient="vertical", command=self.loop_listbox.yview)
        self.loop_listbox.configure(yscrollcommand=scrollbar_loop.set)
        
        self.loop_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_loop.pack(side="right", fill="y")
        
        # Control buttons for loop
        control_frame = tk.Frame(loop_container, bg="#161b22")
        control_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        move_up_btn = tk.Button(control_frame, text="↑ Move Up", bg="#2196f3", fg="#ffffff",
                               font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
                               cursor="hand2", command=self._move_resource_up)
        move_up_btn.pack(side="left", padx=(0, 3))
        
        move_down_btn = tk.Button(control_frame, text="↓ Move Down", bg="#2196f3", fg="#ffffff",
                                 font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
                                 cursor="hand2", command=self._move_resource_down)
        move_down_btn.pack(side="left", padx=(0, 3))
        
        remove_btn = tk.Button(control_frame, text="✗ Remove", bg="#ff9800", fg="#ffffff",
                              font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
                              cursor="hand2", command=self._remove_selected_resource)
        remove_btn.pack(side="left")
        
        # Update the listbox
        self._update_loop_display()
    
    def _add_resource_to_loop(self, resource_id):
        """Add a resource to the gathering loop"""
        self.resource_loop.append(resource_id)
        self._update_loop_display()
        print(f"Added {resource_id} to loop. Current loop: {self.resource_loop}")
    
    def _remove_selected_resource(self):
        """Remove selected resource from loop"""
        selection = self.loop_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.resource_loop):
                removed = self.resource_loop.pop(index)
                self._update_loop_display()
                print(f"Removed {removed} from loop. Current loop: {self.resource_loop}")
    
    def _move_resource_up(self):
        """Move selected resource up in the loop"""
        selection = self.loop_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                self.resource_loop[index], self.resource_loop[index-1] = self.resource_loop[index-1], self.resource_loop[index]
                self._update_loop_display()
                self.loop_listbox.selection_set(index-1)
    
    def _move_resource_down(self):
        """Move selected resource down in the loop"""
        selection = self.loop_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.resource_loop) - 1:
                self.resource_loop[index], self.resource_loop[index+1] = self.resource_loop[index+1], self.resource_loop[index]
                self._update_loop_display()
                self.loop_listbox.selection_set(index+1)
    
    def _clear_resource_loop(self):
        """Clear the entire resource loop"""
        self.resource_loop.clear()
        self._update_loop_display()
        print("Cleared resource loop")
    
    def _show_preset_menu(self):
        """Show preset menu"""
        preset_menu = tk.Menu(self.window, tearoff=0, bg="#2a2a2a", fg="white")
        
        presets = [
            ("Balanced", ["food", "wood", "iron", "stone"]),
            ("Food Focus", ["food", "food", "food", "wood", "iron", "stone"]),
            ("Wood Focus", ["wood", "wood", "wood", "food", "iron", "stone"]),
            ("Iron Focus", ["iron", "iron", "iron", "food", "wood", "stone"]),
            ("Food+Iron", ["food", "food", "iron", "food", "iron"]),
            ("Economy Focus", ["food", "wood", "food", "wood", "iron", "stone"])
        ]
        
        for name, loop in presets:
            preset_menu.add_command(label=name, command=lambda l=loop: self._apply_preset(l))
        
        try:
            preset_menu.tk_popup(self.window.winfo_pointerx(), self.window.winfo_pointery())
        finally:
            preset_menu.grab_release()
    
    def _apply_preset(self, loop):
        """Apply a preset resource loop"""
        self.resource_loop = loop.copy()
        self._update_loop_display()
        print(f"Applied preset loop: {self.resource_loop}")
    
    def _update_loop_display(self):
        """Update the loop display listbox"""
        if not self.loop_listbox:
            return
            
        # Clear current items
        self.loop_listbox.delete(0, tk.END)
        
        # Add items with nice formatting
        for i, resource_id in enumerate(self.resource_loop):
            resource_info = next((r for r in self.available_resources if r["id"] == resource_id), None)
            if resource_info:
                display_text = f"{i+1:2d}. {resource_info['name']}"
                self.loop_listbox.insert(tk.END, display_text)
        
        # Update summary
        if hasattr(self, 'loop_summary_label'):
            self._update_loop_summary()
    
    def _update_loop_summary(self):
        """Update the loop summary display"""
        if not self.resource_loop:
            summary = "No resources in loop"
        else:
            # Count occurrences
            counts = {}
            for resource in self.resource_loop:
                counts[resource] = counts.get(resource, 0) + 1
            
            # Create summary
            parts = []
            for resource_id, count in counts.items():
                resource_info = next((r for r in self.available_resources if r["id"] == resource_id), None)
                if resource_info:
                    name = resource_info["name"].split()[1]  # Get name without emoji
                    if count > 1:
                        parts.append(f"{name}×{count}")
                    else:
                        parts.append(name)
            
            summary = f"Loop: {' → '.join(parts)} (Total: {len(self.resource_loop)} steps)"
        
        if hasattr(self, 'loop_summary_label'):
            self.loop_summary_label.configure(text=summary)
    
    def _lighten_color(self, hex_color):
        """Lighten a hex color for hover effects"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Lighten by 20%
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color
    
    def _show_march_settings(self):
        """Show march assignment settings"""
        settings = self.settings.get("march_assignment", {})
        
        # Queue setup
        queue_section = self._create_section("Queue Setup", "⚔️", "#9c27b0")
        
        # Unlocked queues
        queue_frame = tk.Frame(queue_section, bg="#0f0f23")
        queue_frame.pack(fill="x", pady=5)
        
        tk.Label(queue_frame, text="Unlocked queues:", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.form_vars['unlocked_queues'] = tk.StringVar(value=str(settings.get("unlocked_queues", 2)))
        queue_spin = tk.Spinbox(queue_frame, from_=1, to=6, textvariable=self.form_vars['unlocked_queues'], bg="#1a1a3a", fg="#ffffff",
                               width=3, font=("Segoe UI", 10), command=self._update_queue_display)
        queue_spin.pack(side="left", padx=(10, 0))
        
        # Queue assignments
        self.queue_assignments_frame = tk.Frame(queue_section, bg="#0f0f23")
        self.queue_assignments_frame.pack(fill="x", pady=(10, 0))
        self.form_vars['queue_assignment_vars'] = {}
        self._update_queue_display()
    
    def _update_queue_display(self):
        """Update queue assignments display"""
        try:
            for widget in self.queue_assignments_frame.winfo_children():
                widget.destroy()
            
            self.form_vars['queue_assignment_vars'].clear()
            
            unlocked_count = int(self.form_vars['unlocked_queues'].get())
            current_assignments = self.settings.get("march_assignment", {}).get("queue_assignments", {})
            
            for queue_num in range(1, unlocked_count + 1):
                queue_frame = tk.Frame(self.queue_assignments_frame, bg="#0f0f23")
                queue_frame.pack(fill="x", pady=1)
                
                tk.Label(queue_frame, text=f"Q{queue_num}:", bg="#0f0f23", fg="#ffffff", font=("Segoe UI", 9, "bold"), width=4).pack(side="left")
                assignment_var = tk.StringVar(value=current_assignments.get(str(queue_num), "AutoGather"))
                self.form_vars['queue_assignment_vars'][queue_num] = assignment_var
                
                combo = ttk.Combobox(queue_frame, textvariable=assignment_var, values=["AutoGather", "Rally/Manual", "Manual Only"],
                                   state="readonly", width=12, font=("Segoe UI", 8))
                combo.pack(side="left", padx=(5, 0))
        except Exception as e:
            print(f"Error updating queue display: {e}")
    
    def _create_section(self, title, icon, color):
        """Create settings section"""
        section = tk.Frame(self.content_frame, bg="#1a1a3a", relief="solid", bd=1)
        section.pack(fill="x", pady=(0, 8))
        
        header = tk.Frame(section, bg=color, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{icon} {title}", bg=color, fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(side="left", padx=12, pady=6)
        
        content = tk.Frame(section, bg="#0f0f23")
        content.pack(fill="x", padx=15, pady=10)
        return content
    
    def _setup_footer(self):
        """Setup footer with buttons"""
        footer = tk.Frame(self.window, bg="#1a1a3a", height=70)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_content = tk.Frame(footer, bg="#1a1a3a")
        footer_content.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Status and summary on left
        left_info = tk.Frame(footer_content, bg="#1a1a3a")
        left_info.pack(side="left", fill="both", expand=True)
        
        self.status_label = tk.Label(left_info, text="", bg="#1a1a3a", fg="#b0b0b0", font=("Segoe UI", 9))
        self.status_label.pack(anchor="w")
        
        # Loop summary for AutoGather
        self.loop_summary_label = tk.Label(left_info, text="", bg="#1a1a3a", fg="#00d4ff", font=("Segoe UI", 8))
        self.loop_summary_label.pack(anchor="w")
        
        # Update summary if we're showing AutoGather
        if self.current_module == "auto_gather":
            self._update_loop_summary()
        
        # Action buttons
        action_frame = tk.Frame(footer_content, bg="#1a1a3a")
        action_frame.pack(side="left")
        
        # Test button for AutoGather
        test_btn = tk.Button(action_frame, text="🧪 Test AutoGather", bg="#ff9800", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                            relief="flat", bd=0, padx=15, pady=8, cursor="hand2", command=self._test_autogather)
        test_btn.pack(side="left", padx=(0, 10))
        
        # Main buttons
        btn_frame = tk.Frame(footer_content, bg="#1a1a3a")
        btn_frame.pack(side="right")
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", bg="#f44336", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                              relief="flat", bd=0, padx=20, pady=8, cursor="hand2", command=self._close_window)
        cancel_btn.pack(side="left", padx=(0, 10))
        
        save_btn = tk.Button(btn_frame, text="💾 Save Settings", bg="#4caf50", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                            relief="flat", bd=0, padx=20, pady=8, cursor="hand2", command=self._save_settings)
        save_btn.pack(side="left")
    
    def _test_autogather(self):
        """Test AutoGather functionality"""
        try:
            if not self.app_ref or not hasattr(self.app_ref, 'module_manager'):
                self.status_label.configure(text="❌ Module manager not available", fg="#f44336")
                return
            
            self.status_label.configure(text="🧪 Testing AutoGather...", fg="#ff9800")
            self.window.update()
            
            # Try to manually start AutoGather
            self.app_ref.module_manager.manual_start_autogather(self.instance_name)
            
            self.status_label.configure(text="✅ AutoGather test initiated", fg="#4caf50")
            self.window.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            self.status_label.configure(text=f"❌ Test failed: {str(e)}", fg="#f44336")
            print(f"AutoGather test error: {e}")
    
    def _save_settings(self):
        """Save all settings with enhanced resource loop support"""
        try:
            # AutoStart settings
            if self.current_module == "autostart_game" or "auto_startup" in self.form_vars:
                current_auto_startup = self.settings.get("autostart_game", {}).get("auto_startup", False) if self.instance_running else self.form_vars.get('auto_startup', tk.BooleanVar()).get()
                
                autostart_settings = {
                    "enabled": True,
                    "auto_startup": current_auto_startup
                }
                
                if 'max_retries' in self.form_vars:
                    autostart_settings["max_retries"] = int(self.form_vars['max_retries'].get())
                else:
                    autostart_settings["max_retries"] = self.settings.get("autostart_game", {}).get("max_retries", 3)
                
                if 'retry_delay' in self.form_vars:
                    autostart_settings["retry_delay"] = int(self.form_vars['retry_delay'].get())
                else:
                    autostart_settings["retry_delay"] = self.settings.get("autostart_game", {}).get("retry_delay", 10)
                
                self.settings["autostart_game"] = autostart_settings
            
            # AutoGather settings - ENHANCED with custom loop
            if self.current_module == "auto_gather" or hasattr(self, 'resource_loop'):
                # Get enabled status from toggle
                enabled = True
                if "auto_gather" in self.module_vars and self.module_vars["auto_gather"]:
                    enabled = self.module_vars["auto_gather"].get()
                
                gather_settings = {
                    "enabled": enabled
                }
                
                # Save custom resource loop
                if hasattr(self, 'resource_loop') and self.resource_loop:
                    gather_settings["resource_loop"] = self.resource_loop
                    gather_settings["resource_types"] = list(set(self.resource_loop))  # Unique resources for backward compatibility
                else:
                    # Keep existing values or use defaults
                    existing_gather = self.settings.get("auto_gather", {})
                    gather_settings["resource_loop"] = existing_gather.get("resource_loop", ["food", "wood", "iron", "stone"])
                    gather_settings["resource_types"] = existing_gather.get("resource_types", ["food", "wood", "iron", "stone"])
                
                # Max queues
                if 'max_queues' in self.form_vars:
                    gather_settings["max_queues"] = int(self.form_vars['max_queues'].get())
                else:
                    gather_settings["max_queues"] = self.settings.get("auto_gather", {}).get("max_queues", 6)
                
                # Check interval
                if 'check_interval' in self.form_vars:
                    gather_settings["check_interval"] = int(self.form_vars['check_interval'].get())
                else:
                    gather_settings["check_interval"] = self.settings.get("auto_gather", {}).get("check_interval", 60)
                
                # Other settings
                gather_settings["max_concurrent_gathers"] = self.settings.get("auto_gather", {}).get("max_concurrent_gathers", 5)
                
                self.settings["auto_gather"] = gather_settings
                
                # Log the custom loop for debugging
                print(f"[ModuleSettings] Saved custom resource loop for {self.instance_name}: {gather_settings['resource_loop']}")
            
            # March Assignment settings
            if self.current_module == "march_assignment" or "unlocked_queues" in self.form_vars:
                # Get enabled status from toggle
                enabled = True
                if "march_assignment" in self.module_vars and self.module_vars["march_assignment"]:
                    enabled = self.module_vars["march_assignment"].get()
                
                march_settings = {
                    "enabled": enabled
                }
                
                if 'unlocked_queues' in self.form_vars:
                    unlocked_count = int(self.form_vars['unlocked_queues'].get())
                    march_settings["unlocked_queues"] = unlocked_count
                else:
                    march_settings["unlocked_queues"] = self.settings.get("march_assignment", {}).get("unlocked_queues", 2)
                
                if 'queue_assignment_vars' in self.form_vars:
                    queue_assignments = {}
                    for queue_num, var in self.form_vars['queue_assignment_vars'].items():
                        assignment = var.get()
                        queue_assignments[str(queue_num)] = assignment
                    march_settings["queue_assignments"] = queue_assignments
                else:
                    march_settings["queue_assignments"] = self.settings.get("march_assignment", {}).get("queue_assignments", {"1": "AutoGather", "2": "AutoGather"})
                
                self.settings["march_assignment"] = march_settings
            
            # Save to file
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            # Show success with loop summary
            success_msg = "✅ Settings saved successfully!"
            if hasattr(self, 'resource_loop') and self.resource_loop:
                success_msg += f" Custom loop: {len(self.resource_loop)} steps"
            
            self.status_label.configure(text=success_msg, fg="#4caf50")
            self.window.after(3000, lambda: self.status_label.configure(text=""))
            
            # Notify app and reload settings
            if self.app_ref:
                self.app_ref.add_console_message(f"✅ Saved module settings for {self.instance_name}")
                if hasattr(self.app_ref, 'module_manager') and self.app_ref.module_manager:
                    self.app_ref.module_manager.reload_instance_settings(self.instance_name)
                    
                    # Update AutoGather module settings if it exists
                    if (self.instance_name in self.app_ref.module_manager.instance_modules and 
                        "AutoGather" in self.app_ref.module_manager.instance_modules[self.instance_name]):
                        
                        autogather_module = self.app_ref.module_manager.instance_modules[self.instance_name]["AutoGather"]
                        if hasattr(autogather_module, 'update_settings'):
                            gather_settings = self.settings.get("auto_gather", {})
                            autogather_module.update_settings(gather_settings)
                            print(f"[ModuleSettings] Updated AutoGather settings for {self.instance_name}")
            
            print(f"[ModuleSettings] Settings saved for {self.instance_name}: {self.settings}")
            
        except Exception as e:
            error_msg = f"❌ Error saving: {str(e)}"
            self.status_label.configure(text=error_msg, fg="#f44336")
            print(f"[ModuleSettings] Save error: {e}")
    
    def _load_settings(self):
        """Load settings from file"""
        default_settings = {
            "autostart_game": {
                "enabled": True, 
                "auto_startup": False, 
                "max_retries": 3, 
                "retry_delay": 10
            },
            "auto_gather": {
                "enabled": True, 
                "resource_types": ["food", "wood", "iron", "stone"],
                "resource_loop": ["food", "wood", "iron", "stone"],
                "max_queues": 6,
                "check_interval": 60,
                "max_concurrent_gathers": 5
            },
            "march_assignment": {
                "enabled": True, 
                "unlocked_queues": 2, 
                "queue_assignments": {
                    "1": "AutoGather", 
                    "2": "AutoGather"
                }
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Merge loaded settings with defaults
                for module_key, module_defaults in default_settings.items():
                    if module_key not in loaded_settings:
                        loaded_settings[module_key] = module_defaults.copy()
                    else:
                        # Merge individual settings
                        for setting_key, default_value in module_defaults.items():
                            if setting_key not in loaded_settings[module_key]:
                                loaded_settings[module_key][setting_key] = default_value
                
                print(f"[ModuleSettings] Loaded settings for {self.instance_name}: {loaded_settings}")
                return loaded_settings
                
        except Exception as e:
            print(f"[ModuleSettings] Error loading settings for {self.instance_name}: {e}")
        
        print(f"[ModuleSettings] Using default settings for {self.instance_name}")
        return default_settings
    
    def _close_window(self):
        """Close the window"""
        self.window.destroy()


# Export functions for compatibility
def show_improved_module_settings(parent, instance_name, app_ref=None):
    """Show the improved module settings window"""
    try:
        return ImprovedModuleSettings(parent, instance_name, app_ref)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open module settings: {str(e)}")
        return None

# Legacy compatibility exports
show_slim_module_settings = show_improved_module_settings
show_improved_king_shot_module_settings = show_improved_module_settings
show_king_shot_module_settings = show_improved_module_settings
show_modules_window = show_improved_module_settings