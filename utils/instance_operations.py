"""
BENSON v2.0 - FIXED Instance Operations
Fixed creation completion handling - simple card addition only
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time


class InstanceOperations:
    """Fixed instance operations with simple card addition"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """Create instance with simple card addition"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()
        
        # Log the start
        self.app.add_console_message(f"🔄 Creating MEmu instance: {name}")
        
        # Create loading card immediately
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
            
            # Update counter immediately
            if hasattr(self.app, 'instances_header'):
                self.app.instances_header.configure(text=f"Instances ({len(self.app.instance_cards)})")
            
            # Update UI immediately
            self.app.update_idletasks()
            
            # Update scroll region
            if hasattr(self.app.ui_manager, 'update_scroll_region'):
                self.app.ui_manager.update_scroll_region()
                self.app.after(100, self.app.ui_manager.scroll_to_bottom)
            
            print(f"[InstanceOps] ✅ Loading card created for {name}")
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error creating loading card: {e}")
            loading_card = None

        # Start creation in background
        def creation_thread():
            """Background creation thread"""
            success = False
            error_msg = None
            
            try:
                print(f"[InstanceOps] 🔄 Starting background creation for {name}")
                
                # This is the slow part - runs in background
                success = self.app.instance_manager.create_instance_with_name(name)
                
                print(f"[InstanceOps] ✅ Background creation result: {success}")
                
            except Exception as e:
                print(f"[InstanceOps] ❌ Background creation error: {e}")
                error_msg = str(e)
                success = False
            
            # Schedule completion on main thread
            self.app.after(0, lambda: self._handle_creation_completion(
                name, loading_card, success, error_msg
            ))
        
        # Start the background thread
        thread = threading.Thread(target=creation_thread, daemon=True, name=f"Create-{name}")
        thread.start()
        
        print(f"[InstanceOps] 🚀 Creation thread started for {name}")

    def _handle_creation_completion(self, name, loading_card, success, error_msg):
        """Handle completion with simple card addition - NO REFRESH"""
        try:
            print(f"[InstanceOps] 🎯 Handling completion for {name}, success: {success}")
            
            if success:
                # Show success on loading card
                if loading_card:
                    loading_card.show_success()
                    print(f"[InstanceOps] ✅ Showing success for {name}")
                
                # Wait for success animation, then add new card
                self.app.after(1200, lambda: self._add_new_instance_card_simple(name, loading_card))
                
            else:
                # Show error
                if loading_card:
                    error_message = error_msg or "Creation failed"
                    loading_card.show_error(error_message)
                
                # Remove loading card after error
                self.app.after(3000, lambda: self._remove_loading_card(loading_card))
                
                # Log error
                self.app.add_console_message(f"❌ Failed to create {name}: {error_msg or 'Unknown error'}")
                
        except Exception as e:
            print(f"[InstanceOps] ❌ Error handling completion: {e}")

    def _add_new_instance_card_simple(self, name, loading_card):
        """Simply add the new instance card - SIMPLE VERSION"""
        try:
            print(f"[InstanceOps] 🆕 Adding new card for {name} - SIMPLE METHOD")
            
            # Get fresh instance data (minimal refresh)
            print(f"[InstanceOps] 📊 Getting fresh data for {name}")
            self.app.instance_manager.load_real_instances()
            instances = self.app.instance_manager.get_instances()
            
            # Find our new instance
            new_instance = None
            for instance in instances:
                instance_name = instance["name"]
                # Check for exact match or partial match (since MEmu renames)
                if (instance_name == name or 
                    name in instance_name or 
                    instance_name in name or
                    instance_name.lower() == name.lower()):
                    new_instance = instance
                    print(f"[InstanceOps] 🎯 Found new instance: {instance_name}")
                    break
            
            if not new_instance:
                print(f"[InstanceOps] ❌ Could not find new instance {name}")
                self._remove_loading_card(loading_card)
                return
            
            # Remove loading card first
            if loading_card and loading_card in self.app.instance_cards:
                print(f"[InstanceOps] 🗑️ Removing loading card for {name}")
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
            
            # Create the real card
            print(f"[InstanceOps] 🏗️ Creating real card for {new_instance['name']}")
            real_card = self.app.ui_manager.create_instance_card(
                new_instance["name"], 
                new_instance["status"]
            )
            
            if not real_card:
                print("[InstanceOps] ❌ Failed to create real card")
                return
            
            # Add to the end of the list
            self.app.instance_cards.append(real_card)
            
            # Position the card at the end
            card_index = len(self.app.instance_cards) - 1
            row = card_index // 2
            col = card_index % 2
            
            print(f"[InstanceOps] 📍 Positioning card at row {row}, col {col}")
            real_card.grid(row=row, column=col, padx=4, pady=2, 
                         sticky="e" if col == 0 else "w", 
                         in_=self.app.instances_container)
            
            # Add highlight animation
            self._add_highlight_animation(real_card, new_instance["name"])
            
            # Update UI
            self._update_ui_after_simple_add(new_instance["name"])
            
            print(f"[InstanceOps] ✅ Successfully added new card for {new_instance['name']}")
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error adding new card: {e}")
            import traceback
            traceback.print_exc()
            if loading_card:
                self._remove_loading_card(loading_card)

    def _add_highlight_animation(self, card, name):
        """Add highlight animation to new card"""
        try:
            print(f"[InstanceOps] ✨ Adding highlight animation for {name}")
            
            if not hasattr(card, 'main_container'):
                print(f"[InstanceOps] ⚠️ Card has no main_container for {name}")
                return
            
            # Start with normal color
            original_bg = card.main_container.cget("bg")
            
            # Animation sequence: normal -> green -> normal
            def animate_step(step=0):
                try:
                    if not card.winfo_exists():
                        return
                    
                    if step == 0:
                        # Fade to green
                        card.main_container.configure(bg="#00ff88")
                        card.after(400, lambda: animate_step(1))
                    elif step == 1:
                        # Fade to lighter green
                        card.main_container.configure(bg="#33ff99")
                        card.after(200, lambda: animate_step(2))
                    elif step == 2:
                        # Fade back to original
                        card.main_container.configure(bg=original_bg)
                        print(f"[InstanceOps] ✅ Highlight animation complete for {name}")
                    
                except Exception as e:
                    print(f"[InstanceOps] Animation error: {e}")
            
            # Start animation
            animate_step()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error adding animation: {e}")

    def _update_ui_after_simple_add(self, name):
        """Update UI after simple card addition"""
        try:
            print(f"[InstanceOps] 🔄 Updating UI after adding {name}")
            
            # Configure grid
            if hasattr(self.app, 'instances_container') and self.app.instance_cards:
                self.app.instances_container.grid_columnconfigure(0, weight=1, minsize=580)
                self.app.instances_container.grid_columnconfigure(1, weight=1, minsize=580)
            
            # Update scroll region
            if hasattr(self.app.ui_manager, 'update_scroll_region'):
                self.app.ui_manager.update_scroll_region()
                # Scroll to show new card
                self.app.after(100, self.app.ui_manager.scroll_to_bottom)
            
            # Update counter
            if hasattr(self.app, 'instances_header'):
                count = len(self.app.instance_cards)
                self.app.instances_header.configure(text=f"Instances ({count})")
            
            # Success message
            self.app.add_console_message(f"✅ Successfully created MEmu instance: {name}")
            
            # Force UI update
            self.app.update_idletasks()
            
            print(f"[InstanceOps] ✅ UI update complete for {name}")
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error updating UI: {e}")

    def _remove_loading_card(self, loading_card):
        """Remove loading card safely"""
        try:
            if loading_card and loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
                
                # Update counter
                if hasattr(self.app, 'instances_header'):
                    count = len(self.app.instance_cards)
                    self.app.instances_header.configure(text=f"Instances ({count})")
                    
                # Update scroll region
                if hasattr(self.app.ui_manager, 'update_scroll_region'):
                    self.app.ui_manager.update_scroll_region()
                    
        except Exception as e:
            print(f"[InstanceOps] ❌ Error removing loading card: {e}")

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

    # Delete operations
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
                success = False
                error_msg = None
                
                try:
                    success = self.app.instance_manager.delete_instance(card.name)
                except Exception as e:
                    error_msg = str(e)
                    success = False
                
                self.app.after(0, lambda: self._handle_deletion_completion(
                    card.name, deleting_card, success, error_msg
                ))
            
            threading.Thread(target=deletion_thread, daemon=True, name=f"Delete-{card.name}").start()
            
        except Exception as e:
            print(f"[InstanceOps] ❌ Error in delete operation: {e}")

    def _handle_deletion_completion(self, name, deleting_card, success, error_msg):
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

    def _update_counter(self):
        """Update instance counter"""
        try:
            if hasattr(self.app, 'instances_header'):
                count = len(self.app.instance_cards)
                self.app.instances_header.configure(text=f"Instances ({count})")
        except Exception as e:
            print(f"[InstanceOps] ❌ Error updating counter: {e}")

    # Simple operations
    def start_instance(self, name):
        """Start instance (non-blocking)"""
        def start_thread():
            try:
                success = self.app.instance_manager.start_instance(name)
                message = f"✅ Started: {name}" if success else f"❌ Failed to start: {name}"
                self.app.after(0, lambda: self.app.add_console_message(message))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Error starting {name}: {e}"))
        
        threading.Thread(target=start_thread, daemon=True).start()

    def stop_instance(self, name):
        """Stop instance (non-blocking)"""
        def stop_thread():
            try:
                success = self.app.instance_manager.stop_instance(name)
                message = f"✅ Stopped: {name}" if success else f"❌ Failed to stop: {name}"
                self.app.after(0, lambda: self.app.add_console_message(message))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Error stopping {name}: {e}"))
        
        threading.Thread(target=stop_thread, daemon=True).start()

    def refresh_instances(self):
        """Refresh instances (non-blocking)"""
        self.app.add_console_message("Refreshing instances...")
        
        def refresh_thread():
            try:
                self.app.instance_manager.refresh_instances()
                self.app.after(0, lambda: self.app.load_instances())
                self.app.after(0, lambda: self.app.add_console_message("✅ Refresh complete"))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"❌ Refresh error: {e}"))
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    # Selection operations
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
        
        for card in selected:
            self.start_instance(card.name)

    def stop_selected_instances(self):
        """Stop selected instances"""
        selected = [card for card in self.app.instance_cards 
                   if hasattr(card, 'selected') and hasattr(card, 'name') and card.selected]
        
        if not selected:
            self.app.add_console_message("No instances selected")
            return
        
        for card in selected:
            self.stop_instance(card.name)

    # Legacy compatibility
    def delete_instance_card_with_loading(self, card):
        self.delete_instance_card_with_animation(card)

    def create_instance(self):
        name = simpledialog.askstring("Create Instance", "Enter instance name:")
        if name:
            self.create_instance_with_name(name)

    def clone_selected_instance(self):
        self.app.add_console_message("Clone functionality coming soon...")