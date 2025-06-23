#!/usr/bin/env python3
"""
BENSON v2.0 - FIXED Main Application with Auto-startup Integration
Working loading animation and proper auto-startup triggering
"""

import tkinter as tk
from datetime import datetime
import threading
import time

# Import our custom modules
from core.instance_manager import InstanceManager
from utils.module_manager import ModuleManager


class BensonApp(tk.Tk):
    def __init__(self):
        super().__init__()

        print("[BensonApp] Initializing application...")

        # Configure window but DON'T show it yet
        self.title("BENSON v2.0 - Advanced Edition")
        self.geometry("1200x800")
        self.configure(bg="#0a0e16")
        self.minsize(900, 600)
        
        # Center window but keep it hidden
        self.update_idletasks()
        width = 1200
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Keep window hidden during initialization
        self.withdraw()
        
        # Initialize variables
        self.instance_cards = []
        self.filtered_instances = []
        self.selected_cards = []
        self.search_after_id = None
        self._destroyed = False
        self._initializing = True
        self.instances_container = None
        
        # Initialize search variables
        self.search_var = tk.StringVar()
        self.search_entry = None

        # Create a temporary window just for the loading screen
        self.temp_window = tk.Toplevel()
        self.temp_window.withdraw()  # Hide it initially
        
        # Create simple loading overlay
        self.loading = self._create_simple_loading()
        
        # Start initialization
        self.after(100, self.initialize_background)

    def _create_simple_loading(self):
        """Create a compact, professional loading dialog"""
        
        # Create loading window
        loading_window = tk.Toplevel(self)
        loading_window.title("BENSON v2.0")
        loading_window.configure(bg="#1a1f2e")
        loading_window.attributes('-topmost', True)
        loading_window.resizable(False, False)
        
        # Make it a small, compact window
        window_width = 400
        window_height = 300
        loading_window.update_idletasks()
        screen_width = loading_window.winfo_screenwidth()
        screen_height = loading_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Keep window decorations but make it non-resizable
        # loading_window.overrideredirect(True)  # Removed this line
        
        # Main container with border
        main_container = tk.Frame(loading_window, bg="#00d4ff", bd=2, relief="solid")
        main_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Content frame
        content_frame = tk.Frame(main_container, bg="#1a1f2e")
        content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Logo - smaller and more appropriate
        logo = tk.Label(content_frame, text="⚡", bg="#1a1f2e", fg="#00d4ff", 
                       font=("Segoe UI", 48, "bold"))
        logo.pack(pady=(30, 15))
        
        # Title
        title = tk.Label(content_frame, text="BENSON v2.0", bg="#1a1f2e", fg="#ffffff",
                        font=("Segoe UI", 20, "bold"))
        title.pack(pady=(0, 8))
        
        # Subtitle
        subtitle = tk.Label(content_frame, text="MEmu Instance Manager", bg="#1a1f2e", fg="#00d4ff",
                           font=("Segoe UI", 11))
        subtitle.pack(pady=(0, 25))
        
        # Progress bar container
        progress_container = tk.Frame(content_frame, bg="#1a1f2e")
        progress_container.pack(pady=(0, 15))
        
        # Simple progress bar
        progress_bg = tk.Frame(progress_container, bg="#2a2f3e", height=6, width=200)
        progress_bg.pack()
        
        progress_canvas = tk.Canvas(progress_bg, width=200, height=6, bg="#2a2f3e", 
                                   highlightthickness=0, bd=0)
        progress_canvas.pack()
        
        # Status label
        status_label = tk.Label(content_frame, text="🚀 Initializing...", bg="#1a1f2e", fg="#ffffff",
                               font=("Segoe UI", 12, "bold"))
        status_label.pack(pady=(0, 10))
        
        # Progress dots
        dots_label = tk.Label(content_frame, text="●●●", bg="#1a1f2e", fg="#00d4ff",
                             font=("Segoe UI", 14))
        dots_label.pack()
        
        # Footer
        footer = tk.Label(content_frame, text="Loading...",
                         bg="#1a1f2e", fg="#6b7280", font=("Segoe UI", 9))
        footer.pack(side="bottom", pady=(15, 10))
        
        # Show window
        loading_window.deiconify()
        loading_window.lift()
        loading_window.focus_force()
        
        # Simple, clean loading controller
        class CompactLoadingController:
            def __init__(self, window, status_label, dots_label, progress_canvas):
                self.window = window
                self.status_label = status_label
                self.dots_label = dots_label
                self.progress_canvas = progress_canvas
                self.animation_step = 0
                self.animation_id = None
                self.running = True
                self._start_animation()
            
            def _start_animation(self):
                if not self.running or not self.window.winfo_exists():
                    return
                
                try:
                    # Simple dots animation
                    dot_patterns = ["●○○", "○●○", "○○●", "●●○", "●●●", "○○○"]
                    pattern = dot_patterns[self.animation_step % len(dot_patterns)]
                    self.dots_label.configure(text=pattern)
                    
                    # Simple progress bar animation
                    self.progress_canvas.delete("all")
                    progress_width = (self.animation_step % 40) * 5  # 0 to 200
                    if progress_width > 0:
                        self.progress_canvas.create_rectangle(0, 0, progress_width, 6, 
                                                            fill="#00d4ff", outline="")
                    
                    self.animation_step += 1
                    self.animation_id = self.window.after(300, self._start_animation)
                except:
                    self.running = False
            
            def update_status(self, status_text):
                try:
                    if self.status_label.winfo_exists():
                        status_icons = {
                            "connecting": "🔗", "loading": "📦", "initializing": "⚙️",
                            "setting up": "🛠️", "building": "🏗️", "creating": "🎯",
                            "console": "📝", "finishing": "🎉", "ready": "✨",
                            "finalizing": "✨"
                        }
                        
                        icon = "🚀"
                        for key, emoji in status_icons.items():
                            if key in status_text.lower():
                                icon = emoji
                                break
                        
                        # Truncate long status messages
                        if len(status_text) > 25:
                            status_text = status_text[:22] + "..."
                        
                        formatted_status = f"{icon} {status_text}"
                        self.status_label.configure(text=formatted_status)
                        print(f"[LoadingOverlay] 📝 Status: {formatted_status}")
                except:
                    pass
            
            def close(self):
                try:
                    print("[LoadingOverlay] 🔄 Closing overlay...")
                    self.running = False
                    if self.animation_id:
                        self.window.after_cancel(self.animation_id)
                    if self.window.winfo_exists():
                        self.window.destroy()
                    print("[LoadingOverlay] ✅ Overlay closed")
                except:
                    pass
        
        print("[LoadingOverlay] ✅ Compact loading dialog created")
        return CompactLoadingController(loading_window, status_label, dots_label, progress_canvas)

    def initialize_background(self):
        """Initialize with proper status updates"""
        def init_worker():
            try:
                # Step 1: Create InstanceManager
                self._safe_update_status("Connecting to MEmu...")
                time.sleep(1.0)  # Longer delay to see animation

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

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Modules initialized")

                # Step 4: Setup utilities
                self._safe_update_status("Setting up utilities...")
                time.sleep(1.0)

                # Import here to avoid circular imports
                from utils.instance_operations import InstanceOperations
                from utils.ui_manager import UIManager
                
                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                print("[Init] Utilities set up")

                # Schedule UI setup
                self.after(0, lambda: self.setup_ui_and_finalize(instances_count))

            except Exception as e:
                print(f"[Init ERROR] {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self.show_init_error(str(e)))

        # Start initialization
        threading.Thread(target=init_worker, daemon=True, name="Init").start()

    def _safe_update_status(self, status):
        """Safely update loading status"""
        try:
            self.after(0, lambda: self.loading.update_status(status))
            time.sleep(0.3)  # Give time for UI to update
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

            # Add initial console messages AFTER UI is set up
            print("[BensonApp] Adding initial console messages...")
            self.add_console_message("BENSON v2.0 started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")
            print("[BensonApp] Initial console messages added")

            # Finalize - start card loading process
            self.loading.update_status("Creating instance cards...")
            self.after(300, lambda: self.finalize_and_show(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            self.show_init_error(str(e))

    def finalize_and_show(self, instances_count):
        """Finalize and show main window"""
        try:
            # Start loading instance cards with progress tracking
            self.loading.update_status("Creating instance cards...")
            self._load_cards_with_progress(instances_count)
            
        except Exception as e:
            print(f"[Finalize] Error: {e}")
            self.show_init_error(str(e))

    def _load_cards_with_progress(self, instances_count):
        """Load cards with progress updates"""
        try:
            print("[BensonApp] Starting card creation with progress tracking...")
            instances = self.instance_manager.get_instances()
            
            if not instances:
                print("[BensonApp] No instances to load")
                self.loading.update_status("No instances found")
                self.after(1000, lambda: self._complete_finalization(0))
                return
            
            # Start loading cards one by one with progress
            self._load_next_card(instances, 0, instances_count)
            
        except Exception as e:
            print(f"[LoadCardsProgress] Error: {e}")
            self.show_init_error(str(e))

    def _load_next_card(self, instances, index, total_instances):
        """Load cards one by one with progress updates"""
        try:
            if index >= len(instances):
                # All cards loaded, finalize
                print(f"[BensonApp] All {len(self.instance_cards)} cards loaded successfully")
                self.loading.update_status("All cards loaded! Finalizing...")
                
                # Configure grid
                if hasattr(self, 'instances_container') and self.instance_cards:
                    self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                    self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
                
                # Update scroll region
                if hasattr(self.ui_manager, 'update_scroll_region'):
                    self.ui_manager.update_scroll_region()
                
                # Update counter
                if hasattr(self, 'instances_header'):
                    self.instances_header.configure(text=f"Instances ({len(self.instance_cards)})")
                
                # Force final UI update
                self.update_idletasks()
                self.update()
                
                # Complete after short delay to ensure UI is ready
                self.after(500, lambda: self._complete_finalization(total_instances))
                return
            
            # Load current card
            instance = instances[index]
            name = instance["name"]
            status = instance["status"]
            
            # Update progress
            progress = f"Creating cards... ({index + 1}/{len(instances)})"
            self.loading.update_status(progress)
            print(f"[BensonApp] Creating card {index + 1}/{len(instances)}: {name}")
            
            # Create the card
            card = self.ui_manager.create_instance_card(name, status)
            if card:
                self.instance_cards.append(card)
                
                # Grid placement
                row = index // 2
                col = index % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", 
                        in_=self.instances_container)
                
                # Force immediate update
                card.update_idletasks()
                self.update_idletasks()
                
                print(f"[BensonApp] Card {index + 1} created and placed: {name}")
            
            # Schedule next card creation (with small delay for smooth loading)
            self.after(150, lambda: self._load_next_card(instances, index + 1, total_instances))
            
        except Exception as e:
            print(f"[LoadNextCard] Error at index {index}: {e}")
            # Continue with next card even if one fails
            self.after(100, lambda: self._load_next_card(instances, index + 1, total_instances))

    def _complete_finalization(self, instances_count):
        """Complete the finalization process"""
        try:
            print(f"[BensonApp] Completing finalization with {instances_count} instances")
            
            # Show finalizing status
            self.loading.update_status("Setting up console...")
            
            # Ensure console is ready and add messages
            self._ensure_console_ready_and_add_messages(instances_count)
            
        except Exception as e:
            print(f"[CompleteFinalization] Error: {e}")
            # Fallback - close loading anyway
            self.after(1000, self._close_loading_and_show)

    def _ensure_console_ready_and_add_messages(self, instances_count):
        """Ensure console is ready and add final messages"""
        try:
            # Check if console exists and is ready
            if not hasattr(self, 'console_text') or not self.console_text:
                print("[Console] Console not ready yet, waiting...")
                self.after(200, lambda: self._ensure_console_ready_and_add_messages(instances_count))
                return
            
            # Force console to be ready
            try:
                self.console_text.update_idletasks()
                print("[Console] Console widget is ready")
            except:
                print("[Console] Console widget not accessible yet, waiting...")
                self.after(200, lambda: self._ensure_console_ready_and_add_messages(instances_count))
                return
            
            # Add the missing console messages that should have been added earlier
            print("[Console] Adding final console messages...")
            self.add_console_message(f"✅ BENSON v2.0 ready with {instances_count} instances")
            
            # Force console update
            self.console_text.update_idletasks()
            self.console_text.update()
            
            # Force UI updates
            self.update_idletasks()
            self.update()
            
            print("[Console] Console messages added successfully")
            
            # Now wait for UI to render the console
            self.after(600, lambda: self._show_ready_and_close(instances_count))
            
        except Exception as e:
            print(f"[ConsoleReady] Error: {e}")
            # Fallback
            self.after(1000, self._close_loading_and_show)

    def _show_ready_and_close(self, instances_count):
        """Show ready status and close loading"""
        try:
            print("[Console] Showing ready status and preparing to close")
            
            # Show final ready status
            self.loading.update_status("Console ready! Finishing...")
            
            # Force one more update to ensure console is visible
            self.update_idletasks()
            self.update()
            
            # Wait longer for user to see everything is ready
            self.after(1200, self._close_loading_and_show)
            
        except Exception as e:
            print(f"[ShowReady] Error: {e}")
            self.after(500, self._close_loading_and_show)

    def _close_loading_and_show(self):
        """Close loading and show main window"""
        try:
            print("[BensonApp] Closing loading screen and showing main window...")
            
            # Close loading overlay
            self.loading.close()
            
            # Clean up temp window
            if hasattr(self, 'temp_window'):
                try:
                    self.temp_window.destroy()
                except:
                    pass
            
            # NOW show the main window
            self.deiconify()
            
            # Mark initialization complete
            self._initializing = False
            
            # Focus main window
            self.lift()
            self.focus_force()
            
            print("[BensonApp] ✅ Main window is now visible and ready!")
            
            # NEW: Trigger initial auto-startup check after app is fully loaded
            self.after(2000, self._trigger_initial_auto_startup)
            
        except Exception as e:
            print(f"[CloseLoading] Error: {e}")
            # Fallback - show window anyway
            self.deiconify()

    def _trigger_initial_auto_startup(self):
        """NEW: Trigger initial auto-startup check after app is fully loaded"""
        try:
            if hasattr(self, 'module_manager') and self.module_manager:
                self.add_console_message("🔍 Performing initial auto-startup check...")
                self.module_manager.check_auto_startup_initial()
            else:
                print("[BensonApp] Module manager not available for auto-startup")
        except Exception as e:
            print(f"[AutoStartup] Error triggering initial auto-startup: {e}")

    def force_refresh_instances(self):
        """Force refresh instances - called by instance manager (DISABLED)"""
        try:
            print("[BensonApp] Force refresh disabled - using simple card addition instead")
            # Don't do full refresh anymore - instance operations handle it
            pass
            
        except Exception as e:
            print(f"[ForceRefresh] Error: {e}")

    def load_instance_cards_simple(self):
        """Load instance cards without freezing"""
        try:
            print("[BensonApp] Loading instance cards...")
            instances = self.instance_manager.get_instances()
            
            for i, instance in enumerate(instances):
                name = instance["name"]
                status = instance["status"]
                
                card = self.ui_manager.create_instance_card(name, status)
                if card:
                    self.instance_cards.append(card)
                    
                    # Grid placement
                    row = i // 2
                    col = i % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
                    
                    # Force immediate update for visibility
                    card.update_idletasks()
                    
                    # Update UI every few cards with more aggressive updates
                    if i % 2 == 1:  # Update more frequently
                        self.update_idletasks()
                        self.update()
                    
                    print(f"[BensonApp] Created card {i + 1}/{len(instances)}: {name}")
            
            # Configure grid
            if hasattr(self, 'instances_container') and self.instance_cards:
                self.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Force final updates
            if hasattr(self, 'instances_container'):
                self.instances_container.update_idletasks()
                self.instances_container.update()
            
            # Update scroll region
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
            
            # Update counter
            if hasattr(self, 'instances_header'):
                self.instances_header.configure(text=f"Instances ({len(self.instance_cards)})")
            
            # Final UI update to ensure everything is visible
            self.update_idletasks()
            self.update()
            
            print(f"[BensonApp] Completed card creation: {len(self.instance_cards)} cards")
            
        except Exception as e:
            print(f"[LoadCards] Error: {e}")

    def reposition_all_cards(self):
        """Reposition all instance cards in grid"""
        try:
            for i, card in enumerate(self.instance_cards):
                if card and card.winfo_exists():
                    row = i // 2
                    col = i % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.instances_container)
            
            # Update scroll region after repositioning
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
                
        except Exception as e:
            print(f"[RepositionCards] Error: {e}")

    def force_counter_update(self):
        """Force update of instance counter"""
        try:
            if hasattr(self, 'instances_header'):
                count = len(self.instance_cards)
                self.instances_header.configure(text=f"Instances ({count})")
        except Exception as e:
            print(f"[CounterUpdate] Error: {e}")

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
            self.load_instance_cards_simple()
            
            # Update counter
            self.force_counter_update()
            
        except Exception as e:
            print(f"[LoadInstances] Error: {e}")

    # FIXED: Instance Operations with Auto-startup Integration
    def start_instance(self, name):
        """Start instance with optimization and auto-startup integration"""
        def start_with_optimization():
            try:
                self.add_console_message(f"🔧 Auto-optimizing {name} before start...")
                # FIXED: Use the correct method name
                success = self.instance_manager.optimize_instance_settings(name)
                if success:
                    self.add_console_message(f"✅ {name} optimized successfully")
                else:
                    self.add_console_message(f"⚠ {name} optimization failed, starting anyway...")

                # Start the instance
                start_success = self.instance_manager.start_instance(name)
                
                if start_success:
                    self.add_console_message(f"✅ Started: {name}")
                    
                    # NEW: Trigger auto-startup check for this specific instance
                    if hasattr(self, 'module_manager') and self.module_manager:
                        self.add_console_message(f"🔍 Checking auto-startup for {name}...")
                        # Use the main thread to trigger auto-startup
                        self.after(0, lambda: self.module_manager.trigger_auto_startup_for_instance(name))
                    
                else:
                    self.add_console_message(f"❌ Failed to start: {name}")
                    
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

    # Console operations
    def add_console_message(self, message):
        """Add message to console with better error handling"""
        # Always print to console for debugging
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
            
            # Force immediate update
            self.console_text.update_idletasks()
            
            print(f"[Console] Successfully added message: {message}")
        except Exception as e:
            print(f"[Console] Error adding message: {e} - Message was: {message}")

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

            # Update scroll region after filtering
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

    def show_all_instances(self):
        """Show all instance cards"""
        try:
            for i, card in enumerate(self.instance_cards):
                row = i // 2
                col = i % 2
                card.grid(row=row, column=col, padx=4, pady=2, 
                        sticky="e" if col == 0 else "w", 
                        in_=self.instances_container)
            
            # Update scroll region
            if hasattr(self.ui_manager, 'update_scroll_region'):
                self.ui_manager.update_scroll_region()
                
        except Exception as e:
            print(f"[ShowAll] Error: {e}")

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
            if hasattr(self, 'module_manager'):
                self.module_manager.stop_status_monitoring()
        except:
            pass
        super().destroy()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()