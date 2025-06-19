"""
BENSON v2.0 - FIXED Loading Overlay Component
Fixed animation freezing and timing issues with single animation scheduler
"""

import tkinter as tk
import time


class LoadingOverlay:
    def __init__(self, parent):
        # Store parent reference
        self.parent = parent
        
        # Create independent window
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.attributes('-topmost', True)  # Keep on top
        
        # Position relative to parent window
        window_width = 260
        window_height = 180
        
        # Get parent position with error handling
        try:
            parent.update_idletasks()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            # Center on parent window
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
        except Exception as e:
            print(f"[LoadingOverlay] Error getting parent position: {e}")
            # Fallback to screen center
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(bg="#1e2329")
        
        # FIXED: Single animation control
        self.animation_running = True
        self.animation_step = 0
        self.animation_id = None
        
        # Setup UI
        self._setup_ui()
        
        # FIXED: Start single animation loop
        self._start_single_animation()
    
    def _setup_ui(self):
        """Setup UI components"""
        # Main container
        self.overlay = tk.Frame(self.window, bg="#1e2329")
        self.overlay.pack(fill="both", expand=True)
        
        # Content frame
        content_frame = tk.Frame(self.overlay, bg="#1e2329")
        content_frame.pack(expand=True)
        
        # Icon
        self.icon_label = tk.Label(
            content_frame,
            text="⚡",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 24)
        )
        self.icon_label.pack(pady=(0, 10))
        
        # Title
        self.loading_label = tk.Label(
            content_frame,
            text="BENSON v2.0",
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        )
        self.loading_label.pack(pady=(0, 5))
        
        # Status
        self.status_label = tk.Label(
            content_frame,
            text="Loading...",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(0, 15))
        
        # Progress
        self.progress_frame = tk.Frame(content_frame, bg="#1e2329")
        self.progress_frame.pack()
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 8),
            width=10
        )
        self.progress_label.pack()
    
    def _start_single_animation(self):
        """FIXED: Start single animation loop without conflicts"""
        if not self.animation_running:
            return
        
        try:
            if not self.window.winfo_exists():
                return
            
            # Update animation
            self._update_animation()
            
            # Schedule next update - SINGLE scheduler only
            self.animation_id = self.window.after(300, self._start_single_animation)
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_animation(self):
        """Update animation elements"""
        try:
            if not self.animation_running or not hasattr(self, 'progress_label'):
                return
            
            # Simple progress animation
            states = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●"]
            current_state = states[self.animation_step % len(states)]
            
            self.progress_label.configure(text=current_state)
            
            # Occasionally update icon
            if self.animation_step % 5 == 0:
                icons = ["⚡", "⚙", "🔄", "⭐"]
                icon = icons[(self.animation_step // 5) % len(icons)]
                self.icon_label.configure(text=icon)
            
            self.animation_step += 1
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def update_status(self, status):
        """Update status text safely"""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=status)
                # FIXED: Non-blocking update
                self.window.update_idletasks()
        except (tk.TclError, AttributeError):
            pass
    
    def close(self):
        """FIXED: Safe close with animation cleanup"""
        self.animation_running = False
        
        # Cancel scheduled animation
        if self.animation_id:
            try:
                self.window.after_cancel(self.animation_id)
            except:
                pass
        
        try:
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.withdraw()
                self.window.destroy()
        except (tk.TclError, AttributeError):
            pass
        finally:
            self.window = None
            self.animation_id = None