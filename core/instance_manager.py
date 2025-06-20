"""
BENSON v2.0 - Instance Manager
Handles MEmu instance operations with proper create+rename workflow
"""

import subprocess
import re
import time
import os


class InstanceManager:
    def __init__(self):
        # MEmu installation path
        self.MEMUC_PATH = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        
        # Verify MEmu installation
        if not os.path.exists(self.MEMUC_PATH):
            raise FileNotFoundError(f"MEmu not found at {self.MEMUC_PATH}")
        
        self.instances = []
        self.app = None  # Reference to main app for callbacks
        
        print(f"[InstanceManager] Initialized with MEmu at: {self.MEMUC_PATH}")

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
                            status_code = int(parts[2])
                            
                            # Convert status code to readable status
                            status = self._get_status_from_code(status_code)
                            
                            instance = {
                                "index": index,
                                "name": name,
                                "status": status
                            }
                            self.instances.append(instance)
                            
                            print(f"[InstanceManager] Checking {name} (index {index}) - MEmu says: {status_code}")
                    except (ValueError, IndexError) as e:
                        print(f"[InstanceManager] Error parsing line '{line}': {e}")
            
            print(f"[InstanceManager] Loaded {len(self.instances)} instances")
            
        except subprocess.TimeoutExpired:
            print("[InstanceManager] Timeout loading instances")
        except Exception as e:
            print(f"[InstanceManager] Error loading instances: {e}")

    def _get_status_from_code(self, code):
        """Convert MEmu status code to readable status"""
        status_map = {
            0: "Stopped",
            1: "Running", 
            2: "Starting",
            3: "Stopping"
        }
        return status_map.get(code, f"Unknown({code})")


    def stop_instance(self, name):
        """Stop a specified MEmu instance by name"""
        try:
            instance = next((i for i in self.instances if i["name"] == name), None)
            if not instance:
                print(f"[InstanceManager] Could not find instance '{name}' to stop.")
                return False

            index = instance["index"]
            print(f"[InstanceManager] Stopping instance '{name}' (index {index})...")
            result = subprocess.run(
                [self.MEMUC_PATH, "stop", "-i", str(index)],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' stopped successfully.")
                return True
            else:
                print(f"[InstanceManager] Failed to stop '{name}': {result.stderr}")
                return False
        except Exception as e:
            print(f"[InstanceManager] ERROR stopping '{name}': {e}")
            return False

    def clone_instance(self, name):
        """Clone a specified MEmu instance by name"""
        try:
            print(f"[InstanceManager] Cloning instance '{name}'...")
            result = subprocess.run(
                [self.MEMUC_PATH, "clone", "-n", name],
                capture_output=True, text=True, timeout=15
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



    def create_instance_with_name(self, name):
        """Create a new MEmu instance and rename it to the given name"""
        try:
            print(f"[InstanceManager] Creating unnamed instance...")
            create_result = subprocess.run(
                [self.MEMUC_PATH, "create"],
                capture_output=True, text=True, timeout=20
            )

            if create_result.returncode != 0:
                print(f"[InstanceManager] Failed to create instance: {create_result.stderr}")
                return False

            output = create_result.stdout.strip()
            print(f"[InstanceManager] Create output: {output}")
            match = re.search(r"index:\s*(\d+)", output)
            if not match:
                print("[InstanceManager] Could not find instance index in output.")
                return False

            new_index = match.group(1)
            default_name = f"MEmu{new_index}"
            print(f"[InstanceManager] Renaming '{default_name}' to '{name}'...")

            rename_result = subprocess.run(
                [self.MEMUC_PATH, "rename", "-n", default_name, name],
                capture_output=True, text=True, timeout=10
            )

            if rename_result.returncode == 0:
                print(f"[InstanceManager] Successfully renamed '{default_name}' to '{name}'.")
                return True
            else:
                print(f"[InstanceManager] Failed to rename instance: {rename_result.stderr}")
                return False

        except Exception as e:
            print(f"[InstanceManager] ERROR during create/rename: {e}")
            return False

            # Extract the index from output (e.g., "Create instance success, index: 9")
            output = create_result.stdout.strip()
            print(f"[InstanceManager] Create output: {output}")
            match = re.search(r"index:\s*(\d+)", output)
            if not match:
                print("[InstanceManager] Could not find instance index in output.")
                return False

            new_index = match.group(1)
            print(f"[InstanceManager] Renaming instance index {new_index} to '{name}'...")

            rename_result = subprocess.run(
                [self.MEMUC_PATH, "rename", "-i", new_index, "-n", name],
                capture_output=True, text=True, timeout=10
            )

            if rename_result.returncode == 0:
                print(f"[InstanceManager] Successfully renamed instance to '{name}'.")
                return True
            else:
                print(f"[InstanceManager] Failed to rename instance: {rename_result.stderr}")
                return False

        except Exception as e:
            print(f"[InstanceManager] ERROR during create/rename: {e}")
            return False
        except Exception as e:
            print(f"[InstanceManager] ERROR creating '{name}': {e}")
            return False



    def get_instance(self, name):
        """Return instance dict by name"""
        for instance in self.instances:
            if instance["name"] == name:
                return instance
        return None


    def get_instances(self):
        """Get list of instances"""
        return self.instances

    def create_instance(self, name):
        """FIXED: Create instance with proper MEmu workflow - create then rename"""
        try:
            sanitized_name = self._sanitize_instance_name(name)
            print(f"[InstanceManager] Creating new instance to be named: {sanitized_name}")
            
            # Get current max index to predict new index
            current_max = max([inst["index"] for inst in self.instances], default=-1)
            expected_new_index = current_max + 1
            print(f"[InstanceManager] Current max index: {current_max}, expecting new index: {expected_new_index}")
            
            # FIXED: Step 1 - Create instance without name (MEmu auto-assigns name)
            print(f"[InstanceManager] Step 1: Creating instance...")
            result = subprocess.run(
                [self.MEMUC_PATH, "create"],  # No name parameter!
                capture_output=True, text=True, timeout=60
            )
            
            print(f"[InstanceManager] Create command return code: {result.returncode}")
            print(f"[InstanceManager] Create command stdout: {result.stdout}")
            print(f"[InstanceManager] Create command stderr: {result.stderr}")

            if result.returncode != 0:
                print(f"[InstanceManager] Failed to create instance: {result.stderr}")
                return False
                
            # FIXED: Step 2 - Extract the new index from MEmu response
            new_index = None
            for line in result.stdout.split('\n'):
                if 'index:' in line:
                    try:
                        new_index = int(line.split('index:')[1].strip())
                        print(f"[InstanceManager] MEmu assigned new index: {new_index}")
                        break
                    except (ValueError, IndexError):
                        continue
                        
            if new_index is None:
                print(f"[InstanceManager] Could not extract new index from MEmu response")
                return False
                
            # FIXED: Step 3 - Rename the instance to desired name
            print(f"[InstanceManager] Step 2: Renaming instance {new_index} to '{sanitized_name}'...")
            rename_result = subprocess.run(
                [self.MEMUC_PATH, "rename", "-i", str(new_index), sanitized_name],
                capture_output=True, text=True, timeout=30
            )
            
            print(f"[InstanceManager] Rename command return code: {rename_result.returncode}")
            print(f"[InstanceManager] Rename command stdout: {rename_result.stdout}")
            print(f"[InstanceManager] Rename command stderr: {rename_result.stderr}")
            
            if rename_result.returncode != 0:
                print(f"[InstanceManager] Warning: Rename failed, but instance was created with auto-name")
                # Continue anyway - instance exists, just with auto-name
            
            # Wait for MEmu to register the changes
            print("[InstanceManager] Waiting for MEmu to register changes...")
            time.sleep(2)
            
            # Refresh our instance list
            print("[InstanceManager] Refreshing instance list...")
            old_count = len(self.instances)
            self.load_real_instances()
            new_count = len(self.instances)
            
            print(f"[InstanceManager] Instance count: {old_count} -> {new_count}")
            
            if new_count > old_count:
                # Find the new instance by index
                new_instance = None
                for instance in self.instances:
                    if instance["index"] == new_index:
                        new_instance = instance
                        break
                
                if new_instance:
                    created_name = new_instance["name"]
                    print(f"[InstanceManager] Found new instance: {new_instance}")
                    
                    if created_name == sanitized_name:
                        print(f"[InstanceManager] ✅ Instance created and renamed successfully to '{sanitized_name}'")
                    else:
                        print(f"[InstanceManager] ⚠️ Instance created but rename failed - using auto-name '{created_name}'")
                    
                    # Apply optimization settings
                    print("[InstanceManager] Applying optimization settings...")
                    try:
                        self.optimize_instance_settings(created_name)
                        print("[InstanceManager] Optimization completed")
                    except Exception as opt_error:
                        print(f"[InstanceManager] Optimization failed: {opt_error}")
                    
                    print(f"[InstanceManager] Successfully created and configured instance '{created_name}'")
                    
                    # FIXED: Trigger UI update to show new instance
                    if hasattr(self, 'app') and self.app:
                        print("[InstanceManager] Triggering UI refresh for new instance")
                        self.app.after_idle(self.app.load_instances_after_create)
                    
                    return True
                else:
                    print(f"[InstanceManager] Could not find new instance at index {new_index}")
            else:
                print("[InstanceManager] Instance count did not increase - creation may have failed")
                
            return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout creating instance")
            return False
        except Exception as e:
            print(f"[InstanceManager] ERROR creating instance: {e}")
            return False

    def delete_instance(self, name):
        """Delete an instance by name"""
        try:
            print(f"[InstanceManager] Deleting instance: {name}")
            
            result = subprocess.run(
                [self.MEMUC_PATH, "remove", "-n", name],
                capture_output=True, text=True, timeout=30
            )
            
            print(f"[InstanceManager] Delete result: {result.returncode}")
            print(f"[InstanceManager] Delete stdout: {result.stdout}")
            print(f"[InstanceManager] Delete stderr: {result.stderr}")
            
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully deleted {name}")
                # Refresh instance list
                self.load_real_instances()
                return True
            else:
                print(f"[InstanceManager] Failed to delete {name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout deleting {name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] Error deleting {name}: {e}")
            return False

    def start_instance(self, name):
        """Start an instance"""
        try:
            print(f"[InstanceManager] Starting instance: {name}")
            
            result = subprocess.run(
                [self.MEMUC_PATH, "start", "-n", name],
                capture_output=True, text=True, timeout=60
            )
            
            print(f"[InstanceManager] Start result: {result.returncode}")
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully started {name}")
                return True
            else:
                print(f"[InstanceManager] Failed to start {name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout starting {name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] Error starting {name}: {e}")
            return False

    def stop_instance(self, name):
        """Stop an instance"""
        try:
            print(f"[InstanceManager] Stopping instance: {name}")
            
            result = subprocess.run(
                [self.MEMUC_PATH, "stop", "-n", name],
                capture_output=True, text=True, timeout=30
            )
            
            print(f"[InstanceManager] Stop result: {result.returncode}")
            if result.returncode == 0:
                print(f"[InstanceManager] Successfully stopped {name}")
                return True
            else:
                print(f"[InstanceManager] Failed to stop {name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout stopping {name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] Error stopping {name}: {e}")
            return False

    def optimize_instance_settings(self, name):
        """Apply optimization settings to instance"""
        try:
            settings = {
                'default_ram_mb': 2048,
                'default_cpu_cores': 2,
                'performance_mode': 'balanced'
            }
            
            print(f"[InstanceManager] Optimizing instance '{name}' with settings: {settings}")
            
            # Set RAM
            print(f"[InstanceManager] Setting {name} RAM to {settings['default_ram_mb']}MB")
            ram_result = subprocess.run(
                [self.MEMUC_PATH, "configure", "-n", name, "-memory", str(settings['default_ram_mb'])],
                capture_output=True, text=True, timeout=30
            )
            
            # Set CPU cores
            print(f"[InstanceManager] Setting {name} CPU cores to {settings['default_cpu_cores']}")
            cpu_result = subprocess.run(
                [self.MEMUC_PATH, "configure", "-n", name, "-cpu", str(settings['default_cpu_cores'])],
                capture_output=True, text=True, timeout=30
            )
            
            if ram_result.returncode == 0 and cpu_result.returncode == 0:
                print(f"[InstanceManager] Successfully optimized {name}")
                return True
            else:
                print(f"[InstanceManager] Optimization partially failed for {name}")
                print(f"[InstanceManager] RAM result: {ram_result.stderr}")
                print(f"[InstanceManager] CPU result: {cpu_result.stderr}")
                return False
                
        except Exception as e:
            print(f"[InstanceManager] Error optimizing {name}: {e}")
            return False

    def optimize_instance_with_settings(self, name):
        """Optimize instance with predefined settings"""
        return self.optimize_instance_settings(name)

    def update_instance_statuses(self):
        """Update instance statuses by reloading from MEmu"""
        try:
            print("[InstanceManager] Updating instance statuses...")
            self.load_real_instances()
            print("[InstanceManager] Status update complete")
        except Exception as e:
            print(f"[InstanceManager] Error updating statuses: {e}")

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