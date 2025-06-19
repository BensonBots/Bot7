"""
BENSON v2.0 - Module Manager with Fixed Auto-startup Logic
Handles module auto-startup and management across all instances with accurate status checking
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """Manages module auto-startup and coordination"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.autostart_modules = {}  # instance_name -> module
        self.settings_cache = {}  # instance_name -> settings
    
    def initialize_modules(self):
        """Initialize modules for all instances"""
        try:
            # Import AutoStartGame module
            from modules.autostart_game import AutoStartGameModule
            
            # Get all instances
            instances = self.app.instance_manager.get_instances()
            
            for instance in instances:
                instance_name = instance["name"]
                
                # Create AutoStartGame module for each instance
                autostart_module = AutoStartGameModule(
                    self.app.instance_manager,
                    console_callback=self.app.add_console_message
                )
                
                self.autostart_modules[instance_name] = autostart_module
                
                # Load settings for this instance
                settings = self._load_instance_settings(instance_name)
                self.settings_cache[instance_name] = settings
            
            self.app.add_console_message(f"🔧 Initialized modules for {len(instances)} instances")
            
        except ImportError as e:
            self.app.add_console_message(f"❌ Failed to import AutoStartGame module: {e}")
        except Exception as e:
            self.app.add_console_message(f"❌ Module initialization error: {e}")
    
    def check_auto_startup(self):
        """Check and start auto-startup modules after app initialization - only for running instances"""
        try:
            auto_start_candidates = []
            
            # Check which instances have auto-startup enabled AND are actually running
            for instance_name, settings in self.settings_cache.items():
                if (settings.get("autostart_game", {}).get("auto_startup", False) and 
                    settings.get("autostart_game", {}).get("enabled", True)):
                    
                    # Check if instance is actually running
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance and instance["status"] == "Running":
                        auto_start_candidates.append(instance_name)
                        self.app.add_console_message(f"🎮 {instance_name} is running and has auto-startup enabled")
                    else:
                        status = instance["status"] if instance else "Not Found"
                        self.app.add_console_message(f"⏸ {instance_name} has auto-startup enabled but is {status}")
            
            if auto_start_candidates:
                self.app.add_console_message(f"🚀 Auto-startup will run for: {', '.join(auto_start_candidates)}")
                
                # Start auto-startup after a delay to ensure everything is ready
                def delayed_auto_start():
                    time.sleep(5)  # Wait 5 seconds after app initialization
                    
                    for instance_name in auto_start_candidates:
                        # Double-check instance is still running before starting automation
                        instance = self.app.instance_manager.get_instance(instance_name)
                        if instance and instance["status"] == "Running":
                            self.app.after(0, lambda name=instance_name: self._auto_start_instance(name))
                        else:
                            self.app.after(0, lambda name=instance_name: 
                                         self.app.add_console_message(f"⏸ {name} no longer running, skipping auto-startup"))
                
                threading.Thread(target=delayed_auto_start, daemon=True).start()
            else:
                self.app.add_console_message("📱 No running instances configured for auto-startup")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Auto-startup check error: {e}")
    
    def _auto_start_instance(self, instance_name: str):
        """Auto-start modules for a specific instance - with additional safety checks"""
        try:
            if instance_name not in self.autostart_modules:
                self.app.add_console_message(f"❌ No AutoStartGame module for {instance_name}")
                return
            
            # Final check - make sure instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance or instance["status"] != "Running":
                self.app.add_console_message(f"⏸ {instance_name} is not running, aborting auto-startup")
                return
            
            autostart_module = self.autostart_modules[instance_name]
            settings = self.settings_cache.get(instance_name, {})
            
            if not autostart_module.is_available():
                missing_deps = autostart_module.get_missing_dependencies()
                self.app.add_console_message(f"❌ {instance_name} auto-startup failed: Missing {', '.join(missing_deps)}")
                return
            
            # Check if already running
            running_instances = autostart_module.get_running_instances()
            if instance_name in running_instances:
                self.app.add_console_message(f"⚠️ {instance_name} AutoStartGame already running")
                return
            
            # Get settings
            autostart_settings = settings.get("autostart_game", {})
            max_retries = autostart_settings.get("max_retries", 3)
            
            self.app.add_console_message(f"🎮 Auto-starting game for {instance_name} (instance is running)...")
            
            def on_complete(success):
                if success:
                    self.app.add_console_message(f"✅ {instance_name} auto-startup completed successfully")
                else:
                    self.app.add_console_message(f"❌ {instance_name} auto-startup failed")
            
            # Start the module
            success = autostart_module.start_auto_game(
                instance_name,
                max_retries=max_retries,
                on_complete=on_complete
            )
            
            if not success:
                self.app.add_console_message(f"❌ Failed to start AutoStartGame for {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ {instance_name} auto-startup error: {e}")
    
    def _load_instance_settings(self, instance_name: str) -> Dict:
        """Load settings for a specific instance"""
        settings_file = f"settings_{instance_name}.json"
        default_settings = {
            "autostart_game": {
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10,
                "enabled": True
            }
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                    else:
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                return settings
        except Exception as e:
            print(f"Error loading settings for {instance_name}: {e}")
        
        return default_settings
    
    def get_autostart_module(self, instance_name: str):
        """Get AutoStartGame module for an instance"""
        return self.autostart_modules.get(instance_name)
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            # Get current instances
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for instances that no longer exist
            modules_to_remove = []
            for instance_name in self.autostart_modules.keys():
                if instance_name not in current_names:
                    modules_to_remove.append(instance_name)
            
            for instance_name in modules_to_remove:
                if instance_name in self.autostart_modules:
                    del self.autostart_modules[instance_name]
                if instance_name in self.settings_cache:
                    del self.settings_cache[instance_name]
                self.app.add_console_message(f"🗑 Removed module for deleted instance: {instance_name}")
            
            # Add modules for new instances
            for instance in current_instances:
                instance_name = instance["name"]
                if instance_name not in self.autostart_modules:
                    try:
                        from modules.autostart_game import AutoStartGameModule
                        
                        autostart_module = AutoStartGameModule(
                            self.app.instance_manager,
                            console_callback=self.app.add_console_message
                        )
                        
                        self.autostart_modules[instance_name] = autostart_module
                        
                        # Load settings for new instance
                        settings = self._load_instance_settings(instance_name)
                        self.settings_cache[instance_name] = settings
                        
                        self.app.add_console_message(f"➕ Added module for new instance: {instance_name}")
                        
                    except ImportError as e:
                        self.app.add_console_message(f"❌ Failed to create module for {instance_name}: {e}")
            
            self.app.add_console_message(f"🔄 Refreshed modules for {len(current_instances)} instances")
            
        except Exception as e:
            self.app.add_console_message(f"❌ Module refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings for a specific instance"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            self.app.add_console_message(f"🔄 Reloaded settings for {instance_name}")
        except Exception as e:
            self.app.add_console_message(f"❌ Failed to reload settings for {instance_name}: {e}")
    
    def stop_all_modules(self):
        """Stop all running modules"""
        try:
            stopped_count = 0
            for instance_name, module in self.autostart_modules.items():
                running_instances = module.get_running_instances()
                if instance_name in running_instances:
                    if module.stop_auto_game(instance_name):
                        stopped_count += 1
            
            if stopped_count > 0:
                self.app.add_console_message(f"🛑 Stopped {stopped_count} running modules")
            else:
                self.app.add_console_message("🔍 No running modules to stop")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error stopping modules: {e}")
    
    def start_modules_for_running_instances(self):
        """Start modules for all running instances that have auto-startup enabled"""
        try:
            started_count = 0
            
            for instance_name, settings in self.settings_cache.items():
                if (settings.get("autostart_game", {}).get("auto_startup", False) and 
                    settings.get("autostart_game", {}).get("enabled", True)):
                    
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance and instance["status"] == "Running":
                        module = self.autostart_modules.get(instance_name)
                        if module:
                            running_instances = module.get_running_instances()
                            if instance_name not in running_instances:
                                # Start the module
                                autostart_settings = settings.get("autostart_game", {})
                                max_retries = autostart_settings.get("max_retries", 3)
                                
                                def on_complete(success, name=instance_name):
                                    if success:
                                        self.app.add_console_message(f"✅ {name} manual auto-startup completed")
                                    else:
                                        self.app.add_console_message(f"❌ {name} manual auto-startup failed")
                                
                                if module.start_auto_game(instance_name, max_retries=max_retries, on_complete=on_complete):
                                    started_count += 1
            
            if started_count > 0:
                self.app.add_console_message(f"🚀 Started modules for {started_count} running instances")
            else:
                self.app.add_console_message("📱 No eligible running instances for module startup")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting modules: {e}")
    
    def get_module_status(self) -> Dict:
        """Get status of all modules"""
        status = {
            "total_instances": len(self.autostart_modules),
            "auto_startup_enabled": 0,
            "currently_running": 0,
            "available_modules": 0,
            "running_instances": 0,
            "stopped_instances": 0
        }
        
        try:
            # Count instances by status
            instances = self.app.instance_manager.get_instances()
            for instance in instances:
                if instance["status"] == "Running":
                    status["running_instances"] += 1
                else:
                    status["stopped_instances"] += 1
            
            # Count module statuses
            for instance_name, module in self.autostart_modules.items():
                settings = self.settings_cache.get(instance_name, {})
                
                if settings.get("autostart_game", {}).get("auto_startup", False):
                    status["auto_startup_enabled"] += 1
                
                if module.is_available():
                    status["available_modules"] += 1
                
                running_instances = module.get_running_instances()
                if instance_name in running_instances:
                    status["currently_running"] += 1
        
        except Exception as e:
            self.app.add_console_message(f"❌ Error getting module status: {e}")
        
        return status
    
    def get_detailed_status(self) -> Dict:
        """Get detailed status for all instances and modules"""
        detailed_status = {
            "instances": [],
            "summary": self.get_module_status()
        }
        
        try:
            instances = self.app.instance_manager.get_instances()
            
            for instance in instances:
                instance_name = instance["name"]
                settings = self.settings_cache.get(instance_name, {})
                module = self.autostart_modules.get(instance_name)
                
                instance_info = {
                    "name": instance_name,
                    "status": instance["status"],
                    "cpu": instance["cpu"],
                    "memory": instance["memory"],
                    "auto_startup_enabled": settings.get("autostart_game", {}).get("auto_startup", False),
                    "module_enabled": settings.get("autostart_game", {}).get("enabled", True),
                    "module_available": module.is_available() if module else False,
                    "module_running": False,
                    "max_retries": settings.get("autostart_game", {}).get("max_retries", 3),
                    "retry_delay": settings.get("autostart_game", {}).get("retry_delay", 10)
                }
                
                if module:
                    running_instances = module.get_running_instances()
                    instance_info["module_running"] = instance_name in running_instances
                    
                    # Get current module status if running
                    if instance_info["module_running"]:
                        module_status = module.get_status(instance_name)
                        if module_status:
                            instance_info["module_status"] = module_status
                
                detailed_status["instances"].append(instance_info)
        
        except Exception as e:
            self.app.add_console_message(f"❌ Error getting detailed status: {e}")
        
        return detailed_status
    
    def enable_auto_startup_for_instance(self, instance_name: str, enabled: bool = True):
        """Enable or disable auto-startup for a specific instance"""
        try:
            if instance_name in self.settings_cache:
                self.settings_cache[instance_name]["autostart_game"]["auto_startup"] = enabled
                
                # Save to file
                settings_file = f"settings_{instance_name}.json"
                with open(settings_file, 'w') as f:
                    json.dump(self.settings_cache[instance_name], f, indent=2)
                
                status = "enabled" if enabled else "disabled"
                self.app.add_console_message(f"⚙ Auto-startup {status} for {instance_name}")
                return True
            else:
                self.app.add_console_message(f"❌ No settings found for {instance_name}")
                return False
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error setting auto-startup for {instance_name}: {e}")
            return False