"""
BENSON v2.0 - FIXED Module Manager with Reduced Spam
Now properly manages modules with minimal console noise
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """FIXED: Module manager with reduced spam and better module communication"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_modules = {}  # instance_name -> {module_name: module_instance}
        self.settings_cache = {}
        self.initialization_complete = False
        
        # Status monitoring with spam reduction
        self.status_monitor_running = False
        self.status_monitor_thread = None
        self.status_monitor_stop = threading.Event()
        
        # Track AutoStart completion to prevent duplicates
        self.autostart_completed = {}  # instance_name -> completion_time
        
        # Track which modules are running for each instance
        self.running_modules = {}  # instance_name -> {module_name: True/False}
        
        # NEW: Spam reduction tracking
        self._last_log_times = {}  # message_type -> timestamp
        self._log_intervals = {
            "status_check": 300,  # Only log status checks every 5 minutes
            "cleanup": 120,       # Only log cleanup every 2 minutes
            "monitoring": 600     # Only log monitoring updates every 10 minutes
        }
    
    def _should_log_message(self, message_type: str) -> bool:
        """Check if we should log this type of message to reduce spam"""
        current_time = time.time()
        last_log_time = self._last_log_times.get(message_type, 0)
        interval = self._log_intervals.get(message_type, 60)  # Default 1 minute
        
        if current_time - last_log_time >= interval:
            self._last_log_times[message_type] = current_time
            return True
        return False
    
    def _log_with_spam_filter(self, message: str, message_type: str = "general"):
        """Log message with spam filtering"""
        if message_type == "general" or self._should_log_message(message_type):
            self.app.add_console_message(message)
    
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
                self._log_with_spam_filter("⚠️ AutoGather module not available")
            
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
                    self._log_with_spam_filter(f"✅ AutoGather module initialized for {instance_name}")
                
                self._log_with_spam_filter(f"🔧 Initialized module system for {instance_name}")
            
            self.initialization_complete = True
            self._log_with_spam_filter(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
            # Start QUIET status monitoring
            self._start_quiet_status_monitoring()
            
        except Exception as e:
            self._log_with_spam_filter(f"❌ Module initialization error: {e}")
            import traceback
            traceback.print_exc()
    
    def check_auto_startup_initial(self):
        """Initial auto-startup check for all instances"""
        if not self.initialization_complete:
            self._log_with_spam_filter("⏳ Module system not ready, deferring auto-startup...")
            self.app.after(2000, self.check_auto_startup_initial)
            return
        
        try:
            self._log_with_spam_filter("🔍 Initial module auto-startup check...")
            
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
                        self._log_with_spam_filter(f"✅ {instance_name} ready for module auto-startup")
            
            if auto_start_candidates:
                self._log_with_spam_filter(f"🚀 Starting AutoStart for: {', '.join(auto_start_candidates)}")
                
                for instance_name in auto_start_candidates:
                    # Stagger the starts
                    delay = auto_start_candidates.index(instance_name) * 3000
                    self.app.after(delay, lambda name=instance_name: self._trigger_autostart_for_instance(name))
            else:
                self._log_with_spam_filter("📱 No running instances configured for module auto-startup")
                
        except Exception as e:
            self._log_with_spam_filter(f"❌ Initial module auto-startup error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """Trigger auto-startup with smart duplicate prevention"""
        # SMART CHECK: Don't trigger if already completed recently
        if self._is_autostart_recently_completed(instance_name):
            self._log_with_spam_filter(f"⏸ AutoStart recently completed for {instance_name}, skipping", "status_check")
            return
        
        self._log_with_spam_filter(f"🎯 Module auto-startup triggered for {instance_name}")
        
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
        self._log_with_spam_filter(f"✅ Marked AutoStart complete for {instance_name}")
        
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
            
            if modules_to_start:
                self._log_with_spam_filter(f"🎮 Starting additional modules for {instance_name}: {', '.join(modules_to_start)}")
                
                for module_name in modules_to_start:
                    # Add a small delay between module starts
                    delay = modules_to_start.index(module_name) * 1000
                    self.app.after(delay, lambda name=instance_name, mod=module_name: self._start_module_for_instance(name, mod))
            else:
                # Only log this occasionally to reduce spam
                if self._should_log_message("no_modules"):
                    self._log_with_spam_filter(f"ℹ️ No additional modules to start for {instance_name}")
                
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error starting additional modules for {instance_name}: {e}")
    
    def _start_module_for_instance(self, instance_name: str, module_name: str):
        """Start a specific module for an instance"""
        try:
            if (instance_name not in self.instance_modules or 
                module_name not in self.instance_modules[instance_name]):
                self._log_with_spam_filter(f"❌ Module {module_name} not found for {instance_name}")
                return False
            
            module = self.instance_modules[instance_name][module_name]
            
            # Different modules have different start methods
            if module_name == "AutoGatherModule":
                # AutoGather modules use the base module start method
                if hasattr(module, 'start'):
                    self._log_with_spam_filter(f"🚀 Starting {module_name} for {instance_name}...")
                    success = module.start()
                    if success:
                        self.running_modules[instance_name][module_name] = True
                        self._log_with_spam_filter(f"✅ Started {module_name} for {instance_name}")
                        return True
                    else:
                        self._log_with_spam_filter(f"❌ Failed to start {module_name} for {instance_name}")
                        return False
                else:
                    self._log_with_spam_filter(f"⚠️ {module_name} doesn't have start method")
                    return False
            
            else:
                self._log_with_spam_filter(f"⚠️ Unknown module type: {module_name}")
                return False
                
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error starting {module_name} for {instance_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _stop_modules_for_instance(self, instance_name: str):
        """Stop all running modules for a specific instance - REDUCED LOGGING"""
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
            
            # REDUCED LOGGING: Only log if modules were actually stopped
            if stopped_modules:
                self._log_with_spam_filter(f"🛑 Stopped modules for {instance_name}: {', '.join(stopped_modules)}", "cleanup")
            else:
                # Only log cleanup occasionally
                self._log_with_spam_filter(f"🧹 Cleaned up modules for stopped instance: {instance_name}", "cleanup")
                
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error stopping modules for {instance_name}: {e}")
    
    def _check_and_start_autostart(self, instance_name: str):
        """Check instance status multiple times before starting AutoStart"""
        def check_worker():
            try:
                max_attempts = 5
                check_delay = 2  # seconds between checks
                
                for attempt in range(max_attempts):
                    # REDUCED LOGGING: Only log first and last attempts
                    if attempt == 0 or attempt == max_attempts - 1:
                        self._log_with_spam_filter(f"🔍 Checking {instance_name} status (attempt {attempt + 1}/{max_attempts})...")
                    
                    # Force refresh instance status
                    self.app.instance_manager.update_instance_statuses()
                    time.sleep(1)  # Wait for status update
                    
                    # Check current status
                    instance = self.app.instance_manager.get_instance(instance_name)
                    
                    if instance:
                        current_status = instance["status"]
                        
                        # Only log status on first attempt or if status changed
                        if attempt == 0:
                            self._log_with_spam_filter(f"📊 {instance_name} current status: {current_status}")
                        
                        if current_status == "Running":
                            # Instance is running, proceed with AutoStart
                            self._log_with_spam_filter(f"✅ {instance_name} confirmed running, starting AutoStart...")
                            self.app.after(0, lambda: self._trigger_autostart_for_instance_now(instance_name))
                            return
                        elif current_status in ["Starting", "Stopping"]:
                            # Instance is transitioning, wait longer
                            if attempt == 0:  # Only log once
                                self._log_with_spam_filter(f"⏳ {instance_name} is {current_status.lower()}, waiting...")
                            time.sleep(check_delay * 2)
                        else:
                            # Instance stopped or error
                            if attempt == 0:  # Only log once
                                self._log_with_spam_filter(f"❌ {instance_name} status is {current_status}, waiting...")
                            time.sleep(check_delay)
                    else:
                        if attempt == 0:  # Only log once
                            self._log_with_spam_filter(f"❌ Could not find instance {instance_name}")
                        time.sleep(check_delay)
                
                # All attempts failed - only log once
                self._log_with_spam_filter(f"⏸ {instance_name} did not reach running state after {max_attempts} attempts")
                
            except Exception as e:
                self._log_with_spam_filter(f"❌ Error checking {instance_name} status: {e}")
        
        # Run in background thread
        threading.Thread(target=check_worker, daemon=True, name=f"StatusCheck-{instance_name}").start()
    
    def _trigger_autostart_for_instance_now(self, instance_name: str):
        """Trigger AutoStart module for an instance (immediate)"""
        try:
            if instance_name not in self.instance_modules:
                self._log_with_spam_filter(f"❌ No modules found for {instance_name}")
                return
            
            # Get the AutoStart module
            autostart_module = self.instance_modules[instance_name].get("AutoStartGameModule")
            if not autostart_module:
                self._log_with_spam_filter(f"❌ AutoStart module not found for {instance_name}")
                return
            
            # Check if auto-startup is enabled
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                self._log_with_spam_filter(f"⏸ Auto-startup not enabled for {instance_name}")
                return
            
            # SMART CHECK: Don't run if already completed recently
            if self._is_autostart_recently_completed(instance_name):
                self._log_with_spam_filter(f"⏸ AutoStart recently completed for {instance_name}, skipping", "status_check")
                return
            
            # Final verification that instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance or instance["status"] != "Running":
                self._log_with_spam_filter(f"⏸ {instance_name} not running during final check, aborting AutoStart")
                return
            
            self._log_with_spam_filter(f"🎮 Starting module system for {instance_name}...")
            
            # Start the AutoStart game process
            max_retries = settings.get("autostart_game", {}).get("max_retries", 3)
            
            def on_complete(success: bool):
                if success:
                    self._log_with_spam_filter(f"🎉 AutoStart completed successfully for {instance_name}")
                    # CRITICAL: Mark as completed to prevent future runs AND start other modules
                    self._mark_autostart_completed(instance_name)
                else:
                    self._log_with_spam_filter(f"❌ AutoStart failed for {instance_name}")
            
            success = autostart_module.start_auto_game(
                instance_name=instance_name,
                max_retries=max_retries,
                on_complete=on_complete
            )
            
            if success:
                self._log_with_spam_filter(f"✅ AutoStart initiated for {instance_name}")
            else:
                self._log_with_spam_filter(f"❌ Failed to initiate AutoStart for {instance_name}")
                
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error triggering AutoStart for {instance_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_quiet_status_monitoring(self):
        """FIXED: Start QUIET status monitoring that doesn't spam console"""
        if self.status_monitor_running:
            return
            
        self.status_monitor_running = True
        
        def quiet_monitor_loop():
            while self.status_monitor_running:
                try:
                    time.sleep(60)  # INCREASED: Check every 60 seconds instead of 30
                    
                    if not self.initialization_complete:
                        continue
                    
                    # QUIET: Monitor without excessive logging
                    self._check_instances_quietly()
                    
                except Exception as e:
                    # Only log errors, not routine operations
                    print(f"[ModuleManager] Monitor error: {e}")
                    
        self.status_monitor_thread = threading.Thread(target=quiet_monitor_loop, daemon=True, name="QuietModuleMonitor")
        self.status_monitor_thread.start()
        
        # REDUCED: Only log monitoring start once
        if self._should_log_message("monitoring"):
            self._log_with_spam_filter("🔍 Started quiet module status monitoring", "monitoring")
    
    def _check_instances_quietly(self):
        """QUIET: Check instances without spamming console"""
        try:
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
                            
                            # REDUCED LOGGING: Only restart if really needed
                            if self._should_log_message(f"restart_{instance_name}"):
                                self._log_with_spam_filter(f"🔄 Restarting modules for {instance_name}")
                            self.app.after(0, lambda name=instance_name: self._trigger_autostart_for_instance_now(name))
                    
                    elif current_status != "Running":
                        # Instance stopped - reset completion status and STOP MODULES
                        if instance_name in self.autostart_completed:
                            del self.autostart_completed[instance_name]
                            
                            # Only log reset occasionally
                            if self._should_log_message(f"reset_{instance_name}"):
                                self._log_with_spam_filter(f"🔄 Reset AutoStart completion for stopped instance: {instance_name}", "cleanup")
                                
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
            print(f"[ModuleManager] Quiet monitor error: {e}")
    
    # ... [Rest of the methods remain similar but with spam reduction] ...
    
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
            self._log_with_spam_filter(f"🎯 Manually starting AutoGather for {instance_name}")
            return self._start_module_for_instance(instance_name, "AutoGatherModule")
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error manually starting AutoGather: {e}")
            return False
    
    def manually_stop_gather_for_instance(self, instance_name: str) -> bool:
        """Manually stop AutoGather for an instance"""
        try:
            if (instance_name not in self.instance_modules or 
                "AutoGatherModule" not in self.instance_modules[instance_name]):
                self._log_with_spam_filter(f"❌ AutoGather module not found for {instance_name}")
                return False
            
            module = self.instance_modules[instance_name]["AutoGatherModule"]
            if hasattr(module, 'stop'):
                self._log_with_spam_filter(f"🛑 Stopping AutoGather for {instance_name}")
                success = module.stop()
                if success:
                    self.running_modules[instance_name]["AutoGatherModule"] = False
                    self._log_with_spam_filter(f"✅ Stopped AutoGather for {instance_name}")
                else:
                    self._log_with_spam_filter(f"❌ Failed to stop AutoGather for {instance_name}")
                return success
            else:
                self._log_with_spam_filter(f"⚠️ AutoGather module doesn't have stop method")
                return False
        except Exception as e:
            self._log_with_spam_filter(f"❌ Error manually stopping AutoGather: {e}")
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
    
    def refresh_modules(self):
        """Refresh modules when instances change - QUIET VERSION"""
        try:
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            instances_to_remove = [name for name in self.instance_modules.keys() if name not in current_names]
            
            for instance_name in instances_to_remove:
                if instance_name in self.instance_modules:
                    # Stop any running modules quietly
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
                    
                # REDUCED LOGGING: Only log removal occasionally
                self._log_with_spam_filter(f"🗑 Removed module system for deleted instance: {instance_name}", "cleanup")
            
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
                        
                        self._log_with_spam_filter(f"➕ Added module system for new instance: {instance_name}")
                        
                    except Exception as e:
                        self._log_with_spam_filter(f"❌ Failed to create module system for {instance_name}: {e}")
            
            # REDUCED LOGGING: Summary instead of individual messages
            self._log_with_spam_filter(f"🔄 Refreshed module systems for {len(current_instances)} instances")
            
        except Exception as e:
            self._log_with_spam_filter(f"❌ Module refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings for a specific instance"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            self._log_with_spam_filter(f"🔄 Reloaded module settings for {instance_name}")
        except Exception as e:
            self._log_with_spam_filter(f"❌ Failed to reload settings for {instance_name}: {e}")
    
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