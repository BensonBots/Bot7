"""
BENSON v2.0 - FIXED Loading Overlay - Integrated into Main GUI
No external window - uses overlay on main window
"""

import tkinter as tk
import time


class IntegratedLoadingOverlay:
    """Loading overlay that appears on top of main window instead of separate window"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.overlay_frame = None
        self.animation_running = True
        self.animation_step = 0
        self.animation_id = None
        
        # Create overlay immediately
        self._create_overlay()
        
        # Start animation
        self._start_animation()
    
    def _create_overlay(self):
        """Create loading overlay on top of main window"""
        try:
            # Create overlay frame that covers the entire main window
            self.overlay_frame = tk.Frame(
                self.parent_app,
                bg="#1e2329",
                relief="flat",
                bd=0
            )
            
            # Place overlay on top of everything
            self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Create semi-transparent background effect
            bg_frame = tk.Frame(self.overlay_frame, bg="#0a0e16")
            bg_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Create centered loading content
            content_frame = tk.Frame(bg_frame, bg="#1e2329", relief="solid", bd=2)
            content_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=250)
            
            # BENSON logo
            logo_label = tk.Label(
                content_frame,
                text="🎯",
                bg="#1e2329",
                fg="#00d4ff",
                font=("Segoe UI", 48)
            )
            logo_label.pack(pady=(30, 15))
            
            # Title
            title_label = tk.Label(
                content_frame,
                text="BENSON v2.0",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 18, "bold")
            )
            title_label.pack(pady=(0, 5))
            
            # Subtitle
            subtitle_label = tk.Label(
                content_frame,
                text="Advanced MEmu Instance Manager",
                bg="#1e2329",
                fg="#8b949e",
                font=("Segoe UI", 10)
            )
            subtitle_label.pack(pady=(0, 20))
            
            # Status text
            self.status_label = tk.Label(
                content_frame,
                text="Initializing...",
                bg="#1e2329",
                fg="#ffffff",
                font=("Segoe UI", 11)
            )
            self.status_label.pack(pady=(0, 10))
            
            # Animated progress dots
            self.progress_label = tk.Label(
                content_frame,
                text="●○○○○",
                bg="#1e2329",
                fg="#00d4ff",
                font=("Segoe UI", 14)
            )
            self.progress_label.pack()
            
            # Bring overlay to front
            self.overlay_frame.lift()
            
            print("[LoadingOverlay] Integrated overlay created")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error creating overlay: {e}")
    
    def _start_animation(self):
        """Start loading animation"""
        if not self.animation_running or not self.overlay_frame:
            return
        
        try:
            # Update progress dots
            patterns = [
                "●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●",
                "○○○●○", "○○●○○", "○●○○○"
            ]
            
            if self.progress_label and self.progress_label.winfo_exists():
                pattern = patterns[self.animation_step % len(patterns)]
                self.progress_label.configure(text=pattern)
            
            self.animation_step += 1
            
            # Schedule next animation frame
            if self.animation_running:
                self.animation_id = self.parent_app.after(300, self._start_animation)
                
        except tk.TclError:
            # Widget destroyed, stop animation
            self.animation_running = False
        except Exception as e:
            print(f"[LoadingOverlay] Animation error: {e}")
            self.animation_running = False
    
    def update_status(self, status_text):
        """Update status text"""
        try:
            if self.status_label and self.status_label.winfo_exists():
                self.status_label.configure(text=status_text)
                self.parent_app.update_idletasks()  # Force immediate update
                print(f"[LoadingOverlay] Status: {status_text}")
        except tk.TclError:
            pass
        except Exception as e:
            print(f"[LoadingOverlay] Status update error: {e}")
    
    def close(self):
        """Close the loading overlay"""
        try:
            print("[LoadingOverlay] Closing integrated overlay...")
            
            # Stop animation
            self.animation_running = False
            if self.animation_id:
                try:
                    self.parent_app.after_cancel(self.animation_id)
                except:
                    pass
            
            # Destroy overlay frame
            if self.overlay_frame and self.overlay_frame.winfo_exists():
                self.overlay_frame.destroy()
                
            self.overlay_frame = None
            self.status_label = None
            self.progress_label = None
            
            print("[LoadingOverlay] Integrated overlay closed")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error closing overlay: {e}")
    
    def is_visible(self):
        """Check if overlay is visible"""
        return (self.overlay_frame is not None and 
                self.overlay_frame.winfo_exists() and 
                self.overlay_frame.winfo_viewable())