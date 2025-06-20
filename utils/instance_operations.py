"""
BENSON v2.0 - FIXED Instance Operations with Non-blocking Card Animations
Fixed freezing issues with proper threading and card-based deletion
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time


class InstanceOperations:
    """FIXED: Instance operations with non-blocking animations"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """FIXED: Create instance with non-blocking loading card"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()

        # Import the FIXED loading card component
        from gui.components.loading_instance_card import create_loading_instance_card

        # Create and show loading card immediately
        loading_card = create_loading_instance_card(self.app.instances_container, name)

        # Position the loading card
        current_cards = len(self.app.instance_cards)
        row = current_cards // 2
        col = current_cards % 2
        loading_card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w")

        # Add to instance cards list temporarily
        self.app.instance_cards.append(loading_card)

        # FIXED: Force immediate UI update without blocking
        self.app.update_idletasks()

        # Log start
        self.app.add_console_message(f"🔄 Creating MEmu instance: {name}")

        def create_worker():
            """FIXED: Non-blocking creation worker"""
            success = False
            error_msg = None

            try:
                # Small delay to let UI render
                time.sleep(0.1)

                # Call the actual creation method
                success = self.app.instance_manager.create_instance_with_name(name)

            except Exception as e:
                error_msg = str(e)
                success = False

            # Schedule completion on main thread - FIXED: Non-blocking
            self.app.after_idle(lambda: self._complete_create_with_loading_card(
                name, loading_card, success, error_msg
            ))

        # Start creation in background - FIXED: Daemon thread
        threading.Thread(target=create_worker, daemon=True).start()

    def _complete_create_with_loading_card(self, name, loading_card, success, error=None):
        """FIXED: Complete instance creation with proper non-blocking card replacement"""
        try:
            if success:
                # Show success animation
                loading_card.show_success()

                # Schedule replacement after success animation - FIXED: Non-blocking timing
                self.app.after(1200, lambda: self._replace_with_real_card(name, loading_card))

            else:
                # Show error animation
                error_message = error or "Unknown error occurred"
                loading_card.show_error(error_message)

                # Remove from list after error - FIXED: Non-blocking cleanup
                self.app.after(100, lambda: self._remove_failed_card(loading_card))

                # Log error
                error_msg = f"Failed to create instance: {name}"
                if error:
                    error_msg += f" - {error}"
                self.app.add_console_message(f"❌ {error_msg}")

        except Exception as e:
            print(f"[InstanceOps] Error in completion handler: {e}")
            # Cleanup loading card if something goes wrong
            self._cleanup_loading_card(loading_card)

    def _replace_with_real_card(self, name, loading_card):
        """FIXED: Replace loading card with real card in non-blocking way"""
        try:
            # Get loading card position before removing it
            loading_index = None
            if loading_card in self.app.instance_cards:
                loading_index = self.app.instance_cards.index(loading_card)
                self.app.instance_cards.remove(loading_card)

            # Start background refresh to get new instance data
            def refresh_worker():
                try:
                    # Refresh instance data
                    self.app.instance_manager.load_real_instances()

                    # Find the new instance
                    new_instance = self.app.instance_manager.get_instance(name)
                    if not new_instance:
                        self.app.after_idle(lambda: self._handle_missing_instance(loading_card, name))
                        return

                    # Schedule real card creation on main thread
                    self.app.after_idle(lambda: self._create_real_card_final(
                        name, new_instance["status"], loading_card, loading_index
                    ))

                except Exception as e:
                    print(f"[InstanceOps] Error in refresh worker: {e}")
                    self.app.after_idle(lambda: self._handle_refresh_error(loading_card, name))

            # Start refresh in background
            threading.Thread(target=refresh_worker, daemon=True).start()

        except Exception as e:
            print(f"[InstanceOps] Error replacing card: {e}")
            self._cleanup_loading_card(loading_card)

    def _create_real_card_final(self, name, status, loading_card, loading_index):
        """FIXED: Final step - create real card and cleanup"""
        try:
            # Create the real instance card
            real_card = self.app.ui_manager.create_instance_card(name, status)

            if real_card:
                # Insert at correct position
                if loading_index is not None:
                    self.app.instance_cards.insert(loading_index, real_card)
                else:
                    self.app.instance_cards.append(real_card)

                # Destroy loading card
                loading_card.destroy()

                # FIXED: Schedule layout update to prevent blocking
                self.app.after_idle(lambda: self._finalize_card_creation(name))
            else:
                self._handle_card_creation_failure(loading_card, name)

        except Exception as e:
            print(f"[InstanceOps] Error creating real card: {e}")
            self._cleanup_loading_card(loading_card)

    def _finalize_card_creation(self, name):
        """FIXED: Finalize card creation with non-blocking updates"""
        try:
            # Reposition all cards
            self.app.reposition_all_cards()

            # Update counter
            self.app.force_counter_update()

            # Log success
            self.app.add_console_message(f"✅ Successfully created MEmu instance: {name}")

        except Exception as e:
            print(f"[InstanceOps] Error finalizing: {e}")

    def _remove_failed_card(self, loading_card):
        """Remove failed loading card from list"""
        try:
            if loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
            # Card will destroy itself after error animation
        except Exception as e:
            print(f"[InstanceOps] Error removing failed card: {e}")

    def _cleanup_loading_card(self, loading_card):
        """Emergency cleanup for loading card"""
        try:
            if loading_card in self.app.instance_cards:
                self.app.instance_cards.remove(loading_card)
            loading_card.destroy()
        except:
            pass

    def _handle_missing_instance(self, loading_card, name):
        """Handle case where new instance is not found"""
        loading_card.show_error("Instance not found after creation")
        self._remove_failed_card(loading_card)
        self.app.add_console_message(f"❌ Could not find new instance {name} after creation")

    def _handle_refresh_error(self, loading_card, name):
        """Handle refresh error during card replacement"""
        loading_card.show_error("Refresh failed")
        self._remove_failed_card(loading_card)
        self.app.add_console_message(f"❌ Failed to refresh instances for {name}")

    def _handle_card_creation_failure(self, loading_card, name):
        """Handle real card creation failure"""
        loading_card.show_error("Card creation failed")
        self._remove_failed_card(loading_card)
        self.app.add_console_message(f"❌ Failed to create real card for {name}")

    def delete_instance_card_with_animation(self, card):
        """FIXED: Delete instance with card animation instead of loading overlay"""
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete instance '{card.name}'?\n\nThis cannot be undone.")
        if not result:
            return

        # Import the deleting card component
        from gui.components.deleting_instance_card import create_deleting_instance_card

        # Get the card's position before replacing it
        card_index = None
        if card in self.app.instance_cards:
            card_index = self.app.instance_cards.index(card)

        # Create deleting card at same position
        deleting_card = create_deleting_instance_card(self.app.instances_container, card.name)

        # Replace the original card with deleting card
        if card_index is not None:
            # Remove original card
            self.app.instance_cards[card_index] = deleting_card
            row = card_index // 2
            col = card_index % 2

            # Destroy original card
            card.destroy()

            # Position deleting card
            deleting_card.grid(row=row, column=col, padx=4, pady=2, 
                             sticky="e" if col == 0 else "w")
        else:
            # Fallback: append and reposition
            self.app.instance_cards.append(deleting_card)
            card.destroy()
            self.app.reposition_all_cards()

        # Update UI
        self.app.update_idletasks()

        # Log start
        self.app.add_console_message(f"🗑 Deleting MEmu instance: {card.name}")

        def delete_worker():
            """FIXED: Non-blocking deletion worker"""
            success = False
            error_msg = None

            try:
                # Small delay for animation to start
                time.sleep(0.2)

                # Perform actual deletion
                success = self.app.instance_manager.delete_instance(card.name)

            except Exception as e:
                error_msg = str(e)
                success = False

            # Schedule completion on main thread
            self.app.after_idle(lambda: self._complete_delete_with_animation(
                card.name, deleting_card, success, error_msg
            ))

        # Start deletion in background
        threading.Thread(target=delete_worker, daemon=True).start()

    def _complete_delete_with_animation(self, name, deleting_card, success, error=None):
        """FIXED: Complete deletion with animation"""
        try:
            if success:
                # Show success animation
                deleting_card.show_success()

                # Schedule cleanup after success animation
                self.app.after(2000, lambda: self._finalize_deletion(name, deleting_card))

            else:
                # Show error animation
                error_message = error or "Deletion failed"
                deleting_card.show_error(error_message)

                # Log error
                self.app.add_console_message(f"❌ Failed to delete {name}: {error_message}")

                # Keep error card visible longer, then remove
                self.app.after(5000, lambda: self._cleanup_deleting_card(deleting_card))

        except Exception as e:
            print(f"[InstanceOps] Error in delete completion: {e}")
            self._cleanup_deleting_card(deleting_card)

    def _finalize_deletion(self, name, deleting_card):
        """FIXED: Finalize deletion and cleanup"""
        try:
            # Remove deleting card from list
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)

            # Card will destroy itself after fade animation

            # Refresh instance list
            self.app.after_idle(lambda: self._refresh_after_deletion(name))

        except Exception as e:
            print(f"[InstanceOps] Error finalizing deletion: {e}")

    def _refresh_after_deletion(self, name):
        """Refresh UI after deletion"""
        try:
            # Reposition remaining cards
            self.app.reposition_all_cards()

            # Update counter
            self.app.force_counter_update()

            # Log success
            self.app.add_console_message(f"✅ Successfully deleted instance: {name}")

        except Exception as e:
            print(f"[InstanceOps] Error refreshing after deletion: {e}")

    def _cleanup_deleting_card(self, deleting_card):
        """Emergency cleanup for deleting card"""
        try:
            if deleting_card in self.app.instance_cards:
                self.app.instance_cards.remove(deleting_card)
            deleting_card.destroy()

            # Reposition cards
            self.app.reposition_all_cards()
            self.app.force_counter_update()

        except:
            pass

    def delete_selected_instances_with_animation(self):
        """FIXED: Delete multiple instances with individual card animations"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected for deletion")
            return

        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete {len(selected_cards)} selected instances?\n\nThis cannot be undone.")
        if not result:
            return

        self.app.add_console_message(f"🗑 Deleting {len(selected_cards)} selected instances...")

        # Delete each card with staggered timing
        for i, card in enumerate(selected_cards):
            # Stagger deletions to prevent overwhelming the system
            delay = i * 200  # 200ms between each deletion start
            self.app.after(delay, lambda c=card: self.delete_instance_card_with_animation(c))

    # Legacy method compatibility
    def delete_instance_card_with_loading(self, card):
        """Legacy method - redirects to animation version"""
        self.delete_instance_card_with_animation(card)

    def delete_selected_instances_with_loading(self):
        """Legacy method - redirects to animation version"""
        self.delete_selected_instances_with_animation()

    # Other methods remain the same but with FIXED threading
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
        """FIXED: Start selected instances (non-blocking)"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Starting {len(selected_cards)} selected instances...")

        def start_worker():
            for i, card in enumerate(selected_cards):
                # Stagger starts to prevent system overload
                time.sleep(i * 0.5)

                # Schedule on main thread
                self.app.after_idle(lambda name=card.name: self._start_instance_async(name))

        threading.Thread(target=start_worker, daemon=True).start()

    def stop_selected_instances(self):
        """FIXED: Stop selected instances (non-blocking)"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Stopping {len(selected_cards)} selected instances...")

        def stop_worker():
            for i, card in enumerate(selected_cards):
                # Stagger stops
                time.sleep(i * 0.3)

                # Schedule on main thread
                self.app.after_idle(lambda name=card.name: self._stop_instance_async(name))

        threading.Thread(target=stop_worker, daemon=True).start()

    def _start_instance_async(self, name):
        """Start instance asynchronously"""
        def start_worker():
            try:
                success = self.app.instance_manager.start_instance(name)
                message = f"Starting instance: {name}" if success else f"Failed to start instance: {name}"
                self.app.after_idle(lambda: self.app.add_console_message(message))
            except Exception as e:
                self.app.after_idle(lambda: self.app.add_console_message(f"Error starting {name}: {str(e)}"))

        threading.Thread(target=start_worker, daemon=True).start()

    def _stop_instance_async(self, name):
        """Stop instance asynchronously"""
        def stop_worker():
            try:
                success = self.app.instance_manager.stop_instance(name)
                message = f"Stopping instance: {name}" if success else f"Failed to stop instance: {name}"
                self.app.after_idle(lambda: self.app.add_console_message(message))
            except Exception as e:
                self.app.after_idle(lambda: self.app.add_console_message(f"Error stopping {name}: {str(e)}"))

        threading.Thread(target=stop_worker, daemon=True).start()

    def start_instance(self, name):
        """Start an instance (non-blocking)"""
        self._start_instance_async(name)

    def stop_instance(self, name):
        """Stop an instance (non-blocking)"""
        self._stop_instance_async(name)

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
        """FIXED: Refresh all instances (non-blocking)"""
        self.app.add_console_message("Refreshing all instances from MEmu...")

        def refresh_worker():
            try:
                # Small delay to let UI update
                time.sleep(0.5)

                # Refresh instances
                self.app.instance_manager.refresh_instances()

                instance_count = len(self.app.instance_manager.get_instances())

                # Schedule UI updates on main thread
                self.app.after_idle(lambda: [
                    self.app.load_instances(),
                    self.app.force_counter_update(),
                    self.app.add_console_message(f"Refreshed {instance_count} instances from MEmu")
                ])
            except Exception as e:
                self.app.after_idle(lambda e=e: self.app.add_console_message(f"Refresh error: {str(e)}"))

        threading.Thread(target=refresh_worker, daemon=True).start()