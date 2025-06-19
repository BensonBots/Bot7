"""
BENSON v2.0 - Progress Bar Component
Loading and progress indication
"""

import tkinter as tk
from tkinter import ttk


class ProgressBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#0a0e16", **kwargs)
        
        self._setup_progress_bar()
    
    def _setup_progress_bar(self):
        """Setup the progress bar components"""
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=300,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=5)
        
        self.label = tk.Label(
            self,
            text="",
            bg="#0a0e16",
            fg="#00d4ff",
            font=("Segoe UI", 10)
        )
        self.label.pack()
        
        # Configure custom style
        self._configure_style()
    
    def _configure_style(self):
        """Configure the progress bar style"""
        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar", 
                       background="#00d4ff",
                       troughcolor="#1e2329",
                       borderwidth=0)
    
    def start_progress(self, text="Processing..."):
        """Start the progress bar with text"""
        self.label.configure(text=text)
        self.progress.start(10)
        self.pack(fill="x", padx=20, pady=10)
    
    def stop_progress(self):
        """Stop and hide the progress bar"""
        self.progress.stop()
        self.pack_forget()
    
    def set_progress_text(self, text):
        """Update the progress text"""
        self.label.configure(text=text)