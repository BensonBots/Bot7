"""
BENSON v2.0 - FIXED AutoStartGame Module with Proper Module Communication
Ensures AutoGather starts after successful completion
"""

import os
import time
import threading
import subprocess
from typing import Optional, Dict, List, Callable
from datetime import datetime
import logging

# Safe imports
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class AutoStartGameModule:
    """FIXED: AutoStartGame with proper module communication"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback: Callable = None):
        self.instance_name = instance_name
        self.instance_manager = shared_resources
        self.console_callback = console_callback or print
        
        # FIXED: Proper shared state management
        self.shared_state = getattr(shared_resources, 'shared_state', {})
        if not hasattr(shared_resources, 'shared_state'):
            shared_resources.shared_state = {}
            self.shared_state = shared_resources.shared_state
        
        # Module state tracking
        self.running_tasks = {}
        self.template_cache = {}
        
        # CRITICAL: Track completion properly
        self.game_start_completed = False
        self.last_successful_start = None
        
        # Configuration
        self.templates_dir = "templates"
        self.confidence_threshold = 0.6
        self.default_max_retries = 3
        self.retry_delay = 10
        self.game_load_timeout = 90
        
        # Game state indicators
        self.MAIN_MENU_INDICATORS = ["game_launcher.png"]
        self.GAME_WORLD_INDICATORS = [
            "world.png", "world_icon.png", "town_icon.png", "game_icon.png",
            "home_button.png", "castle.png", "build_button.png", "march_button.png"
        ]
        self.CLOSE_BUTTONS = [
            "close_x.png", "close_x2.png", "close_btn.png", "cancel_btn.png", "ok_btn.png"
        ]
        
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Only log initialization once per instance
        if not hasattr(self.__class__, f'_init_logged_{instance_name}'):
            self.log_message(f"✅ AutoStartGame module initialized for {instance_name}")
            setattr(self.__class__, f'_init_logged_{instance_name}', True)
    
    def log_message(self, message: str):
        """Log message with spam reduction"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} [AutoStartGame-{self.instance_name}] {message}"
        if self.console_callback:
            self.console_callback(full_message)
    
    def start_auto_game(self, instance_name: str = None, max_retries: int = None, 
                       on_complete: Callable = None) -> bool:
        """Start auto game with proper completion signaling"""
        target_instance = instance_name or self.instance_name
        
        # Check if already completed recently
        if self.game_start_completed and self.last_successful_start:
            time_since_success = (datetime.now() - self.last_successful_start).total_seconds()
            if time_since_success < 300:  # 5 minutes
                self.log_message(f"⏸ Game already started successfully {int(time_since_success)}s ago")
                if on_complete:
                    on_complete(True)
                return True
        
        # Check if game is already running
        if self._is_game_already_running():
            self.log_message(f"✅ Game already running for {target_instance}")
            if self._verify_stable_game_state():
                self._mark_success_and_notify(on_complete)
                return True
        
        # Start the actual game launch process
        def run_task():
            try:
                self.log_message(f"🚀 Starting AutoStartGame task for {target_instance}")
                success = self._run_complete_game_start(target_instance, max_retries or self.default_max_retries)
                
                if success:
                    self._mark_success_and_notify(on_complete)
                else:
                    self.log_message(f"❌ AutoStartGame failed for {target_instance}")
                    if on_complete:
                        on_complete(False)
                        
                self.log_message(f"🏁 AutoStartGame task completed for {target_instance}: {'SUCCESS' if success else 'FAILED'}")
                    
            except Exception as e:
                self.log_message(f"❌ {target_instance} AutoStartGame error: {str(e)}")
                if on_complete:
                    on_complete(False)
        
        threading.Thread(target=run_task, daemon=True, name=f"AutoStart-{target_instance}").start()
        return True
    
    def _mark_success_and_notify(self, on_complete: Callable = None):
        """FIXED: Mark success and properly notify other modules"""
        self.game_start_completed = True
        self.last_successful_start = datetime.now()
        
        # CRITICAL: Set shared state for other modules
        self._set_game_accessible_state(True)
        
        # Notify completion callback
        if on_complete:
            on_complete(True)
        
        self.log_message(f"✅ Game accessible - other modules can now start")
    
    def _set_game_accessible_state(self, accessible: bool):
        """FIXED: Properly set shared state for module communication"""
        try:
            # Set multiple state indicators for reliability
            state_keys = [
                f"game_accessible_{self.instance_name}",
                f"game_world_active_{self.instance_name}",
                f"autostart_completed_{self.instance_name}",
                "game_accessible",  # Global key
                "game_world_active"  # Global key
            ]
            
            for key in state_keys:
                self.shared_state[key] = accessible
            
            # Set timestamp
            self.shared_state[f"last_game_check_{self.instance_name}"] = datetime.now().isoformat()
            
            # CRITICAL: Also set on instance manager if available
            if hasattr(self.instance_manager, 'set_game_state'):
                self.instance_manager.set_game_state(self.instance_name, {
                    'game_accessible': accessible,
                    'autostart_completed': accessible
                })
            
            self.log_message(f"📡 Set game accessible state: {accessible}")
            
        except Exception as e:
            self.log_message(f"⚠️ Could not set shared state: {e}")
    
    def _run_complete_game_start(self, instance_name: str, max_retries: int) -> bool:
        """Complete game start process with all steps"""
        for attempt in range(1, max_retries + 1):
            self.log_message(f"🔄 {instance_name} Auto Start attempt {attempt}/{max_retries}")
            
            if self._attempt_game_start_complete(instance_name):
                return True
            
            if attempt < max_retries:
                self.log_message(f"⏳ {instance_name} waiting {self.retry_delay}s before retry")
                time.sleep(self.retry_delay)
        
        return False
    
    def _attempt_game_start_complete(self, instance_name: str) -> bool:
        """Complete game start attempt with state detection"""
        try:
            # Get instance info
            instance = self.instance_manager.get_instance(instance_name)
            if not instance:
                return False
            
            instance_index = instance['index']
            
            # Take screenshot
            screenshot_path = self._take_screenshot(instance_index)
            if not screenshot_path:
                return False
            
            try:
                # Detect current state
                game_state = self._detect_game_state(screenshot_path)
                self.log_message(f"🔍 {instance_name} detected state: {game_state}")
                
                if game_state == "ALREADY_IN_GAME":
                    return self._verify_game_world_stable(instance_index)
                elif game_state == "MAIN_MENU":
                    return self._start_from_main_menu(screenshot_path, instance_index)
                else:
                    return self._handle_unknown_state(screenshot_path, instance_index)
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error in game start attempt: {e}")
            return False
    
    def _detect_game_state(self, screenshot_path: str) -> str:
        """Detect current game state"""
        try:
            # Check for game world first
            if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                return "ALREADY_IN_GAME"
            
            # Check for main menu
            if self._find_any_template(screenshot_path, self.MAIN_MENU_INDICATORS):
                return "MAIN_MENU"
            
            return "UNKNOWN_STATE"
            
        except Exception:
            return "UNKNOWN_STATE"
    
    def _start_from_main_menu(self, screenshot_path: str, instance_index: int) -> bool:
        """Start game from main menu"""
        try:
            self.log_message(f"🎮 {self.instance_name} starting game from main menu")
            
            # Click game launcher
            if self._click_template(screenshot_path, "game_launcher.png", instance_index):
                self.log_message(f"✅ {self.instance_name} clicked game_launcher.png")
                
                # Wait for game to load
                return self._wait_for_game_load(instance_index)
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error starting from main menu: {e}")
            return False
    
    def _wait_for_game_load(self, instance_index: int) -> bool:
        """Wait for game to load with proper state checking"""
        self.log_message(f"⏳ {self.instance_name} waiting for game to load (timeout: {self.game_load_timeout}s)")
        
        start_time = time.time()
        check_count = 0
        
        while (time.time() - start_time) < self.game_load_timeout:
            check_count += 1
            
            screenshot_path = self._take_screenshot(instance_index)
            if not screenshot_path:
                time.sleep(3)
                continue
            
            try:
                state = self._detect_game_state(screenshot_path)
                
                if state == "ALREADY_IN_GAME":
                    if self._verify_game_world_stable(instance_index):
                        self.log_message(f"✅ {self.instance_name} game loaded successfully")
                        return True
                elif state == "UNKNOWN_STATE":
                    # Try to close any dialogs
                    if check_count % 3 == 0:  # Every 3rd check
                        self._try_close_dialogs(screenshot_path, instance_index)
                
            finally:
                self._cleanup_screenshot(screenshot_path)
            
            time.sleep(3)
        
        return False
    
    def _handle_unknown_state(self, screenshot_path: str, instance_index: int) -> bool:
        """Handle unknown state by trying to close dialogs"""
        self.log_message(f"❓ {self.instance_name} unknown state (check #1, consecutive: 1)")
        
        # Try to close dialogs
        if self._try_close_dialogs(screenshot_path, instance_index):
            time.sleep(3)
            # Check if we reached game world
            new_screenshot = self._take_screenshot(instance_index)
            if new_screenshot:
                try:
                    if self._detect_game_state(new_screenshot) == "ALREADY_IN_GAME":
                        return self._verify_game_world_stable(instance_index)
                finally:
                    self._cleanup_screenshot(new_screenshot)
        
        return False
    
    def _try_close_dialogs(self, screenshot_path: str, instance_index: int) -> bool:
        """Try to close any visible dialogs"""
        for close_button in self.CLOSE_BUTTONS:
            if self._find_template_only(screenshot_path, close_button):
                if self._click_template(screenshot_path, close_button, instance_index):
                    self.log_message(f"❌ {self.instance_name} closed dialog with {close_button}")
                    return True
        return False
    
    def _verify_game_world_stable(self, instance_index: int) -> bool:
        """Verify game world is stable"""
        self.log_message(f"🔍 {self.instance_name} verifying game world stability...")
        
        stable_checks = 0
        for check in range(3):
            time.sleep(1)
            
            screenshot_path = self._take_screenshot(instance_index)
            if screenshot_path:
                try:
                    if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                        stable_checks += 1
                        self.log_message(f"✅ {self.instance_name} stability check {check + 1}/3: world_icon.png found")
                    else:
                        self.log_message(f"❌ {self.instance_name} stability check {check + 1}/3: no world icon")
                finally:
                    self._cleanup_screenshot(screenshot_path)
        
        is_stable = stable_checks >= 2
        if is_stable:
            self.log_message(f"✅ {self.instance_name} game world confirmed stable ({stable_checks}/3 checks)")
        
        return is_stable
    
    def _is_game_already_running(self) -> bool:
        """Quick check if game is already running"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance:
                return False
                
            screenshot_path = self._take_screenshot(instance['index'])
            if not screenshot_path:
                return False
            
            try:
                return self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS)
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False
    
    def _verify_stable_game_state(self) -> bool:
        """Quick stability verification"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance:
                return False
            return self._verify_game_world_stable(instance['index'])
        except Exception:
            return False
    
    # Template matching methods
    def _find_any_template(self, screenshot_path: str, template_names: List[str]) -> bool:
        """Find any template from list"""
        if not CV2_AVAILABLE:
            return False
        
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return False
            
            for template_name in template_names:
                template_path = os.path.join(self.templates_dir, template_name)
                if not os.path.exists(template_path):
                    continue
                
                template = cv2.imread(template_path)
                if template is None:
                    continue
                
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val >= self.confidence_threshold:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _find_template_only(self, screenshot_path: str, template_name: str) -> bool:
        """Find template without clicking"""
        return self._find_any_template(screenshot_path, [template_name])
    
    def _click_template(self, screenshot_path: str, template_name: str, instance_index: int) -> bool:
        """Click on template if found"""
        if not CV2_AVAILABLE:
            return False
        
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            if not os.path.exists(template_path):
                return False
            
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                return False
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                self.log_message(f"👆 Clicked position ({click_x}, {click_y})")
                return self._click_position(instance_index, click_x, click_y)
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error clicking template: {e}")
            return False
    
    def _click_position(self, instance_index: int, x: int, y: int) -> bool:
        """Click at coordinates using MEmu ADB"""
        try:
            memuc_path = self.instance_manager.MEMUC_PATH
            
            tap_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _take_screenshot(self, instance_index: int) -> Optional[str]:
        """Take screenshot using MEmu ADB"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"autostart_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/autostart_screen.png"
            
            memuc_path = self.instance_manager.MEMUC_PATH
            
            # Take screenshot
            capture_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "screencap", "-p", device_screenshot]
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            
            if capture_result.returncode != 0:
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot
            pull_cmd = [memuc_path, "adb", "-i", str(instance_index), "pull", device_screenshot, local_screenshot]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            
            if pull_result.returncode != 0:
                return None
            
            # Cleanup device
            subprocess.run([memuc_path, "adb", "-i", str(instance_index), "shell", "rm", device_screenshot], 
                          capture_output=True, timeout=5)
            
            if os.path.exists(local_screenshot) and os.path.getsize(local_screenshot) > 10000:
                return local_screenshot
            
            return None
            
        except Exception:
            return None
    
    def _cleanup_screenshot(self, screenshot_path: str):
        """Cleanup screenshot file"""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except:
            pass
    
    # Interface methods for module manager
    def cleanup_for_stopped_instance(self):
        """Cleanup when instance stops"""
        self.game_start_completed = False
        self.last_successful_start = None
        self._set_game_accessible_state(False)
        self.log_message(f"🧹 Cleaned up AutoStartGame for stopped instance")
    
    def is_game_accessible(self) -> bool:
        """Check if game is accessible for other modules"""
        return self.game_start_completed and self.last_successful_start is not None
    
    def execute_cycle(self) -> bool:
        """Execute cycle for module manager"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance or instance["status"] != "Running":
                return True
            
            # Only run if not already completed
            if not self.game_start_completed:
                return self.start_auto_game()
            
            return True
            
        except Exception:
            return False