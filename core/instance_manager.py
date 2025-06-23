"""
BENSON v2.0 - FIXED Instance Manager with Shared State Support
Now properly manages shared state between modules
"""

import subprocess
import re
import time
import os
import threading


class InstanceManager:
    def __init__(self):
        # MEmu installation path
        self.MEMUC_PATH = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        
        # Verify MEmu installation
        if not os.path.exists(self.MEMUC_PATH):
            raise FileNotFoundError(f"MEmu not found at {self.MEMUC_PATH}")
        
        self.instances = []
        self.app = None  # Reference to main app for callbacks
        
        # NEW: Shared state for modules
        self.shared_state = {
            "game_accessible": {},      # instance_name -> bool
            "module_states": {},        # instance_name -> {module: state}
            "last_updates": {},         # instance_name -> timestamp
            "autostart_completed": {},  # instance_name -> bool
            "game_world_active": {}     # instance_name -> bool
        }
        
        print(f"[InstanceManager] Initialized with MEmu at: {self.MEMUC_PATH}")
        print(f"[InstanceManager] Shared state system ready")

    def set_game_accessible(self, instance_name: str, accessible: bool):
        """NEW: Set game accessibility state for an instance"""
        try:
            self.shared_state["game_accessible"][instance_name] = accessible
            self.shared_state["last_updates"][instance_name] = time.time()
            
            if accessible:
                print(f"[InstanceManager] ✅ Game marked as accessible for {instance_name}")
            else:
                print(f"[InstanceManager] ❌ Game marked as inaccessible for {instance_name}")
                
        except Exception as e:
            print(f"[InstanceManager] Error setting game accessibility: {e}")
    
    def is_game_accessible(self, instance_name: str) -> bool:
        """NEW: Check if game is accessible for an instance"""
        return self.shared_state["game_accessible"].get(instance_name, False)
    
    def set_autostart_completed(self, instance_name: str, completed: bool):
        """NEW: Set AutoStart completion state"""
        try:
            self.shared_state["autostart_completed"][instance_name] = completed
            self.shared_state["last_updates"][instance_name] = time.time()
            
            if completed:
                print(f"[InstanceManager] ✅ AutoStart marked as completed for {instance_name}")
            else:
                print(f"[InstanceManager] 🔄 AutoStart completion reset for {instance_name}")
                
        except Exception as e:
            print(f"[InstanceManager] Error setting AutoStart completion: {e}")
    
    def is_autostart_completed(self, instance_name: str) -> bool:
        """NEW: Check if AutoStart is completed for an instance"""
        return self.shared_state["autostart_completed"].get(instance_name, False)
    
    def set_module_state(self, instance_name: str, module_name: str, state: dict):
        """NEW: Set module state information"""
        try:
            if instance_name not in self.shared_state["module_states"]:
                self.shared_state["module_states"][instance_name] = {}
            
            self.shared_state["module_states"][instance_name][module_name] = state
            self.shared_state["last_updates"][instance_name] = time.time()
            
        except Exception as e:
            print(f"[InstanceManager] Error setting module state: {e}")
    
    def get_module_state(self, instance_name: str, module_name: str) -> dict:
        """NEW: Get module state information"""
        try:
            return self.shared_state["module_states"].get(instance_name, {}).get(module_name, {})
        except Exception as e:
            print(f"[InstanceManager] Error getting module state: {e}")
            return {}
    
    def clear_instance_state(self, instance_name: str):
        """NEW: Clear all shared state for an instance when it stops"""
        try:
            keys_to_clear = ["game_accessible", "module_states", "autostart_completed", "game_world_active"]
            
            for key in keys_to_clear:
                if instance_name in self.shared_state[key]:
                    del self.shared_state[key][instance_name]
            
            if instance_name in self.shared_state["last_updates"]:
                del self.shared_state["last_updates"][instance_name]
                
            print(f"[InstanceManager] 🧹 Cleared shared state for {instance_name}")
            
        except Exception as e:
            print(f"[InstanceManager] Error clearing instance state: {e}")
    
    def get_shared_state_summary(self) -> dict:
        """NEW: Get summary of shared state for debugging"""
        try:
            summary = {
                "total_instances_tracked": len(set().union(*[
                    self.shared_state[key].keys() for key in self.shared_state.keys()
                ])),
                "game_accessible_count": len([v for v in self.shared_state["game_accessible"].values() if v]),
                "autostart_completed_count": len([v for v in self.shared_state["autostart_completed"].values() if v]),
                "instances_with_state": {}
            }
            
            # Get per-instance summary
            all_instances = set()
            for state_dict in self.shared_state.values():
                all_instances.update(state_dict.keys())
            
            for instance_name in all_instances:
                summary["instances_with_state"][instance_name] = {
                    "game_accessible": self.shared_state["game_accessible"].get(instance_name, False),
                    "autostart_completed": self.shared_state["autostart_completed"].get(instance_name, False),
                    "game_world_active": self.shared_state["game_world_active"].get(instance_name, False),
                    "last_update": self.shared_state["last_updates"].get(instance_name, 0)
                }
            
            return summary
            
        except Exception as e:
            print(f"[InstanceManager] Error getting shared state summary: {e}")
            return {"error": str(e)}

    def _sanitize_instance_name(self, name):
        """Sanitize instance name for MEmu compatibility"""
        # Remove special characters, keep alphanumeric and basic chars
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        return sanitized[:50]  # Limit length

    def load_real_instances(self):
        """Load instances from MEmu with timing"""
        try:
            print("[InstanceManager] Loading MEmu instances...")
            start_time = time.time()
            
            result = subprocess.run(
                [self.MEMUC_PATH, "listvms"],
                capture_output=True, text=True, timeout=30
            )
            
            elapsed = time.time() - start_time
            print(f"[InstanceManager] memuc listvms completed in {elapsed:.2f}s")
            
            if result.returncode != 0:
                print(f"[InstanceManager] Error loading instances: {result.stderr}")
                return
            
            # Parse MEmu output
            lines = result.stdout.strip().split('\n')
            print(f"[InstanceManager] Raw MEmu output:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            
            self.instances = []
            for line in lines:
                if line.strip():
                    try:
                        parts = line.split(',')
                        if len(parts) >= 3:
                            index = int(parts[0])
                            name = parts[1]
                            status_info = parts[2] if len(parts) > 2 else "0"
                            
                            # FIXED: Better status detection based on MEmu output format
                            status = self._parse_memu_status(parts)
                            
                            instance = {
                                "index": index,
                                "name": name,
                                "status": status
                            }
                            self.instances.append(instance)
                            
                            print(f"[InstanceManager] Parsed {name} (index {index}) - Status: {status}")
                    except (ValueError, IndexError) as e:
                        print(f"[InstanceManager] Error parsing line '{line}': {e}")
            
            print(f"[InstanceManager] Loaded {len(self.instances)} instances")
            
        except subprocess.TimeoutExpired:
            print("[InstanceManager] Timeout loading instances")
        except Exception as e:
            print(f"[InstanceManager] Error loading instances: {e}")

    def _parse_memu_status(self, parts):
        """FIXED: Parse MEmu status from listvms output with better detection"""
        try:
            # MEmu listvms format: index,name,memory,status,cpu
            # Where memory > 0 usually indicates running instance
            
            if len(parts) >= 5:
                # New format: index,name,memory,status,cpu
                memory = int(parts[2]) if parts[2].isdigit() else 0
                status_code = int(parts[3]) if parts[3].isdigit() else 0
                cpu = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                
                # FIXED: If instance has memory allocated, it's likely running
                if memory > 0 and status_code == 1:
                    return "Running"
                elif memory > 0 and status_code == 0:
                    return "Starting"  # Has memory but not fully running yet
                elif status_code == 1:
                    return "Running"
                elif status_code == 2:
                    return "Starting"
                elif status_code == 3:
                    return "Stopping"
                else:
                    return "Stopped"
                    
            elif len(parts) >= 3:
                # Old format: index,name,status
                status_code_or_memory = parts[2]
                
                if status_code_or_memory.isdigit():
                    value = int(status_code_or_memory)
                    
                    # FIXED: If it's a large number, it's probably memory (running)
                    if value > 1000000:  # Large number = memory allocation = running
                        return "Running"
                    elif value == 0:
                        return "Stopped"
                    elif value == 1:
                        return "Running"
                    elif value == 2:
                        return "Starting"
                    elif value == 3:
                        return "Stopping"
                    else:
                        # Unknown status code but instance might be running
                        return "Running" if value > 0 else "Stopped"
                else:
                    return "Stopped"
                    
        except (ValueError, IndexError) as e:
            print(f"[InstanceManager] Error parsing status: {e}")
            return "Unknown"
        
        return "Stopped"

    def create_instance_with_name(self, name):
        """FAST: Create instance without hanging rename"""
        try:
            sanitized_name = self._sanitize_instance_name(name)
            print(f"[InstanceManager] ⚡ FAST CREATE: Creating instance...")
            
            # Step 1: Create instance (returns index)
            print("[InstanceManager] Step 1: Creating instance...")
            create_result = subprocess.run(
                [self.MEMUC_PATH, "create"],
                capture_output=True, text=True, timeout=120
            )
            
            print(f"[InstanceManager] Create return code: {create_result.returncode}")
            print(f"[InstanceManager] Create stdout: {create_result.stdout}")
            if create_result.stderr:
                print(f"[InstanceManager] Create stderr: {create_result.stderr}")

            if create_result.returncode != 0:
                print(f"[InstanceManager] ❌ Failed to create instance")
                return False
            
            # Step 2: Extract index
            new_index = None
            for line in create_result.stdout.split('\n'):
                if 'index:' in line.lower():
                    try:
                        index_part = line.split('index:')[1].strip()
                        new_index = int(index_part)
                        print(f"[InstanceManager] ✅ Found new index: {new_index}")
                        break
                    except (ValueError, IndexError):
                        continue
            
            if new_index is None:
                print(f"[InstanceManager] ❌ Could not extract index")
                return False
            
            # Step 3: SKIP RENAME - Get instance immediately
            print(f"[InstanceManager] Step 2: ⚡ SKIPPING RENAME for speed")
            print(f"[InstanceManager] Will appear as 'MEmu{new_index}' initially")
            
            # Step 4: Immediate refresh
            print("[InstanceManager] Step 3: Immediate refresh...")
            self.load_real_instances()
            
            # Step 5: Find new instance
            new_instance = None
            for instance in self.instances:
                if instance["index"] == new_index:
                    new_instance = instance
                    break
            
            if new_instance:
                actual_name = new_instance["name"]
                print(f"[InstanceManager] ✅ SUCCESS: Created '{actual_name}' at index {new_index}")
                
                # Step 6: Quick optimization
                try:
                    self.optimize_instance_settings(actual_name)
                    print("[InstanceManager] ✅ Optimization done")
                except Exception as e:
                    print(f"[InstanceManager] ⚠️ Optimization failed: {e}")
                
                # Step 7: Try background rename (non-blocking)
                if sanitized_name != actual_name:
                    print(f"[InstanceManager] 🔄 Starting background rename to '{sanitized_name}'...")
                    self._background_rename(new_index, sanitized_name)
                
                # Step 8: Initialize shared state for new instance
                self.shared_state["game_accessible"][actual_name] = False
                self.shared_state["autostart_completed"][actual_name] = False
                self.shared_state["game_world_active"][actual_name] = False
                self.shared_state["last_updates"][actual_name] = time.time()
                
                # Step 9: Immediate UI refresh
                if hasattr(self, 'app') and self.app:
                    print("[InstanceManager] 🔄 Triggering UI refresh...")
                    self.app.after(0, self.app.force_refresh_instances)
                
                return True
            else:
                print(f"[InstanceManager] ❌ Could not find new instance")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] ❌ ERROR: {e}")
            return False

    def _background_rename(self, index, new_name):
        """Background rename that doesn't block"""
        def rename_worker():
            try:
                print(f"[InstanceManager] 🔄 Background rename to '{new_name}'...")
                result = subprocess.run(
                    [self.MEMUC_PATH, "rename", "-i", str(index), new_name],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    print(f"[InstanceManager] ✅ Background rename successful!")
                    # Refresh UI
                    if hasattr(self, 'app') and self.app:
                        time.sleep(1)  # Small delay
                        self.app.after(0, self.app.force_refresh_instances)
                else:
                    print(f"[InstanceManager] ⚠️ Background rename failed")
                    
            except Exception as e:
                print(f"[InstanceManager] ⚠️ Background rename error: {e}")
        
        threading.Thread(target=rename_worker, daemon=True).start()

    def delete_instance(self, name):
        """Delete an instance using index-based command"""
        try:
            print(f"[InstanceManager] Deleting instance: {name}")
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Instance {name} not found")
                return False
            
            # Clear shared state for this instance
            self.clear_instance_state(name)
            
            result = subprocess.run(
                [self.MEMUC_PATH, "remove", "-i", str(instance["index"])],
                capture_output=True, text=True, timeout=60
            )
            
            print(f"[InstanceManager] Delete result: {result.returncode}")
            if result.stdout:
                print(f"[InstanceManager] Delete stdout: {result.stdout}")
            if result.stderr:
                print(f"[InstanceManager] Delete stderr: {result.stderr}")
            
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully deleted {name}")
                self.load_real_instances()
                return True
            else:
                print(f"[InstanceManager] Failed to delete {name}")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] Error deleting {name}: {e}")
            return False

    def start_instance(self, name):
        """Start an instance using index-based command"""
        try:
            print(f"[InstanceManager] Starting instance: {name}")
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Instance {name} not found")
                return False
            
            result = subprocess.run(
                [self.MEMUC_PATH, "start", "-i", str(instance["index"])],
                capture_output=True, text=True, timeout=90
            )
            
            print(f"[InstanceManager] Start result: {result.returncode}")
            if result.stderr:
                print(f"[InstanceManager] Start stderr: {result.stderr}")
                
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully started {name}")
                
                # Initialize shared state for started instance
                self.shared_state["game_accessible"][name] = False
                self.shared_state["autostart_completed"][name] = False
                self.shared_state["game_world_active"][name] = False
                self.shared_state["last_updates"][name] = time.time()
                
                return True
            else:
                print(f"[InstanceManager] Failed to start {name}")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] Error starting {name}: {e}")
            return False

    def stop_instance(self, name):
        """Stop an instance using index-based command"""
        try:
            print(f"[InstanceManager] Stopping instance: {name}")
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Instance {name} not found")
                return False
            
            # Clear shared state when stopping
            self.clear_instance_state(name)
            
            result = subprocess.run(
                [self.MEMUC_PATH, "stop", "-i", str(instance["index"])],
                capture_output=True, text=True, timeout=60
            )
            
            print(f"[InstanceManager] Stop result: {result.returncode}")
            if result.stderr:
                print(f"[InstanceManager] Stop stderr: {result.stderr}")
                
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully stopped {name}")
                return True
            else:
                print(f"[InstanceManager] Failed to stop {name}")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] Error stopping {name}: {e}")
            return False

    def clone_instance(self, name):
        """Clone instance using index-based command"""
        try:
            print(f"[InstanceManager] Cloning instance '{name}'...")
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Instance {name} not found")
                return False
            
            result = subprocess.run(
                [self.MEMUC_PATH, "clone", "-i", str(instance["index"])],
                capture_output=True, text=True, timeout=180
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' cloned successfully.")
                return True
            else:
                print(f"[InstanceManager] Failed to clone '{name}': {result.stderr}")
                return False
        except Exception as e:
            print(f"[InstanceManager] ERROR cloning '{name}': {e}")
            return False

    def optimize_instance_settings(self, name):
        """Apply optimization settings using index-based commands"""
        try:
            settings = {
                'default_ram_mb': 2048,
                'default_cpu_cores': 2
            }
            
            instance = self.get_instance_by_name(name)
            if not instance:
                print(f"[InstanceManager] Cannot optimize - instance {name} not found")
                return False
            
            index = instance["index"]
            
            # Set RAM
            ram_result = subprocess.run(
                [self.MEMUC_PATH, "configure", "-i", str(index), "-memory", str(settings['default_ram_mb'])],
                capture_output=True, text=True, timeout=30
            )
            
            # Set CPU
            cpu_result = subprocess.run(
                [self.MEMUC_PATH, "configure", "-i", str(index), "-cpu", str(settings['default_cpu_cores'])],
                capture_output=True, text=True, timeout=30
            )
            
            if ram_result.returncode == 0 and cpu_result.returncode == 0:
                print(f"[InstanceManager] Successfully optimized {name}")
                return True
            else:
                print(f"[InstanceManager] Optimization partially failed for {name}")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] Error optimizing {name}: {e}")
            return False

    # Helper methods
    def get_instance_by_name(self, name):
        """Get instance by name"""
        for instance in self.instances:
            if instance["name"] == name:
                return instance
        return None

    def get_instance_status(self, name):
        """Get status of specific instance"""
        instance = self.get_instance_by_name(name)
        return instance["status"] if instance else "Unknown"

    def get_instance(self, name):
        """Return instance dict by name"""
        return self.get_instance_by_name(name)

    def get_instances(self):
        """Get list of instances"""
        return self.instances

    def refresh_instances(self):
        """Refresh instances from MEmu"""
        self.load_real_instances()

    def update_instance_statuses(self):
        """Update instance statuses by reloading from MEmu"""
        try:
            print("[InstanceManager] Updating instance statuses...")
            self.load_real_instances()
            print("[InstanceManager] Status update complete")
        except Exception as e:
            print(f"[InstanceManager] Error updating statuses: {e}")

    def _is_memu_available(self):
        """Check if MEmu is available and working"""
        try:
            result = subprocess.run(
                [self.MEMUC_PATH, "version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False