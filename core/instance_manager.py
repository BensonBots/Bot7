"""
BENSON v2.0 - Compact Instance Manager
Reduced from 300+ lines to ~150 lines while keeping all functionality
"""

import subprocess
import re
import time
import os
import threading


class InstanceManager:
    """Compact instance manager with MEmu operations"""

    def __init__(self):
        self.MEMUC_PATH = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        
        if not os.path.exists(self.MEMUC_PATH):
            raise FileNotFoundError(f"MEmu not found at {self.MEMUC_PATH}")
        
        self.instances = []
        self.app = None
        print(f"[InstanceManager] Initialized with MEmu at: {self.MEMUC_PATH}")

    def load_real_instances(self):
        """Load instances from MEmu"""
        try:
            print("[InstanceManager] Loading MEmu instances...")
            start_time = time.time()
            
            result = subprocess.run([self.MEMUC_PATH, "listvms"], capture_output=True, text=True, timeout=30)
            
            print(f"[InstanceManager] memuc listvms completed in {time.time() - start_time:.2f}s")
            
            if result.returncode != 0:
                print(f"[InstanceManager] Error: {result.stderr}")
                return

            self.instances = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    instance = self._parse_instance_line(line)
                    if instance:
                        self.instances.append(instance)
            
            print(f"[InstanceManager] Loaded {len(self.instances)} instances")
            
        except Exception as e:
            print(f"[InstanceManager] Error loading instances: {e}")

    def _parse_instance_line(self, line):
        """Parse single instance line from MEmu output"""
        try:
            parts = line.split(',')
            if len(parts) >= 3:
                index = int(parts[0])
                name = parts[1]
                status = self._determine_status(parts[2:])
                
                instance = {"index": index, "name": name, "status": status}
                print(f"[InstanceManager] Parsed {name} (index {index}) - Status: {status}")
                return instance
        except Exception as e:
            print(f"[InstanceManager] Error parsing line '{line}': {e}")
        return None

    def _determine_status(self, status_parts):
        """Determine instance status from MEmu output"""
        try:
            if not status_parts:
                return "Stopped"
            
            # Handle different MEmu output formats
            first_val = status_parts[0]
            
            if first_val.isdigit():
                val = int(first_val)
                # Large number likely means memory allocation (running)
                if val > 1000000:
                    return "Running"
                elif val == 1:
                    return "Running"
                elif val == 2:
                    return "Starting"
                elif val == 3:
                    return "Stopping"
                else:
                    return "Running" if val > 0 else "Stopped"
            
            return "Stopped"
            
        except Exception:
            return "Unknown"

    def create_instance_with_name(self, name):
        """Create instance with optimized process"""
        try:
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', name)[:50]
            print(f"[InstanceManager] ⚡ Creating instance...")
            
            # Create instance
            result = subprocess.run([self.MEMUC_PATH, "create"], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"[InstanceManager] ❌ Failed to create instance")
                return False
            
            # Extract index
            new_index = self._extract_new_index(result.stdout)
            if not new_index:
                return False
            
            print(f"[InstanceManager] ✅ Created instance at index {new_index}")
            
            # Quick optimization and refresh
            self._quick_optimize_and_refresh(new_index, sanitized_name)
            return True
            
        except Exception as e:
            print(f"[InstanceManager] ❌ Creation error: {e}")
            return False

    def _extract_new_index(self, output):
        """Extract new instance index from output"""
        for line in output.split('\n'):
            if 'index:' in line.lower():
                try:
                    return int(line.split('index:')[1].strip())
                except:
                    continue
        return None

    def _quick_optimize_and_refresh(self, index, name):
        """Quick optimization and refresh"""
        def optimize_worker():
            try:
                # Basic optimization
                settings = [("-memory", "2048"), ("-cpu", "2"), ("-resolution", "480x800")]
                for param, value in settings:
                    subprocess.run([self.MEMUC_PATH, "configure", "-i", str(index), param, value],
                                 capture_output=True, timeout=10)
                    time.sleep(0.3)
                
                # Background rename
                if name and name != f"MEmu{index}":
                    subprocess.run([self.MEMUC_PATH, "rename", "-i", str(index), name],
                                 capture_output=True, timeout=10)
                
                # Refresh instances
                time.sleep(1)
                self.load_real_instances()
                if self.app:
                    self.app.after(0, self.app.force_refresh_instances)
                    
            except Exception as e:
                print(f"[InstanceManager] Optimization error: {e}")
        
        threading.Thread(target=optimize_worker, daemon=True).start()

    # Core operations
    def start_instance(self, name):
        """Start instance by name"""
        return self._instance_operation(name, "start", "Starting")

    def stop_instance(self, name):
        """Stop instance by name"""
        return self._instance_operation(name, "stop", "Stopping")

    def delete_instance(self, name):
        """Delete instance by name"""
        success = self._instance_operation(name, "remove", "Deleting")
        if success:
            self.load_real_instances()
        return success

    def clone_instance(self, name):
        """Clone instance by name"""
        return self._instance_operation(name, "clone", "Cloning", timeout=180)

    def _instance_operation(self, name, operation, action, timeout=60):
        """Generic instance operation"""
        try:
            print(f"[InstanceManager] {action} instance: {name}")
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Instance {name} not found")
                return False
            
            cmd = [self.MEMUC_PATH, operation, "-i", str(instance["index"])]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            success = result.returncode == 0
            status = "successfully" if success else "failed"
            print(f"[InstanceManager] {action} {status}: {name}")
            
            if result.stderr and not success:
                print(f"[InstanceManager] Error: {result.stderr}")
            
            return success
            
        except Exception as e:
            print(f"[InstanceManager] Error {action.lower()} {name}: {e}")
            return False

    # Utility methods
    def get_instance_by_name(self, name):
        """Get instance by name"""
        for instance in self.instances:
            if instance["name"] == name:
                return instance
        return None

    def get_instance_status(self, name):
        """Get instance status"""
        instance = self.get_instance_by_name(name)
        return instance["status"] if instance else "Unknown"

    def get_instance(self, name):
        """Get instance dict by name"""
        return self.get_instance_by_name(name)

    def get_instances(self):
        """Get all instances"""
        return self.instances

    def refresh_instances(self):
        """Refresh instance list"""
        self.load_real_instances()

    def update_instance_statuses(self):
        """Update instance statuses"""
        try:
            self.load_real_instances()
        except Exception as e:
            print(f"[InstanceManager] Status update error: {e}")

    def optimize_instance_settings(self, name, verify=False):
        """Optimize instance settings"""
        try:
            instance = self.get_instance_by_name(name)
            if not instance:
                return False
            
            index = instance["index"]
            settings = [("-memory", "2048"), ("-cpu", "2"), ("-resolution", "480x800"), ("-dpi", "240")]
            
            success_count = 0
            for param, value in settings:
                try:
                    result = subprocess.run([self.MEMUC_PATH, "configure", "-i", str(index), param, value],
                                          capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        success_count += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[InstanceManager] Setting {param} failed: {e}")
            
            success = success_count >= len(settings) * 0.75
            status = "completed" if success else "partially failed"
            print(f"[InstanceManager] Optimization {status} for {name}")
            return success
            
        except Exception as e:
            print(f"[InstanceManager] Optimization error for {name}: {e}")
            return False