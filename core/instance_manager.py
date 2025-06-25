"""
BENSON v2.0 - Silent Instance Manager
Checks every second but only logs actual changes
"""

import subprocess
import re
import time
import os
import threading


class InstanceManager:
    """Instance manager with silent frequent monitoring"""

    def __init__(self):
        self.MEMUC_PATH = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        
        if not os.path.exists(self.MEMUC_PATH):
            raise FileNotFoundError(f"MEmu not found at {self.MEMUC_PATH}")
        
        self.instances = []
        self.app = None
        self.last_instance_states = {}  # Track previous states to detect changes
        self.shared_state = {}  # Add shared state for module communication
        self.silent_mode = True  # Enable silent monitoring
        self.last_error_log_time = 0  # Prevent error spam
        
        print(f"[InstanceManager] Initialized with MEmu at: {self.MEMUC_PATH}")

    def load_real_instances(self, force_refresh=False, log_result=True):
        """Load instances from MEmu with configurable logging"""
        try:
            start_time = time.time()
            
            result = subprocess.run([self.MEMUC_PATH, "listvms"], capture_output=True, text=True, timeout=30)
            
            elapsed_time = time.time() - start_time
            
            if result.returncode != 0:
                # Only log errors occasionally to avoid spam
                current_time = time.time()
                if (current_time - self.last_error_log_time) > 60:  # Every minute max
                    print(f"[InstanceManager] Error: {result.stderr}")
                    self.last_error_log_time = current_time
                return

            # Parse instances and detect changes
            new_instances = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    instance = self._parse_instance_line(line)
                    if instance:
                        new_instances.append(instance)
            
            # Detect and log only actual changes
            changes_detected = self._detect_and_log_changes(new_instances, log_result)
            
            # Update instances list
            self.instances = new_instances
            
            # Log performance only if slow or forced
            if force_refresh and log_result:
                print(f"[InstanceManager] memuc listvms completed in {elapsed_time:.2f}s")
            elif elapsed_time > 3.0:  # Only log if unusually slow
                print(f"[InstanceManager] ⚠️ Slow response: {elapsed_time:.2f}s")
            
        except Exception as e:
            # Prevent error spam - only log occasionally
            current_time = time.time()
            if (current_time - self.last_error_log_time) > 300:  # Every 5 minutes max
                print(f"[InstanceManager] Error loading instances: {e}")
                self.last_error_log_time = current_time

    def _detect_and_log_changes(self, new_instances, log_result=True):
        """Detect changes and log only significant events"""
        if not log_result:
            # Update tracking without logging
            self._update_state_tracking(new_instances)
            return False
        
        changes_detected = False
        
        # Create current state map
        current_states = {inst["name"]: inst["status"] for inst in new_instances}
        current_names = set(current_states.keys())
        previous_names = set(self.last_instance_states.keys())
        
        # Check for new instances
        new_names = current_names - previous_names
        if new_names:
            for name in new_names:
                print(f"[InstanceManager] ➕ New instance detected: {name}")
                changes_detected = True
        
        # Check for removed instances
        removed_names = previous_names - current_names
        if removed_names:
            for name in removed_names:
                print(f"[InstanceManager] ➖ Instance removed: {name}")
                changes_detected = True
        
        # Check for status changes
        for name in current_names.intersection(previous_names):
            old_status = self.last_instance_states.get(name)
            new_status = current_states.get(name)
            
            if old_status != new_status:
                print(f"[InstanceManager] 🔄 {name}: {old_status} → {new_status}")
                changes_detected = True
        
        # Update tracking
        self.last_instance_states = current_states.copy()
        
        # Log summary only if this is the first load
        if not hasattr(self, '_initial_load_complete'):
            print(f"[InstanceManager] Loaded {len(new_instances)} instances")
            self._initial_load_complete = True
            changes_detected = True
        
        return changes_detected

    def _update_state_tracking(self, new_instances):
        """Update state tracking without logging"""
        current_states = {inst["name"]: inst["status"] for inst in new_instances}
        self.last_instance_states = current_states.copy()

    def _parse_instance_line(self, line):
        """Parse single instance line from MEmu output"""
        try:
            parts = line.split(',')
            if len(parts) >= 3:
                index = int(parts[0])
                name = parts[1]
                status = self._determine_status(parts[2:])
                
                instance = {"index": index, "name": name, "status": status}
                return instance
        except Exception as e:
            # Only log parsing errors occasionally to avoid spam
            current_time = time.time()
            if not hasattr(self, '_last_parse_error_time'):
                self._last_parse_error_time = 0
            
            if (current_time - self._last_parse_error_time) > 300:  # Every 5 minutes
                print(f"[InstanceManager] Error parsing line: {e}")
                self._last_parse_error_time = current_time
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
                
                # Refresh instances with logging
                time.sleep(1)
                self.load_real_instances(force_refresh=True, log_result=True)
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
            self.load_real_instances(force_refresh=True, log_result=True)
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
            
            # Force immediate refresh with logging after operations
            if success:
                time.sleep(1)  # Give MEmu time to update
                self.load_real_instances(force_refresh=True, log_result=True)
            
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
        """Refresh instance list with logging"""
        self.load_real_instances(force_refresh=True, log_result=True)

    def update_instance_statuses(self):
        """Silent status update for background monitoring"""
        try:
            # This is called frequently - no logging unless there are changes
            self.load_real_instances(force_refresh=False, log_result=False)
        except Exception as e:
            # Minimal error logging for background updates
            current_time = time.time()
            if not hasattr(self, '_silent_error_time'):
                self._silent_error_time = 0
            
            if (current_time - self._silent_error_time) > 600:  # Every 10 minutes max
                print(f"[InstanceManager] Background update error: {e}")
                self._silent_error_time = current_time

    def optimize_instance_settings(self, name, verify=False):
        """Optimize instance settings"""
        try:
            instance = self.get_instance_by_name(name)
            if not instance:
                return False
            
            index = instance["index"]
            settings = [("-memory", "2048"), ("-cpu", "2"), ("-resolution", "480x800"), ("-dpi", "240")]
            
            print(f"[InstanceManager] Optimization completed for {name}")
            
            success_count = 0
            for param, value in settings:
                try:
                    result = subprocess.run([self.MEMUC_PATH, "configure", "-i", str(index), param, value],
                                          capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        success_count += 1
                    time.sleep(0.5)
                except Exception as e:
                    # Only log critical optimization failures
                    if success_count == 0:
                        print(f"[InstanceManager] Setting {param} failed: {e}")
            
            success = success_count >= len(settings) * 0.75
            if not success:
                print(f"[InstanceManager] Optimization partially failed for {name}")
            
            return success
            
        except Exception as e:
            print(f"[InstanceManager] Optimization error for {name}: {e}")
            return False

    # Shared state methods for module communication
    def set_game_state(self, instance_name, state_dict):
        """Set game state for module communication"""
        try:
            if not hasattr(self, 'shared_state'):
                self.shared_state = {}
            
            for key, value in state_dict.items():
                state_key = f"{key}_{instance_name}"
                self.shared_state[state_key] = value
                
        except Exception as e:
            print(f"[InstanceManager] Error setting game state: {e}")

    def get_game_state(self, instance_name, key):
        """Get game state for module communication"""
        try:
            if not hasattr(self, 'shared_state'):
                return None
            
            state_key = f"{key}_{instance_name}"
            return self.shared_state.get(state_key)
            
        except Exception as e:
            print(f"[InstanceManager] Error getting game state: {e}")
            return None

    # Quick status methods without triggering refreshes
    def get_running_instances(self):
        """Get list of running instances"""
        return [inst for inst in self.instances if inst["status"] == "Running"]

    def get_stopped_instances(self):
        """Get list of stopped instances"""
        return [inst for inst in self.instances if inst["status"] == "Stopped"]

    def has_running_instances(self):
        """Quick check if any instances are running"""
        return any(inst["status"] == "Running" for inst in self.instances)

    def get_instance_count(self):
        """Get total instance count"""
        return len(self.instances)

    def get_status_summary(self):
        """Get status summary without triggering refresh"""
        running = len([i for i in self.instances if i["status"] == "Running"])
        stopped = len([i for i in self.instances if i["status"] == "Stopped"])
        total = len(self.instances)
        
        return {
            "total": total,
            "running": running,
            "stopped": stopped,
            "has_changes": bool(self.last_instance_states)
        }

    # Debug methods
    def enable_verbose_logging(self):
        """Enable verbose logging for debugging"""
        self.silent_mode = False
        print("[InstanceManager] Verbose logging enabled")

    def disable_verbose_logging(self):
        """Disable verbose logging (default)"""
        self.silent_mode = True
        print("[InstanceManager] Silent mode enabled")

    def force_status_check_with_logging(self):
        """Force a status check with full logging"""
        print("[InstanceManager] Force checking instance statuses...")
        self.load_real_instances(force_refresh=True, log_result=True)