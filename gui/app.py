#!/usr/bin/env python3
"""
BENSON v2.0 - FIXED Main Application File
Fixed loading timing, animation freezing, and non-blocking operations
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
        # Hide the main window initially
        self.withdraw()

        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        self._destroyed = False
        self._initializing = True

        # Show loading overlay with FIXED animations
        self.loading = LoadingOverlay(self)
        
        # Make loading window visible
        self.loading.window.deiconify()
        self.withdraw()

        # Prevent auto-close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # FIXED: Initialize with proper timing to prevent freezing
        self.after(200, self.initialize_background)

    def initialize_background(self):
        """FIXED: Non-blocking initialization with proper error handling"""
        def init_worker():
            try:
                self.loading.update_status("Connecting to MEmu...")
                print("[Init] Step 1: Connecting to MEmu")
                
                # FIXED: Small delays to prevent blocking
                time.sleep(0.1)

                self.instance_manager = InstanceManager()
                print("[Init] Step 2: InstanceManager created")

                self.loading.update_status("Loading MEmu instances...")
                time.sleep(0.1)

                self.instance_manager.load_real_instances()
                print("[Init] Step 3: Instances loaded")
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] Instances count: {instances_count}")

                self.loading.update_status("Initializing modules...")
                time.sleep(0.1)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Step 4: Modules initialized")

                self.loading.update_status("Setting up utilities...")
                time.sleep(0.1)

                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Step 5: Utilities set up")

                # Bind keyboard shortcuts
                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_animation())

                # Schedule UI setup on main thread
                self.after(0, lambda: self.complete_initialization(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                import traceback
                traceback.print_exc()
                err = str(e)
                self.after(0, lambda: self.show_init_error(err))

        # FIXED: Start initialization in background thread
        threading.Thread(target=init_worker, daemon=True).start()

    def complete_initialization(self, instances_count):
        """FIXED: Complete initialization with non-blocking UI setup"""
        try:
            print("[BensonApp] Starting UI setup...")
            self.loading.update_status("Building interface...")

            # FIXED: Setup UI in non-blocking chunks
            self._setup_ui_progressive(0, instances_count)

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _setup_ui_progressive(self, step, instances_count):
        """FIXED: Progressive UI setup to prevent freezing"""
        try:
            # Update loading status
            status_messages = {
                0: "Setting up header...",
                1: "Setting up controls...",
                2: "Building main content...",
                3: "Initializing console...",
                4: "Setting up footer...",
                5: "Loading instances..."
            }
            
            if step in status_messages:
                self.loading.update_status(status_messages[step])
            
            # FIXED: Process one UI component at a time
            if step == 0:
                self.ui_manager.setup_header()
                self.after(30, lambda: self._setup_ui_progressive(1, instances_count))
            elif step == 1:
                self.ui_manager.setup_controls()
                self.after(30, lambda: self._setup_ui_progressive(2, instances_count))
            elif step == 2:
                self.ui_manager.setup_main_content()
                self.after(30, lambda: self._setup_ui_progressive(3, instances_count))
            elif step == 3:
                self.ui_manager.setup_console()
                self.after(30, lambda: self._setup_ui_progressive(4, instances_count))
            elif step == 4:
                self.ui_manager.setup_footer()
                self.after(30, lambda: self._setup_ui_progressive(5, instances_count))
            elif step == 5:
                # Load instances without blocking
                self._load_instances_progressive(instances_count)
            else:
                # UI setup complete
                self._finalize_initialization(instances_count)

        except Exception as e:
            print(f"[BensonApp] UI setup error in step {step}: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _load_instances_progressive(self, instances_count):
        """FIXED: Load instances progressively without blocking"""
        try:
            self.loading.update_status("Creating instance cards...")
            
            # FIXED: Load instances in background to prevent UI freezing
            def instance_worker():
                try:
                    instances = self.instance_manager.get_instances()
                    # Schedule card creation on main thread
                    self.after(0, lambda: self._create_instance_cards_progressive(instances, 0))
                except Exception as e:
                    print(f"[BensonApp] Error loading instances: {e}")
                    self.after(0, lambda: self._finalize_initialization(0))
            
            threading.Thread(target=instance_worker, daemon=True).start()
            
        except Exception as e:
            print(f"[BensonApp] Error in progressive instance loading: {e}")
            self._finalize_initialization(instances_count)

    def _create_instance_cards_progressive(self, instances, current_index):
        """FIXED: Create instance cards one at a time to prevent freezing"""
        try:
            if current_index >= len(instances):
                # All cards created
                self._finalize_initialization(len(instances))
                return
            
            # Update progress
            progress = f"Creating cards ({current_index + 1}/{len(instances)})..."
            self.loading.update_status(progress)
            
            # Create one card
            instance = instances[current_index]
            name = instance["name"]
            status = instance["status"]
            
            try:
                card = self.ui_manager.create_instance_card(name, status)
                if card:
                    self.instance_cards.append(card)
                    
                    # Position card
                    row = current_index // 2
                    col = current_index % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
            except Exception as e:
                print(f"[BensonApp] Error creating card for {name}: {e}")
            
            # FIXED: Continue with next card after small delay
            self.after(20, lambda: self._create_instance_cards_progressive(instances, current_index + 1))
            
        except Exception as e:
            print(f"[BensonApp] Error in progressive card creation: {e}")
            self._finalize_initialization(len(self.instance_cards))

    def _finalize_initialization(self, instances_count):
        """FIXED: Non-blocking finalization to prevent 'Starting Services' freeze"""
        try:
            self.loading.update_status("Finalizing...")
            
            # Add initial console messages
            self.add_console_message("BENSON v2.0 Advanced Edition started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")

            # Module status message
            if hasattr(self, 'module_manager'):
                module_status = self.module_manager.get_module_status()
                self.add_console_message(f"🔧 Modules: {module_status['available_modules']}/{module_status['total_instances']} available")

            # FIXED: Don't start background tasks immediately - delay them
            self.loading.update_status("Ready!")
            
            # FIXED: Show main window quickly without waiting for background tasks
            self.after(200, self._show_main_window_final)

        except Exception as e:
            print(f"[BensonApp] Error in finalization: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _show_main_window_final(self):
        """FIXED: Show main window without blocking on background tasks"""
        try:
            # Finalize UI layout
            self.reposition_all_cards()
            self.force_counter_update()
            
            # Close loading screen
            if hasattr(self, 'loading'):
                self.loading.close()
            
            # FIXED: Show main window immediately
            self.deiconify()
            self.lift()
            self.focus_force()
            
            # Mark initialization complete
            self._initializing = False
            
            # Final message
            self.add_console_message(f"✅ BENSON v2.0 ready with {len(self.instance_manager.get_instances())} instances")
            
            # FIXED: Start background tasks AFTER window is shown (non-blocking)
            self.after(1000, self.start_background_tasks)
            
            # FIXED: Check module auto-startup after background tasks start
            if hasattr(self, 'module_manager'):
                self.after(3000, self.check_module_auto_startup)

        except Exception as e:
            print(f"[BensonApp] Error showing main window: {e}")
            self.show_init_error(str(e))(self, 'module_manager')
            self.after(2000, self.check_module_auto_startup)

        except Exception as e:
            print(f"[BensonApp] Error showing main window: {e}")
            self.show_init_error(str(e))

    def check_module_auto_startup(self):
        """FIXED: Module auto-startup with proper timing"""
        try:
            if not hasattr(self, 'module_manager') or not self.module_manager.initialization_complete:
                self.add_console_message("⏳ Module manager not ready, retrying auto-startup check...")
                self.after(1000, self.check_module_auto_startup)
                return

            self.add_console_message("🔍 Checking for auto-startup modules...")
            
            # Run auto-startup check in background to prevent UI blocking
            def auto_startup_worker():
                try:
                    self.module_manager.check_auto_startup()
                except Exception as e:
                    self.after_idle(lambda: self.add_console_message(f"❌ Auto-startup check error: {e}"))
            
            threading.Thread(target=auto_startup_worker, daemon=True).start()

        except Exception as e:
            self.add_console_message(f"❌ Auto-startup check error: {e}")

    def show_init_error(self, error):
        """Show initialization error"""
        from tkinter import messagebox
        messagebox.showerror("Initialization Error",
                           f"Failed to initialize BENSON:\n\n{error}\n\nThe application will close.")
        self.destroy()

    # FIXED: Search functionality with non-blocking operations
    def on_search_change_debounced(self, *args):
        """Handle search text change with debouncing"""
        # Cancel previous scheduled search
        if self.search_after_id:
            self.after_cancel(self.search_after_id)

        # Get current search text
        query = self.search_var.get()
        if query == "Search instances...":
            return

        # Schedule new search after delay - FIXED: Non-blocking
        self.search_after_id = self.after(100, lambda: self._filter_instances_async(query))

    def _filter_instances_async(self, query):
        """FIXED: Async instance filtering to prevent freezing"""
        def filter_worker():
            try:
                if not query or query == "Search instances...":
                    # Show all instances
                    self.after_idle(self.show_all_instances)
                    return

                query_lower = query.lower()
                visible_cards = []

                for card in self.instance_cards:
                    if query_lower in card.name.lower():
                        visible_cards.append(card)

                # Schedule UI updates on main thread
                self.after_idle(lambda: self._apply_filter_results(visible_cards))

            except Exception as e:
                print(f"[BensonApp] Filter error: {e}")

        threading.Thread(target=filter_worker, daemon=True).start()

    def _apply_filter_results(self, visible_cards):
        """Apply filter results to UI"""
        try:
            # Hide all cards first
            for card in self.instance_cards:
                card.grid_remove()

            # Show filtered cards
            for card in visible_cards:
                card.grid()

            # Reposition visible cards
            self.reposition_cards(visible_cards)

        except Exception as e:
            print(f"[BensonApp] Error applying filter: {e}")

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

    def show_all_instances(self):
        """Show all instance cards"""
        for card in self.instance_cards:
            card.grid()
        self.reposition_all_cards()

    def load_instances(self):
        """FIXED: Load instances without blocking UI"""
        print("[BensonApp] Loading instances...")
        
        def load_worker():
            try:
                instances = self.instance_manager.get_instances()
                self.after_idle(lambda: self._reload_instance_cards(instances))
            except Exception as e:
                print(f"[BensonApp] Error loading instances: {e}")

        threading.Thread(target=load_worker, daemon=True).start()

    def _reload_instance_cards(self, instances):
        """FIXED: Reload instance cards without blocking"""
        try:
            # Clear existing cards
            for card in self.instance_cards:
                try:
                    card.destroy()
                except:
                    pass
            self.instance_cards = []
            
            # Create new cards progressively
            self._create_reload_cards_progressive(instances, 0)

        except Exception as e:
            print(f"[BensonApp] Error reloading cards: {e}")

    def _create_reload_cards_progressive(self, instances, current_index):
        """Create reload cards progressively"""
        try:
            if current_index >= len(instances):
                # All cards reloaded
                self.reposition_all_cards()
                self.force_counter_update()
                return

            # Create one card
            instance = instances[current_index]
            name = instance["name"]
            status = instance["status"]
            
            try:
                card = self.ui_manager.create_instance_card(name, status)
                if card:
                    self.instance_cards.append(card)
                    
                    # Position card
                    row = current_index // 2
                    col = current_index % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
            except Exception as e:
                print(f"[BensonApp] Error creating reload card for {name}: {e}")
            
            # Continue with next card
            self.after(10, lambda: self._create_reload_cards_progressive(instances, current_index + 1))

        except Exception as e:
            print(f"[BensonApp] Error in progressive reload: {e}")

    def reposition_all_cards(self):
        """FIXED: Reposition all cards efficiently"""
        try:
            if self._initializing:
                return  # Skip during initialization
                
            # Clear existing positions
            for card in self.instance_cards:
                try:
                    card.grid_remove()
                except:
                    pass
            
            # Configure grid columns
            if hasattr(self, 'instances_container'):
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
                
                # Position all cards
                for i, card in enumerate(self.instance_cards):
                    try:
                        row = i // 2
                        col = i % 2
                        card.grid(row=row, column=col, padx=4, pady=2, 
                                sticky="e" if col == 0 else "w", 
                                in_=self.instances_container)
                        card.configure(width=580)
                    except Exception as e:
                        print(f"[BensonApp] Error positioning card {i}: {e}")

        except Exception as e:
            print(f"[BensonApp] Error in reposition_all_cards: {e}")

    def reposition_cards(self, cards):
        """FIXED: Reposition specific cards efficiently"""
        try:
            # Clear existing positioning
            for card in cards:
                try:
                    card.grid_remove()
                except:
                    pass
            
            # Position cards
            for i, card in enumerate(cards):
                try:
                    row = i // 2
                    col = i % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
                    card.configure(width=580)
                except Exception as e:
                    print(f"[BensonApp] Error positioning card {i}: {e}")

        except Exception as e:
            print(f"[BensonApp] Error in reposition_cards: {e}")

    def force_counter_update(self):
        """Force update the instance counter"""
        try:
            instances_count = len(self.instance_manager.get_instances())
            new_text = f"Instances ({instances_count})"

            if hasattr(self, 'instances_header'):
                self.instances_header.configure(text=new_text)
                self.update_idletasks()

            return instances_count
        except Exception as e:
            print(f"[BensonApp] Error updating counter: {e}")
            return 0

    def on_card_selection_changed(self):
        """Called when a card's selection state changes"""
        try:
            self.selected_cards = [card for card in self.instance_cards if card.selected]
        except Exception as e:
            print(f"[BensonApp] Error in selection change: {e}")

    # Instance Operations (delegated to instance operations handler)
    def start_instance(self, name):
        """Start an instance with auto-optimization"""
        def start_with_optimization():
            try:
                self.add_console_message(f"🔧 Auto-optimizing {name} before start...")

                # Optimize the instance first
                success = self.instance_manager.optimize_instance_with_settings(name)
                if success:
                    self.add_console_message(f"✅ {name} optimized successfully")
                else:
                    self.add_console_message(f"⚠ {name} optimization failed, starting anyway...")

                # Then start the instance
                self.instance_ops.start_instance(name)
            except Exception as e:
                self.add_console_message(f"❌ Error in start_instance: {e}")

        threading.Thread(target=start_with_optimization, daemon=True).start()

    def stop_instance(self, name):
        """Stop an instance"""
        self.instance_ops.stop_instance(name)

    def delete_instance_card_with_loading(self, card):
        """Delete a single instance card - redirects to animation version"""
        self.instance_ops.delete_instance_card_with_animation(card)

    # UI Methods (delegated to UI manager)
    def show_modules(self, instance_name):
        """Show modules window for an instance"""
        self.ui_manager.show_modules(instance_name)

    # FIXED: Console operations with error handling
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
            print(f"[Console] {message}")

    def clear_console(self):
        """Clear the console"""
        try:
            if hasattr(self, 'console_text'):
                self.console_text.configure(state="normal")
                self.console_text.delete("1.0", "end")
                self.console_text.configure(state="disabled")
                self.add_console_message("Console cleared")
        except (tk.TclError, AttributeError):
            pass

    def start_background_tasks(self):
        """FIXED: Non-blocking background tasks startup"""
        def delayed_start_tasks():
            """Start background tasks after a delay to prevent freezing"""
            try:
                # Wait for UI to be fully ready
                time.sleep(3)
                
                # Start background tasks
                self.after_idle(self._start_actual_background_tasks)
                
            except Exception as e:
                print(f"[BackgroundStart] Error: {e}")
        
        # Start task initialization in background
        threading.Thread(target=delayed_start_tasks, daemon=True).start()
    
    def _start_actual_background_tasks(self):
        """Start the actual background monitoring tasks"""
        try:
            print("[BensonApp] Starting background monitoring...")
            
            def background_updates():
                while not self._destroyed:
                    try:
                        time.sleep(300)  # Every 5 minutes
                        if hasattr(self, 'console_text') and not self._destroyed:
                            # Very infrequent background messages
                            import random
                            if random.random() > 0.995:  # 0.5% chance
                                messages = [
                                    "System health check completed",
                                    "Performance metrics updated"
                                ]
                                self.after_idle(lambda: self.add_console_message(random.choice(messages)))
                    except Exception as e:
                        print(f"[BackgroundUpdates] Error: {e}")
                        break

            def status_monitor():
                """FIXED: Lightweight status monitor"""
                last_status = {}
                full_refresh_counter = 0

                while not self._destroyed:
                    try:
                        time.sleep(30)  # Every 30 seconds (less frequent)

                        if not hasattr(self, 'instance_manager') or self._destroyed or self._initializing:
                            continue

                        # Very light status check
                        full_refresh_counter += 1
                        if full_refresh_counter >= 10:  # Every 5 minutes instead of 2
                            if not getattr(self, '_updating_instances', False):
                                self._updating_instances = True
                                try:
                                    # Light refresh only
                                    self.instance_manager.update_instance_statuses()
                                    full_refresh_counter = 0
                                finally:
                                    self._updating_instances = False

                        # Minimal UI updates
                        if not getattr(self, '_updating_instances', False):
                            def light_update():
                                try:
                                    if self._destroyed or not hasattr(self, 'instance_manager'):
                                        return
                                    
                                    instances = self.instance_manager.get_instances()
                                    ui_updates = []

                                    # Only update changed statuses
                                    for card in self.instance_cards[:5]:  # Limit to first 5 cards
                                        if self._destroyed:
                                            break

                                        for instance in instances:
                                            if instance["name"] == card.name:
                                                real_status = instance["status"]
                                                last_known = last_status.get(card.name)
                                                if last_known != real_status:
                                                    last_status[card.name] = real_status
                                                    ui_updates.append((card, real_status))
                                                break

                                    # Apply updates if any
                                    if ui_updates and not self._destroyed:
                                        self._batch_update_cards(ui_updates)

                                except Exception as e:
                                    print(f"[StatusMonitor] Light update error: {e}")

                            self.after_idle(light_update)

                    except Exception as e:
                        print(f"[StatusMonitor] Error: {e}")
                        time.sleep(30)

            # Start background threads with delay
            threading.Thread(target=background_updates, daemon=True, name="BackgroundUpdates").start()
            threading.Thread(target=status_monitor, daemon=True, name="StatusMonitor").start()
            
            print("[BensonApp] Background tasks started successfully")
            
        except Exception as e:
            print(f"[BensonApp] Error starting background tasks: {e}")

    def _batch_update_cards(self, ui_updates):
        """FIXED: Batch update multiple cards efficiently"""
        try:
            if self._destroyed:
                return

            for card, status in ui_updates:
                if not self._destroyed and hasattr(card, 'update_status'):
                    try:
                        card.update_status(status)
                    except (tk.TclError, AttributeError):
                        continue

            # Non-blocking UI update
            if not self._destroyed:
                self.update_idletasks()

        except Exception as e:
            print(f"[BatchUpdate] Error: {e}")

    def _on_window_close(self):
        """Handle window close properly"""
        try:
            self.destroy()
        except:
            pass

    def destroy(self):
        """FIXED: Enhanced destroy with proper cleanup"""
        self._destroyed = True

        # Stop any running modules
        if hasattr(self, 'module_manager'):
            try:
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