"""
BENSON v2.0 - IMPROVED AutoStart Module
Enhanced popup detection and handling for game offers/dialogs
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
    """Template-only AutoStart - IMPROVED VERSION with better popup handling"""
    
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
        
        # Configuration - HIGHER confidence for precise popup detection
        self.templates_dir = "templates"
        self.confidence_threshold = 0.8  # For menu detection
        self.close_button_confidence = 0.75  # Raised back up for precision
        self.world_confidence = 0.8  # For world detection
        self.default_max_retries = 3
        self.retry_delay = 10
        self.game_load_timeout = 90
        
        # Dialog detection state
        self.last_dialog_close_time = 0
        self.dialog_close_cooldown = 3  # Reduced cooldown
        
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
        
        # ALL close button templates - FIXED close_x6.png (not close_6.png)
        self.CLOSE_BUTTONS = [
            "close_x.png", "close_x2.png", "close_x3.png", "close_x4.png", "close_x5.png", "close_x6.png",
            "close_btn.png", "close_2.png", "close_3.png", "close_4.png", "close_5.png", 
            "closeadd.png", "closeadd2.png", "close_gather.png", "close_left.png"
        ]
        
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
        
        # Log available templates for debugging - FIXED to show actual available close templates
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
            
            # Debug: show ALL available templates to see what we actually have
            self.log_message(f"🔍 ALL available templates: {', '.join(sorted(available_templates))}")
            
            # Check specifically for close_x6.png (not close_6.png)
            if "close_x6.png" in available_templates:
                self.log_message("✅ close_x6.png found in templates!")
            else:
                self.log_message("❌ close_x6.png NOT found in templates directory")
    
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
                if self._attempt_game_start_improved(instance_name):
                    return True
            except Exception as e:
                self.log_message(f"❌ Attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                self.log_message(f"⏳ Waiting {self.retry_delay}s before retry")
                time.sleep(self.retry_delay)
        
        self.log_message("❌ All attempts failed - check your templates and game state")
        return False
    
    def _attempt_game_start_improved(self, instance_name: str) -> bool:
        """Improved game start attempt - launch first, then handle popups"""
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
                    return self._start_from_main_menu_improved(screenshot_path, instance['index'])
                elif game_state == "UNKNOWN_STATE":
                    # ONLY look for popups if we're in unknown state (might be popup blocking)
                    return self._handle_unknown_state_improved(screenshot_path, instance['index'])
                else:
                    self.log_message(f"❌ Unhandled game state: {game_state}")
                    return False
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error in game start attempt: {e}")
            return False
    
    def _check_and_clear_popup_precise(self, screenshot_path: str, instance_index: int) -> bool:
        """Precisely check and clear popups with HIGH confidence only"""
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return False
            
            # Check each close button template with HIGH confidence only
            best_match = None
            best_confidence = 0
            
            for close_button in self.CLOSE_BUTTONS:
                template_path = os.path.join(self.templates_dir, close_button)
                if not os.path.exists(template_path):
                    continue
                
                template = cv2.imread(template_path)
                if template is None:
                    continue
                
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                # Track best match for logging
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = (close_button, max_loc, max_val)
                
                # ONLY accept HIGH confidence matches to avoid misclicks
                if max_val >= self.close_button_confidence:
                    # Calculate click position
                    template_h, template_w = template.shape[:2]
                    click_x = max_loc[0] + template_w // 2
                    click_y = max_loc[1] + template_h // 2
                    
                    # Ensure click is within screen bounds
                    screen_h, screen_w = screenshot.shape[:2]
                    click_x = max(10, min(click_x, screen_w - 10))
                    click_y = max(10, min(click_y, screen_h - 10))
                    
                    self.log_message(f"🎯 HIGH CONFIDENCE popup close: {close_button} at ({click_x}, {click_y}) confidence: {max_val:.3f}")
                    
                    if self._click_position(instance_index, click_x, click_y):
                        return True
            
            # Only log if no popup found (don't spam about low confidence matches)
            if not best_match or best_confidence < 0.5:
                return False
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error in precise popup check: {e}")
            return False
    
    def _find_and_close_popup_at_confidence(self, screenshot_path: str, instance_index: int, confidence: float) -> bool:
        """Find and close popup at specific confidence level - ONLY use high confidence"""
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return False
            
            # Check each close button template with HIGH confidence only
            for close_button in self.CLOSE_BUTTONS:
                template_path = os.path.join(self.templates_dir, close_button)
                if not os.path.exists(template_path):
                    continue
                
                template = cv2.imread(template_path)
                if template is None:
                    continue
                
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                # ONLY accept very high confidence matches (exact template matches)
                if max_val >= self.close_button_confidence:
                    # Calculate click position
                    template_h, template_w = template.shape[:2]
                    click_x = max_loc[0] + template_w // 2
                    click_y = max_loc[1] + template_h // 2
                    
                    # Ensure click is within screen bounds
                    screen_h, screen_w = screenshot.shape[:2]
                    click_x = max(10, min(click_x, screen_w - 10))
                    click_y = max(10, min(click_y, screen_h - 10))
                    
                    self.log_message(f"🎯 Found EXACT popup close: {close_button} at ({click_x}, {click_y}) confidence: {max_val:.3f}")
                    
                    if self._click_position(instance_index, click_x, click_y):
                        return True
                else:
                    # Log near misses for debugging
                    if max_val >= 0.5:
                        self.log_message(f"🔍 Close match but too low: {close_button} confidence: {max_val:.3f} (need {self.close_button_confidence})")
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error in popup detection: {e}")
            return False
    
    def _detect_game_state(self, screenshot_path: str) -> str:
        """Detect current game state using only templates"""
        try:
            # Use higher confidence for world detection to avoid false positives
            if self._find_any_template_with_confidence(screenshot_path, self.GAME_WORLD_INDICATORS, self.world_confidence):
                return "ALREADY_IN_GAME"
            if self._find_any_template_with_confidence(screenshot_path, self.MAIN_MENU_INDICATORS, self.confidence_threshold):
                return "MAIN_MENU"
            return "UNKNOWN_STATE"
        except Exception as e:
            self.log_message(f"❌ Error detecting game state: {e}")
            return "UNKNOWN_STATE"
    
    def _find_any_template_with_confidence(self, screenshot_path: str, template_names: list, confidence: float) -> bool:
        """Find any template from list with specific confidence"""
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
                
                if max_val >= confidence:
                    self.log_message(f"✅ Template match: {template_name} (confidence: {max_val:.3f}) [threshold: {confidence}]")
                    return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error in template matching: {e}")
            return False
    
    def _start_from_main_menu_improved(self, screenshot_path: str, instance_index: int) -> bool:
        """Start game from main menu with improved timing"""
        try:
            self.log_message(f"🎮 Starting game from main menu")
            
            # Try to find and click game launcher template
            for template in self.MAIN_MENU_INDICATORS:
                if self._click_template_improved(screenshot_path, template, instance_index):
                    self.log_message(f"✅ Clicked game launcher using template: {template}")
                    
                    # IMPROVED: Wait 5 seconds for game loading to start
                    self.log_message("⏳ Waiting 5 seconds for game loading to begin...")
                    time.sleep(5)
                    
                    return self._wait_for_game_load_improved(instance_index)
            
            self.log_message("❌ No main menu templates matched current screen")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error starting from main menu: {e}")
            return False
    
    def _wait_for_game_load_improved(self, instance_index: int) -> bool:
        """Wait for game to load - check every second for popups with high precision"""
        self.log_message(f"⏳ Monitoring game loading (timeout: {self.game_load_timeout}s, checking every 1s)")
        
        start_time = time.time()
        check_count = 0
        last_state = None
        consecutive_unknown_states = 0
        
        while (time.time() - start_time) < self.game_load_timeout:
            check_count += 1
            
            screenshot_path = self._take_screenshot(instance_index)
            if not screenshot_path:
                self.log_message("⚠️ Failed to take screenshot, retrying...")
                time.sleep(2)
                continue
            
            try:
                state = self._detect_game_state(screenshot_path)
                
                # Only log important state changes
                if state != last_state and state in ["ALREADY_IN_GAME", "MAIN_MENU"]:
                    self.log_message(f"🔍 Game state: {state}")
                last_state = state
                consecutive_unknown_states = 0
                
                if state == "ALREADY_IN_GAME":
                    if self._verify_game_world_stable(instance_index):
                        self.log_message(f"✅ Game loaded successfully")
                        return True
                elif state == "MAIN_MENU":
                    # Still in menu - might need another click
                    self.log_message("🔄 Still in menu - trying to click launcher again")
                    if self._click_template_improved(screenshot_path, "game_launcher.png", instance_index):
                        self.log_message("✅ Clicked launcher again")
                        # Wait another 5 seconds after re-clicking
                        time.sleep(5)
                elif state == "UNKNOWN_STATE":
                    consecutive_unknown_states += 1
                    
                    # Check for popups immediately when unknown state detected
                    if self._check_and_clear_popup_precise(screenshot_path, instance_index):
                        self.log_message("✅ Cleared popup - continuing to monitor")
                        consecutive_unknown_states = 0
                        # Check again quickly after clearing popup
                        time.sleep(1)
                        continue
                
            finally:
                self._cleanup_screenshot(screenshot_path)
            
            # IMPROVED: Check every 1 second instead of 4 seconds
            time.sleep(1)
        
        self.log_message("❌ Game load timeout")
        return False
    
    def _handle_unknown_state_improved(self, screenshot_path: str, instance_index: int) -> bool:
        """Handle unknown state - check for popup with high precision"""
        self.log_message(f"❓ Unknown state - checking for blocking popup")
        
        # Use precise popup checking
        if self._check_and_clear_popup_precise(screenshot_path, instance_index):
            time.sleep(2)  # Wait for popup to close
            
            # Check state again after clearing popup
            new_screenshot = self._take_screenshot(instance_index)
            if new_screenshot:
                try:
                    new_state = self._detect_game_state(new_screenshot)
                    self.log_message(f"🔍 State after popup clearing: {new_state}")
                    
                    if new_state == "ALREADY_IN_GAME":
                        return self._verify_game_world_stable(instance_index)
                    elif new_state == "MAIN_MENU":
                        return self._start_from_main_menu_improved(new_screenshot, instance_index)
                    else:
                        self.log_message(f"⚠️ Still unknown after popup clearing: {new_state}")
                        
                finally:
                    self._cleanup_screenshot(new_screenshot)
        else:
            self.log_message("ℹ️ No high-confidence popup found")
        
        self.log_message("❌ Could not resolve unknown state")
        return False
    
    def _verify_game_world_stable(self, instance_index: int) -> bool:
        """Verify game world is stable using templates"""
        self.log_message(f"🔍 Verifying game world stability...")
        
        stable_checks = 0
        for check in range(3):
            time.sleep(1)
            
            screenshot_path = self._take_screenshot(instance_index)
            if screenshot_path:
                try:
                    if self._find_any_template_with_confidence(screenshot_path, self.GAME_WORLD_INDICATORS, self.world_confidence):
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
            self.log_message(f"❌ Game world unstable ({stable_checks}/3 checks)")
        
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
                return self._find_any_template_with_confidence(screenshot_path, self.GAME_WORLD_INDICATORS, self.world_confidence)
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
    
    def _click_template_improved(self, screenshot_path: str, template_name: str, instance_index: int) -> bool:
        """Improved template clicking with better accuracy"""
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
            
            # Use appropriate confidence threshold
            threshold = self.close_button_confidence if template_name in self.CLOSE_BUTTONS else self.confidence_threshold
            
            if max_val >= threshold:
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                # Ensure click is within reasonable bounds
                screen_h, screen_w = screenshot.shape[:2]
                click_x = max(10, min(click_x, screen_w - 10))
                click_y = max(10, min(click_y, screen_h - 10))
                
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