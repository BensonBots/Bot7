"""
BENSON v2.0 - Compact Base Module System
Reduced from 300+ lines to ~120 lines with same functionality
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
    """Compact base class for all automation modules"""
    
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
        self.check_interval = 30
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
        
        self.log_message(f"✅ {self.module_name} module initialized")
    
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
            
            self.log_message(f"🚀 Starting {self.module_name}...")
            
            if not self.is_available():
                missing = self.get_missing_dependencies()
                self.log_message(f"❌ Cannot start - missing dependencies: {missing}")
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
            
            # Quick status check
            time.sleep(0.5)
            
            if self.status == ModuleStatus.RUNNING:
                self.log_message(f"✅ {self.module_name} started successfully")
                return True
            elif self.status == ModuleStatus.ERROR:
                self.log_message(f"❌ {self.module_name} failed to start: {self.last_error}")
                return False
            else:
                self.log_message(f"⏳ {self.module_name} starting...")
                return True
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"❌ Failed to start {self.module_name}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the module"""
        try:
            if self.status == ModuleStatus.STOPPED:
                self.log_message(f"{self.module_name} already stopped")
                return True
            
            self.log_message(f"🛑 Stopping {self.module_name}...")
            self.status = ModuleStatus.STOPPING
            self.stop_event.set()
            
            # Wait for worker thread
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=10)
                
                if self.worker_thread.is_alive():
                    self.log_message(f"⚠️ {self.module_name} worker thread did not stop gracefully")
            
            self.status = ModuleStatus.STOPPED
            self.log_message(f"✅ {self.module_name} stopped successfully")
            return True
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"❌ Error stopping {self.module_name}: {e}")
            return False
    
    def pause(self):
        """Pause module execution"""
        if self.status == ModuleStatus.RUNNING:
            self.status = ModuleStatus.PAUSED
            self.log_message(f"⏸️ Paused {self.module_name}")
    
    def resume(self):
        """Resume module execution"""
        if self.status == ModuleStatus.PAUSED:
            self.status = ModuleStatus.RUNNING
            self.log_message(f"▶️ Resumed {self.module_name}")
    
    def _worker_loop(self):
        """Main worker loop with compact error handling"""
        try:
            self.status = ModuleStatus.RUNNING
            self.log_message(f"🔄 {self.module_name} worker loop started")
            
            while not self.stop_event.is_set():
                try:
                    if self.status == ModuleStatus.RUNNING:
                        # Execute module cycle
                        cycle_start = time.time()
                        
                        try:
                            success = self.execute_cycle()
                        except Exception as cycle_error:
                            self.log_message(f"❌ Cycle error: {cycle_error}")
                            success = False
                        
                        cycle_time = time.time() - cycle_start
                        self.execution_count += 1
                        self.last_execution = datetime.now()
                        
                        if success:
                            self.success_count += 1
                            self.retry_count = 0
                            # Log every 10th success to reduce spam
                            if self.execution_count % 10 == 1:
                                self.log_message(f"✅ {self.module_name} cycle {self.execution_count} completed ({cycle_time:.1f}s)")
                        else:
                            self.error_count += 1
                            self.retry_count += 1
                            self.log_message(f"❌ {self.module_name} cycle {self.execution_count} failed (retry {self.retry_count}/{self.max_retries})")
                            
                            if self.retry_count >= self.max_retries:
                                self.log_message(f"🛑 {self.module_name} max retries exceeded, stopping")
                                break
                        
                        # Calculate sleep time
                        sleep_time = max(0, self.check_interval - cycle_time)
                        self.next_execution = datetime.now().timestamp() + sleep_time
                        self._safe_sleep(sleep_time)
                    
                    elif self.status == ModuleStatus.PAUSED:
                        self._safe_sleep(1)
                    else:
                        break
                        
                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.log_message(f"❌ {self.module_name} worker error: {e}")
                    self._safe_sleep(min(self.check_interval, 30))
            
            self.log_message(f"🏁 {self.module_name} worker loop ended")
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.last_error = str(e)
            self.log_message(f"❌ {self.module_name} worker fatal error: {e}")
        finally:
            if self.status != ModuleStatus.STOPPING:
                self.status = ModuleStatus.STOPPED
    
    def _safe_sleep(self, duration: float):
        """Sleep with interruption check"""
        sleep_steps = max(1, int(duration * 10))
        step_duration = duration / sleep_steps
        
        for _ in range(sleep_steps):
            if self.stop_event.is_set():
                break
            time.sleep(step_duration)
    
    def execute_cycle(self) -> bool:
        """Execute one cycle - override in subclasses"""
        self.log_message(f"📋 {self.module_name} base cycle executed")
        time.sleep(1)
        return True
    
    def log_message(self, message: str, level: str = "info"):
        """Compact log message with module context"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [{self.module_name}-{self.instance_name}] {message}"
        
        if self.console_callback:
            self.console_callback(formatted_message)
        
        print(formatted_message)
    
    def get_status_info(self) -> Dict:
        """Get compact status information"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else None
        
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
            if not hasattr(self.shared_resources, 'get_instance'):
                self.log_message("❌ No get_instance method available")
                return None
            
            instance = self.shared_resources.get_instance(self.instance_name)
            if not instance:
                self.log_message(f"❌ Instance {self.instance_name} not found")
                return None
            
            instance_index = instance.get("index")
            if instance_index is None:
                self.log_message(f"❌ No index for instance {self.instance_name}")
                return None
            
            # Take screenshot using MEmu ADB
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"module_screenshot_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/module_screen.png"
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Capture screenshot
            capture_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "screencap", "-p", device_screenshot]
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            
            if capture_result.returncode != 0:
                self.log_message(f"❌ Screenshot capture failed: {capture_result.stderr}")
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot
            pull_cmd = [memuc_path, "adb", "-i", str(instance_index), "pull", device_screenshot, local_screenshot]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            
            if pull_result.returncode != 0:
                self.log_message(f"❌ Screenshot pull failed: {pull_result.stderr}")
                return None
            
            # Cleanup device screenshot
            try:
                cleanup_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "rm", device_screenshot]
                subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
            except:
                pass
            
            # Verify screenshot
            if os.path.exists(local_screenshot) and os.path.getsize(local_screenshot) > 10000:
                self.log_message(f"📸 Screenshot taken: {os.path.basename(local_screenshot)}")
                return local_screenshot
            else:
                self.log_message(f"❌ Invalid screenshot file")
                return None
            
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
            return None
    
    def click_position(self, x: int, y: int) -> bool:
        """Click at specific coordinates"""
        try:
            instance = self.shared_resources.get_instance(self.instance_name)
            if not instance:
                self.log_message(f"❌ Instance {self.instance_name} not found for click")
                return False
            
            instance_index = instance.get("index")
            if instance_index is None:
                self.log_message(f"❌ No index for instance {self.instance_name}")
                return False
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Use ADB to tap
            tap_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "input", "tap", str(x), str(y)]
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_message(f"👆 Clicked position ({x}, {y})")
                return True
            else:
                self.log_message(f"❌ Click failed at ({x}, {y}): {result.stderr}")
                return False
            
        except Exception as e:
            self.log_message(f"❌ Click error at ({x}, {y}): {e}")
            return False
    
    def get_game_state(self, key: str) -> Any:
        """Get shared game state"""
        return self.shared_state.get(key)
    
    def update_game_state(self, updates: Dict):
        """Update shared game state"""
        self.shared_state.update(updates)
        self.log_message(f"📊 Updated game state: {list(updates.keys())}")


# Helper function for debugging
def debug_module_status(module):
    """Debug helper to print module status"""
    if hasattr(module, 'get_status_info'):
        status = module.get_status_info()
        print(f"\n=== {status['module_name']} Debug Status ===")
        print(f"Status: {status['status']}")
        print(f"Enabled: {status['enabled']}")
        print(f"Available: {status['available']}")
        print(f"Executions: {status['execution_count']} (Success: {status['success_count']}, Errors: {status['error_count']})")
        print(f"Last execution: {status['last_execution']}")
        print(f"Last error: {status['last_error']}")
        print("=" * 40)
    else:
        print(f"Module {module} doesn't have status info")