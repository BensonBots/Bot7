# Add this method to your auto_gather.py file

def _click_open_left_with_fallback(self) -> bool:
    """Enhanced open_left clicking with fallback positions"""
    try:
        screenshot_path = self._take_screenshot()
        if not screenshot_path:
            return False
        
        try:
            # Try template matching first
            template_path = self.templates.get('open_left')
            if template_path and os.path.exists(template_path):
                
                import cv2
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
                        
                        # Click the position
                        if self._click_position(click_x, click_y, "open_left"):
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
                    # Wait a moment and check if it worked
                    time.sleep(1)
                    self.log_message(f"✅ Fallback position {i+1} clicked successfully")
                    return True
            
            self.log_message("❌ All fallback positions failed")
            return False
            
        finally:
            self._cleanup_screenshot(screenshot_path)
    
    except Exception as e:
        self.log_message(f"❌ Error in enhanced open_left click: {e}")
        return False

# Replace your existing _click_open_left method with this:
def _click_open_left(self) -> bool:
    """Take screenshot and click open_left button with fallback"""
    return self._click_open_left_with_fallback()

# Also add this improved method for wilderness button
def _click_wilderness_button_with_fallback(self) -> bool:
    """Enhanced wilderness button clicking with fallback"""
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

# Replace your existing _click_wilderness_button method with this:
def _click_wilderness_button(self) -> bool:
    """Take screenshot and click wilderness_button with fallback"""
    return self._click_wilderness_button_with_fallback()

# OPTIONAL: Lower the template matching threshold to be more lenient
def __init__(self, instance_name: str, shared_resources, console_callback=None):
    # ... existing code ...
    
    # Make template matching more lenient
    self.config.template_matching_threshold = 0.5  # Lowered from 0.6
    
    # ... rest of existing code ...