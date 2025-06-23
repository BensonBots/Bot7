"""
BENSON v2.0 - Complete AutoStartGame Module
Combines both versions with enhanced shared state management and spam reduction
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
    """Complete AutoStartGame that properly communicates with other modules and prevents spam"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback: Callable = None):
        self.instance_name = instance_name
        self.instance_manager = shared_resources
        self.console_callback = console_callback or print
        self.logger = self._setup_logging()
        
        # Module state tracking
        self.running_tasks = {}
        self.template_cache = {}
        
        # CRITICAL: Track if we've already successfully started the game
        self.game_start_completed = False
        self.last_successful_start = None
        
        # NEW: Track cleanup logging to prevent spam
        self._cleanup_logged = False
        self._last_cleanup_time = 0
        self._last_status_log = 0
        
        # Enhanced game state detection templates
        self.MAIN_MENU_INDICATORS = [
            "game_launcher.png"
        ]
        
        # Expanded game world indicators
        self.GAME_WORLD_INDICATORS = [
            "world.png",
            "world_icon.png", 
            "town_icon.png",
            "game_icon.png",
            "home_button.png",
            "castle.png",
            "build_button.png",
            "march_button.png",
            "alliance_button.png"
        ]
        
        self.PLAY_BUTTONS = [
            "game_launcher.png",
            "deploy_button.png",
            "play.png",
            "start.png",
            "play_button.png",
            "enter_game.png"
        ]
        
        # Enhanced close/dialog buttons
        self.CLOSE_BUTTONS = [
            "close_x.png",
            "close_x2.png", 
            "close_x3.png",
            "close_x4.png",
            "close_x5.png",
            "close_btn.png",
            "cancel_btn.png",
            "ok_btn.png",
            "confirm_btn.png",
            "skip_btn.png"
        ]
        
        # Loading screen indicators
        self.LOADING_INDICATORS = [
            "loading.png",
            "loading_bar.png",
            "connecting.png",
            "please_wait.png"
        ]
        
        # Configuration
        self.templates_dir = "templates"
        self.confidence_threshold = 0.6
        self.default_max_retries = 3
        self.retry_delay = 10
        
        # Enhanced timing settings - more conservative
        self.screenshot_retry_delay = 3
        self.max_screenshot_retries = 3
        self.game_load_timeout = 90
        self.dialog_check_interval = 4
        
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # FIXED: Only log initialization once
        if not hasattr(self.__class__, '_init_logged'):
            self.log_message(f"✅ AutoStartGame module initialized for {instance_name}")
            self.__class__._init_logged = True
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the module"""
        logger = logging.getLogger(f'AutoStartGame-{self.instance_name}')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(name)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_message(self, message: str):
        """FIXED: Log message with spam reduction"""
        # Filter out repetitive messages
        if self._is_spam_message(message):
            return
            
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} [AutoStartGame-{self.instance_name}] {message}"
        self.logger.info(message)
        if self.console_callback:
            self.console_callback(full_message)
    
    def _is_spam_message(self, message: str) -> bool:
        """Check if message is spam and should be filtered"""
        spam_keywords = [
            "Cleaned up AutoStartGame for stopped instance",
            "Status monitoring",
            "Checking instance status",
            "routine check",
            "periodic update",
            "execute cycle"
        ]
        
        for keyword in spam_keywords:
            if keyword in message:
                # Only allow one cleanup/status message per 60 seconds
                current_time = time.time()
                if current_time - self._last_cleanup_time < 60:
                    return True
                self._last_cleanup_time = current_time
                
        return False
    
    def is_available(self) -> bool:
        """Check if module dependencies are available"""
        if not CV2_AVAILABLE:
            return False
        
        if not hasattr(self.instance_manager, '_is_memu_available'):
            return False
            
        return self.instance_manager._is_memu_available()
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies"""
        missing = []
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        
        if not hasattr(self.instance_manager, '_is_memu_available') or not self.instance_manager._is_memu_available():
            missing.append("memu_not_available")
            
        return missing
    
    def start_auto_game(self, instance_name: str = None, max_retries: int = None, 
                       on_complete: Callable = None) -> bool:
        """SMART: Only start if game isn't already running and we haven't completed recently"""
        target_instance = instance_name or self.instance_name
        
        # CRITICAL CHECK: Don't start if we've already successfully started the game recently
        if self.game_start_completed and self.last_successful_start:
            time_since_success = (datetime.now() - self.last_successful_start).total_seconds()
            if time_since_success < 300:  # Don't restart within 5 minutes
                self.log_message(f"⏸ Game already started successfully {int(time_since_success)}s ago, skipping")
                if on_complete:
                    on_complete(True)
                return True
        
        # SMART CHECK: First verify if game is already running
        if self._is_game_already_running():
            self.log_message(f"✅ Game is already running for {target_instance}, verifying stability...")
            if self._verify_stable_game_state():
                self.game_start_completed = True
                self.last_successful_start = datetime.now()
                # NEW: Mark game as accessible for other modules
                self._mark_game_accessible()
                if on_complete:
                    on_complete(True)
                return True
            else:
                self.log_message(f"⚠️ Game detected but unstable, proceeding with start process...")
        
        if not self.is_available():
            missing_deps = self.get_missing_dependencies()
            self.log_message(f"❌ AutoStartGame not available - missing: {missing_deps}")
            return False
        
        if target_instance in self.running_tasks:
            self.log_message(f"⚠️ AutoStartGame already running for {target_instance}")
            return False
        
        instance = self.instance_manager.get_instance(target_instance)
        if not instance:
            self.log_message(f"❌ Instance {target_instance} not found")
            return False
        
        max_retries = max_retries or self.default_max_retries
        
        # Create task info
        task_info = {
            'instance_name': target_instance,
            'instance_index': instance['index'],
            'max_retries': max_retries,
            'current_attempt': 0,
            'start_time': datetime.now(),
            'status': 'starting',
            'on_complete': on_complete,
            'thread': None
        }
        
        self.running_tasks[target_instance] = task_info
        
        # Start the task in a background thread
        def run_task():
            try:
                self.log_message(f"🚀 Starting AutoStartGame task for {target_instance}")
                success = self._run_auto_start_task(task_info)
                task_info['status'] = 'completed' if success else 'failed'
                
                # Mark completion status
                if success:
                    self.game_start_completed = True
                    self.last_successful_start = datetime.now()
                    # NEW: Mark game as accessible for other modules
                    self._mark_game_accessible()
                
                if task_info['on_complete']:
                    task_info['on_complete'](success)
                    
                self.log_message(f"🏁 AutoStartGame task completed for {target_instance}: {'SUCCESS' if success else 'FAILED'}")
                    
            except Exception as e:
                self.log_message(f"❌ {target_instance} AutoStartGame error: {str(e)}")
                task_info['status'] = 'error'
            finally:
                if target_instance in self.running_tasks:
                    del self.running_tasks[target_instance]
        
        task_thread = threading.Thread(target=run_task, daemon=True, name=f"AutoStart-{target_instance}")
        task_info['thread'] = task_thread
        task_thread.start()
        
        self.log_message(f"🎮 AutoStartGame started for {target_instance}")
        return True
    
    def _mark_game_accessible(self):
        """NEW: Mark game as accessible in shared state for other modules"""
        try:
            # Set shared state for AutoGather and other modules
            if hasattr(self.instance_manager, 'shared_state'):
                if not hasattr(self.instance_manager, 'shared_state'):
                    self.instance_manager.shared_state = {}
                
                # Set game accessibility state
                game_state = {
                    f"game_accessible_{self.instance_name}": True,
                    f"game_world_active_{self.instance_name}": True,
                    f"autostart_completed_{self.instance_name}": True,
                    f"last_game_check_{self.instance_name}": datetime.now().isoformat()
                }
                
                self.instance_manager.shared_state.update(game_state)
                self.log_message("✅ Game marked as accessible for other modules")
            
            # Also try to set it directly on the instance manager
            if hasattr(self.instance_manager, 'set_game_accessible'):
                self.instance_manager.set_game_accessible(self.instance_name, True)
                
        except Exception as e:
            # Don't fail if shared state setting fails
            print(f"[AutoStartGame] Warning: Could not set shared state: {e}")
    
    def _clear_game_accessible(self):
        """NEW: Clear game accessibility when instance stops"""
        try:
            if hasattr(self.instance_manager, 'shared_state'):
                # Clear game accessibility state
                keys_to_remove = [
                    f"game_accessible_{self.instance_name}",
                    f"game_world_active_{self.instance_name}",
                    f"autostart_completed_{self.instance_name}"
                ]
                
                for key in keys_to_remove:
                    self.instance_manager.shared_state.pop(key, None)
            
            if hasattr(self.instance_manager, 'set_game_accessible'):
                self.instance_manager.set_game_accessible(self.instance_name, False)
                
        except Exception as e:
            print(f"[AutoStartGame] Warning: Could not clear shared state: {e}")
    
    def _is_game_already_running(self) -> bool:
        """SMART: Check if game is already running before starting"""
        try:
            screenshot_path = self._take_screenshot_with_retries_simple()
            if not screenshot_path:
                return False
            
            try:
                # Check for game world indicators
                if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                    self.log_message("🎮 Game world detected - game is already running")
                    return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error checking if game is running: {e}")
            return False
    
    def _take_screenshot_with_retries_simple(self) -> Optional[str]:
        """Simple screenshot with fewer retries for quick checks"""
        for attempt in range(2):
            screenshot_path = self._take_screenshot(self._get_instance_index())
            if screenshot_path:
                return screenshot_path
            time.sleep(1)
        return None
    
    def _get_instance_index(self) -> int:
        """Get instance index for this module's instance"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            return instance['index'] if instance else 1
        except:
            return 1
    
    def stop_auto_game(self, instance_name: str = None) -> bool:
        """Stop AutoStartGame for this instance"""
        target_instance = instance_name or self.instance_name
        
        if target_instance not in self.running_tasks:
            return False
        
        task_info = self.running_tasks[target_instance]
        task_info['status'] = 'stopping'
        
        # Wait a moment for graceful shutdown
        try:
            thread = task_info.get('thread')
            if thread and thread.is_alive():
                thread.join(timeout=5)
        except:
            pass
        
        # Force cleanup if still in running tasks
        if target_instance in self.running_tasks:
            del self.running_tasks[target_instance]
        
        return True
    
    def cleanup_for_stopped_instance(self):
        """FIXED: Cleanup when instance is stopped - REDUCED SPAM"""
        current_time = time.time()
        
        # Only log cleanup once per minute to prevent spam
        if current_time - self._last_cleanup_time > 60:
            self.log_message(f"🧹 Cleaned up AutoStartGame for stopped instance: {self.instance_name}")
            self._last_cleanup_time = current_time
        
        # Always perform cleanup, just don't always log it
        self.game_start_completed = False
        self.last_successful_start = None
        
        # Clear game accessibility state
        self._clear_game_accessible()
        
        # Stop any running tasks
        for instance_name in list(self.running_tasks.keys()):
            self.stop_auto_game(instance_name)
    
    def get_status(self, instance_name: str = None) -> Optional[Dict]:
        """Get current status of AutoStartGame for this instance"""
        target_instance = instance_name or self.instance_name
        
        if target_instance not in self.running_tasks:
            # Return success if game was completed recently
            if self.game_start_completed:
                return {
                    'status': 'completed_successfully',
                    'last_completion': self.last_successful_start,
                    'game_running': True
                }
            return None
        
        task_info = self.running_tasks[target_instance]
        elapsed_time = (datetime.now() - task_info['start_time']).total_seconds()
        
        return {
            'status': task_info['status'],
            'current_attempt': task_info['current_attempt'],
            'max_retries': task_info['max_retries'],
            'elapsed_time': elapsed_time,
            'start_time': task_info['start_time']
        }
    
    def get_running_instances(self) -> List[str]:
        """Get list of instances currently running AutoStartGame"""
        return list(self.running_tasks.keys())
    
    def _run_auto_start_task(self, task_info: Dict) -> bool:
        """Main AutoStartGame task implementation"""
        instance_name = task_info['instance_name']
        max_retries = task_info['max_retries']
        
        self.log_message(f"🎮 Auto Start Game started for {instance_name}")
        
        for attempt in range(1, max_retries + 1):
            if task_info['status'] == 'stopping':
                self.log_message(f"🛑 AutoStart stopped for {instance_name}")
                break
                
            task_info['current_attempt'] = attempt
            self.log_message(f"🔄 {instance_name} Auto Start attempt {attempt}/{max_retries}")
            
            if self._attempt_game_start(task_info):
                self.log_message(f"✅ {instance_name} game started successfully after {attempt} attempt(s)")
                return True
            
            if attempt < max_retries:
                self.log_message(f"⏳ {instance_name} waiting {self.retry_delay}s before retry")
                for i in range(self.retry_delay):
                    if task_info['status'] == 'stopping':
                        return False
                    time.sleep(1)
        
        self.log_message(f"❌ {instance_name} failed to start game after {max_retries} attempts")
        return False
    
    def _attempt_game_start(self, task_info: Dict) -> bool:
        """Attempt to start the game with smarter detection"""
        instance_name = task_info['instance_name']
        
        try:
            # Step 1: Take screenshot with retries
            screenshot_path = self._take_screenshot_with_retries(task_info)
            if not screenshot_path:
                self.log_message(f"❌ {instance_name} failed to take initial screenshot")
                return False
            
            try:
                # Step 2: Detect current game state
                game_state = self._detect_game_state(screenshot_path, instance_name)
                self.log_message(f"🔍 {instance_name} detected state: {game_state}")
                
                # Step 3: Handle based on current state
                if game_state == "ALREADY_IN_GAME":
                    self.log_message(f"✅ {instance_name} game is already running")
                    return True
                elif game_state == "LOADING":
                    self.log_message(f"⏳ {instance_name} game is loading, waiting...")
                    return self._wait_for_game_to_load(task_info)
                elif game_state == "MAIN_MENU":
                    return self._start_from_main_menu(task_info, screenshot_path)
                else:
                    return self._handle_unknown_state_smart(task_info, screenshot_path)
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ {instance_name} error in game start attempt: {str(e)}")
            return False
    
    def _take_screenshot_with_retries(self, task_info: Dict) -> Optional[str]:
        """Take screenshot with multiple retries"""
        instance_name = task_info['instance_name']
        instance_index = task_info['instance_index']
        
        for attempt in range(self.max_screenshot_retries):
            if task_info['status'] == 'stopping':
                return None
                
            screenshot_path = self._take_screenshot(instance_index)
            if screenshot_path:
                return screenshot_path
            
            if attempt < self.max_screenshot_retries - 1:
                self.log_message(f"⚠️ {instance_name} screenshot attempt {attempt + 1} failed, retrying...")
                time.sleep(self.screenshot_retry_delay)
        
        self.log_message(f"❌ {instance_name} all screenshot attempts failed")
        return None
    
    def _take_screenshot(self, instance_index: int) -> Optional[str]:
        """Take screenshot using MEmu's ADB wrapper"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"autostart_screenshot_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/autostart_screen.png"
            
            memuc_path = self.instance_manager.MEMUC_PATH
            
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
            
            # Verify screenshot exists and is valid
            if os.path.exists(local_screenshot) and os.path.getsize(local_screenshot) > 10000:
                return local_screenshot
            
            return None
            
        except Exception as e:
            self.log_message(f"❌ Error taking screenshot: {e}")
            return None
    
    def _detect_game_state(self, screenshot_path: str, instance_name: str) -> str:
        """Enhanced game state detection"""
        try:
            # Check for game world first (highest priority)
            if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                return "ALREADY_IN_GAME"
            
            # Check for loading screens
            if self._find_any_template(screenshot_path, self.LOADING_INDICATORS):
                return "LOADING"
            
            # Check for main menu
            if self._find_any_template(screenshot_path, self.MAIN_MENU_INDICATORS):
                return "MAIN_MENU"
            
            return "UNKNOWN_STATE"
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error detecting game state: {str(e)}")
            return "UNKNOWN_STATE"
    
    def _find_any_template(self, screenshot_path: str, template_names: List[str]) -> Optional[str]:
        """Find any of the given templates in the screenshot"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return None
            
            for template_name in template_names:
                template_path = os.path.join(self.templates_dir, template_name)
                
                if not os.path.exists(template_path):
                    continue
                
                # Load template (with caching)
                if template_name not in self.template_cache:
                    template = cv2.imread(template_path)
                    if template is not None:
                        self.template_cache[template_name] = template
                    else:
                        continue
                else:
                    template = self.template_cache[template_name]
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= self.confidence_threshold:
                    return template_name
            
            return None
            
        except Exception as e:
            self.log_message(f"❌ Error in template matching: {e}")
            return None
    
    def _start_from_main_menu(self, task_info: Dict, screenshot_path: str) -> bool:
        """Start game from main menu"""
        instance_name = task_info['instance_name']
        
        try:
            self.log_message(f"🎮 {instance_name} starting game from main menu")
            
            # Try to find and click play button
            for play_button in self.PLAY_BUTTONS:
                if self._click_template(screenshot_path, play_button, task_info):
                    self.log_message(f"✅ {instance_name} clicked {play_button}")
                    
                    # Wait for game to load
                    return self._wait_for_game_to_load(task_info)
            
            # No play buttons found
            self.log_message(f"⚠️ {instance_name} no play buttons found")
            return False
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error starting from main menu: {str(e)}")
            return False
    
    def _handle_unknown_state_smart(self, task_info: Dict, screenshot_path: str) -> bool:
        """SMART: Handle unknown state with VERY careful dialog detection"""
        instance_name = task_info['instance_name']
        
        try:
            self.log_message(f"❓ {instance_name} handling unknown state with enhanced dialog detection")
            
            # CRITICAL: Only try to close dialogs if we actually find close button templates
            dialog_found = False
            close_button_found = None
            
            # Check each close button template to see if it actually exists
            for close_button in self.CLOSE_BUTTONS:
                if self._find_template_only(screenshot_path, close_button):
                    self.log_message(f"🔍 {instance_name} found dialog with {close_button}")
                    close_button_found = close_button
                    dialog_found = True
                    break
            
            if dialog_found and close_button_found:
                # Only click if we actually found a dialog
                if self._click_template(screenshot_path, close_button_found, task_info):
                    self.log_message(f"❌ {instance_name} closed dialog with {close_button_found}")
                    time.sleep(3)  # Wait longer after closing dialog
                    
                    # CRITICAL: Check state again after closing dialog
                    self.log_message(f"🔄 {instance_name} closed dialogs, rechecking state...")
                    new_screenshot = self._take_screenshot_with_retries(task_info)
                    if new_screenshot:
                        try:
                            new_state = self._detect_game_state(new_screenshot, instance_name)
                            if new_state == "ALREADY_IN_GAME":
                                # Verify stability before declaring success
                                if self._verify_game_world_stable(task_info, new_screenshot):
                                    self.log_message(f"✅ {instance_name} reached stable game after closing dialog")
                                    return True
                                else:
                                    self.log_message(f"⚠️ {instance_name} game world unstable after dialog close")
                            elif new_state == "MAIN_MENU":
                                return self._start_from_main_menu(task_info, new_screenshot)
                            else:
                                self.log_message(f"⚠️ {instance_name} still in unknown state after dialog close")
                        finally:
                            self._cleanup_screenshot(new_screenshot)
                else:
                    self.log_message(f"❌ {instance_name} failed to click close button")
            else:
                # NO DIALOGS FOUND - this might be a loading screen or other state
                self.log_message(f"🔍 {instance_name} no dialogs detected, checking if this is loading/transition state")
                
                # Wait a bit and check again - might be loading
                time.sleep(5)
                new_screenshot = self._take_screenshot_with_retries(task_info)
                if new_screenshot:
                    try:
                        new_state = self._detect_game_state(new_screenshot, instance_name)
                        if new_state == "ALREADY_IN_GAME":
                            # Verify stability before declaring success
                            if self._verify_game_world_stable(task_info, new_screenshot):
                                self.log_message(f"✅ {instance_name} game loaded and stable after waiting")
                                return True
                            else:
                                self.log_message(f"⚠️ {instance_name} game world detected but unstable")
                        elif new_state == "MAIN_MENU":
                            self.log_message(f"↩️ {instance_name} back to main menu")
                            return self._start_from_main_menu(task_info, new_screenshot)
                        else:
                            self.log_message(f"⏳ {instance_name} still in transition, continuing to wait...")
                    finally:
                        self._cleanup_screenshot(new_screenshot)
            
            # DON'T assume success - return False to continue waiting
            self.log_message(f"⏳ {instance_name} unknown state handling incomplete, continuing...")
            return False
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error handling unknown state: {str(e)}")
            return False
    
    def _find_template_only(self, screenshot_path: str, template_name: str) -> bool:
        """Find template without clicking - just check if it exists with HIGH CONFIDENCE"""
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
            
            # HIGHER confidence threshold for dialog detection to avoid false positives
            dialog_confidence_threshold = 0.8  # Much higher than normal 0.6
            
            return max_val >= dialog_confidence_threshold
            
        except Exception as e:
            return False
    
    def _wait_for_game_to_load(self, task_info: Dict) -> bool:
        """Wait for game to load with MUCH smarter detection"""
        instance_name = task_info['instance_name']
        
        try:
            self.log_message(f"⏳ {instance_name} waiting for game to load (timeout: {self.game_load_timeout}s)")
            
            start_time = time.time()
            check_count = 0
            consecutive_unknown_states = 0
            
            while (time.time() - start_time) < self.game_load_timeout:
                if task_info['status'] == 'stopping':
                    return False
                
                check_count += 1
                
                # Take screenshot and check state
                screenshot_path = self._take_screenshot_with_retries(task_info)
                if screenshot_path:
                    try:
                        state = self._detect_game_state(screenshot_path, instance_name)
                        
                        if state == "ALREADY_IN_GAME":
                            # CRITICAL: Verify stability before declaring success
                            self.log_message(f"🎯 {instance_name} detected game world, verifying stability...")
                            if self._verify_game_world_stable(task_info, screenshot_path):
                                self.log_message(f"✅ {instance_name} game loaded successfully and stable (check #{check_count})")
                                return True
                            else:
                                self.log_message(f"⚠️ {instance_name} game world unstable, continuing to wait...")
                                consecutive_unknown_states = 0  # Reset counter
                        elif state == "MAIN_MENU":
                            self.log_message(f"⚠️ {instance_name} back at main menu, retrying launcher")
                            if self._click_template(screenshot_path, "game_launcher.png", task_info):
                                self.log_message(f"✅ {instance_name} clicked launcher again")
                                consecutive_unknown_states = 0  # Reset counter
                        elif state == "LOADING":
                            self.log_message(f"⏳ {instance_name} still loading... (check #{check_count})")
                            consecutive_unknown_states = 0  # Reset counter
                        else:
                            # Unknown state - be more careful
                            consecutive_unknown_states += 1
                            self.log_message(f"❓ {instance_name} unknown state (check #{check_count}, consecutive: {consecutive_unknown_states})")
                            
                            # Only try to handle dialogs if we've seen multiple unknown states
                            if consecutive_unknown_states >= 2:
                                # Try to handle unknown state, but DON'T assume success
                                handled = self._handle_unknown_state_smart(task_info, screenshot_path)
                                if handled:
                                    return True
                                consecutive_unknown_states = 0  # Reset after handling
                            else:
                                # Just wait - might be loading/transitioning
                                self.log_message(f"⏳ {instance_name} waiting for state to stabilize...")
                            
                    finally:
                        self._cleanup_screenshot(screenshot_path)
                
                time.sleep(self.dialog_check_interval)
            
            self.log_message(f"❌ {instance_name} game failed to load within {self.game_load_timeout}s timeout")
            return False
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error waiting for game: {str(e)}")
            return False
    
    def _click_template(self, screenshot_path: str, template_name: str, task_info: Dict) -> bool:
        """Click on a template if found"""
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
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                # Calculate click position (center of template)
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                # Click the position
                return self._click_position(task_info['instance_index'], click_x, click_y)
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error clicking template {template_name}: {e}")
            return False
    
    def _click_position(self, instance_index: int, x: int, y: int) -> bool:
        """Click at specific coordinates using MEmu ADB"""
        try:
            memuc_path = self.instance_manager.MEMUC_PATH
            
            # Use ADB to tap at position
            tap_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            success = result.returncode == 0
            
            if success:
                self.log_message(f"👆 Clicked position ({x}, {y})")
            else:
                self.log_message(f"❌ Click failed at ({x}, {y}): {result.stderr}")
                
            return success
            
        except Exception as e:
            self.log_message(f"❌ Error clicking position ({x}, {y}): {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """Safely cleanup screenshot file"""
        if screenshot_path:
            try:
                os.remove(screenshot_path)
            except:
                pass
    
    def _verify_stable_game_state(self) -> bool:
        """Quick verification that game state is stable (for initial checks)"""
        try:
            # Create a minimal task info for the verification
            temp_task_info = {
                'instance_name': self.instance_name,
                'instance_index': self._get_instance_index(),
                'status': 'checking'
            }
            
            return self._verify_game_world_stable(temp_task_info)
            
        except Exception as e:
            self.log_message(f"❌ Error verifying stable game state: {e}")
            return False
    
    def _verify_game_world_stable(self, task_info: Dict, initial_screenshot_path: str = None) -> bool:
        """Verify game world is stable for 2+ seconds, not just a loading flash"""
        instance_name = task_info['instance_name']
        
        try:
            self.log_message(f"🔍 {instance_name} verifying game world stability...")
            
            # Check initial state if screenshot provided
            if initial_screenshot_path:
                if not self._find_any_template(initial_screenshot_path, self.GAME_WORLD_INDICATORS):
                    return False
            
            # Verify stability over multiple checks
            stability_checks = 3  # Check 3 times
            stable_detections = 0
            
            for check_num in range(stability_checks):
                time.sleep(1)  # Wait 1 second between checks
                
                if task_info['status'] == 'stopping':
                    return False
                
                screenshot_path = self._take_screenshot_with_retries(task_info)
                if screenshot_path:
                    try:
                        # Check if game world indicators are still present
                        found_template = self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS)
                        if found_template:
                            stable_detections += 1
                            self.log_message(f"✅ {instance_name} stability check {check_num + 1}/{stability_checks}: {found_template} found")
                        else:
                            self.log_message(f"❌ {instance_name} stability check {check_num + 1}/{stability_checks}: no game world detected")
                            
                    finally:
                        self._cleanup_screenshot(screenshot_path)
                else:
                    self.log_message(f"❌ {instance_name} stability check {check_num + 1}/{stability_checks}: screenshot failed")
            
            # Require at least 2 out of 3 stable detections
            is_stable = stable_detections >= 2
            
            if is_stable:
                self.log_message(f"✅ {instance_name} game world confirmed stable ({stable_detections}/{stability_checks} checks)")
            else:
                self.log_message(f"❌ {instance_name} game world unstable ({stable_detections}/{stability_checks} checks) - likely loading flash")
            
            return is_stable
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error verifying stability: {str(e)}")
            return False
    
    def execute_cycle(self) -> bool:
        """SMART: Execute cycle - only run if needed with spam reduction"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance:
                return False
            
            # CRITICAL: Don't run if we've already completed successfully
            if self.game_start_completed and self.last_successful_start:
                time_since_success = (datetime.now() - self.last_successful_start).total_seconds()
                if time_since_success < 300:  # Don't restart within 5 minutes
                    return True  # Return success, no need to run
            
            # Only run if instance is running and we haven't started the game yet
            if instance["status"] == "Running" and self.instance_name not in self.running_tasks:
                # Quick check if game is already running AND stable
                if self._is_game_already_running() and self._verify_stable_game_state():
                    if not self.game_start_completed:
                        self.game_start_completed = True
                        self.last_successful_start = datetime.now()
                        self._mark_game_accessible()  # NEW: Mark accessible
                        self.log_message(f"✅ {self.instance_name} game already running and stable")
                    
                    return True
                
                # REDUCED LOGGING: Only log when actually starting
                current_time = time.time()
                if current_time - self._last_status_log > 60:  # Only log every minute
                    self.log_message(f"🎯 Auto-triggering game start for running instance: {self.instance_name}")
                    self._last_status_log = current_time
                
                return self.start_auto_game()
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error in execute cycle: {e}")
            return False
    
    def reset_completion_status(self):
        """Reset completion status - call this when instance is restarted"""
        self.game_start_completed = False
        self.last_successful_start = None
        self._clear_game_accessible()
        self.log_message(f"🔄 Reset completion status for {self.instance_name}")
    
    def get_module_info(self) -> Dict:
        """Get module information"""
        return {
            "name": "AutoStartGame",
            "version": "2.3.0",
            "description": "Complete game auto-starter with shared state management and spam reduction",
            "author": "BENSON v2.0",
            "instance_name": self.instance_name,
            "dependencies": self.get_missing_dependencies(),
            "available": self.is_available(),
            "running_tasks": len(self.running_tasks),
            "game_completed": self.game_start_completed,
            "last_success": self.last_successful_start.isoformat() if self.last_successful_start else None,
            "templates_dir": self.templates_dir,
            "smart_features": [
                "Prevents duplicate runs",
                "Smart game state detection",
                "Careful dialog handling", 
                "Quick game running checks",
                "Strategic clicking only",
                "Reduced console spam",
                "Proper module communication",
                "Shared state management"
            ]
        }
    
    def is_game_accessible(self) -> bool:
        """Check if game is accessible for other modules"""
        return self.game_start_completed and self.last_successful_start is not None
    
    def get_shared_state_info(self) -> Dict:
        """Get shared state information for debugging"""
        try:
            shared_info = {}
            if hasattr(self.instance_manager, 'shared_state'):
                for key, value in self.instance_manager.shared_state.items():
                    if self.instance_name in key:
                        shared_info[key] = value
            return shared_info
        except Exception as e:
            return {"error": str(e)}
    
    def force_mark_accessible(self):
        """Force mark game as accessible (for manual override)"""
        self.game_start_completed = True
        self.last_successful_start = datetime.now()
        self._mark_game_accessible()
        self.log_message(f"🔧 Force marked {self.instance_name} as accessible")
    
    def force_clear_accessible(self):
        """Force clear game accessibility (for manual override)"""
        self.game_start_completed = False
        self.last_successful_start = None
        self._clear_game_accessible()
        self.log_message(f"🔧 Force cleared {self.instance_name} accessibility")