"""
BENSON v2.0 - Loading Overlay Component
Loading screen with animation
"""

import tkinter as tk


class LoadingOverlay:
    def __init__(self, parent, status_text="Loading..."):
        self.parent = parent
        
        # Create overlay frame that covers the entire window
        self.overlay = tk.Frame(parent, bg="#0a0e16")
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main loading container
        loading_container = tk.Frame(self.overlay, bg="#1e2329", relief="solid", bd=1)
        loading_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Content frame
        content_frame = tk.Frame(loading_container, bg="#1e2329")
        content_frame.pack(padx=40, pady=30)
        
        # Spinning icon
        self.icon_label = tk.Label(
            content_frame,
            text="⚡",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 24)
        )
        self.icon_label.pack(pady=(0, 10))
        
        # Loading text
        self.loading_label = tk.Label(
            content_frame,
            text="BENSON v2.0",
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        )
        self.loading_label.pack(pady=(0, 5))
        
        # Status text
        self.status_label = tk.Label(
            content_frame,
            text=status_text,
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(0, 15))
        
        # Simple progress indicator
        self.progress_label = tk.Label(
            content_frame,
            text="●●●●●",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 8)
        )
        self.progress_label.pack()
        
        # Start animation
        self.animation_running = True
        self.animate()
    
    def animate(self):
        """Animate the loading indicator"""
        if not self.animation_running:
            return
        
        # Simple progress animation
        progress_states = ["●○○○○", "●●○○○", "●●●○○", "●●●●○", "●●●●●", "○●●●●", "○○●●●", "○○○●●", "○○○○●", "○○○○○"]
        
        try:
            current_progress = self.progress_label.cget("text")
            current_index = progress_states.index(current_progress) if current_progress in progress_states else 0
            next_index = (current_index + 1) % len(progress_states)
            self.progress_label.configure(text=progress_states[next_index])
        except:
            pass
        
        # Continue animation
        if self.animation_running:
            self.parent.after(200, self.animate)
    
    def update_status(self, status):
        """Update the status text"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=status)
            self.parent.update()
    
    def close(self):
        """Close the loading overlay"""
        self.animation_running = False
        try:
            self.overlay.destroy()
        except:
            pass