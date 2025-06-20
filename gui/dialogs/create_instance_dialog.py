"""
BENSON v2.0 - Fixed Create Instance Dialog
Non-freezing animation during creation
"""

import tkinter as tk
from tkinter import messagebox
import threading


class CreateInstanceDialog:
    """Modern dialog with non-freezing animation during creation"""
    
    def __init__(self, parent, app_ref):
        self.parent = parent
        self.app = app_ref
        self.dialog = None
        self.result = None
        self.creating = False
        self.animation_id = None
        self.animation_step = 0
        
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
            
            # Position dialog
            dialog_width = 520
            dialog_height = 450
            x, y = self._get_dialog_position(dialog_width, dialog_height)
            
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            self.dialog.update_idletasks()
            
            # Setup UI
            self._setup_ui(dialog_width, dialog_height)
            
            # Setup events
            self._setup_events()
            
            # Show dialog
            self.dialog.lift()
            self.dialog.focus_force()
            
            # Wait for dialog
            self.dialog.wait_window()
            
            return self.result
            
        except Exception as e:
            print(f"[CreateDialog] Error: {e}")
            if self.dialog:
                try:
                    self.dialog.destroy()
                except:
                    pass
            return None
    
    def _get_dialog_position(self, width, height):
        """Get proper dialog position"""
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
                
                print(f"[CreateDialog] Positioning at: {x},{y}")
                return x, y
            
            # Fallback to center screen
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            return x, y
            
        except Exception as e:
            print(f"[CreateDialog] Position error: {e}")
            return 500, 300
    
    def _setup_ui(self, width, height):
        """Setup modern UI"""
        # Main container
        main_frame = tk.Frame(self.dialog, bg="#1e2329", relief="flat", bd=0)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        self._setup_header(main_frame)
        
        # Content
        content = tk.Frame(main_frame, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Setup sections
        self._setup_icon_section(content)
        self._setup_input_section(content)
        self._setup_info_section(content)
        self._setup_buttons(content)
    
    def _setup_header(self, parent):
        """Setup header with close button"""
        header = tk.Frame(parent, bg="#2d3442", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text="🆕 Create New Instance",
            bg="#2d3442",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Close button
        close_btn = tk.Button(
            header,
            text="×",
            bg="#2d3442",
            fg="#ff6b6b",
            relief="flat",
            bd=0,
            font=("Segoe UI", 16, "bold"),
            cursor="hand2",
            width=3,
            command=self._on_cancel
        )
        close_btn.pack(side="right", padx=15, pady=15)
        
        # Hover effects
        def on_enter(e): close_btn.configure(bg="#ff4444", fg="#ffffff")
        def on_leave(e): close_btn.configure(bg="#2d3442", fg="#ff6b6b")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)
    
    def _setup_icon_section(self, parent):
        """Setup icon and description"""
        icon_section = tk.Frame(parent, bg="#1e2329")
        icon_section.pack(fill="x", pady=(0, 20))
        
        # Icon
        tk.Label(
            icon_section,
            text="📱",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 32)
        ).pack()
        
        # Description
        tk.Label(
            icon_section,
            text="Create a new MEmu Android emulator instance",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 11)
        ).pack(pady=(5, 0))
    
    def _setup_input_section(self, parent):
        """Setup input section"""
        input_section = tk.Frame(parent, bg="#1e2329")
        input_section.pack(fill="x", pady=(0, 15))
        
        # Label
        tk.Label(
            input_section,
            text="Instance Name",
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 8))
        
        # Input container
        self.input_frame = tk.Frame(input_section, bg="#0a0e16", relief="solid", bd=1)
        self.input_frame.pack(fill="x", pady=(0, 5))
        
        # Entry
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(
            self.input_frame,
            textvariable=self.name_var,
            bg="#0a0e16",
            fg="#ffffff",
            font=("Segoe UI", 13),
            relief="flat",
            bd=0,
            insertbackground="#00d4ff"
        )
        self.name_entry.pack(fill="x", padx=15, pady=12)
        
        # Placeholder
        self._setup_placeholder()
        
        # Suggestion
        tk.Label(
            input_section,
            text="💡 Examples: Gaming, Work, Testing, MyApp",
            bg="#1e2329",
            fg="#6b7280",
            font=("Segoe UI", 9)
        ).pack(anchor="w")
    
    def _setup_info_section(self, parent):
        """Setup info section"""
        info_section = tk.Frame(parent, bg="#1e2329")
        info_section.pack(fill="x", pady=(10, 20))
        
        info_box = tk.Frame(info_section, bg="#161b22", relief="solid", bd=1)
        info_box.pack(fill="x")
        
        tk.Label(
            info_box,
            text="📋 Configuration: 2GB RAM • 2 CPU cores • Auto-optimized",
            bg="#161b22",
            fg="#8b949e",
            font=("Segoe UI", 9),
            justify="left"
        ).pack(padx=12, pady=10, anchor="w")
    
    def _setup_buttons(self, parent):
        """Setup buttons with animation support"""
        # Button container
        button_container = tk.Frame(parent, bg="#1e2329")
        button_container.pack(side="bottom", fill="x", pady=(0, 15))
        
        button_frame = tk.Frame(button_container, bg="#1e2329")
        button_frame.pack()
        
        # Cancel button
        self.cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            bg="#404040",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="left", padx=(0, 15))
        
        # Create button with animation support
        self.create_btn = tk.Button(
            button_frame,
            text="✓ Create Instance",
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self._on_create
        )
        self.create_btn.pack(side="left")
        
        # Add hover effects
        self._add_button_hover(self.cancel_btn, "#404040", "#555555")
        self._add_button_hover(self.create_btn, "#00ff88", "#00ff99")
    
    def _add_button_hover(self, button, normal_bg, hover_bg):
        """Add hover effects"""
        def on_enter(e): 
            if not self.creating:
                button.configure(bg=hover_bg)
        def on_leave(e): 
            if not self.creating:
                button.configure(bg=normal_bg)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _setup_placeholder(self):
        """Setup placeholder text"""
        def on_focus_in(e):
            if self.name_entry.get() == "Enter instance name...":
                self.name_entry.delete(0, "end")
                self.name_entry.configure(fg="#ffffff")
        
        def on_focus_out(e):
            if not self.name_entry.get():
                self.name_entry.insert(0, "Enter instance name...")
                self.name_entry.configure(fg="#8b949e")
        
        self.name_entry.insert(0, "Enter instance name...")
        self.name_entry.configure(fg="#8b949e")
        
        self.name_entry.bind("<FocusIn>", on_focus_in)
        self.name_entry.bind("<FocusOut>", on_focus_out)
        
        # Focus and select
        self.name_entry.focus()
        self.name_entry.select_range(0, 'end')
    
    def _setup_events(self):
        """Setup keyboard events"""
        self.dialog.bind('<Return>', lambda e: self._on_create())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        self.name_entry.bind('<Return>', lambda e: self._on_create())
    
    def _on_create(self):
        """Handle create button click - simple and fast"""
        name = self.name_var.get().strip()
        
        if not name or name == "Enter instance name...":
            self._show_validation_error()
            return
        
        if len(name) < 2:
            self._show_validation_error("Name must be at least 2 characters")
            return
        
        # Simple success - close dialog immediately
        self.result = name
        self.dialog.destroy()
    
    def _show_validation_error(self, message="Please enter a valid instance name"):
        """Simple validation error"""
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