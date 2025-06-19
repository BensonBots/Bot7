"""
BENSON v2.0 - Deleting Instance Card Component
Shows a card with deletion animation instead of loading overlay
"""

import tkinter as tk


class DeletingInstanceCard(tk.Frame):
    """Card that shows deletion animation for instances being deleted"""
    
    def __init__(self, parent, instance_name, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Store data
        self.instance_name = instance_name
        self.animation_running = True
        self.animation_step = 0
        self._destroyed = False
        self.animation_id = None
        
        # Configure the main card frame
        self.configure(bg="#1e2329", relief="flat", bd=0, padx=3, pady=3)
        self.configure(width=580, height=85)
        self.pack_propagate(False)
        
        # Setup UI
        self._setup_ui()
        
        # Start deletion animation
        self._start_deletion_animation()
    
    def _setup_ui(self):
        """Setup the deleting card UI"""
        # Main container with deletion border (red)
        self.main_container = tk.Frame(self, bg="#ff6b6b", relief="solid", bd=2)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Content frame
        self.content_frame = tk.Frame(self.main_container, bg="#1e2329")
        self.content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Left side - info section
        left_frame = tk.Frame(self.content_frame, bg="#1e2329")
        left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row - deletion icon and name
        top_row = tk.Frame(left_frame, bg="#1e2329")
        top_row.pack(fill="x", pady=(0, 4))
        
        # Animated deletion icon
        self.deletion_icon = tk.Label(
            top_row,
            text="🗑",
            bg="#1e2329",
            fg="#ff6b6b",
            font=("Segoe UI", 11)
        )
        self.deletion_icon.pack(side="left", padx=(0, 12))
        
        # Instance name (grayed out)
        self.name_label = tk.Label(
            top_row,
            text=self.instance_name,
            bg="#1e2329",
            fg="#8b949e",  # Grayed out
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row - status
        bottom_row = tk.Frame(left_frame, bg="#1e2329")
        bottom_row.pack(fill="x")
        
        # Status icon
        self.status_icon = tk.Label(
            bottom_row,
            text="●",
            bg="#1e2329",
            fg="#ff6b6b",
            font=("Segoe UI", 10)
        )
        self.status_icon.pack(side="left")
        
        # Status text
        self.status_text = tk.Label(
            bottom_row,
            text="Deleting...",
            bg="#1e2329",
            fg="#ff6b6b",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Right side - deletion progress
        self._setup_deletion_section()
    
    def _setup_deletion_section(self):
        """Setup deletion progress section"""
        deletion_frame = tk.Frame(self.content_frame, bg="#1e2329")
        deletion_frame.pack(side="right", padx=12, pady=10)
        
        # Progress dots (deletion style)
        self.progress_frame = tk.Frame(deletion_frame, bg="#1e2329")
        self.progress_frame.pack()
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●●●●●",
            bg="#1e2329",
            fg="#ff6b6b",
            font=("Segoe UI", 12),
            width=8
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Status detail
        self.detail_label = tk.Label(
            deletion_frame,
            text="Removing files...",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 8)
        )
        self.detail_label.pack(pady=(5, 0))
    
    def _start_deletion_animation(self):
        """Start deletion animation loop"""
        if not self.animation_running or self._destroyed:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            # Update deletion animation
            self._update_deletion_animation()
            
            # Schedule next update
            self.animation_id = self.after(350, self._start_deletion_animation)
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_deletion_animation(self):
        """Update deletion animation elements"""
        try:
            if self._destroyed or not self.animation_running:
                return
            
            # Deletion progress (shrinking dots)
            patterns = ["●●●●●", "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"]
            pattern = patterns[self.animation_step % len(patterns)]
            self.progress_label.configure(text=pattern)
            
            # Update deletion icon
            icons = ["🗑", "🔥", "💥", "❌"]
            icon = icons[(self.animation_step // 2) % len(icons)]
            self.deletion_icon.configure(text=icon)
            
            # Update border color (pulsing red)
            border_colors = ["#ff6b6b", "#ff4444", "#ff8888"]
            border_color = border_colors[self.animation_step % len(border_colors)]
            self.main_container.configure(bg=border_color)
            
            # Update status messages
            messages = [
                "Deleting...",
                "Stopping instance...",
                "Removing files...",
                "Cleaning up...",
                "Almost done..."
            ]
            
            details = [
                "Removing files...",
                "Stopping processes...",
                "Clearing cache...",
                "Updating registry...",
                "Finalizing..."
            ]
            
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
        """Fade out animation before removal"""
        if self._destroyed:
            return
        
        # Simple fade by changing opacity-like effect
        fade_colors = ["#444444", "#333333", "#222222", "#111111", "#000000"]
        
        def fade_step(step=0):
            if self._destroyed or step >= len(fade_colors):
                self._safe_destroy()
                return
            
            try:
                self.main_container.configure(bg=fade_colors[step])
                # Fade text colors too
                fade_text_color = fade_colors[step]
                for widget in [self.name_label, self.status_text, self.detail_label]:
                    widget.configure(fg=fade_text_color)
                
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


# Helper function to create deleting card
def create_deleting_instance_card(parent, instance_name):
    """Create a deleting instance card"""
    return DeletingInstanceCard(parent, instance_name)