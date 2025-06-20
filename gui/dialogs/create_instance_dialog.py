"""
BENSON v2.0 - Create Instance Dialog (FIXED)
Fixed positioning for multi-monitor setups and proper parent window centering
"""

import tkinter as tk
from tkinter import messagebox


class CreateInstanceDialog:
    """Modern dialog with FIXED multi-monitor positioning"""
    
    def __init__(self, parent, app_ref):
        self.parent = parent
        self.app = app_ref
        self.dialog = None
        self.result = None
        
    def show(self):
        """Show the create instance dialog with FIXED positioning"""
        try:
            # Create modern dialog window
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("Create MEmu Instance")
            self.dialog.configure(bg="#1e2329")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            self.dialog.resizable(False, False)
            
            # FIXED: Get correct positioning for multi-monitor setups
            dialog_width = 520
            dialog_height = 450
            
            # FIXED: Better parent window detection
            x, y = self._get_proper_dialog_position(dialog_width, dialog_height)
            
            print(f"[CreateDialog] Positioning dialog at: {x},{y}")
            
            # FIXED: Set geometry immediately and force update
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            self.dialog.update_idletasks()
            
            # Setup UI
            self._setup_ui(dialog_width, dialog_height)
            
            # Setup events
            self._setup_events()
            
            # FIXED: Force dialog to appear properly
            self.dialog.update()
            self.dialog.lift()
            self.dialog.focus_force()
            self.dialog.attributes('-topmost', True)
            self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
            
            # Wait for dialog to close
            self.dialog.wait_window()
            
            return self.result
            
        except Exception as e:
            print(f"[CreateInstanceDialog] Error: {e}")
            if self.dialog:
                try:
                    self.dialog.destroy()
                except:
                    pass
            messagebox.showerror("Error", f"Could not create dialog: {str(e)}")
            return None
    
    def _get_proper_dialog_position(self, dialog_width, dialog_height):
        """FIXED: Get proper dialog position for multi-monitor setups"""
        try:
            # Force parent to update and get accurate position
            self.parent.update_idletasks()
            
            # Try multiple approaches to get parent position
            parent_x = None
            parent_y = None
            parent_width = None
            parent_height = None
            
            # Approach 1: Direct parent window info
            try:
                parent_x = self.parent.winfo_x()
                parent_y = self.parent.winfo_y()
                parent_width = self.parent.winfo_width()
                parent_height = self.parent.winfo_height()
                
                # Validate coordinates
                if parent_x <= -10000 or parent_y <= -10000:
                    raise ValueError("Invalid parent coordinates")
                    
                print(f"[CreateDialog] Parent window: {parent_x},{parent_y} ({parent_width}x{parent_height})")
                
            except Exception as e:
                print(f"[CreateDialog] Failed to get parent position: {e}")
                parent_x = None
            
            # Approach 2: If parent coordinates are valid, center on parent
            if parent_x is not None and parent_x > -1000 and parent_y > -1000:
                x = parent_x + (parent_width - dialog_width) // 2
                y = parent_y + (parent_height - dialog_height) // 2
                
                # Validate that dialog will be visible
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                
                # Keep dialog on screen with some margin
                if x < 0:
                    x = 50
                elif x + dialog_width > screen_width:
                    x = screen_width - dialog_width - 50
                
                if y < 0:
                    y = 50
                elif y + dialog_height > screen_height:
                    y = screen_height - dialog_height - 50
                
                print(f"[CreateDialog] Centering on parent: {x},{y}")
                return x, y
            
            # Approach 3: Fallback - center on primary screen
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            
            x = (screen_width - dialog_width) // 2
            y = (screen_height - dialog_height) // 2
            
            print(f"[CreateDialog] Fallback to screen center: {x},{y}")
            return x, y
            
        except Exception as e:
            print(f"[CreateDialog] Error calculating position: {e}")
            # Emergency fallback
            return 500, 300
    
    def _setup_ui(self, width, height):
        """Setup the dialog UI"""
        # Main container with shadow effect
        shadow_frame = tk.Frame(self.dialog, bg="#000000")
        shadow_frame.place(x=3, y=3, width=width, height=height)
        
        main_frame = tk.Frame(self.dialog, bg="#1e2329", relief="solid", bd=1)
        main_frame.place(x=0, y=0, width=width, height=height)
        
        # Custom title bar
        self._setup_title_bar(main_frame)
        
        # Content area
        content = tk.Frame(main_frame, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Header section
        self._setup_header(content)
        
        # Input section
        self._setup_input_section(content)
        
        # Info section
        self._setup_info_section(content)
        
        # Button section
        self._setup_buttons(content)
    
    def _setup_title_bar(self, parent):
        """Setup custom title bar"""
        title_bar = tk.Frame(parent, bg="#2d3442", height=45)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            title_bar,
            text="🆕 Create New MEmu Instance",
            bg="#2d3442",
            fg="#f0f6fc",
            font=("Segoe UI", 13, "bold")
        )
        title_label.pack(side="left", padx=20, pady=12)
        
        # Close button with hover effects
        close_btn = tk.Button(
            title_bar,
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
        close_btn.pack(side="right", padx=15, pady=12)
        
        # Add hover effects to close button
        def on_enter(e):
            close_btn.configure(bg="#ff4444", fg="#ffffff")
        
        def on_leave(e):
            close_btn.configure(bg="#2d3442", fg="#ff6b6b")
        
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)
        
        # Make draggable
        self._make_draggable(title_bar)
    
    def _setup_header(self, parent):
        """Setup header with icon and description"""
        header_section = tk.Frame(parent, bg="#1e2329")
        header_section.pack(fill="x", pady=(0, 20))
        
        # Icon
        icon_label = tk.Label(
            header_section,
            text="📱",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 32)
        )
        icon_label.pack()
        
        # Description
        desc_label = tk.Label(
            header_section,
            text="Create a new MEmu Android emulator instance",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 11)
        )
        desc_label.pack(pady=(5, 0))
    
    def _setup_input_section(self, parent):
        """Setup input section"""
        input_section = tk.Frame(parent, bg="#1e2329")
        input_section.pack(fill="x", pady=(0, 15))
        
        # Label
        label = tk.Label(
            input_section,
            text="Instance Name",
            bg="#1e2329",
            fg="#f0f6fc",
            font=("Segoe UI", 12, "bold")
        )
        label.pack(anchor="w", pady=(0, 8))
        
        # Input field container
        self.input_frame = tk.Frame(input_section, bg="#0a0e16", relief="solid", bd=1)
        self.input_frame.pack(fill="x", pady=(0, 5))
        
        # Entry field
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
        
        # Setup placeholder
        self._setup_placeholder()
        
        # Suggestion text
        suggestion = tk.Label(
            input_section,
            text="💡 Examples: Gaming, Work, Testing, MyApp",
            bg="#1e2329",
            fg="#6b7280",
            font=("Segoe UI", 9)
        )
        suggestion.pack(anchor="w")
    
    def _setup_info_section(self, parent):
        """Setup info section"""
        info_section = tk.Frame(parent, bg="#1e2329")
        info_section.pack(fill="x", pady=(10, 20))
        
        # Info box with smaller content
        info_box = tk.Frame(info_section, bg="#161b22", relief="solid", bd=1)
        info_box.pack(fill="x")
        
        info_text = tk.Label(
            info_box,
            text="📋 New instance configuration:\n• 2GB RAM • 2 CPU cores • Auto-optimized",
            bg="#161b22",
            fg="#8b949e",
            font=("Segoe UI", 9),
            justify="left"
        )
        info_text.pack(padx=12, pady=10, anchor="w")
    
    def _setup_buttons(self, parent):
        """Setup button section with hover effects"""
        # Create button container that stays at bottom
        button_container = tk.Frame(parent, bg="#1e2329")
        button_container.pack(side="bottom", fill="x", pady=(0, 15))
        
        # Button frame
        button_frame = tk.Frame(button_container, bg="#1e2329")
        button_frame.pack()
        
        # Cancel button with hover effects
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
        
        # Create button with hover effects
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
        self._add_button_hover(self.cancel_btn, "#404040", "#555555", "#ffffff", "#ffffff")
        self._add_button_hover(self.create_btn, "#00ff88", "#00ff99", "#000000", "#000000")
    
    def _add_button_hover(self, button, normal_bg, hover_bg, normal_fg, hover_fg):
        """Add hover effects to buttons"""
        def on_enter(e):
            try:
                button.configure(bg=hover_bg, fg=hover_fg, relief="raised", bd=1)
            except:
                pass
        
        def on_leave(e):
            try:
                button.configure(bg=normal_bg, fg=normal_fg, relief="flat", bd=0)
            except:
                pass
        
        def on_click(e):
            try:
                click_color = self._get_click_color(normal_bg)
                button.configure(bg=click_color)
                button.after(100, lambda: button.configure(bg=normal_bg))
            except:
                pass
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)
    
    def _get_click_color(self, color):
        """Get click color for button"""
        click_map = {
            "#404040": "#303030",
            "#00ff88": "#00dd77"
        }
        return click_map.get(color, color)
    
    def _setup_placeholder(self):
        """Setup placeholder text functionality"""
        def on_focus_in(e):
            if self.name_entry.get() == "Enter instance name...":
                self.name_entry.delete(0, "end")
                self.name_entry.configure(fg="#ffffff")
        
        def on_focus_out(e):
            if not self.name_entry.get():
                self.name_entry.insert(0, "Enter instance name...")
                self.name_entry.configure(fg="#8b949e")
        
        # Set initial placeholder
        self.name_entry.insert(0, "Enter instance name...")
        self.name_entry.configure(fg="#8b949e")
        
        # Bind events
        self.name_entry.bind("<FocusIn>", on_focus_in)
        self.name_entry.bind("<FocusOut>", on_focus_out)
        
        # Focus on entry
        self.name_entry.focus()
        self.name_entry.select_range(0, 'end')
    
    def _setup_events(self):
        """Setup keyboard events"""
        self.dialog.bind('<Return>', lambda e: self._on_create())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        self.name_entry.bind('<Return>', lambda e: self._on_create())
    
    def _make_draggable(self, widget):
        """Make dialog draggable with proper screen bounds"""
        def start_drag(event):
            try:
                widget.start_x = event.x
                widget.start_y = event.y
                widget.configure(cursor="fleur")
            except Exception as e:
                print(f"[CreateInstanceDialog] Drag start error: {e}")
        
        def drag_dialog(event):
            try:
                x = self.dialog.winfo_x() + (event.x - widget.start_x)
                y = self.dialog.winfo_y() + (event.y - widget.start_y)
                
                # Keep on screen with proper bounds
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                dialog_width = self.dialog.winfo_width()
                dialog_height = self.dialog.winfo_height()
                
                # Allow some off-screen dragging but keep mostly visible
                x = max(-dialog_width + 100, min(x, screen_width - 100))
                y = max(0, min(y, screen_height - 50))
                
                self.dialog.geometry(f"+{x}+{y}")
            except Exception as e:
                print(f"[CreateInstanceDialog] Drag error: {e}")
        
        def stop_drag(event):
            try:
                widget.configure(cursor="")
            except Exception as e:
                print(f"[CreateInstanceDialog] Drag stop error: {e}")
        
        try:
            widget.bind("<Button-1>", start_drag)
            widget.bind("<B1-Motion>", drag_dialog)
            widget.bind("<ButtonRelease-1>", stop_drag)
        except Exception as e:
            print(f"[CreateInstanceDialog] Drag binding error: {e}")
    
    def _on_create(self):
        """Handle create button click"""
        name = self.name_var.get().strip()
        
        if not name or name == "Enter instance name...":
            # Show validation error
            self._show_validation_error()
            return
        
        # Validate name (basic check)
        if len(name) < 2:
            self._show_validation_error("Name must be at least 2 characters long")
            return
        
        if any(char in name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            self._show_validation_error("Name contains invalid characters")
            return
        
        # Success - store result and close
        self.result = name
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()
    
    def _show_validation_error(self, message="Please enter a valid instance name"):
        """Show validation error with animation"""
        try:
            # Shake animation
            self._shake_dialog()
            
            # Flash input field
            self.input_frame.configure(bg="#ff6b6b")
            self.dialog.after(200, lambda: self.input_frame.configure(bg="#0a0e16"))
            
        except Exception as e:
            print(f"[CreateInstanceDialog] Validation error display failed: {e}")
    
    def _shake_dialog(self):
        """Shake animation for validation errors"""
        try:
            original_x = self.dialog.winfo_x()
            original_y = self.dialog.winfo_y()
            shake_distance = 8
            
            def shake_step(step=0):
                try:
                    if step > 6:
                        self.dialog.geometry(f"+{original_x}+{original_y}")
                        return
                    
                    offset = shake_distance if step % 2 == 0 else -shake_distance
                    x = original_x + offset
                    
                    # Keep on screen
                    screen_width = self.dialog.winfo_screenwidth()
                    dialog_width = self.dialog.winfo_width()
                    x = max(0, min(x, screen_width - dialog_width))
                    
                    self.dialog.geometry(f"+{x}+{original_y}")
                    self.dialog.after(60, lambda: shake_step(step + 1))
                    
                except Exception as e:
                    print(f"[CreateInstanceDialog] Shake step error: {e}")
                    try:
                        self.dialog.geometry(f"+{original_x}+{original_y}")
                    except:
                        pass
            
            shake_step()
            
        except Exception as e:
            print(f"[CreateInstanceDialog] Shake animation error: {e}")


# Helper function for easy usage
def show_create_instance_dialog(parent, app_ref):
    """Show the create instance dialog and return the result"""
    dialog = CreateInstanceDialog(parent, app_ref)
    return dialog.show()