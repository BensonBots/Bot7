"""
BENSON v2.0 - Log Viewer Dialog
View instance logs and activity
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class LogViewer:
    def __init__(self, parent, instance_name, app_ref=None):
        self.parent = parent
        self.instance_name = instance_name
        self.app_ref = app_ref
        
        self._create_window()
        self._setup_content()
        self._load_logs()
    
    def _create_window(self):
        """Create the log viewer window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"{self.instance_name} - Logs")
        self.window.geometry("700x500")
        self.window.configure(bg="#1e2329")
        self.window.transient(self.parent)
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"700x500+{x}+{y}")
    
    def _setup_content(self):
        """Setup the window content"""
        # Header
        header_frame = tk.Frame(self.window, bg="#1e2329")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Title
        title = tk.Label(
            header_frame,
            text=f"📋 {self.instance_name} - Activity Logs",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 14, "bold")
        )
        title.pack(side="left")
        
        # Control buttons
        self._create_control_buttons(header_frame)
        
        # Log level filter
        self._create_log_filter(header_frame)
        
        # Log text area
        self._create_log_text_area()
        
        # Footer with info
        self._create_footer()
    
    def _create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = tk.Frame(parent, bg="#1e2329")
        button_frame.pack(side="right")
        
        # Refresh button
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 Refresh",
            bg="#1a1f2e",
            fg="#00d4ff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._refresh_logs
        )
        refresh_btn.pack(side="right", padx=(5, 0))
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="🗑 Clear",
            bg="#1a1f2e",
            fg="#ff6b6b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._clear_logs
        )
        clear_btn.pack(side="right", padx=(5, 0))
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save",
            bg="#1a1f2e",
            fg="#00ff88",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._save_logs
        )
        save_btn.pack(side="right")
    
    def _create_log_filter(self, parent):
        """Create log level filter"""
        filter_frame = tk.Frame(parent, bg="#1e2329")
        filter_frame.pack(side="right", padx=(0, 20))
        
        filter_label = tk.Label(
            filter_frame,
            text="Level:",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 9)
        )
        filter_label.pack(side="left")
        
        self.log_level_var = tk.StringVar(value="All")
        log_levels = ["All", "INFO", "DEBUG", "WARNING", "ERROR"]
        
        self.level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_level_var,
            values=log_levels,
            width=8,
            state="readonly",
            font=("Segoe UI", 8)
        )
        self.level_combo.pack(side="left", padx=(5, 0))
        self.level_combo.bind("<<ComboboxSelected>>", self._filter_logs)
    
    def _create_log_text_area(self):
        """Create the log text area"""
        # Frame for text area and scrollbar
        text_frame = tk.Frame(self.window, bg="#161b22", relief="solid", bd=1)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Text widget
        self.log_text = tk.Text(
            text_frame,
            bg="#0a0e16",
            fg="#58a6ff",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            insertbackground="#58a6ff",
            selectbackground="#264f78",
            padx=10,
            pady=8
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack text and scrollbar
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure text tags for different log levels
        self._configure_text_tags()
    
    def _create_footer(self):
        """Create footer with info"""
        footer = tk.Frame(self.window, bg="#1e2329")
        footer.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = tk.Label(
            footer,
            text="Ready",
            bg="#1e2329",
            fg="#8b949e",
            font=("Segoe UI", 8)
        )
        self.status_label.pack(side="left")
        
        # Close button
        close_btn = tk.Button(
            footer,
            text="Close",
            bg="#ff6b6b",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.window.destroy
        )
        close_btn.pack(side="right")
    
    def _configure_text_tags(self):
        """Configure text tags for different log levels"""
        self.log_text.tag_configure("INFO", foreground="#58a6ff")
        self.log_text.tag_configure("DEBUG", foreground="#8b949e")
        self.log_text.tag_configure("WARNING", foreground="#ffd93d")
        self.log_text.tag_configure("ERROR", foreground="#ff6b6b")
        self.log_text.tag_configure("SUCCESS", foreground="#00ff88")
        self.log_text.tag_configure("timestamp", foreground="#7d8590")
    
    def _load_logs(self):
        """Load logs for the instance"""
        self.status_label.configure(text="Loading logs...")
        
        # Get logs from instance manager if available
        if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
            logs = self.app_ref.instance_manager.get_instance_logs(self.instance_name)
        else:
            # Default sample logs
            logs = [
                "[INFO] Instance initialized successfully",
                "[DEBUG] Memory allocation: 2048MB",
                "[INFO] Network interface configured",
                "[DEBUG] Graphics driver loaded",
                "[WARNING] High CPU usage detected",
                "[INFO] Android system booted",
                "[ERROR] Failed to connect to network proxy",
                "[INFO] All systems operational",
                "[DEBUG] Performance monitoring active",
                "[INFO] Ready for user interaction"
            ]
        
        # Clear existing content
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        
        # Add logs with timestamps and formatting
        for log_entry in logs:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            self._add_log_entry(timestamp, log_entry)
        
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
        self.status_label.configure(text=f"Loaded {len(logs)} log entries")
    
    def _add_log_entry(self, timestamp, log_entry):
        """Add a single log entry with proper formatting"""
        # Determine log level
        level = "INFO"
        if "[DEBUG]" in log_entry:
            level = "DEBUG"
        elif "[WARNING]" in log_entry:
            level = "WARNING"
        elif "[ERROR]" in log_entry:
            level = "ERROR"
        elif "successfully" in log_entry.lower() or "operational" in log_entry.lower():
            level = "SUCCESS"
        
        # Insert timestamp
        self.log_text.insert("end", timestamp, "timestamp")
        self.log_text.insert("end", " ")
        
        # Insert log entry with appropriate tag
        self.log_text.insert("end", log_entry, level)
        self.log_text.insert("end", "\n")
    
    def _refresh_logs(self):
        """Refresh the logs"""
        self._load_logs()
        
        if self.app_ref and hasattr(self.app_ref, 'add_console_message'):
            self.app_ref.add_console_message(f"Refreshed logs for {self.instance_name}")
    
    def _clear_logs(self):
        """Clear the log display"""
        result = messagebox.askyesno("Clear Logs", "Are you sure you want to clear the log display?")
        if result:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")
            self.status_label.configure(text="Log display cleared")
    
    def _save_logs(self):
        """Save logs to file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Save Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
            initialname=f"{self.instance_name}_logs.txt"
        )
        
        if filename:
            try:
                content = self.log_text.get("1.0", "end-1c")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"BENSON v2.0 - Log Export\n")
                    f.write(f"Instance: {self.instance_name}\n")
                    f.write(f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("-" * 50 + "\n\n")
                    f.write(content)
                
                self.status_label.configure(text=f"Logs saved to {filename}")
                
                if self.app_ref and hasattr(self.app_ref, 'add_console_message'):
                    self.app_ref.add_console_message(f"Exported logs for {self.instance_name} to {filename}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save logs: {str(e)}")
                self.status_label.configure(text="Failed to save logs")
    
    def _filter_logs(self, event=None):
        """Filter logs by level"""
        selected_level = self.log_level_var.get()
        
        if selected_level == "All":
            # Show all logs
            self._load_logs()
        else:
            # Filter by level
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            
            # Get all logs and filter
            if self.app_ref and hasattr(self.app_ref, 'instance_manager'):
                all_logs = self.app_ref.instance_manager.get_instance_logs(self.instance_name)
            else:
                all_logs = [
                    "[INFO] Instance initialized successfully",
                    "[DEBUG] Memory allocation: 2048MB",
                    "[INFO] Network interface configured",
                    "[DEBUG] Graphics driver loaded",
                    "[WARNING] High CPU usage detected",
                    "[INFO] Android system booted",
                    "[ERROR] Failed to connect to network proxy",
                    "[INFO] All systems operational"
                ]
            
            filtered_logs = [log for log in all_logs if f"[{selected_level}]" in log]
            
            for log_entry in filtered_logs:
                timestamp = datetime.now().strftime("[%H:%M:%S]")
                self._add_log_entry(timestamp, log_entry)
            
            self.log_text.configure(state="disabled")
            self.log_text.see("end")
            
            self.status_label.configure(text=f"Showing {len(filtered_logs)} {selected_level} entries")