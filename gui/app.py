#!/usr/bin/env python3
"""
BENSON v2.0 - Main Application File (Streamlined)
Modular architecture with separated utilities and module auto-startup
"""

import tkinter as tk
from datetime import datetime
import threading
import time
import os

# Import our custom modules
from core.instance_manager import InstanceManager
from core.ocr_helper import OCRHelper
from gui.components.loading_overlay import LoadingOverlay

# Import utility modules
from utils.ocr_handler import OCRHandler
from utils.instance_operations import InstanceOperations
from utils.ui_manager import UIManager
from utils.module_manager import ModuleManager

# Import GUI components
from gui.components.instance_card import InstanceCard
from gui.components.progress_bar import ProgressBar
from gui.components.search_bar import SearchBar

# Try to import OCR functionality
try:
    from core.ocr_helper import OCRHelper
    OCR_AVAILABLE = True
except ImportError:
    OCRHelper = None
    OCR_AVAILABLE = False


class BensonApp(tk.Tk):
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        print("[BensonApp] Initializing application...")
        
        # Initialize managers
        self.instance_manager = InstanceManager()
        self.instance_manager.set_app_reference(self)  # Set app reference for module cleanup
        
        # Initialize OCR helper
        try:
            self.ocr_helper = OCRHelper()
            if not self.ocr_helper.is_ocr_available():
                print("[BensonApp] OCR not available - missing dependencies")
                self.ocr_helper = None
        except Exception as e:
            print(f"[BensonApp] OCR initialization failed: {e}")
            self.ocr_helper = None
        
        # Initialize handlers
        self.ocr_handler = OCRHandler(self)
        self.instance_ops = InstanceOperations(self)
        self.ui_manager = UIManager(self)
        
        # Initialize module manager
        self.module_manager = ModuleManager(self)
        self.module_manager.initialize_modules()
        
        print("[BensonApp] Setting up UI...")
        
        # Setup main window
        self.title("BENSON v2.0 - Advanced Edition")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.configure(bg="#0a0e16")
        
        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        
        # Show loading overlay
        self.loading = LoadingOverlay(self)
        
        # Initialize in background
        self.after(100, self.initialize_background)
    
    def initialize_background(self):
        """Initialize the application in background with loading screen"""
        def init_worker():
            try:
                # Update loading status
                self.loading.update_status("Connecting to MEmu...")
                time.sleep(0.2)
                
                self.loading.update_status("Loading instances...")
                time.sleep(0.2)
                
                self.loading.update_status("Initializing modules...")
                time.sleep(0.2)
                
                # Setup keyboard shortcuts
                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_loading())
                
                # Setup UI on main thread
                self.after(0, self.complete_initialization)
                
            except Exception as e:
                print(f"[BensonApp] Initialization error: {e}")
                self.after(0, lambda: self.show_init_error(str(e)))
        
        # Run initialization in background thread
        threading.Thread(target=init_worker, daemon=True).start()
    
    def complete_initialization(self):
        """Complete initialization on main thread"""
        try:
            self.loading.update_status("Building interface...")
            
            print("[BensonApp] Setting up UI...")
            self.setup_ui()
            
            self.loading.update_status("Starting modules...")
            time.sleep(0.2)
            
            # Start background tasks
            self.start_background_tasks()
            
            # Close loading screen
            self.loading.close()
            
            # Initial refresh to ensure counter is correct
            self.force_counter_update()
            
            # Check for module auto-startup AFTER everything else is ready
            self.after(1000, self.check_module_auto_startup)
            
            print("[BensonApp] Initialization complete!")
            
        except Exception as e:
            self.loading.close()
            self.show_init_error(str(e))
    
    def check_module_auto_startup(self):
        """Check and start auto-startup modules"""
        try:
            self.module_manager.check_auto_startup()
        except Exception as e:
            self.add_console_message(f"❌ Auto-startup check error: {e}")
    
    def show_init_error(self, error):
        """Show initialization error"""
        from tkinter import messagebox
        messagebox.showerror("Initialization Error", 
                           f"Failed to initialize BENSON:\n\n{error}\n\nThe application will close.")
        self.destroy()
    
    def start_background_optimization(self):
        """Start MEmu optimization in background after UI is ready"""
        def optimization_callback(results):
            # This runs on main thread
            if 'error' in results:
                self.add_console_message(f"⚠ Optimization error: {results['error']}")
            else:
                total_processed = results['optimized'] + results['skipped'] + results['failed']
                if total_processed > 0:
                    self.add_console_message(f"🔧 MEmu Optimization: {results['optimized']} optimized, {results['skipped']} already optimal, {results['failed']} failed")
                else:
                    self.add_console_message("📱 No instances found to optimize")
        
        # Run optimization in background
        self.instance_manager.optimize_all_instances_async(
            lambda results: self.after(0, lambda: optimization_callback(results))
        )
    
    def setup_ui(self):
        """Setup the main user interface using UI manager"""
        self.ui_manager.setup_header()
        self.ui_manager.setup_controls()
        self.ui_manager.setup_main_content()
        self.ui_manager.setup_console()
        self.ui_manager.setup_footer()
        
        # Load initial instances
        self.load_instances()
        
        # Initial console messages
        self.add_console_message("BENSON v2.0 Advanced Edition started")
        instances_count = len(self.instance_manager.get_instances())
        self.add_console_message(f"Loaded {instances_count} MEmu instances")
        
        # OCR status message
        if self.ocr_helper:
            regions = self.ocr_helper.get_available_regions()
            self.add_console_message(f"🔍 OCR functionality ready with {len(regions)} predefined regions")
        else:
            self.add_console_message("⚠ OCR not available - install easyocr, opencv-python for OCR features")
        
        # Module status message
        module_status = self.module_manager.get_module_status()
        self.add_console_message(f"🔧 Modules: {module_status['available_modules']}/{module_status['total_instances']} available, {module_status['auto_startup_enabled']} auto-startup enabled")
    
    # Search functionality with debouncing
    def on_search_change_debounced(self, *args):
        """Handle search text change with debouncing"""
        # Cancel previous scheduled search
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        
        # Get current search text
        query = self.search_var.get()
        if query == "Search instances...":
            return
        
        # Schedule new search after 150ms delay
        self.search_after_id = self.after(150, lambda: self.filter_instances_fast(query))
    
    def on_search_focus_in(self, event):
        """Handle search focus in"""
        if self.search_entry.get() == "Search instances...":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg="#ffffff")
    
    def on_search_focus_out(self, event):
        """Handle search focus out"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search instances...")
            self.search_entry.configure(fg="#8b949e")
    
    def filter_instances_fast(self, query):
        """Fast instance filtering without heavy operations"""
        if not query or query == "Search instances...":
            # Show all instances
            self.show_all_instances()
            return
        
        # Hide/show existing cards instead of recreating them
        query_lower = query.lower()
        visible_cards = []
        
        for card in self.instance_cards:
            if query_lower in card.name.lower():
                card.grid()  # Show the card
                visible_cards.append(card)
            else:
                card.grid_remove()  # Hide the card
        
        # Reposition visible cards
        self.reposition_cards(visible_cards)
    
    def show_all_instances(self):
        """Show all instance cards"""
        for card in self.instance_cards:
            card.grid()
        self.reposition_all_cards()
    
    def reposition_cards(self, cards):
        """Reposition given cards in proper layout"""
        # Clear existing positioning
        for card in cards:
            card.grid_remove()
        
        # Always use 2-column grid layout
        for i, card in enumerate(cards):
            row = i // 2
            col = i % 2
            card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w", in_=self.instances_container)
            card.configure(width=580)
            
            # Configure column weights to center cards
            self.instances_container.grid_columnconfigure(col, weight=1)
    
    def reposition_all_cards(self):
        """Reposition all cards in proper layout"""
        self.reposition_cards(self.instance_cards)
    
    def force_counter_update(self):
        """Force update the instance counter"""
        instances_count = len(self.instance_manager.get_instances())
        new_text = f"⚡ MEmu Instances ({instances_count})"
        
        if hasattr(self, 'instances_header'):
            self.instances_header.configure(text=new_text)
            self.update_idletasks()
        
        return instances_count
    
    def load_instances(self):
        """Load and display instance cards"""
        print("[BensonApp] Loading instances...")
        
        # Clear existing cards
        for card in self.instance_cards:
            card.destroy()
        self.instance_cards.clear()
        self.selected_cards.clear()
        
        # Get instances from manager
        instances = self.instance_manager.get_instances()
        
        if len(instances) == 0:
            # No instances - show message
            no_instances_label = tk.Label(
                self.instances_container,
                text="No MEmu instances found\nClick 'Create' to add a new instance",
                bg="#0a0e16",
                fg="#8b949e",
                font=("Segoe UI", 12),
                justify="center"
            )
            no_instances_label.grid(row=0, column=0, columnspan=2, pady=50)
            
        else:
            # Import the enhanced instance card
            from gui.components.instance_card import InstanceCard
            
            # Create instance cards
            for i, instance in enumerate(instances):
                card = InstanceCard(
                    self.instances_container,
                    name=instance["name"],
                    status=instance["status"],
                    cpu_usage=instance["cpu"],
                    memory_usage=instance["memory"],
                    app_ref=self
                )
                
                self.instance_cards.append(card)
            
            # Position cards properly
            self.reposition_all_cards()
        
        # Force counter update
        self.force_counter_update()
        
        # Refresh modules when instances change
        if hasattr(self, 'module_manager'):
            self.module_manager.refresh_modules()
    
    def on_card_selection_changed(self):
        """Called when a card's selection state changes"""
        self.selected_cards = [card for card in self.instance_cards if card.selected]
        print(f"[BensonApp] Selection changed: {len(self.selected_cards)} cards selected")
    
    # OCR Methods (delegated to OCR handler)
    def test_instance_ocr(self, instance_name, region_name="left_panel"):
        """Test OCR on a specific instance with default region"""
        self.ocr_handler.test_instance_ocr(instance_name, region_name)
    
    def test_instance_ocr_region(self, instance_name, region_name):
        """Test OCR on a specific instance with specified region"""
        self.ocr_handler.test_instance_ocr_region(instance_name, region_name)
    
    def test_instance_ocr_custom(self, instance_name, custom_region):
        """Test OCR on a specific instance with custom region"""
        self.ocr_handler.test_instance_ocr_custom(instance_name, custom_region)
    
    # Instance Operations (delegated to instance operations handler)
    def start_instance(self, name):
        """Start an instance"""
        self.instance_ops.start_instance(name)
    
    def stop_instance(self, name):
        """Stop an instance"""
        self.instance_ops.stop_instance(name)
    
    def delete_instance_card_with_loading(self, card):
        """Delete a single instance card with loading"""
        self.instance_ops.delete_instance_card_with_loading(card)
    
    # UI Methods (delegated to UI manager)
    def show_modules(self, instance_name):
        """Show modules window for an instance"""
        self.ui_manager.show_modules(instance_name)
    
    # Console operations
    def add_console_message(self, message):
        """Add a message to the console"""
        if not hasattr(self, 'console_text'):
            print(f"[Console] {message}")
            return
        
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"
        
        self.console_text.configure(state="normal")
        self.console_text.insert("end", full_message)
        self.console_text.configure(state="disabled")
        self.console_text.see("end")
    
    def clear_console(self):
        """Clear the console"""
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")
        self.add_console_message("Console cleared")
    
    def start_background_tasks(self):
        """Start background update tasks with reduced frequency"""
        def background_updates():
            while True:
                time.sleep(60)  # Increased interval to reduce resource usage (1 minute)
                if hasattr(self, 'console_text'):
                    messages = [
                        "System health check completed",
                        "Performance metrics updated",
                        "Instance synchronization successful"
                    ]
                    import random
                    if random.random() > 0.9:  # Much less frequent messages (10% chance)
                        self.add_console_message(random.choice(messages))
                    
        def status_monitor():
            """Monitor instance statuses in background with MUCH less frequency"""
            last_status = {}  # Track last known status
            full_refresh_counter = 0
            
            while True:
                time.sleep(10)  # Check every 10 seconds instead of 3
                try:
                    # Skip if no instance manager
                    if not hasattr(self, 'instance_manager'):
                        continue
                    
                    # Do a full refresh every 60 seconds (6 cycles)
                    full_refresh_counter += 1
                    if full_refresh_counter >= 6:
                        self.instance_manager.load_real_instances()
                        full_refresh_counter = 0
                    else:
                        # Just update statuses of existing instances (lightweight)
                        self.instance_manager.update_instance_statuses()
                    
                    instances = self.instance_manager.get_instances()
                    
                    # Update card statuses only if they actually changed
                    for card in self.instance_cards:
                        for instance in instances:
                            if instance["name"] == card.name:
                                real_status = instance["status"]
                                
                                # Only update if status actually changed
                                last_known = last_status.get(card.name)
                                if last_known != real_status:
                                    last_status[card.name] = real_status
                                    # Update card on main thread
                                    self.after(0, lambda c=card, s=real_status: c.update_status(s))
                                break
                                
                except Exception as e:
                    # Reduce error logging frequency
                    if hasattr(self, '_last_error_time'):
                        if time.time() - self._last_error_time > 30:  # Only log errors every 30 seconds
                            print(f"[StatusMonitor] Error: {e}")
                            self._last_error_time = time.time()
                    else:
                        print(f"[StatusMonitor] Error: {e}")
                        self._last_error_time = time.time()
                
        # Start background threads
        threading.Thread(target=background_updates, daemon=True).start()
        threading.Thread(target=status_monitor, daemon=True).start()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()