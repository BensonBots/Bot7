"""
auto_gather.py - AutoGather module with template matching fallback fixes
Restored to original working structure with only the fallback enhancements
"""

import cv2
import numpy as np
import time
import os
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from march_queue_analyzer import MarchQueueAnalyzer, QueueInfo


@dataclass 
class GatherConfig:
    """Configuration for auto gather module"""
    template_matching_threshold: float = 0.5  # Lowered from 0.6 for better reliability
    screenshot_timeout: int = 10
    cycle_delay: int = 19  # 19 second delay between cycles
    max_retries: int = 3
    enable_simple_navigation: bool = True


class AutoGatherModule:
    """AutoGather module with enhanced template matching fallback"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        self.instance_name = instance_name
        self.shared_resources = shared_resources
        self.console_callback = console_callback or print
        
        # Configuration
        self.config = GatherConfig()
        
        # State management
        self.is_running = False
        self.worker_thread = None
        self.stop_event = threading.Event()
        
        # Template paths
        self.templates = {
            'open_left': 'templates/open_left.png',
            'wilderness_button': 'templates/wilderness_button.png'
        }
        
        # Get instance info
        self.instance_index = self._get_instance_index()
        
        # Initialize march queue analyzer
        self.march_analyzer = MarchQueueAnalyzer(instance_name, self.config, self.log_message)
        
        self.log_message(f"✅ AutoGather module initialized for {instance_name} (SIMPLE NAVIGATION)")
    
    def _get_instance_index(self) -> Optional[int]:
        """Get the MEmu instance index"""
        try:
            instances = self.shared_resources.instance_manager.instances
            for instance in instances:
                if instance.name == self.instance_name:
                    self.log_message(f"✅ Found instance index: {instance.index}")
                    return instance.index
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
        """Start the AutoGather module"""
        if self.is_running:
            self.log_message("⚠️ AutoGather already running")
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
        """Stop the AutoGather module"""
        if not self.is_running:
            return
        
        self.log_message("🛑 Stopping AutoGather...")
        self.is_running = False
        self.stop_event.set()
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        self.log_message("✅ AutoGather stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        self.log_message("🔄 AutoGather worker loop started")
        cycle_count = 1
        retry_count = 0
        max_retries = self.config.max_retries
        
        while self.is_running and not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                # Perform navigation and analysis
                success = self._perform_simple_navigation()
                
                elapsed_time = time.time() - start_time
                
                if success:
                    self.log_message(f"✅ AutoGather cycle {cycle_count} completed (took {elapsed_time:.1f}s)")
                    cycle_count += 1
                    retry_count = 0  # Reset retry count on success
                else:
                    retry_count += 1
                    self.log_message(f"❌ AutoGather cycle {cycle_count + retry_count - 1} failed (retry {retry_count}/{max_retries})")
                    
                    if retry_count >= max_retries:
                        self.log_message("🛑 AutoGather max retries exceeded, stopping module")
                        break
                
                # Wait before next cycle
                if self.is_running:
                    for _ in range(self.config.cycle_delay):
                        if self.stop_event.wait(1):
                            break
                
            except Exception as e:
                self.log_message(f"❌ Error in worker loop: {e}")
                break
        
        self.is_running = False
        self.log_message("🏁 AutoGather worker loop ended")
    
    def _perform_simple_navigation(self) -> bool:
        """Perform simple navigation sequence with enhanced template matching"""
        try:
            self.log_message("📋 Starting simple navigation sequence...")
            
            # Step 1: Click open_left button with fallback
            self.log_message("🔄 Step 1: Clicking open_left button")
            if not self._click_open_left():
                self.log_message("❌ Failed to click open_left")
                return False
            
            # Step 2: Wait for left panel to open
            self.log_message("⏳ Step 2: Waiting 1 second for left panel to open")
            time.sleep(1)
            
            # Step 3: Click wilderness button with fallback
            self.log_message("🌲 Step 3: Clicking wilderness button")
            if not self._click_wilderness_button():
                self.log_message("❌ Failed to click wilderness button")
                return False
            
            # Step 4: Wait for march queue to load
            self.log_message("⏳ Step 4: Waiting 3 seconds for march queue to load")
            time.sleep(3)
            
            # Step 5: Perform OCR analysis
            self.log_message("🔍 Step 5: Starting OCR analysis")
            queues = self._analyze_march_queues()
            
            if queues:
                available_count = len([q for q in queues.values() if q.is_available])
                self.log_message(f"✅ OCR complete: {len(queues)} queues analyzed, {available_count} available")
            else:
                self.log_message("❌ OCR analysis failed")
                return False
            
            self.log_message("✅ Simple navigation completed successfully")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error in simple navigation: {e}")
            return False
    
    def _click_open_left(self) -> bool:
        """Take screenshot and click open_left button with fallback"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Try template matching first
                template_path = self.templates.get('open_left')
                if template_path and os.path.exists(template_path):
                    
                    screenshot = cv2.imread(screenshot_path)
                    template = cv2.imread(template_path)
                    
                    if screenshot is not None and template is not None:
                        # Template matching
                        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        
                        self.log_message(f"🔍 open_left confidence: {max_val:.3f} (threshold: {self.config.template_matching_threshold})")
                        
                        if max_val >= self.config.template_matching_threshold:
                            template_height, template_width = template.shape[:2]
                            click_x = max_loc[0] + template_width // 2
                            click_y = max_loc[1] + template_height // 2
                            
                            self.log_message(f"✅ open_left found at ({click_x}, {click_y})")
                            self.log_message(f"👆 Clicking open_left at ({click_x}, {click_y})")
                            
                            # Click the position
                            if self._click_position(click_x, click_y, "open_left"):
                                self.log_message("✅ Successfully clicked open_left")
                                return True
                
                # If template matching fails, try fallback positions
                self.log_message("⚠️ Template matching failed, trying fallback positions")
                
                # Common positions for open_left button (from your logs)
                fallback_positions = [
                    (22, 344),   # Your most common position
                    (20, 340),   # Slight variation
                    (25, 348),   # Slight variation
                    (22, 350),   # Lower variation
                    (18, 344),   # Left variation
                ]
                
                for i, (x, y) in enumerate(fallback_positions):
                    self.log_message(f"🎯 Trying fallback position {i+1}: ({x}, {y})")
                    
                    if self._click_position(x, y, f"open_left_fallback_{i+1}"):
                        # Wait a moment to see if it worked
                        time.sleep(0.5)
                        self.log_message(f"✅ Fallback position {i+1} clicked successfully")
                        return True
                
                self.log_message("❌ All fallback positions failed")
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception as e:
            self.log_message(f"❌ Error in enhanced open_left click: {e}")
            return False
    
    def _click_wilderness_button(self) -> bool:
        """Take screenshot and click wilderness_button with fallback"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Try template matching first
                if self._click_template(screenshot_path, 'wilderness_button'):
                    return True
                
                # If template matching fails, try fallback positions
                self.log_message("⚠️ Wilderness button template matching failed, trying fallback positions")
                
                # Common positions for wilderness button
                fallback_positions = [
                    (225, 170),   # Your successful position
                    (220, 170),   # Slight left
                    (230, 170),   # Slight right
                    (225, 165),   # Slight up
                    (225, 175),   # Slight down
                ]
                
                for i, (x, y) in enumerate(fallback_positions):
                    self.log_message(f"🎯 Trying wilderness fallback position {i+1}: ({x}, {y})")
                    
                    if self._click_position(x, y, f"wilderness_fallback_{i+1}"):
                        time.sleep(1)
                        self.log_message(f"✅ Wilderness fallback position {i+1} clicked successfully")
                        return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception as e:
            self.log_message(f"❌ Error in enhanced wilderness click: {e}")
            return False
    
    def _click_template(self, screenshot_path: str, template_key: str) -> bool:
        """Click template using template matching"""
        try:
            template_path = self.templates.get(template_key)
            if not template_path or not os.path.exists(template_path):
                self.log_message(f"❌ Template not found: {template_key}")
                return False
            
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                self.log_message(f"❌ Failed to load images for {template_key}")
                return False
            
            # Template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            self.log_message(f"🔍 {template_key} confidence: {max_val:.3f} (threshold: {self.config.template_matching_threshold})")
            
            if max_val >= self.config.template_matching_threshold:
                template_height, template_width = template.shape[:2]
                click_x = max_loc[0] + template_width // 2
                click_y = max_loc[1] + template_height // 2
                
                self.log_message(f"✅ {template_key} found at ({click_x}, {click_y})")
                self.log_message(f"👆 Clicking {template_key} at ({click_x}, {click_y})")
                
                # Click the position
                if self._click_position(click_x, click_y, template_key):
                    self.log_message(f"✅ Successfully clicked {template_key}")
                    return True
            else:
                self.log_message(f"❌ {template_key} confidence too low: {max_val:.3f}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error clicking template {template_key}: {e}")
            return False
    
    def _click_position(self, x: int, y: int, element_name: str) -> bool:
        """Click at specific coordinates"""
        try:
            if not self.instance_index:
                self.log_message("❌ No instance index available")
                return False
            
            # Use shared resources to click position
            if hasattr(self.shared_resources.instance_manager, 'click_position'):
                success = self.shared_resources.instance_manager.click_position(
                    self.instance_name, x, y
                )
                return success
            else:
                # Fallback to ADB
                adb_port = 5555 + (self.instance_index - 1) * 10
                cmd = f'adb -s 127.0.0.1:{adb_port} shell input tap {x} {y}'
                
                import subprocess
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                return result.returncode == 0
                
        except Exception as e:
            self.log_message(f"❌ Error clicking position: {e}")
            return False
    
    def _take_screenshot(self) -> Optional[str]:
        """Take screenshot and return path"""
        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = "screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate screenshot filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshots_dir, f"{self.instance_name}_{timestamp}.png")
            
            # Use shared resources to take screenshot
            if hasattr(self.shared_resources.instance_manager, 'take_screenshot'):
                success = self.shared_resources.instance_manager.take_screenshot(
                    self.instance_name, screenshot_path
                )
            else:
                # Fallback method
                success = self._take_screenshot_fallback(screenshot_path)
            
            if success and os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                self.log_message(f"📸 Screenshot taken ({file_size} bytes)")
                return screenshot_path
            else:
                self.log_message("❌ Screenshot failed")
                return None
                
        except Exception as e:
            self.log_message(f"❌ Error taking screenshot: {e}")
            return None
    
    def _take_screenshot_fallback(self, screenshot_path: str) -> bool:
        """Fallback screenshot method using ADB"""
        try:
            if not self.instance_index:
                return False
            
            # Use ADB to take screenshot
            adb_port = 5555 + (self.instance_index - 1) * 10
            adb_cmd = f'adb -s 127.0.0.1:{adb_port} shell screencap -p'
            
            import subprocess
            result = subprocess.run(adb_cmd, shell=True, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                # Save screenshot
                with open(screenshot_path, 'wb') as f:
                    f.write(result.stdout.replace(b'\r\n', b'\n'))
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Fallback screenshot error: {e}")
            return False
    
    def _cleanup_screenshot(self, screenshot_path: str):
        """Clean up screenshot file"""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            self.log_message(f"⚠️ Could not clean up screenshot: {e}")
    
    def _analyze_march_queues(self) -> Dict[int, QueueInfo]:
        """Analyze march queues using OCR"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return {}
            
            try:
                # Analyze using march queue analyzer
                queues = self.march_analyzer.analyze_march_queues(screenshot_path)
                return queues
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Error analyzing march queues: {e}")
            return {}