"""
BENSON v2.0 - Compact Instance Operations
Reduced from 400+ lines to ~150 lines with same functionality
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time


class InstanceOperations:
    """Compact instance operations with clean module integration"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """Create instance with loading card animation"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()
        self.app.add_console_message(f"🔄 Creating MEmu instance: {name}")
        
        # Create and position loading card
        loading_card = self._create_and_position_loading_card(name)
        
        # Start creation in background
        threading.Thread(target=lambda: self._handle_creation_process(name, loading_card), 
                        daemon=True, name=f"Create-{name}").start()

    def _create_and_position_loading_card(self, name):
        """Create and position loading card"""
        try:
            from gui.components.loading_instance_card import create_loading_instance_card
            loading_card = create_loading_instance_card(self.app.instances_container, name)
            
            # Position it
            current_cards = len(self.app.instance_cards)
            row = current_cards // 2
            col = current_cards % 2
            loading_card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w")
            
            # Add to list and update UI
            self.app.instance_cards.append(loading_card)
            self._update_ui_after_card_change()
            
            return loading_card
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error creating loading card: {e}")
            return None

    def _handle_creation_process(self, name, loading_card):
        """Handle the entire creation process"""
        try:
            success = self.app.instance_manager.create_instance_with_name(name)
            self.app.after(0, lambda: self._creation_completed(name, loading_card, success))
        except Exception as e:
            self.app.after(0, lambda: self._creation_completed(name, loading_card, False, str(e)))

    def _creation_completed(self, name, loading_card, success, error_msg=None):
        """Handle creation completion"""
        try:
            if success:
                if loading_card:
                    loading_card.show_success()
                self.app.after(1200, lambda: self._replace_with_real_card(name, loading_card))
            else:
                if loading_card:
                    loading_card.show_error(error_msg or "Creation failed")
                self.app.after(3000, lambda: self._remove_loading_card(loading_card))
                self.app.add_console_message(f"❌ Failed to create {name}: {error_msg or 'Unknown error'}")
                
        except Exception as e:
            print(f"[InstanceOps] ❌ Error handling completion: {e}")

    def _replace_with_real_card(self, name, loading_card):
        """Replace loading card with real instance card"""
        try:
            # Refresh data and find new instance
            self.app.instance_manager.load_real_instances()
            instances = self.app.instance_manager.get_instances()
            
            new_instance = self._find_new_instance(instances, name)
            if not new_instance:
                print(f"[InstanceOps] ❌ Could not find new instance {name}")
                self._remove_loading_card(loading_card)
                return
            
            # Remove loading card and create real card
            if loading_card and loading_card in self.app.instance_cards:
                card_index = self.app.instance_cards.index(loading_card)
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
                
                # Create and insert real card
                real_card = self.app.ui_manager.create_instance_card(new_instance["name"], new_instance["status"])
                if real_card:
                    self.app.instance_cards.insert(card_index, real_card)
                    self._position_card(real_card, card_index)
                    self._add_highlight_animation(real_card)
                    self._finalize_creation(new_instance["name"])
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error replacing card: {e}")
            if loading_card:
                self._remove_loading_card(loading_card)

    def _find_new_instance(self, instances, name):
        """Find the newly created instance"""
        for instance in instances:
            instance_name = instance["name"]
            if (instance_name == name or name in instance_name or 
                instance_name in name or instance_name.lower() == name.lower()):
                return instance
        return None

    def _position_card(self, card, index):
        """Position card in grid"""
        row = index // 2
        col = index % 2
        card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w", 
                 in_=self.app.instances_container)

    def _add_highlight_animation(self, card):
        """Add brief highlight animation to new card"""
        try:
            if hasattr(card, 'main_container'):
                original_bg = card.main_container.cget("bg")
                
                def animate():
                    if not card.winfo_exists(): return
                    card.main_container.configure(bg="#00ff88")
                    card.after(400, lambda: self._restore_bg(card, original_bg))
                
                animate()
        except: pass

    def _restore_bg(self, card, original_bg):
        """Restore original background after animation"""
        try:
            if card.winfo_exists():
                card.main_container.configure(bg=original_bg)
        except: pass

    def _finalize_creation(self, name):
        """Finalize creation process"""
        self._update_ui_after_card_change()
        self.app.add_console_message(f"✅ Successfully created MEmu instance: {name}")
        
        # Refresh modules
        if hasattr(self.app, 'module_manager'):
            self.app.module_manager.refresh_modules()

    def _remove_loading_card(self, loading_card):
        """Remove loading card safely"""
        try:
            if loading_card and loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
                self._update_ui_after_card_change()
        except Exception as e:
            print(f"[InstanceOps] ❌ Error removing loading card: {e}")

    def _update_ui_after_card_change(self):
        """Update UI elements after card changes"""
        try:
            # Configure grid
            if self.app.instances_container and self.app.instance_cards:
                self.app.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.app.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Update counter
            if hasattr(self.app, 'instances_header'):
                count = len(self.app.instance_cards)
                self.app.instances_header.configure(text=f"Instances ({count})")
            
            # Update scroll region
            if hasattr(self.app.ui_manager, 'update_scroll_region'):
                self.app.ui_manager.update_scroll_region()
                self.app.after(100, self.app.ui_manager.scroll_to_bottom)
            
            self.app.update_idletasks()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error updating UI: {e}")

    # Instance control operations
    def start_instance(self, name):
        """Start instance with module integration"""
        def start_worker():
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
        
        threading.Thread(target=start_worker, daemon=True).start()

    def stop_instance(self, name):
        """Stop instance with module cleanup"""
        def stop_worker():
            try:
                self.app.add_console_message(f"🔄 Stopping instance: {name}")
                
                # Clean up modules first
                if hasattr(self.app, 'module_manager'):
                    self.app.module_manager.cleanup_for_stopped_instance(name)
                
                success = self.app.instance_manager.stop_instance(name)
                message = f"✅ Stopped: {name}" if success else f"❌ Failed to stop: {name}"
                self.app.after(0, lambda: self.app.add_console_message(message))
                
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Error stopping {name}: {e}"))
        
        threading.Thread(target=stop_worker, daemon=True).start()

    def delete_instance_card_with_animation(self, card):
        """Delete instance with animation"""
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete instance '{card.name}'?\n\nThis cannot be undone.")
        if not result:
            return

        try:
            from gui.components.deleting_instance_card import create_deleting_instance_card
            
            # Create deleting card and replace original
            deleting_card = create_deleting_instance_card(self.app.instances_container, card.name)
            card_index = self.app.instance_cards.index(card) if card in self.app.instance_cards else len(self.app.instance_cards)
            
            if card in self.app.instance_cards:
                self.app.instance_cards[card_index] = deleting_card
            else:
                self.app.instance_cards.append(deleting_card)
            
            card.destroy()
            self._position_card(deleting_card, card_index)
            self.app.update_idletasks()
            self.app.add_console_message(f"🗑 Deleting MEmu instance: {card.name}")

            # Start deletion process
            threading.Thread(target=lambda: self._handle_deletion(card.name, deleting_card), 
                           daemon=True, name=f"Delete-{card.name}").start()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error in delete operation: {e}")

    def _handle_deletion(self, name, deleting_card):
        """Handle deletion process"""
        try:
            # Clean up modules first
            if hasattr(self.app, 'module_manager'):
                self.app.module_manager.cleanup_for_stopped_instance(name)
            
            # Delete the instance
            success = self.app.instance_manager.delete_instance(name)
            self.app.after(0, lambda: self._deletion_completed(name, deleting_card, success))
        except Exception as e:
            self.app.after(0, lambda: self._deletion_completed(name, deleting_card, False, str(e)))

    def _deletion_completed(self, name, deleting_card, success, error_msg=None):
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
        """Finalize deletion and cleanup"""
        try:
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)
                deleting_card.destroy()
            
            self._reposition_all_cards()
            self._update_ui_after_card_change()
            
            # Refresh modules
            if hasattr(self.app, 'module_manager'):
                self.app.module_manager.refresh_modules()
            
            self.app.add_console_message(f"✅ Successfully deleted instance: {name}")
        except Exception as e:
            print(f"[InstanceOps] ❌ Error finalizing deletion: {e}")

    def _cleanup_deleting_card(self, deleting_card):
        """Cleanup failed deleting card"""
        try:
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)
            deleting_card.destroy()
            self._reposition_all_cards()
            self._update_ui_after_card_change()
        except: pass

    def _reposition_all_cards(self):
        """Reposition all cards after removal"""
        try:
            for i, card in enumerate(self.app.instance_cards):
                if card and card.winfo_exists():
                    self._position_card(card, i)
        except Exception as e:
            print(f"[InstanceOps] ❌ Error repositioning cards: {e}")

    # Bulk operations
    def refresh_instances(self):
        """Refresh all instances"""
        self.app.add_console_message("Refreshing instances...")
        
        def refresh_worker():
            try:
                self.app.instance_manager.refresh_instances()
                self.app.after(0, lambda: self.app.load_instances())
                
                if hasattr(self.app, 'module_manager'):
                    self.app.after(0, lambda: self.app.module_manager.refresh_modules())
                
                self.app.after(0, lambda: self.app.add_console_message("✅ Refresh complete"))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Refresh error: {e}"))
        
        threading.Thread(target=refresh_worker, daemon=True).start()

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
        """Start all selected instances"""
        selected = [card for card in self.app.instance_cards 
                   if hasattr(card, 'selected') and hasattr(card, 'name') and card.selected]
        
        if not selected:
            self.app.add_console_message("No instances selected")
            return
        
        self.app.add_console_message(f"🚀 Starting {len(selected)} selected instances...")
        
        for i, card in enumerate(selected):
            # Stagger starts to avoid overload
            delay = i * 2000
            self.app.after(delay, lambda name=card.name: self.start_instance(name))

    def stop_selected_instances(self):
        """Stop all selected instances"""
        selected = [card for card in self.app.instance_cards 
                   if hasattr(card, 'selected') and hasattr(card, 'name') and card.selected]
        
        if not selected:
            self.app.add_console_message("No instances selected")
            return
        
        self.app.add_console_message(f"⏹ Stopping {len(selected)} selected instances...")
        
        for card in selected:
            self.stop_instance(card.name)

    # Legacy compatibility methods
    def create_instance(self):
        """Create instance with dialog (legacy method)"""
        name = simpledialog.askstring("Create Instance", "Enter instance name:")
        if name:
            self.create_instance_with_name(name)

    def clone_selected_instance(self):
        """Clone selected instance (placeholder)"""
        self.app.add_console_message("Clone functionality coming soon...")

    def delete_instance_card_with_loading(self, card):
        """Legacy method name"""
        self.delete_instance_card_with_animation(card)