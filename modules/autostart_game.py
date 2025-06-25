"""
BENSON v2.0 - Template-Only AutoStart Module
Only uses image detection - no fallback position clicking
"""

import os
import time
import threading
import subprocess
from typing import Optional, Callable
from datetime import datetime

# Safe imports
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class AutoStartGameModule:
    """Template-only AutoStart - requires proper image templates"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback: Callable = None):
        self.instance_name = instance_name
        self.instance_manager = shared_resources
        self.console_callback = console_callback or print
        
        # Setup shared state
        self.shared_state = getattr(shared_resources, 'shared_state', {})
        if not hasattr(shared_resources, 'shared_state'):
            shared_resources.shared_state = {}
            self.shared_state = shared_resources.shared_state
        
        # State tracking
        self.game_start_completed = False
        self.last_successful_start = None
        
        # Configuration
        self.templates_dir = "templates"
        self.confidence_threshold = 0.6
        self.default_max_retries = 3
        self.retry_delay = 10
        self.game_load_timeout = 90
        
        # Setup and validate templates
        self._setup_and_validate_templates()
        
        # Log initialization once per instance
        if not hasattr(self.__class__, f'_init_logged_{instance_name}'):
            self.log_message(f"✅ AutoStartGame initialized for {instance_name}")
            setattr(self.__class__, f'_init_logged_{instance_name}', True)
    
    def _setup_and_validate_templates(self):
        """Setup templates directory and validate requirements"""
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Game detection templates
        self.MAIN_MENU_INDICATORS = ["game_launcher.png", "main_menu.png", "start_game.png", "play_button.png"]
        self.GAME_WORLD_INDICATORS = ["world.png", "world_icon.png", "town_icon.png", "game_icon.png",
                                     "home_button.png", "castle.png", "build_button.png", "march_button.png",
                                     "base_icon.png", "city_icon.png", "village_icon.png"]
        self.CLOSE_BUTTONS = ["close_x.png", "close_x2.png", "close_btn.png", "cancel_btn.png", "ok_btn.png",
                              "close_2.png", "close_3.png", "close_4.png", "close_5.png", "x_button.png"]
        
        # Check OpenCV availability
        if not CV2_AVAILABLE:
            self.log_message("❌ OpenCV not available - AutoStart requires cv2 for image detection")
            self.is_available = False
            return
        
        # Check for templates
        available_templates = self._get_available_templates()
        
        if not available_templates:
            self.log_message("❌ No template files found in templates/ directory")
            self.log_message("📋 AutoStart requires image templates to work properly")
            self.is_available = False
            return
        
        # Check for essential templates
        has_menu_template = any(template in available_templates for template in self.MAIN_MENU_INDICATORS)
        has_world_template = any(template in available_templates for template in self.GAME_WORLD_INDICATORS)
        
        if not has_menu_template:
            self.log_message("⚠️ No main menu templates found - may have difficulty starting games")
        
        if not has_world_template:
            self.log_message("⚠️ No game world templates found - may have difficulty detecting game state")
        
        self.is_available = True
        self.log_message(f"✅ Found {len(available_templates)} template files")
        
        # Log available templates for debugging
        if available_templates:
            menu_templates = [t for t in available_templates if t in self.MAIN_MENU_INDICATORS]
            world_templates = [t for t in available_templates if t in self.GAME_WORLD_INDICATORS]
            close_templates = [t for t in available_templates if t in self.CLOSE_BUTTONS]
            
            if menu_templates:
                self.log_message(f"📋 Menu templates: {', '.join(menu_templates)}")
            if world_templates:
                self.log_message(f"🌍 World templates: {', '.join(world_templates)}")
            if close_templates:
                self.log_message(f"❌ Close templates: {', '.join(close_templates)}")
    
    def _get_available_templates(self) -> list:
        """Get list of available template files"""
        try:
            if not os.path.exists(self.templates_dir):
                return []
            return [f for f in os.listdir(self.templates_dir) if f.endswith('.png')]
        except:
            return []
    
    def log_message(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} [AutoStartGame-{self.instance_name}] {message}"
        if self.console_callback:
            self.console_callback(full_message)
    
    def start_auto_game(self, instance_name: str = None, max_retries: int = None, 
                       on_complete: Callable = None) -> bool:
        """Start auto game with template-only detection"""
        target_instance = instance_name or self.instance_name
        
        # Check if AutoStart is available
        if not self.is_available:
            self.log_message("❌ AutoStart not available - missing templates or OpenCV")
            if on_complete: on_complete(False)
            return False
        
        # Check if recently completed
        if self.game_start_completed and self.last_successful_start:
            time_since = (datetime.now() - self.last_successful_start).total_seconds()
            if time_since < 300:  # 5 minutes
                self.log_message(f"⏸ Game already started {int(time_since)}s ago")
                if on_complete: on_complete(True)
                return True
        
        # Check if already running
        if self._is_game_already_running():
            self.log_message(f"✅ Game already running for {target_instance}")
            if self._verify_stable_game_state():
                self._mark_success_and_notify(on_complete)
                return True
        
        # Start game launch process
        def run_task():
            try:
                self.log_message(f"🚀 Starting AutoStartGame for {target_instance}")
                success = self._run_complete_game_start(target_instance, max_retries or self.default_max_retries)
                
                if success:
                    self._mark_success_and_notify(on_complete)
                else:
                    self.log_message(f"❌ AutoStartGame failed for {target_instance}")
                    if on_complete: on_complete(False)
                        
                self.log_message(f"🏁 AutoStartGame completed: {'SUCCESS' if success else 'FAILED'}")
                    
            except Exception as e:
                self.log_message(f"❌ AutoStartGame error: {str(e)}")
                if on_complete: on_complete(False)
        
        threading.Thread(target=run_task, daemon=True, name=f"AutoStart-{target_instance}").start()
        return True
    
    def _mark_success_and_notify(self, on_complete: Callable = None):
        """Mark success and notify other modules"""
        self.game_start_completed = True
        self.last_successful_start = datetime.now()
        self._set_game_accessible_state(True)
        
        if on_complete: on_complete(True)
        self.log_message(f"✅ Game accessible - other modules can start")
    
    def _set_game_accessible_state(self, accessible: bool):
        """Set shared state for module communication"""
        try:
            # Set multiple state indicators
            state_keys = [
                f"game_accessible_{self.instance_name}",
                f"game_world_active_{self.instance_name}",
                f"autostart_completed_{self.instance_name}",
                "game_accessible", "game_world_active"
            ]
            
            for key in state_keys:
                self.shared_state[key] = accessible
            
            self.shared_state[f"last_game_check_{self.instance_name}"] = datetime.now().isoformat()
            
            # Also set on instance manager if available
            if hasattr(self.instance_manager, 'set_game_state'):
                self.instance_manager.set_game_state(self.instance_name, {
                    'game_accessible': accessible,
                    'autostart_completed': accessible
                })
            
            self.log_message(f"📡 Set game accessible state: {accessible}")
            
        except Exception as e:
            self.log_message(f"⚠️ Could not set shared state: {e}")
    
    def _run_complete_game_start(self, instance_name: str, max_retries: int) -> bool:
        """Complete game start process using only templates"""
        for attempt in range(1, max_retries + 1):
            self.log_message(f"🔄 Auto start attempt {attempt}/{max_retries}")
            
            try:
                if self._attempt_game_start_template_only(instance_name):
                    return True
            except Exception as e:
                self.log_message(f"❌ Attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                self.log_message(f"⏳ Waiting {self.retry_delay}s before retry")
                time.sleep(self.retry_delay)
        
        self.log_message("❌ All attempts failed - check your templates and game state")
        return False
    
    def _attempt_game_start_template_only(self, instance_name: str) -> bool:
        """Template-only game start attempt"""
        try:
            instance = self.instance_manager.get_instance(instance_name)
            if not instance:
                self.log_message(f"❌ Instance {instance_name} not found")
                return False
            
            screenshot_path = self._take_screenshot(instance['index'])
            if not screenshot_path:
                self.log_message("❌ Failed to take screenshot")
                return False
            
            try:
                # Detect current state using templates
                game_state = self._detect_game_state(screenshot_path)
                self.log_message(f"🔍 Detected state: {game_state}")
                
                if game_state == "ALREADY_IN_GAME":
                    return self._verify_game_world_stable(instance['index'])
                elif game_state == "MAIN_MENU":
                    return self._start_from_main_menu_template_only(screenshot_path, instance['index'])
                elif game_state == "UNKNOWN_STATE":
                    return self._handle_unknown_state_template_only(screenshot_path, instance['index'])
                else:
                    self.log_message(f"❌ Unhandled game state: {game_state}")
                    return False
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error in template-only game start: {e}")
            return False
    
    def _detect_game_state(self, screenshot_path: str) -> str:
        """Detect current game state using only templates"""
        try:
            if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                return "ALREADY_IN_GAME"
            if self._find_any_template(screenshot_path, self.MAIN_MENU_INDICATORS):
                return "MAIN_MENU"
            return "UNKNOWN_STATE"
        except Exception as e:
            self.log_message(f"❌ Error detecting game state: {e}")
            return "UNKNOWN_STATE"
    
    def _start_from_main_menu_template_only(self, screenshot_path: str, instance_index: int) -> bool:
        """Start game from main menu using only templates"""
        try:
            self.log_message(f"🎮 Starting game from main menu using templates")
            
            # Try to find and click game launcher template
            for template in self.MAIN_MENU_INDICATORS:
                if self._click_template(screenshot_path, template, instance_index):
                    self.log_message(f"✅ Clicked game launcher using template: {template}")
                    return self._wait_for_game_load_template_only(instance_index)
            
            self.log_message("❌ No main menu templates matched current screen")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error starting from main menu: {e}")
            return False
    
    def _wait_for_game_load_template_only(self, instance_index: int) -> bool:
        """Wait for game to load using only template detection"""
        self.log_message(f"⏳ Waiting for game to load using templates (timeout: {self.game_load_timeout}s)")
        
        start_time = time.time()
        check_count = 0
        last_state = None
        
        while (time.time() - start_time) < self.game_load_timeout:
            check_count += 1
            
            # Always take a FRESH screenshot for each check
            screenshot_path = self._take_screenshot(instance_index)
            if not screenshot_path:
                self.log_message("⚠️ Failed to take screenshot, retrying...")
                time.sleep(3)
                continue
            
            try:
                state = self._detect_game_state(screenshot_path)
                
                # Only log state changes to reduce spam
                if state != last_state:
                    self.log_message(f"🔍 Game state: {state}")
                    last_state = state
                
                if state == "ALREADY_IN_GAME":
                    if self._verify_game_world_stable(instance_index):
                        self.log_message(f"✅ Game loaded successfully (detected via templates)")
                        return True
                elif state == "UNKNOWN_STATE":
                    # Try to close dialogs with the current fresh screenshot
                    dialogs_found = self._check_and_close_dialogs_fresh(screenshot_path, instance_index)
                    if dialogs_found:
                        self.log_message("⏳ Closed dialogs, continuing to wait for game load...")
                
            finally:
                self._cleanup_screenshot(screenshot_path)
            
            time.sleep(3)
        
        self.log_message("❌ Game load timeout - could not detect game world with available templates")
        return False
    
    def _check_and_close_dialogs_fresh(self, screenshot_path: str, instance_index: int) -> bool:
        """Check for and close dialogs using current fresh screenshot"""
        dialogs_found = False
        
        # Check each close button template against current screenshot
        for close_button in self.CLOSE_BUTTONS:
            if self._find_template_only(screenshot_path, close_button):
                self.log_message(f"🔍 Found dialog close button: {close_button}")
                
                if self._click_template(screenshot_path, close_button, instance_index):
                    self.log_message(f"❌ Closed dialog using template: {close_button}")
                    dialogs_found = True
                    time.sleep(1.5)  # Wait for dialog animation to complete
                    break  # Only close one dialog at a time, let next iteration handle more
                else:
                    self.log_message(f"⚠️ Failed to click close button: {close_button}")
        
        if not dialogs_found:
            self.log_message("ℹ️ No dialog close buttons detected in current screenshot")
        
        return dialogs_found
    
    def _handle_unknown_state_template_only(self, screenshot_path: str, instance_index: int) -> bool:
        """Handle unknown state using only templates"""
        self.log_message(f"❓ Unknown state - attempting to close dialogs with templates")
        
        # Try to close dialogs with current screenshot
        if self._check_and_close_dialogs_fresh(screenshot_path, instance_index):
            # Wait for dialogs to close, then take a completely fresh screenshot
            time.sleep(3)
            
            new_screenshot = self._take_screenshot(instance_index)
            if new_screenshot:
                try:
                    new_state = self._detect_game_state(new_screenshot)
                    self.log_message(f"🔍 State after closing dialogs: {new_state}")
                    
                    if new_state == "ALREADY_IN_GAME":
                        return self._verify_game_world_stable(instance_index)
                    elif new_state == "MAIN_MENU":
                        return self._start_from_main_menu_template_only(new_screenshot, instance_index)
                    else:
                        self.log_message(f"⚠️ Still in unknown state after closing dialogs: {new_state}")
                        
                finally:
                    self._cleanup_screenshot(new_screenshot)
        
        self.log_message("❌ Could not resolve unknown state with available templates")
        return False
    
    def _try_close_dialogs_template_only(self, screenshot_path: str, instance_index: int) -> bool:
        """Try to close visible dialogs using only templates"""
        dialogs_closed = False
        
        for close_button in self.CLOSE_BUTTONS:
            if self._find_template_only(screenshot_path, close_button):
                if self._click_template(screenshot_path, close_button, instance_index):
                    self.log_message(f"❌ Closed dialog using template: {close_button}")
                    dialogs_closed = True
                    
                    # Wait for dialog to close and take NEW screenshot
                    time.sleep(2)
                    new_screenshot = self._take_screenshot(instance_index)
                    
                    if new_screenshot:
                        try:
                            # Update screenshot_path to the new one for next iteration
                            self._cleanup_screenshot(screenshot_path)
                            screenshot_path = new_screenshot
                            self.log_message("📸 Took fresh screenshot after closing dialog")
                        except Exception as e:
                            self.log_message(f"⚠️ Error updating screenshot: {e}")
                            self._cleanup_screenshot(new_screenshot)
                    else:
                        self.log_message("⚠️ Could not take fresh screenshot after dialog close")
                        break  # Stop trying if we can't get new screenshots
        
        if not dialogs_closed:
            self.log_message("ℹ️ No dialog close buttons detected")
        
        return dialogs_closed
    
    def _verify_game_world_stable(self, instance_index: int) -> bool:
        """Verify game world is stable using templates"""
        self.log_message(f"🔍 Verifying game world stability using templates...")
        
        stable_checks = 0
        for check in range(3):
            time.sleep(1)
            
            screenshot_path = self._take_screenshot(instance_index)
            if screenshot_path:
                try:
                    if self._find_any_template(screenshot_path, self.GAME_WORLD_INDICATORS):
                        stable_checks += 1
                        self.log_message(f"✅ Stability check {check + 1}/3: game world detected")
                    else:
                        self.log_message(f"❌ Stability check {check + 1}/3: no game world detected")
                finally:
                    self._cleanup_screenshot(screenshot_path)
        
        is_stable = stable_checks >= 2
        if is_stable:
            self.log_message(f"✅ Game world confirmed stable ({stable_checks}/3 checks)")
        else:
            self.log_message(f"❌ Game world unstable ({stable_checks}/3 checks) - check your world templates")
        
        return is_stable
    
    def _is_game_already_running(self) -> bool:
        """Check if game is already running using templates"""
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
                
        except Exception as e:
            self.log_message(f"❌ Error checking if game running: {e}")
            return False
    
    def _verify_stable_game_state(self) -> bool:
        """Quick stability verification"""
        try:
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance:
                return False
            return self._verify_game_world_stable(instance['index'])
        except:
            return False
    
    # Template matching methods
    def _find_any_template(self, screenshot_path: str, template_names: list) -> bool:
        """Find any template from list"""
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                self.log_message(f"❌ Could not load screenshot: {screenshot_path}")
                return False
            
            for template_name in template_names:
                template_path = os.path.join(self.templates_dir, template_name)
                if not os.path.exists(template_path):
                    continue
                
                template = cv2.imread(template_path)
                if template is None:
                    self.log_message(f"⚠️ Could not load template: {template_name}")
                    continue
                
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val >= self.confidence_threshold:
                    self.log_message(f"✅ Template match: {template_name} (confidence: {max_val:.3f})")
                    return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error in template matching: {e}")
            return False
    
    def _find_template_only(self, screenshot_path: str, template_name: str) -> bool:
        """Find specific template without clicking"""
        return self._find_any_template(screenshot_path, [template_name])
    
    def _click_template(self, screenshot_path: str, template_name: str, instance_index: int) -> bool:
        """Click on template if found"""
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
                
                self.log_message(f"👆 Clicking template {template_name} at ({click_x}, {click_y}) confidence: {max_val:.3f}")
                return self._click_position(instance_index, click_x, click_y)
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error clicking template {template_name}: {e}")
            return False
    
    def _click_position(self, instance_index: int, x: int, y: int) -> bool:
        """Click at coordinates using MEmu ADB"""
        try:
            memuc_path = self.instance_manager.MEMUC_PATH
            tap_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "input", "tap", str(x), str(y)]
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return True
            else:
                self.log_message(f"❌ ADB tap failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error clicking position: {e}")
            return False
    
    def _take_screenshot(self, instance_index: int) -> Optional[str]:
        """Take screenshot using MEmu ADB"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"autostart_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/autostart_screen.png"
            
            memuc_path = self.instance_manager.MEMUC_PATH
            
            # Take and pull screenshot
            capture_cmd = [memuc_path, "adb", "-i", str(instance_index), "shell", "screencap", "-p", device_screenshot]
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            
            if capture_result.returncode != 0:
                self.log_message(f"❌ Screenshot capture failed: {capture_result.stderr}")
                return None
            
            time.sleep(0.5)
            
            pull_cmd = [memuc_path, "adb", "-i", str(instance_index), "pull", device_screenshot, local_screenshot]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            
            if pull_result.returncode != 0:
                self.log_message(f"❌ Screenshot pull failed: {pull_result.stderr}")
                return None
            
            # Cleanup device
            subprocess.run([memuc_path, "adb", "-i", str(instance_index), "shell", "rm", device_screenshot], 
                          capture_output=True, timeout=5)
            
            if os.path.exists(local_screenshot) and os.path.getsize(local_screenshot) > 10000:
                return local_screenshot
            else:
                self.log_message(f"❌ Invalid screenshot file")
                return None
            
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
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
        """Check if game is accessible"""
        return self.game_start_completed and self.last_successful_start is not None
    
    def execute_cycle(self) -> bool:
        """Execute cycle for module manager"""
        try:
            if not self.is_available:
                return False
            
            instance = self.instance_manager.get_instance(self.instance_name)
            if not instance or instance["status"] != "Running":
                return True
            
            if not self.game_start_completed:
                return self.start_auto_game()
            
            return True
            
        except:
            return False