"""
BENSON v2.0 - AutoGather Module with March Queue Analysis
Integrates OCR-based march queue reading and analysis
"""

import os
import time
import re
from typing import List, Dict
from datetime import datetime, timedelta
import numpy as np

# Import base module system
from modules.base_module import BaseModule, ModulePriority

# Safe imports
try:
    import cv2
    import easyocr
    CV2_AVAILABLE = True
    OCR_AVAILABLE = True
except ImportError as e:
    CV2_AVAILABLE = False
    OCR_AVAILABLE = False
    print(f"Warning: CV2 or EasyOCR not available: {e}")


class QueueInfo:
    """Information about a single march queue"""
    def __init__(self, queue_num: int, task_type: str = "", status: str = "", time_remaining: str = ""):
        self.queue_num = queue_num
        self.task_type = task_type  # "Gathering Lv. Idle Mill", "Gathering Lv. Idle Lumberyard", etc.
        self.status = status        # "Unlock", "Cannot use", etc.
        self.time_remaining = time_remaining  # "00:43:30", "Idle", etc.
        
    def is_available(self) -> bool:
        """Check if queue is available for use"""
        # For queues 1-2: Available if timer shows "Idle" 
        if self.queue_num <= 2:
            return "idle" in self.time_remaining.lower()
        
        # For queues 3-6: Available if status is NOT "Unlock" (Unlock means locked/unavailable)
        # Should be empty/available status, not "Unlock" or "Cannot use"
        else:
            return self.status.lower() not in ["unlock", "cannot use"]
    
    def is_busy(self) -> bool:
        """Check if queue is currently running a task"""
        # For queues 1-2: Busy if timer shows time remaining (XX:XX:XX format)
        if self.queue_num <= 2:
            return re.search(r'\d{1,2}:\d{2}:\d{2}', self.time_remaining) is not None
        
        # For queues 3-6: Not applicable (they're either available or locked)
        else:
            return False
    
    def is_gathering(self) -> bool:
        """Check if queue is actively gathering"""
        return "gathering" in self.task_type.lower() and self.is_busy()
        
    def __str__(self):
        availability = "AVAILABLE" if self.is_available() else "BUSY" if self.is_busy() else "UNUSABLE"
        return f"Queue {self.queue_num}: {self.task_type} | {self.status} | {self.time_remaining} | {availability}"


class AutoGatherModule(BaseModule):
    """AutoGather module with integrated march queue analysis"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        super().__init__(instance_name, shared_resources, console_callback)
        
        # Module configuration
        self.module_name = "AutoGather"
        self.check_interval = 30  # Check every 30 seconds
        self.max_retries = 3
        
        # Template configuration
        self.templates_dir = "templates/gather"
        self.confidence_threshold = 0.7
        
        # Templates we need
        self.MARCH_TEMPLATES = {
            "open_left": ["open_left.png"],
            "wilderness_button": ["wilderness_button.png", "wilderness.png", "wild_btn.png"]
        }
        
        # OCR Configuration
        self.ocr_reader = None
        self._initialize_ocr()
        
        # March queue regions (coordinates for OCR analysis)
        self.queue_regions = {
            1: {
                "task": (74, 215, 176, 19),
                "timer": (121, 235, 71, 19)
            },
            2: {
                "task": (68, 260, 175, 19),
                "timer": (118, 280, 75, 18)
            },
            3: {
                "name": (68, 303, 176, 21),
                "status": (118, 324, 75, 19)
            },
            4: {
                "name": (68, 350, 175, 22),
                "status": (115, 371, 82, 22)
            },
            5: {
                "name": (65, 396, 185, 21),
                "status": (114, 419, 85, 20)
            },
            6: {
                "name": (63, 441, 195, 21),
                "status": (111, 464, 88, 21)
            }
        }
        
        # State tracking
        self.last_march_check = None
        self.current_queues = []
        self.available_queues = []
        self.busy_queues = []
        
        # Statistics
        self.total_checks = 0
        self.successful_reads = 0
        
        # Create templates directory
        os.makedirs(self.templates_dir, exist_ok=True)
        
        self.log_message(f"✅ AutoGather (Queue Analyzer) module initialized for {instance_name}")
    
    def _initialize_ocr(self):
        """Initialize OCR reader"""
        try:
            if OCR_AVAILABLE:
                self.ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                self.log_message("✅ OCR reader initialized")
            else:
                self.log_message("❌ OCR not available - text analysis disabled")
        except Exception as e:
            self.log_message(f"❌ Failed to initialize OCR: {e}")
            self.ocr_reader = None
    
    def get_module_priority(self) -> ModulePriority:
        """AutoGather has high priority for resource management"""
        return ModulePriority.HIGH
    
    def get_dependencies(self) -> List[str]:
        """AutoGather depends on AutoStartGame"""
        return ["AutoStartGame"]
    
    def is_available(self) -> bool:
        """Check if module dependencies are available"""
        if not CV2_AVAILABLE:
            return False
        
        # Check if AutoStartGame has marked the game as accessible
        if hasattr(self.shared_resources, 'shared_state') and self.shared_resources.shared_state:
            # Check for instance-specific game accessibility
            game_accessible_key = f"game_accessible_{self.instance_name}"
            game_accessible = self.shared_resources.shared_state.get(game_accessible_key, False)
            
            if game_accessible:
                self.log_message("✅ Game accessibility confirmed via shared state")
                return True
            else:
                # Also check generic game_accessible key for compatibility
                generic_accessible = self.shared_resources.shared_state.get("game_accessible", False)
                if generic_accessible:
                    self.log_message("✅ Game accessibility confirmed via generic state")
                    return True
        
        # Fallback: Check if instance is running
        try:
            instance = self.shared_resources.get_instance(self.instance_name)
            if instance and instance["status"] == "Running":
                # Additional check: if AutoStart module exists and has completed
                if hasattr(self.shared_resources, 'shared_state'):
                    autostart_completed_key = f"autostart_completed_{self.instance_name}"
                    if self.shared_resources.shared_state.get(autostart_completed_key, False):
                        self.log_message("✅ Game accessibility confirmed via AutoStart completion")
                        return True
                
                # Final fallback: assume accessible if running for more than 2 minutes
                self.log_message("⚠️ Game accessibility not confirmed, but instance is running - proceeding")
                return True
            else:
                self.log_message(f"❌ Instance {self.instance_name} not running - cannot read march queue")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error checking instance status: {e}")
            return False
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies"""
        missing = []
        
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        
        if not OCR_AVAILABLE:
            missing.append("easyocr")
        
        # Check if game is accessible
        if not self._is_game_accessible():
            missing.append("game_must_be_accessible")
        
        return missing
    
    def _is_game_accessible(self) -> bool:
        """Helper method to check game accessibility"""
        if hasattr(self.shared_resources, 'shared_state') and self.shared_resources.shared_state:
            # Check instance-specific accessibility
            game_accessible_key = f"game_accessible_{self.instance_name}"
            if self.shared_resources.shared_state.get(game_accessible_key, False):
                return True
            
            # Check generic accessibility
            if self.shared_resources.shared_state.get("game_accessible", False):
                return True
            
            # Check AutoStart completion
            autostart_completed_key = f"autostart_completed_{self.instance_name}"
            if self.shared_resources.shared_state.get(autostart_completed_key, False):
                return True
        
        # Fallback: check if instance is running
        try:
            instance = self.shared_resources.get_instance(self.instance_name)
            return instance and instance["status"] == "Running"
        except:
            return False
    
    def execute_cycle(self) -> bool:
        """Execute one cycle of march queue reading and analysis"""
        try:
            # Check if game is still accessible
            if not self.is_available():
                # Only log this every 10 cycles to reduce spam
                if not hasattr(self, '_availability_log_count'):
                    self._availability_log_count = 0
                
                self._availability_log_count += 1
                if self._availability_log_count >= 10:
                    self.log_message("Game not accessible, skipping march queue reading")
                    self._availability_log_count = 0
                
                return False
            
            # REDUCED LOGGING: Only log significant actions
            if not hasattr(self, '_cycle_count'):
                self._cycle_count = 0
            
            self._cycle_count += 1
            self.total_checks += 1
            
            # Log every 5th cycle instead of every cycle
            if self._cycle_count == 1 or self._cycle_count % 5 == 0:
                self.log_message(f"📋 March Queue analysis #{self._cycle_count} - Reading and analyzing...")
            
            # Read and analyze march queue
            success = self._read_and_analyze_march_queue()
            
            if success:
                self.successful_reads += 1
                if self._cycle_count % 5 == 0:  # Only log occasionally
                    available_count = len(self.available_queues)
                    busy_count = len(self.busy_queues)
                    self.log_message(f"✅ Queue analysis complete: {available_count} available, {busy_count} busy")
            
            self.last_march_check = datetime.now()
            return success
            
        except Exception as e:
            self.log_message(f"March queue analysis error: {e}", "error")
            return False
    
    def _read_and_analyze_march_queue(self) -> bool:
        """Read march queue by navigating to it, then analyze with OCR"""
        try:
            # Step 1: Navigate to march queue
            if not self._navigate_to_march_queue():
                return False
            
            # Step 2: Take screenshot for analysis
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                self.log_message("❌ Failed to take screenshot for analysis")
                return False
            
            try:
                # Step 3: Analyze the march queue
                queues = self._analyze_march_queues(screenshot_path)
                
                if queues:
                    self._process_queue_analysis(queues)
                    return True
                else:
                    self.log_message("❌ Failed to analyze any queues")
                    return False
                    
            finally:
                # Clean up screenshot
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                    
        except Exception as e:
            self.log_message(f"Error in march queue analysis: {e}", "error")
            return False
    
    def _navigate_to_march_queue(self) -> bool:
        """Navigate to march queue by clicking open_left then wilderness_button"""
        try:
            # Step 1: Click open_left
            if not self._click_open_left():
                self.log_message("❌ Failed to click open_left")
                return False
            
            # Wait for UI to open
            time.sleep(2)
            
            # Step 2: Click wilderness_button
            if not self._click_wilderness_button():
                self.log_message("❌ Failed to click wilderness_button")
                return False
            
            # Wait for march queue to load
            time.sleep(3)  # Give extra time for queue to fully load
            
            return True
            
        except Exception as e:
            self.log_message(f"Error navigating to march queue: {e}", "error")
            return False
    
    def _click_open_left(self) -> bool:
        """Click the open_left button"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for open_left template
                for template in self.MARCH_TEMPLATES["open_left"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Clicked open_left button")
                        return True
                
                # Fallback: try common positions for left menu button
                left_positions = [(50, 300), (30, 250), (40, 350), (60, 280)]
                for x, y in left_positions:
                    self.click_position(x, y)
                    time.sleep(0.5)
                
                self.log_message("⚠️ Used fallback positions for open_left")
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error clicking open_left: {e}", "error")
            return False
    
    def _click_wilderness_button(self) -> bool:
        """Click the wilderness_button"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for wilderness_button template
                for template in self.MARCH_TEMPLATES["wilderness_button"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Clicked wilderness_button")
                        return True
                
                # Fallback: try common positions for wilderness button
                wilderness_positions = [(100, 200), (150, 180), (120, 220), (80, 200)]
                for x, y in wilderness_positions:
                    self.click_position(x, y)
                    time.sleep(0.5)
                
                self.log_message("⚠️ Used fallback positions for wilderness_button")
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error clicking wilderness_button: {e}", "error")
            return False
    
    def _analyze_march_queues(self, image_path: str) -> List[QueueInfo]:
        """Analyze march queues using OCR"""
        if not self.ocr_reader:
            self.log_message("❌ OCR reader not available")
            return []
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                self.log_message("❌ Failed to load screenshot for analysis")
                return []
            
            queues = []
            
            for queue_num, queue_regions in self.queue_regions.items():
                queue_info = QueueInfo(queue_num)
                
                for region_type, (x, y, w, h) in queue_regions.items():
                    # Extract region
                    region_image = image[y:y+h, x:x+w]
                    if region_image.size == 0:
                        continue
                    
                    # Extract text using OCR
                    region_name = f"Queue {queue_num} {region_type.title()}"
                    extracted_text = self._extract_text_from_region(region_image, region_name)
                    
                    # Store the extracted information
                    if region_type == "task":
                        queue_info.task_type = extracted_text
                    elif region_type == "timer":
                        queue_info.time_remaining = extracted_text
                    elif region_type == "name":
                        queue_info.task_type = extracted_text  # For queues 3-6, name contains task info
                    elif region_type == "status":
                        queue_info.status = extracted_text
                
                # Determine status for queues 1-2 based on timer
                if queue_num <= 2:
                    if queue_info.time_remaining:
                        if "idle" in queue_info.time_remaining.lower():
                            queue_info.status = "Available (Idle)"
                        elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                            queue_info.status = "Busy (Gathering)"
                        else:
                            queue_info.status = "Unknown"
                    else:
                        queue_info.status = "Unknown"
                else:
                    # For queues 3-6, status comes from the status region
                    if not queue_info.status:
                        queue_info.status = "Available"  # Empty status means available
                
                queues.append(queue_info)
            
            return queues
            
        except Exception as e:
            self.log_message(f"Error analyzing march queues: {e}", "error")
            return []
    
    def _extract_text_from_region(self, image_region, region_name: str) -> str:
        """Extract and clean text using OCR with appropriate preprocessing"""
        try:
            # Get the best preprocessing method for this region type
            processed = self._preprocess_for_ocr(image_region, region_name)
            
            # Run OCR
            results = self.ocr_reader.readtext(processed, detail=True, paragraph=False)
            
            # Extract and clean text
            texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.1:  # Only use confident results
                    cleaned_text = self._clean_text_for_type(text, self._get_text_type(region_name))
                    if cleaned_text:
                        texts.append(cleaned_text)
            
            # Combine all text pieces
            combined_text = " ".join(texts)
            
            # Final cleaning pass
            combined_text = self._clean_text_for_type(combined_text, self._get_text_type(region_name))
            
            return combined_text
            
        except Exception as e:
            self.log_message(f"Error processing {region_name}: {str(e)}")
            return ""
    
    def _preprocess_for_ocr(self, image, region_name: str):
        """Preprocess image for better OCR results"""
        region_lower = region_name.lower()
        
        if 'timer' in region_lower:
            # Enhanced timer method for better seconds recognition
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Strong contrast for better digit recognition
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(2,2))
            enhanced = clahe.apply(gray)
            
            # 4x upscale for tiny timer digits
            upscaled = cv2.resize(enhanced, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)
            
            # Strong sharpening for digit clarity
            kernel = np.array([[0, -2, 0], [-2, 9, -2], [0, -2, 0]])
            sharpened = cv2.filter2D(upscaled, -1, kernel)
            
            # Light denoising to clean up artifacts
            denoised = cv2.fastNlMeansDenoising(sharpened, None, 2, 7, 21)
            return denoised
            
        elif 'task' in region_lower or 'name' in region_lower:
            # 3x Lanczos scaling for tasks
            return cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
        else:
            # Default: 2x cubic scaling
            return cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    def _get_text_type(self, region_name: str) -> str:
        """Determine text type for cleaning"""
        region_lower = region_name.lower()
        
        if 'timer' in region_lower:
            return "timer"
        elif 'task' in region_lower or 'name' in region_lower:
            return "task"
        elif 'status' in region_lower:
            return "status"
        else:
            return "general"
    
    def _clean_text_for_type(self, text: str, text_type: str) -> str:
        """Clean text based on what type it is"""
        if text_type == "timer":
            # Timer-specific cleaning
            fixes = {
                'O': '0', 'o': '0', 'l': '1', 'I': '1', '|': '1', 'j': ':', 'i': '1',
                'S': '5', 's': '5', 'Z': '2', 'z': '2', 'G': '6', 'g': '9',
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
            
            # Pattern fixes - convert dots to colons
            text = re.sub(r'(\d{2})\.(\d{2})\.(\d{2})', r'\1:\2:\3', text)  # 00.43.30 -> 00:43:30
            text = re.sub(r'(\d{2})\.(\d{2})\.(\d{1})', r'\1:\2:0\3', text)  # 00.43.3 -> 00:43:03
            
        elif text_type == "task":
            # Task-specific cleaning
            fixes = {
                '31d1e': 'Idle', '3ldle': 'Idle', 'B1d1e': 'Idle', 'Bldlc': 'Idle',
                '3idle': 'Idle', 'bidle': 'Idle', 'ldle': 'Idle', 'idle': 'Idle',
                'Milll': 'Mill', 'Mi11': 'Mill', 'MiII': 'Mill', 'MilI': 'Mill',
                'Gathcring': 'Gathering', 'Gathenng': 'Gathering', 'Gatherng': 'Gathering',
                'Lumbcryard': 'Lumberyard', 'Lumberyd': 'Lumberyard',
                'Lv ': 'Lv. ', 'Ly': 'Lv.', 'LV': 'Lv.'
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
            
            # Add period to Lv
            text = re.sub(r'\bLv\b(?!\.)', 'Lv.', text)
            
        elif text_type == "status":
            # Status-specific cleaning
            fixes = {
                'Un10ck': 'Unlock', 'UnI0ck': 'Unlock', 'unl0ck': 'Unlock', 'Unl0ck': 'Unlock',
                'Cannol': 'Cannot', 'Cann0t': 'Cannot', 'Canot': 'Cannot', 'Can not': 'Cannot',
                'usc': 'use', 'u5c': 'use', 'u5e': 'use', 'uSc': 'use', 'u5C': 'use',
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
        
        # Clean up spacing
        text = ' '.join(text.split())
        text = text.replace(' .', '.').replace('. ', '.')
        text = text.replace(' :', ':').replace(': ', ':')
        
        return text.strip()
    
    def _process_queue_analysis(self, queues: List[QueueInfo]):
        """Process the analyzed queue information"""
        try:
            self.current_queues = queues
            self.available_queues = [q for q in queues if q.is_available()]
            self.busy_queues = [q for q in queues if q.is_busy()]
            
            # Log detailed results every 10th cycle
            if hasattr(self, '_cycle_count') and self._cycle_count % 10 == 0:
                self.log_message("📊 Detailed Queue Analysis:")
                
                for queue in queues:
                    if queue.is_available():
                        self.log_message(f"   ✅ Queue {queue.queue_num}: Available")
                    elif queue.is_busy():
                        self.log_message(f"   ⏰ Queue {queue.queue_num}: Busy ({queue.time_remaining})")
                    else:
                        self.log_message(f"   ❌ Queue {queue.queue_num}: Locked")
                
                if self.available_queues:
                    available_nums = [str(q.queue_num) for q in self.available_queues]
                    self.log_message(f"🎯 Can start marches in queues: {', '.join(available_nums)}")
                else:
                    self.log_message("⏳ No queues available for new marches")
            
        except Exception as e:
            self.log_message(f"Error processing queue analysis: {e}", "error")
    
    def _click_template(self, screenshot_path: str, template_name: str) -> bool:
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
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                template_h, template_w = template.shape[:2]
                click_x = max_loc[0] + template_w // 2
                click_y = max_loc[1] + template_h // 2
                
                return self.click_position(click_x, click_y)
            
            return False
            
        except Exception as e:
            self.log_message(f"Error clicking template {template_name}: {e}", "error")
            return False
    
    def get_march_status(self) -> Dict:
        """Get detailed march queue status"""
        return {
            "module_status": self.status.value,
            "last_check": self.last_march_check.isoformat() if self.last_march_check else None,
            "total_checks": self.total_checks,
            "successful_reads": self.successful_reads,
            "success_rate": (self.successful_reads / max(1, self.total_checks)) * 100,
            "available_queues": len(self.available_queues),
            "busy_queues": len(self.busy_queues),
            "total_queues": len(self.current_queues),
            "queue_details": [
                {
                    "queue_num": q.queue_num,
                    "task_type": q.task_type,
                    "status": q.status,
                    "time_remaining": q.time_remaining,
                    "available": q.is_available(),
                    "busy": q.is_busy(),
                    "gathering": q.is_gathering()
                }
                for q in self.current_queues
            ],
            "game_accessible": self._is_game_accessible(),
            "ocr_available": self.ocr_reader is not None
        }
    
    def force_march_check(self) -> bool:
        """Force an immediate march queue check (manual trigger)"""
        self.log_message("🎯 Force checking march queue (manual trigger)")
        return self.execute_cycle()
    
    def get_available_queue_count(self) -> int:
        """Get number of available queues"""
        return len(self.available_queues)
    
    def get_busy_queue_count(self) -> int:
        """Get number of busy queues"""
        return len(self.busy_queues)
    
    def can_start_new_march(self) -> bool:
        """Check if any queue is available for a new march"""
        return len(self.available_queues) > 0