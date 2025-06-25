"""
BENSON v2.0 - Enhanced March Queue Analyzer
Fixed version with error handling and improved methods
"""

import cv2
import numpy as np
import time
import os
import math
import concurrent.futures
from threading import Lock
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class QueueInfo:
    """Information about a march queue"""
    name: str = ""
    task: str = ""
    status: str = ""
    time_remaining: str = ""
    is_available: bool = False


@dataclass
class OCRResult:
    """OCR result with scoring"""
    text: str
    confidence: float
    method_id: int
    method_name: str
    score: float = 0.0


class MarchQueueAnalyzer:
    """Enhanced OCR analysis with new methods and optimizations"""
    
    def __init__(self, instance_name: str, config, log_callback=None):
        self.instance_name = instance_name
        self.config = config
        self.log_callback = log_callback or print
        
        # OCR setup
        self.ocr_reader = None
        self.tesseract_available = False
        self._initialize_ocr()
        
        # Method performance tracking
        self.method_scores = {}
        self.method_usage_count = {}
        
        # Thread safety for parallel processing
        self.results_lock = Lock()
        
        # Simple queue regions
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
    
    def _initialize_ocr(self):
        """Initialize OCR readers"""
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=False)
            self.log("✅ EasyOCR reader initialized")
        except ImportError:
            self.log("❌ easyocr not installed")
            return False
        except Exception as e:
            self.log(f"❌ EasyOCR initialization failed: {e}")
            return False
        
        # Try to initialize Tesseract
        try:
            import pytesseract
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            self.log("✅ Tesseract OCR available")
        except:
            self.log("⚠️ Tesseract not available (optional)")
            self.tesseract_available = False
        
        return True
    
    def log(self, message: str):
        """Log message"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [MarchAnalyzer-{self.instance_name}] {message}"
        self.log_callback(formatted_message)
    
    def analyze_march_queues(self, screenshot_path: str) -> Dict[int, QueueInfo]:
        """Enhanced OCR analysis of march queues with parallel processing"""
        try:
            self.log("🔍 Starting enhanced march queue OCR...")
            
            if not self.ocr_reader:
                self.log("❌ OCR reader not available")
                return {}
            
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                self.log("❌ Failed to load screenshot")
                return {}
            
            # Analyze queues in parallel for better performance
            queues = self._analyze_queues_parallel(screenshot)
            
            # Count available queues
            available_count = len([q for q in queues.values() if q.is_available])
            available_numbers = [str(num) for num, q in queues.items() if q.is_available]
            
            self.log(f"✅ Enhanced OCR complete - {len(queues)} queues analyzed")
            if available_numbers:
                self.log(f"🎯 Available queues: {', '.join(available_numbers)}")
            
            # Log method performance summary
            self._log_method_performance()
            
            return queues
            
        except Exception as e:
            self.log(f"❌ OCR analysis error: {e}")
            return {}
    
    def _analyze_queues_parallel(self, screenshot) -> Dict[int, QueueInfo]:
        """Analyze queues in parallel for better performance"""
        queues = {}
        
        def analyze_single_queue(queue_num):
            try:
                queue_info = self._analyze_queue(queue_num, screenshot.copy())
                if queue_info:
                    with self.results_lock:
                        queues[queue_num] = queue_info
            except Exception as e:
                self.log(f"❌ Error analyzing Queue {queue_num}: {e}")
        
        # Process queues in parallel (limit threads to avoid overwhelming)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_single_queue, i) for i in range(1, 7)]
            concurrent.futures.wait(futures, timeout=30)  # 30 second timeout
        
        return queues
    
    def _analyze_queue(self, queue_num: int, screenshot) -> Optional[QueueInfo]:
        """Analyze a single queue with enhanced OCR"""
        try:
            if queue_num not in self.queue_regions:
                return None
            
            queue_info = QueueInfo()
            regions = self.queue_regions[queue_num]
            
            # For queues 1-2: read task and timer
            if queue_num <= 2:
                if 'task' in regions:
                    queue_info.task = self._enhanced_ocr_with_fallbacks(screenshot, regions['task'], f"Q{queue_num}_task")
                
                if 'timer' in regions:
                    queue_info.time_remaining = self._enhanced_ocr_with_fallbacks(screenshot, regions['timer'], f"Q{queue_num}_timer")
                
                # Enhanced availability check
                queue_info.is_available = self._is_queue_available(queue_info.task, queue_info.time_remaining)
            
            # For queues 3-6: read name and status
            else:
                if 'name' in regions:
                    queue_info.name = self._enhanced_ocr_with_fallbacks(screenshot, regions['name'], f"Q{queue_num}_name")
                
                if 'status' in regions:
                    queue_info.status = self._enhanced_ocr_with_fallbacks(screenshot, regions['status'], f"Q{queue_num}_status")
                
                # Enhanced availability check
                queue_info.is_available = self._is_commander_queue_available(queue_info.name, queue_info.status)
            
            # Log results
            if queue_num <= 2:
                status = "AVAILABLE" if queue_info.is_available else "BUSY"
                self.log(f"📊 Queue {queue_num}: Task='{queue_info.task}' | Timer='{queue_info.time_remaining}' | {status}")
            else:
                status = "AVAILABLE" if queue_info.is_available else "LOCKED"
                self.log(f"📊 Queue {queue_num}: Name='{queue_info.name}' | Status='{queue_info.status}' | {status}")
            
            return queue_info
                
        except Exception as e:
            self.log(f"❌ Error analyzing Queue {queue_num}: {e}")
            return None
    
    def _enhanced_ocr_with_fallbacks(self, screenshot, region: tuple, region_id: str) -> str:
        """OCR with multiple fallback strategies"""
        
        # Strategy 1: Normal enhanced OCR
        try:
            result = self._enhanced_ocr(screenshot, region, region_id)
            if self._validate_ocr_result(result, region_id):
                return self._post_process_text_result(result, region_id)
        except Exception as e:
            self.log(f"⚠️ Primary OCR failed for {region_id}: {e}")
        
        # Strategy 2: Simple OCR with basic preprocessing
        try:
            x, y, w, h = region
            roi = screenshot[y:y+h, x:x+w]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
            
            # Simple enhancement
            enhanced = cv2.resize(gray, (w*4, h*4), interpolation=cv2.INTER_CUBIC)
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Quick OCR
            results = self.ocr_reader.readtext(binary, detail=1)
            if results:
                result = max(results, key=lambda x: x[2])[1]
                return self._post_process_text_result(result, region_id)
        
        except Exception as e:
            self.log(f"⚠️ Fallback OCR failed for {region_id}: {e}")
        
        # Strategy 3: Return empty but log for debugging
        self.log(f"❌ All OCR strategies failed for {region_id}")
        return ""
    
    def _validate_ocr_result(self, text: str, region_id: str) -> bool:
        """Validate if OCR result makes sense"""
        if not text or len(text.strip()) < 1:
            return False
        
        if region_id.endswith('_timer'):
            # Timer should have digits and possibly colons
            return any(c.isdigit() for c in text)
        
        elif region_id.endswith('_status'):
            # Status should be short
            return len(text.strip()) <= 10
        
        elif region_id.endswith('_task') or region_id.endswith('_name'):
            # Task/name should have reasonable characters
            return len(text.strip()) >= 2 and not all(c in '.,!@#$%^&*()' for c in text)
        
        return True
    
    def _post_process_text_result(self, text: str, region_id: str) -> str:
        """Enhanced text post-processing"""
        if not text:
            return text
        
        # First, clean up the text
        text = text.strip()
        
        # Common corrections - MORE COMPREHENSIVE
        corrections = {
            # Queue text corrections
            'Qucuc': 'Queue',
            'Qucue': 'Queue', 
            'Queuec': 'Queue',
            'Quque': 'Queue',
            'Oucue': 'Queue',
            'Oueue': 'Queue',
            'Qucud': 'Queue',
            'Gucuc': 'Queue',
            
            # Idle corrections
            'Idlc': 'Idle',
            'Idic': 'Idle',
            'Id1c': 'Idle',
            'Id1e': 'Idle',
            '1d1e': 'Idle',
            'ld1e': 'Idle',
            'Idle': 'Idle',  # Keep correct ones
            
            # March corrections
            'Merch': 'March',
            'Morch': 'March',
            'Mareh': 'March',
        }
        
        result = text
        
        # Apply corrections
        for wrong, right in corrections.items():
            result = result.replace(wrong, right)
        
        # Special handling for different region types
        if region_id.endswith('_timer'):
            # Timer-specific cleaning
            import re
            
            # Look for timer patterns
            timer_pattern = r'(\d{1,2}):(\d{2}):(\d{2})'
            match = re.search(timer_pattern, result)
            if match:
                # Format properly
                hours = match.group(1).zfill(2)
                minutes = match.group(2).zfill(2)
                seconds = match.group(3).zfill(2)
                result = f"{hours}:{minutes}:{seconds}"
            else:
                # Look for other timer patterns like "27/2" -> keep as is
                # Or pure numbers
                digits_only = re.sub(r'[^\d]', '', result)
                if len(digits_only) >= 1:
                    result = digits_only
        
        elif region_id.endswith('_task') or region_id.endswith('_name'):
            # Text field specific cleaning
            import re
            
            # Fix common "March Queue" variations
            result = re.sub(r'March\s+(Qu[a-z]{3})\s*(\d?)', r'March Queue \2', result).strip()
            
            # Clean up extra spaces
            result = re.sub(r'\s+', ' ', result)
            
            # If it looks like "March Queue" but has number, format properly
            if 'March Queue' in result:
                numbers = re.findall(r'\d+', result)
                if numbers:
                    result = f"March Queue {numbers[0]}"
                else:
                    result = "March Queue"
        
        elif region_id.endswith('_status'):
            # Status should be simple - single digit or simple text
            import re
            if result.isdigit():
                result = result
            elif 'idle' in result.lower():
                result = 'Idle'
            else:
                # Keep only alphanumeric
                result = re.sub(r'[^a-zA-Z0-9]', '', result)
        
        return result
    
    def _enhanced_ocr(self, screenshot, region: tuple, region_id: str) -> str:
        """Enhanced OCR with adaptive method selection"""
        try:
            x, y, w, h = region
            
            # Extract region safely
            screenshot_height, screenshot_width = screenshot.shape[:2]
            if x + w > screenshot_width or y + h > screenshot_height:
                w = min(w, screenshot_width - x)
                h = min(h, screenshot_height - y)
            
            roi = screenshot[y:y+h, x:x+w]
            
            if roi.size == 0:
                return ""
            
            # Select methods based on region type and performance
            enhancement_methods = self._select_best_methods_for_region(roi, region_id)
            
            self.log(f"🔍 Testing {len(enhancement_methods)} optimized OCR methods for {region_id}...")
            
            all_results = []
            
            for i, (method_name, enhance_method) in enumerate(enhancement_methods, 1):
                try:
                    enhanced_roi = enhance_method(roi)
                    
                    # Use appropriate OCR engine
                    if method_name.startswith("Tesseract"):
                        method_best_text, method_best_conf = self._run_tesseract_ocr(enhanced_roi, method_name)
                    else:
                        # Use EasyOCR with text_threshold for better results
                        results = self.ocr_reader.readtext(enhanced_roi, detail=1, text_threshold=0.3)
                        
                        method_best_text = ""
                        method_best_conf = 0.0
                        
                        if results:
                            for detection in results:
                                bbox, text, confidence = detection
                                if confidence > method_best_conf:
                                    method_best_text = text
                                    method_best_conf = confidence
                    
                    # Clean the text
                    if method_best_text:
                        method_best_text = ' '.join(method_best_text.split())
                    
                    # Calculate enhanced score
                    score = self._calculate_enhanced_score(method_best_text, method_best_conf, region_id, method_name, all_results)
                    
                    result = OCRResult(
                        text=method_best_text,
                        confidence=method_best_conf,
                        method_id=i,
                        method_name=method_name,
                        score=score
                    )
                    all_results.append(result)
                    
                    # Update method tracking
                    self._update_method_stats(method_name, score)
                    
                    self.log(f"   {i:2d}. {method_name:<20}: '{method_best_text}' (conf: {method_best_conf:.3f}, score: {score:.3f})")
                    
                    # Early exit if we get a perfect result
                    if score >= 1.5:
                        self.log(f"🎯 EARLY EXIT: Excellent result found (score: {score:.3f})")
                        best_result = result
                        break
                
                except Exception as e:
                    result = OCRResult("", 0.0, i, method_name, 0.0)
                    all_results.append(result)
                    self.log(f"   {i:2d}. {method_name:<20}: FAILED - {str(e)[:30]}")
                    continue
            else:
                # Find best result by score if no early exit
                best_result = max(all_results, key=lambda r: r.score) if all_results else None
            
            if best_result and best_result.text:
                self.log(f"🏆 WINNER: {best_result.method_name} = '{best_result.text}' (conf: {best_result.confidence:.3f}, score: {best_result.score:.3f})")
                return best_result.text
            else:
                self.log(f"❌ All {len(enhancement_methods)} methods failed to detect readable text")
                return ""
                    
        except Exception as e:
            self.log(f"❌ OCR error: {e}")
            return ""
    
    def _select_best_methods_for_region(self, roi: np.ndarray, region_id: str) -> list:
        """Select only the most promising methods based on region type and image analysis"""
        
        # Quick image analysis
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        brightness = np.mean(gray)
        contrast = np.std(gray)
        size_score = roi.shape[0] * roi.shape[1]
        
        # Based on performance logs, prioritize best performers
        if region_id.endswith('_timer'):
            if size_score < 1000:  # Small region
                return [
                    ("Timer_Format_Specialist", self._method_timer_format_specialist),
                    ("Histogram_Eq", self._method_histogram_eq),
                    ("Tesseract_Numbers", self._method_tesseract_numbers),
                    ("CLAHE_Sharp_6x", self._method_clahe_sharp_6x),
                ]
            else:
                return [
                    ("Multi_Scale_OCR", self._method_multi_scale_ocr),
                    ("Contrast_Stretch", self._method_contrast_stretch),
                    ("Timer_Format_Specialist", self._method_timer_format_specialist),
                    ("Frequency_Domain_Enhance", self._method_frequency_domain_enhance),
                ]
        
        elif region_id.endswith('_status'):
            return [
                ("Single_Digit_Specialist", self._method_single_digit_specialist),
                ("Super_Resolution", self._method_super_resolution),
                ("CLAHE_Sharp_6x", self._method_clahe_sharp_6x),
                ("Small_Text_Enhancer", self._method_small_text_enhancer),
                ("Unsharp_Mask_4x", self._method_unsharp_mask_4x),
            ]
        
        else:  # name/task - Your logs show these work best for text
            return [
                ("MSER_Detection", self._method_mser_detection),
                ("Gamma_Enhance", self._method_gamma_enhance),
                ("Multi_Scale_OCR", self._method_multi_scale_ocr),
                ("Adaptive_Denoise", self._method_adaptive_denoise),
                ("Contrast_Stretch", self._method_contrast_stretch),
                ("Machine_Learning_Inspired", self._method_machine_learning_inspired),
            ]
    
    def _calculate_enhanced_score(self, text: str, confidence: float, region_id: str, method_name: str, previous_results: list = None) -> float:
        """Enhanced scoring system that considers more factors"""
        if not text:
            return 0.0
        
        # Calibrate confidence first
        calibrated_confidence = self._calibrate_confidence(confidence, method_name, len(text), region_id)
        score = calibrated_confidence
        
        # Base scoring improvements
        if 3 <= len(text) <= 50:
            score += 0.1
        
        # Enhanced pattern matching with more specific bonuses
        if region_id.endswith("_timer"):
            # Timer-specific enhancements
            digit_count = sum(1 for c in text if c.isdigit())
            if ":" in text and digit_count >= 4:  # Format like "00:27:00"
                score += 0.6
            elif "/" in text and digit_count >= 2:  # Format like "2/27"
                score += 0.4
            elif digit_count >= 3 and len(text) <= 8:  # Pure digits like "127"
                score += 0.3
            elif any(pattern in text.lower() for pattern in ["gathering", "march"]):
                score += 0.2
        
        elif region_id.endswith("_task"):
            # Task-specific enhancements
            text_clean = text.lower().replace(" ", "")
            if "marchqueue" in text_clean or "march queue" in text.lower():
                score += 0.5
            elif "gathering" in text.lower():
                score += 0.4
            elif any(word in text.lower() for word in ["march", "queue", "idle"]):
                score += 0.3
        
        elif region_id.endswith("_name"):
            # Name-specific enhancements
            text_clean = text.lower().replace(" ", "")
            if "idle" in text.lower() or "idlc" in text.lower():
                score += 0.5  # Idle is very important
            elif "marchqueue" in text_clean or "march queue" in text.lower():
                score += 0.4
            elif len(text) >= 3 and any(c.isalpha() for c in text):
                score += 0.2
        
        elif region_id.endswith("_status"):
            # Status-specific enhancements
            if text.isdigit() and len(text) == 1:
                score += 0.5  # Single digits are perfect for status
            elif text.isdigit() and len(text) <= 3:
                score += 0.3
            elif any(word in text.lower() for word in ["idle", "gathering"]):
                score += 0.4
        
        # Method-specific bonuses
        if "Specialist" in method_name:
            score += 0.1  # Specialist methods get bonus
        
        if "Deep_Learning" in method_name or "Machine_Learning" in method_name:
            score += 0.05  # AI-inspired methods get small bonus
        
        # Consistency bonus (if we have previous results)
        if previous_results:
            similar_results = [r for r in previous_results if r.text == text]
            if len(similar_results) > 1:
                score += 0.1  # Consistency across methods
        
        # Penalty adjustments
        if len(text) < 2:
            score -= 0.4  # Stronger penalty for very short text
        elif len(text) > 100:
            score -= 0.3
        
        # Character quality analysis
        special_chars = sum(1 for c in text if not c.isalnum() and c not in " :.-/")
        if special_chars > len(text) * 0.4:
            score -= 0.2
        
        return max(0.0, score)
    
    def _calibrate_confidence(self, raw_confidence: float, method_name: str, text_length: int, region_type: str) -> float:
        """Calibrate OCR confidence based on known method behaviors"""
        
        # Method-specific calibration based on observations
        calibration_factors = {
            'EasyOCR_methods': 0.8,  # Tend to over-report
            'Tesseract_methods': 1.0,  # Generally accurate
            'Custom_methods': 0.9,  # Slightly optimistic
        }
        
        # Method-specific calibration
        if 'Tesseract' in method_name:
            factor = calibration_factors['Tesseract_methods']
        elif any(x in method_name for x in ['CLAHE', 'Contrast', 'Sobel', 'Gamma', 'MSER']):
            factor = calibration_factors['Custom_methods']
        else:
            factor = calibration_factors['EasyOCR_methods']
        
        calibrated = raw_confidence * factor
        
        # Adjust based on text characteristics
        if text_length < 3:
            calibrated *= 0.8  # Short text is less reliable
        elif text_length > 20:
            calibrated *= 0.9  # Very long text might have errors
        
        # Region-specific adjustments
        if region_type.endswith('_timer') and ':' not in str(text_length):
            calibrated *= 0.7  # Timer without colons is suspicious
        
        return min(1.0, calibrated)
    
    def _update_method_stats(self, method_name: str, score: float):
        """Update method performance statistics"""
        if method_name not in self.method_scores:
            self.method_scores[method_name] = []
            self.method_usage_count[method_name] = 0
        
        self.method_scores[method_name].append(score)
        self.method_usage_count[method_name] += 1
    
    def _log_method_performance(self):
        """Log method performance summary"""
        if not self.method_scores:
            return
        
        self.log("📈 Method Performance Summary:")
        
        # Calculate averages and sort by performance
        method_stats = []
        for method_name, scores in self.method_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                success_rate = sum(1 for s in scores if s > 0.5) / len(scores)
                method_stats.append((method_name, avg_score, success_rate, len(scores)))
        
        # Sort by average score
        method_stats.sort(key=lambda x: x[1], reverse=True)
        
        for method_name, avg_score, success_rate, count in method_stats[:5]:
            self.log(f"   🥇 {method_name:<20}: avg={avg_score:.3f}, success={success_rate:.1%}, uses={count}")
    
    def _is_queue_available(self, task: str, timer: str) -> bool:
        """Enhanced availability check for gathering queues"""
        if not task:
            return False
        
        task_lower = task.lower()
        
        # Check for known busy indicators
        busy_indicators = ["gathering", "march"]
        if any(indicator in task_lower for indicator in busy_indicators):
            # If we have a timer, it's probably busy
            if timer and any(c.isdigit() for c in timer):
                return False
        
        # Check for available indicators
        available_indicators = ["march queue", "idle"]
        if any(indicator in task_lower for indicator in available_indicators):
            return True
        
        # Default to available if we can read something
        return bool(task.strip())
    
    def _is_commander_queue_available(self, name: str, status: str) -> bool:
        """Enhanced availability check for commander queues"""
        if not name:
            return False
        
        name_lower = name.lower()
        status_lower = status.lower() if status else ""
        
        # Check for locked indicators
        if "march queue" in name_lower and not status:
            return False  # Empty status usually means locked
        
        # Check for available indicators
        if "idle" in name_lower or "idle" in status_lower:
            return True
        
        # If we have a meaningful name and status, probably available
        return bool(name.strip() and len(name.strip()) > 2)
    
    def _run_tesseract_ocr(self, enhanced_roi: np.ndarray, method_name: str) -> tuple:
        """Run Tesseract OCR with appropriate configuration"""
        if not self.tesseract_available:
            return "", 0.0
        
        try:
            import pytesseract
            
            # Convert to grayscale if needed
            if len(enhanced_roi.shape) == 3:
                gray = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = enhanced_roi
            
            # Configure Tesseract based on expected content
            if "Numbers" in method_name or "Digits" in method_name:
                # For numbers/digits only
                config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789:/.,'
            elif "Text" in method_name:
                # For text
                config = '--oem 3 --psm 8'
            else:
                # Default
                config = '--oem 3 --psm 6'
            
            # Get text and confidence
            text = pytesseract.image_to_string(gray, config=config).strip()
            
            # Get confidence (Tesseract returns per-character confidence)
            try:
                data = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            except:
                confidence = 0.8 if text else 0.0  # Default confidence if text found
            
            return text, confidence
            
        except Exception as e:
            return "", 0.0
    
    # ===========================================
    # ENHANCED OCR METHODS - FIXED VERSIONS
    # ===========================================
    
    def _method_timer_format_specialist(self, roi: np.ndarray) -> np.ndarray:
        """Specialized method for XX:XX:XX timer format"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Pre-process specifically for timer format
        # 1. Enhance colon visibility
        kernel_vertical = np.array([[1], [1], [1]], dtype=np.uint8)
        enhanced_colons = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_vertical)
        
        # 2. Enhance digit segments
        kernel_digit = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 3))
        enhanced_digits = cv2.morphologyEx(enhanced_colons, cv2.MORPH_CLOSE, kernel_digit)
        
        # 3. Massive upscaling for digit clarity
        h, w = enhanced_digits.shape
        scaled = cv2.resize(enhanced_digits, (w * 15, h * 15), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_deep_learning_upscale(self, roi: np.ndarray) -> np.ndarray:
        """Method: Simulated deep learning super-resolution - FIXED"""
        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
            
            # Ensure minimum size to prevent negative indices
            min_size = 10
            h, w = gray.shape
            if h < min_size or w < min_size:
                # Pad to minimum size
                pad_h = max(0, min_size - h)
                pad_w = max(0, min_size - w)
                gray = cv2.copyMakeBorder(gray, pad_h//2, pad_h//2, pad_w//2, pad_w//2, cv2.BORDER_REFLECT)
                h, w = gray.shape
            
            # Multi-stage upscaling with different kernels
            # Stage 1: Bicubic 2x
            stage1 = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            
            # Stage 2: Edge-preserving smoothing
            stage1_3ch = cv2.cvtColor(stage1, cv2.COLOR_GRAY2BGR)
            smoothed = cv2.edgePreservingFilter(stage1_3ch, flags=2, sigma_s=50, sigma_r=0.4)
            smoothed_gray = cv2.cvtColor(smoothed, cv2.COLOR_BGR2GRAY)
            
            # Stage 3: Safe adaptive sharpening
            grad_x = cv2.Sobel(smoothed_gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(smoothed_gray, cv2.CV_64F, 0, 1, ksize=3)
            grad_mag = np.sqrt(grad_x**2 + grad_y**2)
            
            # Avoid division by zero and ensure valid indices
            if np.max(grad_mag) > 0:
                sharpen_strength = np.clip(grad_mag / np.max(grad_mag) * 2.0, 0.5, 2.0)
            else:
                sharpen_strength = np.ones_like(grad_mag) * 0.5
            
            # Apply varying sharpening with bounds checking
            result = smoothed_gray.copy().astype(np.float64)
            rows, cols = smoothed_gray.shape
            
            for i in range(1, rows - 1):  # Ensure we stay within bounds
                for j in range(1, cols - 1):
                    try:
                        strength = sharpen_strength[i, j]
                        laplacian = (-4 * smoothed_gray[i, j] + 
                                   smoothed_gray[i-1, j] + smoothed_gray[i+1, j] + 
                                   smoothed_gray[i, j-1] + smoothed_gray[i, j+1])
                        result[i, j] = smoothed_gray[i, j] + strength * laplacian * 0.1
                    except IndexError:
                        # Skip problematic pixels
                        continue
            
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            # Final 2x upscale
            h2, w2 = result.shape
            final = cv2.resize(result, (w2 * 2, h2 * 2), interpolation=cv2.INTER_LANCZOS4)
            
            return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            # Fallback to simple super resolution
            return self._method_super_resolution(roi)
    
    def _method_frequency_domain_enhance(self, roi: np.ndarray) -> np.ndarray:
        """Method: Advanced frequency domain text enhancement"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Pad image to avoid edge effects
        rows, cols = gray.shape
        pad_rows = cv2.getOptimalDFTSize(rows)
        pad_cols = cv2.getOptimalDFTSize(cols)
        padded = np.zeros((pad_rows, pad_cols), dtype=np.float32)
        padded[:rows, :cols] = gray.astype(np.float32)
        
        # FFT
        dft = cv2.dft(padded, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # Create sophisticated filter for text enhancement
        crow, ccol = pad_rows // 2, pad_cols // 2
        
        # High-pass filter with text-friendly characteristics
        mask = np.ones((pad_rows, pad_cols, 2), dtype=np.float32)
        
        # Remove very low frequencies (background)
        cv2.circle(mask, (ccol, crow), 20, 0, -1)
        
        # Enhance mid-frequencies where text edges typically are
        y, x = np.ogrid[:pad_rows, :pad_cols]
        center_dist = np.sqrt((x - ccol)**2 + (y - crow)**2)
        
        # Boost frequencies in text range (enhance text edges)
        text_freq_boost = np.where((center_dist > 20) & (center_dist < 100), 1.5, 1.0)
        mask[:, :, 0] *= text_freq_boost
        mask[:, :, 1] *= text_freq_boost
        
        # Apply filter
        filtered_dft = dft_shift * mask
        
        # Inverse FFT
        idft_shift = np.fft.ifftshift(filtered_dft)
        idft = cv2.idft(idft_shift)
        result = cv2.magnitude(idft[:, :, 0], idft[:, :, 1])
        
        # Crop back to original size and normalize
        result = result[:rows, :cols]
        result = np.uint8(cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX))
        
        # Scale up
        h, w = result.shape
        scaled = cv2.resize(result, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_text_oriented_gradients(self, roi: np.ndarray) -> np.ndarray:
        """Method: Text-oriented gradient enhancement - FIXED"""
        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
            
            # Ensure minimum size
            if gray.shape[0] < 3 or gray.shape[1] < 3:
                # Pad small images
                gray = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_REFLECT)
            
            # Calculate gradients in multiple directions
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Diagonal gradients for slanted text - FIXED kernel application
            kernel_diag1 = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
            kernel_diag2 = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
            
            # Safe filter application
            grad_diag1 = cv2.filter2D(gray, cv2.CV_64F, kernel_diag1)
            grad_diag2 = cv2.filter2D(gray, cv2.CV_64F, kernel_diag2)
            
            # Combine gradients with weights favoring text-like structures
            combined_grad = np.sqrt(grad_x**2 * 0.4 + grad_y**2 * 0.4 + grad_diag1**2 * 0.1 + grad_diag2**2 * 0.1)
            
            # Normalize and enhance
            if np.max(combined_grad) > 0:
                combined_grad = np.uint8(cv2.normalize(combined_grad, None, 0, 255, cv2.NORM_MINMAX))
            else:
                combined_grad = np.zeros_like(gray, dtype=np.uint8)
            
            # Combine with original using adaptive weighting
            alpha = 0.6
            enhanced = cv2.addWeighted(gray, alpha, combined_grad, 1-alpha, 0)
            
            # Apply text-specific morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))  # Horizontal emphasis
            enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            # Scale up
            h, w = enhanced.shape
            scaled = cv2.resize(enhanced, (w * 5, h * 5), interpolation=cv2.INTER_CUBIC)
            
            return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            # Fallback to simple enhancement
            return self._method_contrast_stretch(roi)
    
    def _method_single_digit_specialist(self, roi: np.ndarray) -> np.ndarray:
        """Method: Optimized for single digits (status indicators)"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Massive padding for single characters
        h, w = gray.shape
        pad_size = max(h, w, 20)
        
        padded = cv2.copyMakeBorder(gray, pad_size, pad_size, pad_size, pad_size, 
                                   cv2.BORDER_CONSTANT, value=255)
        
        # Find the main character region
        _, binary = cv2.threshold(padded, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find largest connected component (the digit)
        contours, _ = cv2.findContours(255 - binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Extract digit with padding
            digit_roi = padded[max(0, y-10):y+h+10, max(0, x-10):x+w+10]
            
            # Extreme upscaling for single digit
            dh, dw = digit_roi.shape
            scaled_digit = cv2.resize(digit_roi, (dw * 20, dh * 20), interpolation=cv2.INTER_CUBIC)
            
            return cv2.cvtColor(scaled_digit, cv2.COLOR_GRAY2BGR)
        
        # Fallback: just massive upscaling
        ph, pw = padded.shape
        scaled = cv2.resize(padded, (pw * 15, ph * 15), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_small_text_enhancer(self, roi: np.ndarray) -> np.ndarray:
        """Method: Specialized for very small text"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Check if image is very small
        if gray.shape[0] < 20 or gray.shape[1] < 50:
            # Pad the image first
            pad_y = max(20 - gray.shape[0], 0)
            pad_x = max(50 - gray.shape[1], 0)
            gray = cv2.copyMakeBorder(gray, pad_y//2, pad_y//2, pad_x//2, pad_x//2, 
                                     cv2.BORDER_REFLECT)
        
        # Extreme upscaling first
        h, w = gray.shape
        upscaled = cv2.resize(gray, (w * 8, h * 8), interpolation=cv2.INTER_CUBIC)
        
        # Apply strong sharpening
        kernel = np.array([[-2,-2,-2], [-2,17,-2], [-2,-2,-2]])
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        enhanced = clahe.apply(sharpened)
        
        # Final upscaling
        h2, w2 = enhanced.shape
        final = cv2.resize(enhanced, (w2 * 2, h2 * 2), interpolation=cv2.INTER_LANCZOS4)
        
        return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
    
    def _method_machine_learning_inspired(self, roi: np.ndarray) -> np.ndarray:
        """Method: ML-inspired feature enhancement"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Feature extraction inspired by CNN layers
        
        # Layer 1: Edge detection (like first conv layer)
        edges = cv2.Canny(gray, 50, 150)
        
        # Layer 2: Multiple filter responses (like conv layer)
        filters = [
            np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),  # Vertical edges
            np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]),  # Horizontal edges
            np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]),    # Laplacian
            np.array([[1, 0, -1], [0, 0, 0], [-1, 0, 1]]),   # Diagonal
        ]
        
        feature_maps = []
        for filt in filters:
            filtered = cv2.filter2D(gray, cv2.CV_64F, filt)
            feature_maps.append(np.abs(filtered))
        
        # Layer 3: Non-linear activation (ReLU-like)
        activated_maps = []
        for fm in feature_maps:
            # Apply threshold (like ReLU)
            activated = np.where(fm > 30, fm, 0)
            activated_maps.append(activated)
        
        # Layer 4: Pooling-like operation (local maxima)
        pooled_maps = []
        for am in activated_maps:
            # Max pooling 2x2
            pooled = am[::2, ::2]  # Simple downsampling
            # Upsample back
            upsampled = cv2.resize(pooled, (am.shape[1], am.shape[0]), interpolation=cv2.INTER_NEAREST)
            pooled_maps.append(upsampled)
        
        # Combine feature maps
        combined_features = np.sum(pooled_maps, axis=0)
        combined_features = np.uint8(cv2.normalize(combined_features, None, 0, 255, cv2.NORM_MINMAX))
        
        # Final combination with original
        result = cv2.addWeighted(gray, 0.7, combined_features, 0.3, 0)
        
        # Scale up
        h, w = result.shape
        scaled = cv2.resize(result, (w * 6, h * 6), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    # ===========================================
    # EXISTING METHODS (keeping the best ones)
    # ===========================================
    
    def _method_histogram_eq(self, roi: np.ndarray) -> np.ndarray:
        """Method: Histogram equalization"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Histogram equalization
        equalized = cv2.equalizeHist(gray)
        
        # Scale up
        h, w = equalized.shape
        scaled = cv2.resize(equalized, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_tesseract_numbers(self, roi: np.ndarray) -> np.ndarray:
        """Method: Tesseract optimized for numbers/timers"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Optimize for number recognition
        # Increase contrast
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
        
        # Scale up significantly
        h, w = enhanced.shape
        scaled = cv2.resize(enhanced, (w * 8, h * 8), interpolation=cv2.INTER_CUBIC)
        
        # Apply strong threshold
        _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def _method_clahe_sharp_6x(self, roi: np.ndarray) -> np.ndarray:
        """Method: CLAHE + Sharpening + 6x scaling"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Sharpening kernel
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Scale up 6x
        h, w = sharpened.shape
        scaled = cv2.resize(sharpened, (w * 6, h * 6), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_super_resolution(self, roi: np.ndarray) -> np.ndarray:
        """Method: Simple super-resolution using interpolation"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Multi-stage upsampling for better quality
        # Stage 1: 2x with cubic
        h, w = gray.shape
        stage1 = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        
        # Stage 2: Apply sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(stage1, -1, kernel)
        
        # Stage 3: Another 2x upsampling
        h2, w2 = sharpened.shape
        stage2 = cv2.resize(sharpened, (w2 * 2, h2 * 2), interpolation=cv2.INTER_LANCZOS4)
        
        # Stage 4: Final 2x with edge-preserving
        h3, w3 = stage2.shape
        final = cv2.resize(stage2, (w3 * 2, h3 * 2), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
    
    def _method_unsharp_mask_4x(self, roi: np.ndarray) -> np.ndarray:
        """Method: Unsharp masking + 4x scaling"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Unsharp masking
        blurred = cv2.GaussianBlur(gray, (0, 0), 2.0)
        unsharp = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
        
        # Scale up
        h, w = unsharp.shape
        scaled = cv2.resize(unsharp, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_contrast_stretch(self, roi: np.ndarray) -> np.ndarray:
        """Method: Histogram stretching for better contrast"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Calculate percentiles for stretching
        p2, p98 = np.percentile(gray, (2, 98))
        
        # Apply contrast stretching
        stretched = np.clip((gray - p2) * 255.0 / (p98 - p2), 0, 255).astype(np.uint8)
        
        # Additional sharpening
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        sharpened = cv2.filter2D(stretched, -1, kernel)
        
        # Scale up
        h, w = sharpened.shape
        scaled = cv2.resize(sharpened, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_multi_scale_ocr(self, roi: np.ndarray) -> np.ndarray:
        """Method: Multi-scale processing optimized for OCR"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Process at multiple scales and combine
        scales = [2, 3, 4]
        results = []
        
        for scale in scales:
            h, w = gray.shape
            scaled = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
            
            # Apply different processing for each scale
            if scale == 2:
                # Light processing for 2x
                processed = cv2.bilateralFilter(scaled, 5, 50, 50)
            elif scale == 3:
                # Medium processing for 3x
                processed = cv2.GaussianBlur(scaled, (3, 3), 0)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                processed = clahe.apply(processed)
            else:
                # Heavy processing for 4x
                processed = cv2.fastNlMeansDenoising(scaled, h=8)
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                processed = cv2.filter2D(processed, -1, kernel)
            
            results.append(processed)
        
        # Use the 4x scale result (most processed)
        return cv2.cvtColor(results[2], cv2.COLOR_GRAY2BGR)
    
    def _method_adaptive_denoise(self, roi: np.ndarray) -> np.ndarray:
        """Method: Adaptive denoising based on image characteristics"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Calculate noise level
        noise_level = np.std(cv2.Laplacian(gray, cv2.CV_64F))
        
        # Adaptive denoising strength
        h_value = min(15, max(5, noise_level / 10))
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, h=h_value)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
        enhanced = clahe.apply(denoised)
        
        # Scale up
        h, w = enhanced.shape
        scaled = cv2.resize(enhanced, (w * 5, h * 5), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_gamma_enhance(self, roi: np.ndarray) -> np.ndarray:
        """Method: Gamma correction + enhancement"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Gamma correction
        gamma = 1.2
        lookupTable = np.empty((1,256), np.uint8)
        for i in range(256):
            lookupTable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
        corrected = cv2.LUT(gray, lookupTable)
        
        # Scale up
        h, w = corrected.shape
        scaled = cv2.resize(corrected, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    
    def _method_mser_detection(self, roi: np.ndarray) -> np.ndarray:
        """Method: MSER (Maximally Stable Extremal Regions) for text detection"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi.copy()
        
        # Create MSER detector
        mser = cv2.MSER_create()
        
        # Detect regions
        regions, _ = mser.detectRegions(gray)
        
        # Create mask from detected regions
        mask = np.zeros_like(gray)
        for region in regions:
            # Convert region to contour format
            hull = cv2.convexHull(region.reshape(-1, 1, 2))
            cv2.fillPoly(mask, [hull], 255)
        
        # Apply mask to enhance text regions
        enhanced = cv2.bitwise_and(gray, mask)
        
        # If no regions found, use original
        if np.sum(enhanced) == 0:
            enhanced = gray
        
        # Scale up
        h, w = enhanced.shape
        scaled = cv2.resize(enhanced, (w * 6, h * 6), interpolation=cv2.INTER_CUBIC)
        
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)