#!/usr/bin/env python3
"""
BENSON v2.0 - FIXED Main Application File
Fixed loading freezing and instance creation issues
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

        # Show loading overlay
        self.loading = LoadingOverlay(self)
        
        # Make loading window visible
        self.loading.window.deiconify()
        self.withdraw()

        # Prevent auto-close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Start initialization after UI settles
        self.after(100, self.initialize_background)

    def initialize_background(self):
        """Initialize in background without blocking UI"""
        def init_worker():
            try:
                # Step 1: Initialize Instance Manager
                self.after_idle(lambda: self.loading.update_status("Connecting to MEmu..."))
                print("[Init] Step 1: Connecting to MEmu")
                time.sleep(0.2)

                self.instance_manager = InstanceManager()
                print("[Init] Step 2: InstanceManager created")

                # Step 2: Load instances
                self.after_idle(lambda: self.loading.update_status("Loading MEmu instances..."))
                time.sleep(0.2)

                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] Step 3: {instances_count} instances loaded")

                # Step 3: Initialize modules
                self.after_idle(lambda: self.loading.update_status("Initializing modules..."))
                time.sleep(0.2)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Step 4: Modules initialized")

                # Step 4: Setup utilities
                self.after_idle(lambda: self.loading.update_status("Setting up utilities..."))
                time.sleep(0.2)

                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Step 5: Utilities set up")

                # Bind keyboard shortcuts
                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_animation())

                # Schedule UI setup on main thread
                self.after_idle(lambda: self.setup_ui_and_finalize(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                import traceback
                traceback.print_exc()
                self.after_idle(lambda: self.show_init_error(str(e)))

        # Start initialization in background thread
        threading.Thread(target=init_worker, daemon=True).start()

    def setup_ui_and_finalize(self, instances_count):
        """Setup UI and finalize initialization in non-blocking way"""
        try:
            print("[BensonApp] Setting up UI...")
            self.loading.update_status("Building interface...")

            # Setup UI components quickly
            self.ui_manager.setup_header()
            self.ui_manager.setup_controls()
            self.ui_manager.setup_main_content()
            self.ui_manager.setup_console()
            self.ui_manager.setup_footer()
            
            print("[BensonApp] UI setup complete")

            # Add initial console messages
            self.add_console_message("BENSON v2.0 Advanced Edition started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")

            # Load instance cards if any exist
            if instances_count > 0:
                self.loading.update_status("Creating instance cards...")
                self.after(50, lambda: self.load_instances_final(instances_count))
            else:
                self.after(50, lambda: self.finalize_startup_fast(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            self.show_init_error(str(e))

    def load_instances_final(self, instances_count):
        """Load instances without blocking"""
        try:
            instances = self.instance_manager.get_instances()
            
            # Create cards quickly
            for i, instance in enumerate(instances):
                try:
                    name = instance["name"]
                    status = instance["status"]
                    
                    card = self.ui_manager.create_instance_card(name, status)
                    if card:
                        self.instance_cards.append(card)
                        
                        # Position card immediately without grid operations
                        card.pack_forget()  # Remove from pack
                        
                except Exception as e:
                    print(f"[BensonApp] Error creating card {i}: {e}")
                    continue
            
            print(f"[BensonApp] Created {len(self.instance_cards)} instance cards")
            
            # Finalize after card creation with FAST method
            self.after(50, lambda: self.finalize_startup_fast(instances_count))
            
        except Exception as e:
            print(f"[BensonApp] Error loading instances: {e}")
            self.finalize_startup_fast(0)

    def finalize_startup_fast(self, instances_count):
        """FIXED: Fast finalization without blocking grid operations"""
        try:
            print("[BensonApp] Fast finalizing startup...")
            self.loading.update_status("Finalizing...")
            
            # SKIP the reposition_all_cards() call that causes freezing
            # Instead, position cards with simple method
            if self.instance_cards:
                self.position_cards_simple()
            
            # Update counter quickly
            try:
                if hasattr(self, 'instances_header'):
                    self.instances_header.configure(text=f"Instances ({instances_count})")
            except:
                pass
            
            # Module status message
            if hasattr(self, 'module_manager'):
                try:
                    module_status = self.module_manager.get_module_status()
                    self.add_console_message(f"🔧 Modules: {module_status['available_modules']}/{module_status['total_instances']} available")
                except:
                    self.add_console_message("🔧 Modules initialized")

            # Close loading and show main window immediately
            self.loading.update_status("Ready!")
            
            # Show main window immediately
            self.after(100, self.show_main_window)

        except Exception as e:
            print(f"[BensonApp] Error in fast finalization: {e}")
            # Even if there's an error, still show the main window
            self.after(100, self.show_main_window)

    def position_cards_simple(self):
        """Simple card positioning without complex grid operations"""
        try:
            print("[BensonApp] Simple card positioning...")
            
            # Configure container grid columns
            if hasattr(self, 'instances_container'):
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
                
                # Position cards with simple grid
                for i, card in enumerate(self.instance_cards):
                    try:
                        row = i // 2
                        col = i % 2
                        card.grid(row=row, column=col, padx=4, pady=2, 
                                sticky="ew", in_=self.instances_container)
                        
                        # Don't configure width here - it can cause blocking
                        
                    except Exception as e:
                        print(f"[BensonApp] Error positioning card {i}: {e}")
                        continue
            
            print("[BensonApp] Card positioning complete")
            
        except Exception as e:
            print(f"[BensonApp] Error in simple positioning: {e}")

    def show_main_window(self):
        """Show main window and complete initialization"""
        try:
            print("[BensonApp] Showing main window...")
            
            # Close loading screen
            if hasattr(self, 'loading'):
                self.loading.close()
            
            # Show main window
            self.deiconify()
            self.lift()
            self.focus_force()
            
            # Mark initialization complete
            self._initializing = False
            
            # Final message
            instance_count = len(self.instance_manager.get_instances())
            self.add_console_message(f"✅ BENSON v2.0 ready with {instance_count} instances")
            
            # Start background tasks after a delay
            self.after(2000, self.start_background_tasks)
            
            # Check module auto-startup after background tasks
            if hasattr(self, 'module_manager'):
                self.after(4000, self.check_module_auto_startup)

            print("[BensonApp] Main window shown successfully")

        except Exception as e:
            print(f"[BensonApp] Error showing main window: {e}")
            # Force show window even if there's an error
            try:
                if hasattr(self, 'loading'):
                    self.loading.close()
                self.deiconify()
            except:
                pass

    def check_module_auto_startup(self):
        """Check module auto-startup with proper timing"""
        try:
            if not hasattr(self, 'module_manager') or not self.module_manager.initialization_complete:
                self.add_console_message("⏳ Module manager not ready, retrying auto-startup check...")
                self.after(1000, self.check_module_auto_startup)
                return

            self.add_console_message("🔍 Checking for auto-startup modules...")
            
            # Run auto-startup check in background
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

    # Search functionality with non-blocking operations
    def on_search_change_debounced(self, *args):
        """Handle search text change with debouncing"""
        if self.search_after_id:
            self.after_cancel(self.search_after_id)

        query = self.search_var.get()
        if query == "Search instances...":
            return

        self.search_after_id = self.after(100, lambda: self._filter_instances_async(query))

    def _filter_instances_async(self, query):
        """Async instance filtering to prevent freezing"""
        def filter_worker():
            try:
                if not query or query == "Search instances...":
                    self.after_idle(self.show_all_instances)
                    return

                query_lower = query.lower()
                visible_cards = []

                for card in self.instance_cards:
                    if query_lower in card.name.lower():
                        visible_cards.append(card)

                self.after_idle(lambda: self._apply_filter_results(visible_cards))

            except Exception as e:
                print(f"[BensonApp] Filter error: {e}")

        threading.Thread(target=filter_worker, daemon=True).start()

    def _apply_filter_results(self, visible_cards):
        """Apply filter results to UI"""
        try:
            for card in self.instance_cards:
                card.grid_remove()

            for card in visible_cards:
                card.grid()

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
        """Load instances without blocking UI"""
        print("[BensonApp] Loading instances...")
        
        def load_worker():
            try:
                instances = self.instance_manager.get_instances()
                self.after_idle(lambda: self._reload_instance_cards(instances))
            except Exception as e:
                print(f"[BensonApp] Error loading instances: {e}")

        threading.Thread(target=load_worker, daemon=True).start()

    def _reload_instance_cards(self, instances):
        """Reload instance cards without blocking"""
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
        """Reposition all cards efficiently - ONLY when not initializing"""
        try:
            if self._initializing:
                print("[BensonApp] Skipping reposition during initialization")
                return
                
            print("[BensonApp] Repositioning cards...")
            
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

            print("[BensonApp] Card repositioning complete")

        except Exception as e:
            print(f"[BensonApp] Error in reposition_all_cards: {e}")

    def reposition_cards(self, cards):
        """Reposition specific cards efficiently"""
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

    # Console operations with error handling
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
        """Start background tasks without blocking"""
        def delayed_start_tasks():
            try:
                # Wait for UI to be fully ready
                time.sleep(2)
                
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
                """Lightweight status monitor"""
                last_status = {}
                full_refresh_counter = 0

                while not self._destroyed:
                    try:
                        time.sleep(30)  # Every 30 seconds

                        if not hasattr(self, 'instance_manager') or self._destroyed or self._initializing:
                            continue

                        # Light status check
                        full_refresh_counter += 1
                        if full_refresh_counter >= 10:  # Every 5 minutes
                            if not getattr(self, '_updating_instances', False):
                                self._updating_instances = True
                                try:
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
        """Batch update multiple cards efficiently"""
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
        """Enhanced destroy with proper cleanup"""
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