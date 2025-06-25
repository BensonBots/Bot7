"""
BENSON v2.0 - Fixed AutoGather Module with OCR Queue Analysis
Proper OCR integration and intelligent gathering logic
"""

import os
import time
import threading
import subprocess
from typing import Dict, Optional
from datetime import datetime


class AutoGatherModule:
    """Fixed AutoGather with OCR queue analysis and intelligent gathering"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        self.instance_name = instance_name
        self.shared_resources = shared_resources
        self.console_callback = console_callback or print
        self.instance_index = self._get_instance_index()
        
        # State management
        self.is_running = False
        self.worker_thread = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.cycle_delay = 60  # 60 seconds between cycles (more reasonable)
        self.max_retries = 3
        self.last_queue_analysis = None
        self.available_queues = []
        
        # OCR integration
        self.queue_analyzer = None
        self._init_queue_analyzer()
        
        # Template-based navigation (no coordinate guessing)
        self.navigation_templates = {
            'open_left': ['open_left.png'],
            'wilderness_button': ['wilderness_button.png'],
            'close_left': ['close_left.png']
        }
        
        # Template matching confidence (adjusted for practical use)
        self.confidence_thresholds = {
            'open_left': 0.65,     # Lowered from 0.8 - still higher than normal for precision
            'close_left': 0.65,    # Lowered from 0.8 - still higher than normal for precision
            'wilderness_button': 0.6  # Normal confidence
        }
        
        self.log_message(f"✅ AutoGather initialized for {instance_name}")
    
    def _init_queue_analyzer(self):
        """Initialize Local InternVL OCR analyzer only"""
        try:
            from modules.local_internvl_analyzer import LocalInternVLAnalyzer
            
            config = {
                'confidence_threshold': 0.6,
                'templates_dir': 'templates'
            }
            
            self.queue_analyzer = LocalInternVLAnalyzer(
                instance_name=self.instance_name,
                config=config,
                log_callback=self.console_callback
            )
            
            # Check if model loaded successfully
            if self.queue_analyzer.is_available():
                model_info = self.queue_analyzer.get_model_info()
                self.log_message(f"✅ Local InternVL initialized on {model_info['device']}")
                self.ocr_method = f"Local InternVL ({model_info['device']})"
            else:
                self.log_message("❌ Local InternVL failed to initialize")
                self.log_message("💡 Install requirements: pip install transformers torch torchvision")
                self.queue_analyzer = None
                self.ocr_method = "Failed"
                
        except ImportError:
            self.log_message("❌ Local InternVL not available - missing dependencies")
            self.log_message("📋 Install with: pip install transformers torch torchvision pillow")
            self.queue_analyzer = None
            self.ocr_method = "Missing Dependencies"
        except Exception as e:
            self.log_message(f"❌ Local InternVL init error: {e}")
            self.queue_analyzer = None
            self.ocr_method = "Error"
    
    def _get_instance_index(self) -> Optional[int]:
        """Get MEmu instance index"""
        try:
            instances = self.shared_resources.get_instances()
            for instance in instances:
                if instance["name"] == self.instance_name:
                    return instance["index"]
            return None
        except Exception as e:
            self.log_message(f"❌ Error getting instance index: {e}")
            return None
    
    def log_message(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [AutoGather-{self.instance_name}] {message}"
        self.console_callback(formatted_message)
    
    def start(self):
        """Start AutoGather module"""
        if self.is_running:
            self.log_message("⚠️ AutoGather already running")
            return False
        
        # Check if game is accessible
        if not self._is_game_accessible():
            self.log_message("❌ Game not accessible - AutoStart must complete first")
            return False
        
        try:
            self.log_message("🚀 Starting AutoGather module...")
            self.is_running = True
            self.stop_event.clear()
            
            # Start worker thread
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            
            self.log_message("✅ AutoGather started successfully")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to start AutoGather: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop AutoGather module"""
        if not self.is_running:
            return True
        
        self.log_message("🛑 Stopping AutoGather...")
        self.is_running = False
        self.stop_event.set()
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        self.log_message("✅ AutoGather stopped")
        return True
    
    def _is_game_accessible(self) -> bool:
        """Check if game is accessible via shared state"""
        try:
            # Get shared state
            shared_state = getattr(self.shared_resources, 'shared_state', {})
            
            # Check multiple accessibility keys
            accessibility_keys = [
                f"game_accessible_{self.instance_name}",
                f"autostart_completed_{self.instance_name}",
                "game_accessible",
                "game_world_active"
            ]
            
            for key in accessibility_keys:
                if shared_state.get(key, False):
                    return True
            
            # Fallback: Check if instance is running
            instance = self.shared_resources.get_instance(self.instance_name)
            if instance and instance["status"] == "Running":
                self.log_message("⚠️ Instance running but no accessibility state - proceeding anyway")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error checking game accessibility: {e}")
            return False
    
    def _worker_loop(self):
        """Main worker loop with OCR queue analysis"""
        self.log_message("🔄 AutoGather worker loop started")
        cycle_count = 1
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Re-check game accessibility each cycle
                if not self._is_game_accessible():
                    self.log_message("⏸ Game no longer accessible, pausing...")
                    time.sleep(10)
                    continue
                
                start_time = time.time()
                self.log_message(f"🌾 Starting AutoGather cycle {cycle_count}")
                
                # Step 1: Navigate to march queue (this will open it if needed)
                navigation_success = self._perform_navigation()
                
                if navigation_success:
                    # Step 2: Analyze march queues with OCR (now that queue is open)
                    queue_analysis = self._analyze_march_queues()
                    
                    # Step 3: Check if we need to gather based on queue status
                    if self._should_start_gathering(queue_analysis):
                        self.log_message("✅ Available queues found - gathering should start automatically")
                        success = True
                        
                        # Step 4: Wait and analyze queues again to see if gathering started
                        time.sleep(3)
                        post_analysis = self._analyze_march_queues()
                        self._compare_queue_states(queue_analysis, post_analysis)
                    else:
                        self.log_message("⏸ No available queues - skipping gathering")
                        success = True  # Not an error, just nothing to do
                else:
                    self.log_message("❌ Failed to navigate to march queue")
                    success = False
                
                elapsed_time = time.time() - start_time
                
                if success:
                    self.log_message(f"✅ AutoGather cycle {cycle_count} completed (took {elapsed_time:.1f}s)")
                else:
                    self.log_message(f"❌ AutoGather cycle {cycle_count} failed (took {elapsed_time:.1f}s)")
                
                cycle_count += 1
                
                # Wait before next cycle
                if self.is_running:
                    self.log_message(f"⏳ Waiting {self.cycle_delay}s before next cycle...")
                    for _ in range(self.cycle_delay):
                        if self.stop_event.wait(1):
                            break
                
            except Exception as e:
                self.log_message(f"❌ Error in worker loop: {e}")
                time.sleep(5)
        
        self.is_running = False
        self.log_message("🏁 AutoGather worker loop ended")
    
    def _analyze_march_queues(self) -> Dict:
        """Analyze march queues using Local InternVL only"""
        try:
            if not self.queue_analyzer:
                self.log_message("❌ Local InternVL not available - cannot analyze queues")
                self.log_message("💡 Install: pip install transformers torch torchvision pillow")
                return {"available_queues": [], "method": "unavailable", "error": "InternVL not initialized"}
            
            if not self.queue_analyzer.is_available():
                self.log_message("❌ Local InternVL model not loaded")
                return {"available_queues": [], "method": "model_not_loaded"}
            
            # Take screenshot for Local InternVL analysis
            screenshot_path = self._take_screenshot_for_ocr()
            if not screenshot_path:
                self.log_message("❌ Failed to take screenshot for Local InternVL")
                return {"available_queues": [], "method": "screenshot_failed"}
            
            try:
                self.log_message(f"🤖 Analyzing march queues with {self.ocr_method}...")
                queue_results = self.queue_analyzer.analyze_march_queues(screenshot_path)
                
                # Process Local InternVL results
                available_queues = []
                for queue_num, queue_info in queue_results.items():
                    if queue_info.is_available:
                        available_queues.append(queue_num)
                        self.log_message(f"📊 Queue {queue_num}: AVAILABLE")
                    else:
                        task_info = f" - {queue_info.task}" if queue_info.task and queue_info.task != 'idle' else ""
                        timer_info = f" ({queue_info.time_remaining})" if queue_info.time_remaining else ""
                        self.log_message(f"📊 Queue {queue_num}: BUSY{task_info}{timer_info}")
                
                self.available_queues = available_queues
                self.last_queue_analysis = {
                    "timestamp": datetime.now(),
                    "available_queues": available_queues,
                    "total_queues": len(queue_results),
                    "method": "local_internvl",
                    "device": self.queue_analyzer.device if hasattr(self.queue_analyzer, 'device') else "unknown"
                }
                
                return self.last_queue_analysis
                
            finally:
                # Cleanup screenshot
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                
        except Exception as e:
            self.log_message(f"❌ Error in Local InternVL analysis: {e}")
            return {"available_queues": [], "method": "error", "error": str(e)}
    
    def _take_screenshot_for_ocr(self) -> Optional[str]:
        """Take screenshot specifically for OCR analysis"""
        try:
            if not self.instance_index:
                return None
            
            import tempfile
            temp_dir = tempfile.gettempdir()
            screenshot_path = os.path.join(temp_dir, f"autogather_ocr_{self.instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/autogather_ocr.png"
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Take screenshot
            capture_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "shell", "screencap", "-p", device_screenshot]
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            
            if capture_result.returncode != 0:
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot
            pull_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "pull", device_screenshot, screenshot_path]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            
            if pull_result.returncode != 0:
                return None
            
            # Cleanup device
            subprocess.run([memuc_path, "adb", "-i", str(self.instance_index), "shell", "rm", device_screenshot], 
                          capture_output=True, timeout=5)
            
            if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 10000:
                return screenshot_path
            
            return None
            
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
            return None
    
    def _should_start_gathering(self, queue_analysis: Dict) -> bool:
        """Determine if we should start gathering based on queue analysis"""
        available_queues = queue_analysis.get("available_queues", [])
        
        if not available_queues:
            self.log_message("⏸ No available queues for gathering")
            return False
        
        # Check if we have queues available for AutoGather (typically queues 1-2)
        gather_queues = [q for q in available_queues if q <= 2]
        
        if not gather_queues:
            self.log_message("⏸ No AutoGather queues available (all gathering queues busy)")
            return False
        
        self.log_message(f"✅ Found {len(gather_queues)} available gathering queues: {gather_queues}")
        return True
    
    def _perform_navigation(self) -> bool:
        """Perform navigation sequence: open_left → wilderness_button → OCR when close_left appears"""
        try:
            self.log_message("📋 Starting template-based navigation to march queue...")
            
            # Take initial screenshot
            screenshot_path = self._take_screenshot_for_navigation()
            if not screenshot_path:
                self.log_message("❌ Failed to take initial screenshot")
                return False
            
            try:
                # Step 1: Check if march queue is already open (look for close_left)
                if self._find_template_in_screenshot(screenshot_path, 'close_left'):
                    self.log_message("✅ March queue already open - proceeding to OCR")
                    return True
                
                # Step 2: Click open_left button to open menu
                if not self._click_template_from_list(screenshot_path, 'open_left'):
                    self.log_message("❌ Failed to find and click open_left button")
                    return False
                
                time.sleep(2)  # Wait for menu to open
                
                # Take new screenshot after menu opens
                menu_screenshot = self._take_screenshot_for_navigation()
                if not menu_screenshot:
                    self.log_message("❌ Failed to take screenshot after menu opened")
                    return False
                
                try:
                    # Step 3: Click wilderness_button to open march queue
                    if not self._click_template_from_list(menu_screenshot, 'wilderness_button'):
                        self.log_message("❌ Failed to find and click wilderness_button")
                        return False
                    
                    time.sleep(3)  # Wait for march queue to load
                    
                    # Step 4: Verify march queue opened by looking for close_left
                    queue_screenshot = self._take_screenshot_for_navigation()
                    if not queue_screenshot:
                        self.log_message("❌ Failed to take screenshot after wilderness click")
                        return False
                    
                    try:
                        if self._find_template_in_screenshot(queue_screenshot, 'close_left'):
                            self.log_message("✅ March queue opened successfully - ready for OCR")
                            return True
                        else:
                            self.log_message("❌ March queue did not open - close_left not found")
                            return False
                            
                    finally:
                        self._cleanup_screenshot(queue_screenshot)
                    
                finally:
                    self._cleanup_screenshot(menu_screenshot)
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
            
        except Exception as e:
            self.log_message(f"❌ Error in template-based navigation: {e}")
            return False
    
    def _find_template_in_screenshot(self, screenshot_path: str, template_type: str) -> bool:
        """Check if template exists in screenshot (without clicking)"""
        try:
            template_list = self.navigation_templates.get(template_type, [])
            
            if not template_list:
                self.log_message(f"❌ No templates defined for {template_type}")
                return False
            
            for template_name in template_list:
                if self._template_exists_in_screenshot(screenshot_path, template_name, template_type):
                    self.log_message(f"🔍 Found {template_type} using template: {template_name}")
                    return True
            
            self.log_message(f"🔍 {template_type} not found in screenshot")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error finding {template_type}: {e}")
            return False
    
    def _template_exists_in_screenshot(self, screenshot_path: str, template_name: str, template_type: str) -> bool:
        """Check if specific template exists in screenshot"""
        try:
            # Check if OpenCV is available
            try:
                import cv2
                import numpy as np
            except ImportError:
                self.log_message("❌ OpenCV not available - cannot use template detection")
                return False
            
            # Check if template file exists
            template_path = os.path.join("templates", template_name)
            if not os.path.exists(template_path):
                self.log_message(f"⚠️ Template not found: {template_name}")
                return False
            
            # Load screenshot and template
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                return False
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            # Use appropriate confidence threshold
            confidence_threshold = self.confidence_thresholds.get(template_type, 0.6)
            
            if max_val >= confidence_threshold:
                self.log_message(f"✅ Template match: {template_name} confidence: {max_val:.3f}")
                return True
            else:
                self.log_message(f"🔍 {template_name} confidence too low: {max_val:.3f} < {confidence_threshold}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error checking template {template_name}: {e}")
            return False
    
    def _click_template_from_list(self, screenshot_path: str, template_type: str) -> bool:
        """Click button using template detection from list of possible templates"""
        try:
            template_list = self.navigation_templates.get(template_type, [])
            
            if not template_list:
                self.log_message(f"❌ No templates defined for {template_type}")
                return False
            
            self.log_message(f"🔍 Looking for {template_type} using {len(template_list)} templates...")
            
            for template_name in template_list:
                if self._click_template_if_found(screenshot_path, template_name, template_type):
                    self.log_message(f"✅ Successfully clicked {template_type} using template: {template_name}")
                    return True
            
            # List which templates we tried
            self.log_message(f"❌ Could not find {template_type} with any of these templates: {', '.join(template_list)}")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error clicking {template_type} with templates: {e}")
            return False
    
    def _click_template_if_found(self, screenshot_path: str, template_name: str, template_type: str) -> bool:
        """Click template if found in screenshot"""
        try:
            # Check if OpenCV is available
            try:
                import cv2
                import numpy as np
            except ImportError:
                self.log_message("❌ OpenCV not available - cannot use template detection")
                return False
            
            # Check if template file exists
            template_path = os.path.join("templates", template_name)
            if not os.path.exists(template_path):
                self.log_message(f"⚠️ Template not found: {template_name}")
                return False
            
            # Load screenshot and template
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None:
                self.log_message(f"❌ Could not load screenshot: {screenshot_path}")
                return False
            
            if template is None:
                self.log_message(f"❌ Could not load template: {template_name}")
                return False
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            # Use appropriate confidence threshold
            confidence_threshold = self.confidence_thresholds.get(template_type, 0.6)
            
            if max_val >= confidence_threshold:
                # Calculate click position
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                self.log_message(f"🎯 Found {template_name} at ({click_x}, {click_y}) confidence: {max_val:.3f}")
                
                # Click the position
                return self._click_position(click_x, click_y)
            else:
                self.log_message(f"🔍 {template_name} not found (confidence: {max_val:.3f} < {confidence_threshold})")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error with template {template_name}: {e}")
            return False
    
    def _take_screenshot_for_navigation(self) -> Optional[str]:
        """Take screenshot for navigation template matching"""
        try:
            if not self.instance_index:
                return None
            
            import tempfile
            temp_dir = tempfile.gettempdir()
            screenshot_path = os.path.join(temp_dir, f"autogather_nav_{self.instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/autogather_nav.png"
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            # Take screenshot
            capture_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "shell", "screencap", "-p", device_screenshot]
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            
            if capture_result.returncode != 0:
                self.log_message(f"❌ Navigation screenshot capture failed: {capture_result.stderr}")
                return None
            
            time.sleep(0.5)
            
            # Pull screenshot
            pull_cmd = [memuc_path, "adb", "-i", str(self.instance_index), "pull", device_screenshot, screenshot_path]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            
            if pull_result.returncode != 0:
                self.log_message(f"❌ Navigation screenshot pull failed: {pull_result.stderr}")
                return None
            
            # Cleanup device
            subprocess.run([memuc_path, "adb", "-i", str(self.instance_index), "shell", "rm", device_screenshot], 
                          capture_output=True, timeout=5)
            
            if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 10000:
                return screenshot_path
            else:
                self.log_message(f"❌ Invalid navigation screenshot")
                return None
            
        except Exception as e:
            self.log_message(f"❌ Navigation screenshot error: {e}")
            return None
    
    def _cleanup_screenshot(self, screenshot_path: str):
        """Cleanup screenshot file"""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except:
            pass
    
    def _click_position(self, x: int, y: int) -> bool:
        """Click at specific coordinates"""
        try:
            if not self.instance_index:
                return False
            
            memuc_path = self.shared_resources.MEMUC_PATH
            
            tap_cmd = [
                memuc_path, "adb", "-i", str(self.instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
            
        except Exception as e:
            self.log_message(f"❌ Error clicking position: {e}")
            return False
    
    def _compare_queue_states(self, before: Dict, after: Dict):
        """Compare queue states before and after navigation"""
        try:
            before_queues = set(before.get("available_queues", []))
            after_queues = set(after.get("available_queues", []))
            
            newly_busy = before_queues - after_queues
            newly_available = after_queues - before_queues
            
            if newly_busy:
                self.log_message(f"✅ Started gathering - queues now busy: {list(newly_busy)}")
            
            if newly_available:
                self.log_message(f"ℹ️ Queues became available: {list(newly_available)}")
            
            if not newly_busy and not newly_available:
                self.log_message("⚠️ No queue state changes detected")
                
        except Exception as e:
            self.log_message(f"❌ Error comparing queue states: {e}")
    
    def get_status(self) -> Dict:
        """Get module status"""
        model_info = self.queue_analyzer.get_model_info() if self.queue_analyzer else {"model_loaded": False}
        
        return {
            "running": self.is_running,
            "instance_name": self.instance_name,
            "game_accessible": self._is_game_accessible(),
            "worker_active": self.worker_thread and self.worker_thread.is_alive() if self.worker_thread else False,
            "available_queues": self.available_queues,
            "last_analysis": self.last_queue_analysis,
            "cycle_delay": self.cycle_delay,
            "ocr_method": self.ocr_method,
            "local_model_loaded": model_info.get("model_loaded", False),
            "device": model_info.get("device", "unknown"),
            "cuda_available": model_info.get("cuda_available", False)
        }