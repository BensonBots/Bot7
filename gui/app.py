#!/usr/bin/env python3
"""
BENSON v2.0 - Fixed Main Application with Integrated Loading
Uses integrated loading overlay instead of external window
"""

import tkinter as tk
from datetime import datetime
import threading
import time

# Import our custom modules
from core.instance_manager import InstanceManager
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
        self._initializing = True
        self.instances_container = None
        
        # Initialize search variables
        self.search_var = tk.StringVar()
        self.search_entry = None

        # Show main window immediately
        self.center_window()
        self.deiconify()

        # FIXED: Create integrated loading overlay directly
        self.loading = self._create_integrated_loading()
        
        # Start initialization after a short delay
        self.after(200, self.initialize_background)

    def _create_integrated_loading(self):
        """Create beautiful modern loading overlay"""
        class ModernLoading:
            def __init__(self, parent):
                self.parent = parent
                self.overlay_frame = None
                self.animation_running = True
                self.animation_step = 0
                self.animation_id = None
                self.status_label = None
                self.progress_label = None
                self.logo_label = None
                self._create_overlay()
                self._start_animation()
            
            def _create_overlay(self):
                """Create beautiful loading overlay"""
                try:
                    # Main overlay with gradient-like effect
                    self.overlay_frame = tk.Frame(self.parent, bg="#0a0e16", relief="flat", bd=0)
                    self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)
                    
                    # Subtle background gradient effect
                    bg_frame = tk.Frame(self.overlay_frame, bg="#0a0e16")
                    bg_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                    
                    # Center content container with modern styling
                    content_frame = tk.Frame(bg_frame, bg="#1e2329", relief="flat", bd=0)
                    content_frame.place(relx=0.5, rely=0.5, anchor="center", width=420, height=320)
                    
                    # Subtle border effect
                    border_frame = tk.Frame(content_frame, bg="#343a46", height=2)
                    border_frame.pack(fill="x")
                    
                    # Main content area
                    main_content = tk.Frame(content_frame, bg="#1e2329")
                    main_content.pack(fill="both", expand=True, padx=40, pady=40)
                    
                    # Logo with modern styling
                    self.logo_label = tk.Label(
                        main_content,
                        text="🎯",
                        bg="#1e2329",
                        fg="#00d4ff",
                        font=("Segoe UI", 48)
                    )
                    self.logo_label.pack(pady=(0, 20))
                    
                    # Modern title
                    self.title_label = tk.Label(
                        main_content,
                        text="BENSON",
                        bg="#1e2329",
                        fg="#ffffff",
                        font=("Segoe UI", 28, "bold")
                    )
                    self.title_label.pack(pady=(0, 8))
                    
                    # Version with accent color
                    version_label = tk.Label(
                        main_content,
                        text="v2.0 Advanced Edition",
                        bg="#1e2329",
                        fg="#00d4ff",
                        font=("Segoe UI", 12)
                    )
                    version_label.pack(pady=(0, 30))
                    
                    # Status with modern font
                    self.status_label = tk.Label(
                        main_content,
                        text="Initializing...",
                        bg="#1e2329",
                        fg="#ffffff",
                        font=("Segoe UI", 12)
                    )
                    self.status_label.pack(pady=(0, 20))
                    
                    # Modern progress bar-like animation
                    progress_container = tk.Frame(main_content, bg="#1e2329")
                    progress_container.pack()
                    
                    self.progress_label = tk.Label(
                        progress_container,
                        text="●○○○○",
                        bg="#1e2329",
                        fg="#00d4ff",
                        font=("Segoe UI", 16)
                    )
                    self.progress_label.pack()
                    
                    # Subtle footer
                    footer_label = tk.Label(
                        main_content,
                        text="Advanced MEmu Instance Manager",
                        bg="#1e2329",
                        fg="#8b949e",
                        font=("Segoe UI", 9)
                    )
                    footer_label.pack(side="bottom", pady=(30, 0))
                    
                    self.overlay_frame.lift()
                    print("[LoadingOverlay] Modern loading overlay created")
                    
                except Exception as e:
                    print(f"[LoadingOverlay] Error: {e}")
            
            def _start_animation(self):
                """Simple, smooth animation that actually works"""
                if not self.animation_running or not self.overlay_frame:
                    return
                try:
                    # Simple working progress animation
                    patterns = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●"]
                    
                    if self.progress_label and self.progress_label.winfo_exists():
                        pattern = patterns[self.animation_step % len(patterns)]
                        self.progress_label.configure(text=pattern)
                    
                    # Simple logo color pulse
                    if self.logo_label and self.logo_label.winfo_exists():
                        colors = ["#00d4ff", "#33ddff", "#00d4ff", "#66e6ff"]
                        color = colors[self.animation_step % len(colors)]
                        self.logo_label.configure(fg=color)
                    
                    self.animation_step += 1
                    
                    if self.animation_running:
                        self.animation_id = self.parent.after(400, self._start_animation)
                        
                except Exception as e:
                    print(f"[LoadingAnimation] Error: {e}")
                    self.animation_running = False
            
            def update_status(self, status_text):
                """Update status with smooth transition"""
                try:
                    if self.status_label and self.status_label.winfo_exists():
                        self.status_label.configure(text=status_text)
                        self.parent.update_idletasks()
                        print(f"[LoadingOverlay] Status: {status_text}")
                except:
                    pass
            
            def close(self):
                """Smooth close with fade effect"""
                try:
                    print("[LoadingOverlay] Closing with fade...")
                    self.animation_running = False
                    
                    if self.animation_id:
                        try:
                            self.parent.after_cancel(self.animation_id)
                        except:
                            pass
                    
                    # Fade out effect
                    if self.overlay_frame and self.overlay_frame.winfo_exists():
                        self._fade_out()
                    
                except Exception as e:
                    print(f"[LoadingOverlay] Close error: {e}")
            
            def _fade_out(self):
                """Smooth fade out animation"""
                fade_colors = ["#1e2329", "#161b22", "#0f1419", "#0a0e16", "#050709"]
                step = 0
                
                def fade_step():
                    nonlocal step
                    try:
                        if step < len(fade_colors) and self.overlay_frame.winfo_exists():
                            # Find the content frame and update its color
                            for child in self.overlay_frame.winfo_children():
                                for content in child.winfo_children():
                                    content.configure(bg=fade_colors[step])
                                    
                            step += 1
                            if step < len(fade_colors):
                                self.parent.after(80, fade_step)
                            else:
                                self.overlay_frame.destroy()
                                self.overlay_frame = None
                                print("[LoadingOverlay] Fade complete")
                    except:
                        try:
                            self.overlay_frame.destroy()
                        except:
                            pass
                
                fade_step()
        
        return ModernLoading(self)

    def initialize_background(self):
        """Initialize in background thread"""
        def init_worker():
            try:
                # Step 1: Create InstanceManager
                self.after_idle(lambda: self.loading.update_status("Connecting to MEmu..."))
                print("[Init] Step 1: Connecting to MEmu")
                time.sleep(0.5)

                self.instance_manager = InstanceManager()
                self.instance_manager.app = self  # For callbacks
                print("[Init] Step 2: InstanceManager created")

                # Step 2: Load instances
                self.after_idle(lambda: self.loading.update_status("Loading MEmu instances..."))
                time.sleep(0.5)

                self.instance_manager.load_real_instances()
                instances_count = len(self.instance_manager.get_instances())
                print(f"[Init] Step 3: {instances_count} instances loaded")

                # Step 3: Initialize modules
                self.after_idle(lambda: self.loading.update_status("Initializing modules..."))
                time.sleep(0.5)

                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                print("[Init] Step 4: Modules initialized")

                # Step 4: Setup utilities
                self.after_idle(lambda: self.loading.update_status("Setting up utilities..."))
                time.sleep(0.5)

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

            # Load cards after UI setup
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
        """SMOOTH: Add new instance card with elegant fade-in animation"""
        print("[BensonApp] ===== SMOOTH CARD ADDITION =====")
        
        try:
            # Step 1: Get current instance count
            current_count = len(self.instance_cards)
            print(f"[BensonApp] Current UI cards: {current_count}")
            
            # Step 2: Reload instances from MEmu
            self.instance_manager.load_real_instances()
            new_instances = self.instance_manager.get_instances()
            new_count = len(new_instances)
            print(f"[BensonApp] MEmu instances: {new_count}")
            
            # Step 3: Check if we need to add a new card
            if new_count > current_count:
                print(f"[BensonApp] ✨ Adding {new_count - current_count} new card(s)")
                
                # Find the new instance(s) by comparing with existing cards
                existing_names = [card.name for card in self.instance_cards if hasattr(card, 'name')]
                
                for instance in new_instances:
                    if instance["name"] not in existing_names:
                        print(f"[BensonApp] 🎨 Creating new card for: {instance['name']}")
                        
                        # Create the new card
                        new_card = self.ui_manager.create_instance_card(
                            instance["name"], 
                            instance["status"]
                        )
                        
                        if new_card:
                            # Add to our list
                            self.instance_cards.append(new_card)
                            
                            # Position the new card
                            total_cards = len(self.instance_cards)
                            row = (total_cards - 1) // 2
                            col = (total_cards - 1) % 2
                            
                            new_card.grid(row=row, column=col, padx=4, pady=2, 
                                        sticky="e" if col == 0 else "w", 
                                        in_=self.instances_container)
                            
                            # Start with invisible card
                            new_card.configure(bg="#0a0e16")  # Match background
                            new_card.main_container.configure(bg="#0a0e16")
                            
                            # Trigger smooth fade-in animation
                            self._animate_card_fade_in(new_card, instance["name"])
                            
                            print(f"[BensonApp] ✅ Added card for: {instance['name']}")
                            break
            
            elif new_count < current_count:
                print(f"[BensonApp] 🗑 Instance was deleted, doing full refresh...")
                self._full_refresh_instances()
                
            else:
                print(f"[BensonApp] 🔄 No new instances, checking for renames...")
                # Check for name changes (renames)
                self._check_for_renames(new_instances)
            
            # Update counter
            if hasattr(self, 'instances_header'):
                self.instances_header.configure(text=f"Instances ({len(self.instance_cards)})")
            
            # Add console message
            self.add_console_message(f"✅ Instance ready - Total: {len(self.instance_cards)} instances")
                
        except Exception as e:
            print(f"[BensonApp] ❌ SMOOTH ADDITION ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to full refresh
            self._full_refresh_instances()
        
        print("[BensonApp] ===== SMOOTH ADDITION COMPLETE =====")
    
    def _animate_card_fade_in(self, card, name):
        """Simple, smooth fade-in animation that doesn't lag"""
        print(f"[BensonApp] 🎭 Starting simple fade-in for: {name}")
        
        # Simple 3-step fade
        fade_steps = ["#1a1f2e", "#2a2f3e", "#343a46"]
        step = 0
        
        def animate_step():
            nonlocal step
            try:
                if step < len(fade_steps) and card.winfo_exists():
                    color = fade_steps[step]
                    
                    # Simple border animation
                    if hasattr(card, 'main_container'):
                        card.main_container.configure(bg=color)
                    
                    step += 1
                    if step < len(fade_steps):
                        card.after(200, animate_step)  # Slower, smoother
                    else:
                        # Final highlight
                        card.after(100, lambda: self._final_card_highlight(card))
                        
            except tk.TclError:
                print(f"[BensonApp] Animation stopped - card destroyed")
        
        # Start simple animation
        animate_step()
    
    def _final_card_highlight(self, card):
        """Brief highlight at the end"""
        try:
            if card.winfo_exists() and hasattr(card, 'main_container'):
                # Brief blue highlight
                card.main_container.configure(bg="#00d4ff")
                card.after(300, lambda: card.main_container.configure(bg="#343a46") if card.winfo_exists() else None)
        except:
            pass
    
    def _check_for_renames(self, new_instances):
        """Check if any instances were renamed and update cards"""
        try:
            # Create mapping of index -> new_name
            index_to_name = {inst["index"]: inst["name"] for inst in new_instances}
            
            for card in self.instance_cards:
                if hasattr(card, 'name'):
                    # Find this card's instance by name in the new list
                    card_instance = None
                    for inst in new_instances:
                        if inst["name"] == card.name:
                            card_instance = inst
                            break
                    
                    # If not found by name, try to find by checking for renames
                    if not card_instance:
                        # This might be a renamed instance
                        print(f"[BensonApp] 🏷 Possible rename detected for: {card.name}")
                        # For now, just log it - we could add rename detection logic here
            
        except Exception as e:
            print(f"[BensonApp] Error checking renames: {e}")
    
    def _full_refresh_instances(self):
        """Full refresh when needed (fallback)"""
        print("[BensonApp] 🔄 Performing full refresh...")
        
        try:
            # Get fresh data
            self.instance_manager.load_real_instances()
            new_instances = self.instance_manager.get_instances()
            
            # Clear existing cards
            for card in self.instance_cards:
                try:
                    card.destroy()
                except:
                    pass
            self.instance_cards = []
            
            # Recreate all cards
            for i, instance in enumerate(new_instances):
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
            
            # Update UI
            self.instances_container.update_idletasks()
            self.update_idletasks()
            
            print(f"[BensonApp] ✅ Full refresh complete: {len(self.instance_cards)} cards")
            
        except Exception as e:
            print(f"[BensonApp] Full refresh error: {e}")
    
    def force_refresh_instances(self):
        """Manual force refresh - same as clicking refresh button"""
        print("[BensonApp] Manual force refresh triggered...")
        self.load_instances_after_create()
    
    def _fallback_background_refresh(self):
        """Fallback background refresh if immediate refresh fails"""
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