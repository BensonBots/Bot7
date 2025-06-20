#!/usr/bin/env python3
"""
BENSON v2.0 - FINAL FIXED Main Application
Working loading animation and smooth instance operations
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
        self._initializing = True
        self.instances_container = None
        
        # Initialize search variables
        self.search_var = tk.StringVar()
        self.search_entry = None

        # Show main window immediately
        self.center_window()
        self.deiconify()

        # Create WORKING loading overlay with VISIBLE animation
        self.loading = self._create_visible_loading()
        
        # Start initialization
        self.after(50, self.initialize_background)

    def _create_visible_loading(self):
        """Create loading overlay with GUARANTEED visible animation"""
        
        class VisibleLoadingOverlay:
            def __init__(self, parent):
                self.parent = parent
                self.overlay_frame = None
                self.animation_running = True
                self.animation_step = 0
                self.animation_id = None
                self.status_label = None
                self.progress_label = None
                self.logo_label = None
                self.dots_label = None
                
                print("[LoadingOverlay] 🎬 Creating VISIBLE loading overlay...")
                self._create_overlay()
                # Start animation immediately
                self.parent.after(1, self._start_visible_animation)
            
            def _create_overlay(self):
                """Create overlay with guaranteed visible elements"""
                try:
                    # Full screen overlay
                    self.overlay_frame = tk.Frame(self.parent, bg="#0a0e16")
                    self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)
                    
                    # Center container
                    center_frame = tk.Frame(self.overlay_frame, bg="#1e2329", relief="solid", bd=3)
                    center_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=400)
                    
                    # Content
                    content = tk.Frame(center_frame, bg="#1e2329")
                    content.pack(fill="both", expand=True, padx=40, pady=35)
                    
                    # LARGE animated logo
                    self.logo_label = tk.Label(
                        content,
                        text="🎯",
                        bg="#1e2329",
                        fg="#00d4ff",
                        font=("Segoe UI", 80)  # HUGE
                    )
                    self.logo_label.pack(pady=(0, 20))
                    
                    # Title
                    title = tk.Label(
                        content,
                        text="BENSON v2.0",
                        bg="#1e2329",
                        fg="#ffffff",
                        font=("Segoe UI", 32, "bold")
                    )
                    title.pack(pady=(0, 10))
                    
                    # Subtitle
                    subtitle = tk.Label(
                        content,
                        text="Advanced Edition",
                        bg="#1e2329",
                        fg="#00d4ff", 
                        font=("Segoe UI", 16)
                    )
                    subtitle.pack(pady=(0, 30))
                    
                    # Status
                    self.status_label = tk.Label(
                        content,
                        text="Initializing...",
                        bg="#1e2329",
                        fg="#ffffff",
                        font=("Segoe UI", 18, "bold")
                    )
                    self.status_label.pack(pady=(0, 20))
                    
                    # HUGE progress dots
                    self.progress_label = tk.Label(
                        content,
                        text="●○○○○",
                        bg="#1e2329",
                        fg="#00d4ff",
                        font=("Segoe UI", 28, "bold")  # HUGE
                    )
                    self.progress_label.pack(pady=(0, 15))
                    
                    # Extra animated dots
                    self.dots_label = tk.Label(
                        content,
                        text="...",
                        bg="#1e2329",
                        fg="#8b949e",
                        font=("Segoe UI", 20)
                    )
                    self.dots_label.pack()
                    
                    # Footer
                    footer = tk.Label(
                        content,
                        text="MEmu Instance Manager",
                        bg="#1e2329",
                        fg="#6b7280",
                        font=("Segoe UI", 12)
                    )
                    footer.pack(side="bottom", pady=(25, 0))
                    
                    # Force to top and update
                    self.overlay_frame.lift()
                    self.overlay_frame.tkraise()
                    self.parent.update()
                    
                    print("[LoadingOverlay] ✅ Visible overlay created")
                    
                except Exception as e:
                    print(f"[LoadingOverlay] ❌ Error creating overlay: {e}")
            
            def _start_visible_animation(self):
                """Start GUARANTEED visible animation"""
                if not self.animation_running:
                    return
                
                try:
                    # Check widgets exist
                    if not (self.overlay_frame and self.overlay_frame.winfo_exists()):
                        return
                    
                    if not (self.progress_label and self.progress_label.winfo_exists()):
                        return
                    
                    # Progress animation
                    progress_patterns = [
                        "●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●",
                        "○○○●○", "○○●○○", "○●○○○"
                    ]
                    
                    progress = progress_patterns[self.animation_step % len(progress_patterns)]
                    self.progress_label.configure(text=progress)
                    
                    # Logo color animation (dramatic)
                    if self.logo_label and self.logo_label.winfo_exists():
                        logo_colors = ["#00d4ff", "#00ff88", "#ffdd00", "#ff6b6b"]
                        logo_color = logo_colors[self.animation_step % len(logo_colors)]
                        self.logo_label.configure(fg=logo_color)
                    
                    # Dots animation
                    if self.dots_label and self.dots_label.winfo_exists():
                        dots_patterns = [".", "..", "...", "..", "."]
                        dots = dots_patterns[self.animation_step % len(dots_patterns)]
                        self.dots_label.configure(text=dots)
                    
                    self.animation_step += 1
                    
                    # FORCE immediate visual update
                    try:
                        self.progress_label.update()
                        if self.logo_label:
                            self.logo_label.update()
                        if self.dots_label:
                            self.dots_label.update()
                        self.parent.update_idletasks()
                    except:
                        pass
                    
                    # Schedule next frame (250ms for smooth visible animation)
                    if self.animation_running:
                        self.animation_id = self.parent.after(250, self._start_visible_animation)
                    
                    print(f"[LoadingOverlay] 🎬 Animation frame {self.animation_step}: {progress}")
                    
                except Exception as e:
                    print(f"[LoadingOverlay] ❌ Animation error: {e}")
                    self.animation_running = False
            
            def update_status(self, status_text):
                """Update status with FORCED visibility"""
                try:
                    if self.status_label and self.status_label.winfo_exists():
                        self.status_label.configure(text=status_text)
                        # FORCE immediate updates
                        self.status_label.update_idletasks()
                        self.status_label.update()
                        self.parent.update_idletasks()
                        self.parent.update()
                        print(f"[LoadingOverlay] 📝 Status: {status_text}")
                except Exception as e:
                    print(f"[LoadingOverlay] ❌ Status error: {e}")
            
            def close(self):
                """Close overlay"""
                try:
                    print("[LoadingOverlay] 🔄 Closing overlay...")
                    
                    # Stop animation
                    self.animation_running = False
                    
                    # Cancel animation
                    if self.animation_id:
                        try:
                            self.parent.after_cancel(self.animation_id)
                        except:
                            pass
                    
                    # Destroy overlay
                    if self.overlay_frame and self.overlay_frame.winfo_exists():
                        self.overlay_frame.destroy()
                    
                    # Clear references
                    self.overlay_frame = None
                    self.status_label = None
                    self.progress_label = None
                    self.logo_label = None
                    self.dots_label = None
                    
                    print("[LoadingOverlay] ✅ Overlay closed")
                    
                except Exception as e:
                    print(f"[LoadingOverlay] ❌ Close error: {e}")
        
        return VisibleLoadingOverlay(self)

    def initialize_background(self):
        """Initialize with proper status updates"""
        def init_worker():
            try:
                # Step 1: Create InstanceManager
                self._safe_update_status("Connecting to MEmu...")
                time.sleep(0.8)  # Longer delay to see animation

                self.instance_manager = InstanceManager()
                self.instance_manager.app = self
                print("[Init] InstanceManager created")

                # Step 2: Load instances
                self._safe_update_status("Loading MEmu instances...")
                time.sleep(0.8)

                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] {instances_count} instances loaded")

                # Step 3: Initialize modules
                self._safe_update_status("Initializing modules...")
                time.sleep(0.8)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Modules initialized")

                # Step 4: Setup utilities
                self._safe_update_status("Setting up utilities...")
                time.sleep(0.8)

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
            time.sleep(0.2)  # Give time for UI to update
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
            self.add_console_message("BENSON v2.0 Advanced Edition started")
            self.add_console_message(f"Loaded {instances_count} MEmu instances")

            # Finalize
            self.loading.update_status("Finalizing...")
            self.after(500, lambda: self.finalize_and_show(instances_count))

        except Exception as e:
            print(f"[BensonApp] UI setup error: {e}")
            self.show_init_error(str(e))

    def finalize_and_show(self, instances_count):
        """Finalize and show main window"""
        try:
            # Load instance cards
            self.load_instance_cards_simple()
            
            # Close loading overlay
            self.loading.close()
            
            # Mark initialization complete
            self._initializing = False
            
            # Focus main window
            self.lift()
            self.focus_force()
            
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
                    
                    # Update UI every few cards
                    if i % 3 == 2:
                        self.update_idletasks()
                    
                    print(f"[BensonApp] Created card {i + 1}/{len(instances)}: {name}")
            
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
            
            print(f"[BensonApp] Completed card creation: {len(self.instance_cards)} cards")
            
        except Exception as e:
            print(f"[LoadCards] Error: {e}")

    # Removed the problematic load_instances_after_create method that was causing duplicates
    # Now instance operations handle their own card creation

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

    # Instance Operations
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

    # Console operations
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
        except:
            pass
        super().destroy()


if __name__ == "__main__":
    print("Starting BENSON v2.0...")
    app = BensonApp()
    app.mainloop()