"""
BENSON v2.0 - Instance Manager (FINAL FIXED)
Includes timeout safeguards and improved subprocess handling
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


    

    def refresh_instances(self):
        """Reload the instance list"""
        print("[InstanceManager] Manual instance refresh requested")
        self.load_real_instances()

    def optimize_instance_with_settings(self, name):
        """Placeholder to simulate optimization of an instance"""
        print(f"[InstanceManager] Optimizing instance '{name}' with settings: {self.optimization_defaults}")
        # Add real optimization logic here if needed
        return True


    

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
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print(f"[InstanceManager] Instance '{name}' started successfully.")
                return True
            else:
                print(f"[InstanceManager] Failed to start '{name}': {result.stderr}")
                return False
        except Exception as e:
            print(f"[InstanceManager] ERROR starting '{name}': {e}")
            return False

    def get_instances(self):
        return self.instances