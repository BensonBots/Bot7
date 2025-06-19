"""
BENSON v2.0 - Complete Instance Operations with Fixed Loading Card Replacement
Better create instance dialog with proper naming and error handling
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time


class InstanceOperations:
    """Complete instance operations with fixed loading card system"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """Create instance with loading card animation instead of modal"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()
        
        # Import the loading card component
        from gui.components.loading_instance_card import create_loading_instance_card
        
        # Create and show loading card immediately
        loading_card = create_loading_instance_card(self.app.instances_container, name)
        
        # Position the loading card (add to the grid)
        current_cards = len(self.app.instance_cards)
        row = current_cards // 2
        col = current_cards % 2
        loading_card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w")
        
        # Add to instance cards list temporarily
        self.app.instance_cards.append(loading_card)
        
        # Update UI immediately
        self.app.update_idletasks()
        
        # Log start
        self.app.add_console_message(f"🔄 Creating MEmu instance: {name}")

        def create_worker():
            success = False
            error_msg = None
            
            try:
                # Call the actual creation method
                success = self.app.instance_manager.create_instance_with_name(name)
                
            except Exception as e:
                error_msg = str(e)
                success = False
            
            # Schedule completion on main thread
            self.app.after(0, lambda: self._complete_create_with_loading_card(
                name, loading_card, success, error_msg
            ))

        # Start creation in background
        threading.Thread(target=create_worker, daemon=True).start()

    def _complete_create_with_loading_card(self, name, loading_card, success, error=None):
        """FIXED: Complete instance creation with proper card replacement"""
        try:
            if success:
                # Show success animation
                loading_card.show_success()
                
                # Wait a moment, then replace with real card
                def replace_with_real_card():
                    try:
                        print(f"[InstanceOps] Replacing loading card for {name} with real card")
                        
                        # Get the loading card's position before removing it
                        loading_row = None
                        loading_col = None
                        loading_index = None
                        
                        if loading_card in self.app.instance_cards:
                            loading_index = self.app.instance_cards.index(loading_card)
                            loading_row = loading_index // 2
                            loading_col = loading_index % 2
                            
                            # Remove loading card from list
                            self.app.instance_cards.remove(loading_card)
                        
                        # Refresh instances to get the new one
                        refresh_worker_thread = threading.Thread(
                            target=self._refresh_and_replace_card, 
                            args=(name, loading_card, loading_index, loading_row, loading_col),
                            daemon=True
                        )
                        refresh_worker_thread.start()
                        
                    except Exception as e:
                        print(f"[InstanceOps] Error in replace_with_real_card: {e}")
                        # Still destroy the loading card
                        try:
                            loading_card.destroy()
                        except:
                            pass
                
                # Replace after success animation
                self.app.after(1500, replace_with_real_card)
                
            else:
                # Show error animation
                error_message = error or "Unknown error occurred"
                loading_card.show_error(error_message)
                
                # Remove from list after error is shown
                def remove_failed_card():
                    try:
                        if loading_card in self.app.instance_cards:
                            self.app.instance_cards.remove(loading_card)
                        # Card will auto-destroy itself after fade animation
                    except Exception as e:
                        print(f"[InstanceOps] Error removing failed card: {e}")
                
                self.app.after(100, remove_failed_card)
                
                # Log error
                error_msg = f"Failed to create instance: {name}"
                if error:
                    error_msg += f" - {error}"
                self.app.add_console_message(f"❌ {error_msg}")
                
        except Exception as e:
            print(f"[InstanceOps] Error in completion handler: {e}")
            # Cleanup loading card if something goes wrong
            try:
                if loading_card in self.app.instance_cards:
                    self.app.instance_cards.remove(loading_card)
                loading_card.destroy()
            except:
                pass

    def _refresh_and_replace_card(self, name, loading_card, loading_index, loading_row, loading_col):
        """FIXED: Refresh instances and replace loading card in background"""
        try:
            print(f"[InstanceOps] Refreshing instances to find new instance: {name}")
            
            # Refresh instance manager data
            self.app.instance_manager.load_real_instances()
            
            # Find the new instance
            new_instance = self.app.instance_manager.get_instance(name)
            if not new_instance:
                print(f"[InstanceOps] Could not find new instance {name} after refresh")
                self.app.after(0, lambda: self._cleanup_failed_replace(loading_card, name))
                return
            
            print(f"[InstanceOps] Found new instance: {new_instance}")
            
            # Schedule UI updates on main thread
            self.app.after(0, lambda: self._create_real_card(
                name, new_instance["status"], loading_card, loading_index, loading_row, loading_col
            ))
            
        except Exception as e:
            print(f"[InstanceOps] Error in refresh_and_replace_card: {e}")
            self.app.after(0, lambda: self._cleanup_failed_replace(loading_card, name))

    def _create_real_card(self, name, status, loading_card, loading_index, loading_row, loading_col):
        """Create the real instance card to replace loading card"""
        try:
            print(f"[InstanceOps] Creating real card for {name} with status {status}")
            
            # Create the real instance card
            real_card = self.app.ui_manager.create_instance_card(name, status)
            
            if real_card:
                # Insert the real card at the same position as the loading card
                if loading_index is not None:
                    self.app.instance_cards.insert(loading_index, real_card)
                else:
                    self.app.instance_cards.append(real_card)
                
                # FIXED: Position the new card and reposition all others
                self.app.after(50, lambda: self._finalize_card_replacement(loading_card, real_card, name))
            else:
                print(f"[InstanceOps] Failed to create real card for {name}")
                self._cleanup_failed_replace(loading_card, name)
                
        except Exception as e:
            print(f"[InstanceOps] Error creating real card for {name}: {e}")
            self._cleanup_failed_replace(loading_card, name)

    def _finalize_card_replacement(self, loading_card, real_card, name):
        """Finalize the card replacement process"""
        try:
            # Destroy the loading card
            loading_card.destroy()
            
            # FIXED: Reposition ALL cards to ensure proper layout
            self.app.reposition_all_cards()
            
            # Update counter
            self.app.force_counter_update()
            
            # Log success
            self.app.add_console_message(f"✅ Successfully created MEmu instance: {name}")
            
            print(f"[InstanceOps] Successfully replaced loading card with real card for {name}")
            
        except Exception as e:
            print(f"[InstanceOps] Error finalizing card replacement: {e}")

    def _cleanup_failed_replace(self, loading_card, name):
        """Cleanup if card replacement fails"""
        try:
            loading_card.destroy()
            self.app.add_console_message(f"❌ Failed to create real card for {name}")
        except:
            pass

    def create_instance(self):
        """Legacy create instance method (fallback)"""
        name = simpledialog.askstring("Create MEmu Instance", 
                                     "Enter MEmu instance name:\n(e.g., MyGame, Instance1, etc.)")

        if name:
            self.create_instance_with_name(name)
        else:
            self.app.add_console_message("Instance creation cancelled")

    def clone_selected_instance(self):
        """Clone the selected instance"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instance selected for cloning")
            return

        self.app.add_console_message("Clone functionality coming soon...")

    def start_selected_instances(self):
        """Start selected instances (non-blocking)"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Starting {len(selected_cards)} selected instances...")
        
        def start_worker():
            for card in selected_cards:
                # Add small delay between starts to prevent system overload
                threading.Thread(target=lambda name=card.name: self.start_instance(name), daemon=True).start()
                time.sleep(0.5)  # Stagger starts
        
        threading.Thread(target=start_worker, daemon=True).start()

    def stop_selected_instances(self):
        """Stop selected instances (non-blocking)"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Stopping {len(selected_cards)} selected instances...")
        
        def stop_worker():
            for card in selected_cards:
                # Add small delay between stops
                threading.Thread(target=lambda name=card.name: self.stop_instance(name), daemon=True).start()
                time.sleep(0.3)  # Stagger stops
        
        threading.Thread(target=stop_worker, daemon=True).start()

    def delete_selected_instances_with_loading(self):
        """Delete selected instances with loading screen (non-blocking)"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected for deletion")
            return

        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete {len(selected_cards)} selected instances?\n\nThis cannot be undone.")
        if not result:
            return

        # Show loading overlay
        from gui.components.loading_overlay import LoadingOverlay
        loading = LoadingOverlay(self.app)
        loading.update_status(f"Deleting {len(selected_cards)} instances...")

        def delete_worker():
            success_count = 0
            error_msg = None
            
            try:
                for i, card in enumerate(selected_cards):
                    self.app.after(0, lambda msg=f"Deleting {card.name} ({i+1}/{len(selected_cards)})...": loading.update_status(msg))

                    success = self.app.instance_manager.delete_instance(card.name)
                    if success:
                        success_count += 1

                    time.sleep(0.3)

            except Exception as e:
                error_msg = str(e)
            finally:
                self.app.after(0, lambda s=success_count, err=error_msg: self._complete_bulk_delete(selected_cards, loading, s, err))

        threading.Thread(target=delete_worker, daemon=True).start()

    def _complete_bulk_delete(self, deleted_cards, loading, success_count, error=None):
        """Complete bulk deletion"""
        loading.close()

        # Remove cards from UI
        for card in deleted_cards:
            if card in self.app.instance_cards:
                self.app.instance_cards.remove(card)
            if card in self.app.selected_cards:
                self.app.selected_cards.remove(card)
            card.destroy()

        # Refresh UI
        self.app.load_instances()
        self.app.force_counter_update()

        if success_count > 0:
            self.app.add_console_message(f"✓ Successfully deleted {success_count} instances")

        if error:
            self.app.add_console_message(f"✗ Error during deletion: {error}")

    def delete_instance_card_with_loading(self, card):
        """Delete a single instance card with loading (non-blocking)"""
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete instance '{card.name}'?\n\nThis cannot be undone.")

        if not result:
            return

        from gui.components.loading_overlay import LoadingOverlay
        loading = LoadingOverlay(self.app)
        loading.update_status("Deleting instance...")

        def delete_worker():
            error_msg = None
            success = False
            
            try:
                success = self.app.instance_manager.delete_instance(card.name)
            except Exception as e:
                error_msg = str(e)
                success = False
            finally:
                self.app.after(0, lambda s=success, err=error_msg: self._complete_single_delete(card, loading, s, err))

        threading.Thread(target=delete_worker, daemon=True).start()

    def _complete_single_delete(self, card, loading, success, error=None):
        """Complete single instance deletion"""
        loading.close()

        if success:
            if card in self.app.instance_cards:
                self.app.instance_cards.remove(card)
            if card in self.app.selected_cards:
                self.app.selected_cards.remove(card)
            card.destroy()

            self.app.load_instances()
            self.app.force_counter_update()
            self.app.add_console_message(f"✓ Successfully deleted instance: {card.name}")
        else:
            error_msg = f"Failed to delete instance: {card.name}"
            if error:
                error_msg += f"\nError: {error}"
            self.app.add_console_message(f"✗ {error_msg}")
            messagebox.showerror("Delete Failed", error_msg)

    def start_instance(self, name):
        """Start an instance (non-blocking)"""
        def start_worker():
            try:
                success = self.app.instance_manager.start_instance(name)
                if success:
                    self.app.after(0, lambda: self.app.add_console_message(f"Starting instance: {name}"))
                else:
                    self.app.after(0, lambda: self.app.add_console_message(f"Failed to start instance: {name}"))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"Error starting {name}: {str(e)}"))

        # Run in background thread to avoid blocking UI
        threading.Thread(target=start_worker, daemon=True).start()

    def stop_instance(self, name):
        """Stop an instance (non-blocking)"""
        def stop_worker():
            try:
                success = self.app.instance_manager.stop_instance(name)
                if success:
                    self.app.after(0, lambda: self.app.add_console_message(f"Stopping instance: {name}"))
                else:
                    self.app.after(0, lambda: self.app.add_console_message(f"Failed to stop instance: {name}"))
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"Error stopping {name}: {str(e)}"))

        # Run in background thread to avoid blocking UI
        threading.Thread(target=stop_worker, daemon=True).start()

    def toggle_select_all(self):
        """Toggle selection of all instances"""
        if not self.app.instance_cards:
            return

        all_selected = all(card.selected for card in self.app.instance_cards)

        if all_selected:
            for card in self.app.instance_cards:
                if card.selected:
                    card.toggle_checkbox()
            self.app.add_console_message("All instances unselected")
        else:
            for card in self.app.instance_cards:
                if not card.selected:
                    card.toggle_checkbox()
            self.app.add_console_message("All instances selected")

    def select_all_instances(self):
        """Select all instances"""
        for card in self.app.instance_cards:
            if not card.selected:
                card.toggle_checkbox()
        self.app.add_console_message("All instances selected")

    def refresh_instances(self):
        """Refresh all instances (non-blocking)"""
        self.app.add_console_message("Refreshing all instances from MEmu...")

        def delayed_refresh():
            try:
                time.sleep(0.5)
                self.app.instance_manager.refresh_instances()
                
                instance_count = len(self.app.instance_manager.get_instances())
                
                self.app.after(0, lambda: [
                    self.app.load_instances(),
                    self.app.force_counter_update(),
                    self.app.add_console_message(f"Refreshed {instance_count} instances from MEmu")
                ])
            except Exception as e:
                self.app.after(0, lambda: self.app.add_console_message(f"Refresh error: {str(e)}"))

        threading.Thread(target=delayed_refresh, daemon=True).start()