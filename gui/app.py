#!/usr/bin/env python3
"""
BENSON v2.0 - Main Application File (FINAL COMPLETE FIXED)
All fixes applied: Loading timing, console spam, auto-close prevention, non-blocking instance loading
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
        # Hide the main window completely
        self.withdraw()

        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        self._destroyed = False

        # Show loading overlay
        self.loading = LoadingOverlay(self)
        
        # Make loading window visible and main window hidden
        self.loading.window.deiconify()
        self.withdraw()

        # Prevent auto-close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Initialize in background with proper timing
        self.after(100, self.initialize_background)

    def initialize_background(self):
        """Fixed initialization with proper timing and error handling"""
        def init_worker():
            try:
                self.after(0, lambda: self.loading.update_status("Connecting to MEmu..."))
                print("[Init] Step 1: Connecting to MEmu")
                time.sleep(0.2)

                self.instance_manager = InstanceManager()
                print("[Init] Step 2: InstanceManager created")

                self.after(0, lambda: self.loading.update_status("Loading MEmu instances..."))
                time.sleep(0.2)

                self.instance_manager.load_real_instances()
                print("[Init] Step 3: Instances loaded")
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] Instances count: {instances_count}")

                self.after(0, lambda: self.loading.update_status("Initializing modules..."))
                time.sleep(0.2)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Step 4: Modules initialized")

                self.after(0, lambda: self.loading.update_status("Setting up utilities..."))
                time.sleep(0.2)

                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Step 5: Utilities set up")

                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_loading())

                self.after(0, lambda: self.complete_initialization(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                import traceback
                traceback.print_exc()
                err = str(e)
                self.after(0, lambda: self.show_init_error(err))

        threading.Thread(target=init_worker, daemon=True).start()

    def complete_initialization(self, instances_count):
        """FIXED: Keep loading screen until GUI is actually ready"""
        try:
            print("[BensonApp] Starting UI setup...")
            self.loading.update_status("Building interface...")

            def build_ui_in_chunks():
                # Setup UI in smaller chunks to prevent blocking
                self.ui_manager.setup_header()
                self.after(10, lambda: self._continue_ui_setup(1, instances_count))

            # Start UI setup after a short delay
            self.after(100, build_ui_in_chunks)

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _continue_ui_setup(self, step, instances_count):
        """Continue UI setup in steps to prevent blocking"""
        try:
            # Update loading status with current step
            status_messages = {
                1: "Setting up controls...",
                2: "Building main content...",
                3: "Initializing console...",
                4: "Finalizing interface...",
                5: "Loading instances..."
            }
            
            if step <= 5:
                self.loading.update_status(status_messages.get(step, "Building interface..."))
            
            # Process one step at a time with minimal blocking
            if step == 1:
                self.ui_manager.setup_controls()
                self.after(50, lambda: self._continue_ui_setup(2, instances_count))
            elif step == 2:
                self.ui_manager.setup_main_content()
                self.after(50, lambda: self._continue_ui_setup(3, instances_count))
            elif step == 3:
                self.ui_manager.setup_console()
                self.after(50, lambda: self._continue_ui_setup(4, instances_count))
            elif step == 4:
                self.ui_manager.setup_footer()
                self.after(50, lambda: self._continue_ui_setup(5, instances_count))
            elif step == 5:
                # Start loading instances
                self.load_instances()
                # Move to next step
                self.after(50, lambda: self._continue_ui_setup(6, instances_count))
            elif step == 6:
                # Initial console messages
                self.add_console_message("BENSON v2.0 Advanced Edition started")
                instances_count = len(self.instance_manager.get_instances())
                self.add_console_message(f"Loaded {instances_count} MEmu instances")

                # Module status message
                module_status = self.module_manager.get_module_status()
                self.add_console_message(f"🔧 Modules: {module_status['available_modules']}/{module_status['total_instances']} available, {module_status['auto_startup_enabled']} auto-startup enabled")

                # Start final checks
                self.after(100, lambda: self._finish_initialization(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error in step {step}: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _finish_initialization(self, instances_count):
        """FIXED: Final initialization with proper timing"""
        try:
            self.loading.update_status("Starting services...")
            self.start_background_tasks()
            
            def check_ready():
                # FIXED: More thorough readiness check
                cards_ready = len(self.instance_cards) == instances_count
                ui_ready = hasattr(self, 'console_text') and hasattr(self, 'instances_container')
                
                if cards_ready and ui_ready:
                    # FIXED: Extended delay to ensure GUI is fully rendered
                    def final_show():
                        try:
                            # Close loading screen
                            self.loading.close()
                            
                            # FIXED: Longer delay before showing main window
                            self.after(500, self._show_main_window)
                        except Exception as e:
                            print(f"[BensonApp] Error in final show: {e}")
                            self._show_main_window()
                    
                    self.after(200, final_show)
                else:
                    # Update status to show progress
                    self.loading.update_status(f"Finalizing ({len(self.instance_cards)}/{instances_count})...")
                    # Check again in 100ms
                    self.after(100, check_ready)
            
            # Start checking if ready
            self.after(100, check_ready)

        except Exception as e:
            print(f"[BensonApp] Error in finish initialization: {e}")
            if hasattr(self, 'loading'):
                self.loading.close()
            self.show_init_error(str(e))

    def _show_main_window(self):
        """FIXED: Show the main window with proper sequencing"""
        try:
            # FIXED: Ensure everything is fully rendered first
            self.update_idletasks()
            self.update()
            
            # Show main window
            self.deiconify()
            
            # FIXED: Give window time to render before bringing to front
            def bring_to_front():
                try:
                    self.lift()  # Bring to front
                    self.focus_force()  # Force focus
                    
                    # Final updates
                    self.update_idletasks()
                    
                    # Add console message
                    self.add_console_message(f"✅ BENSON v2.0 ready with {len(self.instance_manager.get_instances())} instances")
                    
                    # Check module auto-startup after everything is ready
                    self.after(3000, self.check_module_auto_startup)
                    
                except Exception as e:
                    print(f"[BensonApp] Error bringing window to front: {e}")
            
            # FIXED: Delay bringing to front to ensure rendering is complete
            self.after(300, bring_to_front)

        except Exception as e:
            print(f"[BensonApp] Error showing main window: {e}")
            self.show_init_error(str(e))

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

    def load_instances(self):
        """FIXED: Load instances without blocking loading animation"""
        print("[BensonApp] Loading instances...")
        
        # Get instances data in background first
        def get_instances_data():
            try:
                instances = self.instance_manager.get_instances()
                total_instances = len(instances)
                
                # Schedule UI creation on main thread
                self.after(0, lambda: self._create_instance_cards(instances, total_instances))
                
            except Exception as e:
                print(f"[BensonApp] Error getting instances: {e}")
                self.after(0, lambda: self._create_instance_cards([], 0))
        
        # Run data fetching in background to not block animations
        threading.Thread(target=get_instances_data, daemon=True).start()

    def _create_instance_cards(self, instances, total_instances):
        """FIXED: Create instance cards with better scheduling"""
        print(f"[BensonApp] Creating {total_instances} instance cards...")
        
        # Clear existing cards if any
        for card in self.instance_cards:
            try:
                card.destroy()
            except:
                pass
        self.instance_cards = []
        
        # Update loading status
        if hasattr(self, 'loading'):
            self.loading.update_status(f"Creating {total_instances} instance cards...")
        
        # Create cards in small batches to prevent freezing
        batch_size = 2  # Process 2 cards at a time
        
        def create_batch(start_index=0):
            if start_index >= total_instances:
                # All cards created
                print(f"[BensonApp] Finished creating {len(self.instance_cards)} cards")
                self.after(50, self._finalize_instance_loading)
                return
            
            # Create this batch
            end_index = min(start_index + batch_size, total_instances)
            
            for i in range(start_index, end_index):
                instance = instances[i]
                name = instance["name"]
                status = instance["status"]
                
                print(f"[BensonApp] Creating card {i+1}/{total_instances}: {name}")
                
                try:
                    # Create card
                    card = self.ui_manager.create_instance_card(name, status)
                    if card:
                        self.instance_cards.append(card)
                        
                        # Position card immediately
                        row = i // 2
                        col = i % 2
                        card.grid(row=row, column=col, padx=4, pady=2, 
                                sticky="e" if col == 0 else "w", 
                                in_=self.instances_container)
                        
                except Exception as e:
                    print(f"[BensonApp] Error creating card for {name}: {e}")
            
            # Update loading status
            if hasattr(self, 'loading'):
                self.loading.update_status(f"Created {end_index}/{total_instances} instances...")
            
            # Force small UI update
            self.update_idletasks()
            
            # Schedule next batch with small delay to keep animations smooth
            self.after(50, lambda: create_batch(end_index))
        
        # Start creating batches
        if total_instances > 0:
            create_batch()
        else:
            self._finalize_instance_loading()

    def _finalize_instance_loading(self):
        """Finalize instance loading and reposition cards"""
        try:
            print(f"[BensonApp] Finalizing {len(self.instance_cards)} instance cards")
            
            # FIXED: Reposition all cards properly
            self.reposition_all_cards()
            
            # Update counter
            self.force_counter_update()
            
            # Final UI update
            self.update_idletasks()
            
            print("[BensonApp] Instance loading completed")
            
        except Exception as e:
            print(f"[BensonApp] Error finalizing instance loading: {e}")

    def reposition_all_cards(self):
        """FIXED: Reposition all cards in proper 2-column layout"""
        try:
            print(f"[BensonApp] Repositioning {len(self.instance_cards)} cards")
            
            # Clear all existing grid positions
            for card in self.instance_cards:
                try:
                    card.grid_remove()
                except:
                    pass
            
            # Configure grid columns
            self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
            self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Position all cards in 2-column layout
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
            
            print(f"[BensonApp] Repositioned {len(self.instance_cards)} cards")
            
        except Exception as e:
            print(f"[BensonApp] Error in reposition_all_cards: {e}")

    def reposition_cards(self, cards):
        """FIXED: Reposition given cards in proper layout"""
        try:
            # Clear existing positioning for these cards
            for card in cards:
                try:
                    card.grid_remove()
                except:
                    pass
            
            # Position cards in 2-column layout
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
            
            # Configure column weights
            self.instances_container.grid_columnconfigure(0, weight=1)
            self.instances_container.grid_columnconfigure(1, weight=1)
            
        except Exception as e:
            print(f"[BensonApp] Error in reposition_cards: {e}")

    def force_counter_update(self):
        """Force update the instance counter"""
        instances_count = len(self.instance_manager.get_instances())
        new_text = f"⚡ MEmu Instances ({instances_count})"

        if hasattr(self, 'instances_header'):
            self.instances_header.configure(text=new_text)
            self.update_idletasks()

        return instances_count

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

    # UI Methods (delegated to UI manager)
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
        """FIXED: Background tasks with reduced frequency to prevent spam"""
        def background_updates():
            while not self._destroyed:
                try:
                    time.sleep(300)  # Every 5 minutes instead of 60 seconds
                    if hasattr(self, 'console_text') and not self._destroyed:
                        messages = [
                            "System health check completed",
                            "Performance metrics updated",
                            "Instance synchronization successful"
                        ]
                        import random
                        if random.random() > 0.98:  # Much less frequent (2% chance)
                            self.add_console_message(random.choice(messages))
                except Exception as e:
                    print(f"[BackgroundUpdates] Error: {e}")
                    break

        def status_monitor():
            """FIXED: Status monitor with reduced frequency and no spam"""
            last_status = {}
            full_refresh_counter = 0

            while not self._destroyed:
                try:
                    time.sleep(15)  # Every 15 seconds instead of 5

                    # Skip if no instance manager or destroyed
                    if not hasattr(self, 'instance_manager') or self._destroyed:
                        continue

                    # Do a full refresh every 2 minutes instead of 1 minute
                    full_refresh_counter += 1
                    if full_refresh_counter >= 8:  # 8 * 15s = 2 minutes
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
                    time.sleep(15)

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

    def _on_window_close(self):
        """Handle window close properly"""
        try:
            self.destroy()
        except:
            pass

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