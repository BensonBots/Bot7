"""
BENSON v2.0 - InternVL OCR Queue Analyzer
Uses InternVL multimodal AI for intelligent march queue analysis
"""

import os
import base64
import time
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class QueueInfo:
    """Information about a march queue"""
    name: str = ""
    task: str = ""
    status: str = ""
    time_remaining: str = ""
    is_available: bool = False


class InternVLQueueAnalyzer:
    """Advanced OCR analysis using InternVL multimodal AI"""
    
    def __init__(self, instance_name: str, config, log_callback=None):
        self.instance_name = instance_name
        self.config = config
        self.log_callback = log_callback or print
        
        # InternVL API configuration
        self.api_url = "https://opengllab-internvl.hf.space/api/predict"
        self.model_name = "OpenGVLab/InternVL2-8B"
        self.max_retries = 3
        self.timeout = 30
        
        # Queue analysis prompts
        self.queue_analysis_prompt = """
Look at this march queue interface screenshot. I need you to analyze each visible march queue and tell me:

For each queue (numbered 1, 2, 3, 4, 5, 6), identify:
1. Is the queue AVAILABLE (idle/empty) or BUSY (has a task running)?
2. If busy, what task is it doing? (gathering, marching, etc.)
3. If there's a timer, what time is remaining?

Please respond in this exact JSON format:
{
    "queues": {
        "1": {"available": true/false, "task": "task description", "timer": "time if any"},
        "2": {"available": true/false, "task": "task description", "timer": "time if any"},
        etc.
    }
}

Only include queues that you can clearly see in the image. If a queue is empty/idle/available, set available=true and task="idle".
"""
        
        self.log("✅ InternVL OCR Analyzer initialized")
    
    def log(self, message: str):
        """Log message"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [InternVL-{self.instance_name}] {message}"
        self.log_callback(formatted_message)
    
    def analyze_march_queues(self, screenshot_path: str) -> Dict[int, QueueInfo]:
        """Analyze march queues using InternVL multimodal AI"""
        try:
            self.log("🤖 Starting InternVL AI queue analysis...")
            
            if not os.path.exists(screenshot_path):
                self.log("❌ Screenshot file not found")
                return {}
            
            # Convert image to base64
            image_base64 = self._encode_image_to_base64(screenshot_path)
            if not image_base64:
                self.log("❌ Failed to encode image")
                return {}
            
            # Query InternVL API
            ai_response = self._query_internvl_api(image_base64)
            if not ai_response:
                self.log("❌ Failed to get AI response")
                return {}
            
            # Parse AI response into queue info
            queues = self._parse_ai_response(ai_response)
            
            # Log results
            available_count = len([q for q in queues.values() if q.is_available])
            self.log(f"✅ InternVL analysis complete - {len(queues)} queues analyzed, {available_count} available")
            
            return queues
            
        except Exception as e:
            self.log(f"❌ InternVL analysis error: {e}")
            return {}
    
    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 for API"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            self.log(f"❌ Image encoding error: {e}")
            return None
    
    def _query_internvl_api(self, image_base64: str) -> Optional[str]:
        """Query InternVL API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.log(f"🌐 Querying InternVL API (attempt {attempt + 1}/{self.max_retries})...")
                
                # Prepare API payload
                payload = {
                    "data": [
                        image_base64,  # Image in base64 format
                        self.queue_analysis_prompt,  # Text prompt
                        {
                            "max_new_tokens": 1000,
                            "temperature": 0.1,  # Low temperature for consistent results
                            "top_p": 0.9,
                            "seed": 42  # Fixed seed for reproducibility
                        }
                    ]
                }
                
                # Make API request
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'BENSON-OCR-Client/1.0'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the AI response text
                    if 'data' in result and len(result['data']) > 0:
                        ai_text = result['data'][0]
                        self.log(f"✅ Got AI response ({len(ai_text)} chars)")
                        return ai_text
                    else:
                        self.log("❌ Empty response from API")
                        
                else:
                    self.log(f"❌ API error: {response.status_code} - {response.text}")
                
            except requests.exceptions.Timeout:
                self.log(f"⏱️ API timeout on attempt {attempt + 1}")
            except requests.exceptions.RequestException as e:
                self.log(f"🌐 Network error: {e}")
            except Exception as e:
                self.log(f"❌ API query error: {e}")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                self.log(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        self.log("❌ All API attempts failed")
        return None
    
    def _parse_ai_response(self, ai_response: str) -> Dict[int, QueueInfo]:
        """Parse AI response into QueueInfo objects"""
        try:
            self.log("🔍 Parsing AI response...")
            
            # Log the raw response for debugging
            self.log(f"📝 AI Response: {ai_response[:200]}...")
            
            # Try to extract JSON from the response
            json_data = self._extract_json_from_response(ai_response)
            
            if not json_data:
                self.log("❌ Could not extract valid JSON from AI response")
                return {}
            
            queues = {}
            
            # Parse each queue from the JSON
            if 'queues' in json_data:
                for queue_str, queue_data in json_data['queues'].items():
                    try:
                        queue_num = int(queue_str)
                        
                        queue_info = QueueInfo()
                        queue_info.is_available = queue_data.get('available', False)
                        queue_info.task = queue_data.get('task', '')
                        queue_info.time_remaining = queue_data.get('timer', '')
                        
                        # Set status based on availability
                        if queue_info.is_available:
                            queue_info.status = 'Available'
                            queue_info.name = 'Idle'
                        else:
                            queue_info.status = 'Busy'
                            queue_info.name = queue_info.task
                        
                        queues[queue_num] = queue_info
                        
                        # Log individual queue results
                        status = "AVAILABLE" if queue_info.is_available else "BUSY"
                        task_info = f" ({queue_info.task})" if queue_info.task and queue_info.task != 'idle' else ""
                        timer_info = f" - {queue_info.time_remaining}" if queue_info.time_remaining else ""
                        
                        self.log(f"📊 Queue {queue_num}: {status}{task_info}{timer_info}")
                        
                    except (ValueError, KeyError) as e:
                        self.log(f"⚠️ Error parsing queue {queue_str}: {e}")
                        continue
            
            return queues
            
        except Exception as e:
            self.log(f"❌ Error parsing AI response: {e}")
            return {}
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from AI response text"""
        try:
            # Try to find JSON in the response
            # Look for content between { and }
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx + 1]
                
                # Try to parse the JSON
                try:
                    json_data = json.loads(json_str)
                    self.log("✅ Successfully extracted JSON from AI response")
                    return json_data
                except json.JSONDecodeError:
                    self.log("⚠️ Found JSON-like text but couldn't parse it")
            
            # Fallback: try to parse the entire response as JSON
            try:
                json_data = json.loads(response)
                self.log("✅ Parsed entire response as JSON")
                return json_data
            except json.JSONDecodeError:
                pass
            
            # If JSON parsing fails, try to create structured data from text
            return self._fallback_text_parsing(response)
            
        except Exception as e:
            self.log(f"❌ JSON extraction error: {e}")
            return None
    
    def _fallback_text_parsing(self, response: str) -> Optional[Dict]:
        """Fallback text parsing if JSON extraction fails"""
        try:
            self.log("🔄 Attempting fallback text parsing...")
            
            # Look for queue information in text format
            lines = response.split('\n')
            queues_data = {}
            
            for line in lines:
                line = line.strip()
                
                # Look for patterns like "Queue 1: Available" or "Queue 2: Busy (Gathering)"
                if 'queue' in line.lower() and ':' in line:
                    try:
                        # Extract queue number
                        queue_part = line.split(':')[0].lower()
                        queue_num = None
                        
                        for char in queue_part:
                            if char.isdigit():
                                queue_num = int(char)
                                break
                        
                        if queue_num is None:
                            continue
                        
                        # Extract status
                        status_part = line.split(':', 1)[1].strip().lower()
                        
                        is_available = any(word in status_part for word in ['available', 'idle', 'empty', 'free'])
                        
                        task = 'idle' if is_available else 'busy'
                        if not is_available and '(' in status_part and ')' in status_part:
                            # Extract task from parentheses
                            task_start = status_part.find('(') + 1
                            task_end = status_part.find(')')
                            if task_end > task_start:
                                task = status_part[task_start:task_end].strip()
                        
                        queues_data[str(queue_num)] = {
                            'available': is_available,
                            'task': task,
                            'timer': ''
                        }
                        
                    except Exception as e:
                        self.log(f"⚠️ Error parsing line '{line}': {e}")
                        continue
            
            if queues_data:
                self.log(f"✅ Fallback parsing found {len(queues_data)} queues")
                return {'queues': queues_data}
            else:
                self.log("❌ Fallback parsing found no queue data")
                return None
                
        except Exception as e:
            self.log(f"❌ Fallback parsing error: {e}")
            return None
    
    def get_api_status(self) -> Dict:
        """Check if InternVL API is accessible"""
        try:
            self.log("🔍 Checking InternVL API status...")
            
            # Simple test request
            test_response = requests.get(
                "https://opengllab-internvl.hf.space/",
                timeout=10,
                headers={'User-Agent': 'BENSON-OCR-Client/1.0'}
            )
            
            if test_response.status_code == 200:
                self.log("✅ InternVL API is accessible")
                return {"status": "available", "code": 200}
            else:
                self.log(f"⚠️ InternVL API returned {test_response.status_code}")
                return {"status": "limited", "code": test_response.status_code}
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ InternVL API not accessible: {e}")
            return {"status": "unavailable", "error": str(e)}
        except Exception as e:
            self.log(f"❌ API status check error: {e}")
            return {"status": "error", "error": str(e)}