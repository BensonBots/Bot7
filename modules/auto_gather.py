"""
BENSON v2.0 - FIXED AutoGather Module with OCR Image Saving
Addresses multiple issues found in the logs and code
Added OCR image saving functionality for debugging and analysis
"""

import cv2
import numpy as np
import time
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import tempfile
import subprocess
from datetime import datetime


@dataclass
class AutoGatherConfig:
    """Configuration for AutoGather module"""
    cycle_interval: int = 18  # seconds between cycles
    template_matching_threshold: float = 0.7
    ocr_confidence_threshold: float = 0.5
    max_retries: int = 3
    navigation_timeout: int = 10
    save_ocr_images: bool = True  # NEW: Enable OCR image saving
    ocr_save_directory: str = "ocr_images"  # NEW: Directory for OCR images
    keep_ocr_images_days: int = 7  # NEW: Days to keep OCR images


@dataclass 
class QueueInfo:
    """Information about a march queue"""
    name: str = ""
    task: str = ""
    status: str = ""
    time_remaining: str = ""
    is_available: bool = False


class AutoGatherModule:
    """
    FIXED AutoGather module with proper error handling and debugging
    Enhanced with OCR image saving functionality
    """
    
    def __init__(self, instance_name: str, shared_resources=None, log_callback=None, console_callback=None):
        self.instance_name = instance_name
        self.shared_resources = shared_resources
        self.log_callback = log_callback
        self.console_callback = console_callback
        
        # FIXED: Configuration and state
        self.config = AutoGatherConfig()
        self.ocr_reader = None
        self.is_running = False
        self.queues: Dict[int, QueueInfo] = {}
        self.worker_thread = None
        
        # FIXED: Proper MEmu paths and instance tracking
        self.memu_path = self._get_memu_path()
        self.instance_index = self._get_instance_index()
        
        # FIXED: Template paths
        self.templates_dir = "templates"
        self.templates = {
            'open_left': os.path.join(self.templates_dir, 'open_left.png'),
            'wilderness_button': os.path.join(self.templates_dir, 'wilderness_button.png')
        }
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # NEW: OCR image saving setup
        self.ocr_save_dir = os.path.join(self.config.ocr_save_directory, self.instance_name)
        if self.config.save_ocr_images:
            os.makedirs(self.ocr_save_dir, exist_ok=True)
            self._cleanup_old_ocr_images()
        
        # FIXED: OCR regions with better coordinates
        self.queue_regions = {
            1: {
                'task': (50, 180, 200, 25),
                'timer': (50, 205, 200, 25)
            },
            2: {
                'task': (50, 230, 200, 25),
                'timer': (50, 255, 200, 25)
            },
            3: {
                'name': (50, 280, 200, 25),
                'status': (250, 280, 150, 25)
            },
            4: {
                'name': (50, 305, 200, 25),
                'status': (250, 305, 150, 25)
            },
            5: {
                'name': (50, 330, 200, 25),
                'status': (250, 330, 150, 25)
            },
            6: {
                'name': (50, 355, 200, 25),
                'status': (250, 355, 150, 25)
            }
        }
        
        self.log("✅ AutoGather module initialized with FIXED configuration and OCR image saving")
    
    def _cleanup_old_ocr_images(self):
        """NEW: Clean up old OCR images based on configured retention period"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return
            
            cutoff_time = time.time() - (self.config.keep_ocr_images_days * 24 * 60 * 60)
            cleaned_count = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        try:
                            os.remove(filepath)
                            cleaned_count += 1
                        except Exception as e:
                            self.log(f"⚠️ Could not remove old OCR image {filename}: {e}")
            
            if cleaned_count > 0:
                self.log(f"🧹 Cleaned up {cleaned_count} old OCR images (older than {self.config.keep_ocr_images_days} days)")
                
        except Exception as e:
            self.log(f"⚠️ Error cleaning up old OCR images: {e}")
    
    def _get_memu_path(self) -> str:
        """FIXED: Get MEmu executable path"""
        try:
            if self.shared_resources and hasattr(self.shared_resources, 'MEMUC_PATH'):
                return self.shared_resources.MEMUC_PATH
            return r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        except Exception as e:
            self.log(f"⚠️ Error getting MEmu path: {e}")
            return r"C:\Program Files\Microvirt\MEmu\memuc.exe"
    
    def _get_instance_index(self) -> int:
        """FIXED: Get instance index with better error handling"""
        try:
            self.log(f"🔍 Getting instance index for {self.instance_name}")
            
            if not self.shared_resources:
                self.log("❌ No shared_resources available")
                return 1
            
            # Try to get instance by name
            if hasattr(self.shared_resources, 'get_instance'):
                instance = self.shared_resources.get_instance(self.instance_name)
                if instance:
                    index = instance.get('index', 1)
                    self.log(f"✅ Found instance index: {index}")
                    return index
            
            # Try direct access to instances list
            if hasattr(self.shared_resources, 'instances'):
                self.log(f"🔍 Found {len(self.shared_resources.instances)} instances")
                
                for i, instance in enumerate(self.shared_resources.instances):
                    try:
                        # Handle both dict and object instances
                        if isinstance(instance, dict):
                            inst_name = instance.get('name', '')
                            inst_index = instance.get('index', i + 1)
                        else:
                            inst_name = getattr(instance, 'name', '')
                            inst_index = getattr(instance, 'index', i + 1)
                        
                        self.log(f"🔍 Dict instance {i}: name={inst_name}, index={inst_index}")
                        
                        if inst_name == self.instance_name:
                            self.log(f"✅ Found matching instance: {inst_name} at index {inst_index}")
                            return inst_index
                            
                    except Exception as e:
                        self.log(f"⚠️ Error processing instance {i}: {e}")
                        continue
            
            self.log(f"❌ Instance {self.instance_name} not found, using fallback index 1")
            return 1
            
        except Exception as e:
            self.log(f"❌ Error getting instance index: {e}")
            return 1
    
    def log(self, message: str):
        """FIXED: Logging with multiple fallbacks"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [AutoGather-{self.instance_name}] {message}"
        
        # Print to console first (for debugging)
        print(formatted_message)
        
        # Try console callback
        if self.console_callback:
            try:
                self.console_callback(formatted_message)
            except Exception as e:
                print(f"[AutoGather] Console callback error: {e}")
        
        # Try log callback
        if self.log_callback:
            try:
                self.log_callback(formatted_message)
            except Exception as e:
                print(f"[AutoGather] Log callback error: {e}")
    
    def initialize(self):
        """FIXED: Initialize with better error handling"""
        try:
            # Try to initialize OCR with error handling
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                self.log("✅ OCR reader initialized successfully")
                return True
            except ImportError:
                self.log("❌ easyocr not installed - OCR functionality disabled")
                return False
            except Exception as e:
                self.log(f"❌ OCR initialization failed: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ AutoGather initialization failed: {e}")
            return False
    
    def start(self):
        """FIXED: Start the AutoGather module with proper thread management"""
        try:
            if self.is_running:
                self.log("⚠️ AutoGather already running")
                return True
            
            # Initialize if not done yet
            if not self.ocr_reader:
                if not self.initialize():
                    self.log("❌ Cannot start - initialization failed")
                    return False
            
            # Verify MEmu path exists
            if not os.path.exists(self.memu_path):
                self.log(f"❌ MEmu not found at: {self.memu_path}")
                return False
            
            # Verify instance index is valid
            if not self._verify_instance_exists():
                self.log(f"❌ Instance {self.instance_name} (index {self.instance_index}) not accessible")
                return False
            
            self.is_running = True
            self.log("🚀 Starting AutoGather module...")
            
            # Start worker thread with daemon=True for proper cleanup
            import threading
            self.worker_thread = threading.Thread(
                target=self._worker_loop, 
                daemon=True,
                name=f"AutoGather-{self.instance_name}"
            )
            self.worker_thread.start()
            
            self.log("🔄 AutoGather worker loop started")
            self.log("✅ AutoGather started successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start AutoGather: {e}")
            self.is_running = False
            return False
    
    def _verify_instance_exists(self) -> bool:
        """FIXED: Verify instance exists and is accessible"""
        try:
            # Quick test - try to get instance info
            cmd = [self.memu_path, "listvms"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.log(f"❌ MEmu listvms failed: {result.stderr}")
                return False
            
            # Parse output to find our instance
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            index = int(parts[0])
                            name = parts[1]
                            if index == self.instance_index or name == self.instance_name:
                                self.log(f"✅ Verified instance exists: {name} (index {index})")
                                return True
                        except ValueError:
                            continue
            
            self.log(f"❌ Instance not found in MEmu list")
            return False
            
        except Exception as e:
            self.log(f"❌ Error verifying instance: {e}")
            return False
    
    def stop(self):
        """FIXED: Stop the AutoGather module properly"""
        try:
            self.log("🛑 Stopping AutoGather...")
            self.is_running = False
            
            # Wait for worker thread to finish
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5)
                if self.worker_thread.is_alive():
                    self.log("⚠️ Worker thread did not stop gracefully")
            
            self.log("✅ AutoGather stopped")
            return True
            
        except Exception as e:
            self.log(f"❌ Error stopping AutoGather: {e}")
            return False
    
    def _worker_loop(self):
        """FIXED: Main worker loop with better error handling"""
        cycle_count = 0
        consecutive_failures = 0
        
        try:
            while self.is_running:
                try:
                    cycle_count += 1
                    start_time = time.time()
                    
                    self.log(f"📋 March Queue analysis #{cycle_count} - Reading and analyzing...")
                    
                    # Check if instance is still running
                    if not self._is_instance_running():
                        self.log("⏸️ Instance not running, pausing AutoGather")
                        time.sleep(30)  # Wait and check again
                        continue
                    
                    # Navigate to march queue and analyze
                    success = self._navigate_to_march_queue()
                    if success:
                        self._analyze_march_queues()
                        consecutive_failures = 0  # Reset failure count on success
                    else:
                        consecutive_failures += 1
                        self.log(f"❌ AutoGather cycle {cycle_count} failed (consecutive failures: {consecutive_failures}/{self.config.max_retries})")
                        
                        if consecutive_failures >= self.config.max_retries:
                            self.log(f"❌ AutoGather failed {self.config.max_retries} consecutive times, stopping...")
                            break
                    
                    elapsed_time = time.time() - start_time
                    self.log(f"✅ AutoGather cycle {cycle_count} completed (took {elapsed_time:.1f}s)")
                    
                    # Wait for next cycle (interruptible)
                    self._sleep_interruptible(self.config.cycle_interval)
                    
                except Exception as e:
                    self.log(f"❌ Error in AutoGather cycle {cycle_count}: {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= self.config.max_retries:
                        self.log("❌ Too many consecutive errors, stopping AutoGather")
                        break
                    
                    # Sleep before retry
                    self._sleep_interruptible(10)
                    
        except Exception as e:
            self.log(f"❌ Fatal error in AutoGather worker loop: {e}")
        finally:
            self.is_running = False
            self.log("🏁 AutoGather worker loop ended")
    
    def _sleep_interruptible(self, seconds: float):
        """Sleep that can be interrupted when stopping"""
        sleep_steps = int(seconds * 10)  # Check every 0.1 seconds
        for _ in range(sleep_steps):
            if not self.is_running:
                break
            time.sleep(0.1)
    
    def _is_instance_running(self) -> bool:
        """Check if the MEmu instance is currently running"""
        try:
            if not self.shared_resources:
                return True  # Assume running if we can't check
            
            if hasattr(self.shared_resources, 'get_instance'):
                instance = self.shared_resources.get_instance(self.instance_name)
                if instance:
                    return instance.get('status') == 'Running'
            
            return True  # Assume running if we can't determine
            
        except Exception as e:
            self.log(f"⚠️ Error checking instance status: {e}")
            return True  # Assume running on error
    
    def _navigate_to_march_queue(self) -> bool:
        """FIXED: Navigate to march queue with better error handling"""
        try:
            self.log("🧭 Navigating to march queue...")
            
            # Step 1: Take initial screenshot
            screenshot_path = self._take_screenshot_with_retries()
            if not screenshot_path:
                self.log("❌ Failed to take initial screenshot")
                return False
            
            try:
                # Step 2: Try to click open left panel
                self.log("📱 Attempting to open left panel...")
                if not self._click_template_in_screenshot(screenshot_path, 'open_left'):
                    self.log("❌ Failed to click open_left.png")
                    return False
                
                # Wait for panel to open
                time.sleep(3)
                
                # Step 3: Take new screenshot for wilderness button
                wilderness_screenshot = self._take_screenshot_with_retries()
                if not wilderness_screenshot:
                    self.log("❌ Failed to take screenshot after opening panel")
                    return False
                
                try:
                    # Step 4: Click wilderness button
                    self.log("🌲 Attempting to click wilderness button...")
                    if not self._click_template_in_screenshot(wilderness_screenshot, 'wilderness_button'):
                        self.log("❌ Failed to click wilderness_button.png")
                        return False
                    
                    # Wait for march queue to load
                    time.sleep(4)
                    
                    self.log("✅ Successfully navigated to march queue")
                    return True
                    
                finally:
                    self._cleanup_screenshot(wilderness_screenshot)
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log(f"❌ Navigation error: {e}")
            return False
    
    def _take_screenshot_with_retries(self) -> Optional[str]:
        """FIXED: Take screenshot with retries and better error handling"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                screenshot_path = self._take_screenshot_adb()
                if screenshot_path and os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path)
                    if file_size > 10000:  # Reasonable size check
                        self.log(f"📸 Screenshot taken successfully (attempt {attempt + 1}, size: {file_size} bytes)")
                        return screenshot_path
                    else:
                        self.log(f"⚠️ Screenshot too small (attempt {attempt + 1}, size: {file_size} bytes)")
                        if screenshot_path:
                            self._cleanup_screenshot(screenshot_path)
                else:
                    self.log(f"❌ Screenshot failed (attempt {attempt + 1})")
                
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retry
                    
            except Exception as e:
                self.log(f"❌ Screenshot error (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
        
        self.log("❌ All screenshot attempts failed")
        return None
    
    def _take_screenshot_adb(self) -> Optional[str]:
        """FIXED: Take screenshot using ADB with proper paths"""
        try:
            # Use temp directory for screenshots
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            local_screenshot = os.path.join(temp_dir, f"autogather_screenshot_{self.instance_index}_{timestamp}.png")
            device_screenshot = "/sdcard/autogather_screen.png"
            
            # Take screenshot on device
            capture_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "screencap", "-p", device_screenshot
            ]
            
            self.log(f"📸 Taking screenshot with command: {' '.join(capture_cmd)}")
            
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15)
            if capture_result.returncode != 0:
                self.log(f"❌ Screenshot capture failed: {capture_result.stderr}")
                return None
            
            time.sleep(0.5)  # Wait for file to be written
            
            # Pull screenshot from device
            pull_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "pull", device_screenshot, local_screenshot
            ]
            
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=15)
            if pull_result.returncode != 0:
                self.log(f"❌ Screenshot pull failed: {pull_result.stderr}")
                return None
            
            # Clean up device screenshot
            cleanup_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "rm", device_screenshot
            ]
            
            try:
                subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
            except:
                pass  # Don't fail if cleanup fails
            
            # Verify screenshot exists and is valid
            if os.path.exists(local_screenshot):
                file_size = os.path.getsize(local_screenshot)
                if file_size > 10000:
                    self.log(f"✅ Screenshot saved: {os.path.basename(local_screenshot)} ({file_size} bytes)")
                    return local_screenshot
                else:
                    self.log(f"❌ Screenshot too small: {file_size} bytes")
                    os.remove(local_screenshot)
            else:
                self.log("❌ Screenshot file not created")
            
            return None
            
        except subprocess.TimeoutExpired:
            self.log("❌ Screenshot command timed out")
            return None
        except Exception as e:
            self.log(f"❌ Screenshot error: {e}")
            return None
    
    def _click_template_in_screenshot(self, screenshot_path: str, template_name: str) -> bool:
        """FIXED: Click template with better error handling and verification"""
        try:
            # Check if template file exists
            template_path = self.templates.get(template_name)
            if not template_path or not os.path.exists(template_path):
                self.log(f"❌ Template not found: {template_name} at {template_path}")
                return False
            
            self.log(f"✅ Found template at: {template_path}")
            
            # Verify screenshot exists and is valid
            if not os.path.exists(screenshot_path):
                self.log(f"❌ Screenshot not found: {screenshot_path}")
                return False
            
            try:
                # Load images
                screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                
                if screenshot is None:
                    self.log(f"❌ Failed to load screenshot: {screenshot_path}")
                    return False
                
                if template is None:
                    self.log(f"❌ Failed to load template: {template_path}")
                    return False
                
                # Get dimensions
                template_height, template_width = template.shape[:2]
                screenshot_height, screenshot_width = screenshot.shape[:2]
                
                self.log(f"📏 Template dimensions: {template_width}x{template_height}")
                self.log(f"📏 Screenshot dimensions: {screenshot_width}x{screenshot_height}")
                
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
                    
                    # Click at the position
                    if self._click_position(click_x, click_y):
                        self.log(f"✅ Successfully clicked {template_name} at ({click_x}, {click_y})")
                        return True
                    else:
                        self.log(f"❌ Failed to click {template_name} at ({click_x}, {click_y})")
                        return False
                else:
                    self.log(f"❌ Template confidence {max_val:.3f} below threshold {self.config.template_matching_threshold}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Template matching error: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Click template error: {e}")
            return False
    
    def _click_position(self, x: int, y: int) -> bool:
        """FIXED: Click position using ADB with better error handling"""
        try:
            # Use ADB to tap at position
            tap_cmd = [
                self.memu_path, "adb", "-i", str(self.instance_index),
                "shell", "input", "tap", str(x), str(y)
            ]
            
            self.log(f"👆 Clicking position ({x}, {y}) with command: {' '.join(tap_cmd)}")
            
            result = subprocess.run(tap_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log(f"✅ Successfully clicked position ({x}, {y})")
                return True
            else:
                self.log(f"❌ Click failed at ({x}, {y}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"❌ Click command timed out at ({x}, {y})")
            return False
        except Exception as e:
            self.log(f"❌ Click error at ({x}, {y}): {e}")
            return False
    
    def _analyze_march_queues(self):
        """FIXED: Analyze march queues with better error handling"""
        try:
            self.log("🔍 Starting march queue analysis...")
            
            # Take screenshot of march queue screen
            screenshot_path = self._take_screenshot_with_retries()
            if not screenshot_path:
                self.log("❌ Failed to take screenshot for queue analysis")
                return
            
            try:
                self.log("🔍 Starting OCR analysis of march queues...")
                
                # NEW: Save full screenshot if OCR saving is enabled
                if self.config.save_ocr_images:
                    self._save_full_screenshot(screenshot_path)
                
                # Clear previous queue data
                self.queues.clear()
                
                # Analyze each queue
                for queue_num in range(1, 7):
                    if not self.is_running:  # Check if we should stop
                        break
                    self._analyze_single_queue(queue_num, screenshot_path)
                
                self.log(f"✅ OCR analysis complete - analyzed {len(self.queues)} queues")
                
                # Report results
                available_queues = [q for q_num, q in self.queues.items() if q.is_available]
                if available_queues:
                    queue_numbers = [str(q_num) for q_num, q in self.queues.items() if q.is_available]
                    self.log(f"🎯 Available queues for marches: {', '.join(queue_numbers)}")
                else:
                    self.log("⚠️ No available queues found for new marches")
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log(f"❌ Queue analysis error: {e}")
    
    def _save_full_screenshot(self, screenshot_path: str):
        """NEW: Save full screenshot for reference"""
        try:
            if not self.config.save_ocr_images:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"full_screenshot_{timestamp}.png"
            save_path = os.path.join(self.ocr_save_dir, filename)
            
            # Copy screenshot to OCR save directory
            import shutil
            shutil.copy2(screenshot_path, save_path)
            
            self.log(f"💾 Saved full screenshot: {filename}")
            
        except Exception as e:
            self.log(f"⚠️ Error saving full screenshot: {e}")
    
    def _analyze_single_queue(self, queue_num: int, screenshot_path: str):
        """FIXED: Analyze a single march queue with better error handling"""
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
                availability = "AVAILABLE" if queue_info.is_available else "BUSY"
                self.log(f"📊 Queue {queue_num}: Task='{queue_info.task}' | Timer='{queue_info.time_remaining}' | Status={availability}")
            else:
                availability = "AVAILABLE" if queue_info.is_available else "LOCKED/BUSY"
                self.log(f"📊 Queue {queue_num}: Name='{queue_info.name}' | Status='{queue_info.status}' | Available={availability}")
                
        except Exception as e:
            self.log(f"❌ Error analyzing Queue {queue_num}: {e}")
    
    def _perform_ocr_on_region(self, screenshot_path: str, region: tuple, text_type: str) -> str:
        """ENHANCED: Perform OCR with image saving and better error handling"""
        try:
            if not self.ocr_reader:
                self.log(f"❌ OCR reader not available for {text_type}")
                return ""
            
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                self.log(f"❌ Failed to load screenshot for OCR: {screenshot_path}")
                return ""
            
            # Extract region
            x, y, w, h = region
            
            # Validate region bounds
            screenshot_height, screenshot_width = screenshot.shape[:2]
            if x + w > screenshot_width or y + h > screenshot_height:
                self.log(f"⚠️ OCR region out of bounds for {text_type}: ({x},{y},{w},{h}) vs screenshot ({screenshot_width},{screenshot_height})")
                # Adjust bounds
                w = min(w, screenshot_width - x)
                h = min(h, screenshot_height - y)
            
            roi = screenshot[y:y+h, x:x+w]
            
            if roi.size == 0:
                self.log(f"❌ Empty ROI for {text_type}")
                return ""
            
            # NEW: Save OCR region image
            saved_image_path = None
            if self.config.save_ocr_images:
                saved_image_path = self._save_ocr_region_image(roi, text_type)
            
            # Perform OCR
            try:
                results = self.ocr_reader.readtext(roi, detail=1)
                self.log(f"🔍 OCR results for {text_type}: {len(results)} detections")
                
                if not results:
                    self.log(f"❌ No text detected in {text_type} region")
                    if saved_image_path:
                        self.log(f"💾 OCR region saved for analysis: {os.path.basename(saved_image_path)}")
                    return ""
                
                # Process results
                best_text = ""
                best_confidence = 0.0
                
                for detection in results:
                    bbox, text, confidence = detection
                    
                    # Filter by confidence
                    if confidence >= self.config.ocr_confidence_threshold:
                        if confidence > best_confidence:
                            best_text = text
                            best_confidence = confidence
                        self.log(f"   ✅ '{text}' (confidence: {confidence:.3f})")
                    else:
                        self.log(f"   ❌ '{text}' (confidence: {confidence:.3f}) - below threshold")
                
                if best_text:
                    # Clean the text
                    cleaned_text = self._clean_text_for_type(best_text, text_type)
                    if cleaned_text != best_text:
                        self.log(f"🧹 Cleaned text: '{best_text}' → '{cleaned_text}'")
                    
                    # NEW: Log saved image info
                    if saved_image_path:
                        self.log(f"💾 OCR region saved: {os.path.basename(saved_image_path)} (result: '{cleaned_text}')")
                    
                    return cleaned_text
                else:
                    self.log(f"❌ No text passed confidence threshold for {text_type}")
                    if saved_image_path:
                        self.log(f"💾 OCR region saved for analysis: {os.path.basename(saved_image_path)}")
                    return ""
                    
            except Exception as ocr_error:
                self.log(f"❌ OCR processing error for {text_type}: {ocr_error}")
                if saved_image_path:
                    self.log(f"💾 OCR region saved for debugging: {os.path.basename(saved_image_path)}")
                return ""
                
        except Exception as e:
            self.log(f"❌ OCR error for {text_type}: {e}")
            return ""
    
    def _save_ocr_region_image(self, roi_image: np.ndarray, text_type: str) -> Optional[str]:
        """NEW: Save OCR region image for debugging and analysis"""
        try:
            if not self.config.save_ocr_images:
                return None
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            
            # Clean text_type for filename
            clean_text_type = re.sub(r'[^\w\-_]', '_', text_type)
            filename = f"ocr_{clean_text_type}_{timestamp}.png"
            
            # Save path
            save_path = os.path.join(self.ocr_save_dir, filename)
            
            # Enhance image for better visibility (optional)
            enhanced_roi = self._enhance_ocr_image(roi_image)
            
            # Save the image
            success = cv2.imwrite(save_path, enhanced_roi)
            
            if success:
                return save_path
            else:
                self.log(f"⚠️ Failed to save OCR region image: {filename}")
                return None
                
        except Exception as e:
            self.log(f"⚠️ Error saving OCR region image: {e}")
            return None
    
    def _enhance_ocr_image(self, roi_image: np.ndarray) -> np.ndarray:
        """NEW: Enhance OCR region image for better visibility and analysis"""
        try:
            # Scale up the image for better visibility
            scale_factor = 4
            height, width = roi_image.shape[:2]
            new_width = width * scale_factor
            new_height = height * scale_factor
            
            # Use INTER_CUBIC for better quality when scaling up
            scaled = cv2.resize(roi_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Convert to grayscale for analysis
            if len(scaled.shape) == 3:
                gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
            else:
                gray = scaled
            
            # Apply slight sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            
            # Convert back to BGR for saving
            if len(roi_image.shape) == 3:
                return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
            else:
                return sharpened
                
        except Exception as e:
            self.log(f"⚠️ Error enhancing OCR image: {e}")
            return roi_image  # Return original if enhancement fails
    
    def _clean_text_for_type(self, text: str, text_type: str) -> str:
        """ENHANCED: Clean OCR text based on context with improved gathering and time detection"""
        if not text:
            return ""
        
        # Handle "Idle" first before any other processing
        if text.lower() in ['idle', 'idlc', 'id1e', '1dle', 'id1c', 'idl3', '1d1e', 'id1c', 'idlc']:
            return 'Idle'
        
        if "timer" in text_type.lower():
            # ENHANCED: Timer-specific cleaning with better time format detection
            original_text = text
            
            # Character replacements for common OCR mistakes in times
            fixes = {
                'O': '0', 'o': '0', 'l': '1', 'I': '1', '|': '1', 'i': '1',
                'S': '5', 's': '5', 'Z': '2', 'z': '2', 'G': '6', 'g': '9',
                'B': '8', 'D': '0', 'Q': '0', 'T': '7', 'j': ':', 'J': '1'
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
            
            # ENHANCED: Multiple time format patterns
            # Convert various separators to colons
            text = re.sub(r'(\d{2})\.(\d{2})\.(\d{2})', r'\1:\2:\3', text)  # 02.41.29 -> 02:41:29
            text = re.sub(r'(\d{2})\.(\d{2})\.(\d{1})', r'\1:\2:0\3', text)  # 02.41.9 -> 02:41:09
            text = re.sub(r'(\d{2}),(\d{2}),(\d{2})', r'\1:\2:\3', text)     # 02,41,29 -> 02:41:29
            text = re.sub(r'(\d{2}) (\d{2}) (\d{2})', r'\1:\2:\3', text)     # 02 41 29 -> 02:41:29
            text = re.sub(r'(\d{2})-(\d{2})-(\d{2})', r'\1:\2:\3', text)     # 02-41-29 -> 02:41:29
            
            # Handle 6-digit times without separators (025400 -> 02:54:00)
            if re.match(r'^\d{6}
    
    def _determine_queue_availability(self, queue_num: int, queue_info: QueueInfo) -> bool:
        """ENHANCED: Determine queue availability with better gathering and time detection logic"""
        try:
            if queue_num <= 2:
                # For queues 1-2, check timer and task
                if queue_info.time_remaining:
                    # Check for idle indicators
                    idle_keywords = ['idle', 'idlc', 'id1e', '1dle', 'id1c']
                    if any(keyword in queue_info.time_remaining.lower() for keyword in idle_keywords):
                        queue_info.status = "Available (Idle)"
                        return True
                    # ENHANCED: Better time pattern detection
                    elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                        # Valid time format detected - queue is busy
                        if queue_info.task and 'gathering' in queue_info.task.lower():
                            queue_info.status = f"Busy (Gathering - {queue_info.time_remaining})"
                        else:
                            queue_info.status = f"Busy ({queue_info.time_remaining})"
                        return False
                    # ENHANCED: Handle partial time formats
                    elif re.search(r'\d{2}[:\.,]\d{2}[:\.,]?\d*', queue_info.time_remaining):
                        # Partial time detected - still busy
                        queue_info.status = f"Busy (Time: {queue_info.time_remaining})"
                        return False
                    else:
                        self.log(f"❓ Queue {queue_num} timer format unrecognized: '{queue_info.time_remaining}'")
                        queue_info.status = "Unknown Timer Format"
                        return False
                else:
                    # No timer detected
                    if queue_info.task:
                        # Check if task indicates gathering
                        if 'gathering' in queue_info.task.lower():
                            queue_info.status = "Possibly Busy (Gathering detected, no timer)"
                            return False
                        elif 'idle' in queue_info.task.lower():
                            queue_info.status = "Available (Task shows Idle)"
                            return True
                        else:
                            queue_info.status = "Possibly Available (Task unclear)"
                            return True
                    else:
                        # No timer, no task - assume available
                        queue_info.status = "Possibly Available (No data)"
                        return True
                        
            else:
                # For queues 3-6, check status text
                if not queue_info.status:
                    # No status detected - check if queue name exists
                    if queue_info.name:
                        queue_info.status = "Available (No status text)"
                        return True
                    else:
                        queue_info.status = "Unknown (No data)"
                        return False
                elif any(keyword in queue_info.status.lower() for keyword in ['idle', 'available']):
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['unlock', 'cannot', 'locked']):
                    return False
                elif 'use' in queue_info.status.lower():
                    # Probably "Cannot use"
                    queue_info.status = "Cannot use"
                    return False
                else:
                    # Unknown status - be conservative
                    self.log(f"❓ Queue {queue_num} status unclear: '{queue_info.status}'")
                    queue_info.status = f"Unknown ({queue_info.status})"
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error determining availability for Queue {queue_num}: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """FIXED: Safe screenshot cleanup"""
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception as e:
                self.log(f"⚠️ Could not cleanup screenshot {screenshot_path}: {e}")
    
    # ENHANCED: Better status and control methods with OCR image info
    def get_status(self) -> Dict:
        """Get current AutoGather status"""
        ocr_image_count = 0
        ocr_image_size = 0
        
        if os.path.exists(self.ocr_save_dir):
            try:
                files = os.listdir(self.ocr_save_dir)
                ocr_image_count = len([f for f in files if f.endswith('.png')])
                ocr_image_size = sum(os.path.getsize(os.path.join(self.ocr_save_dir, f)) 
                                   for f in files if os.path.isfile(os.path.join(self.ocr_save_dir, f)))
            except:
                pass
        
        return {
            "running": self.is_running,
            "instance_name": self.instance_name,
            "instance_index": self.instance_index,
            "memu_path": self.memu_path,
            "ocr_available": self.ocr_reader is not None,
            "templates_available": all(os.path.exists(path) for path in self.templates.values()),
            "queue_count": len(self.queues),
            "available_queues": len([q for q in self.queues.values() if q.is_available]),
            "ocr_image_saving": self.config.save_ocr_images,
            "ocr_save_directory": self.ocr_save_dir,
            "ocr_image_count": ocr_image_count,
            "ocr_image_size_mb": round(ocr_image_size / (1024 * 1024), 2)
        }
    
    def force_cycle(self) -> bool:
        """Force a single AutoGather cycle (for testing)"""
        try:
            if not self.is_running:
                self.log("🎯 Force running single AutoGather cycle...")
                
                # Temporarily set running to allow cycle
                self.is_running = True
                
                # Check prerequisites
                if not self.ocr_reader and not self.initialize():
                    self.log("❌ Cannot run cycle - OCR not available")
                    self.is_running = False
                    return False
                
                # Run single cycle
                success = self._navigate_to_march_queue()
                if success:
                    self._analyze_march_queues()
                    self.log("✅ Force cycle completed successfully")
                    result = True
                else:
                    self.log("❌ Force cycle failed")
                    result = False
                
                self.is_running = False
                return result
            else:
                self.log("⚠️ AutoGather is already running, cannot force cycle")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in force cycle: {e}")
            self.is_running = False
            return False
    
    def update_config(self, **kwargs):
        """Update AutoGather configuration with enhanced OCR settings"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    old_value = getattr(self.config, key)
                    setattr(self.config, key, value)
                    self.log(f"⚙️ Updated config: {key} = {value} (was: {old_value})")
                    
                    # Handle OCR directory changes
                    if key == 'save_ocr_images' and value:
                        os.makedirs(self.ocr_save_dir, exist_ok=True)
                        self.log(f"📁 Created OCR save directory: {self.ocr_save_dir}")
                    elif key == 'ocr_save_directory':
                        self.ocr_save_dir = os.path.join(value, self.instance_name)
                        if self.config.save_ocr_images:
                            os.makedirs(self.ocr_save_dir, exist_ok=True)
                            self.log(f"📁 Updated OCR save directory: {self.ocr_save_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Error updating config: {e}")
            return False
    
    def optimize_for_gathering_detection(self):
        """NEW: Optimize settings for better gathering and time detection"""
        try:
            self.log("🎯 Optimizing AutoGather for better gathering and time detection...")
            
            # Lower confidence threshold for better detection
            self.update_config(
                ocr_confidence_threshold=0.35,  # From 0.5 to 0.35 for better detection
                template_matching_threshold=0.6,  # From 0.7 to 0.6 for panel state changes
            )
            
            self.log("✅ AutoGather optimized for gathering detection")
            return True
            
        except Exception as e:
            self.log(f"❌ Error optimizing for gathering detection: {e}")
            return False
    
    # NEW: OCR image management methods
    def get_ocr_images_info(self) -> Dict:
        """Get information about saved OCR images"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            files = []
            total_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                    total_size += stat.st_size
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x['created'], reverse=True)
            
            return {
                "directory": self.ocr_save_dir,
                "total_files": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": files[:50]  # Limit to 50 most recent files
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_ocr_images(self, older_than_days: Optional[int] = None) -> Dict:
        """Clear OCR images (optionally only older than specified days)"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            deleted_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    # Check age if specified
                    if cutoff_time is not None:
                        file_time = os.path.getmtime(filepath)
                        if file_time >= cutoff_time:
                            continue  # Skip newer files
                    
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        self.log(f"⚠️ Could not delete OCR image {filename}: {e}")
            
            self.log(f"🧹 Cleared {deleted_count} OCR images ({deleted_size / (1024 * 1024):.2f} MB)")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # FIXED: Add debugging methods
    def debug_templates(self) -> Dict:
        """Debug template availability"""
        template_status = {}
        for name, path in self.templates.items():
            template_status[name] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0
            }
        return template_status
    
    def debug_instance_connection(self) -> Dict:
        """Debug MEmu instance connection"""
        try:
            # Test basic MEmu command
            cmd = [self.memu_path, "version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            version_ok = result.returncode == 0
            version_output = result.stdout if version_ok else result.stderr
            
            # Test instance list
            list_cmd = [self.memu_path, "listvms"]
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=10)
            
            list_ok = list_result.returncode == 0
            
            return {
                "memu_path": self.memu_path,
                "memu_exists": os.path.exists(self.memu_path),
                "version_command_ok": version_ok,
                "version_output": version_output,
                "list_command_ok": list_ok,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index,
                "list_output": list_result.stdout if list_ok else list_result.stderr
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "memu_path": self.memu_path,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index
            }
    
    def debug_screenshot(self) -> Dict:
        """Debug screenshot functionality"""
        try:
            self.log("🐛 Testing screenshot functionality...")
            
            screenshot_path = self._take_screenshot_with_retries()
            if screenshot_path:
                file_size = os.path.getsize(screenshot_path)
                self.log(f"✅ Screenshot test successful: {file_size} bytes")
                
                # Cleanup test screenshot
                self._cleanup_screenshot(screenshot_path)
                
                return {
                    "success": True,
                    "file_size": file_size,
                    "path": screenshot_path
                }
            else:
                self.log("❌ Screenshot test failed")
                return {"success": False, "error": "Screenshot failed"}
                
        except Exception as e:
            self.log(f"❌ Screenshot test error: {e}")
            return {"success": False, "error": str(e)}


# ENHANCED: Convenience functions for external use
def create_autogather_module(instance_name: str, shared_resources=None, console_callback=None) -> AutoGatherModule:
    """Create and return a configured AutoGather module"""
    return AutoGatherModule(instance_name, shared_resources, console_callback)


def test_autogather_prerequisites(instance_name: str, shared_resources=None) -> Dict:
    """Test if AutoGather can run for an instance"""
    try:
        # Create temporary module for testing
        module = AutoGatherModule(instance_name, shared_resources)
        
        # Test initialization
        init_success = module.initialize()
        
        # Test templates
        template_status = module.debug_templates()
        
        # Test instance connection
        connection_status = module.debug_instance_connection()
        
        # Test screenshot
        screenshot_status = module.debug_screenshot()
        
        # Test OCR image saving
        ocr_info = module.get_ocr_images_info()
        
        return {
            "instance_name": instance_name,
            "initialization": init_success,
            "templates": template_status,
            "connection": connection_status,
            "screenshot": screenshot_status,
            "ocr_images": ocr_info,
            "overall_ready": (init_success and 
                            connection_status.get("memu_exists", False) and
                            screenshot_status.get("success", False))
        }
        
    except Exception as e:
        return {
            "instance_name": instance_name,
            "error": str(e),
            "overall_ready": False
        }, text):
                text = f"{text[:2]}:{text[2:4]}:{text[4:6]}"
            elif re.match(r'^\d{5}
    
    def _determine_queue_availability(self, queue_num: int, queue_info: QueueInfo) -> bool:
        """FIXED: Determine queue availability with better logic"""
        try:
            if queue_num <= 2:
                # For queues 1-2, check timer
                if queue_info.time_remaining:
                    # Check for idle indicators
                    idle_keywords = ['idle', 'idlc', 'id1e', '1dle', 'id1c']
                    if any(keyword in queue_info.time_remaining.lower() for keyword in idle_keywords):
                        queue_info.status = "Available (Idle)"
                        return True
                    elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                        queue_info.status = "Busy (Gathering)"
                        return False
                    else:
                        queue_info.status = "Unknown"
                        return False
                else:
                    # No timer detected - might be available
                    queue_info.status = "Possibly Available"
                    return True
                    
            else:
                # For queues 3-6, check status text
                if not queue_info.status:
                    # No status detected - assume available if queue exists
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['idle', 'available']):
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['unlock', 'cannot', 'locked']):
                    return False
                else:
                    # Unknown status - be conservative
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error determining availability for Queue {queue_num}: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """FIXED: Safe screenshot cleanup"""
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception as e:
                self.log(f"⚠️ Could not cleanup screenshot {screenshot_path}: {e}")
    
    # ENHANCED: Better status and control methods with OCR image info
    def get_status(self) -> Dict:
        """Get current AutoGather status"""
        ocr_image_count = 0
        ocr_image_size = 0
        
        if os.path.exists(self.ocr_save_dir):
            try:
                files = os.listdir(self.ocr_save_dir)
                ocr_image_count = len([f for f in files if f.endswith('.png')])
                ocr_image_size = sum(os.path.getsize(os.path.join(self.ocr_save_dir, f)) 
                                   for f in files if os.path.isfile(os.path.join(self.ocr_save_dir, f)))
            except:
                pass
        
        return {
            "running": self.is_running,
            "instance_name": self.instance_name,
            "instance_index": self.instance_index,
            "memu_path": self.memu_path,
            "ocr_available": self.ocr_reader is not None,
            "templates_available": all(os.path.exists(path) for path in self.templates.values()),
            "queue_count": len(self.queues),
            "available_queues": len([q for q in self.queues.values() if q.is_available]),
            "ocr_image_saving": self.config.save_ocr_images,
            "ocr_save_directory": self.ocr_save_dir,
            "ocr_image_count": ocr_image_count,
            "ocr_image_size_mb": round(ocr_image_size / (1024 * 1024), 2)
        }
    
    def force_cycle(self) -> bool:
        """Force a single AutoGather cycle (for testing)"""
        try:
            if not self.is_running:
                self.log("🎯 Force running single AutoGather cycle...")
                
                # Temporarily set running to allow cycle
                self.is_running = True
                
                # Check prerequisites
                if not self.ocr_reader and not self.initialize():
                    self.log("❌ Cannot run cycle - OCR not available")
                    self.is_running = False
                    return False
                
                # Run single cycle
                success = self._navigate_to_march_queue()
                if success:
                    self._analyze_march_queues()
                    self.log("✅ Force cycle completed successfully")
                    result = True
                else:
                    self.log("❌ Force cycle failed")
                    result = False
                
                self.is_running = False
                return result
            else:
                self.log("⚠️ AutoGather is already running, cannot force cycle")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in force cycle: {e}")
            self.is_running = False
            return False
    
    def update_config(self, **kwargs):
        """Update AutoGather configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    old_value = getattr(self.config, key)
                    setattr(self.config, key, value)
                    self.log(f"⚙️ Updated config: {key} = {value} (was: {old_value})")
                    
                    # Handle OCR directory changes
                    if key == 'save_ocr_images' and value:
                        os.makedirs(self.ocr_save_dir, exist_ok=True)
                        self.log(f"📁 Created OCR save directory: {self.ocr_save_dir}")
                    elif key == 'ocr_save_directory':
                        self.ocr_save_dir = os.path.join(value, self.instance_name)
                        if self.config.save_ocr_images:
                            os.makedirs(self.ocr_save_dir, exist_ok=True)
                            self.log(f"📁 Updated OCR save directory: {self.ocr_save_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Error updating config: {e}")
            return False
    
    # NEW: OCR image management methods
    def get_ocr_images_info(self) -> Dict:
        """Get information about saved OCR images"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            files = []
            total_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                    total_size += stat.st_size
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x['created'], reverse=True)
            
            return {
                "directory": self.ocr_save_dir,
                "total_files": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": files[:50]  # Limit to 50 most recent files
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_ocr_images(self, older_than_days: Optional[int] = None) -> Dict:
        """Clear OCR images (optionally only older than specified days)"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            deleted_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    # Check age if specified
                    if cutoff_time is not None:
                        file_time = os.path.getmtime(filepath)
                        if file_time >= cutoff_time:
                            continue  # Skip newer files
                    
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        self.log(f"⚠️ Could not delete OCR image {filename}: {e}")
            
            self.log(f"🧹 Cleared {deleted_count} OCR images ({deleted_size / (1024 * 1024):.2f} MB)")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # FIXED: Add debugging methods
    def debug_templates(self) -> Dict:
        """Debug template availability"""
        template_status = {}
        for name, path in self.templates.items():
            template_status[name] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0
            }
        return template_status
    
    def debug_instance_connection(self) -> Dict:
        """Debug MEmu instance connection"""
        try:
            # Test basic MEmu command
            cmd = [self.memu_path, "version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            version_ok = result.returncode == 0
            version_output = result.stdout if version_ok else result.stderr
            
            # Test instance list
            list_cmd = [self.memu_path, "listvms"]
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=10)
            
            list_ok = list_result.returncode == 0
            
            return {
                "memu_path": self.memu_path,
                "memu_exists": os.path.exists(self.memu_path),
                "version_command_ok": version_ok,
                "version_output": version_output,
                "list_command_ok": list_ok,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index,
                "list_output": list_result.stdout if list_ok else list_result.stderr
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "memu_path": self.memu_path,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index
            }
    
    def debug_screenshot(self) -> Dict:
        """Debug screenshot functionality"""
        try:
            self.log("🐛 Testing screenshot functionality...")
            
            screenshot_path = self._take_screenshot_with_retries()
            if screenshot_path:
                file_size = os.path.getsize(screenshot_path)
                self.log(f"✅ Screenshot test successful: {file_size} bytes")
                
                # Cleanup test screenshot
                self._cleanup_screenshot(screenshot_path)
                
                return {
                    "success": True,
                    "file_size": file_size,
                    "path": screenshot_path
                }
            else:
                self.log("❌ Screenshot test failed")
                return {"success": False, "error": "Screenshot failed"}
                
        except Exception as e:
            self.log(f"❌ Screenshot test error: {e}")
            return {"success": False, "error": str(e)}


# ENHANCED: Convenience functions for external use
def create_autogather_module(instance_name: str, shared_resources=None, console_callback=None) -> AutoGatherModule:
    """Create and return a configured AutoGather module"""
    return AutoGatherModule(instance_name, shared_resources, console_callback)


def test_autogather_prerequisites(instance_name: str, shared_resources=None) -> Dict:
    """Test if AutoGather can run for an instance"""
    try:
        # Create temporary module for testing
        module = AutoGatherModule(instance_name, shared_resources)
        
        # Test initialization
        init_success = module.initialize()
        
        # Test templates
        template_status = module.debug_templates()
        
        # Test instance connection
        connection_status = module.debug_instance_connection()
        
        # Test screenshot
        screenshot_status = module.debug_screenshot()
        
        # Test OCR image saving
        ocr_info = module.get_ocr_images_info()
        
        return {
            "instance_name": instance_name,
            "initialization": init_success,
            "templates": template_status,
            "connection": connection_status,
            "screenshot": screenshot_status,
            "ocr_images": ocr_info,
            "overall_ready": (init_success and 
                            connection_status.get("memu_exists", False) and
                            screenshot_status.get("success", False))
        }
        
    except Exception as e:
        return {
            "instance_name": instance_name,
            "error": str(e),
            "overall_ready": False
        }, text):  # 25400 -> 02:54:00
                text = f"0{text[0]}:{text[1:3]}:{text[3:5]}"
            elif re.match(r'^\d{4}
    
    def _determine_queue_availability(self, queue_num: int, queue_info: QueueInfo) -> bool:
        """FIXED: Determine queue availability with better logic"""
        try:
            if queue_num <= 2:
                # For queues 1-2, check timer
                if queue_info.time_remaining:
                    # Check for idle indicators
                    idle_keywords = ['idle', 'idlc', 'id1e', '1dle', 'id1c']
                    if any(keyword in queue_info.time_remaining.lower() for keyword in idle_keywords):
                        queue_info.status = "Available (Idle)"
                        return True
                    elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                        queue_info.status = "Busy (Gathering)"
                        return False
                    else:
                        queue_info.status = "Unknown"
                        return False
                else:
                    # No timer detected - might be available
                    queue_info.status = "Possibly Available"
                    return True
                    
            else:
                # For queues 3-6, check status text
                if not queue_info.status:
                    # No status detected - assume available if queue exists
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['idle', 'available']):
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['unlock', 'cannot', 'locked']):
                    return False
                else:
                    # Unknown status - be conservative
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error determining availability for Queue {queue_num}: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """FIXED: Safe screenshot cleanup"""
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception as e:
                self.log(f"⚠️ Could not cleanup screenshot {screenshot_path}: {e}")
    
    # ENHANCED: Better status and control methods with OCR image info
    def get_status(self) -> Dict:
        """Get current AutoGather status"""
        ocr_image_count = 0
        ocr_image_size = 0
        
        if os.path.exists(self.ocr_save_dir):
            try:
                files = os.listdir(self.ocr_save_dir)
                ocr_image_count = len([f for f in files if f.endswith('.png')])
                ocr_image_size = sum(os.path.getsize(os.path.join(self.ocr_save_dir, f)) 
                                   for f in files if os.path.isfile(os.path.join(self.ocr_save_dir, f)))
            except:
                pass
        
        return {
            "running": self.is_running,
            "instance_name": self.instance_name,
            "instance_index": self.instance_index,
            "memu_path": self.memu_path,
            "ocr_available": self.ocr_reader is not None,
            "templates_available": all(os.path.exists(path) for path in self.templates.values()),
            "queue_count": len(self.queues),
            "available_queues": len([q for q in self.queues.values() if q.is_available]),
            "ocr_image_saving": self.config.save_ocr_images,
            "ocr_save_directory": self.ocr_save_dir,
            "ocr_image_count": ocr_image_count,
            "ocr_image_size_mb": round(ocr_image_size / (1024 * 1024), 2)
        }
    
    def force_cycle(self) -> bool:
        """Force a single AutoGather cycle (for testing)"""
        try:
            if not self.is_running:
                self.log("🎯 Force running single AutoGather cycle...")
                
                # Temporarily set running to allow cycle
                self.is_running = True
                
                # Check prerequisites
                if not self.ocr_reader and not self.initialize():
                    self.log("❌ Cannot run cycle - OCR not available")
                    self.is_running = False
                    return False
                
                # Run single cycle
                success = self._navigate_to_march_queue()
                if success:
                    self._analyze_march_queues()
                    self.log("✅ Force cycle completed successfully")
                    result = True
                else:
                    self.log("❌ Force cycle failed")
                    result = False
                
                self.is_running = False
                return result
            else:
                self.log("⚠️ AutoGather is already running, cannot force cycle")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in force cycle: {e}")
            self.is_running = False
            return False
    
    def update_config(self, **kwargs):
        """Update AutoGather configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    old_value = getattr(self.config, key)
                    setattr(self.config, key, value)
                    self.log(f"⚙️ Updated config: {key} = {value} (was: {old_value})")
                    
                    # Handle OCR directory changes
                    if key == 'save_ocr_images' and value:
                        os.makedirs(self.ocr_save_dir, exist_ok=True)
                        self.log(f"📁 Created OCR save directory: {self.ocr_save_dir}")
                    elif key == 'ocr_save_directory':
                        self.ocr_save_dir = os.path.join(value, self.instance_name)
                        if self.config.save_ocr_images:
                            os.makedirs(self.ocr_save_dir, exist_ok=True)
                            self.log(f"📁 Updated OCR save directory: {self.ocr_save_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Error updating config: {e}")
            return False
    
    # NEW: OCR image management methods
    def get_ocr_images_info(self) -> Dict:
        """Get information about saved OCR images"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            files = []
            total_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                    total_size += stat.st_size
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x['created'], reverse=True)
            
            return {
                "directory": self.ocr_save_dir,
                "total_files": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": files[:50]  # Limit to 50 most recent files
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_ocr_images(self, older_than_days: Optional[int] = None) -> Dict:
        """Clear OCR images (optionally only older than specified days)"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            deleted_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    # Check age if specified
                    if cutoff_time is not None:
                        file_time = os.path.getmtime(filepath)
                        if file_time >= cutoff_time:
                            continue  # Skip newer files
                    
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        self.log(f"⚠️ Could not delete OCR image {filename}: {e}")
            
            self.log(f"🧹 Cleared {deleted_count} OCR images ({deleted_size / (1024 * 1024):.2f} MB)")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # FIXED: Add debugging methods
    def debug_templates(self) -> Dict:
        """Debug template availability"""
        template_status = {}
        for name, path in self.templates.items():
            template_status[name] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0
            }
        return template_status
    
    def debug_instance_connection(self) -> Dict:
        """Debug MEmu instance connection"""
        try:
            # Test basic MEmu command
            cmd = [self.memu_path, "version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            version_ok = result.returncode == 0
            version_output = result.stdout if version_ok else result.stderr
            
            # Test instance list
            list_cmd = [self.memu_path, "listvms"]
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=10)
            
            list_ok = list_result.returncode == 0
            
            return {
                "memu_path": self.memu_path,
                "memu_exists": os.path.exists(self.memu_path),
                "version_command_ok": version_ok,
                "version_output": version_output,
                "list_command_ok": list_ok,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index,
                "list_output": list_result.stdout if list_ok else list_result.stderr
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "memu_path": self.memu_path,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index
            }
    
    def debug_screenshot(self) -> Dict:
        """Debug screenshot functionality"""
        try:
            self.log("🐛 Testing screenshot functionality...")
            
            screenshot_path = self._take_screenshot_with_retries()
            if screenshot_path:
                file_size = os.path.getsize(screenshot_path)
                self.log(f"✅ Screenshot test successful: {file_size} bytes")
                
                # Cleanup test screenshot
                self._cleanup_screenshot(screenshot_path)
                
                return {
                    "success": True,
                    "file_size": file_size,
                    "path": screenshot_path
                }
            else:
                self.log("❌ Screenshot test failed")
                return {"success": False, "error": "Screenshot failed"}
                
        except Exception as e:
            self.log(f"❌ Screenshot test error: {e}")
            return {"success": False, "error": str(e)}


# ENHANCED: Convenience functions for external use
def create_autogather_module(instance_name: str, shared_resources=None, console_callback=None) -> AutoGatherModule:
    """Create and return a configured AutoGather module"""
    return AutoGatherModule(instance_name, shared_resources, console_callback)


def test_autogather_prerequisites(instance_name: str, shared_resources=None) -> Dict:
    """Test if AutoGather can run for an instance"""
    try:
        # Create temporary module for testing
        module = AutoGatherModule(instance_name, shared_resources)
        
        # Test initialization
        init_success = module.initialize()
        
        # Test templates
        template_status = module.debug_templates()
        
        # Test instance connection
        connection_status = module.debug_instance_connection()
        
        # Test screenshot
        screenshot_status = module.debug_screenshot()
        
        # Test OCR image saving
        ocr_info = module.get_ocr_images_info()
        
        return {
            "instance_name": instance_name,
            "initialization": init_success,
            "templates": template_status,
            "connection": connection_status,
            "screenshot": screenshot_status,
            "ocr_images": ocr_info,
            "overall_ready": (init_success and 
                            connection_status.get("memu_exists", False) and
                            screenshot_status.get("success", False))
        }
        
    except Exception as e:
        return {
            "instance_name": instance_name,
            "error": str(e),
            "overall_ready": False
        }, text):  # 2540 -> 02:54:0 -> need to pad
                text = f"0{text[0]}:{text[1:3]}:0{text[3]}"
            
            # Handle partial matches like "02.4129" -> "02:41:29"
            partial_match = re.search(r'(\d{2})\.?(\d{4})', text)
            if partial_match:
                hours = partial_match.group(1)
                remaining = partial_match.group(2)
                if len(remaining) == 4:
                    minutes = remaining[:2]
                    seconds = remaining[2:]
                    text = f"{hours}:{minutes}:{seconds}"
            
            self.log(f"🕐 Timer text cleaning: '{original_text}' → '{text}'")
            
        elif "task" in text_type.lower():
            # ENHANCED: Task-specific cleaning with better gathering detection
            original_text = text
            
            # First, handle gathering variations (case-insensitive)
            gathering_patterns = [
                r'\bGath[ce]ring\b', r'\bGatherng\b', r'\bGathenng\b', r'\bGathcring\b',
                r'\bGathering\b', r'\bGathring\b', r'\bGatheing\b', r'\bGathening\b',
                r'\bGathcnng\b', r'\bGathcrng\b', r'\bGathermg\b', r'\bGatherinq\b'
            ]
            
            for pattern in gathering_patterns:
                text = re.sub(pattern, 'Gathering', text, flags=re.IGNORECASE)
            
            # Enhanced character-level fixes for tasks
            fixes = {
                # Idle variations
                '31d1e': 'Idle', '3ldle': 'Idle', 'B1d1e': 'Idle', 'Bldlc': 'Idle',
                '3idle': 'Idle', 'bidle': 'Idle', 'ldle': 'Idle', 'idle': 'Idle',
                'id1e': 'Idle', '1dle': 'Idle', 'id1c': 'Idle', 'idl3': 'Idle',
                
                # Building types
                'Milll': 'Mill', 'Mi11': 'Mill', 'MiII': 'Mill', 'MilI': 'Mill',
                'Mill1': 'Mill', 'Mil1': 'Mill', 'Mi1l': 'Mill',
                'Lumbcryard': 'Lumberyard', 'Lumberyd': 'Lumberyard', 'Lumberyrd': 'Lumberyard',
                'Lumberyard1': 'Lumberyard', 'Lumberyand': 'Lumberyard', 'Lumbcryard': 'Lumberyard',
                
                # Level indicators
                'Lv ': 'Lv. ', 'Ly': 'Lv.', 'LV': 'Lv.', 'Lv.': 'Lv. ',
                'Level': 'Lv. ', 'lvl': 'Lv. ', 'LVL': 'Lv. ',
                
                # Common OCR mistakes
                'Qucuc': 'Queue', 'Queueu': 'Queue', 'Qucue': 'Queue',
                'Oueve': 'Queue', 'Qucve': 'Queue', 'Qucuu': 'Queue'
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
            
            # Clean up level format (Lv.7ldlc -> Lv. 7)
            text = re.sub(r'Lv\.?\s*(\d+)[a-zA-Z]+', r'Lv. \1', text)
            
            # Detect gathering task pattern and extract useful info
            if 'Gathering' in text:
                # Try to extract level and resource type
                level_match = re.search(r'Lv\.?\s*(\d+)', text)
                resource_match = re.search(r'(Mill|Lumberyard|Farm|Mine|Quarry)', text, re.IGNORECASE)
                
                level = level_match.group(1) if level_match else "?"
                resource = resource_match.group(1) if resource_match else "Resource"
                
                # Create clean format
                text = f"Gathering Lv. {level} {resource}"
            
            self.log(f"📋 Task text cleaning: '{original_text}' → '{text}'")
                
        elif "status" in text_type.lower():
            # ENHANCED: Status-specific cleaning
            original_text = text
            
            fixes = {
                # Unlock variations
                'Un10ck': 'Unlock', 'UnI0ck': 'Unlock', 'unl0ck': 'Unlock', 'Unl0ck': 'Unlock',
                'Unl0ck': 'Unlock', 'Un1ock': 'Unlock', 'UnIock': 'Unlock',
                
                # Cannot use variations
                'Cannol': 'Cannot', 'Cann0t': 'Cannot', 'Canot': 'Cannot', 'Can not': 'Cannot',
                'cannolust': 'Cannot use', 'Cannot uSC': 'Cannot use', 'cannot usc': 'Cannot use',
                'Cannot uSc': 'Cannot use', 'Cann0t use': 'Cannot use', 'Cannot u5e': 'Cannot use',
                'Cannot u5c': 'Cannot use', 'cannol use': 'Cannot use', 'Cannol uSc': 'Cannot use',
                
                # Use variations
                'usc': 'use', 'u5c': 'use', 'u5e': 'use', 'uSc': 'use', 'u5C': 'use',
                'uSe': 'use', 'uce': 'use', 'u5E': 'use',
                
                # Idle variations
                'Idlc': 'Idle', 'Id1e': 'Idle', '1dle': 'Idle', 'id1c': 'Idle',
                'idlc': 'Idle', 'id1e': 'Idle', 'idl3': 'Idle', '1d1e': 'Idle'
            }
            
            for mistake, fix in fixes.items():
                text = text.replace(mistake, fix)
            
            self.log(f"📊 Status text cleaning: '{original_text}' → '{text}'")
        
        # Clean up spacing and punctuation
        text = ' '.join(text.split())
        text = text.replace(' .', '.').replace('. ', '.')
        text = text.replace(' :', ':').replace(': ', ':')
        
        return text.strip()
    
    def _determine_queue_availability(self, queue_num: int, queue_info: QueueInfo) -> bool:
        """FIXED: Determine queue availability with better logic"""
        try:
            if queue_num <= 2:
                # For queues 1-2, check timer
                if queue_info.time_remaining:
                    # Check for idle indicators
                    idle_keywords = ['idle', 'idlc', 'id1e', '1dle', 'id1c']
                    if any(keyword in queue_info.time_remaining.lower() for keyword in idle_keywords):
                        queue_info.status = "Available (Idle)"
                        return True
                    elif re.search(r'\d{1,2}:\d{2}:\d{2}', queue_info.time_remaining):
                        queue_info.status = "Busy (Gathering)"
                        return False
                    else:
                        queue_info.status = "Unknown"
                        return False
                else:
                    # No timer detected - might be available
                    queue_info.status = "Possibly Available"
                    return True
                    
            else:
                # For queues 3-6, check status text
                if not queue_info.status:
                    # No status detected - assume available if queue exists
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['idle', 'available']):
                    queue_info.status = "Available"
                    return True
                elif any(keyword in queue_info.status.lower() for keyword in ['unlock', 'cannot', 'locked']):
                    return False
                else:
                    # Unknown status - be conservative
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error determining availability for Queue {queue_num}: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: Optional[str]):
        """FIXED: Safe screenshot cleanup"""
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception as e:
                self.log(f"⚠️ Could not cleanup screenshot {screenshot_path}: {e}")
    
    # ENHANCED: Better status and control methods with OCR image info
    def get_status(self) -> Dict:
        """Get current AutoGather status"""
        ocr_image_count = 0
        ocr_image_size = 0
        
        if os.path.exists(self.ocr_save_dir):
            try:
                files = os.listdir(self.ocr_save_dir)
                ocr_image_count = len([f for f in files if f.endswith('.png')])
                ocr_image_size = sum(os.path.getsize(os.path.join(self.ocr_save_dir, f)) 
                                   for f in files if os.path.isfile(os.path.join(self.ocr_save_dir, f)))
            except:
                pass
        
        return {
            "running": self.is_running,
            "instance_name": self.instance_name,
            "instance_index": self.instance_index,
            "memu_path": self.memu_path,
            "ocr_available": self.ocr_reader is not None,
            "templates_available": all(os.path.exists(path) for path in self.templates.values()),
            "queue_count": len(self.queues),
            "available_queues": len([q for q in self.queues.values() if q.is_available]),
            "ocr_image_saving": self.config.save_ocr_images,
            "ocr_save_directory": self.ocr_save_dir,
            "ocr_image_count": ocr_image_count,
            "ocr_image_size_mb": round(ocr_image_size / (1024 * 1024), 2)
        }
    
    def force_cycle(self) -> bool:
        """Force a single AutoGather cycle (for testing)"""
        try:
            if not self.is_running:
                self.log("🎯 Force running single AutoGather cycle...")
                
                # Temporarily set running to allow cycle
                self.is_running = True
                
                # Check prerequisites
                if not self.ocr_reader and not self.initialize():
                    self.log("❌ Cannot run cycle - OCR not available")
                    self.is_running = False
                    return False
                
                # Run single cycle
                success = self._navigate_to_march_queue()
                if success:
                    self._analyze_march_queues()
                    self.log("✅ Force cycle completed successfully")
                    result = True
                else:
                    self.log("❌ Force cycle failed")
                    result = False
                
                self.is_running = False
                return result
            else:
                self.log("⚠️ AutoGather is already running, cannot force cycle")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in force cycle: {e}")
            self.is_running = False
            return False
    
    def update_config(self, **kwargs):
        """Update AutoGather configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    old_value = getattr(self.config, key)
                    setattr(self.config, key, value)
                    self.log(f"⚙️ Updated config: {key} = {value} (was: {old_value})")
                    
                    # Handle OCR directory changes
                    if key == 'save_ocr_images' and value:
                        os.makedirs(self.ocr_save_dir, exist_ok=True)
                        self.log(f"📁 Created OCR save directory: {self.ocr_save_dir}")
                    elif key == 'ocr_save_directory':
                        self.ocr_save_dir = os.path.join(value, self.instance_name)
                        if self.config.save_ocr_images:
                            os.makedirs(self.ocr_save_dir, exist_ok=True)
                            self.log(f"📁 Updated OCR save directory: {self.ocr_save_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Error updating config: {e}")
            return False
    
    # NEW: OCR image management methods
    def get_ocr_images_info(self) -> Dict:
        """Get information about saved OCR images"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            files = []
            total_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                    total_size += stat.st_size
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x['created'], reverse=True)
            
            return {
                "directory": self.ocr_save_dir,
                "total_files": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": files[:50]  # Limit to 50 most recent files
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_ocr_images(self, older_than_days: Optional[int] = None) -> Dict:
        """Clear OCR images (optionally only older than specified days)"""
        try:
            if not os.path.exists(self.ocr_save_dir):
                return {"error": "OCR save directory does not exist"}
            
            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            deleted_size = 0
            
            for filename in os.listdir(self.ocr_save_dir):
                filepath = os.path.join(self.ocr_save_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    # Check age if specified
                    if cutoff_time is not None:
                        file_time = os.path.getmtime(filepath)
                        if file_time >= cutoff_time:
                            continue  # Skip newer files
                    
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        self.log(f"⚠️ Could not delete OCR image {filename}: {e}")
            
            self.log(f"🧹 Cleared {deleted_count} OCR images ({deleted_size / (1024 * 1024):.2f} MB)")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # FIXED: Add debugging methods
    def debug_templates(self) -> Dict:
        """Debug template availability"""
        template_status = {}
        for name, path in self.templates.items():
            template_status[name] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0
            }
        return template_status
    
    def debug_instance_connection(self) -> Dict:
        """Debug MEmu instance connection"""
        try:
            # Test basic MEmu command
            cmd = [self.memu_path, "version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            version_ok = result.returncode == 0
            version_output = result.stdout if version_ok else result.stderr
            
            # Test instance list
            list_cmd = [self.memu_path, "listvms"]
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=10)
            
            list_ok = list_result.returncode == 0
            
            return {
                "memu_path": self.memu_path,
                "memu_exists": os.path.exists(self.memu_path),
                "version_command_ok": version_ok,
                "version_output": version_output,
                "list_command_ok": list_ok,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index,
                "list_output": list_result.stdout if list_ok else list_result.stderr
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "memu_path": self.memu_path,
                "instance_name": self.instance_name,
                "instance_index": self.instance_index
            }
    
    def debug_screenshot(self) -> Dict:
        """Debug screenshot functionality"""
        try:
            self.log("🐛 Testing screenshot functionality...")
            
            screenshot_path = self._take_screenshot_with_retries()
            if screenshot_path:
                file_size = os.path.getsize(screenshot_path)
                self.log(f"✅ Screenshot test successful: {file_size} bytes")
                
                # Cleanup test screenshot
                self._cleanup_screenshot(screenshot_path)
                
                return {
                    "success": True,
                    "file_size": file_size,
                    "path": screenshot_path
                }
            else:
                self.log("❌ Screenshot test failed")
                return {"success": False, "error": "Screenshot failed"}
                
        except Exception as e:
            self.log(f"❌ Screenshot test error: {e}")
            return {"success": False, "error": str(e)}


# ENHANCED: Convenience functions for external use
def create_autogather_module(instance_name: str, shared_resources=None, console_callback=None) -> AutoGatherModule:
    """Create and return a configured AutoGather module"""
    return AutoGatherModule(instance_name, shared_resources, console_callback)


def test_autogather_prerequisites(instance_name: str, shared_resources=None) -> Dict:
    """Test if AutoGather can run for an instance"""
    try:
        # Create temporary module for testing
        module = AutoGatherModule(instance_name, shared_resources)
        
        # Test initialization
        init_success = module.initialize()
        
        # Test templates
        template_status = module.debug_templates()
        
        # Test instance connection
        connection_status = module.debug_instance_connection()
        
        # Test screenshot
        screenshot_status = module.debug_screenshot()
        
        # Test OCR image saving
        ocr_info = module.get_ocr_images_info()
        
        return {
            "instance_name": instance_name,
            "initialization": init_success,
            "templates": template_status,
            "connection": connection_status,
            "screenshot": screenshot_status,
            "ocr_images": ocr_info,
            "overall_ready": (init_success and 
                            connection_status.get("memu_exists", False) and
                            screenshot_status.get("success", False))
        }
        
    except Exception as e:
        return {
            "instance_name": instance_name,
            "error": str(e),
            "overall_ready": False
        }