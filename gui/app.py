#!/usr/bin/env python3
"""
BENSON v2.0 - Fixed Main Application
Keep the good design, fix the core issues
"""

import tkinter as tk
from datetime import datetime
import threading
import time

# Import our custom modules
from core.instance_manager import InstanceManager
from gui.components.loading_overlay import LoadingOverlay
from utils.instance_operations import InstanceOperations
from utils.ui_manager import UIManager
from utils.module_manager import ModuleManager


class BensonApp(tk.Tk):
    def __init__(self):
        super().__init__()

        print("[BensonApp] Initializing application...")

        # Configure window - KEEP the design but add title bar back
        self.title("BENSON v2.0 - Advanced Edition")
        self.geometry("1200x800")
        self.configure(bg="#0a0e16")
        self.minsize(900, 600)
        
        # FIXED: Use normal window with title bar (no custom controls)
        # self.overrideredirect(True)  # Commented out to get title bar back
        
        # Hide initially
        self.withdraw()

        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        self._destroyed = False
        self._initializing = True
        self.instances_container = None
        
        # FIXED: Initialize search variables
        self.search_var = tk.StringVar()
        self.search_entry = None

        # Show loading overlay FIRST and make sure it's visible
        self.loading = LoadingOverlay(self)
        self.loading.window.deiconify()
        self.loading.window.lift()  # FIXED: Force loading to front
        self.loading.window.focus_force()  # FIXED: Give loading focus
        
        # Start initialization
        self.after(500, self.initialize_background)

    def initialize_background(self):
        """Initialize in background thread - FIXED threading"""
        def init_worker():
            try:
                # Step 1: Create InstanceManager
                self.after_idle(lambda: self.loading.update_status("Connecting to MEmu..."))
                print("[Init] Step 1: Connecting to MEmu")
                time.sleep(0.3)

                self.instance_manager = InstanceManager()
                self.instance_manager.app = self  # For callbacks
                print("[Init] Step 2: InstanceManager created")

                # Step 2: Load instances
                self.after_idle(lambda: self.loading.update_status("Loading MEmu instances..."))
                time.sleep(0.3)

                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] Step 3: {instances_count} instances loaded")

                # Step 3: Initialize modules
                self.after_idle(lambda: self.loading.update_status("Initializing modules..."))
                time.sleep(0.3)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Step 4: Modules initialized")

                # Step 4: Setup utilities
                self.after_idle(lambda: self.loading.update_status("Setting up utilities..."))
                time.sleep(0.3)

                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Step 5: Utilities set up")

                # Schedule UI setup on main thread
                self.after_idle(lambda: self.setup_ui_and_finalize(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                self.after_idle(lambda: self.show_init_error(str(e)))

        # Start initialization in background thread
        threading.Thread(target=init_worker, daemon=True).start()

    def setup_ui_and_finalize(self, instances_count):
        """Setup UI and finalize - FIXED to handle missing methods"""
        try:
            print("[BensonApp] Setting up UI...")
            self.loading.update_status("Building interface...")

            # Setup UI components - TRY original method, fallback to regular
            try:
                self.ui_manager.setup_header_original()  # Try original method
            except AttributeError:
                print("[BensonApp] setup_header_original not found, using setup_header")
                self.ui_manager.setup_header()  # Fallback to regular method
            
            self.ui_manager.setup_controls()
            self.ui_manager.setup_main_content()
            self.ui_manager.setup_console()
            self.ui_manager.setup_footer()
            
            print("[BensonApp] UI setup complete")

            # Add initial console messages
            self.add_console_message("BENSON v2.0 Advanced Edition started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")

            # FIXED: Load cards after UI setup
            self.loading.update_status("Finalizing...")
            self.after(200, lambda: self.finalize_and_show(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            self.show_init_error(str(e))

    def finalize_and_show(self, instances_count):
        """Finalize and show main window"""
        try:
            # Close loading
            self.loading.close()
            
            # Show main window
            self.center_window()
            self.deiconify()
            self.lift()
            self.focus_force()
            
            # Mark initialization complete
            self._initializing = False
            
            # Load instance cards
            self.load_instance_cards_simple()
            
            # Final message
            self.add_console_message(f"✅ BENSON v2.0 ready with {instances_count} instances")
            
            print("[BensonApp] Initialization complete")
            
        except Exception as e:
            print(f"[Finalize] Error: {e}")

    def center_window(self):
        """Center window on screen"""
        try:
            self.update_idletasks()
            width = 1200
            height = 800
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
            print(f"[BensonApp] Centered window at {x},{y}")
        except Exception as e:
            print(f"[Center] Error: {e}")

    def load_instance_cards_simple(self):
        """SIMPLIFIED: Load instance cards without freezing"""
        try:
            print("[BensonApp] Loading instance cards...")
            instances = self.instance_manager.get_instances()
            
            for i, instance in enumerate(instances):
                name = instance["name"]
                status = instance["status"]
                
                card = self.ui_manager.create_instance_card(name, status)
                if card:
                    self.instance_cards.append(card)
                    
                    # Simple grid placement
                    row = i // 2
                    col = i % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
                    
                    print(f"[BensonApp] Created card {i + 1}/{len(instances)}: {name}")
            
            # Configure grid
            if hasattr(self, 'instances_container') and self.instance_cards:
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            print(f"[BensonApp] Completed card creation: {len(self.instance_cards)} cards")
            
        except Exception as e:
            print(f"[LoadCards] Error: {e}")

    def load_instances_after_create(self):
        """FIXED: Refresh instances after creation"""
        print("[BensonApp] Refreshing after instance creation...")
        
        def refresh_worker():
            try:
                # Reload instances
                self.instance_manager.load_real_instances()
                instances = self.instance_manager.get_instances()
                
                # Update UI on main thread
                self.after_idle(lambda: self.refresh_cards_simple(instances))
                
            except Exception as e:
                print(f"[Refresh] Error: {e}")
        
        threading.Thread(target=refresh_worker, daemon=True).start()

    def refresh_cards_simple(self, instances):
        """Simple card refresh"""
        try:
            old_count = len(self.instance_cards)
            new_count = len(instances)
            
            if new_count != old_count:
                print(f"[Refresh] Instance count changed: {old_count} -> {new_count}")
                
                # Clear existing cards
                for card in self.instance_cards:
                    try:
                        card.destroy()
                    except:
                        pass
                self.instance_cards = []
                
                # Recreate all cards
                for i, instance in enumerate(instances):
                    name = instance["name"]
                    status = instance["status"]
                    
                    card = self.ui_manager.create_instance_card(name, status)
                    if card:
                        self.instance_cards.append(card)
                        
                        row = i // 2
                        col = i % 2
                        card.grid(row=row, column=col, padx=4, pady=2, 
                                sticky="e" if col == 0 else "w", 
                                in_=self.instances_container)
                
                # Update counter
                if hasattr(self, 'instances_header'):
                    self.instances_header.configure(text=f"Instances ({new_count})")
                
                print(f"[Refresh] Cards refreshed: {len(self.instance_cards)} total")
            
        except Exception as e:
            print(f"[RefreshCards] Error: {e}")

    # Instance Operations - KEEP original functionality
    def start_instance(self, name):
        """Start instance with optimization"""
        def start_with_optimization():
            try:
                self.add_console_message(f"🔧 Auto-optimizing {name} before start...")
                success = self.instance_manager.optimize_instance_with_settings(name)
                if success:
                    self.add_console_message(f"✅ {name} optimized successfully")
                else:
                    self.add_console_message(f"⚠ {name} optimization failed, starting anyway...")

                self.instance_ops.start_instance(name)
            except Exception as e:
                self.add_console_message(f"❌ Error in start_instance: {e}")

        threading.Thread(target=start_with_optimization, daemon=True).start()

    def stop_instance(self, name):
        """Stop instance"""
        self.instance_ops.stop_instance(name)

    def delete_instance_card_with_loading(self, card):
        """Delete instance card"""
        self.instance_ops.delete_instance_card_with_animation(card)

    def show_modules(self, instance_name):
        """Show modules window"""
        self.ui_manager.show_modules(instance_name)

    # Console operations - KEEP original
    def add_console_message(self, message):
        """Add message to console"""
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
        except Exception as e:
            print(f"[Console] Error: {e}")

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

    # FIXED: Add missing search functionality
    def on_search_change_debounced(self, *args):
        """Handle search text change with debouncing"""
        if self.search_after_id:
            self.after_cancel(self.search_after_id)

        query = self.search_var.get()
        if query == "Search instances...":
            return

        self.search_after_id = self.after(300, lambda: self._filter_instances_simple(query))

    def _filter_instances_simple(self, query):
        """Simple instance filtering"""
        try:
            if not query or query == "Search instances...":
                self.show_all_instances()
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

    def show_all_instances(self):
        """Show all instance cards"""
        try:
            for i, card in enumerate(self.instance_cards):
                row = i // 2
                col = i % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", 
                        in_=self.instances_container)
        except Exception as e:
            print(f"[ShowAll] Error: {e}")

    # FIXED: Add missing card selection method
    def on_card_selection_changed(self):
        """Called when a card's selection state changes"""
        try:
            self.selected_cards = [card for card in self.instance_cards if hasattr(card, 'selected') and card.selected]
        except Exception as e:
            print(f"[CardSelection] Error: {e}")

    def destroy(self):
        """Clean shutdown"""
        self._destroyed = True
        try:
            if hasattr(self, 'loading'):
                self.loading.close()
        except:
            pass
        super().destroy()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()