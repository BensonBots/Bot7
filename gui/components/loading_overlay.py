"""
BENSON v2.0 - Fixed Loading Overlay Component
Fixed animation freezing and timing issues
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
        
        # FIXED: Position relative to parent window, not screen center
        window_width = 260
        window_height = 180
        
        # Get parent position with error handling
        try:
            parent.update_idletasks()  # Ensure parent geometry is current
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            # Center on parent window
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
            print(f"[LoadingOverlay] Parent at: {parent_x}, {parent_y}")
            print(f"[LoadingOverlay] Positioning loading at: {x}, {y}")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error getting parent position: {e}")
            # Fallback to screen center
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure window background
        self.window.configure(bg="#1e2329")
        
        # FIXED: Simple animation state
        self.animation_running = True
        self.animation_step = 0
        
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
        
        # FIXED: Progress with proper width
        self.progress_frame = tk.Frame(content_frame, bg="#1e2329")
        self.progress_frame.pack()
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 8),
            width=10  # FIXED: Ensure enough width
        )
        self.progress_label.pack()
        
        # Start simple animation immediately
        self._update_animation()
        
        # Ensure window is properly sized
        self.window.update_idletasks()
        
        # FIXED: Verify position after creation
        self.window.after(100, lambda: self._verify_position(x, y))
        
        # FIXED: Single animation scheduler
        self._schedule_animation_updates()
    
    def _verify_position(self, expected_x, expected_y):
        """Verify and correct position if needed"""
        try:
            current_x = self.window.winfo_x()
            current_y = self.window.winfo_y()
            
            # If position is wrong, correct it
            if abs(current_x - expected_x) > 50 or abs(current_y - expected_y) > 50:
                print(f"[LoadingOverlay] Correcting position from {current_x},{current_y} to {expected_x},{expected_y}")
                self.window.geometry(f"+{expected_x}+{expected_y}")
                self.window.update()
                
        except Exception as e:
            print(f"[LoadingOverlay] Position verification error: {e}")
    
    def _schedule_animation_updates(self):
        """FIXED: Single animation scheduler to prevent conflicts"""
        if not self.animation_running:
            return
            
        try:
            if self.window.winfo_exists():
                self._update_animation()
                # Schedule next update
                self.window.after(200, self._schedule_animation_updates)  # Slower for smoothness
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_animation(self):
        """FIXED: Single animation method to prevent conflicts"""
        try:
            if not hasattr(self, 'progress_label') or not self.progress_label.winfo_exists():
                return
                
            # FIXED: Simple progress states - no complex patterns
            states = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●", "○○○●○", "○○●○○", "○●○○○"]
            
            # Update progress
            self.progress_label.configure(text=states[self.animation_step % len(states)])
            
            # Update icon occasionally
            if self.animation_step % 4 == 0:  # Every 4th step
                icons = ["⚡", "⚙", "🔄", "⭐"]
                icon = icons[(self.animation_step // 4) % len(icons)]
                self.icon_label.configure(text=icon)
            
            self.animation_step += 1
            
            # Force immediate update
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