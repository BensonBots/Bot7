"""
BENSON v2.0 - Enhanced MEmu ADB OCR Helper
Uses MEmu's built-in ADB wrapper with region selection for targeted OCR
Enhanced with aggressive timer detection for march queues
"""

import subprocess
import tempfile
import os
import time
import re
from typing import List, Dict, Optional, Tuple
import logging
import win32gui
from PIL import Image, ImageGrab, ImageEnhance, ImageOps, ImageFilter

# Safe imports with fallbacks
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Overall OCR availability
OCR_AVAILABLE = CV2_AVAILABLE and NUMPY_AVAILABLE and EASYOCR_AVAILABLE

class OCRHelper:
    """MEmu ADB-based OCR Helper with enhanced timer detection capabilities"""
    
    # Predefined regions for common game UI elements
    REGIONS = {
        "left_panel": {"x": 0, "y": 0, "width": 0.4, "height": 1.0},  # Left 40% of screen
        "right_panel": {"x": 0.6, "y": 0, "width": 0.4, "height": 1.0},  # Right 40% of screen
        "top_bar": {"x": 0, "y": 0, "width": 1.0, "height": 0.15},  # Top 15% of screen
        "bottom_bar": {"x": 0, "y": 0.85, "width": 1.0, "height": 0.15},  # Bottom 15% of screen
        "center": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},  # Center 50% of screen
        "march_queue": {"x": 0.13, "y": 0.27, "width": 0.398, "height": 0.34},  # March queue area - readjusted
        "building_queue": {"x": 0.18, "y": 0.15, "width": 0.18, "height": 0.45},  # Building queue panel - tightly cropped
        "full_screen": {"x": 0, "y": 0, "width": 1.0, "height": 1.0}  # Full screen
    }
    
    def __init__(self):
        self.logger = self._setup_logging()
        self._ocr_reader = None
        self._check_dependencies()
        
        if self.is_dependencies_available():
            self._initialize_ocr()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for OCR operations"""
        logger = logging.getLogger('OCRHelper')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(name)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _check_dependencies(self):
        """Check which dependencies are available"""
        missing = []
        
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        if not NUMPY_AVAILABLE:
            missing.append("numpy")
        if not EASYOCR_AVAILABLE:
            missing.append("easyocr")
        
        if missing:
            self.logger.warning(f"Missing OCR dependencies: {', '.join(missing)}")
        else:
            self.logger.info("All OCR dependencies available")
    
    def is_dependencies_available(self) -> bool:
        """Check if core dependencies are available"""
        return CV2_AVAILABLE and NUMPY_AVAILABLE and EASYOCR_AVAILABLE
    
    def _initialize_ocr(self):
        """Initialize EasyOCR reader"""
        try:
            self.logger.info("Initializing EasyOCR reader...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=False)
            self.logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR: {e}")
            self._ocr_reader = None
    
    def is_ocr_available(self) -> bool:
        """Check if OCR is available"""
        return self._ocr_reader is not None and self.is_dependencies_available()
    
    def get_available_regions(self) -> List[str]:
        """Get list of available predefined regions"""
        return list(self.REGIONS.keys())
    
    def add_custom_region(self, name: str, x: float, y: float, width: float, height: float):
        """Add a custom region (coordinates as percentages 0.0-1.0)"""
        self.REGIONS[name] = {"x": x, "y": y, "width": width, "height": height}
        self.logger.info(f"Added custom region '{name}': x={x}, y={y}, w={width}, h={height}")
    
    def capture_memu_adb_screenshot(self, instance_index: int, memuc_path: str) -> Optional[str]:
        """Capture screenshot using MEmu's ADB wrapper"""
        try:
            temp_dir = tempfile.gettempdir()
            local_screenshot = os.path.join(temp_dir, f"memu_adb_screenshot_{instance_index}_{int(time.time())}.png")
            device_screenshot = "/sdcard/screen.png"
            
            self.logger.info(f"Taking MEmu ADB screenshot for instance {instance_index}")
            
            # Step 1: Take screenshot on device using MEmu's ADB wrapper
            capture_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "screencap", "-p", device_screenshot
            ]
            
            self.logger.info(f"Capture command: {' '.join(capture_cmd)}")
            
            capture_result = subprocess.run(
                capture_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if capture_result.returncode != 0:
                self.logger.error(f"Screenshot capture failed: {capture_result.stderr}")
                return None
            
            # Wait a moment for the file to be written
            time.sleep(0.5)
            
            # Step 2: Pull screenshot from device using MEmu's ADB wrapper
            pull_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "pull", device_screenshot, local_screenshot
            ]
            
            self.logger.info(f"Pull command: {' '.join(pull_cmd)}")
            
            pull_result = subprocess.run(
                pull_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if pull_result.returncode != 0:
                self.logger.error(f"Screenshot pull failed: {pull_result.stderr}")
                return None
            
            # Step 3: Clean up device screenshot
            cleanup_cmd = [
                memuc_path, "adb", "-i", str(instance_index),
                "shell", "rm", device_screenshot
            ]
            
            try:
                subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
            except:
                pass  # Cleanup failure is not critical
            
            # Step 4: Verify screenshot exists and has content
            if os.path.exists(local_screenshot):
                file_size = os.path.getsize(local_screenshot)
                if file_size > 10000:  # At least 10KB
                    self.logger.info(f"MEmu ADB screenshot successful: {local_screenshot} ({file_size} bytes)")
                    return local_screenshot
                else:
                    self.logger.error(f"Screenshot file too small: {file_size} bytes")
                    return None
            else:
                self.logger.error("Screenshot file not found after pull")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("MEmu ADB screenshot command timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error capturing MEmu ADB screenshot: {e}")
            return None
    
    def crop_image_region(self, image_path: str, region_name: str = "left_panel", 
                         custom_region: Dict[str, float] = None) -> Optional[str]:
        """Crop image to specified region"""
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV not available, cannot crop image")
            return image_path
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Could not load image: {image_path}")
                return None
            
            height, width = image.shape[:2]
            
            # Get region coordinates
            if custom_region:
                region = custom_region
                region_name = "custom"
            elif region_name in self.REGIONS:
                region = self.REGIONS[region_name]
            else:
                self.logger.warning(f"Unknown region '{region_name}', using full screen")
                region = self.REGIONS["full_screen"]
            
            # Calculate pixel coordinates
            x = int(region["x"] * width)
            y = int(region["y"] * height)
            crop_width = int(region["width"] * width)
            crop_height = int(region["height"] * height)
            
            # Ensure coordinates are within image bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            crop_width = min(crop_width, width - x)
            crop_height = min(crop_height, height - y)
            
            # Crop the image
            cropped_image = image[y:y+crop_height, x:x+crop_width]
            
            if cropped_image.size == 0:
                self.logger.error("Cropped image is empty")
                return None
            
            # Save cropped image
            cropped_path = image_path.replace('.png', f'_cropped_{region_name}.png')
            cv2.imwrite(cropped_path, cropped_image)
            
            # Save debug copy to desktop
            debug_path = os.path.join(os.path.expanduser("~"), "Desktop", 
                                    f"ocr_debug_cropped_{region_name}_{int(time.time())}.png")
            try:
                cv2.imwrite(debug_path, cropped_image)
                self.logger.info(f"Debug cropped image saved to desktop: {debug_path}")
            except:
                pass
            
            self.logger.info(f"Cropped image to {region_name} region: {crop_width}x{crop_height} at ({x},{y})")
            return cropped_path
            
        except Exception as e:
            self.logger.error(f"Error cropping image: {e}")
            return image_path
    
    def preprocess_image_for_ocr(self, image_path: str) -> Optional[str]:
        """Preprocess image for better OCR results"""
        if not CV2_AVAILABLE:
            return image_path
        
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return image_path
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Resize if too small (EasyOCR works better with larger images)
            height, width = gray.shape
            if height < 600:
                scale_factor = 600 / height
                new_width = int(width * scale_factor)
                gray = cv2.resize(gray, (new_width, 600), interpolation=cv2.INTER_CUBIC)
                self.logger.info(f"Upscaled image from {width}x{height} to {new_width}x600")
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(enhanced)
            
            # Additional processing for text detection
            # Apply bilateral filter to reduce noise while keeping edges sharp
            filtered = cv2.bilateralFilter(denoised, 9, 75, 75)
            
            # Save processed image
            processed_path = image_path.replace('.png', '_processed.png')
            cv2.imwrite(processed_path, filtered)
            
            # Save debug images to desktop
            debug_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            cv2.imwrite(os.path.join(debug_dir, "ocr_debug_original.png"), gray)
            cv2.imwrite(os.path.join(debug_dir, "ocr_debug_enhanced.png"), enhanced)
            cv2.imwrite(os.path.join(debug_dir, "ocr_debug_processed.png"), filtered)
            self.logger.info("OCR debug images saved to desktop")
            
            return processed_path
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            return image_path
    
    def extract_text_from_image(self, image_path: str, confidence_threshold: float = 0.3) -> List[Dict]:
        """Extract text from image using OCR with simple upscaling"""
        if not self.is_ocr_available():
            self.logger.warning("OCR not available")
            return []
        
        try:
            results = []
            
            # Method 1: Standard OCR
            try:
                standard_results = self._ocr_reader.readtext(image_path, detail=1)
                for bbox, text, confidence in standard_results:
                    text = text.strip()
                    if confidence >= confidence_threshold and text:
                        results.append({
                            'bbox': bbox,
                            'text': text,
                            'confidence': confidence,
                            'method': 'standard'
                        })
            except Exception as e:
                self.logger.warning(f"Standard OCR failed: {e}")
            
            # Method 2: Simple upscale and enhance
            upscaled_path = self._simple_upscale_and_enhance(image_path)
            if upscaled_path:
                try:
                    upscaled_results = self._ocr_reader.readtext(upscaled_path, detail=1)
                    for bbox, text, confidence in upscaled_results:
                        text = text.strip().replace(' ', '')
                        if confidence >= 0.1 and text:  # Lower threshold for upscaled
                            # Clean timer text if it looks like one
                            if self._is_timer_like(text):
                                cleaned_text = self._clean_timer_text(text)
                                if cleaned_text and not self._already_found(results, cleaned_text):
                                    results.append({
                                        'bbox': bbox,
                                        'text': cleaned_text,
                                        'confidence': confidence,
                                        'method': 'upscaled'
                                    })
                            elif not self._already_found(results, text):
                                results.append({
                                    'bbox': bbox,
                                    'text': text,
                                    'confidence': confidence,
                                    'method': 'upscaled'
                                })
                except Exception as e:
                    self.logger.warning(f"Upscaled OCR failed: {e}")
                finally:
                    try:
                        if os.path.exists(upscaled_path):
                            os.remove(upscaled_path)
                    except:
                        pass
            
            # Remove duplicates and sort by confidence
            unique_results = self._remove_duplicate_results(results)
            
            return unique_results
            
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return []

    def _simple_upscale_and_enhance(self, image_path: str) -> str:
        """Simple 2x upscale with basic enhancement"""
        try:
            img = Image.open(image_path)
            
            # Get original size
            original_width, original_height = img.size
            
            # Upscale by 2x using high quality resampling
            new_width = original_width * 2
            new_height = original_height * 2
            upscaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale for better OCR
            upscaled = upscaled.convert('L')
            
            # Basic contrast enhancement (not too aggressive)
            enhancer = ImageEnhance.Contrast(upscaled)
            upscaled = enhancer.enhance(1.5)  # Mild contrast boost
            
            # Basic sharpness enhancement
            enhancer = ImageEnhance.Sharpness(upscaled)
            upscaled = enhancer.enhance(1.3)  # Mild sharpening
            
            # Save upscaled version
            upscaled_path = image_path.replace('.png', '_upscaled_2x.png')
            upscaled.save(upscaled_path)
            
            # Save debug copy to desktop
            try:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                debug_path = os.path.join(desktop, f"upscaled_2x_debug_{int(time.time())}.png")
                upscaled.save(debug_path)
                self.logger.info(f"Upscaled 2x debug saved: {debug_path}")
                self.logger.info(f"Upscaled from {original_width}x{original_height} to {new_width}x{new_height}")
            except:
                pass
            
            return upscaled_path
            
        except Exception as e:
            self.logger.warning(f"Simple upscaling failed: {e}")
            return None

    def _enhance_for_green_text(self, image_path: str) -> str:
        """Create enhanced version specifically for green timer text"""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Extract green channel and enhance it
            r, g, b = img.split()
            
            # Enhance the green channel specifically
            green_enhanced = ImageEnhance.Contrast(g).enhance(4.0)  # Higher contrast
            green_enhanced = ImageEnhance.Brightness(green_enhanced).enhance(2.5)  # Much brighter
            
            # Apply sharpening to help with character separation
            green_enhanced = green_enhanced.filter(ImageFilter.SHARPEN)
            
            # Save enhanced version
            enhanced_path = image_path.replace('.png', '_green_enhanced.png')
            green_enhanced.save(enhanced_path)
            
            # Also save debug copy to desktop
            try:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                debug_path = os.path.join(desktop, f"green_enhanced_debug_{int(time.time())}.png")
                green_enhanced.save(debug_path)
                self.logger.info(f"Green enhanced debug saved: {debug_path}")
            except:
                pass
            
            return enhanced_path
            
        except Exception as e:
            self.logger.warning(f"Green text enhancement failed: {e}")
            return None

    def _is_timer_like(self, text: str) -> bool:
        """Check if text looks like a timer"""
        if not text or len(text) < 4:
            return False
        
        # Pattern matching for timer formats
        patterns = [
            r'^\d{1,2}:\d{2}:\d{2}$',  # HH:MM:SS or H:MM:SS
            r'^\d{1,2}:\d{2}$',        # MM:SS or H:MM
            r'^\d{4,8}$',              # 4-8 digits that could be a timer without colons
        ]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        
        # Check if it's mostly numbers with some colons
        clean_text = re.sub(r'[^0-9:.]+', '', text)
        if len(clean_text) >= 4:
            digit_count = len(re.sub(r'[^0-9]', '', clean_text))
            if digit_count >= 4 and digit_count <= 8:
                return True
                
        return False

    def _clean_timer_text(self, text: str) -> str:
        """Clean and standardize timer text"""
        if not text:
            return ""
        
        # Remove unwanted characters
        cleaned = re.sub(r'[^0-9:.]+', '', text)
        cleaned = cleaned.replace('.', ':')
        
        # If it's already in timer format, return it
        if re.match(r'^\d{1,2}:\d{2}:\d{2}$', cleaned) or re.match(r'^\d{1,2}:\d{2}$', cleaned):
            return cleaned
        
        # Smart formatting for digit sequences
        if cleaned.isdigit():
            if len(cleaned) == 6:  # HHMMSS -> HH:MM:SS
                hh, mm, ss = cleaned[:2], cleaned[2:4], cleaned[4:6]
                if int(hh) < 24 and int(mm) < 60 and int(ss) < 60:
                    return f"{hh}:{mm}:{ss}"
            elif len(cleaned) == 4:  # MMSS -> MM:SS
                mm, ss = cleaned[:2], cleaned[2:4]
                if int(mm) < 60 and int(ss) < 60:
                    return f"{mm}:{ss}"
            elif len(cleaned) == 8:  # Could be malformed, try different splits
                # Try HH:MM:SS format first
                hh, mm, ss = cleaned[:2], cleaned[2:4], cleaned[4:6]
                if int(hh) < 24 and int(mm) < 60 and int(ss) < 60:
                    return f"{hh}:{mm}:{ss}"
        
        return ""

    def _already_found(self, results: List[Dict], text: str) -> bool:
        """Check if this text was already found"""
        for result in results:
            if result['text'] == text:
                return True
        return False

    def _remove_duplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results, keeping the highest confidence"""
        if not results:
            return results
        
        # Group by text
        text_groups = {}
        for result in results:
            text = result['text']
            if text not in text_groups or result['confidence'] > text_groups[text]['confidence']:
                text_groups[text] = result
        
        # Sort by confidence (highest first)
        unique_results = list(text_groups.values())
        unique_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return unique_results

    def _create_multiple_preprocessed_versions(self, image_path: str) -> List[str]:
        """Create multiple preprocessed versions for difficult text detection"""
        preprocessed_paths = []
        
        try:
            # Open original image
            img = Image.open(image_path)
            base_name = image_path.replace('.png', '')
            
            # Version 1: Very high contrast
            img1 = img.convert('L')
            enhancer = ImageEnhance.Contrast(img1)
            img1 = enhancer.enhance(5.0)  # Very high contrast
            enhancer = ImageEnhance.Brightness(img1)
            img1 = enhancer.enhance(2.0)  # Much brighter
            path1 = f"{base_name}_high_contrast.png"
            img1.save(path1)
            preprocessed_paths.append(path1)
            
            # Version 2: Fixed threshold for green text
            img2 = img.convert('L')
            # Fix the data type issue by ensuring proper conversion
            img2_array = list(img2.getdata())
            img2_threshold = [255 if x > 50 else 0 for x in img2_array]
            img2_new = Image.new('L', img2.size)
            img2_new.putdata(img2_threshold)
            path2 = f"{base_name}_low_threshold.png"
            img2_new.save(path2)
            preprocessed_paths.append(path2)
            
            # Version 3: Inverted with enhancement
            img3 = img.convert('L')
            img3 = ImageOps.invert(img3)
            enhancer = ImageEnhance.Contrast(img3)
            img3 = enhancer.enhance(3.0)
            path3 = f"{base_name}_inverted.png"
            img3.save(path3)
            preprocessed_paths.append(path3)
            
        except Exception as e:
            self.logger.warning(f"Failed to create preprocessed versions: {e}")
        
        return preprocessed_paths
    
    def perform_ocr_on_memu_instance(self, instance_index: int, memuc_path: str, 
                                   instance_name: str = None, region_name: str = "left_panel",
                                   custom_region: Dict[str, float] = None,
                                   confidence_threshold: float = 0.3) -> Dict:
        """Perform OCR on MEmu instance with region selection"""
        if not self.is_ocr_available():
            return {
                'success': False,
                'error': "OCR not available - missing dependencies",
                'instance_index': instance_index,
                'instance_name': instance_name,
                'region': region_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        try:
            start_time = time.time()
            
            # Use MEmu's ADB wrapper to capture screenshot
            screenshot_path = self.capture_memu_adb_screenshot(instance_index, memuc_path)
            
            if not screenshot_path:
                raise RuntimeError("Failed to capture MEmu ADB screenshot")
            
            # Crop to specified region
            cropped_path = self.crop_image_region(screenshot_path, region_name, custom_region)
            
            if not cropped_path:
                raise RuntimeError("Failed to crop image to specified region")
            
            # Extract text from cropped screenshot
            extracted_texts = self.extract_text_from_image(cropped_path, confidence_threshold)
            
            # Clean up screenshot files
            try:
                os.remove(screenshot_path)
                if cropped_path != screenshot_path:
                    os.remove(cropped_path)
            except:
                pass
            
            processing_time = round(time.time() - start_time, 2)
            
            # Get region info for result
            region_info = custom_region if custom_region else self.REGIONS.get(region_name, {})
            
            # Format results
            result = {
                'success': True,
                'instance_index': instance_index,
                'instance_name': instance_name,
                'region': region_name,
                'region_info': region_info,
                'processing_time': processing_time,
                'text_count': len(extracted_texts),
                'texts': extracted_texts,
                'full_text': self._combine_texts(extracted_texts),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'method': 'MEmu ADB + Simple 2x Upscale',
                'confidence_threshold': confidence_threshold
            }
            
            self.logger.info(f"MEmu ADB OCR completed in {processing_time}s, "
                           f"found {len(extracted_texts)} text elements in {region_name} region")
            return result
            
        except Exception as e:
            self.logger.error(f"MEmu ADB OCR operation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'instance_index': instance_index,
                'instance_name': instance_name,
                'region': region_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _combine_texts(self, extracted_texts: List[Dict]) -> str:
        """Combine extracted texts into readable format"""
        if not extracted_texts:
            return ""
        
        # Sort texts by vertical position (top to bottom, left to right)
        sorted_texts = sorted(extracted_texts, key=lambda x: (x['bbox'][0][1], x['bbox'][0][0]))
        
        # Combine texts
        combined = []
        for item in sorted_texts:
            text = item['text'].strip()
            if text:  # Only add non-empty text
                combined.append(text)
        
        return '\n'.join(combined)
    
    def format_ocr_results_for_console(self, result: Dict) -> str:
        """Format OCR results for console display"""
        if not result['success']:
            return f"❌ OCR Failed: {result.get('error', 'Unknown error')}"
        
        region_info = f" [{result['region']} region]" if result.get('region') else ""
        
        if result['text_count'] == 0:
            return f"🔍 OCR Complete{region_info}: No text found on {result['instance_name']} screen"
        
        method_info = f" ({result.get('method', 'Unknown')})" if 'method' in result else ""
        header = (f"🔍 OCR Results for {result['instance_name']}{region_info}{method_info} "
                 f"({result['text_count']} texts, {result['processing_time']}s):")
        separator = "─" * 60
        
        # Show individual texts with confidence and method
        details = []
        for item in result['texts']:
            confidence_bar = "█" * int(item['confidence'] * 10)
            method_tag = f" [{item.get('method', 'standard')}]" if 'method' in item else ""
            details.append(f"  • \"{item['text']}\" (confidence: {item['confidence']:.2f} {confidence_bar}){method_tag}")
        
        # Combine everything
        if len(details) > 15:  # Limit details for console
            details = details[:15] + [f"  ... and {len(details) - 15} more"]
        
        full_text = result['full_text']
        if len(full_text) > 300:  # Limit full text display
            full_text = full_text[:300] + "..."
        
        return (f"{header}\n{separator}\n"
               f"Region: {result.get('region', 'Unknown')} | "
               f"Confidence Threshold: {result.get('confidence_threshold', 'N/A')}\n"
               f"Combined Text:\n{full_text}\n{separator}\n"
               f"Details:\n" + "\n".join(details))
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing packages"""
        missing = []
        
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        if not NUMPY_AVAILABLE:
            missing.append("numpy")
        if not EASYOCR_AVAILABLE:
            missing.append("easyocr")
        
        return missing
    
    def test_region(self, hwnd: int, x: float, y: float, width: float, height: float, 
                   confidence_threshold: float = 0.3) -> Dict:
        """Test OCR on a specific window region using window handle"""
        if not self.is_ocr_available():
            return {
                'success': False,
                'error': "OCR not available - missing dependencies",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }