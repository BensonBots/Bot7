"""
BENSON v2.0 - Search Bar Component
Search functionality for filtering instances
"""

import tkinter as tk


class SearchBar(tk.Frame):
    def __init__(self, parent, on_search_callback, **kwargs):
        super().__init__(parent, bg="#0a0e16", **kwargs)
        self.on_search = on_search_callback
        
        self._setup_search_bar()
    
    def _setup_search_bar(self):
        """Setup the search bar components"""
        # Search icon
        search_icon = tk.Label(
            self,
            text="🔍",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 12)
        )
        search_icon.pack(side="left", padx=(8, 4))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        
        self.search_entry = tk.Entry(
            self,
            textvariable=self.search_var,
            bg="#1e2329",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            insertbackground="#00d4ff"
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        
        # Placeholder text
        self.search_entry.insert(0, "Search instances...")
        self.search_entry.bind("<FocusIn>", self.on_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_focus_out)
        
        # Configure frame appearance
        self.configure(bg="#1e2329", relief="solid", bd=1, highlightbackground="#343a46")
    
    def on_focus_in(self, event):
        """Handle focus in event"""
        if self.search_entry.get() == "Search instances...":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg="#ffffff")
    
    def on_focus_out(self, event):
        """Handle focus out event"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search instances...")
            self.search_entry.configure(fg="#8b949e")
    
    def on_search_change(self, *args):
        """Handle search text change"""
        query = self.search_var.get()
        if query != "Search instances...":
            self.on_search(query)
    
    def clear_search(self):
        """Clear the search field"""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, "Search instances...")
        self.search_entry.configure(fg="#8b949e")
        self.on_search("")
    
    def set_search_text(self, text):
        """Set the search text programmatically"""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)
        self.search_entry.configure(fg="#ffffff")
        self.on_search(text)