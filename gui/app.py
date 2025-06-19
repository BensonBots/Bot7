import tkinter as tk
from datetime import datetime
import threading
import time
from core.instance_manager import InstanceManager
from gui.components.loading_overlay import LoadingOverlay
from utils.instance_operations import InstanceOperations
from utils.ui_manager import UIManager
from utils.module_manager import ModuleManager

class BensonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BENSON v2.0 - Streamlined")
        self.geometry("1200x800")
        self.configure(bg="#0a0e16")
        self.minsize(900, 600)
        self.instance_cards = []
        self.selected_cards = []
        self.search_after_id = None
        self.loading = LoadingOverlay(self)
        self.after(100, self.initialize_background)
    
    def initialize_background(self):
        def init_worker():
            try:
                self.loading.update_status("Connecting to MEmu...")
                time.sleep(0.3)
                self.instance_manager = InstanceManager()
                
                self.loading.update_status("Loading MEmu instances...")
                time.sleep(0.3)
                self.instance_manager.load_real_instances()
                
                self.loading.update_status("Initializing modules...")
                time.sleep(0.3)
                self.module_manager = ModuleManager(self)
                self.module_manager.initialize_modules()
                
                self.loading.update_status("Setting up interface...")
                time.sleep(0.3)
                self.instance_ops = InstanceOperations(self)
                self.ui_manager = UIManager(self)
                
                self.loading.update_status("Configuring shortcuts...")
                time.sleep(0.2)
                self.bind_all("<Control-r>", lambda e: self.instance_ops.refresh_instances())
                self.bind_all("<Control-a>", lambda e: self.instance_ops.select_all_instances())
                self.bind_all("<Delete>", lambda e: self.instance_ops.delete_selected_instances_with_loading())
                
                self.loading.update_status("Finalizing setup...")
                time.sleep(0.3)
                
                self.after(0, self.complete_initialization)
            except Exception as e:
                self.after(0, lambda: self.show_init_error(str(e)))
        threading.Thread(target=init_worker, daemon=True).start()
    
    def complete_initialization(self):
        try:
            self.loading.update_status("Building interface...")
            self.setup_ui()
            
            self.loading.update_status("Starting background tasks...")
            self.start_background_tasks()
            
            self.loading.update_status("Updating instance counter...")
            self.force_counter_update()
            
            self.loading.update_status("Running background optimization...")
            self.start_background_optimization()
            
            self.loading.update_status("Checking module auto-startup...")
            time.sleep(0.5)
            
            self.loading.update_status("Completing initialization...")
            time.sleep(0.5)
            
            self.loading.close()
            
            self.after(1000, self.check_module_auto_startup)
        except Exception as e:
            self.loading.close()
            self.show_init_error(str(e))
    
    def check_module_auto_startup(self):
        try:
            self.module_manager.check_auto_startup()
        except Exception as e:
            self.add_console_message(f"❌ Auto-startup error: {e}")
    
    def show_init_error(self, error):
        from tkinter import messagebox
        messagebox.showerror("Init Error", f"Failed to initialize:\n{error}")
        self.destroy()
    
    def start_background_optimization(self):
        def optimization_callback(results):
            if 'error' in results:
                self.add_console_message(f"⚠ Optimization error: {results['error']}")
            elif results['optimized'] > 0:
                self.add_console_message(f"🔧 Optimized: {results['optimized']} instances")
        self.instance_manager.optimize_all_instances_async(lambda results: self.after(0, lambda: optimization_callback(results)))
    
    def setup_ui(self):
        self.ui_manager.setup_header()
        self.ui_manager.setup_controls()
        self.ui_manager.setup_main_content()
        self.ui_manager.setup_console()
        self.ui_manager.setup_footer()
        self.load_instances()
        self.add_console_message("BENSON v2.0 started")
        instances_count = len(self.instance_manager.get_instances())
        self.add_console_message(f"Loaded {instances_count} instances")
    
    def on_search_change_debounced(self, *args):
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        query = self.search_var.get()
        if query == "Search instances...":
            return
        self.search_after_id = self.after(150, lambda: self.filter_instances_fast(query))
    
    def on_search_focus_in(self, event):
        if self.search_entry.get() == "Search instances...":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg="#ffffff")
    
    def on_search_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search instances...")
            self.search_entry.configure(fg="#8b949e")
    
    def filter_instances_fast(self, query):
        if not query or query == "Search instances...":
            self.show_all_instances()
            return
        query_lower = query.lower()
        visible_cards = []
        for card in self.instance_cards:
            if query_lower in card.name.lower():
                card.grid()
                visible_cards.append(card)
            else:
                card.grid_remove()
        self.reposition_cards(visible_cards)
    
    def show_all_instances(self):
        for card in self.instance_cards:
            card.grid()
        self.reposition_all_cards()
    
    def reposition_cards(self, cards):
        for card in cards:
            card.grid_remove()
        for i, card in enumerate(cards):
            row = i // 2
            col = i % 2
            card.grid(row=row, column=col, padx=4, pady=2, sticky="e" if col == 0 else "w", in_=self.instances_container)
            card.configure(width=580)
            self.instances_container.grid_columnconfigure(col, weight=1)
    
    def reposition_all_cards(self):
        self.reposition_cards(self.instance_cards)
    
    def force_counter_update(self):
        instances_count = len(self.instance_manager.get_instances())
        new_text = f"⚡ MEmu Instances ({instances_count})"
        if hasattr(self, 'instances_header'):
            self.instances_header.configure(text=new_text)
            self.update_idletasks()
        return instances_count
    
    def load_instances(self):
        for card in self.instance_cards:
            card.destroy()
        self.instance_cards.clear()
        self.selected_cards.clear()
        instances = self.instance_manager.get_instances()
        
        if len(instances) == 0:
            no_instances_label = tk.Label(self.instances_container, text="No MEmu instances found\nClick 'Create' to add a new instance", bg="#0a0e16", fg="#8b949e", font=("Segoe UI", 12), justify="center")
            no_instances_label.grid(row=0, column=0, columnspan=2, pady=50)
        else:
            from gui.components.instance_card import InstanceCard
            for instance in instances:
                card = InstanceCard(self.instances_container, name=instance["name"], status=instance["status"], cpu_usage=instance["cpu"], memory_usage=instance["memory"], app_ref=self)
                self.instance_cards.append(card)
            self.reposition_all_cards()
        
        self.force_counter_update()
        if hasattr(self, 'module_manager'):
            self.module_manager.refresh_modules()
    
    def on_card_selection_changed(self):
        self.selected_cards = [card for card in self.instance_cards if card.selected]
    
    def start_instance(self, name):
        self.instance_ops.start_instance(name)
    
    def stop_instance(self, name):
        self.instance_ops.stop_instance(name)
    
    def delete_instance_card_with_loading(self, card):
        self.instance_ops.delete_instance_card_with_loading(card)
    
    def show_modules(self, instance_name):
        self.ui_manager.show_modules(instance_name)
    
    def add_console_message(self, message):
        if not hasattr(self, 'console_text'):
            return
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"
        self.console_text.configure(state="normal")
        self.console_text.insert("end", full_message)
        self.console_text.configure(state="disabled")
        self.console_text.see("end")
    
    def clear_console(self):
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")
        self.add_console_message("Console cleared")
    
    def start_background_tasks(self):
        def status_monitor():
            last_status = {}
            full_refresh_counter = 0
            while True:
                time.sleep(3)
                try:
                    if not hasattr(self, 'instance_manager'):
                        continue
                    full_refresh_counter += 1
                    if full_refresh_counter >= 10:
                        self.instance_manager.load_real_instances()
                        full_refresh_counter = 0
                    else:
                        self.instance_manager.update_instance_statuses()
                    instances = self.instance_manager.get_instances()
                    for card in self.instance_cards:
                        for instance in instances:
                            if instance["name"] == card.name:
                                real_status = instance["status"]
                                last_known = last_status.get(card.name)
                                if last_known != real_status:
                                    last_status[card.name] = real_status
                                    self.after(0, lambda c=card, s=real_status: c.update_status(s))
                                break
                except:
                    pass
        threading.Thread(target=status_monitor, daemon=True).start()

if __name__ == "__main__":
    app = BensonApp()
    app.mainloop()