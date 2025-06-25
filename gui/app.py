#!/usr/bin/env python3
"""
BENSON v2.0 - Streamlined Main Application
Reduced code with same functionality and design
"""

import tkinter as tk
from datetime import datetime
import threading
import time

from core.instance_manager import InstanceManager


class BensonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        print("[BensonApp] Initializing application...")

        # Configure window
        self.title("BENSON v2.0 - Advanced Edition")
        self.geometry("1200x800")
        self.configure(bg="#0a0e16")
        self.minsize(900, 600)
        
        # Center window but keep hidden
        self._center_window()
        self.withdraw()
        
        # Initialize variables
        self.instance_cards = []
        self.selected_cards = []
        self._destroyed = False
        self._initializing = True
        self.instances_container = None
        self.search_var = tk.StringVar()
        self.search_entry = None
        self.search_after_id = None

        # Create loading screen
        self.loading = self._create_loading_screen()
        
        # Start initialization
        self.after(500, self.initialize_background)

    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = 1200
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_loading_screen(self):
        """Create simple loading dialog"""
        loading_window = tk.Toplevel(self)
        loading_window.title("BENSON v2.0")
        loading_window.configure(bg="#1a1f2e")
        loading_window.attributes('-topmost', True)
        loading_window.resizable(False, False)
        
        # Position and size
        window_width = 400
        window_height = 300
        loading_window.update_idletasks()
        screen_width = loading_window.winfo_screenwidth()
        screen_height = loading_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(loading_window, bg="#00d4ff", bd=2, relief="solid")
        main_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        content_frame = tk.Frame(main_container, bg="#1a1f2e")
        content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Logo and title
        tk.Label(content_frame, text="⚡", bg="#1a1f2e", fg="#00d4ff", 
                font=("Segoe UI", 48, "bold")).pack(pady=(30, 15))
        
        tk.Label(content_frame, text="BENSON v2.0", bg="#1a1f2e", fg="#ffffff",
                font=("Segoe UI", 20, "bold")).pack(pady=(0, 8))
        
        tk.Label(content_frame, text="MEmu Instance Manager", bg="#1a1f2e", fg="#00d4ff",
                font=("Segoe UI", 11)).pack(pady=(0, 25))
        
        # Status label
        status_label = tk.Label(content_frame, text="🚀 Initializing...", bg="#1a1f2e", fg="#ffffff",
                               font=("Segoe UI", 12, "bold"))
        status_label.pack(pady=(0, 10))
        
        # Progress dots
        dots_label = tk.Label(content_frame, text="●●●", bg="#1a1f2e", fg="#00d4ff",
                             font=("Segoe UI", 14))
        dots_label.pack()
        
        tk.Label(content_frame, text="Loading...", bg="#1a1f2e", fg="#6b7280", 
                font=("Segoe UI", 9)).pack(side="bottom", pady=(15, 10))
        
        loading_window.deiconify()
        loading_window.lift()
        loading_window.focus_force()
        
        # Loading controller
        class LoadingController:
            def __init__(self, window, status_label, dots_label):
                self.window = window
                self.status_label = status_label
                self.dots_label = dots_label
                self.animation_step = 0
                self.running = True
                self._start_animation()
            
            def _start_animation(self):
                if not self.running or not self.window.winfo_exists():
                    return
                
                try:
                    dot_patterns = ["●○○", "○●○", "○○●", "●●○", "●●●", "○○○"]
                    pattern = dot_patterns[self.animation_step % len(dot_patterns)]
                    self.dots_label.configure(text=pattern)
                    
                    self.animation_step += 1
                    self.window.after(300, self._start_animation)
                except:
                    self.running = False
            
            def update_status(self, status_text):
                try:
                    if self.status_label.winfo_exists():
                        status_icons = {
                            "connecting": "🔗", "loading": "📦", "initializing": "⚙️",
                            "setting up": "🛠️", "building": "🏗️", "creating": "🎯",
                            "console": "📝", "finishing": "🎉", "ready": "✨"
                        }
                        
                        icon = "🚀"
                        for key, emoji in status_icons.items():
                            if key in status_text.lower():
                                icon = emoji
                                break
                        
                        if len(status_text) > 25:
                            status_text = status_text[:22] + "..."
                        
                        self.status_label.configure(text=f"{icon} {status_text}")
                except:
                    pass
            
            def close(self):
                try:
                    self.running = False
                    if self.window.winfo_exists():
                        self.window.destroy()
                except:
                    pass
        
        print("[LoadingOverlay] Loading dialog created")
        return LoadingController(loading_window, status_label, dots_label)

    def initialize_background(self):
        """Initialize in background"""
        def init_worker():
            try:
                # Step 1: Create InstanceManager
                self._safe_update_status("Connecting to MEmu...")
                time.sleep(1.0)

                self.instance_manager = InstanceManager()
                self.instance_manager.app = self
                print("[Init] InstanceManager created")

                # Step 2: Load instances
                self._safe_update_status("Loading MEmu instances...")
                time.sleep(1.0)

                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] {instances_count} instances loaded")

                # Step 3: Initialize modules
                self._safe_update_status("Initializing modules...")
                time.sleep(1.0)

                try:
                    from utils.module_manager import ModuleManager
                    self.module_manager = ModuleManager(self)
                    print("[Init] ✅ Module manager created successfully")
                except Exception as e:
                    print(f"[Init] ❌ Module manager creation failed: {e}")
                    self.module_manager = None

                # Step 4: Setup utilities
                self._safe_update_status("Setting up utilities...")
                time.sleep(1.0)

                from utils.instance_operations import InstanceOperations
                from utils.ui_manager import UIManager
                
                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Utilities set up")

                # Schedule UI setup
                self.after(0, lambda: self.setup_ui_and_finalize(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                self.after(0, lambda: self.show_init_error(str(e)))

        threading.Thread(target=init_worker, daemon=True, name="Init").start()

    def _safe_update_status(self, status):
        """Safely update loading status"""
        try:
            self.after(0, lambda: self.loading.update_status(status))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Init] Error updating status: {e}")

    def setup_ui_and_finalize(self, instances_count):
        """Setup UI and finalize"""
        try:
            print("[BensonApp] Setting up UI...")
            self.loading.update_status("Building interface...")

            # Setup UI components
            self.ui_manager.setup_header()
            self.ui_manager.setup_controls()
            self.ui_manager.setup_main_content()
            self.ui_manager.setup_console()
            self.ui_manager.setup_footer()
            
            print("[BensonApp] UI setup complete")

            # Add initial console messages
            self.add_console_message("BENSON v2.0 started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")
            
            if self.module_manager and self.module_manager.initialization_complete:
                self.add_console_message("✅ Module system initialized successfully")
            
            # Start card loading
            self.loading.update_status("Creating instance cards...")
            self.after(300, lambda: self._load_cards_and_show(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            self.show_init_error(str(e))

    def _load_cards_and_show(self, instances_count):
        """Load cards and show main window"""
        try:
            instances = self.instance_manager.get_instances()
            
            if instances:
                self._load_cards_with_progress(instances)
            else:
                self.loading.update_status("No instances found")
                self.after(1000, self._complete_and_show)
                
        except Exception as e:
            print(f"[LoadCards] Error: {e}")
            self.show_init_error(str(e))

    def _load_cards_with_progress(self, instances):
        """Load cards with progress updates"""
        def load_next_card(index=0):
            if index >= len(instances):
                # All cards loaded
                self._finalize_ui()
                self.after(500, self._complete_and_show)
                return
            
            instance = instances[index]
            
            # Update progress
            progress = f"Creating cards... ({index + 1}/{len(instances)})"
            self.loading.update_status(progress)
            
            # Create card
            card = self.ui_manager.create_instance_card(instance["name"], instance["status"])
            if card:
                self.instance_cards.append(card)
                
                # Position card
                row = index // 2
                col = index % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", in_=self.instances_container)
                
                card.update_idletasks()
                self.update_idletasks()
            
            # Schedule next card
            self.after(150, lambda: load_next_card(index + 1))
        
        load_next_card()

    def _finalize_ui(self):
        """Finalize UI setup"""
        try:
            # Configure grid
            if self.instances_container and self.instance_cards:
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Update scroll region and counter
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
            
            if hasattr(self, 'instances_header'):
                self.instances_header.configure(text=f"Instances ({len(self.instance_cards)})")
            
            self.update_idletasks()
            
        except Exception as e:
            print(f"[FinalizeUI] Error: {e}")

    def _complete_and_show(self):
        """Complete initialization and show main window"""
        try:
            self.loading.update_status("Console ready! Finishing...")
            
            # Add final console messages
            instances_count = len(self.instance_cards)
            self.add_console_message(f"✅ BENSON v2.0 ready with {instances_count} instances")
            
            if self.module_manager and self.module_manager.initialization_complete:
                self.add_console_message("🔧 Module system ready - start instances to activate")
            
            # Force console update
            if hasattr(self, 'console_text'):
                self.console_text.update_idletasks()
                self.console_text.update()
            
            self.update_idletasks()
            self.update()
            
            # Close loading and show main window
            self.after(1200, self._show_main_window)
            
        except Exception as e:
            print(f"[CompleteAndShow] Error: {e}")
            self.after(500, self._show_main_window)

    def _show_main_window(self):
        """Show the main window"""
        try:
            print("[BensonApp] Showing main window...")
            
            # Close loading
            self.loading.close()
            
            # Show main window
            self.deiconify()
            self._initializing = False
            self.lift()
            self.focus_force()
            
            print("[BensonApp] ✅ Main window is now visible and ready!")
            
        except Exception as e:
            print(f"[ShowMainWindow] Error: {e}")
            self.deiconify()

    # Instance operations with module integration
    def start_instance(self, name):
        """Start instance with optimization and module integration"""
        def start_with_optimization():
            try:
                self.add_console_message(f"🔧 Auto-optimizing {name} before start...")
                
                # Optimize instance
                success = self.instance_manager.optimize_instance_settings(name)
                if success:
                    self.add_console_message(f"✅ {name} optimized successfully")
                
                # Start instance
                start_success = self.instance_manager.start_instance(name)
                
                if start_success:
                    self.add_console_message(f"✅ Started: {name}")
                    
                    # Trigger modules if ready
                    if (hasattr(self, 'module_manager') and self.module_manager and 
                        self.module_manager.initialization_complete):
                        self.add_console_message(f"🔍 Triggering modules for {name}...")
                        self.after(3000, lambda: self.module_manager.trigger_auto_startup_for_instance(name))
                    else:
                        self.add_console_message(f"ℹ️ Module system not ready for {name}")
                else:
                    self.add_console_message(f"❌ Failed to start: {name}")
                        
            except Exception as e:
                self.add_console_message(f"❌ Error starting {name}: {e}")

        threading.Thread(target=start_with_optimization, daemon=True).start()

    def stop_instance(self, name):
        """Stop instance with module cleanup"""
        def stop_with_cleanup():
            try:
                self.add_console_message(f"🔄 Stopping instance: {name}")
                
                # Clean up modules first
                if hasattr(self, 'module_manager') and self.module_manager:
                    self.module_manager.cleanup_for_stopped_instance(name)
                
                # Stop instance
                success = self.instance_manager.stop_instance(name)
                
                if success:
                    self.add_console_message(f"✅ Stopped: {name}")
                else:
                    self.add_console_message(f"❌ Failed to stop: {name}")
                        
            except Exception as e:
                self.add_console_message(f"❌ Error stopping {name}: {e}")

        threading.Thread(target=stop_with_cleanup, daemon=True).start()

    def show_modules(self, instance_name):
        """Show modules window"""
        self.ui_manager.show_modules(instance_name)

    # Console operations
    def add_console_message(self, message):
        """Add message to console"""
        print(f"[Console] {message}")
        
        if not hasattr(self, 'console_text'):
            print(f"[Console] Console widget not available yet: {message}")
            return

        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            full_message = f"{timestamp} {message}\n"

            self.console_text.configure(state="normal")
            self.console_text.insert("end", full_message)
            self.console_text.configure(state="disabled")
            self.console_text.see("end")
            self.console_text.update_idletasks()
            
        except Exception as e:
            print(f"[Console] Error adding message: {e}")

    def clear_console(self):
        """Clear console"""
        try:
            if hasattr(self, 'console_text'):
                self.console_text.configure(state="normal")
                self.console_text.delete("1.0", "end")
                self.console_text.configure(state="disabled")
                self.add_console_message("Console cleared")
        except Exception as e:
            print(f"[Clear] Error: {e}")

    def show_init_error(self, error):
        """Show initialization error"""
        from tkinter import messagebox
        try:
            if hasattr(self, 'loading'):
                self.loading.close()
        except:
            pass
        
        messagebox.showerror("Initialization Error",
                           f"Failed to initialize BENSON:\n\n{error}\n\nThe application will close.")
        self.destroy()

    # Search functionality
    def on_search_change_debounced(self, *args):
        """Handle search with debouncing"""
        if self.search_after_id:
            self.after_cancel(self.search_after_id)

        query = self.search_var.get()
        if query == "Search instances...":
            return

        self.search_after_id = self.after(300, lambda: self._filter_instances(query))

    def _filter_instances(self, query):
        """Filter instances"""
        try:
            if not query or query == "Search instances...":
                self._show_all_instances()
                return

            query_lower = query.lower()
            visible_cards = []

            for card in self.instance_cards:
                if hasattr(card, 'name') and query_lower in card.name.lower():
                    visible_cards.append(card)

            self._apply_filter_results(visible_cards)

        except Exception as e:
            print(f"[Filter] Error: {e}")

    def _apply_filter_results(self, visible_cards):
        """Apply filter results to UI"""
        try:
            for card in self.instance_cards:
                card.grid_remove()

            for i, card in enumerate(visible_cards):
                row = i // 2
                col = i % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", 
                        in_=self.instances_container)

            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()

        except Exception as e:
            print(f"[ApplyFilter] Error: {e}")

    def on_search_focus_in(self, event):
        """Handle search focus in"""
        try:
            if hasattr(self, 'search_entry') and self.search_entry:
                if self.search_entry.get() == "Search instances...":
                    self.search_entry.delete(0, "end")
                    self.search_entry.configure(fg="#ffffff")
        except Exception as e:
            print(f"[SearchFocusIn] Error: {e}")

    def on_search_focus_out(self, event):
        """Handle search focus out"""
        try:
            if hasattr(self, 'search_entry') and self.search_entry:
                if not self.search_entry.get():
                    self.search_entry.insert(0, "Search instances...")
                    self.search_entry.configure(fg="#8b949e")
        except Exception as e:
            print(f"[SearchFocusOut] Error: {e}")

    def _show_all_instances(self):
        """Show all instance cards"""
        try:
            for i, card in enumerate(self.instance_cards):
                row = i // 2
                col = i % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", 
                        in_=self.instances_container)
            
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
                
        except Exception as e:
            print(f"[ShowAll] Error: {e}")

    def on_card_selection_changed(self):
        """Called when a card's selection state changes"""
        try:
            self.selected_cards = [card for card in self.instance_cards 
                                 if hasattr(card, 'selected') and card.selected]
        except Exception as e:
            print(f"[CardSelection] Error: {e}")

    def load_instances(self):
        """Load/reload all instances"""
        try:
            # Clear existing cards
            for card in self.instance_cards:
                try:
                    card.destroy()
                except:
                    pass
            self.instance_cards = []
            
            # Load fresh cards
            instances = self.instance_manager.get_instances()
            for i, instance in enumerate(instances):
                card = self.ui_manager.create_instance_card(instance["name"], instance["status"])
                if card:
                    self.instance_cards.append(card)
                    
                    # Position card
                    row = i // 2
                    col = i % 2
                    card.grid(row=i // 2, column=i % 2, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
            
            # Update UI
            if hasattr(self, 'instances_container') and self.instance_cards:
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
            
            if hasattr(self, 'instances_header'):
                self.instances_header.configure(text=f"Instances ({len(self.instance_cards)})")
            
            self.update_idletasks()
            
        except Exception as e:
            print(f"[LoadInstances] Error: {e}")

    def force_refresh_instances(self):
        """Force refresh instances"""
        try:
            print("[BensonApp] Force refresh disabled - using simple card addition instead")
        except Exception as e:
            print(f"[ForceRefresh] Error: {e}")

    def destroy(self):
        """Clean shutdown"""
        self._destroyed = True
        try:
            if hasattr(self, 'loading'):
                self.loading.close()
            if hasattr(self, 'module_manager') and self.module_manager:
                self.module_manager.stop_all_modules()
        except:
            pass
        super().destroy()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()