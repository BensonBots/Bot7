"""
BENSON v2.0 - AutoGather Module
Automatically manages resource gathering operations
"""

import os
import time
from typing import List, Dict
from datetime import datetime, timedelta

# Import base module system
from modules.base_module import BaseModule, ModulePriority

# Safe imports
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class AutoGatherModule(BaseModule):
    """Module for automatic resource gathering management"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        super().__init__(instance_name, shared_resources, console_callback)
        
        # Module configuration
        self.module_name = "AutoGather"
        self.check_interval = 30  # Check every 30 seconds
        self.max_retries = 3
        
        # Gathering configuration
        self.resource_types = ["food", "wood", "iron", "stone"]
        self.min_march_capacity = 100000
        self.max_concurrent_gathers = 5
        self.gather_duration_preference = "long"  # "short", "medium", "long"
        
        # Template configuration
        self.templates_dir = "templates/gather"
        self.confidence_threshold = 0.7
        
        # Resource gathering templates
        self.GATHER_TEMPLATES = {
            "world_map": ["world_map.png", "map_icon.png"],
            "resource_tiles": {
                "food": ["food_tile.png", "farm_tile.png"],
                "wood": ["wood_tile.png", "lumber_tile.png"],
                "iron": ["iron_tile.png", "mine_tile.png"],
                "stone": ["stone_tile.png", "quarry_tile.png"]
            },
            "gather_button": ["gather_btn.png", "collect_btn.png"],
            "march_slots": ["march_slot.png", "army_slot.png"],
            "confirm_gather": ["confirm_btn.png", "send_btn.png"],
            "close_buttons": ["close_x.png", "back_btn.png"]
        }
        
        # State tracking
        self.current_gathers = {}  # march_id -> gather_info
        self.last_gather_check = None
        self.resource_priorities = ["iron", "food", "wood", "stone"]  # Priority order
        
        # Statistics
        self.total_gathers_sent = 0
        self.total_resources_collected = 0
        
        # Create templates directory
        os.makedirs(self.templates_dir, exist_ok=True)
    
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
        
        # Check if game is accessible
        game_state = self.get_game_state("game_accessible")
        return game_state is True
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies"""
        missing = []
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        
        game_state = self.get_game_state("game_accessible")
        if game_state is not True:
            missing.append("game_must_be_accessible")
        
        return missing
    
    def execute_cycle(self) -> bool:
        """Execute one cycle of gathering management"""
        try:
            # Check if game is still accessible
            if not self.is_available():
                self.log_message("Game not accessible, skipping cycle")
                return False
            
            self.log_message("🌾 Checking gathering status...")
            
            # Update current gather status
            self._update_gather_status()
            
            # Check for completed gathers
            completed_gathers = self._check_completed_gathers()
            if completed_gathers:
                self.log_message(f"✅ {len(completed_gathers)} gathers completed")
            
            # Send new gathers if slots available
            available_slots = self._get_available_march_slots()
            if available_slots > 0:
                new_gathers = self._send_new_gathers(available_slots)
                if new_gathers:
                    self.log_message(f"📤 Sent {new_gathers} new gathers")
            
            # Update shared state
            self._update_shared_state()
            
            self.last_gather_check = datetime.now()
            return True
            
        except Exception as e:
            self.log_message(f"Gathering cycle error: {e}", "error")
            return False
    
    def _update_gather_status(self):
        """Update status of current gathers"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return
            
            # Navigate to army/march management screen
            if self._navigate_to_army_screen(screenshot_path):
                # Check status of each active gather
                for march_id, gather_info in list(self.current_gathers.items()):
                    if self._is_gather_completed(march_id, gather_info):
                        self._handle_completed_gather(march_id, gather_info)
            
            try:
                os.remove(screenshot_path)
            except:
                pass
                
        except Exception as e:
            self.log_message(f"Error updating gather status: {e}", "error")
    
    def _check_completed_gathers(self) -> int:
        """Check for and handle completed gathers"""
        completed_count = 0
        
        for march_id, gather_info in list(self.current_gathers.items()):
            estimated_completion = gather_info.get("estimated_completion")
            if estimated_completion and datetime.now() >= estimated_completion:
                self.log_message(f"✅ Gather {march_id} estimated to be complete")
                self._handle_completed_gather(march_id, gather_info)
                completed_count += 1
        
        return completed_count
    
    def _get_available_march_slots(self) -> int:
        """Get number of available march slots"""
        try:
            # Basic calculation: max concurrent - current active
            active_gathers = len([g for g in self.current_gathers.values() 
                                if g.get("status") == "active"])
            available = self.max_concurrent_gathers - active_gathers
            return max(0, available)
            
        except Exception as e:
            self.log_message(f"Error checking march slots: {e}", "error")
            return 0
    
    def _send_new_gathers(self, available_slots: int) -> int:
        """Send new gathering expeditions"""
        try:
            gathers_sent = 0
            
            for i in range(min(available_slots, len(self.resource_priorities))):
                resource_type = self.resource_priorities[i % len(self.resource_priorities)]
                
                if self._send_gather_for_resource(resource_type):
                    gathers_sent += 1
                    self.total_gathers_sent += 1
                    time.sleep(2)  # Delay between sends
            
            return gathers_sent
            
        except Exception as e:
            self.log_message(f"Error sending new gathers: {e}", "error")
            return 0
    
    def _send_gather_for_resource(self, resource_type: str) -> bool:
        """Send a gathering expedition for specific resource"""
        try:
            self.log_message(f"🎯 Sending gather for {resource_type}")
            
            # Take screenshot and navigate to world map
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Navigate to world map
                if not self._navigate_to_world_map(screenshot_path):
                    return False
                
                time.sleep(2)
                
                # Find and click resource tile
                if not self._find_and_click_resource_tile(resource_type):
                    return False
                
                time.sleep(2)
                
                # Click gather button
                if not self._click_gather_button():
                    return False
                
                time.sleep(2)
                
                # Confirm gather
                if not self._confirm_gather():
                    return False
                
                # Record the new gather
                march_id = f"gather_{resource_type}_{int(time.time())}"
                self.current_gathers[march_id] = {
                    "resource_type": resource_type,
                    "start_time": datetime.now(),
                    "estimated_completion": datetime.now() + timedelta(hours=2),  # Estimate
                    "status": "active"
                }
                
                self.log_message(f"✅ Successfully sent {resource_type} gather")
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error sending {resource_type} gather: {e}", "error")
            return False
    
    def _navigate_to_world_map(self, screenshot_path: str) -> bool:
        """Navigate to world map"""
        try:
            # Look for world map button/icon
            for template in self.GATHER_TEMPLATES["world_map"]:
                if self._click_template(screenshot_path, template):
                    self.log_message("🗺️ Navigated to world map")
                    return True
            
            # Try common world map positions
            world_map_positions = [(50, 100), (100, 100), (400, 100)]
            for x, y in world_map_positions:
                self.click_position(x, y)
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_message(f"Error navigating to world map: {e}", "error")
            return False
    
    def _navigate_to_army_screen(self, screenshot_path: str) -> bool:
        """Navigate to army/march management screen"""
        try:
            # Look for army/march management icons
            army_positions = [(400, 600), (350, 600), (300, 600)]
            for x, y in army_positions:
                self.click_position(x, y)
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_message(f"Error navigating to army screen: {e}", "error")
            return False
    
    def _find_and_click_resource_tile(self, resource_type: str) -> bool:
        """Find and click on a resource tile"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for specific resource tile templates
                resource_templates = self.GATHER_TEMPLATES["resource_tiles"].get(resource_type, [])
                for template in resource_templates:
                    if self._click_template(screenshot_path, template):
                        self.log_message(f"🎯 Found and clicked {resource_type} tile")
                        return True
                
                # Fallback: try common resource tile positions
                tile_positions = [
                    (200, 300), (300, 250), (350, 350), (150, 400), (250, 450)
                ]
                
                for x, y in tile_positions:
                    self.click_position(x, y)
                    time.sleep(1)
                    
                    # Check if gather button appeared
                    if self._check_for_gather_button():
                        self.log_message(f"🎯 Found {resource_type} tile at ({x}, {y})")
                        return True
                
                return False
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error finding {resource_type} tile: {e}", "error")
            return False
    
    def _check_for_gather_button(self) -> bool:
        """Check if gather button is visible"""
        screenshot_path = self.get_screenshot()
        if not screenshot_path:
            return False
        
        try:
            for template in self.GATHER_TEMPLATES["gather_button"]:
                if self._find_template(screenshot_path, template):
                    return True
            return False
        finally:
            try:
                os.remove(screenshot_path)
            except:
                pass
    
    def _click_gather_button(self) -> bool:
        """Click the gather button"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                for template in self.GATHER_TEMPLATES["gather_button"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Clicked gather button")
                        return True
                
                # Fallback positions for gather button
                gather_positions = [(240, 500), (300, 450), (400, 400)]
                for x, y in gather_positions:
                    self.click_position(x, y)
                    time.sleep(1)
                
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error clicking gather button: {e}", "error")
            return False
    
    def _confirm_gather(self) -> bool:
        """Confirm the gathering expedition"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                for template in self.GATHER_TEMPLATES["confirm_gather"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Confirmed gather")
                        return True
                
                # Fallback positions for confirm button
                confirm_positions = [(300, 400), (350, 450), (250, 400)]
                for x, y in confirm_positions:
                    self.click_position(x, y)
                    time.sleep(1)
                
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error confirming gather: {e}", "error")
            return False
    
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
    
    def _find_template(self, screenshot_path: str, template_name: str) -> bool:
        """Find a template without clicking"""
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
            
            return max_val >= self.confidence_threshold
            
        except Exception as e:
            return False
    
    def _is_gather_completed(self, march_id: str, gather_info: Dict) -> bool:
        """Check if a specific gather is completed"""
        # For now, use time estimation
        estimated_completion = gather_info.get("estimated_completion")
        if estimated_completion:
            return datetime.now() >= estimated_completion
        return False
    
    def _handle_completed_gather(self, march_id: str, gather_info: Dict):
        """Handle a completed gather"""
        try:
            self.log_message(f"🎉 Handling completed gather: {march_id}")
            
            # Remove from active gathers
            if march_id in self.current_gathers:
                del self.current_gathers[march_id]
            
            # Update statistics
            self.total_resources_collected += 1
            
            # Update shared state
            self.update_game_state({
                "last_completed_gather": {
                    "march_id": march_id,
                    "resource_type": gather_info.get("resource_type"),
                    "completion_time": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            self.log_message(f"Error handling completed gather: {e}", "error")
    
    def _update_shared_state(self):
        """Update shared game state with gathering information"""
        try:
            gather_summary = {
                "active_gathers": len(self.current_gathers),
                "total_gathers_sent": self.total_gathers_sent,
                "total_resources_collected": self.total_resources_collected,
                "last_gather_check": self.last_gather_check.isoformat() if self.last_gather_check else None,
                "available_march_slots": self._get_available_march_slots(),
                "current_gathers": {
                    march_id: {
                        "resource_type": info.get("resource_type"),
                        "start_time": info.get("start_time").isoformat() if info.get("start_time") else None,
                        "estimated_completion": info.get("estimated_completion").isoformat() if info.get("estimated_completion") else None,
                        "status": info.get("status")
                    }
                    for march_id, info in self.current_gathers.items()
                }
            }
            
            self.update_game_state({"gather_status": gather_summary})
            
        except Exception as e:
            self.log_message(f"Error updating shared state: {e}", "error")
    
    def get_gather_status(self) -> Dict:
        """Get detailed gathering status"""
        return {
            "module_status": self.status.value,
            "active_gathers": len(self.current_gathers),
            "available_slots": self._get_available_march_slots(),
            "total_sent": self.total_gathers_sent,
            "total_collected": self.total_resources_collected,
            "resource_priorities": self.resource_priorities,
            "current_gathers": dict(self.current_gathers),
            "last_check": self.last_gather_check.isoformat() if self.last_gather_check else None
        }
    
    def force_gather_check(self) -> bool:
        """Force an immediate gather check (manual trigger)"""
        self.log_message("🎯 Force checking gathers (manual trigger)")
        return self.execute_cycle()
    
    def update_resource_priorities(self, new_priorities: List[str]):
        """Update resource gathering priorities"""
        valid_resources = ["food", "wood", "iron", "stone"]
        filtered_priorities = [r for r in new_priorities if r in valid_resources]
        
        if filtered_priorities:
            self.resource_priorities = filtered_priorities
            self.log_message(f"📋 Updated resource priorities: {self.resource_priorities}")
            return True
        return False