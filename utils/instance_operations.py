"""
BENSON v2.0 - Instance Operations Handler
Handles instance creation, deletion, and management operations
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time

from gui.components.loading_overlay import LoadingOverlay


class InstanceOperations:
    """Handles instance CRUD operations for the main application"""
    
    def __init__(self, app_ref):
        self.app = app_ref
    
    def create_instance(self, name=None):
        """Create a new instance with loading screen"""
        if name is None:
            # Prompt for instance name
            name = simpledialog.askstring(
                "Create Instance",
                "Enter instance name:",
                parent=self.app
            )
            if not name:  # User cancelled or entered empty name
                return
        
        loading = LoadingOverlay(self.app, "Creating instance...")
        
        def create_worker():
            try:
                success = self.app.instance_manager.create_instance(name)
                
                if success:
                    # Wait for instance to be fully created
                    time.sleep(2)
                    
                    # Refresh UI first
                    self.app.instance_manager.load_real_instances()
                    self.app.after(0, lambda: [
                        self.app.load_instances(),
                        self.app.force_counter_update(),
                        self.app.add_console_message(f"✓ Successfully created instance: {name}")
                    ])
                    
                    # Get current settings before optimization
                    loading.update_status("Checking current settings...")
                    settings = self.app.instance_manager._load_optimization_defaults()
                    current_settings = self.app.instance_manager.get_instance_settings(name)
                    
                    if current_settings:
                        current_msg = f"Current: {current_settings['ram_mb']}MB RAM, {current_settings['cpu_cores']} CPU"
                        target_msg = f"Target: {settings['default_ram_mb']}MB RAM, {settings['default_cpu_cores']} CPU"
                        loading.update_status(f"Optimizing instance...\n{current_msg}\n{target_msg}")
                    else:
                        loading.update_status("Optimizing instance...")
                    
                    opt_success = self.app.instance_manager.optimize_instance_with_settings(name)
                    
                    if opt_success:
                        self.app.add_console_message(f"✓ Successfully optimized instance: {name}")
                    else:
                        self.app.add_console_message(f"⚠ Failed to optimize instance: {name}")
                    
                    # Final refresh after optimization
                    self.app.instance_manager.load_real_instances()
                    self.app.after(0, lambda: [
                        self.app.load_instances(),
                        self.app.force_counter_update()
                    ])
                else:
                    self.app.after(0, lambda: 
                        self.app.add_console_message(f"✗ Failed to create instance: {name}")
                    )
            finally:
                self.app.after(0, loading.close)
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=create_worker, daemon=True).start()
    
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
        """Delete a single instance card with loading screen"""
        loading = LoadingOverlay(self.app, "Deleting instance...")
        
        def delete_worker():
            try:
                success = self.app.instance_manager.delete_instance(card.name)
                if success:
                    # Wait briefly to ensure the instance is deleted
                    time.sleep(1)
                    self.app.after(0, lambda: [
                        # Remove card from UI
                        card.destroy() if card in self.app.instance_cards else None,
                        self.app.instance_cards.remove(card) if card in self.app.instance_cards else None,
                        self.app.selected_cards.remove(card) if card in self.app.selected_cards else None,
                        # Update UI
                        self.app.load_instances(),
                        self.app.force_counter_update(),
                        self.app.add_console_message(f"✓ Successfully deleted instance: {card.name}")
                    ])
                else:
                    self.app.after(0, lambda:
                        self.app.add_console_message(f"✗ Failed to delete instance: {card.name}")
                    )
            finally:
                self.app.after(0, loading.close)
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=delete_worker, daemon=True).start()
    
    def start_instance(self, name):
        """Start an instance with status updates"""
        def start_worker():
            try:
                # Update card status to Starting
                for card in self.app.instance_cards:
                    if card.name == name:
                        self.app.after(0, lambda: card.update_status("Starting"))
                        break
                
                # Check and optimize instance if needed before starting
                if self.app.instance_manager.check_and_optimize_instance(name):
                    self.app.add_console_message(f"✓ Optimized instance before starting: {name}")
                
                success = self.app.instance_manager.start_instance(name)
                if success:
                    self.app.add_console_message(f"✓ Starting instance: {name}")
                    # Refresh instance status after a brief delay
                    time.sleep(2)
                    self.app.instance_manager.load_real_instances()
                    self.app.after(0, lambda: [
                        self.app.load_instances(),
                        self.app.force_counter_update()
                    ])
                    
                    # Check if AutoStartGame should be triggered
                    if hasattr(self.app, 'module_manager'):
                        settings = self.app.module_manager.settings_cache.get(name, {})
                        if (settings.get("autostart_game", {}).get("auto_startup", False) and 
                            settings.get("autostart_game", {}).get("enabled", True)):
                            self.app.add_console_message(f"🎮 Auto-startup enabled for {name}, starting game...")
                            self.app.module_manager._auto_start_instance(name)
                else:
                    self.app.add_console_message(f"✗ Failed to start instance: {name}")
                    # Reset card status to Stopped on failure
                    for card in self.app.instance_cards:
                        if card.name == name:
                            self.app.after(0, lambda: card.update_status("Stopped"))
                            break
            except Exception as e:
                self.app.add_console_message(f"✗ Error starting instance {name}: {str(e)}")
                # Reset card status on error
                for card in self.app.instance_cards:
                    if card.name == name:
                        self.app.after(0, lambda: card.update_status("Stopped"))
                        break
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=start_worker, daemon=True).start()
    
    def stop_instance(self, name):
        """Stop an instance with status updates"""
        def stop_worker():
            try:
                # Update card status to Stopping
                for card in self.app.instance_cards:
                    if card.name == name:
                        self.app.after(0, lambda: card.update_status("Stopping"))
                        break
                
                # Stop any running modules first
                if hasattr(self.app, 'module_manager'):
                    module = self.app.module_manager.get_autostart_module(name)
                    if module and name in module.get_running_instances():
                        self.app.add_console_message(f"🛑 Stopping modules for {name}")
                        module.stop_auto_game(name)
                        time.sleep(1)  # Give module a chance to cleanup
                
                success = self.app.instance_manager.stop_instance(name)
                if success:
                    self.app.add_console_message(f"✓ Stopping instance: {name}")
                    
                    # Wait for instance to fully stop
                    max_wait = 10  # Maximum seconds to wait
                    for _ in range(max_wait):
                        time.sleep(1)
                        # Check if instance is actually stopped
                        status = self.app.instance_manager._get_real_instance_status(
                            next(i["index"] for i in self.app.instance_manager.instances if i["name"] == name),
                            name
                        )
                        if status == "Stopped":
                            break
                    
                    # Final refresh after confirmed stop
                    self.app.instance_manager.load_real_instances()
                    self.app.after(0, lambda: [
                        self.app.load_instances(),
                        self.app.force_counter_update()
                    ])
                else:
                    self.app.add_console_message(f"✗ Failed to stop instance: {name}")
                    # Reset card status to Running on failure
                    for card in self.app.instance_cards:
                        if card.name == name:
                            self.app.after(0, lambda: card.update_status("Running"))
                            break
            except Exception as e:
                self.app.add_console_message(f"✗ Error stopping instance {name}: {str(e)}")
                # Reset card status on error
                for card in self.app.instance_cards:
                    if card.name == name:
                        self.app.after(0, lambda: card.update_status("Running"))
                        break
        
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

    def optimize_instance(self, name):
        """Optimize an instance with loading screen"""
        loading = LoadingOverlay(self.app, "Checking current settings...")
        
        def optimize_worker():
            try:
                # Get current settings
                settings = self.app.instance_manager._load_optimization_defaults()
                current_settings = self.app.instance_manager.get_instance_settings(name)
                
                if current_settings:
                    current_msg = f"Current: {current_settings['ram_mb']}MB RAM, {current_settings['cpu_cores']} CPU"
                    target_msg = f"Target: {settings['default_ram_mb']}MB RAM, {settings['default_cpu_cores']} CPU"
                    loading.update_status(f"Optimizing instance...\n{current_msg}\n{target_msg}")
                else:
                    loading.update_status("Optimizing instance...")
                
                success = self.app.instance_manager.optimize_instance_with_settings(name)
                
                if success:
                    self.app.add_console_message(f"✓ Successfully optimized instance: {name}")
                    
                    # Verify final settings
                    final_settings = self.app.instance_manager.get_instance_settings(name)
                    if final_settings:
                        final_msg = f"✓ Optimized to {final_settings['ram_mb']}MB RAM, {final_settings['cpu_cores']} CPU"
                        loading.update_status(final_msg)
                        time.sleep(1)  # Show final settings briefly
                else:
                    self.app.add_console_message(f"⚠ Failed to optimize instance: {name}")
                
                # Refresh UI
                self.app.instance_manager.load_real_instances()
                self.app.after(0, lambda: [
                    self.app.load_instances(),
                    self.app.force_counter_update()
                ])
                
            finally:
                self.app.after(0, loading.close)
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=optimize_worker, daemon=True).start()

    def optimize_all_instances(self):
        """Optimize all instances with loading screen"""
        loading = LoadingOverlay(self.app, "Checking instances...")
        
        def optimize_worker():
            try:
                instances = self.app.instance_manager.get_instances()
                total = len(instances)
                optimized = 0
                skipped = 0
                failed = 0
                
                for idx, instance in enumerate(instances, 1):
                    name = instance["name"]
                    
                    # Skip running instances
                    if instance["status"] == "Running":
                        skipped += 1
                        continue
                    
                    # Get current settings
                    settings = self.app.instance_manager._load_optimization_defaults()
                    current_settings = self.app.instance_manager.get_instance_settings(name)
                    
                    progress = f"[{idx}/{total}] Optimizing {name}"
                    if current_settings:
                        current_msg = f"Current: {current_settings['ram_mb']}MB RAM, {current_settings['cpu_cores']} CPU"
                        target_msg = f"Target: {settings['default_ram_mb']}MB RAM, {settings['default_cpu_cores']} CPU"
                        loading.update_status(f"{progress}\n{current_msg}\n{target_msg}")
                    else:
                        loading.update_status(f"{progress}")
                    
                    if self.app.instance_manager.optimize_instance_with_settings(name):
                        optimized += 1
                    else:
                        failed += 1
                    
                    # Small delay between instances
                    time.sleep(0.5)
                
                # Show final summary
                summary = f"Optimization complete:\n✓ {optimized} optimized\n⏭ {skipped} skipped\n⚠ {failed} failed"
                loading.update_status(summary)
                time.sleep(2)  # Show summary briefly
                
                # Update UI
                self.app.instance_manager.load_real_instances()
                self.app.after(0, lambda: [
                    self.app.load_instances(),
                    self.app.force_counter_update()
                ])
                
                # Log results
                self.app.add_console_message(f"✓ Optimization complete: {optimized} optimized, {skipped} skipped, {failed} failed")
                
            finally:
                self.app.after(0, loading.close)
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=optimize_worker, daemon=True).start()