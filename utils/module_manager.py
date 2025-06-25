"""
BENSON v2.0 - Compact Module Manager
Reduced from 250+ lines to ~100 lines while maintaining core functionality
"""

import os
import json
import threading
import time
from typing import Dict


class ModuleManager:
    """Compact module manager with auto-triggers"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_modules = {}
        self.settings_cache = {}
        self.initialization_complete = False
        self.autostart_completed = {}
        self.running_modules = {}
        
        print("[ModuleManager] Initializing compact module system...")
        self._init_modules()
        self._start_status_loop()
    
    def _init_modules(self):
        """Initialize modules for all instances"""
        try:
            # Import modules
            from modules.autostart_game import AutoStartGameModule
            
            try:
                from modules.auto_gather import AutoGatherModule
            except ImportError:
                AutoGatherModule = None
            
            # Create modules for each instance
            instances = self.app.instance_manager.get_instances()
            for instance in instances:
                self._create_instance_modules(instance["name"], AutoStartGameModule, AutoGatherModule)
            
            self.initialization_complete = True
            print(f"[ModuleManager] ✅ Ready for {len(instances)} instances")
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Init error: {e}")
            self.initialization_complete = True
    
    def _create_instance_modules(self, instance_name: str, AutoStartGameModule, AutoGatherModule=None):
        """Create modules for single instance"""
        try:
            settings = self._load_settings(instance_name)
            self.settings_cache[instance_name] = settings
            self.instance_modules[instance_name] = {}
            self.running_modules[instance_name] = {}
            
            # AutoStart module (always created)
            autostart = AutoStartGameModule(
                instance_name=instance_name,
                shared_resources=self.app.instance_manager,
                console_callback=self.app.add_console_message
            )
            self.instance_modules[instance_name]["AutoStartGame"] = autostart
            self.running_modules[instance_name]["AutoStartGame"] = False
            
            # AutoGather module (if available and enabled)
            if AutoGatherModule and settings.get("auto_gather", {}).get("enabled", True):
                gather = AutoGatherModule(
                    instance_name=instance_name,
                    shared_resources=self.app.instance_manager,
                    console_callback=self.app.add_console_message
                )
                self.instance_modules[instance_name]["AutoGather"] = gather
                self.running_modules[instance_name]["AutoGather"] = False
            
            print(f"[ModuleManager] ✅ Modules created for {instance_name}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Error creating modules for {instance_name}: {e}")
    
    def _start_status_loop(self):
        """Start background status update loop"""
        def status_loop():
            while hasattr(self, 'app') and self.app:
                try:
                    self.app.instance_manager.update_instance_statuses()
                    self._update_card_statuses()
                    time.sleep(10)
                except Exception as e:
                    print(f"[ModuleManager] Status loop error: {e}")
                    time.sleep(10)
        
        threading.Thread(target=status_loop, daemon=True, name="StatusLoop").start()
    
    def _update_card_statuses(self):
        """Update GUI card statuses"""
        try:
            if not hasattr(self.app, 'instance_cards'):
                return
            
            instances = self.app.instance_manager.get_instances()
            status_map = {inst["name"]: inst["status"] for inst in instances}
            
            for card in self.app.instance_cards:
                if hasattr(card, 'name') and hasattr(card, 'update_status'):
                    new_status = status_map.get(card.name)
                    if new_status and new_status != card.status:
                        self.app.after(0, lambda c=card, s=new_status: c.update_status(s))
        except Exception as e:
            print(f"[ModuleManager] Card update error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """Trigger auto-startup when instance starts"""
        if not self.initialization_complete:
            return
        
        if self._recently_completed(instance_name):
            return
        
        print(f"[ModuleManager] 🎯 Auto-startup triggered for {instance_name}")
        self.app.after(8000, lambda: self._start_autostart(instance_name))
    
    def _start_autostart(self, instance_name: str):
        """Start AutoStart module"""
        try:
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                print(f"[ModuleManager] Auto-startup disabled for {instance_name}")
                return
            
            if instance_name not in self.instance_modules:
                return
            
            autostart = self.instance_modules[instance_name].get("AutoStartGame")
            if not autostart:
                return
            
            # Verify instance is ready
            def check_and_start():
                instance = self.app.instance_manager.get_instance(instance_name)
                if instance and instance["status"] == "Running":
                    self._execute_autostart(instance_name, autostart, settings)
                else:
                    print(f"[ModuleManager] Instance {instance_name} not ready")
            
            check_and_start()
            
        except Exception as e:
            print(f"[ModuleManager] ❌ AutoStart error: {e}")
    
    def _execute_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Execute AutoStart with completion callback"""
        try:
            print(f"[ModuleManager] 🚀 Starting AutoStart for {instance_name}")
            self.app.add_console_message(f"🎮 Starting AutoStart for {instance_name}...")
            
            def on_complete(success: bool):
                if success:
                    self.app.add_console_message(f"✅ AutoStart completed for {instance_name}")
                    self._mark_completed(instance_name)
                    # Auto-start AutoGather
                    self.app.after(3000, lambda: self._start_autogather(instance_name))
                else:
                    self.app.add_console_message(f"❌ AutoStart failed for {instance_name}")
            
            max_retries = settings.get("autostart_game", {}).get("max_retries", 3)
            success = autostart_module.start_auto_game(
                instance_name=instance_name,
                max_retries=max_retries,
                on_complete=on_complete
            )
            
            if success:
                self.running_modules[instance_name]["AutoStartGame"] = True
                
        except Exception as e:
            print(f"[ModuleManager] ❌ Execute AutoStart error: {e}")
    
    def _start_autogather(self, instance_name: str):
        """Auto-start AutoGather after AutoStart completes"""
        try:
            if (instance_name not in self.instance_modules or 
                "AutoGather" not in self.instance_modules[instance_name]):
                return
            
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("auto_gather", {}).get("enabled", True):
                return
            
            if self.running_modules[instance_name].get("AutoGather", False):
                return
            
            print(f"[ModuleManager] 🌾 Auto-starting AutoGather for {instance_name}")
            self.app.add_console_message(f"🌾 Starting AutoGather for {instance_name}...")
            
            gather = self.instance_modules[instance_name]["AutoGather"]
            success = gather.start()
            
            if success:
                self.running_modules[instance_name]["AutoGather"] = True
                self.app.add_console_message(f"✅ AutoGather started for {instance_name}")
            else:
                self.app.add_console_message(f"❌ AutoGather failed for {instance_name}")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ AutoGather start error: {e}")
    
    def cleanup_for_stopped_instance(self, instance_name: str):
        """Clean up when instance stops"""
        try:
            if instance_name not in self.instance_modules:
                return
            
            modules = self.instance_modules[instance_name]
            for module_name, module in modules.items():
                try:
                    if hasattr(module, 'stop'):
                        module.stop()
                    if hasattr(module, 'cleanup_for_stopped_instance'):
                        module.cleanup_for_stopped_instance()
                    self.running_modules[instance_name][module_name] = False
                except Exception as e:
                    print(f"[ModuleManager] Error stopping {module_name}: {e}")
            
            self.autostart_completed.pop(instance_name, None)
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Cleanup error: {e}")
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            for instance_name in list(self.instance_modules.keys()):
                if instance_name not in current_names:
                    self.cleanup_for_stopped_instance(instance_name)
                    del self.instance_modules[instance_name]
                    self.settings_cache.pop(instance_name, None)
                    self.running_modules.pop(instance_name, None)
            
            # Add modules for new instances
            for instance in current_instances:
                if instance["name"] not in self.instance_modules:
                    try:
                        from modules.autostart_game import AutoStartGameModule
                        try:
                            from modules.auto_gather import AutoGatherModule
                        except ImportError:
                            AutoGatherModule = None
                        self._create_instance_modules(instance["name"], AutoStartGameModule, AutoGatherModule)
                    except Exception as e:
                        print(f"[ModuleManager] ❌ Failed to create modules: {e}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings when changed"""
        try:
            settings = self._load_settings(instance_name)
            self.settings_cache[instance_name] = settings
        except Exception as e:
            print(f"[ModuleManager] ❌ Settings reload error: {e}")
    
    def stop_all_modules(self):
        """Stop all modules"""
        for instance_name in list(self.instance_modules.keys()):
            self.cleanup_for_stopped_instance(instance_name)
    
    # Helper methods
    def _recently_completed(self, instance_name: str) -> bool:
        """Check if AutoStart completed recently"""
        if instance_name not in self.autostart_completed:
            return False
        return time.time() - self.autostart_completed[instance_name] < 300
    
    def _mark_completed(self, instance_name: str):
        """Mark AutoStart as completed"""
        self.autostart_completed[instance_name] = time.time()
    
    def _load_settings(self, instance_name: str) -> Dict:
        """Load settings for instance"""
        settings_file = f"settings_{instance_name}.json"
        defaults = {
            "autostart_game": {"auto_startup": False, "max_retries": 3, "enabled": True},
            "auto_gather": {"enabled": True, "check_interval": 30}
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                for key, value in defaults.items():
                    if key not in settings:
                        settings[key] = value
                    else:
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                return settings
        except Exception as e:
            print(f"[ModuleManager] Settings load error: {e}")
        
        return defaults