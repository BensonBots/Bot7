"""
BENSON v2.0 - AutoTrain Module
Automatically manages troop training operations
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


class AutoTrainModule(BaseModule):
    """Module for automatic troop training management"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        super().__init__(instance_name, shared_resources, console_callback)
        
        # Module configuration
        self.module_name = "AutoTrain"
        self.check_interval = 60  # Check every minute
        self.max_retries = 3
        
        # Training configuration
        self.troop_types = ["infantry", "ranged", "cavalry", "siege"]
        self.training_priority = ["infantry", "ranged", "cavalry", "siege"]
        self.max_training_queues = 4
        self.min_resource_threshold = 50000  # Minimum resources before training
        
        # Template configuration
        self.templates_dir = "templates/train"
        self.confidence_threshold = 0.7
        
        # Training templates
        self.TRAIN_TEMPLATES = {
            "barracks": ["barracks.png", "training_grounds.png"],
            "army_tab": ["army_tab.png", "troops_tab.png"],
            "troop_types": {
                "infantry": ["infantry_btn.png", "soldier_btn.png"],
                "ranged": ["archer_btn.png", "ranged_btn.png"],
                "cavalry": ["cavalry_btn.png", "horse_btn.png"],
                "siege": ["siege_btn.png", "catapult_btn.png"]
            },
            "train_button": ["train_btn.png", "recruit_btn.png"],
            "train_max": ["max_btn.png", "train_max.png"],
            "confirm_train": ["confirm_btn.png", "start_training.png"],
            "close_buttons": ["close_x.png", "back_btn.png"],
            "resource_icons": {
                "food": ["food_icon.png"],
                "wood": ["wood_icon.png"], 
                "iron": ["iron_icon.png"],
                "stone": ["stone_icon.png"]
            }
        }
        
        # State tracking
        self.current_training = {}  # queue_id -> training_info
        self.last_training_check = None
        self.current_resources = {"food": 0, "wood": 0, "iron": 0, "stone": 0}
        
        # Statistics
        self.total_troops_trained = 0
        self.total_training_started = 0
        
        # Create templates directory
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def get_module_priority(self) -> ModulePriority:
        """AutoTrain has medium priority"""
        return ModulePriority.MEDIUM
    
    def get_dependencies(self) -> List[str]:
        """AutoTrain depends on AutoStartGame"""
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
        """Execute one cycle of training management"""
        try:
            # Check if game is still accessible
            if not self.is_available():
                self.log_message("Game not accessible, skipping cycle")
                return False
            
            self.log_message("⚔️ Checking training status...")
            
            # Update current resource levels
            self._update_resource_levels()
            
            # Check training queue status
            self._update_training_status()
            
            # Check for completed training
            completed_training = self._check_completed_training()
            if completed_training:
                self.log_message(f"✅ {len(completed_training)} training completed")
            
            # Start new training if resources available and queues free
            if self._should_start_training():
                new_training = self._start_new_training()
                if new_training:
                    self.log_message(f"📤 Started {new_training} new training sessions")
            
            # Update shared state
            self._update_shared_state()
            
            self.last_training_check = datetime.now()
            return True
            
        except Exception as e:
            self.log_message(f"Training cycle error: {e}", "error")
            return False
    
    def _update_resource_levels(self):
        """Update current resource levels from screen"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return
            
            # Try to read resource numbers from screen
            # This is a simplified version - in practice you'd use OCR or template matching
            # For now, we'll get resource info from shared state or estimates
            
            # Check if AutoGather has resource information
            gather_state = self.get_game_state("gather_status")
            if gather_state:
                # Use gathering information to estimate resources
                active_gathers = gather_state.get("active_gathers", 0)
                if active_gathers > 0:
                    # Estimate we have resources if gathers are active
                    for resource in self.current_resources:
                        self.current_resources[resource] = max(self.min_resource_threshold, 
                                                             self.current_resources[resource])
            
            try:
                os.remove(screenshot_path)
            except:
                pass
                
        except Exception as e:
            self.log_message(f"Error updating resource levels: {e}", "error")
    
    def _update_training_status(self):
        """Update status of current training"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return
            
            # Navigate to barracks/training screen
            if self._navigate_to_barracks(screenshot_path):
                # Check status of each active training
                for queue_id, training_info in list(self.current_training.items()):
                    if self._is_training_completed(queue_id, training_info):
                        self._handle_completed_training(queue_id, training_info)
            
            try:
                os.remove(screenshot_path)
            except:
                pass
                
        except Exception as e:
            self.log_message(f"Error updating training status: {e}", "error")
    
    def _check_completed_training(self) -> int:
        """Check for and handle completed training"""
        completed_count = 0
        
        for queue_id, training_info in list(self.current_training.items()):
            estimated_completion = training_info.get("estimated_completion")
            if estimated_completion and datetime.now() >= estimated_completion:
                self.log_message(f"✅ Training {queue_id} estimated to be complete")
                self._handle_completed_training(queue_id, training_info)
                completed_count += 1
        
        return completed_count
    
    def _should_start_training(self) -> bool:
        """Check if we should start new training"""
        try:
            # Check if we have available training queues
            active_training = len([t for t in self.current_training.values() 
                                 if t.get("status") == "active"])
            
            if active_training >= self.max_training_queues:
                return False
            
            # Check if we have sufficient resources
            for resource, amount in self.current_resources.items():
                if amount < self.min_resource_threshold:
                    self.log_message(f"💰 Insufficient {resource}: {amount} < {self.min_resource_threshold}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_message(f"Error checking training conditions: {e}", "error")
            return False
    
    def _start_new_training(self) -> int:
        """Start new training sessions"""
        try:
            training_started = 0
            available_queues = self.max_training_queues - len([t for t in self.current_training.values() 
                                                              if t.get("status") == "active"])
            
            for i in range(min(available_queues, len(self.training_priority))):
                troop_type = self.training_priority[i % len(self.training_priority)]
                
                if self._start_training_for_troop(troop_type):
                    training_started += 1
                    self.total_training_started += 1
                    time.sleep(3)  # Delay between training starts
            
            return training_started
            
        except Exception as e:
            self.log_message(f"Error starting new training: {e}", "error")
            return 0
    
    def _start_training_for_troop(self, troop_type: str) -> bool:
        """Start training for specific troop type"""
        try:
            self.log_message(f"⚔️ Starting training for {troop_type}")
            
            # Take screenshot and navigate to barracks
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Navigate to barracks
                if not self._navigate_to_barracks(screenshot_path):
                    return False
                
                time.sleep(2)
                
                # Click on troop type
                if not self._select_troop_type(troop_type):
                    return False
                
                time.sleep(2)
                
                # Click train max or specific amount
                if not self._click_train_amount():
                    return False
                
                time.sleep(2)
                
                # Confirm training
                if not self._confirm_training():
                    return False
                
                # Record the new training
                queue_id = f"training_{troop_type}_{int(time.time())}"
                self.current_training[queue_id] = {
                    "troop_type": troop_type,
                    "start_time": datetime.now(),
                    "estimated_completion": datetime.now() + timedelta(hours=1),  # Estimate
                    "status": "active"
                }
                
                self.log_message(f"✅ Successfully started {troop_type} training")
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error starting {troop_type} training: {e}", "error")
            return False
    
    def _navigate_to_barracks(self, screenshot_path: str) -> bool:
        """Navigate to barracks/training facility"""
        try:
            # Look for barracks button/icon
            for template in self.TRAIN_TEMPLATES["barracks"]:
                if self._click_template(screenshot_path, template):
                    self.log_message("🏰 Navigated to barracks")
                    return True
            
            # Try common barracks positions
            barracks_positions = [(100, 500), (150, 450), (200, 400)]
            for x, y in barracks_positions:
                self.click_position(x, y)
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_message(f"Error navigating to barracks: {e}", "error")
            return False
    
    def _select_troop_type(self, troop_type: str) -> bool:
        """Select specific troop type for training"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for specific troop type templates
                troop_templates = self.TRAIN_TEMPLATES["troop_types"].get(troop_type, [])
                for template in troop_templates:
                    if self._click_template(screenshot_path, template):
                        self.log_message(f"⚔️ Selected {troop_type}")
                        return True
                
                # Fallback: try common troop selection positions
                troop_positions = {
                    "infantry": (100, 300),
                    "ranged": (200, 300),
                    "cavalry": (300, 300),
                    "siege": (400, 300)
                }
                
                if troop_type in troop_positions:
                    x, y = troop_positions[troop_type]
                    self.click_position(x, y)
                    self.log_message(f"⚔️ Selected {troop_type} at fallback position")
                    return True
                
                return False
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error selecting {troop_type}: {e}", "error")
            return False
    
    def _click_train_amount(self) -> bool:
        """Click train amount (max or specific number)"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Try to click train max button
                for template in self.TRAIN_TEMPLATES["train_max"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Clicked train max")
                        return True
                
                # Fallback: click train button
                for template in self.TRAIN_TEMPLATES["train_button"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Clicked train button")
                        return True
                
                # Final fallback positions
                train_positions = [(300, 400), (350, 450), (250, 400)]
                for x, y in train_positions:
                    self.click_position(x, y)
                    time.sleep(1)
                
                return True
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error clicking train amount: {e}", "error")
            return False
    
    def _confirm_training(self) -> bool:
        """Confirm the training"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                for template in self.TRAIN_TEMPLATES["confirm_train"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Confirmed training")
                        return True
                
                # Fallback positions for confirm button
                confirm_positions = [(300, 500), (350, 450), (250, 500)]
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
            self.log_message(f"Error confirming training: {e}", "error")
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
    
    def _is_training_completed(self, queue_id: str, training_info: Dict) -> bool:
        """Check if specific training is completed"""
        # For now, use time estimation
        estimated_completion = training_info.get("estimated_completion")
        if estimated_completion:
            return datetime.now() >= estimated_completion
        return False
    
    def _handle_completed_training(self, queue_id: str, training_info: Dict):
        """Handle completed training"""
        try:
            self.log_message(f"🎉 Handling completed training: {queue_id}")
            
            # Remove from active training
            if queue_id in self.current_training:
                del self.current_training[queue_id]
            
            # Update statistics
            self.total_troops_trained += 1
            
            # Update shared state
            self.update_game_state({
                "last_completed_training": {
                    "queue_id": queue_id,
                    "troop_type": training_info.get("troop_type"),
                    "completion_time": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            self.log_message(f"Error handling completed training: {e}", "error")
    
    def _update_shared_state(self):
        """Update shared game state with training information"""
        try:
            training_summary = {
                "active_training": len(self.current_training),
                "total_training_started": self.total_training_started,
                "total_troops_trained": self.total_troops_trained,
                "last_training_check": self.last_training_check.isoformat() if self.last_training_check else None,
                "available_queues": self.max_training_queues - len([t for t in self.current_training.values() if t.get("status") == "active"]),
                "current_resources": self.current_resources.copy(),
                "current_training": {
                    queue_id: {
                        "troop_type": info.get("troop_type"),
                        "start_time": info.get("start_time").isoformat() if info.get("start_time") else None,
                        "estimated_completion": info.get("estimated_completion").isoformat() if info.get("estimated_completion") else None,
                        "status": info.get("status")
                    }
                    for queue_id, info in self.current_training.items()
                }
            }
            
            self.update_game_state({"training_status": training_summary})
            
        except Exception as e:
            self.log_message(f"Error updating shared state: {e}", "error")
    
    def get_training_status(self) -> Dict:
        """Get detailed training status"""
        return {
            "module_status": self.status.value,
            "active_training": len(self.current_training),
            "available_queues": self.max_training_queues - len([t for t in self.current_training.values() if t.get("status") == "active"]),
            "total_started": self.total_training_started,
            "total_completed": self.total_troops_trained,
            "training_priority": self.training_priority,
            "current_training": dict(self.current_training),
            "current_resources": self.current_resources.copy(),
            "last_check": self.last_training_check.isoformat() if self.last_training_check else None
        }
    
    def force_training_check(self) -> bool:
        """Force an immediate training check (manual trigger)"""
        self.log_message("🎯 Force checking training (manual trigger)")
        return self.execute_cycle()
    
    def update_training_priority(self, new_priority: List[str]):
        """Update troop training priorities"""
        valid_troops = ["infantry", "ranged", "cavalry", "siege"]
        filtered_priority = [t for t in new_priority if t in valid_troops]
        
        if filtered_priority:
            self.training_priority = filtered_priority
            self.log_message(f"📋 Updated training priority: {self.training_priority}")
            return True
        return False