"""
BENSON v2.0 - Compact Loading Instance Card
Reduced from 200+ lines to ~80 lines with same visual effects
"""

import tkinter as tk
import time


class LoadingInstanceCard(tk.Frame):
    """Compact loading card with smooth animations"""
    
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
        
        # Setup UI and start animations
        self._setup_ui()
        self._start_animations()
    
    def _setup_ui(self):
        """Setup loading card UI"""
        # Main container with animated border
        self.main_container = tk.Frame(self, bg="#ffd93d", relief="solid", bd=2)
        self.main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        content = tk.Frame(self.main_container, bg="#1e2329")
        content.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Left section - icon, name, status
        left = tk.Frame(content, bg="#1e2329")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        
        # Top row
        top = tk.Frame(left, bg="#1e2329")
        top.pack(fill="x", pady=(0, 4))
        
        self.loading_icon = tk.Label(top, text="⚡", bg="#1e2329", fg="#ffd93d", font=("Segoe UI", 11))
        self.loading_icon.pack(side="left", padx=(0, 12))
        
        tk.Label(top, text=self.instance_name, bg="#1e2329", fg="#ffffff",
                font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        
        # Bottom row
        bottom = tk.Frame(left, bg="#1e2329")
        bottom.pack(fill="x")
        
        tk.Label(bottom, text="●", bg="#1e2329", fg="#ffd93d", font=("Segoe UI", 10)).pack(side="left")
        
        self.status_text = tk.Label(bottom, text="Creating...", bg="#1e2329", fg="#ffd93d",
                                   font=("Segoe UI", 10), anchor="w")
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Right section - progress indicator
        right = tk.Frame(content, bg="#1e2329")
        right.pack(side="right", padx=12, pady=10)
        
        self.detail_label = tk.Label(right, text="Setting up...", bg="#1e2329", fg="#8b949e", font=("Segoe UI", 8))
        self.detail_label.pack(pady=(5, 0))
    
    def _start_animations(self):
        """Start smooth animations"""
        if not self.animation_running or self._destroyed:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            self._update_animations()
            
            # Schedule next update (smooth 800ms intervals)
            self.animation_id = self.after(800, self._start_animations)
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_animations(self):
        """Update all animations"""
        try:
            if self._destroyed or not self.animation_running:
                return
            
            # Animate icon (simple 2-state rotation)
            icons = ["⚡", "⚙"]
            icon = icons[(self.animation_step // 2) % len(icons)]
            self.loading_icon.configure(text=icon)
            
            # Animate border (2-color pulse)
            border_colors = ["#ffd93d", "#ffeb3b"]
            border_color = border_colors[self.animation_step % len(border_colors)]
            self.main_container.configure(bg=border_color)
            
            # Update status text every 3rd step
            if self.animation_step % 3 == 0:
                messages = ["Creating...", "Configuring...", "Optimizing...", "Finalizing..."]
                details = ["Setting up...", "Allocating RAM...", "Setting CPU...", "Almost done..."]
                
                msg_index = (self.animation_step // 3) % len(messages)
                self.status_text.configure(text=messages[msg_index])
                self.detail_label.configure(text=details[msg_index])
            
            self.animation_step += 1
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def show_success(self):
        """Show success state"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # Show success state
            self.main_container.configure(bg="#00ff88")
            self.loading_icon.configure(text="✓", fg="#00ff88")
            self.status_text.configure(text="Created successfully!", fg="#00ff88")
            self.detail_label.configure(text="Instance ready!")
            
            print(f"[LoadingCard] {self.instance_name} - Success state shown")
            
        except (tk.TclError, AttributeError):
            pass
    
    def show_error(self, error_message="Creation failed"):
        """Show error state"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # Show error state
            self.main_container.configure(bg="#ff6b6b")
            self.loading_icon.configure(text="✗", fg="#ff6b6b")
            self.status_text.configure(text="Creation failed", fg="#ff6b6b")
            
            # Truncate long error messages
            display_message = error_message[:25] + "..." if len(error_message) > 25 else error_message
            self.detail_label.configure(text=display_message)
            
            print(f"[LoadingCard] {self.instance_name} - Error state shown: {error_message}")
            
            # Auto-destroy after delay
            self.after(3000, self._safe_destroy)
            
        except (tk.TclError, AttributeError):
            pass
    
    def _safe_destroy(self):
        """Safe destroy without complex animations"""
        try:
            self.destroy()
        except:
            pass
    
    def destroy(self):
        """Clean destroy with animation cleanup"""
        self._destroyed = True
        self.animation_running = False
        
        # Cancel animation
        if self.animation_id:
            try:
                self.after_cancel(self.animation_id)
            except:
                pass
        
        super().destroy()


def create_loading_instance_card(parent, instance_name):
    """Create a loading instance card"""
    return LoadingInstanceCard(parent, instance_name)