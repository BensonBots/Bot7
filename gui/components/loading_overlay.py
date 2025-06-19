"""
BENSON v2.0 - Fixed Loading Overlay Component
Fixed freezing animation issue
"""

import tkinter as tk


class LoadingOverlay:
    def __init__(self, parent):
        self.parent = parent
        self.animation_running = True
        self.animation_step = 0
        
        # Create overlay
        self.overlay = tk.Frame(parent, bg="#0a0e16")
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main container
        loading_container = tk.Frame(self.overlay, bg="#1e2329", relief="solid", bd=1)
        loading_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Content
        content_frame = tk.Frame(loading_container, bg="#1e2329")
        content_frame.pack(padx=40, pady=30)
        
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
        self.progress_label = tk.Label(
            content_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 8)
        )
        self.progress_label.pack()
        
        # Start animation with proper error handling
        self.animate()
    
    def animate(self):
        """Fixed animation that won't freeze"""
        if not self.animation_running:
            return
        
        try:
            # Progress states
            states = ["●○○○○", "●●○○○", "●●●○○", "●●●●○", "●●●●●", "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"]
            
            # Update progress
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=states[self.animation_step % len(states)])
                self.animation_step += 1
            
            # Schedule next frame with error handling
            if self.animation_running and hasattr(self, 'parent'):
                try:
                    self.parent.after(150, self.animate)  # Slower animation to prevent issues
                except tk.TclError:
                    # Parent window was destroyed
                    self.animation_running = False
            
        except (tk.TclError, AttributeError):
            # Handle widget destruction gracefully
            self.animation_running = False
    
    def update_status(self, status):
        """Update status with error handling"""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=status)
                # Force update without blocking
                self.parent.update_idletasks()
        except (tk.TclError, AttributeError):
            # Widget may have been destroyed
            pass
    
    def close(self):
        """Safely close the overlay"""
        self.animation_running = False
        try:
            if hasattr(self, 'overlay') and self.overlay.winfo_exists():
                self.overlay.destroy()
        except (tk.TclError, AttributeError):
            pass
        finally:
            # Clear references
            self.overlay = None
            self.parent = None