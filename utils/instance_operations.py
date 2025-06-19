"""
BENSON v2.0 - Fixed Instance Operations
Better create instance dialog with proper naming
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time

from gui.components.loading_overlay import LoadingOverlay


class InstanceOperations:
    """Fixed instance operations with better create dialog"""

    def __init__(self, app_ref):
        self.app = app_ref

    def create_instance_with_name(self, name):
        """Create instance with specific name (called from dialog)"""
        if not name or not name.strip():
            self.app.add_console_message("✗ Invalid instance name")
            return

        name = name.strip()

        # Show loading overlay
        loading = LoadingOverlay(self.app)

        def create_worker():
            try:
                loading.update_status(f"Creating instance '{name}'...")

                self.app.after(0, lambda: self.app.add_console_message(f"Setting up MEmu instance: {name}"))

                # Use the instance manager's create method with the specific name
                success = self.app.instance_manager.create_instance_with_name(name)

                self.app.after(0, lambda: self._complete_create_instance(name, loading, success))

            except Exception as e:
                self.app.after(0, lambda: self._complete_create_instance(name, loading, False, str(e)))

        threading.Thread(target=create_worker, daemon=True).start()

    def create_instance(self):
        """Legacy create instance method (fallback)"""
        name = simpledialog.askstring("Create MEmu Instance", 
                                     "Enter MEmu instance name:\n(e.g., MyGame, Instance1, etc.)")

        if name:
            self.create_instance_with_name(name)
        else:
            self.app.add_console_message("Instance creation cancelled")

    def _complete_create_instance(self, name, loading, success, error=None):
        """Complete instance creation"""
        loading.close()

        if success:
            # Quick refresh
            def refresh_worker():
                time.sleep(0.5)
                self.app.instance_manager.load_real_instances()

                self.app.after(0, lambda: [
                    self.app.load_instances(),
                    self.app.force_counter_update(),
                    self.app.add_console_message(f"✓ Successfully created MEmu instance: {name}")
                ])

            threading.Thread(target=refresh_worker, daemon=True).start()

        else:
            error_msg = f"Failed to create instance: {name}"
            if error:
                error_msg += f"\nError: {error}"
            self.app.add_console_message(f"✗ {error_msg}")
            messagebox.showerror("Creation Failed", error_msg)

    def clone_selected_instance(self):
        """Clone the selected instance"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instance selected for cloning")
            return

        self.app.add_console_message("Clone functionality coming soon...")

    def start_selected_instances(self):
        """Start selected instances"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Starting {len(selected_cards)} selected instances...")
        for card in selected_cards:
            self.start_instance(card.name)

    def stop_selected_instances(self):
        """Stop selected instances"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return

        self.app.add_console_message(f"Stopping {len(selected_cards)} selected instances...")
        for card in selected_cards:
            self.stop_instance(card.name)

    def delete_selected_instances_with_loading(self):
        """Delete selected instances with loading screen"""
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected for deletion")
            return

        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete {len(selected_cards)} selected instances?\n\nThis cannot be undone.")
        if not result:
            return

        # Show loading overlay
        loading = LoadingOverlay(self.app)
        loading.update_status(f"Deleting {len(selected_cards)} instances...")

        def delete_worker():
            try:
                success_count = 0
                for i, card in enumerate(selected_cards):
                    loading.update_status(f"Deleting {card.name} ({i+1}/{len(selected_cards)})...")

                    success = self.app.instance_manager.delete_instance(card.name)
                    if success:
                        success_count += 1

                    time.sleep(0.3)

                self.app.after(0, lambda: self._complete_bulk_delete(selected_cards, loading, success_count))

            except Exception as e:
                self.app.after(0, lambda: self._complete_bulk_delete(selected_cards, loading, 0, str(e)))

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
        """Delete a single instance card with loading"""
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Delete instance '{card.name}'?\n\nThis cannot be undone.")

        if not result:
            return

        loading = LoadingOverlay(self.app)
        loading.update_status("Deleting instance...")

        def delete_worker():
            try:
                success = self.app.instance_manager.delete_instance(card.name)
                self.app.after(0, lambda: self._complete_single_delete(card, loading, success))
            except Exception as e:
                self.app.after(0, lambda: self._complete_single_delete(card, loading, False, str(e)))

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
        """Start an instance"""
        def start_worker():
            success = self.app.instance_manager.start_instance(name)
            if success:
                self.app.after(0, lambda: self.app.add_console_message(f"Starting instance: {name}"))

        # Run in background thread to avoid blocking UI
        threading.Thread(target=start_worker, daemon=True).start()

    def stop_instance(self, name):
        """Stop an instance"""
        def stop_worker():
            success = self.app.instance_manager.stop_instance(name)
            if success:
                self.app.after(0, lambda: self.app.add_console_message(f"Stopping instance: {name}"))

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
        """Refresh all instances"""
        self.app.add_console_message("Refreshing all instances from MEmu...")

        def delayed_refresh():
            time.sleep(0.5)
            self.app.instance_manager.refresh_instances()
            self.app.after(0, lambda: [
                self.app.load_instances(),
                self.app.force_counter_update(),
                self.app.add_console_message(f"Refreshed {len(self.app.instance_manager.get_instances())} instances from MEmu")
            ])

        threading.Thread(target=delayed_refresh, daemon=True).start()