import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
from gui.components.loading_overlay import LoadingOverlay

class InstanceOperations:
    def __init__(self, app_ref):
        self.app = app_ref
    
    def create_instance(self):
        name = simpledialog.askstring("Create Instance", "Enter instance name:")
        if name:
            name = name.strip()
            if not name:
                self.app.add_console_message("✗ Invalid name")
                return
            loading = LoadingOverlay(self.app)
            def create_worker():
                try:
                    loading.update_status("Creating instance...")
                    success = self.app.instance_manager.create_instance(name)
                    self.app.after(0, lambda: self._complete_create_instance(name, loading, success))
                except Exception as e:
                    self.app.after(0, lambda: self._complete_create_instance(name, loading, False, str(e)))
            threading.Thread(target=create_worker, daemon=True).start()
    
    def _complete_create_instance(self, name, loading, success, error=None):
        loading.close()
        if success:
            def refresh_worker():
                time.sleep(0.5)
                self.app.instance_manager.load_real_instances()
                self.app.after(0, lambda: [self.app.load_instances(), self.app.force_counter_update(), self.app.add_console_message(f"✓ Created: {name}")])
            threading.Thread(target=refresh_worker, daemon=True).start()
        else:
            error_msg = f"Failed to create: {name}"
            if error:
                error_msg += f"\n{error}"
            self.app.add_console_message(f"✗ {error_msg}")
            messagebox.showerror("Failed", error_msg)
    
    def clone_selected_instance(self):
        self.app.add_console_message("Clone coming soon...")
    
    def start_selected_instances(self):
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return
        self.app.add_console_message(f"Starting {len(selected_cards)} instances...")
        for card in selected_cards:
            self.start_instance(card.name)
    
    def stop_selected_instances(self):
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return
        self.app.add_console_message(f"Stopping {len(selected_cards)} instances...")
        for card in selected_cards:
            self.stop_instance(card.name)
    
    def delete_selected_instances_with_loading(self):
        selected_cards = [card for card in self.app.instance_cards if card.selected]
        if not selected_cards:
            self.app.add_console_message("No instances selected")
            return
        result = messagebox.askyesno("Delete", f"Delete {len(selected_cards)} instances?\n\nCannot be undone.")
        if not result:
            return
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
        loading.close()
        for card in deleted_cards:
            if card in self.app.instance_cards:
                self.app.instance_cards.remove(card)
            if card in self.app.selected_cards:
                self.app.selected_cards.remove(card)
            card.destroy()
        self.app.load_instances()
        self.app.force_counter_update()
        if success_count > 0:
            self.app.add_console_message(f"✓ Deleted {success_count} instances")
        if error:
            self.app.add_console_message(f"✗ Error: {error}")
    
    def delete_instance_card_with_loading(self, card):
        result = messagebox.askyesno("Delete", f"Delete '{card.name}'?\n\nCannot be undone.")
        if not result:
            return
        loading = LoadingOverlay(self.app)
        loading.update_status("Deleting...")
        def delete_worker():
            try:
                success = self.app.instance_manager.delete_instance(card.name)
                self.app.after(0, lambda: self._complete_single_delete(card, loading, success))
            except Exception as e:
                self.app.after(0, lambda: self._complete_single_delete(card, loading, False, str(e)))
        threading.Thread(target=delete_worker, daemon=True).start()
    
    def _complete_single_delete(self, card, loading, success, error=None):
        loading.close()
        if success:
            if card in self.app.instance_cards:
                self.app.instance_cards.remove(card)
            if card in self.app.selected_cards:
                self.app.selected_cards.remove(card)
            card.destroy()
            self.app.load_instances()
            self.app.force_counter_update()
            self.app.add_console_message(f"✓ Deleted: {card.name}")
        else:
            error_msg = f"Failed to delete: {card.name}"
            if error:
                error_msg += f"\n{error}"
            self.app.add_console_message(f"✗ {error_msg}")
            messagebox.showerror("Failed", error_msg)
    
    def start_instance(self, name):
        def start_worker():
            success = self.app.instance_manager.start_instance(name)
            if success:
                self.app.after(0, lambda: self.app.add_console_message(f"Starting: {name}"))
        threading.Thread(target=start_worker, daemon=True).start()
    
    def stop_instance(self, name):
        def stop_worker():
            success = self.app.instance_manager.stop_instance(name)
            if success:
                self.app.after(0, lambda: self.app.add_console_message(f"Stopping: {name}"))
        threading.Thread(target=stop_worker, daemon=True).start()
    
    def toggle_select_all(self):
        if not self.app.instance_cards:
            return
        all_selected = all(card.selected for card in self.app.instance_cards)
        if all_selected:
            for card in self.app.instance_cards:
                if card.selected:
                    card.toggle_checkbox()
            self.app.add_console_message("All unselected")
        else:
            for card in self.app.instance_cards:
                if not card.selected:
                    card.toggle_checkbox()
            self.app.add_console_message("All selected")
    
    def select_all_instances(self):
        for card in self.app.instance_cards:
            if not card.selected:
                card.toggle_checkbox()
        self.app.add_console_message("All selected")
    
    def refresh_instances(self):
        self.app.add_console_message("Refreshing...")
        def delayed_refresh():
            time.sleep(0.5)
            self.app.instance_manager.refresh_instances()
            self.app.after(0, lambda: [self.app.load_instances(), self.app.force_counter_update(), self.app.add_console_message(f"Refreshed {len(self.app.instance_manager.get_instances())} instances")])
        threading.Thread(target=delayed_refresh, daemon=True).start()