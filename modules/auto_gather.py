import os
import time
import threading
import subprocess
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import tempfile

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

class AutoGather:
    def __init__(self, instance_name: str, instance_index: int, log_callback=None):
        self.instance_name = instance_name
        self.instance_index = instance_index
        self.log_callback = log_callback
        self.is_running = False
        self.worker_thread = None
        self.cycle_count = 0
        
        # Configuration
        self.confidence_threshold = 0.8
        self.max_simultaneous_marches = 5
        self.cycle_delay = 60  # seconds between cycles
        
        # Paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.templates_dir = os.path.join(script_dir, "templates")
        
        # Stats
        self.stats = {
            'cycles_completed': 0,
            'marches_created': 0,
            'resources_gathered': 0,
            'errors': 0
        }
        
        # OCR initialization
        self.ocr = None
        self._init_ocr()
        
        self.log_message(f"✅ AutoGather initialized for {instance_name}")
    
    def _init_ocr(self):
        """Initialize OCR with fallback handling"""
        if not PADDLEOCR_AVAILABLE:
            self.log_message("⚠️ PaddleOCR not available, OCR features disabled")
            return
        
        try:
            self.log_message("🤖 Initializing PaddleOCR...")
            # Try primary initialization
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            self.log_message("✅ PaddleOCR initialized successfully")
        except Exception as e:
            self.log_message(f"❌ Failed to initialize OCR: {e}")
            try:
                self.log_message("🔄 Attempting fallback OCR initialization...")
                # Fallback initialization without show_log parameter
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
                self.log_message("✅ PaddleOCR fallback initialization successful")
            except Exception as fallback_error:
                self.log_message(f"❌ OCR fallback failed: {fallback_error}")
                self.ocr = None
    
    def log_message(self, message: str):
        """Send log message to callback"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def start(self):
        """Start the AutoGather worker"""
        if self.is_running:
            self.log_message("⚠️ AutoGather already running")
            return
        
        self.log_message("🚀 Starting AutoGather...")
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.log_message("🔄 AutoGather worker loop started")
        return True
    
    def stop(self):
        """Stop the AutoGather worker"""
        if not self.is_running:
            return
        
        self.log_message("🛑 Stopping AutoGather...")
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.log_message("✅ AutoGather stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        try:
            while self.is_running:
                self.cycle_count += 1
                
                if self._gather_cycle():
                    self.stats['cycles_completed'] += 1
                    self.log_message("✅ Gather cycle completed successfully")
                else:
                    self.stats['errors'] += 1
                    self.log_message("❌ Gather cycle failed")
                
                # Wait before next cycle
                self.log_message(f"⏳ Waiting {self.cycle_delay}s before next cycle...")
                for _ in range(self.cycle_delay):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            self.log_message(f"❌ Worker loop error: {e}")
            self.stats['errors'] += 1
        finally:
            self.is_running = False
    
    def _take_screenshot(self) -> Optional[str]:
        """Take screenshot using ADB method like AutoStart"""
        try:
            # Create temp file for screenshot
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png', 
                prefix=f'autogather_{self.instance_name}_',
                delete=False
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # Use MEmu ADB to take screenshot
            memuc_path = "C:\\Program Files\\Microvirt\\MEmu\\memuc.exe"
            screenshot_cmd = [
                memuc_path, "adb", "-i", str(self.instance_index), 
                "exec-out", "screencap", "-p"
            ]
            
            # Execute command and save to file
            result = subprocess.run(screenshot_cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                with open(temp_path, 'wb') as f:
                    f.write(result.stdout)
                
                # Verify the file is valid
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                    self.log_message(f"✅ Screenshot captured: {os.path.basename(temp_path)}")
                    return temp_path
                else:
                    self.log_message("❌ Invalid screenshot file")
                    self._cleanup_screenshot(temp_path)
                    return None
            else:
                self.log_message(f"❌ Screenshot command failed: {result.stderr}")
                self._cleanup_screenshot(temp_path)
                return None
                
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
            return None
    
    def _click_template(self, screenshot_path: str, template_name: str, confidence_override: float = None) -> bool:
        """Click on template if found - using ADB method like AutoStart"""
        try:
            screenshot = cv2.imread(screenshot_path)
            template_path = os.path.join(self.templates_dir, template_name)
            
            if not os.path.exists(template_path):
                self.log_message(f"❌ Template not found: {template_path}")
                return False
            
            template = cv2.imread(template_path)
            if screenshot is None or template is None:
                self.log_message(f"❌ Failed to load images for template matching")
                return False
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            # Use override confidence or default
            threshold = confidence_override if confidence_override is not None else self.confidence_threshold
            
            if max_val >= threshold:
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                self.log_message(f"👆 Clicking {template_name} at ({click_x}, {click_y}) confidence: {max_val:.3f}")
                
                # Use ADB tap command like AutoStart
                memuc_path = "C:\\Program Files\\Microvirt\\MEmu\\memuc.exe"
                tap_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "shell", "input", "tap", str(click_x), str(click_y)]
                result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log_message(f"✅ Successfully clicked {template_name}")
                    return True
                else:
                    self.log_message(f"❌ Click command failed: {result.stderr}")
                    return False
            else:
                self.log_message(f"❌ Template {template_name} not found (confidence: {max_val:.3f} < {threshold})")
                return False
            
        except Exception as e:
            self.log_message(f"❌ Click template error: {e}")
            return False
    
    def _find_template(self, screenshot_path: str, template_name: str, confidence_override: float = None) -> bool:
        """Check if template exists on screen with optional confidence override"""
        try:
            screenshot = cv2.imread(screenshot_path)
            template_path = os.path.join(self.templates_dir, template_name)
            
            if not os.path.exists(template_path):
                return False
            
            template = cv2.imread(template_path)
            if screenshot is None or template is None:
                return False
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            threshold = confidence_override if confidence_override is not None else self.confidence_threshold
            return max_val >= threshold
            
        except Exception:
            return False
    
    def _debug_available_templates(self) -> None:
        """Debug: List all available templates for troubleshooting"""
        try:
            if os.path.exists(self.templates_dir):
                templates = [f for f in os.listdir(self.templates_dir) if f.endswith('.png')]
                self.log_message(f"🔍 Available templates ({len(templates)}): {', '.join(sorted(templates))}")
            else:
                self.log_message("❌ Templates directory not found")
        except Exception as e:
            self.log_message(f"❌ Error listing templates: {e}")
    
    def _debug_template_confidence(self, screenshot_path: str, template_name: str) -> float:
        """Debug: Get confidence score for a template without clicking"""
        try:
            screenshot = cv2.imread(screenshot_path)
            template_path = os.path.join(self.templates_dir, template_name)
            
            if not os.path.exists(template_path):
                self.log_message(f"🔍 Template {template_name} does not exist")
                return 0.0
            
            template = cv2.imread(template_path)
            if screenshot is None or template is None:
                self.log_message(f"🔍 Failed to load {template_name} or screenshot")
                return 0.0
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            self.log_message(f"🔍 Template {template_name}: confidence {max_val:.3f} at ({max_loc[0]}, {max_loc[1]})")
            return max_val
            
        except Exception as e:
            self.log_message(f"🔍 Error checking {template_name}: {e}")
            return 0.0
    
    def _navigate_to_queue(self) -> bool:
        """Navigate to march queue with flexible confidence thresholds"""
        screenshot_path = self._take_screenshot()
        if not screenshot_path:
            self.log_message("❌ Failed to take initial screenshot")
            return False
        
        try:
            # Try to open left panel with lower confidence threshold for UI elements
            if self._click_template(screenshot_path, "open_left.png", confidence_override=0.7):
                self.log_message("✅ Opened left panel")
                time.sleep(2)  # Wait for panel to open
                
                # Take new screenshot after panel opens
                self._cleanup_screenshot(screenshot_path)
                screenshot_path = self._take_screenshot()
                if not screenshot_path:
                    self.log_message("❌ Failed to take screenshot after opening panel")
                    return False
                
                # Try to click march queue with standard confidence
                if self._click_template(screenshot_path, "gather_button.png"):
                    self.log_message("✅ Clicked march queue")
                    time.sleep(2)
                    return True
                else:
                    self.log_message("❌ Failed to click march queue button")
                    return False
            else:
                self.log_message("❌ Failed to click open left panel")
                return False
                
        finally:
            self._cleanup_screenshot(screenshot_path)
        
        return False
    
    def _check_marches_returning(self) -> bool:
        """Check if any marches are returning soon"""
        try:
            if not self.ocr:
                return False
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Use OCR to read march timers
                result = self.ocr.ocr(screenshot_path, cls=True)
                
                if result and result[0]:
                    for line in result[0]:
                        text = line[1][0].lower()
                        # Look for time patterns indicating marches returning soon
                        if any(pattern in text for pattern in ['0:0', '0:1', '0:2', '0:3', '0:4', '0:5']):
                            self.log_message(f"⏰ March returning soon: {text}")
                            return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error checking march timers: {e}")
            return False
    
    def _find_empty_march_slots(self) -> List[Tuple[int, int]]:
        """Find empty march slots by looking for + buttons"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return []
            
            try:
                empty_slots = []
                screenshot = cv2.imread(screenshot_path)
                template_path = os.path.join(self.templates_dir, "plus_button.png")
                
                if not os.path.exists(template_path):
                    self.log_message("❌ Plus button template not found")
                    return []
                
                template = cv2.imread(template_path)
                if screenshot is None or template is None:
                    return []
                
                # Find all matches above threshold
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):
                    empty_slots.append(pt)
                
                return empty_slots
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error finding empty slots: {e}")
            return []
    
    def _create_gather_march(self, slot_position: Tuple[int, int]) -> bool:
        """Create a gathering march at the specified slot position"""
        try:
            x, y = slot_position
            
            # Click the + button to create new march
            memuc_path = "C:\\Program Files\\Microvirt\\MEmu\\memuc.exe"
            tap_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "shell", "input", "tap", str(x), str(y)]
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.log_message(f"❌ Failed to click slot at ({x}, {y})")
                return False
            
            time.sleep(2)  # Wait for march creation UI
            
            # Look for gather button in march creation interface
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                if self._click_template(screenshot_path, "gather_button.png"):
                    self.log_message("✅ Clicked gather button")
                    time.sleep(1)
                    
                    # Select resource type (wood by default)
                    if self._click_template(screenshot_path, "wood_icon.png"):
                        self.log_message("✅ Selected wood resource")
                        time.sleep(1)
                        
                        # Search for resource nodes
                        if self._click_template(screenshot_path, "search_button.png"):
                            self.log_message("✅ Started resource search")
                            time.sleep(3)  # Wait for search results
                            
                            # Deploy to first available resource
                            if self._click_template(screenshot_path, "deploy_button.png"):
                                self.log_message("✅ Deployed march")
                                return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error creating march: {e}")
            return False
    
    def _gather_cycle(self) -> bool:
        """Single gather cycle with enhanced debugging"""
        try:
            self.log_message(f"🌾 Starting AutoGather cycle {self.cycle_count}")
            
            # Debug available templates on first cycle
            if self.cycle_count == 1:
                self._debug_available_templates()
            
            # Navigate to march queue
            self.log_message("📋 Navigating to march queue...")
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                self.log_message("❌ Failed to take initial screenshot")
                return False
            
            try:
                # Debug: Check confidence for key templates
                self._debug_template_confidence(screenshot_path, "open_left.png")
                self._debug_template_confidence(screenshot_path, "gather_button.png")
                
                # Try navigation with lower confidence for UI elements
                if not self._navigate_to_queue():
                    self.log_message("❌ Failed to navigate to queue")
                    return False
                
                # Check if we need to wait for marches to return
                if self._check_marches_returning():
                    self.log_message("⏰ Marches returning soon, waiting...")
                    return True
                
                # Look for empty march slots
                empty_slots = self._find_empty_march_slots()
                if not empty_slots:
                    self.log_message("🚫 No empty march slots available")
                    return True
                
                self.log_message(f"✅ Found {len(empty_slots)} empty march slots")
                
                # Process each empty slot
                for slot_index, slot_position in enumerate(empty_slots):
                    if slot_index >= self.max_simultaneous_marches:
                        self.log_message(f"🛑 Reached max marches limit ({self.max_simultaneous_marches})")
                        break
                    
                    self.log_message(f"🎯 Processing slot {slot_index + 1}/{len(empty_slots)}")
                    
                    if self._create_gather_march(slot_position):
                        self.stats['marches_created'] += 1
                        self.log_message(f"✅ March {slot_index + 1} created successfully")
                    else:
                        self.log_message(f"❌ Failed to create march {slot_index + 1}")
                    
                    time.sleep(1)  # Small delay between marches
                
                return True
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Gather cycle error: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: str):
        """Cleanup screenshot file"""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except:
            pass
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'cycle_count': self.cycle_count,
            'instance_name': self.instance_name
        }