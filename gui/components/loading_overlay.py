"""
BENSON v2.0 - Fixed Loading Overlay Component
Fixed freezing animation issue
"""

import tkinter as tk
import time


class LoadingOverlay:
    def __init__(self, parent):
        # Create independent window
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.attributes('-topmost', True)  # Keep on top
        
        # Center the loading window (make it smaller)
        window_width = 260
        window_height = 180
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure window background
        self.window.configure(bg="#1e2329")
        
        self.animation_running = True
        self.animation_step = 0
        self.last_animation_time = time.time()
        
        # Main container (full window)
        self.overlay = tk.Frame(self.window, bg="#1e2329")
        self.overlay.pack(fill="both", expand=True)
        
        # Content frame with proper padding
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
        
        # Progress (fixed animation)
        self.progress_frame = tk.Frame(content_frame, bg="#1e2329")
        self.progress_frame.pack()
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 8)
        )
        self.progress_label.pack()
        
        # Start animation immediately
        self._update_animation()
        
        # Ensure window is properly sized
        self.window.update_idletasks()
        
        # Schedule animation updates
        self._schedule_animation_updates()
    
    def _schedule_animation_updates(self):
        """Schedule continuous animation updates"""
        if not self.animation_running:
            return
            
        try:
            if self.window.winfo_exists():
                self._update_animation()
                # Schedule next update in 150ms
                self.window.after(150, self._schedule_animation_updates)
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_animation(self):
        """Update the animation frame"""
        try:
            if not hasattr(self, 'progress_label') or not self.progress_label.winfo_exists():
                return
                
            # Progress states
            states = ["●○○○○", "●●○○○", "●●●○○", "●●●●○", "●●●●●", "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"]
            
            # Update animation
            self.progress_label.configure(text=states[self.animation_step % len(states)])
            self.animation_step += 1
            
            # Force immediate update of the label
            self.progress_label.update_idletasks()
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def update_status(self, status):
        """Update status with error handling"""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=status)
                # Force update without blocking
                if hasattr(self, 'window'):
                    self.window.update_idletasks()
        except (tk.TclError, AttributeError):
            pass
    
    def close(self):
        """Safely close the overlay"""
        self.animation_running = False
        try:
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.withdraw()  # Hide first
                self.window.update_idletasks()
                self.window.destroy()  # Then destroy
        except (tk.TclError, AttributeError):
            pass
        finally:
            # Clear references
            self.window = None