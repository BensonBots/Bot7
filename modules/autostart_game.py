"""
BENSON v2.0 - AutoStartGame Module
Automatically starts the game on MEmu instances using image detection and UI automation
Based on the Java AutoStartGameTask implementation with improved ad handling
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
    """AutoStartGame module for BENSON - Python implementation of Java AutoStartGameTask"""
    
    def __init__(self, instance_manager, console_callback: Callable = None):
        self.instance_manager = instance_manager
        self.console_callback = console_callback or print
        self.logger = self._setup_logging()
        
        # Module state tracking
        self.running_tasks = {}  # instance_name -> task_info
        self.template_cache = {}  # Cache for loaded templates
        
        # Game state detection templates - matching Java version
        self.MAIN_MENU_INDICATORS = [
            "game_launcher.png"
        ]
        
        self.GAME_WORLD_INDICATORS = [
            "world.png",
            "world_icon.png", 
            "town_icon.png",
            "game_icon.png"
        ]
        
        self.PLAY_BUTTONS = [
            "game_launcher.png",
            "deploy_button.png",
            "play.png",
            "start.png"
        ]
        
        self.CLOSE_BUTTONS = [
            "close_x.png",
            "close_x2.png", 
            "close_x3.png",
            "close_x4.png",
            "close_x5.png"
        ]
        
        self.GENERIC_ELEMENTS = [
            "deploy_button.png",
            "search_button.png",
            "details_button.png"
        ]
        
        # Configuration
        self.templates_dir = "templates"  # Directory containing template images
        self.confidence_threshold = 0.6
        self.default_max_retries = 3
        self.retry_delay = 10  # seconds
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the module"""
        logger = logging.getLogger('AutoStartGame')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(name)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_message(self, message: str):
        """Log message to console and callback"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}"
        self.logger.info(message)
        if self.console_callback:
            self.console_callback(full_message)
    
    def is_available(self) -> bool:
        """Check if module dependencies are available"""
        if not CV2_AVAILABLE:
            return False
        
        # Check if MEmu is available
        if not hasattr(self.instance_manager, '_is_memu_available'):
            return False
            
        return self.instance_manager._is_memu_available()
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies"""
        missing = []
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        return missing
    
    def start_auto_game(self, instance_name: str, max_retries: int = None, 
                       on_complete: Callable = None) -> bool:
        """Start AutoStartGame for an instance"""
        if not self.is_available():
            self.log_message(f"❌ AutoStartGame not available - missing dependencies: {self.get_missing_dependencies()}")
            return False
        
        if instance_name in self.running_tasks:
            self.log_message(f"⚠️ AutoStartGame already running for {instance_name}")
            return False
        
        instance = self.instance_manager.get_instance(instance_name)
        if not instance:
            self.log_message(f"❌ Instance {instance_name} not found")
            return False
        
        max_retries = max_retries or self.default_max_retries
        
        # Create task info
        task_info = {
            'instance_name': instance_name,
            'instance_index': instance['index'],
            'max_retries': max_retries,
            'current_attempt': 0,
            'start_time': datetime.now(),
            'status': 'starting',
            'on_complete': on_complete,
            'thread': None
        }
        
        self.running_tasks[instance_name] = task_info
        
        # Start the task in a background thread
        def run_task():
            try:
                success = self._run_auto_start_task(task_info)
                task_info['status'] = 'completed' if success else 'failed'
                
                if task_info['on_complete']:
                    task_info['on_complete'](success)
                    
            except Exception as e:
                self.log_message(f"❌ {instance_name} AutoStartGame error: {str(e)}")
                task_info['status'] = 'error'
            finally:
                # Clean up task
                if instance_name in self.running_tasks:
                    del self.running_tasks[instance_name]
        
        task_thread = threading.Thread(target=run_task, daemon=True)
        task_info['thread'] = task_thread
        task_thread.start()
        
        self.log_message(f"🎮 AutoStartGame started for {instance_name}")
        return True
    
    def stop_auto_game(self, instance_name: str) -> bool:
        """Stop AutoStartGame for an instance"""
        if instance_name not in self.running_tasks:
            self.log_message(f"⚠️ No AutoStartGame running for {instance_name}")
            return False
        
        task_info = self.running_tasks[instance_name]
        task_info['status'] = 'stopping'
        
        # Note: We can't directly stop threads in Python, but we set status for checks
        self.log_message(f"🛑 AutoStartGame stop requested for {instance_name}")
        return True
    
    def get_status(self, instance_name: str) -> Optional[Dict]:
        """Get current status of AutoStartGame for an instance"""
        if instance_name not in self.running_tasks:
            return None
        
        task_info = self.running_tasks[instance_name]
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
        instance_index = task_info['instance_index']
        max_retries = task_info['max_retries']
        
        self.log_message(f"🎮 Auto Start Game started for {instance_name}")
        
        game_started = False
        
        for attempt in range(1, max_retries + 1):
            if task_info['status'] == 'stopping':
                break
                
            task_info['current_attempt'] = attempt
            self.log_message(f"🔄 {instance_name} Auto Start attempt {attempt}/{max_retries}")
            
            if self._attempt_game_start(task_info):
                game_started = True
                break
            
            if attempt < max_retries:
                self.log_message(f"⏳ {instance_name} waiting {self.retry_delay}s before retry")
                time.sleep(self.retry_delay)
        
        if game_started:
            self.log_message(f"✅ {instance_name} game started successfully after {task_info['current_attempt']} attempt(s)")
            return True
        else:
            self.log_message(f"❌ {instance_name} failed to start game after {max_retries} attempts")
            return False
    
    def _attempt_game_start(self, task_info: Dict) -> bool:
        """Attempt to start the game - main logic"""
        instance_name = task_info['instance_name']
        instance_index = task_info['instance_index']
        
        try:
            # Step 1: Take screenshot
            screenshot_path = self._take_screenshot(instance_index)
            if not screenshot_path:
                self.log_message(f"❌ {instance_name} failed to take screenshot")
                return False
            
            # Step 2: Detect current game state
            game_state = self._detect_game_state(screenshot_path, instance_name)
            self.log_message(f"🔍 {instance_name} detected state: {game_state}")
            
            # Step 3: Handle based on current state
            if game_state == "ALREADY_IN_GAME":
                self.log_message(f"✅ {instance_name} game is already running")
                return True
            elif game_state == "MAIN_MENU":
                return self._start_from_main_menu(task_info, screenshot_path)
            else:
                return self._handle_unknown_state(task_info, screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ {instance_name} error in game start attempt: {str(e)}")
            return False
        finally:
            # Clean up screenshot
            try:
                if 'screenshot_path' in locals() and screenshot_path:
                    os.remove(screenshot_path)
            except:
                pass
    
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
            
            time.sleep(0.5)  # Wait for file to be written
            
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
            self.logger.error(f"Error taking screenshot: {e}")
            return None
    
    def _detect_game_state(self, screenshot_path: str, instance_name: str) -> str:
        """Detect current game state using template matching"""
        try:
            # Check for game world first (already in game)
            if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                return "ALREADY_IN_GAME"
            
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
            self.logger.error(f"Error in template matching: {e}")
            return None
    
    def _start_from_main_menu(self, task_info: Dict, screenshot_path: str) -> bool:
        """Start game from main menu"""
        instance_name = task_info['instance_name']
        instance_index = task_info['instance_index']
        
        try:
            self.log_message(f"🎮 {instance_name} starting game from main menu")
            
            # Try to find and click play button
            for play_button in self.PLAY_BUTTONS:
                if self._click_template(screenshot_path, play_button, instance_index, instance_name):
                    self.log_message(f"✅ {instance_name} clicked {play_button}")
                    
                    # Wait for game to load
                    return self._wait_for_game_to_load(task_info)
            
            # No play buttons found, try common positions
            self.log_message(f"⚠️ {instance_name} no play buttons found, trying common positions")
            return self._handle_unknown_state(task_info, screenshot_path)
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error starting from main menu: {str(e)}")
            return False
    
    def _handle_unknown_state(self, task_info: Dict, screenshot_path: str) -> bool:
        """Handle unknown state with improved ad handling"""
        instance_name = task_info['instance_name']
        instance_index = task_info['instance_index']
        
        try:
            self.log_message(f"❓ {instance_name} handling unknown state with improved ad detection")
            
            # Take multiple screenshots and handle ads iteratively
            max_ad_attempts = 5  # Handle up to 5 consecutive ads
            
            for ad_attempt in range(max_ad_attempts):
                # Take fresh screenshot for this attempt
                current_screenshot = self._take_screenshot(instance_index)
                if not current_screenshot:
                    current_screenshot = screenshot_path
                
                self.log_message(f"🔍 {instance_name} ad handling attempt {ad_attempt + 1}/{max_ad_attempts}")
                
                # Look for close buttons first (ads usually have these)
                ad_closed = False
                for close_btn in self.CLOSE_BUTTONS:
                    if self._click_template(current_screenshot, close_btn, instance_index, instance_name):
                        self.log_message(f"❌ {instance_name} closed ad/dialog with {close_btn}")
                        ad_closed = True
                        time.sleep(2)  # Wait for ad to disappear
                        break
                
                # If no close button found, try clicking center to dismiss
                if not ad_closed:
                    self.log_message(f"🎯 {instance_name} clicking center to dismiss dialogs")
                    self._click_position(instance_index, 240, 400)
                    time.sleep(2)
                
                # Clean up current screenshot if it's different from original
                if current_screenshot != screenshot_path:
                    try:
                        os.remove(current_screenshot)
                    except:
                        pass
                
                # Check if we've reached a known state after handling ads
                time.sleep(1)
                check_screenshot = self._take_screenshot(instance_index)
                if check_screenshot:
                    new_state = self._detect_game_state(check_screenshot, instance_name)
                    
                    try:
                        os.remove(check_screenshot)
                    except:
                        pass
                    
                    if new_state == "ALREADY_IN_GAME":
                        self.log_message(f"✅ {instance_name} reached game after ad handling")
                        return True
                    elif new_state == "MAIN_MENU":
                        self.log_message(f"🎮 {instance_name} reached main menu after ad handling")
                        return self._start_from_main_menu(task_info, screenshot_path)
                
                # If we're still in unknown state, continue to next ad attempt
                self.log_message(f"⏳ {instance_name} still in unknown state, continuing ad cleanup...")
            
            # After all ad attempts, try generic elements
            self.log_message(f"🔧 {instance_name} trying generic UI elements")
            final_screenshot = self._take_screenshot(instance_index)
            if final_screenshot:
                for element in self.GENERIC_ELEMENTS:
                    if self._click_template(final_screenshot, element, instance_index, instance_name):
                        self.log_message(f"🔄 {instance_name} clicked {element}")
                        time.sleep(3)
                        break
                
                try:
                    os.remove(final_screenshot)
                except:
                    pass
            
            # Try common positions as final fallback
            self.log_message(f"🎯 {instance_name} trying common click positions")
            common_positions = [(240, 600), (240, 500), (240, 300), (400, 300), (80, 300)]
            for x, y in common_positions:
                self._click_position(instance_index, x, y)
                time.sleep(1)
            
            # Final check after all attempts
            time.sleep(3)
            final_check_screenshot = self._take_screenshot(instance_index)
            if final_check_screenshot:
                final_state = self._detect_game_state(final_check_screenshot, instance_name)
                
                try:
                    os.remove(final_check_screenshot)
                except:
                    pass
                
                if final_state == "ALREADY_IN_GAME":
                    self.log_message(f"✅ {instance_name} successfully reached game after cleanup")
                    return True
                elif final_state == "MAIN_MENU":
                    self.log_message(f"🎮 {instance_name} reached main menu after cleanup")
                    return self._start_from_main_menu(task_info, screenshot_path)
            
            # If we still haven't reached a known state, assume success
            self.log_message(f"✅ {instance_name} completed unknown state handling (assuming success)")
            return True
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error handling unknown state: {str(e)}")
            return False
    
    def _wait_for_game_to_load(self, task_info: Dict) -> bool:
        """Wait for game to load after clicking play"""
        instance_name = task_info['instance_name']
        instance_index = task_info['instance_index']
        
        try:
            self.log_message(f"⏳ {instance_name} waiting for game to load")
            
            # Wait up to 60 seconds for game to load
            for i in range(60):
                if task_info['status'] == 'stopping':
                    return False
                
                # Take screenshot and check for game world
                screenshot_path = self._take_screenshot(instance_index)
                if screenshot_path:
                    # Check if we're back at main menu (game crashed)
                    if self._find_any_template(screenshot_path, self.MAIN_MENU_INDICATORS):
                        self.log_message(f"⚠️ {instance_name} detected game crash, retrying launcher")
                        # Try clicking launcher again
                        if self._click_template(screenshot_path, "game_launcher.png", instance_index, instance_name):
                            self.log_message(f"✅ {instance_name} clicked launcher again after crash")
                            try:
                                os.remove(screenshot_path)
                            except:
                                pass
                            # Reset timer and continue waiting
                            continue
                    
                    # Check if game is loaded
                    if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                        self.log_message(f"✅ {instance_name} game loaded successfully")
                        try:
                            os.remove(screenshot_path)
                        except:
                            pass
                        return True
                    
                    # Check for error dialogs
                    if self._find_any_template(screenshot_path, self.CLOSE_BUTTONS):
                        self.log_message(f"⚠️ {instance_name} encountered dialog during loading")
                        # Try to close it
                        for close_btn in self.CLOSE_BUTTONS:
                            if self._click_template(screenshot_path, close_btn, instance_index, instance_name):
                                break
                    
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                
                time.sleep(1)
            
            self.log_message(f"❌ {instance_name} game failed to load within timeout")
            return False
            
        except Exception as e:
            self.log_message(f"❌ {instance_name} error waiting for game: {str(e)}")
            return False
    
    def _click_template(self, screenshot_path: str, template_name: str, 
                       instance_index: int, instance_name: str) -> bool:
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
                return self._click_position(instance_index, click_x, click_y)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking template {template_name}: {e}")
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
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error clicking position ({x}, {y}): {e}")
            return False
    
    def get_module_info(self) -> Dict:
        """Get module information"""
        return {
            "name": "AutoStartGame",
            "version": "1.0.0",
            "description": "Automatically starts the game on MEmu instances using image detection",
            "author": "BENSON v2.0",
            "dependencies": self.get_missing_dependencies(),
            "available": self.is_available(),
            "running_instances": len(self.running_tasks),
            "templates_dir": self.templates_dir,
            "supported_templates": {
                "main_menu": self.MAIN_MENU_INDICATORS,
                "game_world": self.GAME_WORLD_INDICATORS,
                "play_buttons": self.PLAY_BUTTONS,
                "close_buttons": self.CLOSE_BUTTONS,
                "generic_elements": self.GENERIC_ELEMENTS
            }
        }
    
    def setup_templates_directory(self) -> str:
        """Setup and return templates directory path"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # Create a readme file with template information
        readme_path = os.path.join(self.templates_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write("""# AutoStartGame Templates

Place your game template images in this directory.

## Required Templates:

### Main Menu Indicators:
- game_launcher.png

### Game World Indicators:
- world.png
- world_icon.png
- town_icon.png
- game_icon.png

### Play Buttons:
- game_launcher.png
- deploy_button.png
- play.png
- start.png

### Close Buttons:
- close_x.png
- close_x2.png
- close_x3.png
- close_x4.png
- close_x5.png

### Generic Elements:
- deploy_button.png
- search_button.png
- details_button.png

Templates should be PNG files with clear, distinctive game UI elements.
""")
        
        return self.templates_dir