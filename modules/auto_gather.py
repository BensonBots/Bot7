"""
BENSON v2.0 - AutoGather Module (Production Ready)
Handles automatic resource gathering with PaddleOCR integration
"""

import os
import time
import cv2
import threading
import subprocess
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import re
from datetime import datetime


class AutoGather:
    """AutoGather module for automatic resource collection"""
    
    def __init__(self, instance_name: str, instance_index: int, ocr, adb_utils, logger=None, log_callback=None, debug_mode: bool = False, verbose_logging: bool = False):
        self.instance_name = instance_name
        self.instance_index = instance_index
        self.ocr = ocr
        self.adb_utils = adb_utils
        self.logger = log_callback or logger
        self.debug_mode = debug_mode
        self.verbose_logging = verbose_logging
        self.running = False
        self.worker_thread = None
        self.cycle_count = 0
        
        # AutoGather settings
        self.settings = self._load_settings()
        
        # Initialize templates directory
        self.templates_dir = os.path.join(os.getcwd(), "templates")
        if not os.path.exists(self.templates_dir):
            self.log_message(f"❌ Templates directory not found: {self.templates_dir}")
        
        # Template categories
        self.NAVIGATION_TEMPLATES = ["open_left.png", "close_left.png", "wilderness_button.png"]
        self.GATHER_TEMPLATES = ["gather_button.png", "deploy_button.png", "search_button.png", "searchrss_button.png"]
        self.RESOURCE_TEMPLATES = ["wood_icon.png", "stone_icon.png", "iron_icon.png", "bread_icon.png"]
        self.CLOSE_TEMPLATES = ["close_x.png", "close_x2.png", "close_x3.png", "close_x4.png", "close_x5.png", "close_x6.png"]
        
        # Resource icon mappings
        self.RESOURCE_ICONS = {
            "food": "bread_icon.png",
            "wood": "wood_icon.png", 
            "stone": "stone_icon.png",
            "iron": "iron_icon.png"
        }
        
        self.log_message(f"✅ AutoGather initialized for {instance_name}")
        self.log_message(f"📋 Settings: {self.settings}")

    def _load_settings(self) -> Dict[str, Any]:
        """Load AutoGather settings"""
        default_settings = {
            'resource_loop': ['food', 'wood', 'stone', 'iron'],
            'current_index': 0,
            'max_queues': 6,
            'enabled': True
        }
        return default_settings
    
    def _get_next_resource(self) -> str:
        """Get next resource from the loop"""
        resources = self.settings['resource_loop']
        if not resources:
            return 'food'
        
        resource = resources[self.settings['current_index'] % len(resources)]
        self.settings['current_index'] += 1
        return resource

    def log_message(self, message: str) -> None:
        """Log a message with timestamp - only important messages shown"""
        if self.logger:
            self.logger(message)
        else:
            # Only show important status messages, not debug/verbose info
            if any(keyword in message for keyword in [
                '✅ AutoGather initialized',
                '🚀 Starting AutoGather',
                '🔄 AutoGather worker loop started', 
                '🌾 Starting AutoGather cycle',
                '✅ Gather cycle completed',
                '❌ Gather cycle failed',
                '⏳ Waiting 60s',
                '🛑 Stopping AutoGather',
                '📊 March Analysis:',
                '📈 Total march queues detected:',
                '🌾 Gathering:',
                '🔄 Returning:',
                '⚔️ Attack/Rally:',
                '💤 Idle:',
                '🔒 Locked/Cannot Use:',
                '⏳ Waiting:',
                '🎯 Resources:',
                '❌ Failed to'
            ]):
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {message}")

    def start(self) -> None:
        """Start the AutoGather worker"""
        if self.running:
            self.log_message("⚠️ AutoGather already running")
            return
        
        self.running = True
        self.cycle_count = 0
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.log_message("🚀 Starting AutoGather...")

    def stop(self) -> None:
        """Stop the AutoGather worker"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        self.log_message("🛑 Stopping AutoGather...")

    def _worker_loop(self) -> None:
        """Main worker loop for AutoGather"""
        self.log_message("🔄 AutoGather worker loop started")
        
        while self.running:
            try:
                self.cycle_count += 1
                self.log_message(f"🌾 Starting AutoGather cycle {self.cycle_count}")
                
                if self._perform_gather_cycle():
                    self.log_message("✅ Gather cycle completed successfully")
                else:
                    self.log_message("❌ Gather cycle failed")
                
                # Wait 60 seconds before next cycle
                self.log_message("⏳ Waiting 60s before next cycle...")
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_message(f"❌ Worker loop error: {e}")
                time.sleep(30)

    def _perform_gather_cycle(self) -> bool:
        """Perform a single gather cycle"""
        try:
            # Check if gathering is needed
            march_texts = self._perform_ocr_detection()
            march_analysis = self._analyze_march_data(march_texts)
            
            if march_texts:
                self._log_march_analysis(march_analysis)
            
            # Calculate deployment plan
            idle_queues = self._find_idle_queues_from_analysis(march_analysis)
            active_queues = march_analysis.get('gathering_marches', 0)
            available_slots = self.settings['max_queues'] - active_queues
            marches_to_deploy = min(available_slots, len(idle_queues))
            
            if marches_to_deploy <= 0:
                # No deployment needed - just monitor
                return True
            
            self.log_message(f"🚀 Deploying {marches_to_deploy} march(es) to queues: {idle_queues[:marches_to_deploy]}")
            
            # Navigate to world view for gathering
            if not self._navigate_to_world_view():
                self.log_message("❌ Failed to navigate to world view")
                return False
            
            # Execute deployments
            return self._execute_march_deployments(idle_queues[:marches_to_deploy])
            
        except Exception as e:
            self.log_message(f"❌ Gather cycle error: {e}")
            return False

    def _find_idle_queues_from_analysis(self, analysis: Dict[str, Any]) -> List[int]:
        """Find idle queue numbers from march analysis"""
        idle_queues = []
        for march in analysis.get('march_details', []):
            if march.get('type') == 'idle':
                queue_num = march.get('queue_number')
                if queue_num:
                    idle_queues.append(queue_num)
        return sorted(idle_queues)

    def _navigate_to_world_view(self) -> bool:
        """Navigate to world view for gathering"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Check if we're already in world view
                if self._template_exists(screenshot_path, "world_icon.png", threshold=0.8):
                    # We're in town view, need to click world icon to go to world view
                    if self._click_template_if_found(screenshot_path, "world_icon.png", threshold=0.8):
                        time.sleep(2)
                        
                        # Verify we're now in world view by checking for town icon
                        new_screenshot = self._take_screenshot()
                        if new_screenshot:
                            try:
                                if self._template_exists(new_screenshot, "town_icon.png", threshold=0.8):
                                    return True
                                else:
                                    self.log_message("❌ Failed to verify world view (no town icon)")
                                    return False
                            finally:
                                self._cleanup_screenshot(new_screenshot)
                    else:
                        self.log_message("❌ Failed to click world icon")
                        return False
                
                elif self._template_exists(screenshot_path, "town_icon.png", threshold=0.8):
                    # Already in world view
                    return True
                else:
                    self.log_message("❌ Cannot determine current view state")
                    return False
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception as e:
            self.log_message(f"❌ Navigation to world view error: {e}")
            return False

    def _execute_march_deployments(self, idle_queues: List[int]) -> bool:
        """Execute march deployments"""
        try:
            success_count = 0
            is_first_march = True
            
            for i, queue_number in enumerate(idle_queues):
                resource_type = self._get_next_resource()
                
                self.log_message(f"🚀 Deploying {resource_type} on Queue {queue_number} ({i+1}/{len(idle_queues)})")
                
                if is_first_march:
                    march_success = self._start_first_march(resource_type, queue_number)
                    is_first_march = False
                else:
                    march_success = self._start_subsequent_march(resource_type, queue_number)
                
                if march_success:
                    success_count += 1
                    self.log_message(f"✅ Deployed {resource_type} on Queue {queue_number}")
                else:
                    self.log_message(f"❌ Failed to deploy {resource_type} on Queue {queue_number}")
            
            self.log_message(f"📊 Deployment summary: {success_count}/{len(idle_queues)} successful")
            return success_count > 0
            
        except Exception as e:
            self.log_message(f"❌ Error executing deployments: {e}")
            return False

    def _start_first_march(self, resource_type: str, queue_number: int) -> bool:
        """Start the first march (with full navigation)"""
        try:
            return self._execute_gathering_sequence(resource_type, queue_number)
        except Exception as e:
            self.log_message(f"❌ Error starting first march: {e}")
            return False

    def _start_subsequent_march(self, resource_type: str, queue_number: int) -> bool:
        """Start subsequent march (already in world view)"""
        try:
            time.sleep(1)
            return self._execute_gathering_sequence(resource_type, queue_number)
        except Exception as e:
            self.log_message(f"❌ Error starting subsequent march: {e}")
            return False

    def _execute_gathering_sequence(self, resource_type: str, queue_number: int) -> bool:
        """Execute the complete gathering sequence"""
        try:
            return (self._click_search_and_dismiss_popup() and
                    self._perform_scroll_to_reveal_resources() and
                    self._select_resource_type(resource_type) and
                    self._set_max_level_and_search() and
                    self._deploy_march())
        except Exception as e:
            self.log_message(f"❌ Error in gathering sequence: {e}")
            return False

    def _navigate_to_march_queue(self) -> bool:
        """Navigate to march queue interface"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False

            try:
                # Check if left panel needs to be opened
                if self._template_exists(screenshot_path, "open_left.png", threshold=0.7):
                    if self._click_template_if_found(screenshot_path, "open_left.png", threshold=0.7):
                        time.sleep(2)
                        
                        # Take new screenshot
                        new_screenshot = self._take_screenshot()
                        if new_screenshot:
                            self._cleanup_screenshot(screenshot_path)
                            screenshot_path = new_screenshot
                
                # Look for wilderness button
                if self._click_template_if_found(screenshot_path, "wilderness_button.png", threshold=0.8):
                    time.sleep(2)
                    
                    # Take new screenshot to verify
                    new_screenshot = self._take_screenshot()
                    if new_screenshot:
                        try:
                            if self._template_exists(new_screenshot, "close_left.png", threshold=0.8):
                                return True
                            else:
                                return False
                        finally:
                            self._cleanup_screenshot(new_screenshot)
                else:
                    return False
                    
            finally:
                self._cleanup_screenshot(screenshot_path)
            
            return False
                
        except Exception as e:
            self.log_message(f"❌ Navigation error: {e}")
            return False

    def _perform_ocr_detection(self) -> List[str]:
        """Perform OCR detection on march queue region to find text-based march information"""
        detected_texts = []
        
        try:
            if not self.ocr:
                return detected_texts
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return detected_texts
            
            try:
                img = cv2.imread(screenshot_path)
                if img is None:
                    return detected_texts
                
                # OCR region coordinates
                march_queue_x1 = 63
                march_queue_y1 = 195
                march_queue_x2 = 247
                march_queue_y2 = 484
                
                # Ensure crop region is within image bounds
                img_height, img_width = img.shape[:2]
                
                crop_x1 = max(0, march_queue_x1)
                crop_y1 = max(0, march_queue_y1)
                crop_x2 = min(img_width, march_queue_x2)
                crop_y2 = min(img_height, march_queue_y2)
                
                if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
                    return detected_texts
                
                cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]
                
                if cropped_img.size == 0:
                    return detected_texts
                
                # Only save debug image if debug mode is enabled
                if self.debug_mode:
                    debug_crop_path = f"debug_crop_{self.instance_name}_{int(time.time())}.png"
                    cv2.imwrite(debug_crop_path, cropped_img)
                
                result = self.ocr.ocr(cropped_img)
                
                if result and len(result) > 0:
                    ocr_data = result[0]
                    
                    if isinstance(ocr_data, dict):
                        if 'rec_texts' in ocr_data and 'rec_scores' in ocr_data:
                            texts = ocr_data['rec_texts']
                            scores = ocr_data['rec_scores']
                            
                            for i, (text, confidence) in enumerate(zip(texts, scores)):
                                text = text.strip()
                                
                                if self._is_march_related_text(text):
                                    detected_texts.append(text)
                    
                    elif isinstance(ocr_data, list):
                        for line_result in ocr_data:
                            if line_result and len(line_result) >= 2:
                                text_info = line_result[1]
                                if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                                    text = text_info[0].strip()
                                    
                                    if self._is_march_related_text(text):
                                        detected_texts.append(text)
                    
            except Exception:
                pass
            finally:
                self._cleanup_screenshot(screenshot_path)
        
        except Exception:
            pass
        
        return detected_texts

    def _analyze_march_data(self, march_texts: List[str]) -> Dict[str, Any]:
        """Analyze detected march texts to extract meaningful information"""
        analysis = {
            'total_queues': 0,
            'gathering_marches': 0,
            'returning_marches': 0,
            'attack_marches': 0,
            'idle_marches': 0,
            'waiting_marches': 0,
            'locked_marches': 0,
            'resource_types': set(),
            'march_details': []
        }
        
        queue_data = {}
        current_queue = None
        
        for i, text in enumerate(march_texts):
            text_lower = text.lower().strip()
            
            queue_match = re.search(r'march queue (\d+)', text_lower)
            if queue_match:
                queue_num = int(queue_match.group(1))
                current_queue = queue_num
                if queue_num not in queue_data:
                    queue_data[queue_num] = {'queue_text': text, 'status': None, 'time': None, 'additional_info': []}
            
            elif any(keyword in text_lower for keyword in ['gathering', 'returning', 'attack', 'rally', 'waiting', 'go to']):
                if current_queue and current_queue in queue_data:
                    queue_data[current_queue]['status'] = text
                else:
                    inferred_queue = (i // 2) + 1
                    if inferred_queue and inferred_queue not in queue_data and 1 <= inferred_queue <= 6:
                        queue_data[inferred_queue] = {'queue_text': f'March Queue {inferred_queue}', 'status': text, 'time': None, 'additional_info': []}
                    elif inferred_queue and inferred_queue in queue_data:
                        queue_data[inferred_queue]['status'] = text
            
            elif re.search(r'\d+:\d+:\d+', text) or re.search(r'\d+:\d+', text):
                if current_queue and current_queue in queue_data:
                    queue_data[current_queue]['time'] = text
                else:
                    inferred_queue = (i // 2) + 1
                    if inferred_queue and inferred_queue in queue_data and 1 <= inferred_queue <= 6:
                        queue_data[inferred_queue]['time'] = text
            
            elif text_lower in ['idle', 'unlock', 'cannot use']:
                if current_queue and current_queue in queue_data:
                    queue_data[current_queue]['status'] = text
        
        # Analyze each detected queue
        for queue_num in sorted(queue_data.keys()):
            data = queue_data[queue_num]
            status = data.get('status', 'unknown')
            status_lower = status.lower().strip() if status else ''
            
            march_info = {
                'queue_number': queue_num,
                'queue_text': data['queue_text'],
                'status': status,
                'time_remaining': data.get('time'),
                'type': 'unknown',
                'resource': None,
                'location': None
            }
            
            if 'gathering' in status_lower:
                march_info['type'] = 'gathering'
                analysis['gathering_marches'] += 1
            elif 'returning' in status_lower:
                march_info['type'] = 'returning'
                analysis['returning_marches'] += 1
            elif any(word in status_lower for word in ['attack', 'rally']):
                march_info['type'] = 'attack'
                analysis['attack_marches'] += 1
            elif 'waiting' in status_lower:
                march_info['type'] = 'waiting'
                analysis['waiting_marches'] += 1
            elif any(word in status_lower for word in ['go to', 'goto']):
                march_info['type'] = 'marching'
            elif 'idle' in status_lower:
                march_info['type'] = 'idle'
                analysis['idle_marches'] += 1
            elif any(word in status_lower for word in ['cannot use', 'unlock']):
                march_info['type'] = 'locked'
                analysis['locked_marches'] += 1
            
            combined_text = f"{data['queue_text']} {status}".lower()
            resource_mapping = {
                'mill': 'food',
                'lumberyard': 'wood', 
                'lumber': 'wood',
                'quarry': 'stone',
                'iron mine': 'iron',
                'mine': 'iron'
            }
            
            for location, resource in resource_mapping.items():
                if location in combined_text:
                    march_info['resource'] = resource
                    march_info['location'] = location
                    analysis['resource_types'].add(resource)
                    break
            
            level_match = re.search(r'lv\.?\s*(\d+)', combined_text)
            if level_match:
                march_info['level'] = int(level_match.group(1))
            
            analysis['march_details'].append(march_info)
            analysis['total_queues'] += 1
        
        analysis['resource_types'] = list(analysis['resource_types'])
        return analysis
    
    def _log_march_analysis(self, analysis: Dict[str, Any]) -> None:
        """Log march analysis results"""
        self.log_message("📊 March Analysis:")
        self.log_message(f"   📈 Total march queues detected: {analysis['total_queues']}")
        
        if analysis['gathering_marches'] > 0:
            self.log_message(f"   🌾 Gathering: {analysis['gathering_marches']}")
        if analysis['returning_marches'] > 0:
            self.log_message(f"   🔄 Returning: {analysis['returning_marches']}")
        if analysis['attack_marches'] > 0:
            self.log_message(f"   ⚔️ Attack/Rally: {analysis['attack_marches']}")
        if analysis['idle_marches'] > 0:
            self.log_message(f"   💤 Idle: {analysis['idle_marches']}")
        if analysis['locked_marches'] > 0:
            self.log_message(f"   🔒 Locked/Cannot Use: {analysis['locked_marches']}")
        if analysis['waiting_marches'] > 0:
            self.log_message(f"   ⏳ Waiting: {analysis['waiting_marches']}")
        
        if analysis['resource_types']:
            self.log_message(f"   🎯 Resources: {', '.join(analysis['resource_types'])}")

    def _is_march_related_text(self, text: str) -> bool:
        """Check if detected text is related to marches or gathering"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_lower = text.lower().strip()
        
        keywords = [
            'march', 'gather', 'gathering', 'collecting', 'returning', 'troop',
            'wood', 'stone', 'iron', 'food', 'bread', 'resource',
            'level', 'lvl', 'tier', 'queue', 'attack', 'rally',
            'waiting', 'go to', 'goto', 'idle', 'cannot use', 'unlock',
            'mill', 'lumberyard', 'quarry', 'iron mine', 'mine'
        ]
        
        for keyword in keywords:
            if keyword in text_lower:
                return True
        
        if re.search(r'\d+:\d+', text):
            return True
        
        return False

    def _click_search_and_dismiss_popup(self) -> bool:
        """Click search button and dismiss any popup"""
        try:
            search_position = (31, 535)
            if not self.adb_utils.run_adb_command(self.instance_index, f"input tap {search_position[0]} {search_position[1]}"):
                return False
            
            time.sleep(1)
            
            dismiss_position = (50, 750)
            self.adb_utils.run_adb_command(self.instance_index, f"input tap {dismiss_position[0]} {dismiss_position[1]}")
            time.sleep(2)
            
            return self._verify_resource_selection_screen()
        except Exception:
            return False

    def _deploy_march(self) -> bool:
        """Deploy march with deploy button"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                deploy_buttons = ["deploy_button.png", "deploy.png"]
                confidences = [0.6, 0.5, 0.4]
                
                for deploy_button in deploy_buttons:
                    for confidence in confidences:
                        if self._click_template_if_found(screenshot_path, deploy_button, threshold=confidence):
                            time.sleep(2)
                            return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False

    def _take_screenshot(self) -> Optional[str]:
        """Take a screenshot using ADB"""
        try:
            if not self.adb_utils:
                return None
            
            for attempt in range(3):
                try:
                    screenshot_data = self.adb_utils.get_screenshot_data(self.instance_index)
                    if screenshot_data:
                        nparr = np.frombuffer(screenshot_data, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if img is not None:
                            screenshot_path = f"screenshot_{self.instance_name}_{int(time.time())}.png"
                            cv2.imwrite(screenshot_path, img)
                            return screenshot_path
                except Exception:
                    pass
            
            device_path = "/sdcard/temp_screenshot.png"
            save_cmd = f"screencap {device_path}"
            
            if self.adb_utils.run_adb_command(self.instance_index, save_cmd):
                local_path = f"screenshot_{self.instance_name}_{int(time.time())}.png"
                
                pull_result = self.adb_utils.run_adb_command_raw(
                    self.instance_index, 
                    f"pull {device_path} {local_path}"
                )
                
                if pull_result and os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    if file_size > 0:
                        try:
                            img = cv2.imread(local_path)
                            if img is not None:
                                self.adb_utils.run_adb_command(self.instance_index, f"rm {device_path}")
                                return local_path
                        except Exception:
                            pass
            
            return None
            
        except Exception:
            return None

    def _find_template_matches(self, screenshot_path: str, template_name: str, threshold: float = 0.8) -> List[dict]:
        """Find all matches of a template in screenshot"""
        matches = []
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            if not os.path.exists(template_path):
                return matches
            
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                return matches
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            
            for pt in zip(*locations[::-1]):
                confidence = result[pt[1], pt[0]]
                matches.append({
                    'location': pt,
                    'confidence': float(confidence)
                })
            
        except Exception:
            pass
        
        return matches

    def _template_exists(self, screenshot_path: str, template_name: str, threshold: float = 0.8) -> bool:
        """Check if template exists in screenshot"""
        matches = self._find_template_matches(screenshot_path, template_name, threshold)
        return len(matches) > 0

    def _click_template_if_found(self, screenshot_path: str, template_name: str, threshold: float = 0.8) -> bool:
        """Click on template if found with sufficient confidence"""
        try:
            matches = self._find_template_matches(screenshot_path, template_name, threshold)
            
            if matches:
                best_match = max(matches, key=lambda x: x['confidence'])
                location = best_match['location']
                
                template_path = os.path.join(self.templates_dir, template_name)
                template_img = cv2.imread(template_path)
                
                if template_img is not None:
                    h, w = template_img.shape[:2]
                    click_x = location[0] + w // 2
                    click_y = location[1] + h // 2
                    
                    if self._click_position(click_x, click_y):
                        return True
                    else:
                        return False
            
            return False
            
        except Exception:
            return False

    def _click_position(self, x: int, y: int) -> bool:
        """Click at coordinates using ADB"""
        try:
            if not self.adb_utils:
                return False
            
            click_cmd = f"input tap {x} {y}"
            result = self.adb_utils.run_adb_command(self.instance_index, click_cmd)
            return result is not None
            
        except Exception:
            return False

    def _cleanup_screenshot(self, screenshot_path: str) -> None:
        """Cleanup screenshot file"""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception:
            pass

    def get_status(self) -> dict:
        """Get current status of AutoGather"""
        return {
            'running': self.running,
            'cycle_count': self.cycle_count,
            'instance_name': self.instance_name,
            'has_ocr': self.ocr is not None,
            'has_adb': self.adb_utils is not None,
            'settings': self.settings
        }
    
    def get_settings_config(self) -> dict:
        """Return settings configuration for GUI"""
        return {
            'resource_loop': {
                'type': 'text',
                'label': 'Resource Loop (comma separated)',
                'value': ','.join(self.settings['resource_loop']),
                'description': 'Resources to gather in order: food, wood, stone, iron'
            },
            'max_queues': {
                'type': 'number',
                'label': 'Max Queues to Use',
                'value': self.settings['max_queues'],
                'min': 1,
                'max': 6,
                'description': 'Maximum march queues to use (leave some for rallies)'
            },
            'enabled': {
                'type': 'boolean',
                'label': 'Auto Gather Enabled',
                'value': self.settings['enabled'],
                'description': 'Enable automatic resource gathering'
            }
        }
    
    def update_settings(self, new_settings: dict) -> bool:
        """Update settings from GUI"""
        try:
            if 'resource_loop' in new_settings:
                resources = [r.strip().lower() for r in new_settings['resource_loop'].split(',')]
                valid_resources = ['food', 'wood', 'stone', 'iron']
                self.settings['resource_loop'] = [r for r in resources if r in valid_resources]
                
            if 'max_queues' in new_settings:
                max_q = int(new_settings['max_queues'])
                self.settings['max_queues'] = max(1, min(6, max_q))
                
            if 'enabled' in new_settings:
                self.settings['enabled'] = bool(new_settings['enabled'])
            
            self.log_message(f"📋 Settings updated: {self.settings}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error updating settings: {e}")
            return False

    def get_module_info(self) -> dict:
        """Return module information for BENSON system"""
        return {
            'name': 'AutoGather',
            'display_name': 'Auto Gather Resources',
            'description': 'Automatically gathers resources using available march queues',
            'version': '2.0.0',
            'author': 'BENSON v2.0',
            'supports_settings': True,
            'supports_start_stop': True
        }
    
    def get_current_settings(self) -> dict:
        """Get current settings in the format expected by BENSON GUI"""
        return {
            'resource_loop': ','.join(self.settings['resource_loop']),
            'max_queues': self.settings['max_queues'],
            'enabled': self.settings['enabled']
        }
    
    def validate_settings(self, settings: dict) -> Tuple[bool, List[str]]:
        """Validate settings before applying"""
        errors = []
        
        try:
            if 'resource_loop' in settings:
                resources = [r.strip().lower() for r in settings['resource_loop'].split(',')]
                valid_resources = ['food', 'wood', 'stone', 'iron']
                invalid = [r for r in resources if r not in valid_resources]
                if invalid:
                    errors.append(f"Invalid resources: {', '.join(invalid)}. Valid: {', '.join(valid_resources)}")
                if not resources:
                    errors.append("Resource loop cannot be empty")
            
            if 'max_queues' in settings:
                try:
                    max_q = int(settings['max_queues'])
                    if max_q < 1 or max_q > 6:
                        errors.append("Max queues must be between 1 and 6")
                except ValueError:
                    errors.append("Max queues must be a number")
                    
        except Exception as e:
            errors.append(f"Settings validation error: {e}")
        
        return len(errors) == 0, errors
    
    def can_start(self) -> bool:
        """Check if module can be started"""
        return (self.settings['enabled'] and 
                not self.running and 
                self.adb_utils is not None and 
                self.ocr is not None)
    
    def get_status_text(self) -> str:
        """Get human-readable status text"""
        if not self.settings['enabled']:
            return "Disabled"
        elif self.running:
            return f"Running - Cycle {self.cycle_count}"
        else:
            return "Stopped"


def register_module() -> dict:
    """Register AutoGather module with BENSON system"""
    return {
        'name': 'AutoGather',
        'display_name': 'Auto Gather Resources',
        'description': 'Automatically gathers resources using available march queues with smart hibernation',
        'version': '2.0.0',
        'author': 'BENSON v2.0',
        'class': AutoGather,
        'supports_settings': True,
        'supports_start_stop': True,
        'default_enabled': False,
        'settings_schema': {
            'resource_loop': {
                'type': 'text',
                'label': 'Resource Loop',
                'default': 'food,wood,stone,iron',
                'description': 'Resources to gather in order (comma separated)',
                'validation': 'required'
            },
            'max_queues': {
                'type': 'number',
                'label': 'Max Queues',
                'default': 6,
                'min': 1,
                'max': 6,
                'description': 'Maximum march queues to use'
            },
            'enabled': {
                'type': 'boolean',
                'label': 'Enabled',
                'default': True,
                'description': 'Enable automatic resource gathering'
            }
        }
    }


# Export the module for dynamic import
__all__ = ['AutoGather', 'register_module']

    def _verify_resource_selection_screen(self) -> bool:
        """Verify we're in resource selection screen"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                indicators = ["plus_button.png", "bread_icon.png", "wood_icon.png"]
                
                for indicator in indicators:
                    if self._template_exists(screenshot_path, indicator, threshold=0.6):
                        return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False

    def _perform_scroll_to_reveal_resources(self) -> bool:
        """Scroll to reveal resources"""
        try:
            scroll_start = (400, 570)
            scroll_end = (80, 570)
            
            steps = 5
            for i in range(steps):
                x = scroll_start[0] + (scroll_end[0] - scroll_start[0]) * i / (steps - 1)
                y = scroll_start[1] + (scroll_end[1] - scroll_start[1]) * i / (steps - 1)
                self.adb_utils.run_adb_command(self.instance_index, f"input tap {int(x)} {int(y)}")
                time.sleep(0.1)
            
            time.sleep(1)
            return True
        except Exception:
            return False

    def _select_resource_type(self, resource_type: str) -> bool:
        """Select the specified resource type"""
        try:
            icon_file = self.RESOURCE_ICONS.get(resource_type.lower())
            if not icon_file:
                return False
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                confidences = [0.6, 0.5, 0.4]
                
                for confidence in confidences:
                    if self._click_template_if_found(screenshot_path, icon_file, threshold=confidence):
                        time.sleep(1)
                        return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False

    def _set_max_level_and_search(self) -> bool:
        """Set maximum level and search for resources"""
        try:
            if not self._set_max_level():
                return False
            
            return self._search_for_available_resource()
        except Exception:
            return False

    def _set_max_level(self) -> bool:
        """Set resource level to maximum"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                matches = self._find_template_matches(screenshot_path, "plus_button.png", threshold=0.6)
                if matches:
                    plus_location = matches[0]['location']
                    
                    for i in range(8):
                        self.adb_utils.run_adb_command(self.instance_index, f"input tap {plus_location[0]} {plus_location[1]}")
                        time.sleep(0.1)
                    
                    return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False

    def _search_for_available_resource(self) -> bool:
        """Search for available resources at different levels"""
        try:
            for level in range(8, 0, -1):
                if self._click_search_resource_button() and self._wait_and_check_for_gather_button():
                    return True
                
                if level > 1 and not self._reduce_level():
                    return False
            
            return False
        except Exception:
            return False

    def _click_search_resource_button(self) -> bool:
        """Click search resource button"""
        try:
            search_resource_position = (237, 789)
            return self.adb_utils.run_adb_command(self.instance_index, f"input tap {search_resource_position[0]} {search_resource_position[1]}") is not None
        except Exception:
            return False

    def _wait_and_check_for_gather_button(self) -> bool:
        """Wait and check for gather button"""
        try:
            time.sleep(3)
            
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                if self._template_exists(screenshot_path, "gather_button.png", threshold=0.6):
                    if self._click_template_if_found(screenshot_path, "gather_button.png", threshold=0.6):
                        time.sleep(1)
                        return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)
                
        except Exception:
            return False

    def _reduce_level(self) -> bool:
        """Reduce level by clicking minus button"""
        try:
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return False
            
            try:
                if self._click_template_if_found(screenshot_path, "minus_button.png", threshold=0.6):
                    time.sleep(0.3)
                    return True
                
                return False
                
            finally:
                self._cleanup_screenshot(screenshot_path)