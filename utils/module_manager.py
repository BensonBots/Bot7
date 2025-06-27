"""
BENSON v2.0 - FIXED Module Manager
Added proper settings reload and AutoGather update methods
"""

import os
import json
import threading
import time
from typing import Dict


class ModuleManager:
    """Fixed module manager with proper AutoGather integration and settings reload"""
    
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
        """Initialize modules for all instances with proper dependencies"""
        try:
            # Import AutoStart module
            from modules.autostart_game import AutoStartGameModule
            
            # Import AutoGather module and check dependencies
            try:
                from modules.auto_gather import AutoGather
                AutoGatherModule = AutoGather
                print("[ModuleManager] ✅ AutoGather module imported successfully")
            except ImportError as e:
                print(f"[ModuleManager] ⚠️ AutoGather import failed: {e}")
                AutoGatherModule = None
            
            # Initialize required dependencies for AutoGather
            ocr_instance = None
            adb_utils_instance = None
            
            if AutoGatherModule:
                # Try to initialize PaddleOCR with robust version handling
                try:
                    from paddleocr import PaddleOCR
                    import inspect
                    
                    # Check PaddleOCR constructor parameters to determine version compatibility
                    ocr_init_params = inspect.signature(PaddleOCR.__init__).parameters
                    
                    # Build initialization parameters based on what's supported
                    init_kwargs = {
                        'use_angle_cls': True,
                        'lang': 'en'
                    }
                    
                    # Only add show_log if it's supported (older versions)
                    if 'show_log' in ocr_init_params:
                        init_kwargs['show_log'] = False
                        print("[ModuleManager] Using PaddleOCR with show_log parameter (older version)")
                    else:
                        print("[ModuleManager] Using PaddleOCR without show_log parameter (newer version)")
                    
                    # Add other common parameters if supported
                    if 'use_gpu' in ocr_init_params:
                        init_kwargs['use_gpu'] = False  # Default to CPU for compatibility
                    
                    # Initialize PaddleOCR with compatible parameters
                    ocr_instance = PaddleOCR(**init_kwargs)
                    print("[ModuleManager] ✅ PaddleOCR initialized successfully")
                    
                except ImportError:
                    print("[ModuleManager] ⚠️ PaddleOCR not available - install with: pip install paddleocr")
                    print("[ModuleManager] ⚠️ AutoGather will be disabled")
                    AutoGatherModule = None
                    ocr_instance = None
                except Exception as e:
                    print(f"[ModuleManager] ⚠️ PaddleOCR initialization failed: {e}")
                    print("[ModuleManager] ⚠️ AutoGather will be disabled")
                    AutoGatherModule = None
                    ocr_instance = None
                
                # Initialize ADB utils
                if AutoGatherModule:
                    try:
                        adb_utils_instance = ADBUtils()
                        print("[ModuleManager] ✅ ADB utils initialized successfully")
                    except Exception as e:
                        print(f"[ModuleManager] ⚠️ ADB utils initialization failed: {e}")
                        AutoGatherModule = None
            
            # Create modules for each instance
            instances = self.app.instance_manager.get_instances()
            for instance in instances:
                self._create_instance_modules(
                    instance["name"], 
                    AutoStartGameModule, 
                    AutoGatherModule,
                    ocr_instance,
                    adb_utils_instance
                )
            
            self.initialization_complete = True
            print(f"[ModuleManager] ✅ Ready for {len(instances)} instances")
            self.app.add_console_message(f"✅ Module system ready for {len(self.instance_modules)} instances")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Init error: {e}")
            self.initialization_complete = True
    
    def _create_instance_modules(self, instance_name: str, AutoStartGameModule, AutoGatherModule=None, ocr=None, adb_utils=None):
        """Create modules for single instance with proper parameters"""
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
            
            # AutoGather module - FIXED creation with all required parameters
            if AutoGatherModule and ocr and adb_utils and settings.get("auto_gather", {}).get("enabled", True):
                try:
                    # Get instance info for AutoGather
                    instance = self.app.instance_manager.get_instance(instance_name)
                    if instance:
                        instance_index = instance.get("index", 0)
                        
                        # Create AutoGather with ALL required parameters
                        gather = AutoGatherModule(
                            instance_name=instance_name,
                            instance_index=instance_index,
                            ocr=ocr,  # Required parameter
                            adb_utils=adb_utils,  # Required parameter
                            logger=None,  # Optional - will use log_callback
                            log_callback=self.app.add_console_message  # Use this for logging
                        )
                        self.instance_modules[instance_name]["AutoGather"] = gather
                        self.running_modules[instance_name]["AutoGather"] = False
                        print(f"[ModuleManager] ✅ AutoGather created for {instance_name} (index: {instance_index})")
                    else:
                        print(f"[ModuleManager] ❌ Could not find instance {instance_name} for AutoGather")
                except Exception as gather_error:
                    print(f"[ModuleManager] ❌ Error creating AutoGather for {instance_name}: {gather_error}")
            elif AutoGatherModule and settings.get("auto_gather", {}).get("enabled", True):
                if not ocr:
                    print(f"[ModuleManager] ⚠️ AutoGather disabled for {instance_name}: OCR not available")
                if not adb_utils:
                    print(f"[ModuleManager] ⚠️ AutoGather disabled for {instance_name}: ADB utils not available")
            
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
            print(f"[ModuleManager] ⚠️ Module system not ready for {instance_name}")
            return
        
        if self._recently_completed(instance_name):
            print(f"[ModuleManager] ⏸️ AutoStart recently completed for {instance_name}")
            return
        
        print(f"[ModuleManager] 🎯 Auto-startup triggered for {instance_name}")
        self.app.add_console_message(f"🔍 Triggering modules for {instance_name}...")
        
        # Start AutoStart after a delay to ensure instance is fully ready
        self.app.after(8000, lambda: self._start_autostart(instance_name))
    
    def _start_autostart(self, instance_name: str):
        """Start AutoStart module"""
        try:
            settings = self.settings_cache.get(instance_name, {})
            auto_startup_enabled = settings.get("autostart_game", {}).get("auto_startup", False)
            
            print(f"[ModuleManager] AutoStart settings for {instance_name}: auto_startup={auto_startup_enabled}")
            
            if not auto_startup_enabled:
                print(f"[ModuleManager] Auto-startup disabled for {instance_name}")
                # Even if auto-startup is disabled, we might want to start AutoGather
                self.app.after(2000, lambda: self._start_autogather(instance_name))
                return
            
            if instance_name not in self.instance_modules:
                print(f"[ModuleManager] ❌ No modules found for {instance_name}")
                return
            
            autostart = self.instance_modules[instance_name].get("AutoStartGame")
            if not autostart:
                print(f"[ModuleManager] ❌ AutoStart module not found for {instance_name}")
                return
            
            # Verify instance is ready
            def check_and_start():
                instance = self.app.instance_manager.get_instance(instance_name)
                if instance and instance["status"] == "Running":
                    self._execute_autostart(instance_name, autostart, settings)
                else:
                    print(f"[ModuleManager] Instance {instance_name} not ready (status: {instance.get('status', 'Unknown') if instance else 'Not found'})")
            
            check_and_start()
            
        except Exception as e:
            print(f"[ModuleManager] ❌ AutoStart error: {e}")
    
    def _execute_autostart(self, instance_name: str, autostart_module, settings: dict):
        """Execute AutoStart with completion callback"""
        try:
            print(f"[ModuleManager] 🚀 Starting AutoStart for {instance_name}")
            self.app.add_console_message(f"🎮 Starting AutoStart for {instance_name}...")
            
            def on_complete(success: bool):
                print(f"[ModuleManager] AutoStart completion callback: success={success}")
                if success:
                    self.app.add_console_message(f"✅ AutoStart completed for {instance_name}")
                    self._mark_completed(instance_name)
                    # Start AutoGather after successful AutoStart
                    print(f"[ModuleManager] 📅 Scheduling AutoGather start for {instance_name}")
                    self.app.after(3000, lambda: self._start_autogather(instance_name))
                else:
                    self.app.add_console_message(f"❌ AutoStart failed for {instance_name}")
                    # Even if AutoStart fails, we might still want to try AutoGather
                    print(f"[ModuleManager] 📅 Scheduling AutoGather start despite AutoStart failure")
                    self.app.after(5000, lambda: self._start_autogather(instance_name))
            
            max_retries = settings.get("autostart_game", {}).get("max_retries", 3)
            success = autostart_module.start_auto_game(
                instance_name=instance_name,
                max_retries=max_retries,
                on_complete=on_complete
            )
            
            if success:
                self.running_modules[instance_name]["AutoStartGame"] = True
                print(f"[ModuleManager] ✅ AutoStart initiated for {instance_name}")
            else:
                print(f"[ModuleManager] ❌ Failed to initiate AutoStart for {instance_name}")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ Execute AutoStart error: {e}")
    
    def _start_autogather(self, instance_name: str):
        """Auto-start AutoGather after AutoStart completes or independently"""
        try:
            print(f"[ModuleManager] 🔍 Checking AutoGather for {instance_name}")
            
            # Check if we have AutoGather module
            if (instance_name not in self.instance_modules or 
                "AutoGather" not in self.instance_modules[instance_name]):
                print(f"[ModuleManager] ❌ No AutoGather module for {instance_name}")
                return
            
            # Check settings
            settings = self.settings_cache.get(instance_name, {})
            gather_enabled = settings.get("auto_gather", {}).get("enabled", True)
            
            print(f"[ModuleManager] AutoGather settings for {instance_name}: enabled={gather_enabled}")
            
            if not gather_enabled:
                print(f"[ModuleManager] AutoGather disabled for {instance_name}")
                return
            
            # Check if already running
            if self.running_modules[instance_name].get("AutoGather", False):
                print(f"[ModuleManager] AutoGather already running for {instance_name}")
                return
            
            # Verify instance is still running
            instance = self.app.instance_manager.get_instance(instance_name)
            if not instance or instance["status"] != "Running":
                print(f"[ModuleManager] Instance {instance_name} not running, skipping AutoGather")
                return
            
            print(f"[ModuleManager] 🌾 Starting AutoGather for {instance_name}")
            self.app.add_console_message(f"🌾 Starting AutoGather for {instance_name}...")
            
            gather = self.instance_modules[instance_name]["AutoGather"]
            
            # Start AutoGather
            gather.start()  # AutoGather.start() doesn't return a value, it's void
            
            # Mark as running
            self.running_modules[instance_name]["AutoGather"] = True
            self.app.add_console_message(f"✅ AutoGather started for {instance_name}")
            print(f"[ModuleManager] ✅ AutoGather successfully started for {instance_name}")
                
        except Exception as e:
            print(f"[ModuleManager] ❌ AutoGather start error for {instance_name}: {e}")
            self.app.add_console_message(f"❌ AutoGather error for {instance_name}: {str(e)}")
    
    def cleanup_for_stopped_instance(self, instance_name: str):
        """Clean up when instance stops"""
        try:
            print(f"[ModuleManager] 🧹 Cleaning up modules for stopped instance: {instance_name}")
            
            if instance_name not in self.instance_modules:
                return
            
            modules = self.instance_modules[instance_name]
            for module_name, module in modules.items():
                try:
                    print(f"[ModuleManager] Stopping {module_name} for {instance_name}")
                    if hasattr(module, 'stop'):
                        module.stop()
                    if hasattr(module, 'cleanup_for_stopped_instance'):
                        module.cleanup_for_stopped_instance()
                    self.running_modules[instance_name][module_name] = False
                    print(f"[ModuleManager] ✅ {module_name} stopped for {instance_name}")
                except Exception as e:
                    print(f"[ModuleManager] Error stopping {module_name}: {e}")
            
            # Clear completion tracking
            self.autostart_completed.pop(instance_name, None)
            print(f"[ModuleManager] ✅ Cleanup completed for {instance_name}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Cleanup error: {e}")
    
    def refresh_modules(self):
        """Refresh modules when instances change"""
        try:
            print("[ModuleManager] 🔄 Refreshing modules...")
            current_instances = self.app.instance_manager.get_instances()
            current_names = [inst["name"] for inst in current_instances]
            
            # Remove modules for deleted instances
            for instance_name in list(self.instance_modules.keys()):
                if instance_name not in current_names:
                    print(f"[ModuleManager] Removing modules for deleted instance: {instance_name}")
                    self.cleanup_for_stopped_instance(instance_name)
                    del self.instance_modules[instance_name]
                    self.settings_cache.pop(instance_name, None)
                    self.running_modules.pop(instance_name, None)
            
            # Add modules for new instances
            for instance in current_instances:
                if instance["name"] not in self.instance_modules:
                    print(f"[ModuleManager] Creating modules for new instance: {instance['name']}")
                    try:
                        from modules.autostart_game import AutoStartGameModule
                        try:
                            from modules.auto_gather import AutoGather
                            AutoGatherModule = AutoGather
                        except ImportError:
                            AutoGatherModule = None
                        
                        # Re-initialize dependencies for new instances
                        ocr_instance = None
                        adb_utils_instance = None
                        
                        if AutoGatherModule:
                            try:
                                from paddleocr import PaddleOCR
                                import inspect
                                
                                # Robust PaddleOCR initialization for refresh
                                ocr_init_params = inspect.signature(PaddleOCR.__init__).parameters
                                init_kwargs = {'use_angle_cls': True, 'lang': 'en'}
                                
                                if 'show_log' in ocr_init_params:
                                    init_kwargs['show_log'] = False
                                if 'use_gpu' in ocr_init_params:
                                    init_kwargs['use_gpu'] = False
                                
                                ocr_instance = PaddleOCR(**init_kwargs)
                                adb_utils_instance = ADBUtils()
                                print("[ModuleManager] ✅ PaddleOCR reinitialized for new instance")
                            except Exception as e:
                                print(f"[ModuleManager] ❌ Failed to reinitialize dependencies: {e}")
                                AutoGatherModule = None
                        
                        self._create_instance_modules(
                            instance["name"], 
                            AutoStartGameModule, 
                            AutoGatherModule,
                            ocr_instance,
                            adb_utils_instance
                        )
                    except Exception as e:
                        print(f"[ModuleManager] ❌ Failed to create modules: {e}")
            
            print("[ModuleManager] ✅ Module refresh completed")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Refresh error: {e}")
    
    def reload_instance_settings(self, instance_name: str):
        """Reload settings when changed - FIXED VERSION"""
        try:
            print(f"[ModuleManager] 🔄 Reloading settings for {instance_name}")
            
            # Load fresh settings from file
            old_settings = self.settings_cache.get(instance_name, {})
            new_settings = self._load_settings(instance_name)
            self.settings_cache[instance_name] = new_settings
            
            # Update AutoGather module settings if it exists and settings changed
            if (instance_name in self.instance_modules and 
                "AutoGather" in self.instance_modules[instance_name]):
                
                autogather_module = self.instance_modules[instance_name]["AutoGather"]
                
                # Check if AutoGather settings changed
                old_gather = old_settings.get("auto_gather", {})
                new_gather = new_settings.get("auto_gather", {})
                
                if old_gather != new_gather:
                    print(f"[ModuleManager] AutoGather settings changed for {instance_name}")
                    if hasattr(autogather_module, 'update_settings'):
                        try:
                            autogather_module.update_settings(new_gather)
                            print(f"[ModuleManager] ✅ AutoGather settings updated for {instance_name}")
                        except Exception as e:
                            print(f"[ModuleManager] ❌ Error updating AutoGather settings: {e}")
                    
                    # If module was disabled, stop it
                    if not new_gather.get("enabled", True) and self.running_modules[instance_name].get("AutoGather", False):
                        try:
                            autogather_module.stop()
                            self.running_modules[instance_name]["AutoGather"] = False
                            print(f"[ModuleManager] ✅ AutoGather stopped for {instance_name} (disabled)")
                        except Exception as e:
                            print(f"[ModuleManager] ❌ Error stopping AutoGather: {e}")
                    
                    # If module was enabled and instance is running, start it
                    elif (new_gather.get("enabled", True) and 
                          not self.running_modules[instance_name].get("AutoGather", False)):
                        instance = self.app.instance_manager.get_instance(instance_name)
                        if instance and instance["status"] == "Running":
                            try:
                                autogather_module.start()
                                self.running_modules[instance_name]["AutoGather"] = True
                                print(f"[ModuleManager] ✅ AutoGather started for {instance_name} (enabled)")
                            except Exception as e:
                                print(f"[ModuleManager] ❌ Error starting AutoGather: {e}")
            
            print(f"[ModuleManager] ✅ Settings reloaded for {instance_name}")
            
        except Exception as e:
            print(f"[ModuleManager] ❌ Settings reload error: {e}")
    
    def stop_all_modules(self):
        """Stop all modules"""
        print("[ModuleManager] 🛑 Stopping all modules...")
        for instance_name in list(self.instance_modules.keys()):
            self.cleanup_for_stopped_instance(instance_name)
        print("[ModuleManager] ✅ All modules stopped")
    
    def get_module_status(self, instance_name: str) -> Dict:
        """Get status of all modules for an instance"""
        try:
            if instance_name not in self.instance_modules:
                return {}
            
            status = {}
            modules = self.instance_modules[instance_name]
            running = self.running_modules.get(instance_name, {})
            
            for module_name, module in modules.items():
                is_running = running.get(module_name, False)
                has_start_method = hasattr(module, 'start')
                has_stop_method = hasattr(module, 'stop')
                
                status[module_name] = {
                    'available': True,
                    'running': is_running,
                    'can_start': has_start_method,
                    'can_stop': has_stop_method
                }
            
            return status
            
        except Exception as e:
            print(f"[ModuleManager] Error getting status: {e}")
            return {}
    
    def manual_start_autogather(self, instance_name: str):
        """Manually start AutoGather for testing"""
        print(f"[ModuleManager] 🔧 Manual AutoGather start requested for {instance_name}")
        self._start_autogather(instance_name)
    
    def manual_stop_autogather(self, instance_name: str):
        """Manually stop AutoGather"""
        try:
            if (instance_name in self.instance_modules and 
                "AutoGather" in self.instance_modules[instance_name]):
                
                autogather_module = self.instance_modules[instance_name]["AutoGather"]
                autogather_module.stop()
                self.running_modules[instance_name]["AutoGather"] = False
                print(f"[ModuleManager] ✅ AutoGather manually stopped for {instance_name}")
                return True
            else:
                print(f"[ModuleManager] ❌ No AutoGather module found for {instance_name}")
                return False
        except Exception as e:
            print(f"[ModuleManager] ❌ Error manually stopping AutoGather: {e}")
            return False
    
    def get_autogather_settings(self, instance_name: str) -> Dict:
        """Get current AutoGather settings for an instance"""
        try:
            if (instance_name in self.instance_modules and 
                "AutoGather" in self.instance_modules[instance_name]):
                
                autogather_module = self.instance_modules[instance_name]["AutoGather"]
                if hasattr(autogather_module, 'get_current_settings'):
                    return autogather_module.get_current_settings()
                elif hasattr(autogather_module, 'settings'):
                    return autogather_module.settings
            
            # Fallback to cached settings
            return self.settings_cache.get(instance_name, {}).get("auto_gather", {})
            
        except Exception as e:
            print(f"[ModuleManager] Error getting AutoGather settings: {e}")
            return {}
    
    # Helper methods
    def _recently_completed(self, instance_name: str) -> bool:
        """Check if AutoStart completed recently"""
        if instance_name not in self.autostart_completed:
            return False
        elapsed = time.time() - self.autostart_completed[instance_name]
        return elapsed < 300  # 5 minutes
    
    def _mark_completed(self, instance_name: str):
        """Mark AutoStart as completed"""
        self.autostart_completed[instance_name] = time.time()
        print(f"[ModuleManager] ✅ Marked AutoStart completed for {instance_name}")
    
    def _load_settings(self, instance_name: str) -> Dict:
        """Load settings for instance"""
        settings_file = f"settings_{instance_name}.json"
        defaults = {
            "autostart_game": {
                "auto_startup": False, 
                "max_retries": 3, 
                "enabled": True,
                "retry_delay": 10
            },
            "auto_gather": {
                "enabled": True, 
                "check_interval": 60,
                "resource_types": ["food", "wood", "iron", "stone"],
                "resource_loop": ["food", "wood", "iron", "stone"],
                "max_queues": 6,
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
                    
                # Merge with defaults to ensure all keys exist
                for key, value in defaults.items():
                    if key not in settings:
                        settings[key] = value
                    else:
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                                
                return settings
        except Exception as e:
            print(f"[ModuleManager] Settings load error for {instance_name}: {e}")
        
        return defaults


class ADBUtils:
    """Simple ADB utilities class for AutoGather"""
    
    def __init__(self):
        self.MEMUC_PATH = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
    
    def run_adb_command(self, instance_index: int, command: str) -> str:
        """Run ADB command and return output"""
        try:
            import subprocess
            cmd = [self.MEMUC_PATH, "adb", "-i", str(instance_index), "shell"] + command.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
    
    def run_adb_command_raw(self, instance_index: int, command: str) -> str:
        """Run raw ADB command"""
        try:
            import subprocess
            cmd = [self.MEMUC_PATH, "adb", "-i", str(instance_index)] + command.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
    
    def get_screenshot_data(self, instance_index: int) -> bytes:
        """Get screenshot data as bytes"""
        try:
            import subprocess
            cmd = [self.MEMUC_PATH, "adb", "-i", str(instance_index), "shell", "screencap", "-p"]
            result = subprocess.run(cmd, capture_output=True, timeout=15)
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None