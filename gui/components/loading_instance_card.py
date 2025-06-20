"""
BENSON v2.0 - FIXED Loading Instance Card Component
Optimized animations to prevent lag and freezing
"""

import tkinter as tk
import time


class LoadingInstanceCard(tk.Frame):
    """FIXED: Loading card with optimized, non-laggy animations"""
    
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
        
        # FIXED: Start optimized animations
        self._start_optimized_animations()
    
    def _setup_ui(self):
        """Setup the loading card UI"""
        # Main container with loading border
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
        
        # Simple loading icon (no animation initially)
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
        
        # Status icon
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
        
        # Right side - FIXED: Simplified progress
        self._setup_progress_section()
    
    def _setup_progress_section(self):
        """Setup simplified progress section"""
        progress_frame = tk.Frame(self.content_frame, bg="#1e2329")
        progress_frame.pack(side="right", padx=12, pady=10)
        
        # FIXED: Simpler progress dots
        self.progress_label = tk.Label(
            progress_frame,
            text="●○○○○",
            bg="#1e2329",
            fg="#ffd93d",
            font=("Segoe UI", 12),
            width=8
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Simple status detail
        self.detail_label = tk.Label(
            progress_frame,
            text="Setting up...",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 8)
        )
        self.detail_label.pack(pady=(5, 0))
    
    def _start_optimized_animations(self):
        """FIXED: Start optimized, non-laggy animations"""
        if not self.animation_running or self._destroyed:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            # FIXED: Combined animation update (less frequent calls)
            self._update_all_animations()
            
            # FIXED: Longer delay for smoother performance (800ms)
            self.animation_id = self.after(800, self._start_optimized_animations)
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def _update_all_animations(self):
        """FIXED: Update all animations in one call to reduce overhead"""
        try:
            if self._destroyed or not self.animation_running:
                return
            
            # FIXED: Simple progress animation
            patterns = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●"]
            pattern = patterns[self.animation_step % len(patterns)]
            self.progress_label.configure(text=pattern)
            
            # FIXED: Simple icon rotation (less icons, slower change)
            icons = ["⚡", "⚙"]
            icon = icons[(self.animation_step // 2) % len(icons)]
            self.loading_icon.configure(text=icon)
            
            # FIXED: Simplified border pulse (only 2 colors)
            border_colors = ["#ffd93d", "#ffeb3b"]
            border_color = border_colors[self.animation_step % len(border_colors)]
            self.main_container.configure(bg=border_color)
            
            # FIXED: Less frequent status updates
            if self.animation_step % 3 == 0:  # Update every 3rd step
                messages = ["Creating...", "Configuring...", "Optimizing...", "Finalizing..."]
                details = ["Setting up...", "Allocating RAM...", "Setting CPU...", "Almost done..."]
                
                msg_index = (self.animation_step // 3) % len(messages)
                self.status_text.configure(text=messages[msg_index])
                self.detail_label.configure(text=details[msg_index])
            
            self.animation_step += 1
            
        except (tk.TclError, AttributeError):
            self.animation_running = False
    
    def show_success(self):
        """FIXED: Simple success state without complex animations"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # FIXED: Simple success state (no animations)
            self.main_container.configure(bg="#00ff88")
            self.loading_icon.configure(text="✓", fg="#00ff88")
            self.status_icon.configure(text="✓", fg="#00ff88")
            self.status_text.configure(text="Created successfully!", fg="#00ff88")
            self.progress_label.configure(text="●●●●●", fg="#00ff88")
            self.detail_label.configure(text="Instance ready!")
            
            print(f"[LoadingCard] {self.instance_name} - Success state shown")
            
        except (tk.TclError, AttributeError):
            pass
    
    def show_error(self, error_message="Creation failed"):
        """FIXED: Simple error state without animations"""
        if self._destroyed:
            return
        
        try:
            # Stop animations
            self.animation_running = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
            
            # FIXED: Simple error state
            self.main_container.configure(bg="#ff6b6b")
            self.loading_icon.configure(text="✗", fg="#ff6b6b")
            self.status_icon.configure(text="✗", fg="#ff6b6b")
            self.status_text.configure(text="Creation failed", fg="#ff6b6b")
            self.progress_label.configure(text="✗✗✗✗✗", fg="#ff6b6b")
            
            # Truncate long error messages
            display_message = error_message[:25] + "..." if len(error_message) > 25 else error_message
            self.detail_label.configure(text=display_message)
            
            print(f"[LoadingCard] {self.instance_name} - Error state shown: {error_message}")
            
            # FIXED: Auto-destroy after delay without animation
            self.after(3000, self._simple_destroy)
            
        except (tk.TclError, AttributeError):
            pass
    
    def _simple_destroy(self):
        """FIXED: Simple destroy without fade animations"""
        try:
            self.destroy()
        except:
            pass
    
    def destroy(self):
        """FIXED: Clean destroy with animation cleanup"""
        self._destroyed = True
        self.animation_running = False
        
        # Cancel scheduled animation
        if self.animation_id:
            try:
                self.after_cancel(self.animation_id)
            except:
                pass
        
        super().destroy()


# Helper function to create loading card
def create_loading_instance_card(parent, instance_name):
    """Create a loading instance card"""
    return LoadingInstanceCard(parent, instance_name)