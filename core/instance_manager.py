"""
BENSON v2.0 - Instance Manager (COMPLETE WITH ALL FEATURES)
Includes timeout safeguards, improved subprocess handling, and create/delete functionality
"""

import subprocess
import json
import time
import os


class InstanceManager:
    def __init__(self):
        # MEmu paths - try to detect automatically
        self.MEMUC_PATH = self._find_memuc_path()

        # Instance storage
        self.instances = []
        self.last_refresh = 0

        # Load optimization defaults from settings
        self.optimization_defaults = self._load_optimization_defaults()

        # Load instances on initialization
        self.load_real_instances()

    def _find_memuc_path(self) -> str:
        """Automatically find MEmu installation path"""
        possible_paths = [
            r"C:\Program Files\Microvirt\MEmu\memuc.exe",
            r"C:\Program Files (x86)\Microvirt\MEmu\memuc.exe",
            r"D:\Program Files\Microvirt\MEmu\memuc.exe",
            r"D:\Program Files (x86)\Microvirt\MEmu\memuc.exe",
            r"E:\Program Files\Microvirt\MEmu\memuc.exe",
            r"E:\Program Files (x86)\Microvirt\MEmu\memuc.exe"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"[InstanceManager] Found MEmu at: {path}")
                return path

        default_path = r"C:\Program Files\Microvirt\MEmu\memuc.exe"
        print(f"[InstanceManager] MEmu not found, using default: {default_path}")
        return default_path

    def _load_optimization_defaults(self):
        """Load optimization defaults from settings"""
        default_settings = {
            "default_ram_mb": 2048,
            "default_cpu_cores": 2,
            "performance_mode": "balanced"
        }

        try:
            settings_file = "benson_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get("optimization", default_settings)
        except Exception as e:
            print(f"[InstanceManager] Error loading optimization defaults: {e}")

        return default_settings

    def load_real_instances(self):
        """Load real MEmu instances with accurate status detection and timeout safeguards"""
        try:
            print("[InstanceManager] Loading MEmu instances...")

            start = time.time()
            result = subprocess.run([self.MEMUC_PATH, "listvms"],
                                    capture_output=True, text=True, timeout=8)
            elapsed = time.time() - start
            print(f"[InstanceManager] memuc listvms completed in {elapsed:.2f}s")

            if result.returncode != 0:
                print(f"[InstanceManager] MEmu command failed: {result.stderr}")
                self.instances = []
                return

            self.instances = []
            lines = result.stdout.strip().split('\n')

            print(f"[InstanceManager] Raw MEmu output:")
            for line in lines:
                print(f"  {line}")

            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 3:
                        index = int(parts[0])
                        name = parts[1].strip()
                        memu_status = parts[2].strip()
                        print(f"[InstanceManager] Checking {name} (index {index}) - MEmu says: {memu_status}")
                        self.instances.append({
                            "index": index,
                            "name": name,
                            "status": "Stopped" if memu_status == "0" else "Running"
                        })

        except subprocess.TimeoutExpired:
            print("[InstanceManager] ERROR: memuc listvms timed out")
            self.instances = []
        except Exception as e:
            print(f"[InstanceManager] Unexpected error loading instances: {e}")
            self.instances = []

    def update_instance_statuses(self):
        """Refresh the statuses of all current instances based on MEmu output"""
        try:
            print("[InstanceManager] Refreshing instance statuses...")

            result = subprocess.run([self.MEMUC_PATH, "listvms"],
                                    capture_output=True, text=True, timeout=8)

            if result.returncode != 0:
                print(f"[InstanceManager] Status refresh failed: {result.stderr}")
                return

            lines = result.stdout.strip().split('\n')
            status_map = {}

            for line in lines:
                parts = line.split(',')
                if len(parts) >= 3:
                    index = int(parts[0])
                    name = parts[1].strip()
                    memu_status = parts[2].strip()
                    status_map[name] = "Stopped" if memu_status == "0" else "Running"

            for instance in self.instances:
                name = instance.get("name")
                if name in status_map:
                    old_status = instance["status"]
                    instance["status"] = status_map[name]
                    if old_status != instance["status"]:
                        print(f"[InstanceManager] Updated {name}: {old_status} → {instance['status']}")

        except subprocess.TimeoutExpired:
            print("[InstanceManager] ERROR: memuc status update timed out")
        except Exception as e:
            print(f"[InstanceManager] Unexpected error in update_instance_statuses: {e}")

    def _get_real_instance_status(self, index, name):
        """Get real-time status of a specific instance"""
        try:
            result = subprocess.run([self.MEMUC_PATH, "listvms"],
                                    capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return "Unknown"
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 3:
                    inst_index = int(parts[0])
                    inst_name = parts[1].strip()
                    memu_status = parts[2].strip()
                    
                    if inst_index == index or inst_name == name:
                        return "Stopped" if memu_status == "0" else "Running"
            
            return "Unknown"
            
        except Exception as e:
            print(f"[InstanceManager] Error getting real status for {name}: {e}")
            return "Unknown"

    def refresh_instances(self):
        """Reload the instance list"""
        print("[InstanceManager] Manual instance refresh requested")
        self.load_real_instances()

    def optimize_instance_with_settings(self, name):
        """Optimize an instance with current settings"""
        print(f"[InstanceManager] Optimizing instance '{name}' with settings: {self.optimization_defaults}")
        
        try:
            instance = self.get_instance(name)
            if not instance:
                print(f"[InstanceManager] Instance '{name}' not found for optimization")
                return False
            
            index = instance["index"]
            
            # Configure memory
            ram_mb = self.optimization_defaults.get("default_ram_mb", 2048)
            print(f"[InstanceManager] Setting {name} RAM to {ram_mb}MB")
            
            result = subprocess.run([
                self.MEMUC_PATH, "configure", "-i", str(index), 
                "-memory", str(ram_mb)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"[InstanceManager] Failed to set RAM for {name}: {result.stderr}")
                return False
            
            # Configure CPU cores
            cpu_cores = self.optimization_defaults.get("default_cpu_cores", 2)
            print(f"[InstanceManager] Setting {name} CPU cores to {cpu_cores}")
            
            result = subprocess.run([
                self.MEMUC_PATH, "configure", "-i", str(index), 
                "-cpu", str(cpu_cores)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"[InstanceManager] Failed to set CPU for {name}: {result.stderr}")
                return False
            
            print(f"[InstanceManager] Successfully optimized {name}")
            return True
            
        except Exception as e:
            print(f"[InstanceManager] Error optimizing {name}: {e}")
            return False

    def start_instance(self, name):
        """Start the specified MEmu instance by name using its index"""
        try:
            instance = next((i for i in self.instances if i["name"] == name), None)
            if not instance:
                print(f"[InstanceManager] Could not find instance '{name}' to start.")
                return False

            index = instance["index"]
            print(f"[InstanceManager] Starting instance '{name}' (index {index})...")
            result = subprocess.run(
                [self.MEMUC_PATH, "start", "-i", str(index)],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' started successfully.")
                # Update status immediately
                instance["status"] = "Starting"
                return True
            else:
                print(f"[InstanceManager] Failed to start '{name}': {result.stderr}")
                return False
        except Exception as e:
            print(f"[InstanceManager] ERROR starting '{name}': {e}")
            return False

    def stop_instance(self, name):
        """Stop the specified MEmu instance by name"""
        try:
            instance = next((i for i in self.instances if i["name"] == name), None)
            if not instance:
                print(f"[InstanceManager] Could not find instance '{name}' to stop.")
                return False

            index = instance["index"]
            print(f"[InstanceManager] Stopping instance '{name}' (index {index})...")
            result = subprocess.run(
                [self.MEMUC_PATH, "stop", "-i", str(index)],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' stopped successfully.")
                # Update status immediately
                instance["status"] = "Stopping"
                return True
            else:
                print(f"[InstanceManager] Failed to stop '{name}': {result.stderr}")
                return False
        except Exception as e:
            print(f"[InstanceManager] ERROR stopping '{name}': {e}")
            return False

    def create_instance_with_name(self, name):
        """FIXED: Create a new MEmu instance with the specified name"""
        try:
            print(f"[InstanceManager] Creating new instance: {name}")
            
            # Check if MEmu is available first
            if not self._is_memu_available():
                print(f"[InstanceManager] MEmu is not available")
                return False
            
            # First, create the instance with MEmu command
            print(f"[InstanceManager] Executing: {self.MEMUC_PATH} create {name}")
            
            result = subprocess.run(
                [self.MEMUC_PATH, "create", name],
                capture_output=True, text=True, timeout=60  # Increased timeout
            )
            
            print(f"[InstanceManager] Create command return code: {result.returncode}")
            print(f"[InstanceManager] Create command stdout: {result.stdout}")
            print(f"[InstanceManager] Create command stderr: {result.stderr}")
            
            if result.returncode != 0:
                print(f"[InstanceManager] Failed to create instance {name}")
                print(f"[InstanceManager] Error: {result.stderr}")
                return False
            
            print(f"[InstanceManager] Instance {name} created successfully")
            
            # Wait a moment for MEmu to register the new instance
            print(f"[InstanceManager] Waiting for MEmu to register new instance...")
            time.sleep(3)
            
            # Refresh our instance list to get the new instance
            print(f"[InstanceManager] Refreshing instance list...")
            old_count = len(self.instances)
            self.load_real_instances()
            new_count = len(self.instances)
            
            print(f"[InstanceManager] Instance count: {old_count} -> {new_count}")
            
            # Find the newly created instance to get its index
            new_instance = next((i for i in self.instances if i["name"] == name), None)
            if not new_instance:
                print(f"[InstanceManager] Warning: Could not find newly created instance {name}")
                # Still consider it successful since MEmu said it worked
                return True
            
            print(f"[InstanceManager] Found new instance: {new_instance}")
            
            # Apply optimization settings to the new instance
            try:
                print(f"[InstanceManager] Applying optimization settings...")
                self.optimize_instance_with_settings(name)
                print(f"[InstanceManager] Optimization completed")
            except Exception as e:
                print(f"[InstanceManager] Warning: Could not optimize new instance {name}: {e}")
                # Don't fail creation if optimization fails
            
            print(f"[InstanceManager] Successfully created and configured instance: {name}")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout creating instance {name}")
            return False
        except FileNotFoundError:
            print(f"[InstanceManager] MEmu executable not found at: {self.MEMUC_PATH}")
            return False
        except Exception as e:
            print(f"[InstanceManager] Error creating instance {name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def delete_instance(self, name):
        """Delete a MEmu instance by name"""
        try:
            instance = next((i for i in self.instances if i["name"] == name), None)
            if not instance:
                print(f"[InstanceManager] Could not find instance '{name}' to delete.")
                return False

            index = instance["index"]
            print(f"[InstanceManager] Deleting instance '{name}' (index {index})...")
            
            # Stop the instance first if it's running
            if instance["status"] == "Running":
                print(f"[InstanceManager] Stopping {name} before deletion...")
                self.stop_instance(name)
                time.sleep(2)  # Wait for it to stop
            
            # Delete the instance
            result = subprocess.run(
                [self.MEMUC_PATH, "remove", "-i", str(index)],
                capture_output=True, text=True, timeout=20
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' deleted successfully.")
                
                # Remove from our local list
                self.instances = [i for i in self.instances if i["name"] != name]
                
                return True
            else:
                print(f"[InstanceManager] Failed to delete '{name}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout deleting instance {name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] ERROR deleting '{name}': {e}")
            return False

    def clone_instance(self, source_name, new_name):
        """Clone an existing MEmu instance"""
        try:
            source_instance = next((i for i in self.instances if i["name"] == source_name), None)
            if not source_instance:
                print(f"[InstanceManager] Could not find source instance '{source_name}' to clone.")
                return False

            source_index = source_instance["index"]
            print(f"[InstanceManager] Cloning instance '{source_name}' (index {source_index}) to '{new_name}'...")
            
            # MEmu clone command
            result = subprocess.run(
                [self.MEMUC_PATH, "clone", "-i", str(source_index), "-n", new_name],
                capture_output=True, text=True, timeout=90  # Cloning takes longer
            )
            
            print(f"[InstanceManager] Clone command return code: {result.returncode}")
            print(f"[InstanceManager] Clone command stdout: {result.stdout}")
            print(f"[InstanceManager] Clone command stderr: {result.stderr}")

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{new_name}' cloned successfully from '{source_name}'.")
                
                # Wait for MEmu to register the cloned instance
                time.sleep(3)
                self.load_real_instances()
                
                return True
            else:
                print(f"[InstanceManager] Failed to clone '{source_name}' to '{new_name}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout cloning instance {source_name} to {new_name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] ERROR cloning '{source_name}' to '{new_name}': {e}")
            return False

    def rename_instance(self, old_name, new_name):
        """Rename a MEmu instance"""
        try:
            instance = next((i for i in self.instances if i["name"] == old_name), None)
            if not instance:
                print(f"[InstanceManager] Could not find instance '{old_name}' to rename.")
                return False

            index = instance["index"]
            print(f"[InstanceManager] Renaming instance '{old_name}' (index {index}) to '{new_name}'...")
            
            # MEmu rename command
            result = subprocess.run(
                [self.MEMUC_PATH, "rename", "-i", str(index), "-n", new_name],
                capture_output=True, text=True, timeout=30
            )
            
            print(f"[InstanceManager] Rename command return code: {result.returncode}")
            print(f"[InstanceManager] Rename command stdout: {result.stdout}")
            print(f"[InstanceManager] Rename command stderr: {result.stderr}")

            if result.returncode == 0:
                print(f"[InstanceManager] Instance renamed from '{old_name}' to '{new_name}' successfully.")
                
                # Update our local instance data
                instance["name"] = new_name
                
                return True
            else:
                print(f"[InstanceManager] Failed to rename '{old_name}' to '{new_name}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[InstanceManager] Timeout renaming instance {old_name} to {new_name}")
            return False
        except Exception as e:
            print(f"[InstanceManager] ERROR renaming '{old_name}' to '{new_name}': {e}")
            return False

    def get_instance_details(self, name):
        """Get detailed information about an instance"""
        try:
            instance = next((i for i in self.instances if i["name"] == name), None)
            if not instance:
                return None

            index = instance["index"]
            
            # Get detailed configuration
            result = subprocess.run(
                [self.MEMUC_PATH, "configure", "-i", str(index)],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                # Parse configuration output
                config_lines = result.stdout.strip().split('\n')
                details = {
                    "name": name,
                    "index": index,
                    "status": instance["status"],
                    "config": {}
                }
                
                for line in config_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        details["config"][key.strip()] = value.strip()
                
                return details
            else:
                return {
                    "name": name,
                    "index": index,
                    "status": instance["status"],
                    "config": {}
                }
                
        except Exception as e:
            print(f"[InstanceManager] Error getting details for {name}: {e}")
            return None

    def get_instance(self, name):
        """Get instance by name"""
        return next((i for i in self.instances if i["name"] == name), None)

    def get_instances(self):
        """Get all instances"""
        return self.instances

    def _is_memu_available(self):
        """Check if MEmu is available and working"""
        try:
            result = subprocess.run([self.MEMUC_PATH, "listvms"],
                                    capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def get_memu_version(self):
        """Get MEmu version information"""
        try:
            result = subprocess.run([self.MEMUC_PATH, "version"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            return "Unknown"
        except:
            return "Unknown"

    def export_instance_list(self, filename="instances_export.json"):
        """Export instance list to JSON file"""
        try:
            export_data = {
                "export_time": time.time(),
                "memu_path": self.MEMUC_PATH,
                "instances": self.instances,
                "optimization_defaults": self.optimization_defaults
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"[InstanceManager] Exported {len(self.instances)} instances to {filename}")
            return True
        except Exception as e:
            print(f"[InstanceManager] Error exporting instances: {e}")
            return False