"""
BENSON v2.0 - AutoMail Module
Automatically claims mail rewards and gifts
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


class AutoMailModule(BaseModule):
    """Module for automatic mail and reward collection"""
    
    def __init__(self, instance_name: str, shared_resources, console_callback=None):
        super().__init__(instance_name, shared_resources, console_callback)
        
        # Module configuration
        self.module_name = "AutoMail"
        self.check_interval = 120  # Check every 2 minutes
        self.max_retries = 3
        
        # Mail configuration
        self.claim_resources = True
        self.claim_items = True
        self.claim_speedups = True
        self.claim_gems = True
        self.delete_read_mail = False
        
        # Template configuration
        self.templates_dir = "templates/mail"
        self.confidence_threshold = 0.7
        
        # Mail templates
        self.MAIL_TEMPLATES = {
            "mail_icon": ["mail_icon.png", "envelope_icon.png", "inbox_icon.png"],
            "mail_notification": ["mail_notification.png", "new_mail.png"],
            "claim_buttons": ["claim_btn.png", "collect_btn.png", "receive_btn.png"],
            "claim_all": ["claim_all.png", "collect_all.png", "receive_all.png"],
            "delete_button": ["delete_btn.png", "trash_btn.png"],
            "confirm_delete": ["confirm_btn.png", "yes_btn.png"],
            "close_buttons": ["close_x.png", "back_btn.png"],
            "reward_types": {
                "resources": ["resource_reward.png", "gold_icon.png"],
                "items": ["item_reward.png", "gear_icon.png"],
                "speedups": ["speedup_reward.png", "clock_icon.png"],
                "gems": ["gem_reward.png", "diamond_icon.png"]
            },
            "mail_categories": {
                "system": ["system_mail.png"],
                "battle": ["battle_mail.png"],
                "alliance": ["alliance_mail.png"],
                "rewards": ["reward_mail.png"]
            }
        }
        
        # State tracking
        self.last_mail_check = None
        self.total_mails_claimed = 0
        self.total_rewards_claimed = 0
        self.last_claim_results = []
        
        # Statistics by reward type
        self.rewards_by_type = {
            "resources": 0,
            "items": 0, 
            "speedups": 0,
            "gems": 0
        }
        
        # Create templates directory
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def get_module_priority(self) -> ModulePriority:
        """AutoMail has low priority - runs when other tasks are idle"""
        return ModulePriority.LOW
    
    def get_dependencies(self) -> List[str]:
        """AutoMail depends on AutoStartGame"""
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
        """Execute one cycle of mail checking and claiming"""
        try:
            # Check if game is still accessible
            if not self.is_available():
                self.log_message("Game not accessible, skipping cycle")
                return False
            
            self.log_message("📬 Checking mail and rewards...")
            
            # Check for mail notifications
            has_new_mail = self._check_for_new_mail()
            
            if has_new_mail or self._should_check_mail():
                # Navigate to mail
                if self._navigate_to_mail():
                    # Claim available rewards
                    claimed_count = self._claim_all_rewards()
                    
                    if claimed_count > 0:
                        self.log_message(f"✅ Claimed {claimed_count} rewards")
                        self.total_rewards_claimed += claimed_count
                    
                    # Delete read mail if enabled
                    if self.delete_read_mail:
                        deleted_count = self._delete_read_mail()
                        if deleted_count > 0:
                            self.log_message(f"🗑️ Deleted {deleted_count} read mails")
                    
                    # Close mail interface
                    self._close_mail_interface()
            else:
                self.log_message("📪 No new mail to check")
            
            # Update shared state
            self._update_shared_state()
            
            self.last_mail_check = datetime.now()
            return True
            
        except Exception as e:
            self.log_message(f"Mail cycle error: {e}", "error")
            return False
    
    def _check_for_new_mail(self) -> bool:
        """Check if there are new mail notifications"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for mail notification indicators
                for template in self.MAIL_TEMPLATES["mail_notification"]:
                    if self._find_template(screenshot_path, template):
                        self.log_message("📨 New mail notification detected")
                        return True
                
                return False
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error checking for new mail: {e}", "error")
            return False
    
    def _should_check_mail(self) -> bool:
        """Check if we should check mail based on timing"""
        if not self.last_mail_check:
            return True
        
        # Check mail periodically even without notifications
        time_since_last = (datetime.now() - self.last_mail_check).total_seconds()
        return time_since_last >= (self.check_interval * 2)  # Check every 4 minutes minimum
    
    def _navigate_to_mail(self) -> bool:
        """Navigate to mail interface"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                # Look for mail icon
                for template in self.MAIL_TEMPLATES["mail_icon"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("📬 Opened mail interface")
                        time.sleep(2)  # Wait for mail to load
                        return True
                
                # Try common mail icon positions
                mail_positions = [(400, 50), (450, 50), (350, 50), (400, 100)]
                for x, y in mail_positions:
                    self.click_position(x, y)
                    time.sleep(2)
                    
                    # Check if mail interface opened
                    if self._verify_mail_interface():
                        self.log_message(f"📬 Opened mail at position ({x}, {y})")
                        return True
                
                return False
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error navigating to mail: {e}", "error")
            return False
    
    def _verify_mail_interface(self) -> bool:
        """Verify that mail interface is open"""
        screenshot_path = self.get_screenshot()
        if not screenshot_path:
            return False
        
        try:
            # Look for mail-specific elements
            mail_elements = (self.MAIL_TEMPLATES["claim_buttons"] + 
                           self.MAIL_TEMPLATES["claim_all"] + 
                           list(self.MAIL_TEMPLATES["mail_categories"].values())[0])
            
            for template in mail_elements:
                if self._find_template(screenshot_path, template):
                    return True
            
            return False
            
        finally:
            try:
                os.remove(screenshot_path)
            except:
                pass
    
    def _claim_all_rewards(self) -> int:
        """Claim all available rewards"""
        try:
            claimed_count = 0
            
            # Try claim all button first
            if self._try_claim_all():
                self.log_message("✅ Used claim all button")
                claimed_count = 1  # Assume at least one reward claimed
            else:
                # Claim individual rewards
                claimed_count = self._claim_individual_rewards()
            
            return claimed_count
            
        except Exception as e:
            self.log_message(f"Error claiming rewards: {e}", "error")
            return 0
    
    def _try_claim_all(self) -> bool:
        """Try to use claim all button"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return False
            
            try:
                for template in self.MAIL_TEMPLATES["claim_all"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("🎁 Clicked claim all")
                        time.sleep(3)  # Wait for claiming animation
                        return True
                
                return False
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error trying claim all: {e}", "error")
            return False
    
    def _claim_individual_rewards(self) -> int:
        """Claim individual rewards one by one"""
        try:
            claimed_count = 0
            max_attempts = 10  # Prevent infinite loops
            
            for attempt in range(max_attempts):
                screenshot_path = self.get_screenshot()
                if not screenshot_path:
                    break
                
                try:
                    # Look for claimable rewards
                    reward_claimed = False
                    
                    for template in self.MAIL_TEMPLATES["claim_buttons"]:
                        if self._click_template(screenshot_path, template):
                            self.log_message(f"🎁 Claimed reward {attempt + 1}")
                            claimed_count += 1
                            reward_claimed = True
                            time.sleep(2)  # Wait between claims
                            break
                    
                    if not reward_claimed:
                        # No more claimable rewards found
                        break
                        
                finally:
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
            
            return claimed_count
            
        except Exception as e:
            self.log_message(f"Error claiming individual rewards: {e}", "error")
            return 0
    
    def _delete_read_mail(self) -> int:
        """Delete read mail messages"""
        try:
            if not self.delete_read_mail:
                return 0
            
            deleted_count = 0
            max_attempts = 5  # Limit deletion attempts
            
            for attempt in range(max_attempts):
                screenshot_path = self.get_screenshot()
                if not screenshot_path:
                    break
                
                try:
                    # Look for delete button
                    mail_deleted = False
                    
                    for template in self.MAIL_TEMPLATES["delete_button"]:
                        if self._click_template(screenshot_path, template):
                            time.sleep(1)
                            
                            # Confirm deletion if prompted
                            if self._confirm_deletion():
                                self.log_message(f"🗑️ Deleted mail {attempt + 1}")
                                deleted_count += 1
                                mail_deleted = True
                                time.sleep(2)
                                break
                    
                    if not mail_deleted:
                        break
                        
                finally:
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
            
            return deleted_count
            
        except Exception as e:
            self.log_message(f"Error deleting mail: {e}", "error")
            return 0
    
    def _confirm_deletion(self) -> bool:
        """Confirm mail deletion if prompted"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return True  # Assume no confirmation needed
            
            try:
                for template in self.MAIL_TEMPLATES["confirm_delete"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("✅ Confirmed mail deletion")
                        return True
                
                return True  # No confirmation dialog found
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error confirming deletion: {e}", "error")
            return False
    
    def _close_mail_interface(self):
        """Close the mail interface"""
        try:
            screenshot_path = self.get_screenshot()
            if not screenshot_path:
                return
            
            try:
                # Look for close buttons
                for template in self.MAIL_TEMPLATES["close_buttons"]:
                    if self._click_template(screenshot_path, template):
                        self.log_message("❌ Closed mail interface")
                        return
                
                # Try common close positions
                close_positions = [(450, 50), (400, 50), (50, 50)]
                for x, y in close_positions:
                    self.click_position(x, y)
                    time.sleep(1)
                
            finally:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
        except Exception as e:
            self.log_message(f"Error closing mail interface: {e}", "error")
    
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
    
    def _update_shared_state(self):
        """Update shared game state with mail information"""
        try:
            mail_summary = {
                "total_mails_claimed": self.total_mails_claimed,
                "total_rewards_claimed": self.total_rewards_claimed,
                "last_mail_check": self.last_mail_check.isoformat() if self.last_mail_check else None,
                "rewards_by_type": self.rewards_by_type.copy(),
                "settings": {
                    "claim_resources": self.claim_resources,
                    "claim_items": self.claim_items,
                    "claim_speedups": self.claim_speedups,
                    "claim_gems": self.claim_gems,
                    "delete_read_mail": self.delete_read_mail
                }
            }
            
            self.update_game_state({"mail_status": mail_summary})
            
        except Exception as e:
            self.log_message(f"Error updating shared state: {e}", "error")
    
    def get_mail_status(self) -> Dict:
        """Get detailed mail status"""
        return {
            "module_status": self.status.value,
            "total_claimed": self.total_rewards_claimed,
            "total_mails": self.total_mails_claimed,
            "rewards_by_type": self.rewards_by_type.copy(),
            "last_check": self.last_mail_check.isoformat() if self.last_mail_check else None,
            "settings": {
                "claim_resources": self.claim_resources,
                "claim_items": self.claim_items,
                "claim_speedups": self.claim_speedups,
                "claim_gems": self.claim_gems,
                "delete_read_mail": self.delete_read_mail
            }
        }
    
    def force_mail_check(self) -> bool:
        """Force an immediate mail check (manual trigger)"""
        self.log_message("🎯 Force checking mail (manual trigger)")
        return self.execute_cycle()
    
    def update_settings(self, **settings):
        """Update mail claiming settings"""
        updated = False
        
        for key, value in settings.items():
            if hasattr(self, key) and isinstance(value, bool):
                setattr(self, key, value)
                updated = True
        
        if updated:
            self.log_message(f"⚙️ Updated mail settings")
        
        return updated