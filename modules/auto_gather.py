import cv2
import numpy as np
import time
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import easyocr
from .base_module import BaseModule


@dataclass
class AutoGatherConfig:
    """Configuration for AutoGather module"""
    cycle_interval: int = 18  # seconds between cycles
    template_matching_threshold: float = 0.7
    ocr_confidence_threshold: float = 0.5
    max_retries: int = 3
    navigation_timeout: int = 10


@dataclass 
class QueueInfo:
    """Information about a march queue"""
    name: str = ""
    task: str = ""
    status: str = ""
    time_remaining: str = ""
    is_available: bool = False


class AutoGatherModule(BaseModule):
    """
    Simplified AutoGather module using template matching for navigation
    and OCR for reading march queue information
    """
    
    def __init__(self, instance_name: str, shared_resources=None, log_callback=None, console_callback=None):
        super().__init__(instance_name, log_callback, console_callback)
        self.shared_resources = shared_resources
        self.config = AutoGatherConfig()
        self.ocr_reader = None
        self.is_running = False
        self.queues: Dict[int, QueueInfo] = {}
        
        # Template matching regions
        self.templates = {
            'open_left': 'templates/open_left.png',
            'wilderness_button': 'templates/wilderness_button.png'
        }
        
        # OCR regions for march queues (x, y, width, height)
        self.queue_regions = {
            # Queues 1-2: Have task name and timer
            1: {
                'task': (50, 180, 200, 25),    # Queue 1 task area
                'timer': (50, 205, 200, 25)    # Queue 1 timer area
            },
            2: {
                'task': (50, 230, 200, 25),    # Queue 2 task area  
                'timer': (50, 255, 200, 25)    # Queue 2 timer area
            },
            # Queues 3-6: Have name and status
            3: {
                'name': (50, 280, 200, 25),    # Queue 3 name area
                'status': (250, 280, 150, 25)   # Queue 3 status area
            },
            4: {
                'name': (50, 305, 200, 25),    # Queue 4 name area
                'status': (250, 305, 150, 25)   # Queue 4 status area
            },
            5: {
                'name': (50, 330, 200, 25),    # Queue 5 name area
                'status': (250, 330, 150, 25)   # Queue 5 status area
            },
            6: {
                'name': (50, 355, 200, 25),    # Queue 6 name area
                'status': (250, 355, 150, 25)   # Queue 6 status area
            }
        }
        
        # THIS IS THE NEW UPDATED CODE VERSION - 2024 CLAUDE FIX
        self.log("🚨 USING NEW CLAUDE-FIXED AUTOGATHER CODE VERSION 2024 🚨")
        
        # Initialize logging from parent class
        if hasattr(self, 'log'):
            self.log("✅ AutoGather (Simplified Template Matching) module initialized for " + instance_name)
        elif console_callback:
            console_callback(f"✅ AutoGather (Simplified Template Matching) module initialized for {instance_name}")
        else:
            print(f"✅ AutoGather (Simplified Template Matching) module initialized for {instance_name}")
    
    def log(self, message: str):
        """Logging method with fallback options"""
        # Try parent class log method first
        if hasattr(super(), 'log'):
            try:
                super().log(message)
                return
            except:
                pass
        
        # Try console callback
        if hasattr(self, 'console_callback') and self.console_callback:
            try:
                self.console_callback(f"[AutoGather-{self.instance_name}] {message}")
                return
            except:
                pass
        
        # Try log callback
        if hasattr(self, 'log_callback') and self.log_callback:
            try:
                self.log_callback(f"[AutoGather-{self.instance_name}] {message}")
                return
            except:
                pass
        
        # Fallback to print
        print(f"[AutoGather-{self.instance_name}] {message}")
    
    def initialize(self):
        """Initialize the OCR reader"""
        try:
            self.ocr_reader = easyocr.Reader(['en'], gpu=False)
            self.log("✅ OCR reader initialized")
            return True
        except Exception as e:
            self.log(f"❌ Failed to initialize OCR reader: {e}")
            return False
    
    def start(self):
        """Start the AutoGather module"""
        if not self.ocr_reader:
            if not self.initialize():
                self.log("❌ Failed to initialize AutoGather module")
                return False
        
        self.is_running = True
        self.log("🚀 Starting AutoGather module...")
        
        # Start the worker loop
        import threading
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.log("🔄 AutoGather worker loop started")
        
        self.log("✅ AutoGather started successfully")
        return True
    
    def stop(self):
        """Stop the AutoGather module"""
        self.is_running = False
        self.log("🛑 AutoGather stopped")
    
    def _worker_loop(self):
        """Main worker loop for AutoGather"""
        cycle_count = 0
        retry_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                start_time = time.time()
                
                self.log(f"📋 March Queue analysis #{cycle_count} - Reading and analyzing...")
                
                # Navigate to march queue and analyze
                success = self._navigate_to_march_queue()
                if success:
                    self._analyze_march_queues()
                    retry_count = 0  # Reset retry count on success
                else:
                    retry_count += 1
                    if retry_count >= self.config.max_retries:
                        self.log(f"❌ AutoGather failed {self.config.max_retries} times, stopping...")
                        break
                    else:
                        self.log(f"❌ AutoGather cycle {cycle_count} failed (retry {retry_count}/{self.config.max_retries})")
                
                elapsed_time = time.time() - start_time
                self.log(f"✅ AutoGather cycle {cycle_count} completed (took {elapsed_time:.1f}s)")
                
                # Wait for next cycle
                if self.is_running:
                    time.sleep(self.config.cycle_interval)
                
            except Exception as e:
                self.log(f"❌ Error in AutoGather worker loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _navigate_to_march_queue(self) -> bool:
        """Navigate to the march queue screen using template matching"""
        try:
            # Step 1: Click open left panel button
            if not self._click_template('open_left'):
                self.log("❌ Failed to click open_left.png")
                return False
            
            # Wait for panel to open
            time.sleep(2)
            
            # Step 2: Click wilderness button  
            if not self._click_template('wilderness_button'):
                self.log("❌ Failed to click wilderness_button.png")
                return False
            
            # Wait for march queue to load
            time.sleep(3)
            
            self.log("✅ Successfully navigated to march queue")
            return True
            
        except Exception as e:
            self.log(f"❌ Navigation error: {e}")
            return False
    
    def _click_template(self, template_name: str) -> bool:
        """Click on a template using OpenCV template matching"""
        try:
            template_path = self.templates.get(template_name)
            if not template_path:
                self.log(f"❌ Template {template_name} not found in templates")
                return False
            
            # Check if template file exists
            if not os.path.exists(template_path):
                self.log(f"❌ Template file not found: {template_path}")
                return False
            
            self.log(f"✅ Found template at: {template_path}")
            
            # Take screenshot
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            # Load template and screenshot
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
            
            if template is None:
                self.log(f"❌ Failed to load template: {template_path}")
                return False
            
            if screenshot is None:
                self.log(f"❌ Failed to load screenshot: {screenshot_path}")
                return False
            
            # Get template dimensions
            template_height, template_width = template.shape[:2]
            self.log(f"📏 Template dimensions: {template_width}x{template_height}")
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            self.log(f"🔍 Template matching confidence: {max_val:.3f} (threshold: {self.config.template_matching_threshold})")
            
            # Check if match is good enough
            if max_val >= self.config.template_matching_threshold:
                # Calculate click position (center of template)
                click_x = max_loc[0] + template_width // 2
                click_y = max_loc[1] + template_height // 2
                
                self.log(f"✅ Template found! Top-left: {max_loc}, Center: ({click_x}, {click_y})")
                
                # Click at the center of the found template
                self.log(f"🎯 Found {template_name}.png at center position ({click_x}, {click_y})")
                success = self._click_position(click_x, click_y)
                
                if success:
                    self.log(f"✅ Successfully clicked {template_name}.png at ({click_x}, {click_y})")
                    return True
                else:
                    self.log(f"❌ Failed to click {template_name}.png at ({click_x}, {click_y})")
                    return False
            else:
                self.log(f"❌ Template confidence {max_val:.3f} below threshold {self.config.template_matching_threshold}")
                self.log(f"❌ Template {template_name}.png not found in screenshot")
                return False
                
        except Exception as e:
            self.log(f"❌ Template matching error for {template_name}: {e}")
            return False
    
    def _take_screenshot(self) -> Optional[str]:
        """Take a screenshot and return the file path"""
        try:
            timestamp = int(time.time())
            screenshot_path = f"module_screenshot_1_{timestamp}.png"
            
            # Use MEmu screenshot command
            result = os.system(f'"{self.memu_path}" screenshot -i {self.instance_index} "{screenshot_path}"')
            
            if result == 0 and os.path.exists(screenshot_path):
                self.log(f"📸 Screenshot taken: {screenshot_path}")
                return screenshot_path
            else:
                self.log(f"❌ Screenshot failed or file not found: {screenshot_path}")
                return None
                
        except Exception as e:
            self.log(f"❌ Screenshot error: {e}")
            return None
    
    def _click_position(self, x: int, y: int) -> bool:
        """Click at the specified position"""
        try:
            # Use MEmu click command
            self.log(f"👆 Clicked position ({x}, {y})")
            result = os.system(f'"{self.memu_path}" click -i {self.instance_index} {x} {y}')
            return result == 0
        except Exception as e:
            self.log(f"❌ Click error: {e}")
            return False
    
    def _analyze_march_queues(self):
        """Analyze march queues using OCR"""
        try:
            # Take screenshot of march queue screen
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                self.log("❌ Failed to take screenshot for queue analysis")
                return
            
            self.log("🔍 Starting OCR analysis of march queues...")
            
            # Analyze each queue
            for queue_num in range(1, 7):  # Queues 1-6
                self._analyze_single_queue(queue_num, screenshot_path)
            
            self.log(f"✅ OCR analysis complete - found {len(self.queues)} queues")
            
            # TODO: Here we would determine which queues are available and start marches
            # For now, just log the results
            available_queues = [q for q in self.queues.values() if q.is_available]
            if available_queues:
                queue_numbers = [str(i) for i, q in self.queues.items() if q.is_available]
                self.log(f"🎯 Can start marches in queues: {', '.join(queue_numbers)}")
            else:
                self.log("⚠️ No available queues found for new marches")
                
        except Exception as e:
            self.log(f"❌ Queue analysis error: {e}")
    
    def _analyze_single_queue(self, queue_num: int, screenshot_path: str):
        """Analyze a single march queue"""
        try:
            self.log(f"📋 Analyzing Queue {queue_num}...")
            
            if queue_num not in self.queue_regions:
                self.log(f"❌ No regions defined for Queue {queue_num}")
                return
            
            queue_info = QueueInfo()
            regions = self.queue_regions[queue_num]
            
            # For queues 1-2: read task and timer
            if queue_num <= 2:
                if 'task' in regions:
                    queue_info.task = self._perform_ocr_on_region(
                        screenshot_path, regions['task'], f"Queue {queue_num} Task"
                    )
                
                if 'timer' in regions:
                    queue_info.time_remaining = self._perform_ocr_on_region(
                        screenshot_path, regions['timer'], f"Queue {queue_num} Timer"
                    )
            
            # For queues 3-6: read name and status
            else:
                if 'name' in regions:
                    queue_info.name = self._perform_ocr_on_region(
                        screenshot_path, regions['name'], f"Queue {queue_num} Name"
                    )
                
                if 'status' in regions:
                    queue_info.status = self._perform_ocr_on_region(
                        screenshot_path, regions['status'], f"Queue {queue_num} Status"
                    )
            
            # Determine availability
            queue_info.is_available = self._determine_queue_availability(queue_num, queue_info)
            
            # Store queue info
            self.queues[queue_num] = queue_info
            
            # Log results
            if queue_num <= 2:
                availability = "AVAILABLE" if queue_info.is_available else "UNUSABLE"
                self.log(f"📊 Queue {queue_num} Final: Queue {queue_num}: {queue_info.task} | {queue_info.status} | {queue_info.time_remaining} | {availability}")
            else:
                availability = "AVAILABLE" if queue_info.is_available else "UNUSABLE"
                self.log(f"📊 Queue {queue_num} Final: Queue {queue_num}: {queue_info.name} | {queue_info.status} |  | {availability}")
                
        except Exception as e:
            self.log(f"❌ Error analyzing Queue {queue_num}: {e}")
    
    def _perform_ocr_on_region(self, screenshot_path: str, region: tuple, text_type: str) -> str:
        """Perform OCR on a specific region of the screenshot"""
        try:
            # Load the screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                self.log(f"❌ Failed to load screenshot: {screenshot_path}")
                return ""
            
            # Extract the region
            x, y, w, h = region
            roi = screenshot[y:y+h, x:x+w]
            
            # SAVE OCR REGION for debugging
            region_filename = f"ocr_region_{text_type}_{int(time.time())}_{x}_{y}_{w}_{h}.png"
            region_path = os.path.join(os.path.dirname(screenshot_path), region_filename)
            cv2.imwrite(region_path, roi)
            self.log(f"💾 Saved OCR region: {region_filename}")
            self.log(f"📁 Full path: {region_path}")
            
            # Perform OCR
            results = self.ocr_reader.readtext(roi, detail=1)
            
            self.log(f"🔍 OCR raw results for {text_type}: {len(results)} detections")
            
            if not results:
                self.log(f"❌ No text detected in {text_type} region")
                return ""
            
            # Process and filter results
            processed_results = []
            for detection in results:
                bbox, text, confidence = detection
                
                # Log each detection
                self.log(f"   {len(processed_results) + 1}. '{text}' (confidence: {confidence:.3f})")
                
                # Filter by confidence
                if confidence >= self.config.ocr_confidence_threshold:
                    processed_results.append((text, confidence))
                else:
                    self.log(f"❌ Low confidence: '{text}' (conf: {confidence:.3f})")
            
            if not processed_results:
                self.log(f"❌ No text passed confidence threshold for {text_type}")
                return ""
            
            # Get the best result
            best_text, best_confidence = max(processed_results, key=lambda x: x[1])
            
            # Clean the text based on its type
            cleaned_text = self._clean_text_for_type(best_text, text_type)
            
            # Log the cleaning process
            if cleaned_text != best_text:
                self.log(f"✅ Accepted: '{best_text}' → '{cleaned_text}' (conf: {best_confidence:.3f})")
            else:
                self.log(f"✅ Accepted: '{best_text}' → '{cleaned_text}' (conf: {best_confidence:.3f})")
            
            return cleaned_text
            
        except Exception as e:
            self.log(f"❌ OCR error for {text_type}: {e}")
            return ""
    
    def _clean_text_for_type(self, text: str, text_type: str) -> str:
        """Clean text based on what type it is"""
        
        # CRITICAL FIX: Handle "Idle" FIRST before any other processing
        if text.lower() in ['idle', 'idlc', 'id1e', '1dle', 'id1c', 'idl3', '1d1e']:
            return 'Idle'  # Return clean "Idle" immediately
        
        if text_type == "timer":
            # Timer-specific cleaning - AFTER idle check
            fixes = {
                'O': '0', 'o': '0', 'l': '1', 'I': '1', '|': '1', 'j': ':', 'i': '1',
                'S': '5', 's': '5', 'Z': '2', 'z': '2', 'G': '6', 'g': '9',
            }
            
            # Apply character fixes to actual timer numbers only
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
                'Lv ': 'Lv. ', 'Ly': 'Lv.', 'LV': 'Lv.',
                'Qucuc': 'Queue'  # Fix "March Qucuc" -> "March Queue"
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
                'Idlc': 'Idle', 'Id1e': 'Idle', '1dle': 'Idle', 'id1c': 'Idle'  # Fix idle variations
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
        
        # Clean up spacing
        text = ' '.join(text.split())
        text = text.replace(' .', '.').replace('. ', '.')
        text = text.replace(' :', ':').replace(': ', ':')
        
        return text.strip()
    
    def _determine_queue_availability(self, queue_num: int, queue_info: QueueInfo) -> bool:
        """Determine if a queue is available for new marches"""
        try:
            # Determine status for queues 1-2 based on timer
            if queue_num <= 2:
                if queue_info.time_remaining:
                    # IMPROVED: Better idle detection
                    if any(idle_word in queue_info.time_remaining.lower() for idle_word in ['idle', 'idlc', 'id1e', '1dle', 'id1c']):
                        queue_info.status = "Available (Idle)"
                        return True
                    elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                        queue_info.status = "Busy (Gathering)"
                        return False
                    else:
                        queue_info.status = "Unknown"
                        return False
                else:
                    queue_info.status = "Unknown"
                    return False
            else:
                # For queues 3-6, status comes from the status region
                if not queue_info.status:
                    queue_info.status = "Available"
                    return True
                # IMPROVED: Better status detection
                elif any(idle_word in queue_info.status.lower() for idle_word in ['idle', 'idlc', 'available']):
                    queue_info.status = "Available"
                    return True
                elif any(busy_word in queue_info.status.lower() for busy_word in ['unlock', 'cannot', 'locked']):
                    return False
                else:
                    # Unknown status, assume not available for safety
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error determining availability for Queue {queue_num}: {e}")
            return False
    
    @property
    def memu_path(self) -> str:
        """Get MEmu executable path"""
        if self.shared_resources and hasattr(self.shared_resources, 'memu_path'):
            return self.shared_resources.memu_path
        return r"C:\Program Files\Microvirt\MEmu\memuc.exe"
    
    @property  
    def instance_index(self) -> int:
        """Get instance index for MEmu commands"""
        try:
            self.log(f"🔍 Getting instance index for {self.instance_name}")
            
            if self.shared_resources and hasattr(self.shared_resources, 'instances'):
                self.log(f"🔍 Found {len(self.shared_resources.instances)} instances")
                
                # Find the instance by name
                for i, instance in enumerate(self.shared_resources.instances):
                    try:
                        # Handle both object and dict instances
                        if hasattr(instance, 'name'):
                            inst_name = instance.name
                            inst_index = instance.index if hasattr(instance, 'index') else i + 1
                            self.log(f"🔍 Object instance {i}: name={inst_name}, index={inst_index}")
                        elif isinstance(instance, dict):
                            inst_name = instance.get('name', '')
                            inst_index = instance.get('index', i + 1)
                            self.log(f"🔍 Dict instance {i}: name={inst_name}, index={inst_index}")
                        else:
                            inst_name = str(instance)
                            inst_index = i + 1
                            self.log(f"🔍 Unknown instance {i}: {inst_name}, index={inst_index}")
                        
                        if inst_name == self.instance_name:
                            self.log(f"✅ Found matching instance: {inst_name} at index {inst_index}")
                            return inst_index
                            
                    except Exception as e:
                        self.log(f"⚠️ Error processing instance {i}: {str(e)}")
                        continue
                
                self.log(f"❌ Instance {self.instance_name} not found, using fallback index 1")
                return 1
            else:
                self.log("❌ No shared resources for instance index, using fallback 1")
                return 1
                
        except Exception as e:
            self.log(f"❌ Error in instance_index: {str(e)}")
            return 1