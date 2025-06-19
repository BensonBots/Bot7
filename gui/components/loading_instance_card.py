"""
BENSON v2.0 - Loading Instance Card Component
Shows a fake instance card with loading animation during creation
"""

import tkinter as tk
import time


class LoadingInstanceCard(tk.Frame):
    """Fake instance card that shows loading animation during creation"""
    
    def __init__(self, parent, instance_name, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Store data
        self.instance_name = instance_name
        self.animation_running = True
        self.animation_step = 0
        self._destroyed = False
        
        # Configure the main card frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3)
        self.configure(width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI
        self._setup_ui()
        
        # Start animations
        self._start_animations()
    
    def _setup_ui(self):
        """Setup the loading card UI"""
        # Main container with special loading border
        self.main_container = tk.Frame(self, bg="#ffd93d", relief="solid", bd=2)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Content frame
        self.content_frame = tk.Frame(self.main_container, bg="#1e2329")
        self.content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Left side - info section
        left_frame = tk.Frame(self.content_frame, bg="#1e2329")
        left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - loading icon and name
        top_row = tk.Frame(left_frame, bg="#1e2329")
        top_row.pack(fill="x", pady=(0, 4))
        
        # Animated loading icon instead of checkbox
        self.loading_icon = tk.Label(
            top_row,
            text="⚡",
            bg="#1e2329",
            fg="#ffd93d",
            font=("Segoe UI", 11)
        )
        self.loading_icon.pack(side="left", padx=(0, 12))
        
        # Instance name
        self.name_label = tk.Label(
            top_row,
            text=self.instance_name,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom_row = tk.Frame(left_frame, bg="#1e2329")
        bottom_row.pack(fill="x")
        
        # Animated status
        self.status_icon = tk.Label(
            bottom_row,
            text="●",
            bg="#1e2329",
            fg="#ffd93d",
            font=("Segoe UI", 10)
        )
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(
            bottom_row,
            text="Creating...",
            bg="#1e2329",
            fg="#ffd93d",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Right side - loading animation
        self._setup_loading_section()
    
    def _setup_loading_section(self):
        """Setup the right side loading animation"""
        loading_frame = tk.Frame(self.content_frame, bg="#1e2329")
        loading_frame.pack(side="right", padx=12, pady=10)
        
        # Progress dots
        self.progress_frame = tk.Frame(loading_frame, bg="#1e2329")
        self.progress_frame.pack()
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#ffd93d",
            font=("Segoe UI", 12),
            width=8
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Status detail
        self.detail_label = tk.Label(
            loading_frame,
            text="Setting up MEmu...",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 8)
        )
        self.detail_label.pack(pady=(5, 0))
    
    def _start_animations(self):
        """Start all animations"""
        self._animate_loading_icon()
        self._animate_progress_dots()
        self._animate_border()
        self._cycle_status_messages()
    
    def _animate_loading_icon(self):
        """Animate the loading icon"""
        if self._destroyed or not self.animation_running:
            return
        
        icons = ["⚡", "⚙", "🔄", "⭐"]
        try:
            icon = icons[self.animation_step % len(icons)]
            self.loading_icon.configure(text=icon)
            self.after(500, self._animate_loading_icon)
        except tk.TclError:
            pass
    
    def _animate_progress_dots(self):
        """Animate the progress dots"""
        if self._destroyed or not self.animation_running:
            return
        
        patterns = [
            "●○○○○", "●●○○○", "●●●○○", "●●●●○", "●●●●●",
            "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"
        ]
        
        try:
            pattern = patterns[self.animation_step % len(patterns)]
            self.progress_label.configure(text=pattern)
            self.after(200, self._animate_progress_dots)
        except tk.TclError:
            pass
    
    def _animate_border(self):
        """Animate the border color"""
        if self._destroyed or not self.animation_running:
            return
        
        colors = ["#ffd93d", "#ffeb3b", "#fff176", "#ffeb3b"]
        try:
            color = colors[self.animation_step % len(colors)]
            self.main_container.configure(bg=color)
            self.after(300, self._animate_border)
        except tk.TclError:
            pass
    
    def _cycle_status_messages(self):
        """Cycle through status messages"""
        if self._destroyed or not self.animation_running:
            return
        
        messages = [
            "Creating instance...",
            "Configuring MEmu...",
            "Allocating resources...",
            "Optimizing settings...",
            "Finalizing setup..."
        ]
        
        details = [
            "Setting up MEmu...",
            "Configuring RAM...",
            "Setting CPU cores...",
            "Applying settings...",
            "Almost done..."
        ]
        
        try:
            msg_index = (self.animation_step // 5) % len(messages)
            self.status_text.configure(text=messages[msg_index])
            self.detail_label.configure(text=details[msg_index])
            self.animation_step += 1
            self.after(1000, self._cycle_status_messages)
        except tk.TclError:
            pass
    
    def show_success(self):
        """Show success state briefly before removal"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            
            # Show success state
            self.main_container.configure(bg="#00ff88")
            self.loading_icon.configure(text="✓", fg="#00ff88")
            self.status_icon.configure(text="✓", fg="#00ff88")
            self.status_text.configure(text="Created successfully!", fg="#00ff88")
            self.progress_label.configure(text="●●●●●", fg="#00ff88")
            self.detail_label.configure(text="Instance ready!")
            
            # Animate success
            self._animate_success_pulse()
            
        except tk.TclError:
            pass
    
    def show_error(self, error_message="Creation failed"):
        """Show error state before removal"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            
            # Show error state
            self.main_container.configure(bg="#ff6b6b")
            self.loading_icon.configure(text="✗", fg="#ff6b6b")
            self.status_icon.configure(text="✗", fg="#ff6b6b")
            self.status_text.configure(text="Creation failed", fg="#ff6b6b")
            self.progress_label.configure(text="✗✗✗✗✗", fg="#ff6b6b")
            self.detail_label.configure(text=error_message[:30] + "..." if len(error_message) > 30 else error_message)
            
            # Animate error shake
            self._animate_error_shake()
            
            # Auto-remove after 5 seconds
            self.after(5000, self._fade_out_and_remove)
            
        except tk.TclError:
            pass
    
    def _animate_success_pulse(self):
        """Pulse animation for success"""
        def pulse(step=0):
            if self._destroyed or step > 6:
                return
            
            try:
                colors = ["#00ff88", "#00cc66", "#00ff88"]
                color = colors[step % len(colors)]
                self.main_container.configure(bg=color)
                self.after(150, lambda: pulse(step + 1))
            except tk.TclError:
                pass
        
        pulse()
    
    def _animate_error_shake(self):
        """Shake animation for error"""
        original_x = self.winfo_x()
        
        def shake(step=0):
            if self._destroyed or step > 8:
                return
            
            try:
                offset = 5 if step % 2 == 0 else -5
                # Since we can't easily move the frame, we'll use a visual shake effect
                if step % 2 == 0:
                    self.configure(bg="#ff4444")
                else:
                    self.configure(bg="#1e2329")
                
                self.after(100, lambda: shake(step + 1))
            except tk.TclError:
                pass
        
        shake()
    
    def _fade_out_and_remove(self):
        """Fade out animation before removal"""
        if self._destroyed:
            return
        
        # Simple fade by changing opacity-like effect
        fade_colors = ["#ff6b6b", "#cc5555", "#aa4444", "#883333", "#661111", "#441111"]
        
        def fade_step(step=0):
            if self._destroyed or step >= len(fade_colors):
                self.destroy()
                return
            
            try:
                self.main_container.configure(bg=fade_colors[step])
                self.after(100, lambda: fade_step(step + 1))
            except tk.TclError:
                self.destroy()
        
        fade_step()
    
    def destroy(self):
        """Clean destroy"""
        self._destroyed = True
        self.animation_running = False
        super().destroy()


# Helper function to create loading card
def create_loading_instance_card(parent, instance_name):
    """Create a loading instance card"""
    return LoadingInstanceCard(parent, instance_name)