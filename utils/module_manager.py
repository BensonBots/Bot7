"""
BENSON v2.0 - Fixed Module Manager
Fixed auto-startup logic and timing issues
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """Fixed module manager with proper auto-startup timing"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.autostart_modules = {}
        self.settings_cache = {}
        self.initialization_complete = False
        self.auto_startup_pending = False
    
    def initialize_modules(self):
        """Initialize modules for all instances"""
        try:
            from modules.autostart_game import AutoStartGameModule
            
            instances = self.app.instance_manager.get_instances()
            
            for instance in instances:
                instance_name = instance["name"]
                
                # Create module with proper error handling
                try:
                    autostart_module = AutoStartGameModule(
                        self.app.instance_manager,
                        console_callback=self.app.add_console_message
                    )
                    
                    self.autostart_modules[instance_name] = autostart_module
                    settings = self._load_instance_settings(instance_name)
                    self.settings_cache[instance_name] = settings
                    
                except Exception as e:
                    self.app.add_console_message(f"❌ Failed to initialize module for {instance_name}: {e}")
                    continue
            
            self.initialization_complete = True
            self.app.add_console_message(f"🔧 Initialized modules for {len(self.autostart_modules)} instances")
            
        except ImportError as e:
            self.app.add_console_message(f"❌ AutoStartGame module not available: {e}")
        except Exception as e:
            self.app.add_console_message(f"❌ Module initialization error: {e}")
    
    def check_auto_startup(self):
        """FIXED: Check and start auto-startup modules with proper timing"""
        if not self.initialization_complete:
            self.app.add_console_message("⏳ Module initialization not complete, deferring auto-startup...")
            self.auto_startup_pending = True
            # Try again in 2 seconds
            self.app.after(2000, self.check_auto_startup)
            return
        
        try:
            self.app.add_console_message("🔍 Checking auto-startup configuration...")
            
            # Force refresh instance statuses first
            self.app.instance_manager.update_instance_statuses()
            time.sleep(0.5)  # Small delay for status update
            
            auto_start_candidates = []
            
            for instance_name, settings in self.settings_cache.items():
                autostart_settings = settings.get("autostart_game", {})
                
                if (autostart_settings.get("auto_startup", False) and 
                    autostart_settings.get("enabled", True)):
                    
                    # Double-check instance status
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance:
                        real_status = self.app.instance_manager._get_real_instance_status(
                            instance["index"], instance["name"]
                        )
                        
                        if real_status == "Running":
                            auto_start_candidates.append(instance_name)
                            self.app.add_console_message(f"✅ {instance_name} is running and configured for auto-startup")
                        else:
                            self.app.add_console_message(f"⏸ {instance_name} has auto-startup enabled but is {real_status}")
                    else:
                        self.app.add_console_message(f"❌ {instance_name} not found in instance list")
            
            if auto_start_candidates:
                self.app.add_console_message(f"🚀 Starting auto-startup for: {', '.join(auto_start_candidates)}")
                
                # Start auto-startup with proper delay
                def delayed_start():
                    # Wait for everything to stabilize
                    time.sleep(3)
                    
                    for instance_name in auto_start_candidates:
                        # Final status check before starting
                        instance = self.app.instance_manager.get_instance(instance_name)
                        if instance:
                            current_status = self.app.instance_manager._get_real_instance_status(
                                instance["index"], instance["name"]
                            )
                            
                            if current_status == "Running":
                                # Schedule on main thread
                                self.app.after(0, lambda name=instance_name: self._auto_start_instance(name))
                            else:
                                self.app.after(0, lambda name=instance_name, status=current_status: 
                                             self.app.add_console_message(f"⏸ {name} status changed to {status}, skipping auto-startup"))
                        
                        time.sleep(1)  # Stagger starts
                
                threading.Thread(target=delayed_start, daemon=True).start()
            else:
                self.app.add_console_message("📱 No running instances configured for auto-startup")
            
            self.auto_startup_pending = False
                
        except Exception as e:
            self.app.add_console_message(f"❌ Auto-startup check error: {e}")
            self.auto_startup_pending = False
    
    def _auto_start_instance(self, instance_name: str):
        """FIXED: Auto-start with better error handling and status checks"""
        try:
            if instance_name not in self.autostart_modules:
                self.app.add_console_message(f"❌ No AutoStartGame module for {instance_name}")
                return
            
            # Triple check - make sure instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance:
                self.app.add_console_message(f"❌ {instance_name} not found, aborting auto-startup")
                return
            
            # Check real status one more time
            real_status = self.app.instance_manager._get_real_instance_status(
                instance["index"], instance["name"]
            )
            
            if real_status != "Running":
                self.app.add_console_message(f"⏸ {instance_name} is {real_status}, aborting auto-startup")
                return
            
            autostart_module = self.autostart_modules[instance_name]
            
            # Check if module is available
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
            settings = self.settings_cache.get(instance_name, {})
            autostart_settings = settings.get("autostart_game", {})
            max_retries = autostart_settings.get("max_retries", 3)
            
            self.app.add_console_message(f"🎮 Auto-starting AutoStartGame for {instance_name}...")
            
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
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            modules_to_remove = [name for name in self.autostart_modules.keys() if name not in current_names]
            
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
            instances = self.app.instance_manager.get_instances()
            for instance in instances:
                if instance["status"] == "Running":
                    status["running_instances"] += 1
                else:
                    status["stopped_instances"] += 1
            
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