"""
BENSON v2.0 - Enhanced Instance Card Component with OCR Region Selection
"""

import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import json
import threading
import weakref
import win32gui
import win32con
from PIL import Image, ImageTk, ImageGrab


class CustomOCRRegionDialog(tk.Toplevel):
    def __init__(self, parent, screenshot=None):
        super().__init__(parent)
        
        # Initialize result
        self.result = None
        
        # Store screenshot
        if isinstance(screenshot, str):
            # If screenshot is a path, load it
            self.screenshot = Image.open(screenshot)
        else:
            # Otherwise assume it's already a PIL Image
            self.screenshot = screenshot
        self.photo = None  # To prevent garbage collection
        
        # Get screen dimensions for max size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate window size based on screenshot or default size
        if self.screenshot:
            # Add some padding for window decorations and controls
            window_width = min(self.screenshot.width + 40, screen_width - 100)
            window_height = min(self.screenshot.height + 120, screen_height - 100)
        else:
            window_width = 800
            window_height = 600
        
        # Dialog setup
        self.title("Select OCR Region")
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Create variables for coordinate inputs - clean defaults
        self.x_var = tk.StringVar(value="0.0")
        self.y_var = tk.StringVar(value="0.0")
        self.w_var = tk.StringVar(value="0.2")
        self.h_var = tk.StringVar(value="0.1")
        
        # Create main frame with scrollbars
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create coordinate inputs at the top
        coords_frame = ttk.LabelFrame(main_frame, text="Coordinates (as percentage)")
        coords_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid for coordinate inputs
        for i, (label, var) in enumerate([
            ("X:", self.x_var),
            ("Y:", self.y_var),
            ("Width:", self.w_var),
            ("Height:", self.h_var)
        ]):
            ttk.Label(coords_frame, text=label).grid(row=0, column=i*2, padx=5, pady=5)
            entry = ttk.Entry(coords_frame, textvariable=var, width=10)
            entry.grid(row=0, column=i*2+1, padx=5, pady=5)
            entry.bind('<KeyRelease>', lambda e: self._schedule_preview_update())
        
        # Removed preset buttons as requested
        
        # Create scrollable canvas for the preview
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create preview canvas with scrollbars
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg="#000000",
            highlightthickness=0,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.preview_canvas.xview)
        v_scrollbar.config(command=self.preview_canvas.yview)
        
        # Create buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # Ensure window is visible on screen
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        self.geometry(f"+{x}+{y}")
        
        # Schedule first preview update
        self._schedule_preview_update()
        
        # Wait for window to be destroyed
        self.wait_window()
    
    def _apply_preset(self, x, y, w, h):
        """Apply preset coordinates - keeping this method in case needed later"""
        self.x_var.set(x)
        self.y_var.set(y)
        self.w_var.set(w)
        self.h_var.set(h)
        self._schedule_preview_update()
    
    def _save_region_to_desktop(self, x, y, w, h):
        """Save the selected region as an image to the desktop with better scaling for OCR"""
        if not self.screenshot or not isinstance(self.screenshot, Image.Image):
            return
        
        try:
            # Calculate pixel coordinates
            px1 = int(x * self.screenshot.width)
            py1 = int(y * self.screenshot.height)
            px2 = int((x + w) * self.screenshot.width)
            py2 = int((y + h) * self.screenshot.height)
            
            # Crop the region
            region = self.screenshot.crop((px1, py1, px2, py2))
            
            # Scale up the region for better OCR (minimum 200px width for text)
            original_width, original_height = region.size
            if original_width < 200:
                scale_factor = 200 / original_width
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                region = region.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Get desktop path
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ocr_region_{timestamp}.png"
            filepath = os.path.join(desktop, filename)
            
            # Save the image
            region.save(filepath)
            messagebox.showinfo("Success", f"Region saved to desktop as {filename}\nOriginal: {original_width}x{original_height}, Saved: {region.size[0]}x{region.size[1]}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save region: {str(e)}")
    
    def _on_ok(self):
        """Handle OK button click"""
        try:
            # Get current values
            x = float(self.x_var.get())
            y = float(self.y_var.get())
            w = float(self.w_var.get())
            h = float(self.h_var.get())
            
            # Validate values
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                messagebox.showerror("Invalid Values", "All values must be between 0 and 1")
                return
                
            # Store result
            self.result = {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }
            
            # Save region to desktop
            self._save_region_to_desktop(x, y, w, h)
            
            # Close dialog
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Values", "Please enter valid numbers")
    
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.destroy()
        
    def _schedule_preview_update(self):
        """Schedule a preview update with debouncing"""
        if hasattr(self, '_update_job'):
            self.after_cancel(self._update_job)
        self._update_job = self.after(100, self._update_preview)
        
    def _update_preview(self):
        """Update the preview display with FIXED coordinate handling"""
        try:
            # Get current values
            x = float(self.x_var.get())
            y = float(self.y_var.get())
            w = float(self.w_var.get())
            h = float(self.h_var.get())
            
            # Clear previous
            self.preview_canvas.delete('all')
            
            # If we have a screenshot, display it at actual size
            if self.screenshot and isinstance(self.screenshot, Image.Image):
                # Configure canvas scrollregion to match image size
                self.preview_canvas.config(
                    scrollregion=(0, 0, self.screenshot.width, self.screenshot.height)
                )
                
                # Create photo image at actual size
                self.photo = ImageTk.PhotoImage(self.screenshot)
                
                # Display image
                self.preview_canvas.create_image(0, 0, image=self.photo, anchor="nw")
                
                # Calculate selection coordinates in actual pixels
                px1 = int(x * self.screenshot.width)
                py1 = int(y * self.screenshot.height)
                px2 = int((x + w) * self.screenshot.width)
                py2 = int((y + h) * self.screenshot.height)
                
                # Draw semi-transparent overlay
                self.preview_canvas.create_rectangle(0, 0, self.screenshot.width, py1, fill="#000000", stipple="gray50")  # Top
                self.preview_canvas.create_rectangle(0, py2, self.screenshot.width, self.screenshot.height, fill="#000000", stipple="gray50")  # Bottom
                self.preview_canvas.create_rectangle(0, py1, px1, py2, fill="#000000", stipple="gray50")  # Left
                self.preview_canvas.create_rectangle(px2, py1, self.screenshot.width, py2, fill="#000000", stipple="gray50")  # Right
                
                # Draw selection rectangle
                self.preview_canvas.create_rectangle(
                    px1, py1, px2, py2,
                    outline="#00ff88",
                    width=2
                )
                
                # Add corner markers with FIXED coordinates
                marker_size = 8
                # Top-left corner
                self.preview_canvas.create_line(px1, py1, px1 + marker_size, py1, fill="#00ff88", width=2)
                self.preview_canvas.create_line(px1, py1, px1, py1 + marker_size, fill="#00ff88", width=2)
                # Top-right corner
                self.preview_canvas.create_line(px2, py1, px2 - marker_size, py1, fill="#00ff88", width=2)
                self.preview_canvas.create_line(px2, py1, px2, py1 + marker_size, fill="#00ff88", width=2)
                # Bottom-left corner
                self.preview_canvas.create_line(px1, py2, px1 + marker_size, py2, fill="#00ff88", width=2)
                self.preview_canvas.create_line(px1, py2, px1, py2 - marker_size, fill="#00ff88", width=2)
                # Bottom-right corner - FIXED: Added missing coordinates for both lines
                self.preview_canvas.create_line(px2, py2, px2 - marker_size, py2, fill="#00ff88", width=2)
                self.preview_canvas.create_line(px2, py2, px2, py2 - marker_size, fill="#00ff88", width=2)
                
                # Add coordinates and size info
                region_width = px2 - px1
                region_height = py2 - py1
                info_text = f"({int(x*100)}%, {int(y*100)}%) - ({int((x+w)*100)}%, {int((y+h)*100)}%) | {region_width}x{region_height}px"
                
                self.preview_canvas.create_text(
                    10,  # Fixed position in bottom-left
                    self.screenshot.height - 10,
                    text=info_text,
                    fill="#8b949e",
                    font=("Segoe UI", 9),
                    anchor="sw"
                )
                
                # Add warning if region is too small for good OCR
                if region_width < 100 or region_height < 20:
                    self.preview_canvas.create_text(
                        10,
                        self.screenshot.height - 30,
                        text="⚠ Region may be too small for reliable OCR (recommended: >100x20px)",
                        fill="#ff9800",
                        font=("Segoe UI", 9),
                        anchor="sw"
                    )
            else:
                # Show message if no screenshot
                self.preview_canvas.create_text(
                    400, 300,
                    text="No screenshot available",
                    fill="#ff6b6b",
                    font=("Segoe UI", 12)
                )
            
        except ValueError:
            # Invalid number format - show error state
            self.preview_canvas.delete('all')
            self.preview_canvas.create_text(
                400, 300,
                text="Invalid Values",
                fill="#ff6b6b",
                font=("Segoe UI", 12)
            )


class InstanceCard(tk.Frame):
    def __init__(self, parent, name, status="Offline", cpu_usage=0, memory_usage=0, app_ref=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Store instance data
        self.name = name
        self.status = status
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.selected = False
        self._destroyed = False
        
        # Use weak reference to prevent circular references
        self.app_ref = weakref.ref(app_ref) if app_ref else None
        
        # Event handler references for cleanup
        self._event_handlers = []
        
        # Configure the main card frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3)
        self.configure(width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI components
        self._setup_ui()
        self._setup_context_menu()
        self._bind_events()
        
        # Set initial status
        self.update_status_display(status)
        
        # Fade-in animation
        self.after(50, self.animate_fade_in)
    
    def _setup_ui(self):
        """Setup the complete UI structure"""
        # Main container with shadow effect
        self.shadow_frame = tk.Frame(self, bg="#000000", bd=0)
        self.shadow_frame.place(x=2, y=2, relwidth=1, relheight=1)
        
        self.main_container = tk.Frame(self, bg="#343a46", relief="solid", bd=1)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Inner content frame
        self.content_frame = tk.Frame(self.main_container, bg="#1e2329")
        self.content_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Left side - instance info
        self._setup_info_section()
        
        # Right side - action buttons
        self._setup_action_buttons()
        
        # Progress bar (initially hidden)
        self._setup_progress_bar()
    
    def _setup_info_section(self):
        """Setup the instance information section"""
        left_frame = tk.Frame(self.content_frame, bg="#1e2329")
        left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - checkbox and name
        top_row = tk.Frame(left_frame, bg="#1e2329")
        top_row.pack(fill="x", pady=(0, 4))
        
        # Selection checkbox
        self.selected_var = tk.BooleanVar()
        self.checkbox = tk.Label(
            top_row,
            text="☐",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 11),
            cursor="hand2"
        )
        self.checkbox.pack(side="left", padx=(0, 12))
        
        # Instance name
        self.name_label = tk.Label(
            top_row,
            text=self.name,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom_row = tk.Frame(left_frame, bg="#1e2329")
        bottom_row.pack(fill="x")
        
        # Status display
        self.status_icon = tk.Label(
            bottom_row,
            text=self._get_status_icon(self.status),
            bg="#1e2329",
            font=("Segoe UI", 10)
        )
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(
            bottom_row,
            text=self.status,
            bg="#1e2329",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.status_text.pack(side="left", padx=(8, 0))
    
    def _setup_action_buttons(self):
        """Setup action buttons with improved layout"""
        button_frame = tk.Frame(self.content_frame, bg="#1e2329")
        button_frame.pack(side="right", padx=12, pady=10)
        
        # Start/Stop button
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start",
            bg="#00e676",
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
        
        # OCR Test button with dropdown arrow
        ocr_frame = tk.Frame(button_frame, bg="#1e2329")
        ocr_frame.pack(side="right", padx=(6, 0))
        
        self.ocr_btn = tk.Button(
            ocr_frame,
            text="🔍 OCR ▼",
            bg="#ff9800",
            fg="#ffffff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=6,
            command=self._show_ocr_menu
        )
        self.ocr_btn.pack()
        
        # Modules button
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
        self.modules_btn.pack(side="right")
        
        # Context menu button
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
        
        # Add hover effects
        self._add_button_hover_effects()
    
    def _setup_progress_bar(self):
        """Setup progress bar for operations"""
        self.progress_frame = tk.Frame(self.content_frame, bg="#1e2329", height=3)
        self.progress_canvas = tk.Canvas(
            self.progress_frame, 
            bg="#2a2a2a", 
            height=3, 
            highlightthickness=0
        )
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 3, 
            fill="#00d4ff", 
            outline=""
        )
        self.progress_canvas.pack(fill="x")
    
    def _setup_context_menu(self):
        """Setup the context menu with consistent styling"""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2a2a2a", fg="white", bd=0)
        
        menu_items = [
            ("🎯 Start Instance", self._safe_start_instance),
            ("⏹ Stop Instance", self._safe_stop_instance),
            ("🔄 Restart Instance", self._safe_restart_instance),
            None,  # Separator
            ("📋 View Logs", self._safe_view_logs),
            ("💾 Export Config", self._safe_export_config),
            ("🗑 Delete Instance", self._safe_delete_instance)
        ]
        
        for item in menu_items:
            if item is None:
                self.context_menu.add_separator()
            else:
                label, command = item
                self.context_menu.add_command(label=label, command=command)
    
    def _setup_ocr_menu(self):
        """Setup the OCR region selection menu"""
        self.ocr_menu = tk.Menu(self, tearoff=0, bg="#2a2a2a", fg="white", bd=0)
        
        # Get available regions from OCR helper
        app = self._get_app_ref()
        if app and hasattr(app, 'ocr_helper') and app.ocr_helper:
            regions = app.ocr_helper.get_available_regions()
        else:
            # Default regions if OCR helper not available
            regions = ["left_panel", "right_panel", "top_bar", "bottom_bar", "center", "march_queue", "full_screen"]
        
        # Add region options
        region_icons = {
            "left_panel": "◐",
            "right_panel": "◑", 
            "top_bar": "▔",
            "bottom_bar": "▁",
            "center": "◯",
            "march_queue": "📋",
            "full_screen": "⬜"
        }
        
        for region in regions:
            icon = region_icons.get(region, "▫")
            display_name = region.replace("_", " ").title()
            self.ocr_menu.add_command(
                label=f"{icon} {display_name}",
                command=lambda r=region: self._safe_test_ocr_region(r)
            )
        
        self.ocr_menu.add_separator()
        self.ocr_menu.add_command(
            label="🎯 Custom Region...",
            command=self._safe_test_ocr_custom
        )
    
    def _bind_events(self):
        """Bind events with proper cleanup tracking"""
        # List of elements that should be clickable
        clickable_elements = [
            self, self.main_container, self.content_frame,
            self.checkbox, self.name_label, self.status_icon, self.status_text
        ]
        
        # Bind events and track for cleanup
        for element in clickable_elements:
            # Left click for selection
            handler_id = element.bind("<Button-1>", self._on_click)
            self._event_handlers.append((element, "<Button-1>", handler_id))
            
            # Right click for context menu
            handler_id = element.bind("<Button-3>", self._on_right_click)
            self._event_handlers.append((element, "<Button-3>", handler_id))
        
        # Hover effects
        self._bind_hover_effects()
    
    def _bind_hover_effects(self):
        """Add hover effects with proper cleanup"""
        hover_elements = [self, self.main_container, self.content_frame]
        
        for element in hover_elements:
            enter_id = element.bind("<Enter>", self._on_hover_enter)
            leave_id = element.bind("<Leave>", self._on_hover_leave)
            self._event_handlers.extend([
                (element, "<Enter>", enter_id),
                (element, "<Leave>", leave_id)
            ])
    
    def _add_button_hover_effects(self):
        """Add hover effects to buttons"""
        buttons = [
            (self.start_btn, self._on_start_btn_hover),
            (self.ocr_btn, self._on_ocr_btn_hover),
            (self.modules_btn, self._on_modules_btn_hover),
            (self.context_btn, self._on_context_btn_hover)
        ]
        
        for button, hover_handler in buttons:
            enter_id = button.bind("<Enter>", lambda e, h=hover_handler: h(e, True))
            leave_id = button.bind("<Leave>", lambda e, h=hover_handler: h(e, False))
            self._event_handlers.extend([
                (button, "<Enter>", enter_id),
                (button, "<Leave>", leave_id)
            ])
    
    # Event handlers
    def _on_click(self, event):
        """Handle left click events"""
        if not self._destroyed:
            self.toggle_checkbox()
    
    def _on_right_click(self, event):
        """Handle right click events"""
        if not self._destroyed:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            except Exception:
                pass
            finally:
                self.context_menu.grab_release()
    
    def _on_hover_enter(self, event):
        """Handle hover enter"""
        if not self._destroyed and not self.selected:
            try:
                self.content_frame.configure(bg="#252932")
                self._update_child_backgrounds("#252932")
            except tk.TclError:
                pass
    
    def _on_hover_leave(self, event):
        """Handle hover leave"""
        if not self._destroyed and not self.selected:
            try:
                self.content_frame.configure(bg="#1e2329")
                self._update_child_backgrounds("#1e2329")
            except tk.TclError:
                pass
    
    def _on_start_btn_hover(self, event, entering):
        """Handle start button hover"""
        if self._destroyed:
            return
        
        if entering:
            current_bg = self.start_btn.cget("bg")
            new_bg = "#00ff88" if current_bg == "#00e676" else "#ff8a80"
            self.start_btn.configure(bg=new_bg)
        else:
            current_text = self.start_btn.cget("text")
            new_bg = "#00e676" if "Start" in current_text else "#ff6b6b"
            self.start_btn.configure(bg=new_bg)
    
    def _on_ocr_btn_hover(self, event, entering):
        """Handle OCR button hover"""
        if not self._destroyed:
            new_bg = "#ffb74d" if entering else "#ff9800"
            self.ocr_btn.configure(bg=new_bg)
    
    def _on_modules_btn_hover(self, event, entering):
        """Handle modules button hover"""
        if not self._destroyed:
            new_bg = "#42a5f5" if entering else "#2196f3"
            self.modules_btn.configure(bg=new_bg)
    
    def _on_context_btn_hover(self, event, entering):
        """Handle context button hover"""
        if not self._destroyed:
            new_bg = "#606060" if entering else "#404040"
            self.context_btn.configure(bg=new_bg)
    
    # Safe wrapper methods for app interactions
    def _get_app_ref(self):
        """Safely get app reference"""
        if self.app_ref:
            app = self.app_ref()
            if app and not app._destroyed if hasattr(app, '_destroyed') else True:
                return app
        return None
    
    def _safe_toggle_instance(self):
        """Safely toggle instance"""
        try:
            if self.status == "Running":
                self._safe_stop_instance()
            else:
                self._safe_start_instance()
        except Exception as e:
            print(f"[InstanceCard] Error toggling instance {self.name}: {e}")
    
    def _safe_start_instance(self):
        """Safely start instance"""
        try:
            app = self._get_app_ref()
            if app:
                threading.Thread(
                    target=lambda: app.start_instance(self.name),
                    daemon=True
                ).start()
        except Exception as e:
            print(f"[InstanceCard] Error starting instance {self.name}: {e}")
    
    def _safe_stop_instance(self):
        """Safely stop instance"""
        try:
            app = self._get_app_ref()
            if app:
                threading.Thread(
                    target=lambda: app.stop_instance(self.name),
                    daemon=True
                ).start()
        except Exception as e:
            print(f"[InstanceCard] Error stopping instance {self.name}: {e}")
    
    def _safe_restart_instance(self):
        """Safely restart instance"""
        try:
            self._safe_stop_instance()
            self.after(2500, self._safe_start_instance)
        except Exception as e:
            print(f"[InstanceCard] Error restarting instance {self.name}: {e}")
    
    def _show_ocr_menu(self):
        """Show OCR region selection menu"""
        try:
            # Create OCR menu if not exists
            if not hasattr(self, 'ocr_menu'):
                self._setup_ocr_menu()
            
            # Show menu at button position
            button_x = self.ocr_btn.winfo_rootx()
            button_y = self.ocr_btn.winfo_rooty() + self.ocr_btn.winfo_height()
            self.ocr_menu.tk_popup(button_x, button_y)
        except Exception as e:
            print(f"[InstanceCard] Error showing OCR menu: {e}")
            # Fallback to default OCR test
            self._safe_test_ocr_region("left_panel")
        finally:
            try:
                self.ocr_menu.grab_release()
            except:
                pass
    
    def _safe_test_ocr_region(self, region_name):
        """Safely test OCR on specified region"""
        try:
            app = self._get_app_ref()
            if app:
                app.test_instance_ocr_region(self.name, region_name)
        except Exception as e:
            print(f"[InstanceCard] Error testing OCR region {region_name} for {self.name}: {e}")
            messagebox.showerror("OCR Error", f"Could not test OCR: {str(e)}")
    
    def _safe_test_ocr_custom(self):
        """Safely test OCR on custom region"""
        try:
            app = self._get_app_ref()
            if not app:
                raise ValueError("Could not get app reference")

            # Get instance details
            instance = app.instance_manager.get_instance(self.name)
            if not instance:
                raise ValueError(f"Instance {self.name} not found")

            # Capture screenshot first
            screenshot_path = app.ocr_helper.capture_memu_adb_screenshot(
                instance["index"],
                app.instance_manager.MEMUC_PATH
            )

            if not screenshot_path:
                raise ValueError("Failed to capture screenshot")

            # Create custom region dialog with the screenshot
            custom_dialog = CustomOCRRegionDialog(self, screenshot_path)
            
            if custom_dialog.result:
                app.test_instance_ocr_custom(self.name, custom_dialog.result)

            # Clean up screenshot
            try:
                os.remove(screenshot_path)
            except:
                pass

        except Exception as e:
            print(f"[InstanceCard] Error testing custom OCR for {self.name}: {e}")
            messagebox.showerror("OCR Error", str(e))
    
    def _safe_show_modules(self):
        """Safely show modules"""
        try:
            app = self._get_app_ref()
            if app:
                app.show_modules(self.name)
        except Exception as e:
            print(f"[InstanceCard] Error showing modules for {self.name}: {e}")
    
    def _safe_view_logs(self):
        """Safely view logs"""
        try:
            from gui.dialogs.log_viewer import LogViewer
            app = self._get_app_ref()
            LogViewer(self, self.name, app)
        except Exception as e:
            print(f"[InstanceCard] Error viewing logs for {self.name}: {e}")
            messagebox.showerror("Error", f"Could not open log viewer: {str(e)}")
    
    def _safe_export_config(self):
        """Safely export config"""
        try:
            config = {
                "name": self.name,
                "status": self.status,
                "cpu": self.cpu_usage,
                "memory": self.memory_usage,
                "created": datetime.now().isoformat()
            }
            
            filename = f"{self.name}_config.json"
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            
            messagebox.showinfo("Export Complete", f"Configuration exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export config: {str(e)}")
    
    def _safe_delete_instance(self):
        """Safely delete instance"""
        try:
            app = self._get_app_ref()
            if app:
                app.delete_instance_card_with_loading(self)
        except Exception as e:
            print(f"[InstanceCard] Error deleting instance {self.name}: {e}")
            messagebox.showerror("Error", f"Could not delete instance: {str(e)}")
    
    def _safe_show_context_menu(self):
        """Safely show context menu"""
        try:
            button_x = self.winfo_rootx() + self.winfo_width() - 30
            button_y = self.winfo_rooty() + 30
            self.context_menu.tk_popup(button_x, button_y)
        except Exception:
            pass
        finally:
            self.context_menu.grab_release()
    
    # Public interface methods
    def toggle_checkbox(self):
        """Toggle selection state with improved visual feedback"""
        if self._destroyed:
            return
        
        current = self.selected_var.get()
        self.selected_var.set(not current)
        self.selected = not current
        
        if self.selected:
            self.checkbox.configure(text="☑", fg="#00ff88")
            self.main_container.configure(bg="#00d4ff")
            self.shadow_frame.configure(bg="#001122")
            self._animate_selection(True)
        else:
            self.checkbox.configure(text="☐", fg="#00d4ff")
            self.main_container.configure(bg="#343a46")
            self.shadow_frame.configure(bg="#000000")
            self._animate_selection(False)
        
        # Notify app of selection change
        app = self._get_app_ref()
        if app and hasattr(app, 'on_card_selection_changed'):
            app.on_card_selection_changed()
    
    def update_status(self, new_status):
        """Update instance status with visual feedback"""
        if self._destroyed:
            return
        
        self.status = new_status
        
        # Map status to display text and colors
        status_map = {
            "Running": ("Running ✓", "#00ff88", "#00ff88"),  # Text, Text color, Border color
            "Stopped": ("Stopped ⏹", "#ff6b6b", "#343a46"),
            "Starting": ("Starting ⚡", "#ffd93d", "#ffd93d"),
            "Stopping": ("Stopping ⏸", "#ff9800", "#ff9800"),
            "Error": ("Error ⚠", "#ff6b6b", "#ff6b6b"),
            "Offline": ("Offline ⚫", "#8b949e", "#343a46")
        }
        
        # Get status display properties
        status_text, text_color, border_color = status_map.get(
            new_status, 
            (new_status, "#8b949e", "#343a46")  # Default colors for unknown status
        )
        
        # Update status display
        self.status_text.configure(text=status_text, fg=text_color)
        self.main_container.configure(bg=border_color)
        
        # Update button state and appearance
        if new_status == "Running":
            self.start_btn.configure(text="⏹ Stop", bg="#ff6b6b")
        elif new_status == "Starting":
            self.start_btn.configure(text="Starting...", bg="#ffd93d")
            self._show_progress_bar()
            self._animate_progress(100)
        elif new_status == "Stopping":
            self.start_btn.configure(text="Stopping...", bg="#ff9800")
            self._show_progress_bar()
            self._animate_progress(100)
        else:
            self.start_btn.configure(text="▶ Start", bg="#00e676")
    
    def update_status_display(self, new_status):
        """Update the visual status display"""
        if self._destroyed:
            return
        
        colors = {
            "Running": "#00ff88",
            "Stopped": "#8b949e",
            "Offline": "#8b949e",
            "Starting": "#ffd93d",
            "Stopping": "#ff9800",
            "Error": "#ff6b6b"
        }
        
        color = colors.get(new_status, "#8b949e")
        icon = self._get_status_icon(new_status)
        
        self.status_icon.configure(text=icon, fg=color)
        self.status_text.configure(text=new_status, fg=color)
        
        # Update card border based on status
        if new_status == "Running":
            self.main_container.configure(bg="#00ff88")
        elif new_status == "Error":
            self.main_container.configure(bg="#ff6b6b")
        elif new_status in ["Starting", "Stopping"]:
            self.main_container.configure(bg="#ffd93d")
        else:
            self.main_container.configure(bg="#343a46")
    
    # Animation methods
    def animate_fade_in(self):
        """Animate card appearing"""
        if self._destroyed:
            return
        
        fade_colors = ["#0f1419", "#141a20", "#191e25", "#1c212a", "#1e2329"]
        
        def fade_step(step=0):
            if self._destroyed or step >= len(fade_colors):
                return
            
            try:
                self.content_frame.configure(bg=fade_colors[step])
                self._update_child_backgrounds(fade_colors[step])
                self.after(50, lambda: fade_step(step + 1))
            except tk.TclError:
                pass
        
        fade_step()
    
    def _animate_selection(self, selected):
        """Animate selection state change"""
        if self._destroyed:
            return
        
        if selected:
            colors = ["#005577", "#004466", "#005577"]
            def pulse(step=0):
                if self._destroyed or step >= len(colors):
                    return
                try:
                    self.configure(bg=colors[step % len(colors)])
                    self.after(100, lambda: pulse(step + 1))
                except tk.TclError:
                    pass
            pulse()
    
    def _animate_starting(self):
        """Animate starting status with pulsing icon"""
        def pulse():
            if self._destroyed or self.status != "Starting":
                return
            try:
                current_color = self.status_icon.cget("fg")
                new_color = "#ffeb3b" if current_color == "#ffd93d" else "#ffd93d"
                self.status_icon.configure(fg=new_color)
                self.after(500, pulse)
            except tk.TclError:
                pass
        pulse()
    
    def _show_progress_bar(self):
        """Show progress bar for operations"""
        if self._destroyed:
            return
        
        try:
            self.progress_frame.pack(fill="x", pady=(2, 0), before=self.content_frame)
            self._animate_progress(100)
        except tk.TclError:
            pass
    
    def _hide_progress_bar(self):
        """Hide progress bar"""
        if not self._destroyed:
            try:
                self.progress_frame.pack_forget()
            except tk.TclError:
                pass
    
    def _animate_progress(self, target_progress, current_progress=0, step=5):
        """Animate progress bar"""
        if self._destroyed:
            return
        
        if current_progress < target_progress:
            try:
                width = self.progress_canvas.winfo_width()
                if width > 1:
                    progress_width = int(width * (current_progress / 100))
                    self.progress_canvas.coords(self.progress_bar, 0, 0, progress_width, 3)
                
                next_progress = min(current_progress + step, target_progress)
                self.after(50, lambda: self._animate_progress(target_progress, next_progress, step))
            except tk.TclError:
                pass
        elif target_progress >= 100:
            self.after(500, self._hide_progress_bar)
    
    # Utility methods
    def _get_status_icon(self, status):
        """Get icon for status"""
        icons = {
            "Running": "✓",
            "Stopped": "⏹",
            "Starting": "⚡",
            "Stopping": "⏸",
            "Error": "⚠",
            "Offline": "⚫"
        }
        return icons.get(status, "?")
    
    def _update_child_backgrounds(self, color):
        """Update child element backgrounds recursively"""
        if self._destroyed:
            return
        
        def update_recursive(widget):
            try:
                if hasattr(widget, 'configure') and 'bg' in widget.configure():
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
        """Enhanced destroy with proper cleanup"""
        self._destroyed = True
        
        # Clean up event handlers
        for element, event, handler_id in self._event_handlers:
            try:
                element.unbind(event, handler_id)
            except (tk.TclError, AttributeError):
                pass
        
        self._event_handlers.clear()
        
        # Clean up references
        self.app_ref = None
        
        # Call parent destroy
        super().destroy()