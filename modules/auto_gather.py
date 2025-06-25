"""
BENSON v2.0 - Simple AutoGather Navigation
Just clicks open_left → wait → click wilderness_button → OCR
"""

import os
import time
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import tempfile

from modules.base_module import BaseModule, ModulePriority


@dataclass
class AutoGatherConfig:
    """Simple configuration for AutoGather module"""
    cycle_interval: int = 20
    template_matching_threshold: float = 0.6
    ocr_confidence_threshold: float = 0.35
    save_ocr_images: bool = True
    ocr_save_directory: str = "ocr_images"
    keep_ocr_images_days: int = 7


class AutoGatherModule(BaseModule):
    """
    Simple AutoGather module - just does the navigation sequence and OCR
    """
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        super().__init__(instance_name, shared_resources, console_callback)
        
        self.module_name = "AutoGather"
        self.check_interval = 20
        self.config = AutoGatherConfig()
        
        # MEmu setup
        self.memu_path = self._get_memu_path()
        self.instance_index = self._get_instance_index()
        
        # Template paths
        self.templates_dir = "templates"
        self.templates = {
            'open_left': os.path.join(self.templates_dir, 'open_left.png'),
            'wilderness_button': os.path.join(self.templates_dir, 'wilderness_button.png')
        }
        
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize queue analyzer
        self.queue_analyzer = None
        self._initialize_queue_analyzer()
        
        self.queues: Dict[int, object] = {}
        self.last_analysis_time = None
        
        self.log_message(f"✅ AutoGather module initialized for {instance_name} (SIMPLE NAVIGATION)")
    
    def get_module_priority(self) -> ModulePriority:
        return ModulePriority.HIGH
    
    def get_dependencies(self) -> List[str]:
        return ["AutoStartGame"]
    
    def is_available(self) -> bool:
        try:
            import cv2
            import numpy as np
        except ImportError:
            return False
        return self._is_game_accessible()
    
    def get_missing_dependencies(self) -> List[str]:
        missing = []
        try:
            import cv2
            import numpy as np
        except ImportError:
            missing.append("opencv-python")
        
        try:
            import easyocr
        except ImportError:
            missing.append("easyocr")
        
        if not self._is_game_accessible():
            missing.append("game_must_be_accessible")
        
        return missing
    
    def _is_game_accessible(self) -> bool:
        try:
            if hasattr(self.shared_resources, 'shared_state'):
                game_key = f"game_accessible_{self.instance_name}"
                return self.shared_resources.shared_state.get(game_key, False)
            return True
        except Exception as e:
            self.log_message(f"⚠️ Error checking game accessibility: {e}")
            return False
    
    def _get_memu_path(self) -> str:
        try:
            if hasattr(self.shared_resources, 'MEMUC_PATH'):
                return self.shared_resources.MEMUC_PATH
            return r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        except Exception as e:
            self.log_message(f"⚠️ Error getting MEmu path: {e}")
            return r"C:\Program Files\Microvirt\MEmu\memuc.exe"
    
    def _get_instance_index(self) -> int:
        try:
            if not self.shared_resources:
                return 1
            
            if hasattr(self.shared_resources, 'get_instance'):
                instance = self.shared_resources.get_instance(self.instance_name)
                if instance:
                    index = instance.get('index', 1)
                    self.log_message(f"✅ Found instance index: {index}")
                    return index
            
            if hasattr(self.shared_resources, 'instances'):
                for i, instance in enumerate(self.shared_resources.instances):
                    try:
                        if isinstance(instance, dict):
                            inst_name = instance.get('name', '')
                            inst_index = instance.get('index', i + 1)
                        else:
                            inst_name = getattr(instance, 'name', '')
                            inst_index = getattr(instance, 'index', i + 1)
                        
                        if inst_name == self.instance_name:
                            self.log_message(f"✅ Found matching instance: {inst_name} at index {inst_index}")
                            return inst_index
                    except Exception as e:
                        continue
            
            self.log_message(f"❌ Instance {self.instance_name} not found, using fallback index 1")
            return 1
        except Exception as e:
            self.log_message(f"❌ Error getting instance index: {e}")
            return 1
    
    def _initialize_queue_analyzer(self):
        try:
            from modules.march_queue_analyzer import MarchQueueAnalyzer
            
            self.queue_analyzer = MarchQueueAnalyzer(
                instance_name=self.instance_name,
                config=self.config,
                log_callback=self.log_message
            )
            
            self.log_message("✅ March queue analyzer initialized")
        except ImportError as e:
            self.log_message(f"❌ Could not import MarchQueueAnalyzer: {e}")
            self.queue_analyzer = None
        except Exception as e:
            self.log_message(f"❌ Error initializing queue analyzer: {e}")
            self.queue_analyzer = None
    
    def execute_cycle(self) -> bool:
        """Simple navigation: open_left → wait → wilderness_button → OCR"""
        try:
            if not self.is_available():
                self.log_message("Game not accessible, skipping cycle")
                return False
            
            self.log_message("📋 Starting simple navigation sequence...")
            
            # Step 1: Click open_left
            self.log_message("🔄 Step 1: Clicking open_left button")
            if not self._click_open_left():
                self.log_message("❌ Failed to click open_left")
                return False
            
            # Step 2: Wait 1 second
            self.log_message("⏳ Step 2: Waiting 1 second for left panel to open")
            time.sleep(1)
            
            # Step 3: Click wilderness_button
            self.log_message("🌲 Step 3: Clicking wilderness button")
            if not self._click_wilderness_button():
                self.log_message("❌ Failed to click wilderness_button")
                return False
            
            # Step 4: Wait for march queue to load
            self.log_message("⏳ Step 4: Waiting 3 seconds for march queue to load")
            time.sleep(3)
            
            # Step 5: Do OCR analysis
            self.log_message("🔍 Step 5: Starting OCR analysis")
            self._analyze_march_queues()
            
            self.log_message("✅ Simple navigation completed successfully")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error in simple navigation: {e}")
            return False
    
    def _click_open_left(self) -> bool:
        """Take screenshot and click open_left button"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                return self._click_template(screenshot_path, 'open_left')
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception as e:
            self.log_message(f"❌ Error clicking open_left: {e}")
            return False
    
    def _click_wilderness_button(self) -> bool:
        """Take screenshot and click wilderness_button"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                return self._click_template(screenshot_path, 'wilderness_button')
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception as e:
            self.log_message(f"❌ Error clicking wilderness_button: {e}")
            return False
    
    def _click_template(self, screenshot_path: str, template_name: str) -> bool:
        """Click template with basic template matching"""
        try:
            import cv2
            
            template_path = self.templates.get(template_name)
            if not template_path or not os.path.exists(template_path):
                self.log_message(f"❌ Template not found: {template_name}")
                return False
            
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                self.log_message(f"❌ Failed to load images for {template_name}")
                return False
            
            # Template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            self.log_message(f"🔍 {template_name} confidence: {max_val:.3f} (threshold: {self.config.template_matching_threshold})")
            
            if max_val >= self.config.template_matching_threshold:
                template_height, template_width = template.shape[:2]
                click_x = max_loc[0] + template_width // 2
                click_y = max_loc[1] + template_height // 2
                
                self.log_message(f"✅ {template_name} found at ({click_x}, {click_y})")
                
                # Click the position
                return self._click_position(click_x, click_y, template_name)
            else:
                self.log_message(f"❌ {template_name} confidence too low: {max_val:.3f}")
                return False
        
        except Exception as e:
            self.log_message(f"❌ Template matching error for {template_name}: {e}")
            return False
    
    def _click_position(self, x: int, y: int, context: str = "") -> bool:
        """Click position using ADB"""
        try:
            tap_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            self.log_message(f"👆 Clicking {context} at ({x}, {y})")
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_message(f"✅ Successfully clicked {context}")
                return True
            else:
                self.log_message(f"❌ Click failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_message(f"❌ Click command timed out")
            return False
        except Exception as e:
            self.log_message(f"❌ Click error: {e}")
            return False
    
    def _take_screenshot(self) -> Optional[str]:
        """Take screenshot using ADB"""
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            local_screenshot = os.path.join(temp_dir, f"autogather_screenshot_{self.instance_index}_{timestamp}.png")
            device_screenshot = "/sdcard/autogather_screen.png"
            
            # Take screenshot on device
            capture_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "screencap", "-p", device_screenshot
            ]
            
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            if capture_result.returncode != 0:
                self.log_message(f"❌ Screenshot capture failed")
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot from device
            pull_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "pull", device_screenshot, local_screenshot
            ]
            
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            if pull_result.returncode != 0:
                self.log_message(f"❌ Screenshot pull failed")
                return None
            
            # Clean up device screenshot
            cleanup_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "rm", device_screenshot
            ]
            subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
            
            # Verify screenshot
            if os.path.exists(local_screenshot):
                file_size = os.path.getsize(local_screenshot)
                if file_size > 10000:
                    self.log_message(f"📸 Screenshot taken ({file_size} bytes)")
                    return local_screenshot
                else:
                    self.log_message(f"❌ Screenshot too small: {file_size} bytes")
                    os.remove(local_screenshot)
            
            return None
        
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
            return None
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """Clean up screenshot file"""
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception:
                pass
    
    def _analyze_march_queues(self):
        """Analyze march queues using OCR"""
        try:
            if not self.queue_analyzer:
                self.log_message("❌ Queue analyzer not available")
                return
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                self.log_message("❌ Failed to take screenshot for OCR")
                return
            
            try:
                self.queues = self.queue_analyzer.analyze_march_queues(screenshot_path)
                self.last_analysis_time = datetime.now()
                
                # Log results
                available_count = len([q for q in self.queues.values() if q.is_available])
                self.log_message(f"✅ OCR complete: {len(self.queues)} queues analyzed, {available_count} available")
                
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception as e:
            self.log_message(f"❌ OCR analysis error: {e}")
    
    def get_status(self) -> Dict:
        """Get current AutoGather status"""
        queue_count = len(self.queues)
        available_queues = len([q for q in self.queues.values() if q.is_available])
        
        return {
            "running": self.status.value == "running",
            "instance_name": self.instance_name,
            "instance_index": self.instance_index,
            "queue_count": queue_count,
            "available_queues": available_queues,
            "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "simple_navigation": True
        }
    
    def force_cycle(self) -> bool:
        """Force a single cycle"""
        try:
            if self.status.value == "running":
                self.log_message("⚠️ AutoGather is already running")
                return False
            
            self.log_message("🎯 Force running simple navigation cycle...")
            
            if not self.is_available():
                missing = self.get_missing_dependencies()
                self.log_message(f"❌ Missing dependencies: {missing}")
                return False
            
            return self.execute_cycle()
        
        except Exception as e:
            self.log_message(f"❌ Error in force cycle: {e}")
            return False


# Convenience functions
def create_autogather_module(instance_name: str, shared_resources=None, console_callback=None) -> AutoGatherModule:
    """Create simple AutoGather module"""
    return AutoGatherModule(instance_name, shared_resources, console_callback)


def test_autogather_prerequisites(instance_name: str, shared_resources=None) -> Dict:
    """Test if AutoGather can run"""
    try:
        module = AutoGatherModule(instance_name, shared_resources)
        
        is_available = module.is_available()
        missing_deps = module.get_missing_dependencies()
        
        return {
            "instance_name": instance_name,
            "available": is_available,
            "missing_dependencies": missing_deps,
            "overall_ready": is_available and len(missing_deps) == 0,
            "simple_navigation": True
        }
    
    except Exception as e:
        return {
            "instance_name": instance_name,
            "error": str(e),
            "overall_ready": False,
            "simple_navigation": False
        }