"""
BENSON v2.0 - COMPLETE FIXED Module Manager with Auto-Module Starting
Now properly starts all enabled modules after AutoStart completes
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """COMPLETE FIXED: Module manager that starts all enabled modules after AutoStart"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_modules = {}  # instance_name -> {module_name: module_instance}
        self.settings_cache = {}
        self.initialization_complete = False
        
        # Status monitoring
        self.status_monitor_running = False
        self.status_monitor_thread = None
        self.status_monitor_stop = threading.Event()
        
        # Track AutoStart completion to prevent duplicates
        self.autostart_completed = {}  # instance_name -> completion_time
        
        # NEW: Track which modules are running for each instance
        self.running_modules = {}  # instance_name -> {module_name: True/False}
    
    def initialize_modules(self):
        """Initialize all modules for all instances"""
        try:
            # Import module classes
            from modules.autostart_game import AutoStartGameModule
            
            # Try to import optional modules
            AutoGatherModule = None
            try:
                from modules.auto_gather import AutoGatherModule
            except ImportError:
                self.app.add_console_message("⚠️ AutoGather module not available")
            
            instances = self.app.instance_manager.get_instances()
            
            for instance in instances:
                instance_name = instance["name"]
                
                # Load settings for this instance
                settings = self._load_instance_settings(instance_name)
                self.settings_cache[instance_name] = settings
                
                # Initialize module container for this instance
                self.instance_modules[instance_name] = {}
                self.running_modules[instance_name] = {}
                
                # Create AutoStartGame module (always enabled)
                autostart_config = settings.get("autostart_game", {})
                autostart_module = AutoStartGameModule(
                    instance_name=instance_name,
                    shared_resources=self.app.instance_manager,
                    console_callback=self.app.add_console_message
                )
                self.instance_modules[instance_name]["AutoStartGameModule"] = autostart_module
                self.running_modules[instance_name]["AutoStartGameModule"] = False
                
                # Create AutoGather module if available and enabled
                if AutoGatherModule and settings.get("auto_gather", {}).get("enabled", True):
                    gather_module = AutoGatherModule(
                        instance_name=instance_name,
                        shared_resources=self.app.instance_manager,
                        console_callback=self.app.add_console_message
                    )
                    self.instance_modules[instance_name]["AutoGatherModule"] = gather_module
                    self.running_modules[instance_name]["AutoGatherModule"] = False
                    self.app.add_console_message(f"✅ AutoGather module initialized for {instance_name}")
                
                self.app.add_console_message(f"🔧 Initialized module system for {instance_name}")
            
            self.initialization_complete = True
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
            # Start SMART status monitoring
            self._start_smart_status_monitoring()
            
        except Exception as e:
            self.app.add_console_message(f"❌ Module initialization error: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            for instance_name in self.instance_modules.keys():
                settings = self.settings_cache.get(instance_name, {})
                autostart_settings = settings.get("autostart_game", {})
                
                if autostart_settings.get("auto_startup", False):
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance and instance["status"] == "Running":
                        auto_start_candidates.append(instance_name)
                        self.app.add_console_message(f"✅ {instance_name} ready for module auto-startup")
            
            if auto_start_candidates:
                self.app.add_console_message(f"🚀 Starting AutoStart for: {', '.join(auto_start_candidates)}")
                
                for instance_name in auto_start_candidates:
                    # Stagger the starts
                    delay = auto_start_candidates.index(instance_name) * 3000
                    self.app.after(delay, lambda name=instance_name: self._trigger_autostart_for_instance(name))
            else:
                self.app.add_console_message("📱 No running instances configured for module auto-startup")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Initial module auto-startup error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """Trigger auto-startup with smart duplicate prevention"""
        # SMART CHECK: Don't trigger if already completed recently
        if self._is_autostart_recently_completed(instance_name):
            self.app.add_console_message(f"⏸ AutoStart recently completed for {instance_name}, skipping")
            return
        
        self.app.add_console_message(f"🎯 Module auto-startup triggered for {instance_name}")
        
        # Add delay and multiple checks to ensure instance is fully started
        self.app.after(8000, lambda: self._check_and_start_autostart(instance_name))
    
    def _is_autostart_recently_completed(self, instance_name: str) -> bool:
        """Check if AutoStart was completed recently for this instance"""
        if instance_name not in self.autostart_completed:
            return False
        
        last_completion = self.autostart_completed[instance_name]
        time_since = (time.time() - last_completion)
        
        # Don't restart within 5 minutes
        return time_since < 300
    
    def _mark_autostart_completed(self, instance_name: str):
        """Mark AutoStart as completed for this instance"""
        self.autostart_completed[instance_name] = time.time()
        self.running_modules[instance_name]["AutoStartGameModule"] = True
        self.app.add_console_message(f"✅ Marked AutoStart complete for {instance_name}")
        
        # NEW: Start other enabled modules after AutoStart completes
        self._start_other_modules_after_autostart(instance_name)
    
    def _start_other_modules_after_autostart(self, instance_name: str):
        """NEW: Start other enabled modules after AutoStart completes successfully"""
        try:
            if instance_name not in self.instance_modules:
                return
            
            settings = self.settings_cache.get(instance_name, {})
            modules_to_start = []
            
            # Check AutoGather
            if ("AutoGatherModule" in self.instance_modules[instance_name] and 
                settings.get("auto_gather", {}).get("enabled", True) and
                not self.running_modules[instance_name].get("AutoGatherModule", False)):
                modules_to_start.append("AutoGatherModule")
            
            # Add other modules here as they're implemented
            # if ("AutoTrainModule" in self.instance_modules[instance_name] and 
            #     settings.get("auto_train", {}).get("enabled", True)):
            #     modules_to_start.append("AutoTrainModule")
            
            if modules_to_start:
                self.app.add_console_message(f"🎮 Starting additional modules for {instance_name}: {', '.join(modules_to_start)}")
                
                for module_name in modules_to_start:
                    # Add a small delay between module starts
                    delay = modules_to_start.index(module_name) * 1000
                    self.app.after(delay, lambda name=instance_name, mod=module_name: self._start_module_for_instance(name, mod))
            else:
                self.app.add_console_message(f"ℹ️ No additional modules to start for {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting additional modules for {instance_name}: {e}")
    
    def _start_module_for_instance(self, instance_name: str, module_name: str):
        """Start a specific module for an instance"""
        try:
            if (instance_name not in self.instance_modules or 
                module_name not in self.instance_modules[instance_name]):
                self.app.add_console_message(f"❌ Module {module_name} not found for {instance_name}")
                return False
            
            module = self.instance_modules[instance_name][module_name]
            
            # Different modules have different start methods
            if module_name == "AutoGatherModule":
                # AutoGather modules use the base module start method
                if hasattr(module, 'start'):
                    self.app.add_console_message(f"🚀 Starting {module_name} for {instance_name}...")
                    success = module.start()
                    if success:
                        self.running_modules[instance_name][module_name] = True
                        self.app.add_console_message(f"✅ Started {module_name} for {instance_name}")
                        return True
                    else:
                        self.app.add_console_message(f"❌ Failed to start {module_name} for {instance_name}")
                        return False
                else:
                    self.app.add_console_message(f"⚠️ {module_name} doesn't have start method")
                    return False
            
            # Add other module types as needed
            elif module_name == "AutoTrainModule":
                if hasattr(module, 'start'):
                    success = module.start()
                    if success:
                        self.running_modules[instance_name][module_name] = True
                        self.app.add_console_message(f"✅ Started {module_name} for {instance_name}")
                        return True
                    else:
                        self.app.add_console_message(f"❌ Failed to start {module_name} for {instance_name}")
                        return False
                else:
                    self.app.add_console_message(f"⚠️ {module_name} doesn't have start method")
                    return False
            
            else:
                self.app.add_console_message(f"⚠️ Unknown module type: {module_name}")
                return False
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting {module_name} for {instance_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _stop_modules_for_instance(self, instance_name: str):
        """Stop all running modules for a specific instance"""
        try:
            if instance_name not in self.instance_modules:
                return
            
            modules = self.instance_modules[instance_name]
            stopped_modules = []
            
            for module_name, module in modules.items():
                try:
                    # Stop AutoStartGame modules
                    if hasattr(module, 'stop_auto_game'):
                        if module.get_running_instances():  # Only if actually running
                            module.stop_auto_game()
                            stopped_modules.append(f"{module_name}(AutoStart)")
                            self.running_modules[instance_name][module_name] = False
                    
                    # Stop AutoGather and other modules using base module system
                    if hasattr(module, 'stop'):
                        if self.running_modules[instance_name].get(module_name, False):
                            module.stop()
                            stopped_modules.append(module_name)
                            self.running_modules[instance_name][module_name] = False
                    
                    # Call cleanup for stopped instance
                    if hasattr(module, 'cleanup_for_stopped_instance'):
                        module.cleanup_for_stopped_instance()
                        
                except Exception as e:
                    print(f"Error stopping {module_name} for {instance_name}: {e}")
            
            if stopped_modules:
                self.app.add_console_message(f"🛑 Stopped modules for {instance_name}: {', '.join(stopped_modules)}")
            else:
                self.app.add_console_message(f"🧹 Cleaned up modules for stopped instance: {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error stopping modules for {instance_name}: {e}")
    
    def _check_and_start_autostart(self, instance_name: str):
        """Check instance status multiple times before starting AutoStart"""
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
                            # Instance is running, proceed with AutoStart
                            self.app.add_console_message(f"✅ {instance_name} confirmed running, starting AutoStart...")
                            self.app.after(0, lambda: self._trigger_autostart_for_instance_now(instance_name))
                            return
                        elif current_status in ["Starting", "Stopping"]:
                            # Instance is transitioning, wait longer
                            self.app.add_console_message(f"⏳ {instance_name} is {current_status.lower()}, waiting...")
                            time.sleep(check_delay * 2)
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
    
    def _trigger_autostart_for_instance_now(self, instance_name: str):
        """Trigger AutoStart module for an instance (immediate)"""
        try:
            if instance_name not in self.instance_modules:
                self.app.add_console_message(f"❌ No modules found for {instance_name}")
                return
            
            # Get the AutoStart module
            autostart_module = self.instance_modules[instance_name].get("AutoStartGameModule")
            if not autostart_module:
                self.app.add_console_message(f"❌ AutoStart module not found for {instance_name}")
                return
            
            # Check if auto-startup is enabled
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                self.app.add_console_message(f"⏸ Auto-startup not enabled for {instance_name}")
                return
            
            # SMART CHECK: Don't run if already completed recently
            if self._is_autostart_recently_completed(instance_name):
                self.app.add_console_message(f"⏸ AutoStart recently completed for {instance_name}, skipping")
                return
            
            # Final verification that instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance or instance["status"] != "Running":
                self.app.add_console_message(f"⏸ {instance_name} not running during final check, aborting AutoStart")
                return
            
            self.app.add_console_message(f"🎮 Starting module system for {instance_name}...")
            
            # Start the AutoStart game process
            max_retries = settings.get("autostart_game", {}).get("max_retries", 3)
            
            def on_complete(success: bool):
                if success:
                    self.app.add_console_message(f"🎉 AutoStart completed successfully for {instance_name}")
                    # CRITICAL: Mark as completed to prevent future runs AND start other modules
                    self._mark_autostart_completed(instance_name)
                else:
                    self.app.add_console_message(f"❌ AutoStart failed for {instance_name}")
            
            success = autostart_module.start_auto_game(
                instance_name=instance_name,
                max_retries=max_retries,
                on_complete=on_complete
            )
            
            if success:
                self.app.add_console_message(f"✅ AutoStart initiated for {instance_name}")
            else:
                self.app.add_console_message(f"❌ Failed to initiate AutoStart for {instance_name}")
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error triggering AutoStart for {instance_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_smart_status_monitoring(self):
        """Start SMART status monitoring that doesn't restart completed AutoStarts"""
        if self.status_monitor_running:
            return
            
        self.status_monitor_running = True
        
        def smart_monitor_loop():
            while self.status_monitor_running:
                try:
                    time.sleep(30)  # Check every 30 seconds (less frequent)
                    
                    if not self.initialization_complete:
                        continue
                    
                    # Monitor each instance
                    current_instances = self.app.instance_manager.get_instances()
                    
                    for instance in current_instances:
                        instance_name = instance["name"]
                        current_status = instance["status"]
                        
                        if instance_name in self.instance_modules:
                            # SMART: Only restart AutoStart if:
                            # 1. Instance is running
                            # 2. Auto-startup is enabled
                            # 3. AutoStart hasn't completed recently
                            # 4. No AutoStart is currently running
                            
                            if current_status == "Running":
                                settings = self.settings_cache.get(instance_name, {})
                                if settings.get("autostart_game", {}).get("auto_startup", False):
                                    
                                    # Check if AutoStart completed recently
                                    if self._is_autostart_recently_completed(instance_name):
                                        continue  # Skip - already completed recently
                                    
                                    # Check if AutoStart is currently running
                                    autostart_module = self.instance_modules[instance_name].get("AutoStartGameModule")
                                    if autostart_module and autostart_module.get_running_instances():
                                        continue  # Skip - already running
                                    
                                    # Check if game is already running (smart check)
                                    if hasattr(autostart_module, '_is_game_already_running'):
                                        if autostart_module._is_game_already_running():
                                            self._mark_autostart_completed(instance_name)
                                            continue  # Skip - game already running
                                    
                                    # Only now consider restarting
                                    self.app.add_console_message(f"🔄 Restarting modules for {instance_name}")
                                    self.app.after(0, lambda name=instance_name: self._trigger_autostart_for_instance_now(name))
                            
                            elif current_status != "Running":
                                # Instance stopped - reset completion status and STOP MODULES
                                if instance_name in self.autostart_completed:
                                    del self.autostart_completed[instance_name]
                                    self.app.add_console_message(f"🔄 Reset AutoStart completion for stopped instance: {instance_name}")
                                    
                                    # Reset module completion status too
                                    autostart_module = self.instance_modules[instance_name].get("AutoStartGameModule")
                                    if autostart_module and hasattr(autostart_module, 'reset_completion_status'):
                                        autostart_module.reset_completion_status()
                                
                                # Reset running status for all modules
                                for module_name in self.running_modules.get(instance_name, {}):
                                    self.running_modules[instance_name][module_name] = False
                                
                                # CRITICAL: Stop any running modules for stopped instances
                                self._stop_modules_for_instance(instance_name)
                    
                except Exception as e:
                    print(f"[ModuleManager] Smart monitor error: {e}")
                    
        self.status_monitor_thread = threading.Thread(target=smart_monitor_loop, daemon=True, name="SmartModuleMonitor")
        self.status_monitor_thread.start()
        self.app.add_console_message("🔍 Started smart module status monitoring")
    
    def get_module_status_for_instance(self, instance_name: str) -> Dict:
        """Get status of all modules for an instance"""
        if instance_name not in self.instance_modules:
            return {"error": "Instance not found"}
        
        status = {
            "instance_name": instance_name,
            "autostart_completed": self._is_autostart_recently_completed(instance_name),
            "modules": {}
        }
        
        for module_name in self.instance_modules[instance_name]:
            is_running = self.running_modules.get(instance_name, {}).get(module_name, False)
            status["modules"][module_name] = {
                "enabled": True,  # Could check settings here
                "running": is_running,
                "status": "running" if is_running else "stopped"
            }
        
        return status
    
    def manually_start_gather_for_instance(self, instance_name: str) -> bool:
        """Manually start AutoGather for an instance"""
        try:
            self.app.add_console_message(f"🎯 Manually starting AutoGather for {instance_name}")
            return self._start_module_for_instance(instance_name, "AutoGatherModule")
        except Exception as e:
            self.app.add_console_message(f"❌ Error manually starting AutoGather: {e}")
            return False
    
    def manually_stop_gather_for_instance(self, instance_name: str) -> bool:
        """Manually stop AutoGather for an instance"""
        try:
            if (instance_name not in self.instance_modules or 
                "AutoGatherModule" not in self.instance_modules[instance_name]):
                self.app.add_console_message(f"❌ AutoGather module not found for {instance_name}")
                return False
            
            module = self.instance_modules[instance_name]["AutoGatherModule"]
            if hasattr(module, 'stop'):
                self.app.add_console_message(f"🛑 Stopping AutoGather for {instance_name}")
                success = module.stop()
                if success:
                    self.running_modules[instance_name]["AutoGatherModule"] = False
                    self.app.add_console_message(f"✅ Stopped AutoGather for {instance_name}")
                else:
                    self.app.add_console_message(f"❌ Failed to stop AutoGather for {instance_name}")
                return success
            else:
                self.app.add_console_message(f"⚠️ AutoGather module doesn't have stop method")
                return False
        except Exception as e:
            self.app.add_console_message(f"❌ Error manually stopping AutoGather: {e}")
            return False
    
    def manually_start_all_modules_for_instance(self, instance_name: str) -> bool:
        """Manually start all enabled modules for an instance"""
        try:
            self.app.add_console_message(f"🚀 Manually starting all modules for {instance_name}")
            
            if instance_name not in self.instance_modules:
                self.app.add_console_message(f"❌ No modules found for {instance_name}")
                return False
            
            settings = self.settings_cache.get(instance_name, {})
            modules_started = []
            
            # Start AutoGather if enabled and not running
            if ("AutoGatherModule" in self.instance_modules[instance_name] and 
                settings.get("auto_gather", {}).get("enabled", True) and
                not self.running_modules[instance_name].get("AutoGatherModule", False)):
                
                if self._start_module_for_instance(instance_name, "AutoGatherModule"):
                    modules_started.append("AutoGatherModule")
            
            # Add other modules as they become available
            # if ("AutoTrainModule" in self.instance_modules[instance_name] and 
            #     settings.get("auto_train", {}).get("enabled", True) and
            #     not self.running_modules[instance_name].get("AutoTrainModule", False)):
            #     
            #     if self._start_module_for_instance(instance_name, "AutoTrainModule"):
            #         modules_started.append("AutoTrainModule")
            
            if modules_started:
                self.app.add_console_message(f"✅ Started modules for {instance_name}: {', '.join(modules_started)}")
                return True
            else:
                self.app.add_console_message(f"ℹ️ No modules to start for {instance_name} (already running or disabled)")
                return True
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error manually starting modules for {instance_name}: {e}")
            return False
    
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
    
    def get_autostart_module(self, instance_name: str):
        """Get AutoStart module for specific instance"""
        if instance_name in self.instance_modules:
            return self.instance_modules[instance_name].get("AutoStartGameModule")
        return None
    
    def get_instance_status(self, instance_name: str) -> Dict:
        """Get comprehensive status for an instance"""
        if instance_name not in self.instance_modules:
            return {"error": "Instance not found"}
        
        modules = self.instance_modules[instance_name]
        status = {
            "instance_name": instance_name,
            "total_modules": len(modules),
            "autostart_completed": self._is_autostart_recently_completed(instance_name),
            "modules": {}
        }
        
        for module_name, module in modules.items():
            running_status = self.running_modules.get(instance_name, {}).get(module_name, False)
            
            if hasattr(module, 'get_module_info'):
                status["modules"][module_name] = module.get_module_info()
            elif hasattr(module, 'get_status'):
                status["modules"][module_name] = module.get_status()
            else:
                status["modules"][module_name] = {"status": "unknown"}
            
            status["modules"][module_name]["running"] = running_status
        
        return status
    
    def get_all_status(self) -> Dict:
        """Get status for all instances"""
        status = {
            "total_instances": len(self.instance_modules),
            "initialization_complete": self.initialization_complete,
            "status_monitoring": self.status_monitor_running,
            "instances": {}
        }
        
        for instance_name in self.instance_modules.keys():
            status["instances"][instance_name] = self.get_instance_status(instance_name)
        
        return status
    
    def start_autostart_for_instance(self, instance_name: str) -> bool:
        """Manually start AutoStart for an instance"""
        try:
            autostart_module = self.get_autostart_module(instance_name)
            if not autostart_module:
                self.app.add_console_message(f"❌ AutoStart module not found for {instance_name}")
                return False
            
            return autostart_module.start_auto_game()
            
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting AutoStart for {instance_name}: {e}")
            return False
    
    def stop_autostart_for_instance(self, instance_name: str) -> bool:
        """Stop AutoStart for an instance"""
        try:
            autostart_module = self.get_autostart_module(instance_name)
            if not autostart_module:
                return False
            
            return autostart_module.stop_auto_game()
            
        except Exception as e:
            self.app.add_console_message(f"❌ Error stopping AutoStart for {instance_name}: {e}")
            return False
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            instances_to_remove = [name for name in self.instance_modules.keys() if name not in current_names]
            
            for instance_name in instances_to_remove:
                if instance_name in self.instance_modules:
                    # Stop any running modules
                    modules = self.instance_modules[instance_name]
                    for module_name, module in modules.items():
                        try:
                            if hasattr(module, 'stop_auto_game'):
                                module.stop_auto_game()
                            if hasattr(module, 'stop'):
                                module.stop()
                        except:
                            pass
                    
                    del self.instance_modules[instance_name]
                
                if instance_name in self.settings_cache:
                    del self.settings_cache[instance_name]
                
                if instance_name in self.running_modules:
                    del self.running_modules[instance_name]
                
                # Clear completion status
                if instance_name in self.autostart_completed:
                    del self.autostart_completed[instance_name]
                    
                self.app.add_console_message(f"🗑 Removed module system for deleted instance: {instance_name}")
            
            # Add modules for new instances
            for instance in current_instances:
                instance_name = instance["name"]
                if instance_name not in self.instance_modules:
                    try:
                        from modules.autostart_game import AutoStartGameModule
                        
                        # Try to import AutoGather
                        AutoGatherModule = None
                        try:
                            from modules.auto_gather import AutoGatherModule
                        except ImportError:
                            pass
                        
                        # Load settings and create modules
                        settings = self._load_instance_settings(instance_name)
                        self.settings_cache[instance_name] = settings
                        
                        # Initialize module container
                        self.instance_modules[instance_name] = {}
                        self.running_modules[instance_name] = {}
                        
                        # Create AutoStart module
                        autostart_module = AutoStartGameModule(
                            instance_name=instance_name,
                            shared_resources=self.app.instance_manager,
                            console_callback=self.app.add_console_message
                        )
                        self.instance_modules[instance_name]["AutoStartGameModule"] = autostart_module
                        self.running_modules[instance_name]["AutoStartGameModule"] = False
                        
                        # Create AutoGather module if available
                        if AutoGatherModule and settings.get("auto_gather", {}).get("enabled", True):
                            gather_module = AutoGatherModule(
                                instance_name=instance_name,
                                shared_resources=self.app.instance_manager,
                                console_callback=self.app.add_console_message
                            )
                            self.instance_modules[instance_name]["AutoGatherModule"] = gather_module
                            self.running_modules[instance_name]["AutoGatherModule"] = False
                        
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
        for instance_name, modules in self.instance_modules.items():
            for module_name, module in modules.items():
                try:
                    if hasattr(module, 'stop_auto_game'):
                        module.stop_auto_game()
                    if hasattr(module, 'stop'):
                        module.stop()
                    # Mark as stopped
                    if instance_name in self.running_modules:
                        self.running_modules[instance_name][module_name] = False
                except Exception as e:
                    print(f"Error stopping {module_name} for {instance_name}: {e}")
        
        self.stop_status_monitoring()
    
    def get_running_modules_for_instance(self, instance_name: str) -> List[str]:
        """Get list of running modules for an instance"""
        if instance_name not in self.running_modules:
            return []
        
        running = []
        for module_name, is_running in self.running_modules[instance_name].items():
            if is_running:
                running.append(module_name)
        
        return running
    
    def is_module_running(self, instance_name: str, module_name: str) -> bool:
        """Check if a specific module is running for an instance"""
        return self.running_modules.get(instance_name, {}).get(module_name, False)
    
    def force_restart_module(self, instance_name: str, module_name: str) -> bool:
        """Force restart a specific module"""
        try:
            self.app.add_console_message(f"🔄 Force restarting {module_name} for {instance_name}")
            
            # Stop first if running
            if self.is_module_running(instance_name, module_name):
                if module_name == "AutoGatherModule":
                    self.manually_stop_gather_for_instance(instance_name)
                # Add other module types as needed
                
                # Wait a moment
                time.sleep(2)
            
            # Start the module
            if module_name == "AutoGatherModule":
                return self.manually_start_gather_for_instance(instance_name)
            # Add other module types as needed
            else:
                return self._start_module_for_instance(instance_name, module_name)
                
        except Exception as e:
            self.app.add_console_message(f"❌ Error force restarting {module_name}: {e}")
            return False
    
    def debug_module_status(self, instance_name: str = None):
        """Debug method to print detailed module status"""
        print("\n" + "="*60)
        print("MODULE MANAGER DEBUG STATUS")
        print("="*60)
        
        print(f"Initialization complete: {self.initialization_complete}")
        print(f"Status monitoring running: {self.status_monitor_running}")
        print(f"Total instances: {len(self.instance_modules)}")
        print(f"AutoStart completions: {len(self.autostart_completed)}")
        
        if instance_name:
            instances_to_check = [instance_name] if instance_name in self.instance_modules else []
        else:
            instances_to_check = list(self.instance_modules.keys())
        
        for inst_name in instances_to_check:
            print(f"\n--- Instance: {inst_name} ---")
            
            # AutoStart status
            autostart_completed = self._is_autostart_recently_completed(inst_name)
            print(f"AutoStart completed: {autostart_completed}")
            
            # Module status
            modules = self.instance_modules.get(inst_name, {})
            running_status = self.running_modules.get(inst_name, {})
            
            for mod_name, module in modules.items():
                is_running = running_status.get(mod_name, False)
                status_symbol = "🟢" if is_running else "🔴"
                print(f"  {status_symbol} {mod_name}: {'RUNNING' if is_running else 'STOPPED'}")
                
                # Additional module info if available
                if hasattr(module, 'get_status_info'):
                    try:
                        info = module.get_status_info()
                        print(f"    Status: {info.get('status', 'unknown')}")
                        print(f"    Executions: {info.get('execution_count', 0)}")
                        print(f"    Errors: {info.get('error_count', 0)}")
                        if info.get('last_error'):
                            print(f"    Last error: {info['last_error']}")
                    except Exception as e:
                        print(f"    Error getting status: {e}")
        
        print("="*60)
    
    # Legacy compatibility methods
    def check_auto_startup(self):
        """Legacy method - redirect to new module system"""
        self.check_auto_startup_initial()
    
    def get_module_status(self) -> Dict:
        """Legacy method - get overall module status"""
        total_instances = len(self.instance_modules)
        total_modules = 0
        running_modules = 0
        auto_startup_enabled = 0
        completed_autostarts = len(self.autostart_completed)
        
        for instance_name, modules in self.instance_modules.items():
            total_modules += len(modules)
            
            # Count running modules
            for module_name in modules.keys():
                if self.running_modules.get(instance_name, {}).get(module_name, False):
                    running_modules += 1
            
            settings = self.settings_cache.get(instance_name, {})
            if settings.get("autostart_game", {}).get("auto_startup", False):
                auto_startup_enabled += 1
        
        return {
            "total_instances": total_instances,
            "total_modules": total_modules,
            "running_modules": running_modules,
            "auto_startup_enabled": auto_startup_enabled,
            "completed_autostarts": completed_autostarts,
            "initialization_complete": self.initialization_complete,
            "status_monitoring": self.status_monitor_running
        }
    
    # NEW: Method to force completion status (for testing)
    def force_mark_autostart_completed(self, instance_name: str):
        """Force mark AutoStart as completed (for testing/debugging)"""
        self.app.add_console_message(f"🔧 Force marking AutoStart complete for {instance_name}")
        self._mark_autostart_completed(instance_name)
    
    # NEW: Method to clear completion status (for testing)
    def clear_autostart_completion(self, instance_name: str):
        """Clear AutoStart completion status (for testing/debugging)"""
        if instance_name in self.autostart_completed:
            del self.autostart_completed[instance_name]
            self.app.add_console_message(f"🔧 Cleared AutoStart completion for {instance_name}")
        
        if instance_name in self.running_modules:
            self.running_modules[instance_name]["AutoStartGameModule"] = False
            self.app.add_console_message(f"🔧 Reset AutoStart running status for {instance_name}")
    
    # NEW: Comprehensive module control
    def get_module_control_info(self) -> Dict:
        """Get comprehensive module control information for UI"""
        control_info = {
            "manager_status": {
                "initialized": self.initialization_complete,
                "monitoring": self.status_monitor_running,
                "total_instances": len(self.instance_modules)
            },
            "instances": {}
        }
        
        for instance_name in self.instance_modules.keys():
            instance_info = {
                "autostart_completed": self._is_autostart_recently_completed(instance_name),
                "modules": {},
                "available_actions": []
            }
            
            # Get instance status
            instance = self.app.instance_manager.get_instance(instance_name)
            instance_running = instance and instance["status"] == "Running"
            instance_info["instance_running"] = instance_running
            
            # Get module info
            for module_name in self.instance_modules[instance_name]:
                is_running = self.running_modules.get(instance_name, {}).get(module_name, False)
                instance_info["modules"][module_name] = {
                    "running": is_running,
                    "can_start": not is_running and instance_running,
                    "can_stop": is_running,
                    "can_restart": instance_running
                }
            
            # Determine available actions
            if instance_running:
                if not instance_info["autostart_completed"]:
                    instance_info["available_actions"].append("start_autostart")
                
                if not instance_info["modules"].get("AutoGatherModule", {}).get("running", False):
                    instance_info["available_actions"].append("start_gather")
                else:
                    instance_info["available_actions"].append("stop_gather")
                
                instance_info["available_actions"].append("start_all_modules")
                instance_info["available_actions"].append("restart_all_modules")
            
            control_info["instances"][instance_name] = instance_info
        
        return control_info