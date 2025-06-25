"""
BENSON v2.0 - Optimized Module Manager - 50% Size Reduction
Streamlined version with essential functionality maintained
"""

import os
import json
import threading
import time
from typing import Dict


class ModuleManager:
    """Optimized module manager with proper auto-triggers"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_modules = {}
        self.settings_cache = {}
        self.initialization_complete = False
        self.autostart_completed = {}
        self.running_modules = {}
        
        print("[ModuleManager] Initializing optimized module system...")
        self._initialize_modules()
        self._start_status_updates()
    
    def _initialize_modules(self):
        """Initialize modules for all instances"""
        try:
            # Import required modules
            try:
                from modules.autostart_game import AutoStartGameModule
                print("[ModuleManager] ✅ AutoStartGame imported")
            except ImportError as e:
                print(f"[ModuleManager] ❌ AutoStartGame import failed: {e}")
                return
            
            try:
                from modules.auto_gather import AutoGatherModule
                print("[ModuleManager] ✅ AutoGather imported")
            except ImportError as e:
                print(f"[ModuleManager] ❌ AutoGather import failed: {e}")
                AutoGatherModule = None
            
            # Create modules for each instance
            instances = self.app.instance_manager.get_instances()
            for instance in instances:
                self._create_modules_for_instance(instance["name"], AutoStartGameModule, AutoGatherModule)
            
            self.initialization_complete = True
            print(f"[ModuleManager] ✅ Initialization complete for {len(instances)} instances")
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Initialization error: {e}")
            self.initialization_complete = True
    
    def _create_modules_for_instance(self, instance_name: str, AutoStartGameModule, AutoGatherModule=None):
        """Create modules for a single instance"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            self.instance_modules[instance_name] = {}
            self.running_modules[instance_name] = {}
            
            # Create AutoStart module
            autostart_module = AutoStartGameModule(
                instance_name=instance_name,
                shared_resources=self.app.instance_manager,
                console_callback=self.app.add_console_message
            )
            self.instance_modules[instance_name]["AutoStartGame"] = autostart_module
            self.running_modules[instance_name]["AutoStartGame"] = False
            
            # Create AutoGather if available
            if AutoGatherModule and settings.get("auto_gather", {}).get("enabled", True):
                gather_module = AutoGatherModule(
                    instance_name=instance_name,
                    shared_resources=self.app.instance_manager,
                    console_callback=self.app.add_console_message
                )
                self.instance_modules[instance_name]["AutoGather"] = gather_module
                self.running_modules[instance_name]["AutoGather"] = False
            
            print(f"[ModuleManager] ✅ Created modules for {instance_name}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Error creating modules for {instance_name}: {e}")
    
    def _start_status_updates(self):
        """Start status update loop"""
        def update_loop():
            while hasattr(self, 'app') and self.app:
                try:
                    self.app.instance_manager.update_instance_statuses()
                    self._update_gui_cards()
                    time.sleep(10)
                except Exception as e:
                    print(f"[ModuleManager] Status update error: {e}")
                    time.sleep(10)
        
        threading.Thread(target=update_loop, daemon=True, name="StatusUpdater").start()
        print("[ModuleManager] ✅ Status update loop started")
    
    def _update_gui_cards(self):
        """Update GUI cards with current status"""
        try:
            if not hasattr(self.app, 'instance_cards'):
                return
            
            instances = self.app.instance_manager.get_instances()
            status_map = {inst["name"]: inst["status"] for inst in instances}
            
            for card in self.app.instance_cards:
                if hasattr(card, 'name') and hasattr(card, 'update_status'):
                    current_status = status_map.get(card.name)
                    if current_status and current_status != card.status:
                        self.app.after(0, lambda c=card, s=current_status: c.update_status(s))
        except Exception as e:
            print(f"[ModuleManager] GUI update error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """Trigger auto-startup when instance starts"""
        if not self.initialization_complete:
            return
        
        if self._is_autostart_recently_completed(instance_name):
            print(f"[ModuleManager] AutoStart recently completed for {instance_name}")
            return
        
        print(f"[ModuleManager] 🎯 Auto-startup triggered for {instance_name}")
        self.app.after(8000, lambda: self._start_autostart_for_instance(instance_name))
    
    def _start_autostart_for_instance(self, instance_name: str):
        """Start AutoStart for an instance"""
        try:
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                print(f"[ModuleManager] Auto-startup not enabled for {instance_name}")
                return
            
            if instance_name not in self.instance_modules:
                return
            
            autostart_module = self.instance_modules[instance_name].get("AutoStartGame")
            if not autostart_module:
                return
            
            self._verify_and_start_autostart(instance_name, autostart_module, settings)
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Error in AutoStart process: {e}")
    
    def _verify_and_start_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Verify instance is ready and start AutoStart"""
        def check_ready(attempt=1):
            try:
                self.app.instance_manager.update_instance_statuses()
                instance = self.app.instance_manager.get_instance(instance_name)
                
                if not instance:
                    if attempt < 5:
                        self.app.after(2000, lambda: check_ready(attempt + 1))
                    return
                
                if instance["status"] == "Running":
                    self._actually_start_autostart(instance_name, autostart_module, settings)
                elif instance["status"] in ["Starting", "Connecting"] and attempt < 10:
                    self.app.after(2000, lambda: check_ready(attempt + 1))
                    
            except Exception as e:
                print(f"[ModuleManager] Error checking {instance_name}: {e}")
        
        check_ready()
    
    def _actually_start_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Start the AutoStart module"""
        try:
            print(f"[ModuleManager] 🚀 Starting AutoStart for {instance_name}")
            self.app.add_console_message(f"🎮 Starting module system for {instance_name}...")
            
            def on_complete(success: bool):
                if success:
                    print(f"[ModuleManager] ✅ AutoStart completed for {instance_name}")
                    self.app.add_console_message(f"✅ AutoStart completed for {instance_name}")
                    self._mark_autostart_completed(instance_name)
                    # FIXED: Auto-start AutoGather
                    self.app.after(3000, lambda: self._auto_start_autogather(instance_name))
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
                self.app.add_console_message(f"✅ AutoStart initiated for {instance_name}")
            else:
                self.app.add_console_message(f"❌ Failed to initiate AutoStart for {instance_name}")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ Error starting AutoStart: {e}")
    
    def _auto_start_autogather(self, instance_name: str):
        """FIXED: Auto-start AutoGather after AutoStart completes"""
        try:
            if instance_name not in self.instance_modules:
                return
            
            if "AutoGather" not in self.instance_modules[instance_name]:
                self.app.add_console_message(f"⚠️ AutoGather not available for {instance_name}")
                return
            
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("auto_gather", {}).get("enabled", True):
                return
            
            if self.running_modules[instance_name].get("AutoGather", False):
                return
            
            print(f"[ModuleManager] 🌾 Auto-starting AutoGather for {instance_name}")
            self.app.add_console_message(f"🌾 Auto-starting AutoGather for {instance_name}...")
            
            gather_module = self.instance_modules[instance_name]["AutoGather"]
            success = gather_module.start()
            
            if success:
                self.running_modules[instance_name]["AutoGather"] = True
                self.app.add_console_message(f"✅ Auto-started AutoGather for {instance_name}")
            else:
                self.app.add_console_message(f"❌ Failed to start AutoGather for {instance_name}")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ Error auto-starting AutoGather: {e}")
    
    def _is_autostart_recently_completed(self, instance_name: str) -> bool:
        """Check if AutoStart completed recently"""
        if instance_name not in self.autostart_completed:
            return False
        return time.time() - self.autostart_completed[instance_name] < 300
    
    def _mark_autostart_completed(self, instance_name: str):
        """Mark AutoStart as completed"""
        self.autostart_completed[instance_name] = time.time()
    
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
            
            if instance_name in self.autostart_completed:
                del self.autostart_completed[instance_name]
            
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
                        self._create_modules_for_instance(instance["name"], AutoStartGameModule, AutoGatherModule)
                    except Exception as e:
                        print(f"[ModuleManager] ❌ Failed to create modules: {e}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Module refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings when changed"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
        except Exception as e:
            print(f"[ModuleManager] ❌ Failed to reload settings: {e}")
    
    def _load_instance_settings(self, instance_name: str) -> Dict:
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
            print(f"[ModuleManager] Error loading settings: {e}")
        
        return defaults
    
    def stop_all_modules(self):
        """Stop all modules"""
        for instance_name in list(self.instance_modules.keys()):
            self.cleanup_for_stopped_instance(instance_name)