"""
BENSON v2.0 - Base Module System
Provides the foundation for all automation modules
"""

import os
import threading
import time
import subprocess
import tempfile
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum


class ModuleStatus(Enum):
    """Module execution status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    PAUSED = "paused"


class ModulePriority(Enum):
    """Module execution priority"""
    CRITICAL = 1  # AutoStartGame
    HIGH = 2      # AutoGather
    MEDIUM = 3    # AutoTrain
    LOW = 4       # AutoMail
    BACKGROUND = 5


class BaseModule:
    """Base class for all automation modules"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback: Callable = None):
        self.instance_name = instance_name
        self.shared_resources = shared_resources
        self.console_callback = console_callback or print
        
        # Module identification
        self.module_name = "BaseModule"
        self.version = "1.0.0"
        
        # Execution state
        self.status = ModuleStatus.STOPPED
        self.enabled = True
        self.check_interval = 30  # seconds
        self.max_retries = 3
        self.retry_count = 0
        
        # Threading
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.last_execution = None
        self.next_execution = None
        
        # Statistics
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        self.last_error = None
        
        # Shared state
        self.shared_state = {}
    
    def get_module_priority(self) -> ModulePriority:
        """Get module priority - override in subclasses"""
        return ModulePriority.MEDIUM
    
    def get_dependencies(self) -> List[str]:
        """Get list of module dependencies - override in subclasses"""
        return []
    
    def is_available(self) -> bool:
        """Check if module can run - override in subclasses"""
        return True
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies - override in subclasses"""
        return []
    
    def start(self) -> bool:
        """Start the module"""
        try:
            if self.status in [ModuleStatus.RUNNING, ModuleStatus.STARTING]:
                self.log_message("Module already running or starting")
                return True
            
            if not self.is_available():
                missing = self.get_missing_dependencies()
                self.log_message(f"Cannot start - missing dependencies: {missing}")
                return False
            
            self.status = ModuleStatus.STARTING
            self.stop_event.clear()
            self.retry_count = 0
            self.start_time = datetime.now()
            
            # Start worker thread
            self.worker_thread = threading.Thread(
                target=self._worker_loop,
                name=f"{self.module_name}-{self.instance_name}",
                daemon=True
            )
            self.worker_thread.start()
            
            self.log_message(f"Started {self.module_name}")
            return True
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"Failed to start: {e}", "error")
            return False
    
    def stop(self) -> bool:
        """Stop the module"""
        try:
            if self.status == ModuleStatus.STOPPED:
                return True
            
            self.status = ModuleStatus.STOPPING
            self.stop_event.set()
            
            # Wait for worker thread to finish
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=10)
                
                if self.worker_thread.is_alive():
                    self.log_message("Warning: Worker thread did not stop gracefully")
            
            self.status = ModuleStatus.STOPPED
            self.log_message(f"Stopped {self.module_name}")
            return True
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"Error stopping: {e}", "error")
            return False
    
    def pause(self):
        """Pause module execution"""
        if self.status == ModuleStatus.RUNNING:
            self.status = ModuleStatus.PAUSED
            self.log_message(f"Paused {self.module_name}")
    
    def resume(self):
        """Resume module execution"""
        if self.status == ModuleStatus.PAUSED:
            self.status = ModuleStatus.RUNNING
            self.log_message(f"Resumed {self.module_name}")
    
    def _worker_loop(self):
        """Main worker loop"""
        try:
            self.status = ModuleStatus.RUNNING
            
            while not self.stop_event.is_set():
                try:
                    if self.status == ModuleStatus.RUNNING:
                        # Execute module cycle
                        cycle_start = time.time()
                        success = self.execute_cycle()
                        cycle_time = time.time() - cycle_start
                        
                        self.execution_count += 1
                        self.last_execution = datetime.now()
                        
                        if success:
                            self.success_count += 1
                            self.retry_count = 0
                        else:
                            self.error_count += 1
                            self.retry_count += 1
                            
                            if self.retry_count >= self.max_retries:
                                self.log_message(f"Max retries exceeded, stopping module")
                                break
                        
                        # Calculate next execution time
                        sleep_time = max(0, self.check_interval - cycle_time)
                        self.next_execution = datetime.now().timestamp() + sleep_time
                    
                    # Sleep with interruption check
                    for _ in range(int(self.check_interval * 10)):  # Check every 0.1 seconds
                        if self.stop_event.is_set():
                            break
                        time.sleep(0.1)
                        
                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.log_message(f"Cycle error: {e}", "error")
                    
                    # Sleep before retry
                    time.sleep(min(self.check_interval, 30))
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"Worker loop error: {e}", "error")
        finally:
            if self.status != ModuleStatus.STOPPING:
                self.status = ModuleStatus.STOPPED
    
    def execute_cycle(self) -> bool:
        """Execute one cycle of module logic - override in subclasses"""
        self.log_message("Base module cycle executed")
        return True
    
    def log_message(self, message: str, level: str = "info"):
        """Log a message"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [{self.module_name}-{self.instance_name}] {message}"
        
        if self.console_callback:
            self.console_callback(formatted_message)
        
        print(formatted_message)
    
    def get_status_info(self) -> Dict:
        """Get detailed status information"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "module_name": self.module_name,
            "instance_name": self.instance_name,
            "status": self.status.value,
            "enabled": self.enabled,
            "available": self.is_available(),
            "priority": self.get_module_priority().value,
            "dependencies": self.get_dependencies(),
            "missing_dependencies": self.get_missing_dependencies(),
            "check_interval": self.check_interval,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "next_execution": datetime.fromtimestamp(self.next_execution).isoformat() if self.next_execution else None,
            "uptime_seconds": uptime,
            "last_error": self.last_error
        }
    
    # Utility methods for subclasses
    def get_screenshot(self) -> Optional[str]:
        """Take screenshot of the instance"""
        try:
            # Get instance index
            if not hasattr(self.shared_resources, 'get_instance'):
                return None
            
            instance = self.shared_resources.get_instance(self.instance_name)
            if not instance:
                return None
            
            instance_index = instance.get("index")
            if instance_index is None:
                return None
            
            # Take screenshot using MEmu ADB
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"module_screenshot_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/module_screen.png"
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Take screenshot on device
            capture_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "screencap", "-p", device_screenshot
            ]
            
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            if capture_result.returncode != 0:
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot from device
            pull_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "pull", device_screenshot, local_screenshot
            ]
            
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            if pull_result.returncode != 0:
                return None
            
            # Clean up device screenshot
            cleanup_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "rm", device_screenshot
            ]
            
            try:
                subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
            except:
                pass
            
            # Verify screenshot exists
            if os.path.exists(local_screenshot) and os.path.getsize(local_screenshot) > 10000:
                return local_screenshot
            
            return None
            
        except Exception as e:
            self.log_message(f"Screenshot error: {e}", "error")
            return None
    
    def click_position(self, x: int, y: int) -> bool:
        """Click at specific coordinates"""
        try:
            instance = self.shared_resources.get_instance(self.instance_name)
            if not instance:
                return False
            
            instance_index = instance.get("index")
            if instance_index is None:
                return False
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Use ADB to tap at position
            tap_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            self.log_message(f"Click error at ({x}, {y}): {e}", "error")
            return False
    
    def get_game_state(self, key: str) -> Any:
        """Get shared game state"""
        return self.shared_state.get(key)
    
    def update_game_state(self, updates: Dict):
        """Update shared game state"""
        self.shared_state.update(updates)


class ConcurrentModuleManager:
    """Manages multiple modules running concurrently for a single instance"""
    
    def __init__(self, instance_name: str, instance_manager, console_callback: Callable = None):
        self.instance_name = instance_name
        self.instance_manager = instance_manager
        self.console_callback = console_callback or print
        
        # Module registry
        self.modules = {}  # module_name -> module_instance
        self.module_classes = {}  # module_name -> (class, config)
        
        # Shared resources and state
        self.shared_state = {}
        
        # Manager state
        self.running = False
        self.lock = threading.Lock()
    
    def register_module(self, module_class, **config):
        """Register a module class with configuration"""
        module_name = module_class.__name__
        self.module_classes[module_name] = (module_class, config)
        self.log_message(f"Registered module: {module_name}")
    
    def start_all_enabled(self) -> bool:
        """Start all enabled modules"""
        with self.lock:
            try:
                success_count = 0
                
                # Sort modules by priority
                sorted_modules = sorted(
                    self.module_classes.items(),
                    key=lambda x: self._get_module_priority(x[1][0])
                )
                
                for module_name, (module_class, config) in sorted_modules:
                    if config.get("enabled", True):
                        if self._start_module_internal(module_name, module_class, config):
                            success_count += 1
                            time.sleep(1)  # Stagger starts
                
                self.running = success_count > 0
                
                if success_count > 0:
                    self.log_message(f"Started {success_count}/{len(self.module_classes)} modules")
                
                return success_count > 0
                
            except Exception as e:
                self.log_message(f"Error starting modules: {e}", "error")
                return False
    
    def stop_all(self) -> bool:
        """Stop all running modules"""
        with self.lock:
            try:
                stop_count = 0
                
                for module_name, module in list(self.modules.items()):
                    if module.stop():
                        stop_count += 1
                
                self.modules.clear()
                self.running = False
                
                if stop_count > 0:
                    self.log_message(f"Stopped {stop_count} modules")
                
                return True
                
            except Exception as e:
                self.log_message(f"Error stopping modules: {e}", "error")
                return False
    
    def start_module(self, module_name: str) -> bool:
        """Start a specific module"""
        with self.lock:
            if module_name in self.modules:
                return True  # Already running
            
            if module_name not in self.module_classes:
                self.log_message(f"Module {module_name} not registered")
                return False
            
            module_class, config = self.module_classes[module_name]
            return self._start_module_internal(module_name, module_class, config)
    
    def stop_module(self, module_name: str) -> bool:
        """Stop a specific module"""
        with self.lock:
            if module_name not in self.modules:
                return True  # Already stopped
            
            module = self.modules[module_name]
            success = module.stop()
            
            if success:
                del self.modules[module_name]
            
            return success
    
    def _start_module_internal(self, module_name: str, module_class, config) -> bool:
        """Internal method to start a module"""
        try:
            # Create module instance
            module = module_class(
                instance_name=self.instance_name,
                shared_resources=self.instance_manager,
                console_callback=self.console_callback
            )
            
            # Apply configuration
            for key, value in config.items():
                if hasattr(module, key):
                    setattr(module, key, value)
            
            # Set shared state
            module.shared_state = self.shared_state
            
            # Start module
            if module.start():
                self.modules[module_name] = module
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"Error starting {module_name}: {e}", "error")
            return False
    
    def _get_module_priority(self, module_class) -> int:
        """Get module priority for sorting"""
        try:
            # Create temporary instance to get priority
            temp_module = module_class("temp", None, None)
            return temp_module.get_module_priority().value
        except:
            return ModulePriority.MEDIUM.value
    
    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        with self.lock:
            running_modules = len([m for m in self.modules.values() if m.status == ModuleStatus.RUNNING])
            
            module_statuses = {}
            for name, module in self.modules.items():
                module_statuses[name] = module.get_status_info()
            
            return {
                "instance_name": self.instance_name,
                "manager_running": self.running,
                "total_modules": len(self.module_classes),
                "registered_modules": list(self.module_classes.keys()),
                "running_modules": running_modules,
                "active_modules": list(self.modules.keys()),
                "module_statuses": module_statuses,
                "shared_state_keys": list(self.shared_state.keys())
            }
    
    def log_message(self, message: str, level: str = "info"):
        """Log a message"""
        formatted_message = f"[ModuleManager-{self.instance_name}] {message}"
        
        if self.console_callback:
            self.console_callback(formatted_message)
        
        print(formatted_message)