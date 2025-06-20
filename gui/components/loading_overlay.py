"""
BENSON v2.0 - FIXED Loading Overlay Component
Fixed positioning for multi-monitor setups and proper centering
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
        
        # Position on PRIMARY MONITOR CENTER - FIXED for multi-monitor
        window_width = 260
        window_height = 180
        
        # FIXED: Get primary monitor dimensions
        try:
            # Force parent to update first
            parent.update_idletasks()
            
            # Get primary screen dimensions (not parent window)
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Center on PRIMARY screen
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            print(f"[LoadingOverlay] Screen: {screen_width}x{screen_height}, Centering at: {x},{y}")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error getting screen dimensions: {e}")
            # Fallback positioning
            x = 500
            y = 300
        
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
    
    def __init__(self, parent_app):
        """FIXED: Create loading overlay with proper animation"""
        self.parent_app = parent_app
        self.animation_running = True
        self.animation_id = None
        self.dots_count = 0
        
        # Create window
        self.create_window()
        
        # Start animation
        self.animate_dots()
        
    def create_window(self):
        """Create the loading window"""
        try:
            self.window = tk.Toplevel(self.parent_app)
            self.window.title("Loading BENSON...")
            self.window.geometry("400x300")
            self.window.configure(bg="#1e2329")
            self.window.resizable(False, False)
            
            # Remove decorations for loading screen
            self.window.overrideredirect(True)
            
            # Make it modal and on top
            self.window.transient(self.parent_app)
            self.window.grab_set()
            
            # Center on screen
            self.center_on_screen()
            
            # Create content
            self.setup_content()
            
            print("[LoadingOverlay] Window created")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error creating window: {e}")
    
    def setup_content(self):
        """Setup loading content with BENSON design"""
        # Main container
        main_frame = tk.Frame(self.window, bg="#1e2329")
        main_frame.pack(fill="both", expand=True)
        
        # Logo/Icon
        logo_label = tk.Label(
            main_frame,
            text="🎯",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Arial", 48)
        )
        logo_label.pack(pady=(60, 20))
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="BENSON v2.0",
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Advanced MEmu Instance Manager",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Status
        self.status_label = tk.Label(
            main_frame,
            text="Starting up...",
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 11)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Animated dots
        self.dots_label = tk.Label(
            main_frame,
            text="•○○○",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Arial", 16)
        )
        self.dots_label.pack()

    def center_on_screen(self):
        """Center loading window on screen"""
        try:
            # Get parent window position if available
            if self.parent_app.winfo_viewable():
                parent_x = self.parent_app.winfo_rootx()
                parent_y = self.parent_app.winfo_rooty()
                parent_width = self.parent_app.winfo_width()
                parent_height = self.parent_app.winfo_height()
                
                x = parent_x + (parent_width - 400) // 2
                y = parent_y + (parent_height - 300) // 2
            else:
                # Center on screen
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 300) // 2
            
            self.window.geometry(f"400x300+{x}+{y}")
            print(f"[LoadingOverlay] Centered at {x},{y}")
            
        except Exception as e:
            print(f"[LoadingOverlay] Error centering: {e}")

    def animate_dots(self):
        """Animate loading dots"""
        if not self.animation_running:
            return
            
        try:
            # Update dots pattern
            self.dots_count = (self.dots_count + 1) % 4
            dots = "•" * self.dots_count + "○" * (4 - self.dots_count)
            
            if hasattr(self, 'dots_label') and self.dots_label.winfo_exists():
                self.dots_label.config(text=dots)
            
            # Schedule next animation
            if self.animation_running:
                self.animation_id = self.window.after(400, self.animate_dots)
                
        except Exception as e:
            print(f"[LoadingOverlay] Animation error: {e}")
            self.animation_running = False

    def update_status(self, message):
        """Update status message"""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.config(text=message)
                print(f"[LoadingOverlay] Status: {message}")
        except Exception as e:
            print(f"[LoadingOverlay] Status update error: {e}")

    def close(self):
        """Close loading overlay cleanly"""
        try:
            print("[LoadingOverlay] Closing...")
            self.animation_running = False
            
            if self.animation_id:
                try:
                    self.window.after_cancel(self.animation_id)
                except:
                    pass
            
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.grab_release()
                self.window.destroy()
                print("[LoadingOverlay] Closed successfully")
                
        except Exception as e:
            print(f"[LoadingOverlay] Error closing: {e}")