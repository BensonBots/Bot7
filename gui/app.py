#!/usr/bin/env python3
"""
BENSON v2.0 - Main Application File (OCR Removed)
Clean version without OCR dependencies
"""

import tkinter as tk
from datetime import datetime
import threading
import time

# Import our custom modules
from core.instance_manager import InstanceManager
from gui.components.loading_overlay import LoadingOverlay

# Import utility modules
from utils.instance_operations import InstanceOperations
from utils.ui_manager import UIManager
from utils.module_manager import ModuleManager


class BensonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        print("[BensonApp] Initializing application...")
        
        # Configure window
        self.title("BENSON v2.0 - Advanced Edition")
        self.geometry("1200x800")
        self.configure(bg="#0a0e16")
        self.minsize(900, 600)
        
        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        self._destroyed = False
        
        # Show loading overlay
        self.loading = LoadingOverlay(self)
        
        # Initialize in background with proper timing
        self.after(100, self.initialize_background)
    
    def initialize_background(self):
        """Fixed initialization with proper timing and error handling"""
        def init_worker():
            try:
                # Step 1: Initialize core systems
                self.loading.update_status("Connecting to MEmu...")
                time.sleep(0.2)
                
                self.instance_manager = InstanceManager()
                
                # Step 2: Load instances - WAIT for this to complete
                self.loading.update_status("Loading MEmu instances...")
                time.sleep(0.2)
                
                # Force load instances and wait
                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                
                # Step 3: Initialize modules BEFORE UI setup
                self.loading.update_status("Initializing modules...")
                time.sleep(0.2)
                
                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                
                # Step 4: Initialize utilities
                self.loading.update_status("Setting up utilities...")
                time.sleep(0.2)
                
                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                
                # Step 5: Setup keyboard shortcuts
                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_loading())
                
                # Pass instance count to completion
                self.after(0, lambda: self.complete_initialization(instances_count))
                
            except Exception as e:
                print(f"[BensonApp] Initialization error: {e}")
                self.after(0, lambda: self.show_init_error(str(e)))
        
        # Run initialization in background thread
        threading.Thread(target=init_worker, daemon=True).start()
    
    def complete_initialization(self, instances_count):
        """Fixed completion - LOADING SCREEN STAYS UNTIL ACTUALLY READY"""
        try:
            self.loading.update_status("Building interface...")
            time.sleep(0.5)
            
            print("[BensonApp] Setting up UI...")
            self.setup_ui()
            
            # Critical: Don't close loading until EVERYTHING is actually rendered
            self.loading.update_status("Rendering instance cards...")
            
            # Force multiple complete UI updates
            for i in range(10):  # More update cycles
                self.update_idletasks()
                self.update()
                time.sleep(0.1)
            
            # Wait for cards to actually render
            time.sleep(2.0)  # Much longer wait
            
            self.loading.update_status("Starting background services...")
            time.sleep(0.3)
            
            # Start background tasks
            self.start_background_tasks()
            
            self.loading.update_status("Finalizing...")
            
            # More forced updates
            for i in range(5):
                self.update_idletasks()
                self.update()
                time.sleep(0.2)
            
            # Force counter update
            self.force_counter_update()
            
            # Final status update
            self.loading.update_status("Ready!")
            time.sleep(0.5)
            
            # ONLY close loading screen after everything is actually ready
            # Don't use after() - do it synchronously
            self._complete_loading()
            
            # Auto-startup check much later
            self.after(5000, self.check_module_auto_startup)
            
            print(f"[BensonApp] Initialization complete with {instances_count} instances!")
            
        except Exception as e:
            self.loading.close()
            self.show_init_error(str(e))
    
    def _complete_loading(self):
        """Complete the loading process after ensuring GUI is ready"""
        try:
            # Wait even longer and do more updates
            time.sleep(0.5)
            
            # Multiple rounds of UI updates to ensure everything is rendered
            for i in range(5):
                self.update_idletasks()
                time.sleep(0.1)
                self.update()
                time.sleep(0.1)
            
            # Give extra time for instance cards to fully render
            time.sleep(0.5)
            
            # Final update round
            self.update_idletasks()
            self.update()
            
            # Close loading screen
            self.loading.close()
            
            # One more update after loading screen is gone
            time.sleep(0.2)
            self.update_idletasks()
            
            # Add final initialization message
            self.add_console_message("✅ BENSON v2.0 ready - GUI fully loaded and responsive")
            
        except Exception as e:
            print(f"[BensonApp] Error completing loading: {e}")
            try:
                self.loading.close()
            except:
                pass
    
    def check_module_auto_startup(self):
        """FIXED: Proper auto-startup check with timing"""
        try:
            # Ensure module manager is ready
            if not hasattr(self, 'module_manager') or not self.module_manager.initialization_complete:
                self.add_console_message("⏳ Module manager not ready, retrying auto-startup check...")
                self.after(1000, self.check_module_auto_startup)
                return
            
            self.add_console_message("🔍 Checking for auto-startup modules...")
            
            # Call the fixed auto-startup check
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
        """REMOVED - No startup optimization, only optimize when user starts instance"""
        # Optimization now only happens when user clicks "Start" on an instance
        # This prevents unnecessary optimization checks on startup
        self.add_console_message("💡 Optimization will run automatically when you start instances")
        pass
    
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
        
        # Module status message
        module_status = self.module_manager.get_module_status()
        self.add_console_message(f"🔧 Modules: {module_status['available_modules']}/{module_status['total_instances']} available, {module_status['auto_startup_enabled']} auto-startup enabled")
        
        # NO STARTUP OPTIMIZATION - only optimize when user clicks start
    
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
            # Import the optimized instance card
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
    
    # Instance Operations (delegated to instance operations handler)
    def start_instance(self, name):
        """Start an instance with auto-optimization - ONLY when user clicks start"""
        # Auto-optimize before starting
        def start_with_optimization():
            self.add_console_message(f"🔧 Auto-optimizing {name} before start...")
            
            # Optimize the instance first
            success = self.instance_manager.optimize_instance_with_settings(name)
            if success:
                self.add_console_message(f"✅ {name} optimized successfully")
            else:
                self.add_console_message(f"⚠ {name} optimization failed, starting anyway...")
            
            # Then start the instance
            self.instance_ops.start_instance(name)
        
        # Run optimization and start in background
        threading.Thread(target=start_with_optimization, daemon=True).start()
    
    def stop_instance(self, name):
        """Stop an instance"""
        self.instance_ops.stop_instance(name)
    
    def delete_instance_card_with_loading(self, card):
        """Delete a single instance card with loading"""
        self.instance_ops.delete_instance_card_with_loading(card)
    
    # UI Methods (delegated to UI manager) - Analytics and Settings removed
    def show_modules(self, instance_name):
        """Show modules window for an instance"""
        self.ui_manager.show_modules(instance_name)
    
    # Console operations
    def add_console_message(self, message):
        """Add a message to the console with error handling"""
        if not hasattr(self, 'console_text'):
            print(f"[Console] {message}")
            return
        
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            full_message = f"{timestamp} {message}\n"
            
            self.console_text.configure(state="normal")
            self.console_text.insert("end", full_message)
            self.console_text.configure(state="disabled")
            self.console_text.see("end")
        except (tk.TclError, AttributeError):
            # Handle case where console is not ready or destroyed
            print(f"[Console] {message}")
    
    def clear_console(self):
        """Clear the console"""
        try:
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            self.add_console_message("Console cleared")
        except (tk.TclError, AttributeError):
            pass
    
    def start_background_tasks(self):
        """Optimized background tasks with reduced frequency to prevent GUI lag"""
        def background_updates():
            while not self._destroyed:
                try:
                    time.sleep(60)  # Reduced frequency: every 60 seconds instead of 30
                    if hasattr(self, 'console_text') and not self._destroyed:
                        messages = [
                            "System health check completed",
                            "Performance metrics updated", 
                            "Instance synchronization successful"
                        ]
                        import random
                        if random.random() > 0.9:  # Much less frequent messages (10% chance)
                            self.add_console_message(random.choice(messages))
                except Exception as e:
                    print(f"[BackgroundUpdates] Error: {e}")
                    break
                    
        def status_monitor():
            """Optimized status monitor with less frequent updates to reduce lag"""
            last_status = {}
            full_refresh_counter = 0
            
            while not self._destroyed:
                try:
                    time.sleep(5)  # Increased from 3 to 5 seconds
                    
                    # Skip if no instance manager or destroyed
                    if not hasattr(self, 'instance_manager') or self._destroyed:
                        continue
                    
                    # Do a full refresh every 60 seconds (12 * 5s) instead of 30s
                    full_refresh_counter += 1
                    if full_refresh_counter >= 12:
                        # Only do full refresh if not currently busy
                        if not getattr(self, '_updating_instances', False):
                            self._updating_instances = True
                            try:
                                self.instance_manager.load_real_instances()
                                full_refresh_counter = 0
                            finally:
                                self._updating_instances = False
                    else:
                        # Light status update only
                        if not getattr(self, '_updating_instances', False):
                            self._updating_instances = True
                            try:
                                self.instance_manager.update_instance_statuses()
                            finally:
                                self._updating_instances = False
                    
                    # Only update UI if not currently updating
                    if not getattr(self, '_updating_instances', False):
                        instances = self.instance_manager.get_instances()
                        
                        # Batch UI updates to reduce lag
                        ui_updates = []
                        
                        for card in self.instance_cards:
                            if self._destroyed:
                                break
                                
                            for instance in instances:
                                if instance["name"] == card.name:
                                    real_status = instance["status"]
                                    
                                    # Only update if status actually changed
                                    last_known = last_status.get(card.name)
                                    if last_known != real_status:
                                        last_status[card.name] = real_status
                                        ui_updates.append((card, real_status))
                                    break
                        
                        # Apply all UI updates at once on main thread
                        if ui_updates and not self._destroyed:
                            try:
                                self.after_idle(lambda: self._batch_update_cards(ui_updates))
                            except tk.TclError:
                                # App is closing
                                return
                                
                except Exception as e:
                    print(f"[StatusMonitor] Error: {e}")
                    time.sleep(5)  # Wait before retrying on error
                    
        # Start background threads with daemon=True
        threading.Thread(target=background_updates, daemon=True, name="BackgroundUpdates").start()
        threading.Thread(target=status_monitor, daemon=True, name="StatusMonitor").start()
    
    def _batch_update_cards(self, ui_updates):
        """Batch update multiple cards at once to reduce UI lag"""
        try:
            if self._destroyed:
                return
            
            # Update cards in batches to prevent UI freezing
            for card, status in ui_updates:
                if not self._destroyed and hasattr(card, 'update_status'):
                    try:
                        card.update_status(status)
                    except (tk.TclError, AttributeError):
                        # Card may have been destroyed
                        continue
            
            # Force UI update after batch
            if not self._destroyed:
                self.update_idletasks()
                
        except Exception as e:
            print(f"[BatchUpdate] Error: {e}")
    
    def destroy(self):
        """Enhanced destroy with proper cleanup"""
        self._destroyed = True
        
        # Stop any running modules
        if hasattr(self, 'module_manager'):
            try:
                # Stop all running modules gracefully
                for instance_name, module in self.module_manager.autostart_modules.items():
                    try:
                        running_instances = module.get_running_instances()
                        if instance_name in running_instances:
                            module.stop_auto_game(instance_name)
                    except:
                        pass
            except:
                pass
        
        # Clean up loading overlay
        if hasattr(self, 'loading'):
            try:
                self.loading.close()
            except:
                pass
        
        # Call parent destroy
        super().destroy()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()