"""
BENSON v2.0 - Enhanced OCR Operations Handler (Compatible Version)
Works with existing OCR helper without modifications
"""

import tkinter as tk
from tkinter import messagebox
import threading
from PIL import Image, ImageEnhance, ImageFilter
import os
import tempfile


class OCRHandler:
    """Handles OCR operations for the main application"""
    
    def __init__(self, app_ref):
        self.app = app_ref
        self.ocr_helper = getattr(app_ref, 'ocr_helper', None)
    
    def test_instance_ocr(self, instance_name, region_name="left_panel"):
        """Test OCR on a specific instance with default region"""
        self.test_instance_ocr_region(instance_name, region_name)
    
    def test_instance_ocr_region(self, instance_name, region_name):
        """Test OCR on a specific instance with specified region"""
        if not self.ocr_helper:
            self._show_ocr_not_available_dialog()
            return
        
        # Get instance details
        instance = self.app.instance_manager.get_instance(instance_name)
        if not instance:
            self.app.add_console_message(f"❌ OCR test failed: Instance {instance_name} not found")
            return
        
        region_display = region_name.replace("_", " ").title()
        self.app.add_console_message(f"🔍 Starting OCR test on {instance_name} ({region_display} region)...")
        
        def ocr_worker():
            try:
                # Perform OCR operation with region
                result = self.ocr_helper.perform_ocr_on_memu_instance(
                    instance["index"], 
                    self.app.instance_manager.MEMUC_PATH,
                    instance_name,
                    region_name=region_name,
                    confidence_threshold=0.3
                )
                
                # Update UI on main thread
                self.app.after(0, lambda: self.handle_ocr_result(result))
                
            except Exception as e:
                error_msg = f"OCR test failed for {instance_name}: {str(e)}"
                print(f"[OCRHandler] {error_msg}")
                self.app.after(0, lambda: self.app.add_console_message(f"❌ {error_msg}"))
        
        # Run OCR in background thread
        threading.Thread(target=ocr_worker, daemon=True).start()
    
    def test_instance_ocr_custom(self, instance_name, custom_region):
        """Test OCR on a specific instance with custom region and enhanced preprocessing"""
        if not self.ocr_helper:
            self.app.add_console_message("❌ OCR test failed: Required packages not installed")
            return
        
        # Get instance details
        instance = self.app.instance_manager.get_instance(instance_name)
        if not instance:
            self.app.add_console_message(f"❌ OCR test failed: Instance {instance_name} not found")
            return
        
        region_info = f"x={custom_region['x']:.3f}, y={custom_region['y']:.3f}, w={custom_region['width']:.3f}, h={custom_region['height']:.3f}"
        self.app.add_console_message(f"🔍 Starting enhanced OCR test on {instance_name} ({region_info})...")
        
        def ocr_worker():
            enhanced_screenshot_path = None
            original_screenshot_path = None
            
            try:
                # First, capture the screenshot
                original_screenshot_path = self.ocr_helper.capture_memu_adb_screenshot(
                    instance["index"],
                    self.app.instance_manager.MEMUC_PATH
                )
                
                if not original_screenshot_path:
                    raise ValueError("Failed to capture screenshot")
                
                # Create enhanced version of the screenshot
                enhanced_screenshot_path = self._create_enhanced_screenshot(
                    original_screenshot_path, custom_region, instance_name
                )
                
                if enhanced_screenshot_path:
                    # Temporarily replace the original screenshot
                    backup_path = original_screenshot_path + ".backup"
                    os.rename(original_screenshot_path, backup_path)
                    os.rename(enhanced_screenshot_path, original_screenshot_path)
                    
                    try:
                        # Use full region on the enhanced image
                        full_region = {'x': 0.0, 'y': 0.0, 'width': 1.0, 'height': 1.0}
                        
                        result = self.ocr_helper.perform_ocr_on_memu_instance(
                            instance["index"], 
                            self.app.instance_manager.MEMUC_PATH,
                            instance_name,
                            region_name="custom",
                            custom_region=full_region,
                            confidence_threshold=0.1  # Lower threshold for time detection
                        )
                        
                        # Add enhancement info to result
                        result['enhanced'] = True
                        result['original_region'] = custom_region
                        
                    finally:
                        # Restore original screenshot
                        if os.path.exists(original_screenshot_path):
                            os.remove(original_screenshot_path)
                        os.rename(backup_path, original_screenshot_path)
                        
                else:
                    # Fallback to regular OCR if enhancement failed
                    self.app.add_console_message("⚠️ Enhancement failed, using regular OCR...")
                    result = self.ocr_helper.perform_ocr_on_memu_instance(
                        instance["index"], 
                        self.app.instance_manager.MEMUC_PATH,
                        instance_name,
                        region_name="custom",
                        custom_region=custom_region,
                        confidence_threshold=0.1
                    )
                    result['enhanced'] = False
                
                # Update UI on main thread
                self.app.after(0, lambda: self.handle_ocr_result(result))
                
            except Exception as e:
                error_msg = f"Enhanced OCR test failed for {instance_name}: {str(e)}"
                print(f"[OCRHandler] {error_msg}")
                self.app.after(0, lambda: self.app.add_console_message(f"❌ {error_msg}"))
            
            finally:
                # Clean up any remaining files
                try:
                    if enhanced_screenshot_path and os.path.exists(enhanced_screenshot_path):
                        os.remove(enhanced_screenshot_path)
                except:
                    pass
        
        # Run OCR in background thread
        threading.Thread(target=ocr_worker, daemon=True).start()
    
    def _create_enhanced_screenshot(self, original_path, custom_region, instance_name):
        """Create an enhanced version of the screenshot focused on the custom region"""
        try:
            # Load the original image
            image = Image.open(original_path)
            
            # Calculate crop coordinates
            width, height = image.size
            x1 = int(custom_region['x'] * width)
            y1 = int(custom_region['y'] * height)
            x2 = int((custom_region['x'] + custom_region['width']) * width)
            y2 = int((custom_region['y'] + custom_region['height']) * height)
            
            # Crop to the region
            cropped = image.crop((x1, y1, x2, y2))
            orig_width, orig_height = cropped.size
            
            # Scale up the image significantly for better OCR
            target_width = max(300, orig_width * 4)  # At least 300px wide or 4x original
            scale_factor = target_width / orig_width
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            
            # Use LANCZOS for high-quality upscaling
            enhanced = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale for better text recognition
            enhanced = enhanced.convert('L')
            
            # Enhance contrast for better text visibility
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(2.5)  # Strong contrast boost
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(2.0)
            
            # Apply noise reduction and sharpening
            enhanced = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            # Create temporary file for enhanced image
            temp_dir = tempfile.gettempdir()
            timestamp = str(int(time.time() * 1000)) if 'time' in globals() else "temp"
            enhanced_path = os.path.join(temp_dir, f"enhanced_ocr_{instance_name}_{timestamp}.png")
            
            # Save enhanced image
            enhanced.save(enhanced_path)
            
            # Also save debug copy to desktop
            try:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                debug_filename = f"ocr_enhanced_{instance_name}_{custom_region['x']:.3f}_{custom_region['y']:.3f}.png"
                debug_path = os.path.join(desktop, debug_filename)
                enhanced.save(debug_path)
                print(f"[OCRHandler] Enhanced image saved to desktop: {debug_filename}")
                print(f"[OCRHandler] Scaled from {orig_width}x{orig_height} to {new_width}x{new_height}")
            except Exception as e:
                print(f"[OCRHandler] Could not save debug image: {e}")
            
            return enhanced_path
            
        except Exception as e:
            print(f"[OCRHandler] Error creating enhanced screenshot: {e}")
            return None
    
    def handle_ocr_result(self, result):
        """Handle OCR result on main thread with enhanced time detection"""
        try:
            if result['success']:
                # Check if we found any time-like patterns
                time_patterns = self._extract_time_patterns(result)
                
                # Format and display results
                console_output = self.ocr_helper.format_ocr_results_for_console(result)
                
                # Add enhancement info
                if result.get('enhanced', False):
                    console_output += "\n🔧 Used enhanced image preprocessing"
                
                # Add time pattern info if found
                if time_patterns:
                    console_output += f"\n🕒 Detected time patterns: {', '.join(time_patterns)}"
                    self.app.add_console_message(console_output)
                    self.app.add_console_message(f"✅ SUCCESS: Found time value(s): {', '.join(time_patterns)}")
                else:
                    self.app.add_console_message(console_output)
                    if result['text_count'] > 0:
                        self.app.add_console_message("⚠️ Text found but no time patterns detected")
                    else:
                        self.app.add_console_message("💡 No text detected. Try: larger region, higher contrast area, or different location")
                
                # Show detailed results in a popup if there's text
                if result['text_count'] > 0:
                    self.show_ocr_results_dialog(result, time_patterns)
                
            else:
                error_msg = result.get('error', 'Unknown error')
                self.app.add_console_message(f"❌ OCR test failed: {error_msg}")
                
        except Exception as e:
            print(f"[OCRHandler] Error handling OCR result: {e}")
            self.app.add_console_message(f"❌ Error processing OCR result: {str(e)}")
    
    def _extract_time_patterns(self, result):
        """Extract time-like patterns from OCR results"""
        import re
        
        time_patterns = []
        
        # Common time patterns
        patterns = [
            r'\d{1,2}:\d{2}:\d{2}',  # HH:MM:SS or H:MM:SS
            r'\d{2,3}:\d{2}:\d{2}',  # MMM:MM:SS (for very long times)
            r'\d{1,2}:\d{2}',        # HH:MM or H:MM
            r'\d+:\d{2}',            # Any number followed by :XX
            r'\d{2}:\d{2}:\d{2}',    # Strict HH:MM:SS
        ]
        
        # Check full text first
        full_text = result.get('full_text', '')
        
        for pattern in patterns:
            matches = re.findall(pattern, full_text)
            time_patterns.extend(matches)
        
        # Also check individual text elements
        for text_item in result.get('texts', []):
            text = text_item.get('text', '').strip()
            
            # Clean up common OCR errors in time text
            text = text.replace('O', '0').replace('l', '1').replace('I', '1').replace('S', '5')
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                time_patterns.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for pattern in time_patterns:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)
        
        return unique_patterns
    
    def show_ocr_results_dialog(self, result, time_patterns=None):
        """Show detailed OCR results in a dialog with time pattern highlighting"""
        try:
            # Create results window
            results_window = tk.Toplevel(self.app)
            results_window.title(f"OCR Results - {result['instance_name']}")
            results_window.geometry("800x600")
            results_window.configure(bg="#1e2329")
            results_window.transient(self.app)
            
            # Center the window
            results_window.update_idletasks()
            x = (results_window.winfo_screenwidth() // 2) - (400)
            y = (results_window.winfo_screenheight() // 2) - (300)
            results_window.geometry(f"800x600+{x}+{y}")
            
            # Title with region info
            region_info = f" [{result.get('region', 'Unknown')} region]"
            if result.get('enhanced', False):
                region_info += " [Enhanced]"
            
            title = tk.Label(
                results_window,
                text=f"🔍 OCR Results - {result['instance_name']}{region_info}",
                bg="#1e2329",
                fg="#00d4ff",
                font=("Segoe UI", 14, "bold")
            )
            title.pack(pady=20)
            
            # Time patterns section (if found)
            if time_patterns:
                time_frame = tk.Frame(results_window, bg="#1e2329")
                time_frame.pack(pady=(0, 10), padx=20, fill="x")
                
                time_label = tk.Label(
                    time_frame,
                    text=f"🕒 Time Patterns Found: {', '.join(time_patterns)}",
                    bg="#1e2329",
                    fg="#00ff88",
                    font=("Segoe UI", 12, "bold")
                )
                time_label.pack()
            
            # Stats frame
            stats_frame = tk.Frame(results_window, bg="#1e2329")
            stats_frame.pack(pady=10)
            
            stats_text = (f"Processing Time: {result['processing_time']}s | "
                         f"Text Count: {result['text_count']} | "
                         f"Confidence Threshold: {result.get('confidence_threshold', 'N/A')}")
            
            stats_label = tk.Label(
                stats_frame,
                text=stats_text,
                bg="#1e2329",
                fg="#8b949e",
                font=("Segoe UI", 10)
            )
            stats_label.pack()
            
            # Results text with scrollbar
            text_frame = tk.Frame(results_window, bg="#1e2329")
            text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            results_text = tk.Text(
                text_frame,
                bg="#0a0e16",
                fg="#ffffff",
                font=("Segoe UI", 11),
                relief="flat",
                bd=0,
                wrap="word",
                padx=10,
                pady=10
            )
            
            scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=scrollbar.set)
            
            results_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Insert formatted results
            full_text = result['full_text'] if result['full_text'] else "No text found"
            results_text.insert("1.0", full_text)
            
            # Add detailed breakdown
            if result['text_count'] > 0:
                results_text.insert("end", "\n\n" + "="*50 + "\nDetailed Breakdown:\n" + "="*50 + "\n")
                for i, item in enumerate(result['texts'], 1):
                    confidence_bar = "█" * int(item['confidence'] * 10)
                    results_text.insert("end", f"\n{i}. \"{item['text']}\"\n")
                    results_text.insert("end", f"   Confidence: {item['confidence']:.3f} {confidence_bar}\n")
                    
                    # Highlight if this looks like a time pattern
                    if time_patterns:
                        for pattern in time_patterns:
                            if pattern in item['text']:
                                results_text.insert("end", f"   ⭐ TIME PATTERN DETECTED! ⭐\n")
                                break
            
            results_text.configure(state="disabled")
            
            # Button frame
            button_frame = tk.Frame(results_window, bg="#1e2329")
            button_frame.pack(pady=20)
            
            # Copy time patterns button (if found)
            if time_patterns:
                copy_time_btn = tk.Button(
                    button_frame,
                    text="🕒 Copy Time",
                    bg="#00ff88",
                    fg="#000000",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat",
                    bd=0,
                    padx=20,
                    pady=8,
                    cursor="hand2",
                    command=lambda: self._copy_to_clipboard(', '.join(time_patterns))
                )
                copy_time_btn.pack(side="left", padx=(0, 10))
            
            # Copy all text button
            copy_btn = tk.Button(
                button_frame,
                text="📋 Copy All",
                bg="#2196f3",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                bd=0,
                padx=20,
                pady=8,
                cursor="hand2",
                command=lambda: self._copy_to_clipboard(result['full_text'])
            )
            copy_btn.pack(side="left", padx=(0, 10))
            
            # Close button
            close_btn = tk.Button(
                button_frame,
                text="✗ Close",
                bg="#ff6b6b",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                bd=0,
                padx=20,
                pady=8,
                cursor="hand2",
                command=results_window.destroy
            )
            close_btn.pack(side="left")
            
        except Exception as e:
            print(f"[OCRHandler] Error showing OCR results dialog: {e}")
            # Fallback to simple message box
            text_preview = result['full_text'][:200] + "..." if len(result['full_text']) > 200 else result['full_text']
            if time_patterns:
                text_preview = f"Time: {', '.join(time_patterns)}\n\n{text_preview}"
            messagebox.showinfo("OCR Results", text_preview)
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.app.clipboard_clear()
            self.app.clipboard_append(text)
            self.app.add_console_message(f"📋 Copied: {text[:50]}{'...' if len(text) > 50 else ''}")
        except Exception as e:
            self.app.add_console_message(f"❌ Failed to copy: {str(e)}")
    
    def _show_ocr_not_available_dialog(self):
        """Show OCR not available dialog"""
        install_msg = """OCR functionality requires additional packages.

Install with:
pip install easyocr opencv-python pillow

Optional (for better window capture):
pip install pyautogui pygetwindow

Note: EasyOCR will download language models on first use (~47MB)"""
        
        messagebox.showinfo("OCR Not Available", install_msg)
        self.app.add_console_message("❌ OCR test failed: Required packages not installed")


# Add this import at the top if missing
import time