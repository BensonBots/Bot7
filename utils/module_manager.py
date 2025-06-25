"""
BENSON v2.0 - FIXED Module Manager - Auto-triggers and Status Updates
Streamlined version that properly starts AutoGather and updates GUI
"""

import os
import json
import threading
import time
from typing import Dict, List


class ModuleManager:
    """Fixed module manager with proper auto-triggers and status updates"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.instance_modules = {}  # instance_name -> {module_name: module_instance}
        self.settings_cache = {}
        self.initialization_complete = False
        
        # Tracking
        self.autostart_completed = {}  # instance_name -> completion_time
        self.running_modules = {}  # instance_name -> {module_name: True/False}
        
        # Status update timer
        self.status_update_timer = None
        
        print("[ModuleManager] Event-driven module system initializing...")
        self._initialize_modules_simple()
        
        # Start status update loop
        self._start_status_updates()
    
    def _initialize_modules_simple(self):
        """Simple initialization without background threads"""
        try:
            print("[ModuleManager] Simple module initialization...")
            
            # Import modules
            try:
                from modules.autostart_game import AutoStartGameModule
                print("[ModuleManager] ✅ AutoStartGame imported")
            except ImportError as e:
                print(f"[ModuleManager] ❌ AutoStartGame import failed: {e}")
                return
            
            # Import AutoGather
            AutoGatherModule = None
            try:
                from modules.auto_gather import AutoGatherModule
                print("[ModuleManager] ✅ AutoGather imported successfully")
            except ImportError as e:
                print(f"[ModuleManager] ❌ AutoGather import failed: {e}")
                print("[ModuleManager] 🔍 Checking if auto_gather.py exists...")
                import os
                if os.path.exists("modules/auto_gather.py"):
                    print("[ModuleManager] ✅ auto_gather.py file exists")
                    print("[ModuleManager] 💡 Import failed due to missing dependencies or syntax errors")
                else:
                    print("[ModuleManager] ❌ auto_gather.py file not found")
            except Exception as e:
                print(f"[ModuleManager] ❌ AutoGather unexpected error: {e}")
                import traceback
                traceback.print_exc()
            
            # Get instances
            instances = self.app.instance_manager.get_instances()
            print(f"[ModuleManager] Found {len(instances)} instances")
            
            # Create modules for each instance
            for instance in instances:
                instance_name = instance["name"]
                self._create_modules_for_instance(instance_name, AutoStartGameModule, AutoGatherModule)
            
            # Mark as complete
            self.initialization_complete = True
            print(f"[ModuleManager] ✅ Initialization complete for {len(instances)} instances")
            
            # Log final status
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Initialization error: {e}")
            self.initialization_complete = True
    
    def _create_modules_for_instance(self, instance_name: str, AutoStartGameModule, AutoGatherModule=None):
        """Create modules for a single instance"""
        try:
            # Load settings
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            
            # Initialize containers
            self.instance_modules[instance_name] = {}
            self.running_modules[instance_name] = {}
            
            # Create AutoStart module (always)
            autostart_module = AutoStartGameModule(
                instance_name=instance_name,
                shared_resources=self.app.instance_manager,
                console_callback=self.app.add_console_message
            )
            self.instance_modules[instance_name]["AutoStartGame"] = autostart_module
            self.running_modules[instance_name]["AutoStartGame"] = False
            
            # Create AutoGather if available and enabled
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
        """Start periodic status updates to keep GUI in sync"""
        def update_loop():
            while hasattr(self, 'app') and self.app:
                try:
                    # Update instance statuses every 10 seconds
                    if self.app.instance_manager:
                        self.app.instance_manager.update_instance_statuses()
                        
                        # Update GUI cards
                        self._update_gui_cards()
                    
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"[ModuleManager] Status update error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=update_loop, daemon=True, name="StatusUpdater")
        thread.start()
        print("[ModuleManager] ✅ Status update loop started")
    
    def _update_gui_cards(self):
        """Update GUI instance cards with current status"""
        try:
            if not hasattr(self.app, 'instance_cards') or not self.app.instance_cards:
                return
            
            instances = self.app.instance_manager.get_instances()
            instance_status_map = {inst["name"]: inst["status"] for inst in instances}
            
            # Update each card
            for card in self.app.instance_cards:
                if hasattr(card, 'name') and hasattr(card, 'update_status'):
                    current_status = instance_status_map.get(card.name)
                    if current_status and current_status != card.status:
                        # Schedule UI update on main thread
                        self.app.after(0, lambda c=card, s=current_status: c.update_status(s))
            
        except Exception as e:
            print(f"[ModuleManager] GUI update error: {e}")
    
    def trigger_auto_startup_for_instance(self, instance_name: str):
        """EVENT: Trigger auto-startup when instance starts"""
        if not self.initialization_complete:
            print(f"[ModuleManager] Module system not ready for {instance_name}")
            return
        
        # Check if already completed recently
        if self._is_autostart_recently_completed(instance_name):
            print(f"[ModuleManager] AutoStart recently completed for {instance_name}, skipping")
            return
        
        print(f"[ModuleManager] 🎯 Auto-startup triggered for {instance_name}")
        
        # Wait for MEmu instance to fully boot
        self.app.after(8000, lambda: self._start_autostart_for_instance(instance_name))
    
    def _start_autostart_for_instance(self, instance_name: str):
        """Start AutoStart for an instance with proper timing checks"""
        try:
            print(f"[ModuleManager] 🎯 Starting AutoStart process for {instance_name}")
            
            # Check settings first
            settings = self.settings_cache.get(instance_name, {})
            if not settings.get("autostart_game", {}).get("auto_startup", False):
                print(f"[ModuleManager] Auto-startup not enabled for {instance_name}")
                return
            
            # Get AutoStart module
            if instance_name not in self.instance_modules:
                print(f"[ModuleManager] No modules found for {instance_name}")
                return
            
            autostart_module = self.instance_modules[instance_name].get("AutoStartGame")
            if not autostart_module:
                print(f"[ModuleManager] AutoStart module not found for {instance_name}")
                return
            
            # Wait and verify instance is running
            self._verify_and_start_autostart(instance_name, autostart_module, settings)
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Error in AutoStart process for {instance_name}: {e}")
    
    def _verify_and_start_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Verify instance is ready and start AutoStart"""
        def check_instance_ready(attempt=1):
            try:
                # Refresh instance status
                self.app.instance_manager.update_instance_statuses()
                
                # Check current status
                instance = self.app.instance_manager.get_instance(instance_name)
                if not instance:
                    if attempt < 5:
                        print(f"[ModuleManager] Instance {instance_name} not found, retrying...")
                        self.app.after(2000, lambda: check_instance_ready(attempt + 1))
                    return
                
                current_status = instance["status"]
                print(f"[ModuleManager] Check {attempt}: {instance_name} status = {current_status}")
                
                if current_status == "Running":
                    # Instance is running, start AutoStart
                    print(f"[ModuleManager] ✅ {instance_name} confirmed running, starting AutoStart...")
                    self._actually_start_autostart(instance_name, autostart_module, settings)
                    
                elif current_status in ["Starting", "Connecting"] and attempt < 10:
                    # Still starting, wait more
                    print(f"[ModuleManager] ⏳ {instance_name} still starting, waiting...")
                    self.app.after(2000, lambda: check_instance_ready(attempt + 1))
                    
                else:
                    # Instance stopped or too many attempts
                    print(f"[ModuleManager] ❌ {instance_name} not ready for AutoStart")
                    
            except Exception as e:
                print(f"[ModuleManager] Error checking {instance_name}: {e}")
        
        # Start checking
        check_instance_ready()
    
    def _actually_start_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Actually start the AutoStart module"""
        try:
            print(f"[ModuleManager] 🚀 Starting AutoStart for {instance_name}")
            self.app.add_console_message(f"🎮 Starting module system for {instance_name}...")
            
            # Start AutoStart with completion callback
            def on_complete(success: bool):
                if success:
                    print(f"[ModuleManager] ✅ AutoStart completed for {instance_name}")
                    self.app.add_console_message(f"✅ AutoStart completed for {instance_name}")
                    self._mark_autostart_completed(instance_name)
                    
                    # FIXED: Auto-start AutoGather after AutoStart completes
                    self._auto_start_additional_modules(instance_name)
                else:
                    print(f"[ModuleManager] ❌ AutoStart failed for {instance_name}")
                    self.app.add_console_message(f"❌ AutoStart failed for {instance_name}")
            
            # Get retry settings
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
            print(f"[ModuleManager] ❌ Error starting AutoStart for {instance_name}: {e}")
    
    def _auto_start_additional_modules(self, instance_name: str):
        """FIXED: Auto-start additional modules after AutoStart completes"""
        try:
            if instance_name not in self.instance_modules:
                print(f"[ModuleManager] ❌ No modules found for {instance_name}")
                return
            
            settings = self.settings_cache.get(instance_name, {})
            
            # Check if AutoGather is available
            if "AutoGather" not in self.instance_modules[instance_name]:
                print(f"[ModuleManager] ⚠️ AutoGather not available for {instance_name} - module not imported")
                self.app.add_console_message(f"⚠️ AutoGather not available for {instance_name} - check module installation")
                return
            
            # Check if AutoGather is enabled in settings
            if not settings.get("auto_gather", {}).get("enabled", True):
                print(f"[ModuleManager] ℹ️ AutoGather disabled in settings for {instance_name}")
                self.app.add_console_message(f"ℹ️ AutoGather disabled in settings for {instance_name}")
                return
            
            # Check if already running
            if self.running_modules[instance_name].get("AutoGather", False):
                print(f"[ModuleManager] ℹ️ AutoGather already running for {instance_name}")
                return
            
            print(f"[ModuleManager] 🌾 Auto-starting AutoGather for {instance_name}")
            self.app.add_console_message(f"🌾 Auto-starting AutoGather for {instance_name}...")
            
            # Wait a moment for game to be fully accessible
            self.app.after(3000, lambda: self._start_autogather(instance_name))
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Error auto-starting modules for {instance_name}: {e}")
            self.app.add_console_message(f"❌ Error auto-starting modules for {instance_name}: {e}")
    
    def _start_autogather(self, instance_name: str):
        """Start AutoGather module"""
        try:
            gather_module = self.instance_modules[instance_name].get("AutoGather")
            if not gather_module:
                return
            
            if hasattr(gather_module, 'start'):
                success = gather_module.start()
                if success:
                    self.running_modules[instance_name]["AutoGather"] = True
                    self.app.add_console_message(f"✅ Auto-started AutoGather for {instance_name}")
                    print(f"[ModuleManager] ✅ AutoGather started for {instance_name}")
                else:
                    self.app.add_console_message(f"❌ Failed to start AutoGather for {instance_name}")
                    print(f"[ModuleManager] ❌ AutoGather failed to start for {instance_name}")
            else:
                print(f"[ModuleManager] AutoGather module has no start method")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ Error starting AutoGather for {instance_name}: {e}")
    
    def _is_autostart_recently_completed(self, instance_name: str) -> bool:
        """Check if AutoStart completed recently"""
        if instance_name not in self.autostart_completed:
            return False
        
        last_completion = self.autostart_completed[instance_name]
        time_since = time.time() - last_completion
        return time_since < 300  # 5 minutes
    
    def _mark_autostart_completed(self, instance_name: str):
        """Mark AutoStart as completed"""
        self.autostart_completed[instance_name] = time.time()
        print(f"[ModuleManager] ✅ Marked AutoStart complete for {instance_name}")
    
    def cleanup_for_stopped_instance(self, instance_name: str):
        """Clean up when instance stops"""
        try:
            if instance_name not in self.instance_modules:
                return
            
            print(f"[ModuleManager] 🧹 Cleaning up modules for stopped instance: {instance_name}")
            
            # Stop all modules for this instance
            modules = self.instance_modules[instance_name]
            for module_name, module in modules.items():
                try:
                    if hasattr(module, 'stop_auto_game'):
                        module.stop_auto_game()
                    if hasattr(module, 'stop'):
                        module.stop()
                    if hasattr(module, 'cleanup_for_stopped_instance'):
                        module.cleanup_for_stopped_instance()
                    
                    self.running_modules[instance_name][module_name] = False
                    
                except Exception as e:
                    print(f"[ModuleManager] Error stopping {module_name}: {e}")
            
            # Clear completion status
            if instance_name in self.autostart_completed:
                del self.autostart_completed[instance_name]
            
            print(f"[ModuleManager] ✅ Cleaned up modules for {instance_name}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Cleanup error for {instance_name}: {e}")
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            instances_to_remove = [name for name in self.instance_modules.keys() if name not in current_names]
            
            for instance_name in instances_to_remove:
                self.cleanup_for_stopped_instance(instance_name)
                if instance_name in self.instance_modules:
                    del self.instance_modules[instance_name]
                if instance_name in self.settings_cache:
                    del self.settings_cache[instance_name]
                if instance_name in self.running_modules:
                    del self.running_modules[instance_name]
                print(f"[ModuleManager] 🗑 Removed modules for deleted instance: {instance_name}")
            
            # Add modules for new instances
            for instance in current_instances:
                instance_name = instance["name"]
                if instance_name not in self.instance_modules:
                    try:
                        from modules.autostart_game import AutoStartGameModule
                        AutoGatherModule = None
                        try:
                            from modules.auto_gather import AutoGatherModule
                        except ImportError:
                            pass
                        
                        self._create_modules_for_instance(instance_name, AutoStartGameModule, AutoGatherModule)
                        print(f"[ModuleManager] ➕ Added modules for new instance: {instance_name}")
                        
                    except Exception as e:
                        print(f"[ModuleManager] ❌ Failed to create modules for {instance_name}: {e}")
            
            print(f"[ModuleManager] 🔄 Module refresh complete: {len(current_instances)} instances")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Module refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings when changed"""
        try:
            settings = self._load_instance_settings(instance_name)
            self.settings_cache[instance_name] = settings
            print(f"[ModuleManager] 🔄 Reloaded settings for {instance_name}")
        except Exception as e:
            print(f"[ModuleManager] ❌ Failed to reload settings for {instance_name}: {e}")
    
    def _load_instance_settings(self, instance_name: str) -> Dict:
        """Load settings for instance"""
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
                "resource_types": ["food", "wood", "iron", "stone"]
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
            print(f"[ModuleManager] Error loading settings for {instance_name}: {e}")
        
        return default_settings
    
    # Manual control methods
    def manually_start_gather_for_instance(self, instance_name: str) -> bool:
        """Manually start AutoGather"""
        try:
            if (instance_name not in self.instance_modules or 
                "AutoGather" not in self.instance_modules[instance_name]):
                self.app.add_console_message(f"❌ AutoGather not available for {instance_name}")
                return False
            
            return self._start_autogather(instance_name)
        except Exception as e:
            self.app.add_console_message(f"❌ Error starting AutoGather: {e}")
            return False
    
    def manually_stop_gather_for_instance(self, instance_name: str) -> bool:
        """Manually stop AutoGather"""
        try:
            if (instance_name not in self.instance_modules or 
                "AutoGather" not in self.instance_modules[instance_name]):
                return False
            
            module = self.instance_modules[instance_name]["AutoGather"]
            if hasattr(module, 'stop'):
                success = module.stop()
                if success:
                    self.running_modules[instance_name]["AutoGather"] = False
                    self.app.add_console_message(f"🛑 Stopped AutoGather for {instance_name}")
                return success
            return False
        except Exception as e:
            self.app.add_console_message(f"❌ Error stopping AutoGather: {e}")
            return False
    
    # Status methods
    def get_module_status_for_instance(self, instance_name: str) -> Dict:
        """Get module status for instance"""
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
                "enabled": True,
                "running": is_running,
                "status": "running" if is_running else "stopped"
            }
        
        return status
    
    def get_module_status(self) -> Dict:
        """Get overall module status"""
        total_instances = len(self.instance_modules)
        total_modules = sum(len(modules) for modules in self.instance_modules.values())
        running_modules = 0
        
        for instance_name, instance_modules in self.running_modules.items():
            running_modules += sum(1 for running in instance_modules.values() if running)
        
        return {
            "total_instances": total_instances,
            "total_modules": total_modules,
            "running_modules": running_modules,
            "completed_autostarts": len(self.autostart_completed),
            "initialization_complete": self.initialization_complete
        }
    
    def stop_all_modules(self):
        """Stop all modules"""
        for instance_name in list(self.instance_modules.keys()):
            self.cleanup_for_stopped_instance(instance_name)
        print("[ModuleManager] 🛑 All modules stopped")