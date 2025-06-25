"""
BENSON v2.0 - Compact Create Instance Dialog
Reduced from 300+ lines to ~100 lines with same functionality
"""

import tkinter as tk
from tkinter import messagebox


class CreateInstanceDialog:
    """Compact dialog for creating instances"""
    
    def __init__(self, parent, app_ref):
        self.parent = parent
        self.app = app_ref
        self.dialog = None
        self.result = None
        
    def show(self):
        """Show the create instance dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("Create MEmu Instance")
            self.dialog.configure(bg="#1e2329")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            self.dialog.resizable(False, False)
            
            # Position and size
            width, height = 520, 450
            x, y = self._get_center_position(width, height)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Setup UI
            self._setup_ui()
            
            # Show and wait
            self.dialog.lift()
            self.dialog.focus_force()
            self.dialog.wait_window()
            
            return self.result
            
        except Exception as e:
            print(f"[CreateDialog] Error: {e}")
            if self.dialog:
                try: self.dialog.destroy()
                except: pass
            return None
    
    def _get_center_position(self, width, height):
        """Get centered position"""
        try:
            self.parent.update_idletasks()
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            if parent_x > -1000 and parent_y > -1000:
                x = parent_x + (parent_width - width) // 2
                y = parent_y + (parent_height - height) // 2
                
                # Keep on screen
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = max(50, min(x, screen_width - width - 50))
                y = max(50, min(y, screen_height - height - 50))
                return x, y
            
            # Fallback to screen center
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            return (screen_width - width) // 2, (screen_height - height) // 2
            
        except:
            return 500, 300
    
    def _setup_ui(self):
        """Setup complete UI"""
        # Main container
        main = tk.Frame(self.dialog, bg="#1e2329")
        main.pack(fill="both", expand=True)
        
        # Header with close button
        self._create_header(main)
        
        # Content
        content = tk.Frame(main, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Icon and description
        self._create_icon_section(content)
        
        # Input section
        self._create_input_section(content)
        
        # Info section
        self._create_info_section(content)
        
        # Buttons
        self._create_buttons(content)
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self._on_create())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _create_header(self, parent):
        """Create header with title and close button"""
        header = tk.Frame(parent, bg="#2d3442", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Title
        tk.Label(header, text="🆕 Create New Instance", bg="#2d3442", fg="#ffffff",
                font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=15)
        
        # Close button
        close_btn = tk.Button(header, text="×", bg="#2d3442", fg="#ff6b6b", relief="flat", bd=0,
                             font=("Segoe UI", 16, "bold"), cursor="hand2", width=3, command=self._on_cancel)
        close_btn.pack(side="right", padx=15, pady=15)
        
        # Hover effect
        close_btn.bind("<Enter>", lambda e: close_btn.configure(bg="#ff4444", fg="#ffffff"))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(bg="#2d3442", fg="#ff6b6b"))
    
    def _create_icon_section(self, parent):
        """Create icon and description section"""
        icon_section = tk.Frame(parent, bg="#1e2329")
        icon_section.pack(fill="x", pady=(0, 20))
        
        tk.Label(icon_section, text="📱", bg="#1e2329", fg="#00d4ff", font=("Segoe UI", 32)).pack()
        tk.Label(icon_section, text="Create a new MEmu Android emulator instance", bg="#1e2329", fg="#8b949e",
                font=("Segoe UI", 11)).pack(pady=(5, 0))
    
    def _create_input_section(self, parent):
        """Create input section"""
        input_section = tk.Frame(parent, bg="#1e2329")
        input_section.pack(fill="x", pady=(0, 15))
        
        # Label
        tk.Label(input_section, text="Instance Name", bg="#1e2329", fg="#ffffff",
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        
        # Input container
        self.input_frame = tk.Frame(input_section, bg="#0a0e16", relief="solid", bd=1)
        self.input_frame.pack(fill="x", pady=(0, 5))
        
        # Entry with placeholder
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(self.input_frame, textvariable=self.name_var, bg="#0a0e16", fg="#ffffff",
                                  font=("Segoe UI", 13), relief="flat", bd=0, insertbackground="#00d4ff")
        self.name_entry.pack(fill="x", padx=15, pady=12)
        
        # Setup placeholder
        self._setup_placeholder()
        
        # Suggestion
        tk.Label(input_section, text="💡 Examples: Gaming, Work, Testing, MyApp", bg="#1e2329", fg="#6b7280",
                font=("Segoe UI", 9)).pack(anchor="w")
    
    def _create_info_section(self, parent):
        """Create info section"""
        info_section = tk.Frame(parent, bg="#1e2329")
        info_section.pack(fill="x", pady=(10, 20))
        
        info_box = tk.Frame(info_section, bg="#161b22", relief="solid", bd=1)
        info_box.pack(fill="x")
        
        tk.Label(info_box, text="📋 Configuration: 2GB RAM • 2 CPU cores • Auto-optimized", bg="#161b22", fg="#8b949e",
                font=("Segoe UI", 9)).pack(padx=12, pady=10, anchor="w")
    
    def _create_buttons(self, parent):
        """Create action buttons"""
        button_container = tk.Frame(parent, bg="#1e2329")
        button_container.pack(side="bottom", fill="x", pady=(0, 15))
        
        button_frame = tk.Frame(button_container, bg="#1e2329")
        button_frame.pack()
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", bg="#404040", fg="#ffffff", font=("Segoe UI", 11, "bold"),
                              relief="flat", bd=0, padx=30, pady=12, cursor="hand2", command=self._on_cancel)
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Create button
        self.create_btn = tk.Button(button_frame, text="✓ Create Instance", bg="#00ff88", fg="#000000",
                                   font=("Segoe UI", 11, "bold"), relief="flat", bd=0, padx=30, pady=12,
                                   cursor="hand2", command=self._on_create)
        self.create_btn.pack(side="left")
        
        # Add hover effects
        self._add_hover_effects([
            (cancel_btn, "#404040", "#555555"),
            (self.create_btn, "#00ff88", "#00ff99")
        ])
    
    def _add_hover_effects(self, button_configs):
        """Add hover effects to buttons"""
        for button, normal_bg, hover_bg in button_configs:
            button.bind("<Enter>", lambda e, b=button, h=hover_bg: b.configure(bg=h))
            button.bind("<Leave>", lambda e, b=button, n=normal_bg: b.configure(bg=n))
    
    def _setup_placeholder(self):
        """Setup placeholder text behavior"""
        placeholder = "Enter instance name..."
        
        def on_focus_in(e):
            if self.name_entry.get() == placeholder:
                self.name_entry.delete(0, "end")
                self.name_entry.configure(fg="#ffffff")
        
        def on_focus_out(e):
            if not self.name_entry.get():
                self.name_entry.insert(0, placeholder)
                self.name_entry.configure(fg="#8b949e")
        
        self.name_entry.insert(0, placeholder)
        self.name_entry.configure(fg="#8b949e")
        self.name_entry.bind("<FocusIn>", on_focus_in)
        self.name_entry.bind("<FocusOut>", on_focus_out)
        self.name_entry.bind('<Return>', lambda e: self._on_create())
        
        # Focus and select
        self.name_entry.focus()
        self.name_entry.select_range(0, 'end')
    
    def _on_create(self):
        """Handle create button click"""
        name = self.name_var.get().strip()
        
        if not name or name == "Enter instance name...":
            self._show_validation_error()
            return
        
        if len(name) < 2:
            self._show_validation_error("Name must be at least 2 characters")
            return
        
        # Success - close dialog
        self.result = name
        self.dialog.destroy()
    
    def _show_validation_error(self, message="Please enter a valid instance name"):
        """Show validation error with visual feedback"""
        try:
            # Flash input field red
            self.input_frame.configure(bg="#ff6b6b")
            self.dialog.after(200, lambda: self.input_frame.configure(bg="#0a0e16"))
        except Exception as e:
            print(f"[CreateDialog] Validation error: {e}")
    
    def _on_cancel(self):
        """Handle cancel"""
        self.result = None
        self.dialog.destroy()


def show_create_instance_dialog(parent, app_ref):
    """Show the create instance dialog"""
    dialog = CreateInstanceDialog(parent, app_ref)
    return dialog.show()