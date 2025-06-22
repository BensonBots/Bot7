"""
BENSON v2.0 - Fixed Module Manager 
Fixed AutoStart detection with proper timing and status checking
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """Fixed module manager with improved AutoStart detection"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_managers = {}  # instance_name -> ConcurrentModuleManager
        self.settings_cache = {}
        self.initialization_complete = False
        
        # Status monitoring
        self.status_monitor_running = False
        self.status_monitor_thread = None
        self.status_monitor_stop = threading.Event()
    
    def initialize_modules(self):
        """Initialize all modules for all instances"""
        try:
            # Import all module classes
            from modules.autostart_game import AutoStartGameModule
            from modules.base_module import ConcurrentModuleManager
            
            # Try to import optional modules
            AutoGatherModule = None
            
            try:
                from modules.auto_gather import AutoGatherModule
            except ImportError:
                self.app.add_console_message("⚠️ AutoGather module not available")
            
            instances = self.app.instance_manager.get_instances()
            
            for instance in instances:
                instance_name = instance["name"]
                
                # Create concurrent module manager for this instance
                manager = ConcurrentModuleManager(
                    instance_name=instance_name,
                    instance_manager=self.app.instance_manager,
                    console_callback=self.app.add_console_message
                )
                
                # Load settings for this instance
                settings = self._load_instance_settings(instance_name)
                self.settings_cache[instance_name] = settings
                
                # Register AutoStartGame (always required)
                autostart_config = settings.get("autostart_game", {})
                autostart_config["enabled"] = True  # Always enabled
                manager.register_module(AutoStartGameModule, **autostart_config)
                
                # Register AutoGather if available and enabled
                if AutoGatherModule:
                    gather_config = settings.get("auto_gather", {})
                    if gather_config.get("enabled", True):
                        manager.register_module(AutoGatherModule, **gather_config)
                
                self.instance_managers[instance_name] = manager
                
                self.app.add_console_message(f"🔧 Initialized module system for {instance_name}")
            
            self.initialization_complete = True
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_managers)} instances")
            
            # Start status monitoring
            self._start_status_monitoring()
            
        except ImportError as e:
            self.app.add_console_message(f"❌ Module import error: {e}")
        except Exception as e:
            self.app.add_console_message(f"❌ Module initialization error: {e}")
    
    def check_auto_startup_initial(self):
        """Initial auto-startup check for all instances"""
        if not self.initialization_complete:
            self.app.add_console_message("⏳ Module system not ready, deferring auto-startup...")
            self.app.after(2000, self.check_auto_startup_initial)
            return
        
        try:
            self.app.add_console_message("🔍 Initial module auto-startup check...")
            
            # Force refresh instance statuses
            self.app.instance_manager.update_instance_statuses()
            time.sleep(0.5)
            
            auto_start_candidates = []
            
            for instance_name, manager in self.instance_managers.items():
                settings = self.settings_cache.get(instance_name, {})
                autostart_settings = settings.get("autostart_game", {})
                
                if autostart_settings.get("auto_startup", False):
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance and instance["status"] == "Running":
                        auto_start_candidates.append(instance_name)
                        self.app.add_console_message(f"✅ {instance_name} ready for module auto-startup")
            
            if auto_start_candidates:
                self.app.add_console_message(f"🚀 Starting module systems: {', '.join(auto_start_candidates)}")
                
                for instance_name in auto_start_candidates:
                    # Stagger the starts
                    delay = auto_start_candidates.index(instance_name) * 3000
                    self.app.after(delay, lambda name=instance_name: self._start_all_modules_for_instance(name))
            else:
                self.app.add_console_message("📱 No running instances configured for module auto-startup")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Initial module auto-startup error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """FIXED: Trigger auto-startup with better timing and detection"""
        self.app.add_console_message(f"🎯 Module auto-startup triggered for {instance_name}")
        
        # FIXED: Add longer delay and multiple checks to ensure instance is fully started
        self.app.after(8000, lambda: self._check_and_start_modules(instance_name))
    
    def _check_and_start_modules(self, instance_name: str):
        """FIXED: Check instance status multiple times before starting modules"""
        def check_worker():
            try:
                max_attempts = 5
                check_delay = 2  # seconds between checks
                
                for attempt in range(max_attempts):
                    self.app.add_console_message(f"🔍 Checking {instance_name} status (attempt {attempt + 1}/{max_attempts})...")
                    
                    # Force refresh instance status
                    self.app.instance_manager.update_instance_statuses()
                    time.sleep(1)  # Wait for status update
                    
                    # Check current status
                    instance = self.app.instance_manager.get_instance(instance_name)
                    
                    if instance:
                        current_status = instance["status"]
                        self.app.add_console_message(f"📊 {instance_name} current status: {current_status}")
                        
                        if current_status == "Running":
                            # Instance is running, proceed with module startup
                            self.app.add_console_message(f"✅ {instance_name} confirmed running, starting modules...")
                            self.app.after(0, lambda: self._start_all_modules_for_instance(instance_name))
                            return
                        elif current_status in ["Starting", "Stopping"]:
                            # Instance is transitioning, wait longer
                            self.app.add_console_message(f"⏳ {instance_name} is {current_status.lower()}, waiting...")
                            time.sleep(check_delay * 2)  # Wait longer for transitioning states
                        else:
                            # Instance stopped or error
                            self.app.add_console_message(f"❌ {instance_name} status is {current_status}, waiting...")
                            time.sleep(check_delay)
                    else:
                        self.app.add_console_message(f"❌ Could not find instance {instance_name}")
                        time.sleep(check_delay)
                
                # All attempts failed
                self.app.add_console_message(f"⏸ {instance_name} did not reach running state after {max_attempts} attempts")
                
            except Exception as e:
                self.app.add_console_message(f"❌ Error checking {instance_name} status: {e}")
        
        # Run in background thread
        threading.Thread(target=check_worker, daemon=True, name=f"StatusCheck-{instance_name}").start()
    
    def _start_all_modules_for_instance(self, instance_name: str):
        """Start all enabled modules for an instance"""
        try:
            if instance_name not in self.instance_managers:
                self.app.add_console_message(f"❌ No module manager for {instance_name}")
                return
            
            # FINAL verification that instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance or instance["status"] != "Running":
                self.app.add_console_message(f"⏸ {instance_name} not running during final check, aborting module startup")
                return
            
            manager = self.instance_managers[instance_name]
            settings = self.settings_cache.get(instance_name, {})
            
            # Check if auto-startup is enabled
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                self.app.add_console_message(f"⏸ Auto-startup not enabled for {instance_name}")
                return
            
            self.app.add_console_message(f"🎮 Starting module system for {instance_name}...")
            
            # Start all enabled modules
            success = manager.start_all_enabled()
            
            if success:
                self.app.add_console_message(f"✅ Module system started for {instance_name}")
                
                # Give the AutoStart module a moment to initialize, then trigger it
                self.app.after(2000, lambda: self._trigger_autostart_module(instance_name))
            else:
                self.app.add_console_message(f"❌ Failed to start module system for {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting modules for {instance_name}: {e}")
    
    def _trigger_autostart_module(self, instance_name: str):
        """FIXED: Manually trigger the AutoStart module"""
        try:
            if instance_name not in self.instance_managers:
                return
            
            manager = self.instance_managers[instance_name]
            
            # Get the AutoStartGame module
            status_report = manager.get_status_report()
            
            if "AutoStartGameModule" in status_report.get("module_statuses", {}):
                module_status = status_report["module_statuses"]["AutoStartGameModule"]
                
                if module_status.get("status") == "running":
                    self.app.add_console_message(f"🚀 Triggering AutoStart for {instance_name}...")
                    
                    # Try to get the actual module instance and start it
                    autostart_module = manager.modules.get("AutoStartGameModule")
                    if autostart_module and hasattr(autostart_module, 'start_auto_game'):
                        # Start the auto game process
                        success = autostart_module.start_auto_game(
                            instance_name=instance_name,
                            max_retries=3,
                            on_complete=lambda success: self._on_autostart_complete(instance_name, success)
                        )
                        
                        if success:
                            self.app.add_console_message(f"✅ AutoStart initiated for {instance_name}")
                        else:
                            self.app.add_console_message(f"❌ Failed to initiate AutoStart for {instance_name}")
                    else:
                        self.app.add_console_message(f"❌ AutoStart module not available for {instance_name}")
                else:
                    self.app.add_console_message(f"❌ AutoStart module not running for {instance_name}")
            else:
                self.app.add_console_message(f"❌ AutoStart module not found for {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error triggering AutoStart for {instance_name}: {e}")
    
    def _on_autostart_complete(self, instance_name: str, success: bool):
        """Handle AutoStart completion"""
        if success:
            self.app.add_console_message(f"🎉 AutoStart completed successfully for {instance_name}")
        else:
            self.app.add_console_message(f"❌ AutoStart failed for {instance_name}")
    
    def _start_status_monitoring(self):
        """Start background status monitoring"""
        if self.status_monitor_running:
            return
            
        self.status_monitor_running = True
        
        def monitor_loop():
            while self.status_monitor_running:
                try:
                    time.sleep(15)  # Check every 15 seconds
                    
                    if not self.initialization_complete:
                        continue
                    
                    # Monitor each instance's modules
                    current_instances = self.app.instance_manager.get_instances()
                    
                    for instance in current_instances:
                        instance_name = instance["name"]
                        current_status = instance["status"]
                        
                        if instance_name in self.instance_managers:
                            manager = self.instance_managers[instance_name]
                            
                            # If instance became running and modules aren't running
                            if current_status == "Running":
                                status_report = manager.get_status_report()
                                running_modules = status_report.get("running_modules", 0)
                                
                                # If no modules running but should be
                                if running_modules == 0:
                                    settings = self.settings_cache.get(instance_name, {})
                                    if settings.get("autostart_game", {}).get("auto_startup", False):
                                        self.app.add_console_message(f"🔄 Restarting modules for {instance_name}")
                                        self.app.after(0, lambda name=instance_name: self._start_all_modules_for_instance(name))
                            
                            # If instance stopped, stop modules
                            elif current_status != "Running":
                                status_report = manager.get_status_report()
                                if status_report.get("running_modules", 0) > 0:
                                    self.app.add_console_message(f"⏹ Stopping modules for stopped instance: {instance_name}")
                                    manager.stop_all()
                    
                except Exception as e:
                    print(f"[ModuleManager] Status monitor error: {e}")
                    
        self.status_monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="ModuleStatusMonitor")
        self.status_monitor_thread.start()
        self.app.add_console_message("🔍 Started module status monitoring")
    
    def _load_instance_settings(self, instance_name: str) -> Dict:
        """Load settings for a specific instance"""
        settings_file = f"settings_{instance_name}.json"
        default_settings = {
            "autostart_game": {
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10,
                "enabled": True
            },
            "auto_gather": {
                "enabled": True,
                "check_interval": 30,
                "resource_types": ["food", "wood", "iron", "stone"],
                "min_march_capacity": 100000,
                "max_concurrent_gathers": 5
            },
            "march_assignment": {
                "enabled": True,
                "unlocked_queues": 2,
                "queue_assignments": {"1": "AutoGather", "2": "AutoGather"}
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
    
    def get_module_manager(self, instance_name: str):
        """Get module manager for specific instance"""
        return self.instance_managers.get(instance_name)
    
    def get_instance_status(self, instance_name: str) -> Dict:
        """Get comprehensive status for an instance"""
        if instance_name not in self.instance_managers:
            return {"error": "Instance not found"}
        
        manager = self.instance_managers[instance_name]
        return manager.get_status_report()
    
    def get_all_status(self) -> Dict:
        """Get status for all instances"""
        status = {
            "total_instances": len(self.instance_managers),
            "initialization_complete": self.initialization_complete,
            "status_monitoring": self.status_monitor_running,
            "instances": {}
        }
        
        for instance_name, manager in self.instance_managers.items():
            status["instances"][instance_name] = manager.get_status_report()
        
        return status
    
    def start_modules_for_instance(self, instance_name: str) -> bool:
        """Manually start modules for an instance"""
        if instance_name not in self.instance_managers:
            return False
        
        manager = self.instance_managers[instance_name]
        return manager.start_all_enabled()
    
    def stop_modules_for_instance(self, instance_name: str) -> bool:
        """Stop modules for an instance"""
        if instance_name not in self.instance_managers:
            return False
        
        manager = self.instance_managers[instance_name]
        return manager.stop_all()
    
    def start_specific_module(self, instance_name: str, module_name: str) -> bool:
        """Start a specific module for an instance"""
        if instance_name not in self.instance_managers:
            return False
        
        manager = self.instance_managers[instance_name]
        return manager.start_module(module_name)
    
    def stop_specific_module(self, instance_name: str, module_name: str) -> bool:
        """Stop a specific module for an instance"""
        if instance_name not in self.instance_managers:
            return False
        
        manager = self.instance_managers[instance_name]
        return manager.stop_module(module_name)
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove managers for deleted instances
            managers_to_remove = [name for name in self.instance_managers.keys() if name not in current_names]
            
            for instance_name in managers_to_remove:
                if instance_name in self.instance_managers:
                    self.instance_managers[instance_name].stop_all()
                    del self.instance_managers[instance_name]
                if instance_name in self.settings_cache:
                    del self.settings_cache[instance_name]
                self.app.add_console_message(f"🗑 Removed module system for deleted instance: {instance_name}")
            
            # Add managers for new instances
            for instance in current_instances:
                instance_name = instance["name"]
                if instance_name not in self.instance_managers:
                    # Initialize for new instance (simplified version)
                    try:
                        from modules.base_module import ConcurrentModuleManager
                        from modules.autostart_game import AutoStartGameModule
                        
                        manager = ConcurrentModuleManager(
                            instance_name=instance_name,
                            instance_manager=self.app.instance_manager,
                            console_callback=self.app.add_console_message
                        )
                        
                        # Load settings and register basic modules
                        settings = self._load_instance_settings(instance_name)
                        self.settings_cache[instance_name] = settings
                        
                        # Register at least AutoStartGame
                        autostart_config = settings.get("autostart_game", {})
                        manager.register_module(AutoStartGameModule, **autostart_config)
                        
                        self.instance_managers[instance_name] = manager
                        
                        self.app.add_console_message(f"➕ Added module system for new instance: {instance_name}")
                        
                    except Exception as e:
                        self.app.add_console_message(f"❌ Failed to create module system for {instance_name}: {e}")
            
            self.app.add_console_message(f"🔄 Refreshed module systems for {len(current_instances)} instances")
            
        except Exception as e:
            self.app.add_console_message(f"❌ Module refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings for a specific instance"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            self.app.add_console_message(f"🔄 Reloaded module settings for {instance_name}")
        except Exception as e:
            self.app.add_console_message(f"❌ Failed to reload settings for {instance_name}: {e}")
    
    def stop_status_monitoring(self):
        """Stop status monitoring (for cleanup)"""
        self.status_monitor_running = False
        if self.status_monitor_thread:
            self.status_monitor_thread.join(timeout=5)
    
    def stop_all_modules(self):
        """Stop all modules for all instances"""
        for instance_name, manager in self.instance_managers.items():
            try:
                manager.stop_all()
            except Exception as e:
                print(f"Error stopping modules for {instance_name}: {e}")
        
        self.stop_status_monitoring()
    
    # Legacy compatibility methods
    def check_auto_startup(self):
        """Legacy method - redirect to new module system"""
        self.check_auto_startup_initial()
    
    def get_autostart_module(self, instance_name: str):
        """Legacy method - get AutoStartGame module"""
        if instance_name in self.instance_managers:
            manager = self.instance_managers[instance_name]
            return manager.modules.get("AutoStartGameModule")
        return None
    
    def get_module_status(self) -> Dict:
        """Legacy method - get overall module status"""
        total_instances = len(self.instance_managers)
        total_modules = 0
        running_modules = 0
        auto_startup_enabled = 0
        
        for instance_name, manager in self.instance_managers.items():
            status_report = manager.get_status_report()
            total_modules += status_report.get("total_modules", 0)
            running_modules += status_report.get("running_modules", 0)
            
            settings = self.settings_cache.get(instance_name, {})
            if settings.get("autostart_game", {}).get("auto_startup", False):
                auto_startup_enabled += 1
        
        return {
            "total_instances": total_instances,
            "total_modules": total_modules,
            "running_modules": running_modules,
            "auto_startup_enabled": auto_startup_enabled,
            "initialization_complete": self.initialization_complete,
            "status_monitoring": self.status_monitor_running
        }