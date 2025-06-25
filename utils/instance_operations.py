"""
BENSON v2.0 - Streamlined Instance Operations
Cleaned up version with proper module integration and status updates
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time


class InstanceOperations:
    """Streamlined instance operations with clean module integration"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """Create instance with loading card"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()
        self.app.add_console_message(f"🔄 Creating MEmu instance: {name}")
        
        # Create loading card
        loading_card = self._create_loading_card(name)
        
        # Start creation in background
        def creation_thread():
            try:
                success = self.app.instance_manager.create_instance_with_name(name)
                self.app.after(0, lambda: self._handle_creation_completion(name, loading_card, success))
            except Exception as e:
                self.app.after(0, lambda: self._handle_creation_completion(name, loading_card, False, str(e)))
        
        threading.Thread(target=creation_thread, daemon=True, name=f"Create-{name}").start()

    def _create_loading_card(self, name):
        """Create loading card"""
        try:
            from gui.components.loading_instance_card import create_loading_instance_card
            loading_card = create_loading_instance_card(self.app.instances_container, name)
            
            # Position it
            current_cards = len(self.app.instance_cards)
            row = current_cards // 2
            col = current_cards % 2
            loading_card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w")
            
            # Add to list temporarily
            self.app.instance_cards.append(loading_card)
            self._update_counter()
            self.app.update_idletasks()
            
            if hasattr(self.app.ui_manager, 'update_scroll_region'):
                self.app.ui_manager.update_scroll_region()
                self.app.after(100, self.app.ui_manager.scroll_to_bottom)
            
            return loading_card
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error creating loading card: {e}")
            return None

    def _handle_creation_completion(self, name, loading_card, success, error_msg=None):
        """Handle creation completion"""
        try:
            if success:
                if loading_card:
                    loading_card.show_success()
                self.app.after(1200, lambda: self._add_new_instance_card(name, loading_card))
            else:
                if loading_card:
                    loading_card.show_error(error_msg or "Creation failed")
                self.app.after(3000, lambda: self._remove_loading_card(loading_card))
                self.app.add_console_message(f"❌ Failed to create {name}: {error_msg or 'Unknown error'}")
                
        except Exception as e:
            print(f"[InstanceOps] ❌ Error handling completion: {e}")

    def _add_new_instance_card(self, name, loading_card):
        """Add new instance card"""
        try:
            # Get fresh instance data
            self.app.instance_manager.load_real_instances()
            instances = self.app.instance_manager.get_instances()
            
            # Find our new instance
            new_instance = None
            for instance in instances:
                instance_name = instance["name"]
                if (instance_name == name or name in instance_name or 
                    instance_name in name or instance_name.lower() == name.lower()):
                    new_instance = instance
                    break
            
            if not new_instance:
                print(f"[InstanceOps] ❌ Could not find new instance {name}")
                self._remove_loading_card(loading_card)
                return
            
            # Remove loading card
            if loading_card and loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
            
            # Create real card
            real_card = self.app.ui_manager.create_instance_card(
                new_instance["name"], new_instance["status"]
            )
            
            if real_card:
                self.app.instance_cards.append(real_card)
                
                # Position card
                card_index = len(self.app.instance_cards) - 1
                row = card_index // 2
                col = card_index % 2
                real_card.grid(row=row, column=col, padx=4, pady=2, 
                             sticky="e" if col == 0 else "w", in_=self.app.instances_container)
                
                # Add highlight animation
                self._add_highlight_animation(real_card)
                
                # Update UI
                self._update_after_add(new_instance["name"])
                
                # Refresh modules
                if hasattr(self.app, 'module_manager'):
                    self.app.module_manager.refresh_modules()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error adding new card: {e}")
            if loading_card:
                self._remove_loading_card(loading_card)

    def _add_highlight_animation(self, card):
        """Add highlight animation"""
        try:
            if hasattr(card, 'main_container'):
                original_bg = card.main_container.cget("bg")
                
                def animate_step(step=0):
                    if not card.winfo_exists():
                        return
                    if step == 0:
                        card.main_container.configure(bg="#00ff88")
                        card.after(400, lambda: animate_step(1))
                    elif step == 1:
                        card.main_container.configure(bg="#33ff99")
                        card.after(200, lambda: animate_step(2))
                    elif step == 2:
                        card.main_container.configure(bg=original_bg)
                
                animate_step()
        except Exception as e:
            print(f"[InstanceOps] Animation error: {e}")

    def _update_after_add(self, name):
        """Update UI after adding card"""
        try:
            # Configure grid
            if self.app.instances_container and self.app.instance_cards:
                self.app.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.app.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Update scroll region and counter
            if hasattr(self.app.ui_manager, 'update_scroll_region'):
                self.app.ui_manager.update_scroll_region()
                self.app.after(100, self.app.ui_manager.scroll_to_bottom)
            
            self._update_counter()
            self.app.add_console_message(f"✅ Successfully created MEmu instance: {name}")
            self.app.update_idletasks()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error updating UI: {e}")

    def _remove_loading_card(self, loading_card):
        """Remove loading card safely"""
        try:
            if loading_card and loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
                self._update_counter()
                if hasattr(self.app.ui_manager, 'update_scroll_region'):
                    self.app.ui_manager.update_scroll_region()
        except Exception as e:
            print(f"[InstanceOps] ❌ Error removing loading card: {e}")

    def start_instance(self, name):
        """Start instance with module integration"""
        def start_thread():
            try:
                self.app.add_console_message(f"🔄 Starting instance: {name}")
                success = self.app.instance_manager.start_instance(name)
                
                if success:
                    self.app.after(0, lambda: self.app.add_console_message(f"✅ Started: {name}"))
                    
                    # Trigger module auto-startup
                    if hasattr(self.app, 'module_manager') and self.app.module_manager.initialization_complete:
                        self.app.after(0, lambda: self.app.module_manager.trigger_auto_startup_for_instance(name))
                else:
                    self.app.after(0, lambda: self.app.add_console_message(f"❌ Failed to start: {name}"))
                    
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Error starting {name}: {e}"))
        
        threading.Thread(target=start_thread, daemon=True).start()

    def stop_instance(self, name):
        """Stop instance with module cleanup"""
        def stop_thread():
            try:
                self.app.add_console_message(f"🔄 Stopping instance: {name}")
                
                # Clean up modules first
                if hasattr(self.app, 'module_manager'):
                    self.app.module_manager.cleanup_for_stopped_instance(name)
                
                # Stop the instance
                success = self.app.instance_manager.stop_instance(name)
                message = f"✅ Stopped: {name}" if success else f"❌ Failed to stop: {name}"
                self.app.after(0, lambda: self.app.add_console_message(message))
                
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Error stopping {name}: {e}"))
        
        threading.Thread(target=stop_thread, daemon=True).start()

    def delete_instance_card_with_animation(self, card):
        """Delete instance with animation"""
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete instance '{card.name}'?\n\nThis cannot be undone.")
        if not result:
            return

        try:
            from gui.components.deleting_instance_card import create_deleting_instance_card
            
            # Get card position
            card_index = None
            if card in self.app.instance_cards:
                card_index = self.app.instance_cards.index(card)

            # Create deleting card
            deleting_card = create_deleting_instance_card(self.app.instances_container, card.name)

            # Replace original card
            if card_index is not None:
                self.app.instance_cards[card_index] = deleting_card
                row = card_index // 2
                col = card_index % 2
                
                card.destroy()
                deleting_card.grid(row=row, column=col, padx=4, pady=2, 
                                 sticky="e" if col == 0 else "w")
            else:
                self.app.instance_cards.append(deleting_card)
                card.destroy()
                self._reposition_all_cards()

            self.app.update_idletasks()
            self.app.add_console_message(f"🗑 Deleting MEmu instance: {card.name}")

            # Start deletion in background
            def deletion_thread():
                try:
                    # Clean up modules first
                    if hasattr(self.app, 'module_manager'):
                        self.app.module_manager.cleanup_for_stopped_instance(card.name)
                    
                    # Delete the instance
                    success = self.app.instance_manager.delete_instance(card.name)
                    self.app.after(0, lambda: self._handle_deletion_completion(
                        card.name, deleting_card, success
                    ))
                except Exception as e:
                    self.app.after(0, lambda: self._handle_deletion_completion(
                        card.name, deleting_card, False, str(e)
                    ))
            
            threading.Thread(target=deletion_thread, daemon=True, name=f"Delete-{card.name}").start()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error in delete operation: {e}")

    def _handle_deletion_completion(self, name, deleting_card, success, error_msg=None):
        """Handle deletion completion"""
        try:
            if success:
                deleting_card.show_success()
                self.app.after(2000, lambda: self._finalize_deletion(name, deleting_card))
            else:
                deleting_card.show_error(error_msg or "Deletion failed")
                self.app.add_console_message(f"❌ Failed to delete {name}: {error_msg}")
                self.app.after(5000, lambda: self._cleanup_deleting_card(deleting_card))
        except Exception as e:
            print(f"[InstanceOps] ❌ Error handling deletion completion: {e}")

    def _finalize_deletion(self, name, deleting_card):
        """Finalize deletion"""
        try:
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)
                deleting_card.destroy()
            
            self._reposition_all_cards()
            self._update_counter()
            
            # Refresh modules
            if hasattr(self.app, 'module_manager'):
                self.app.module_manager.refresh_modules()
            
            self.app.add_console_message(f"✅ Successfully deleted instance: {name}")
        except Exception as e:
            print(f"[InstanceOps] ❌ Error finalizing deletion: {e}")

    def _cleanup_deleting_card(self, deleting_card):
        """Cleanup deleting card"""
        try:
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)
            deleting_card.destroy()
            self._reposition_all_cards()
            self._update_counter()
        except:
            pass

    def _reposition_all_cards(self):
        """Reposition all cards"""
        try:
            for i, card in enumerate(self.app.instance_cards):
                if card and card.winfo_exists():
                    row = i // 2
                    col = i % 2
                    card.grid(row=row, column=col, padx=4, pady=2, 
                            sticky="e" if col == 0 else "w", 
                            in_=self.app.instances_container)
        except Exception as e:
            print(f"[InstanceOps] ❌ Error repositioning cards: {e}")

    def _update_counter(self):
        """Update instance counter"""
        try:
            if hasattr(self.app, 'instances_header'):
                count = len(self.app.instance_cards)
                self.app.instances_header.configure(text=f"Instances ({count})")
        except Exception as e:
            print(f"[InstanceOps] ❌ Error updating counter: {e}")

    def refresh_instances(self):
        """Refresh instances"""
        self.app.add_console_message("Refreshing instances...")
        
        def refresh_thread():
            try:
                self.app.instance_manager.refresh_instances()
                self.app.after(0, lambda: self.app.load_instances())
                
                # Refresh modules
                if hasattr(self.app, 'module_manager'):
                    self.app.after(0, lambda: self.app.module_manager.refresh_modules())
                
                self.app.after(0, lambda: self.app.add_console_message("✅ Refresh complete"))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Refresh error: {e}"))
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def toggle_select_all(self):
        """Toggle selection of all instances"""
        if not self.app.instance_cards:
            return

        all_selected = all(getattr(card, 'selected', False) for card in self.app.instance_cards 
                          if hasattr(card, 'selected'))

        for card in self.app.instance_cards:
            if hasattr(card, 'toggle_checkbox') and hasattr(card, 'selected'):
                if all_selected and card.selected:
                    card.toggle_checkbox()
                elif not all_selected and not card.selected:
                    card.toggle_checkbox()

        message = "All instances unselected" if all_selected else "All instances selected"
        self.app.add_console_message(message)

    def start_selected_instances(self):
        """Start selected instances"""
        selected = [card for card in self.app.instance_cards 
                   if hasattr(card, 'selected') and hasattr(card, 'name') and card.selected]
        
        if not selected:
            self.app.add_console_message("No instances selected")
            return
        
        self.app.add_console_message(f"🚀 Starting {len(selected)} selected instances...")
        
        for i, card in enumerate(selected):
            # Stagger starts
            delay = i * 2000
            self.app.after(delay, lambda name=card.name: self.start_instance(name))

    def stop_selected_instances(self):
        """Stop selected instances"""
        selected = [card for card in self.app.instance_cards 
                   if hasattr(card, 'selected') and hasattr(card, 'name') and card.selected]
        
        if not selected:
            self.app.add_console_message("No instances selected")
            return
        
        self.app.add_console_message(f"⏹ Stopping {len(selected)} selected instances...")
        
        for card in selected:
            self.stop_instance(card.name)

    # Legacy compatibility
    def create_instance(self):
        """Create instance with dialog"""
        name = simpledialog.askstring("Create Instance", "Enter instance name:")
        if name:
            self.create_instance_with_name(name)

    def clone_selected_instance(self):
        """Clone selected instance (placeholder)"""
        self.app.add_console_message("Clone functionality coming soon...")

    def delete_instance_card_with_loading(self, card):
        """Legacy method name"""
        self.delete_instance_card_with_animation(card)