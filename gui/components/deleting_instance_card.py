"""
BENSON v2.0 - Compact Deleting Instance Card
Reduced from 250+ lines to ~90 lines with same visual effects
"""

import tkinter as tk


class DeletingInstanceCard(tk.Frame):
    """Compact card showing deletion animation"""
    
    def __init__(self, parent, instance_name, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Core data
        self.instance_name = instance_name
        self.animation_running = True
        self.animation_step = 0
        self._destroyed = False
        self.animation_id = None
        
        # Configure frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3, width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI and start animation
        self._setup_ui()
        self._start_deletion_animation()
    
    def _setup_ui(self):
        """Setup deleting card UI"""
        # Main container with red deletion border
        self.main_container = tk.Frame(self, bg="#ff6b6b", relief="solid", bd=2)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        content = tk.Frame(self.main_container, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Left section
        left = tk.Frame(content, bg="#1e2329")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - deletion icon and name
        top = tk.Frame(left, bg="#1e2329")
        top.pack(fill="x", pady=(0, 4))
        
        self.deletion_icon = tk.Label(top, text="🗑", bg="#1e2329", fg="#ff6b6b", font=("Segoe UI", 11))
        self.deletion_icon.pack(side="left", padx=(0, 12))
        
        self.name_label = tk.Label(top, text=self.instance_name, bg="#1e2329", fg="#8b949e",
                                  font=("Segoe UI", 13, "bold"), anchor="w")
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom = tk.Frame(left, bg="#1e2329")
        bottom.pack(fill="x")
        
        self.status_icon = tk.Label(bottom, text="●", bg="#1e2329", fg="#ff6b6b", font=("Segoe UI", 10))
        self.status_icon.pack(side="left")
        
        self.status_text = tk.Label(bottom, text="Deleting...", bg="#1e2329", fg="#ff6b6b",
                                   font=("Segoe UI", 10), anchor="w")
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Right section - deletion progress
        right = tk.Frame(content, bg="#1e2329")
        right.pack(side="right", padx=12, pady=10)
        
        self.progress_label = tk.Label(right, text="●●●●●", bg="#1e2329", fg="#ff6b6b",
                                      font=("Segoe UI", 12), width=8)
        self.progress_label.pack(pady=(5, 0))
        
        self.detail_label = tk.Label(right, text="Removing files...", bg="#1e2329", fg="#8b949e",
                                    font=("Segoe UI", 8))
        self.detail_label.pack(pady=(5, 0))
    
    def _start_deletion_animation(self):
        """Start deletion animation loop"""
        if not self.animation_running or self._destroyed:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            self._update_deletion_animation()
            
            # Schedule next update (350ms for smooth deletion effect)
            self.animation_id = self.after(350, self._start_deletion_animation)
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_deletion_animation(self):
        """Update deletion animation elements"""
        try:
            if self._destroyed or not self.animation_running:
                return
            
            # Progress animation (shrinking dots)
            patterns = ["●●●●●", "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"]
            pattern = patterns[self.animation_step % len(patterns)]
            self.progress_label.configure(text=pattern)
            
            # Deletion icon animation
            icons = ["🗑", "🔥", "💥", "❌"]
            icon = icons[(self.animation_step // 2) % len(icons)]
            self.deletion_icon.configure(text=icon)
            
            # Border color pulse
            border_colors = ["#ff6b6b", "#ff4444", "#ff8888"]
            border_color = border_colors[self.animation_step % len(border_colors)]
            self.main_container.configure(bg=border_color)
            
            # Update status messages
            messages = ["Deleting...", "Stopping instance...", "Removing files...", "Cleaning up...", "Almost done..."]
            details = ["Removing files...", "Stopping processes...", "Clearing cache...", "Updating registry...", "Finalizing..."]
            
            msg_index = (self.animation_step // 3) % len(messages)
            self.status_text.configure(text=messages[msg_index])
            self.detail_label.configure(text=details[msg_index])
            
            self.animation_step += 1
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def show_success(self):
        """Show deletion success state"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # Show success state
            self.main_container.configure(bg="#666666")
            self.deletion_icon.configure(text="✓", fg="#00ff88")
            self.status_icon.configure(text="✓", fg="#00ff88")
            self.status_text.configure(text="Deleted successfully!", fg="#00ff88")
            self.progress_label.configure(text="○○○○○", fg="#666666")
            self.detail_label.configure(text="Instance removed")
            
            # Fade out after success
            self.after(1000, self._fade_out)
            
        except (tk.TclError, AttributeError):
            pass
    
    def show_error(self, error_message="Deletion failed"):
        """Show deletion error state"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # Show error state
            self.main_container.configure(bg="#ff3333")
            self.deletion_icon.configure(text="⚠", fg="#ffff00")
            self.status_icon.configure(text="⚠", fg="#ffff00")
            self.status_text.configure(text="Deletion failed", fg="#ffff00")
            self.progress_label.configure(text="✗✗✗✗✗", fg="#ffff00")
            
            # Truncate long error messages
            display_message = error_message[:30] + "..." if len(error_message) > 30 else error_message
            self.detail_label.configure(text=display_message)
            
            # Keep error visible longer
            self.after(5000, self._fade_out)
            
        except (tk.TclError, AttributeError):
            pass
    
    def _fade_out(self):
        """Simple fade out before removal"""
        if self._destroyed:
            return
        
        # Simple fade by changing colors
        fade_colors = ["#444444", "#333333", "#222222", "#111111", "#000000"]
        
        def fade_step(step=0):
            if self._destroyed or step >= len(fade_colors):
                self._safe_destroy()
                return
            
            try:
                color = fade_colors[step]
                self.main_container.configure(bg=color)
                
                # Fade text colors
                for widget in [self.name_label, self.status_text, self.detail_label]:
                    widget.configure(fg=color)
                
                self.after(150, lambda: fade_step(step + 1))
                
            except (tk.TclError, AttributeError):
                self._safe_destroy()
        
        fade_step()
    
    def _safe_destroy(self):
        """Safe destroy with cleanup"""
        try:
            self.destroy()
        except:
            pass
    
    def destroy(self):
        """Clean destroy with animation cleanup"""
        self._destroyed = True
        self.animation_running = False
        
        # Cancel scheduled animation
        if self.animation_id:
            try:
                self.after_cancel(self.animation_id)
            except:
                pass
        
        super().destroy()


def create_deleting_instance_card(parent, instance_name):
    """Create a deleting instance card"""
    return DeletingInstanceCard(parent, instance_name)