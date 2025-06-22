"""
BENSON v2.0 - Updated March Assignment System
Simplified march queue management with individual queue configuration
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class SimplifiedMarchManager:
    """Simplified march queue manager for individual queue configuration"""
    
    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        self.settings_file = f"march_config_{instance_name}.json"
        
        # Default queue assignments
        self.queue_assignments = {
            1: "AutoGather",      # Queue 1: Usually for gathering
            2: "AutoGather",      # Queue 2: Usually for gathering
            3: "Rally/Manual",    # Queue 3: For rallies/manual (if unlocked)
            4: "Rally/Manual",    # Queue 4: For rallies/manual (if unlocked)
            5: "Manual Only",     # Queue 5: Manual only (if unlocked)
            6: "Manual Only"      # Queue 6: Manual only (if unlocked)
        }
        
        # Number of unlocked queues (default 2)
        self.unlocked_queues = 2
        
        # Load existing configuration
        self.load_configuration()
    
    def load_configuration(self):
        """Load march queue configuration from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    config = json.load(f)
                
                # Load unlocked queue count
                self.unlocked_queues = config.get("unlocked_queues", 2)
                
                # Load individual queue assignments
                saved_assignments = config.get("queue_assignments", {})
                for queue_str, assignment in saved_assignments.items():
                    queue_num = int(queue_str)
                    if 1 <= queue_num <= 6:
                        self.queue_assignments[queue_num] = assignment
                
                print(f"[MarchManager] Loaded configuration for {self.instance_name}: {self.unlocked_queues} queues")
                
        except Exception as e:
            print(f"[MarchManager] Error loading configuration: {e}")
            # Use defaults
            pass
    
    def save_configuration(self):
        """Save march queue configuration to file"""
        try:
            config = {
                "unlocked_queues": self.unlocked_queues,
                "queue_assignments": {
                    str(queue_num): assignment 
                    for queue_num, assignment in self.queue_assignments.items()
                    if queue_num <= self.unlocked_queues
                },
                "last_updated": datetime.now().isoformat(),
                "instance_name": self.instance_name
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            print(f"[MarchManager] Saved configuration for {self.instance_name}")
            
        except Exception as e:
            print(f"[MarchManager] Error saving configuration: {e}")
    
    def update_unlocked_queues(self, count: int):
        """Update number of unlocked queues"""
        if 1 <= count <= 6:
            self.unlocked_queues = count
            print(f"[MarchManager] Updated unlocked queues to {count}")
            return True
        return False
    
    def update_queue_assignment(self, queue_number: int, assignment: str):
        """Update assignment for a specific queue"""
        valid_assignments = ["AutoGather", "Rally/Manual", "Manual Only"]
        
        if 1 <= queue_number <= 6 and assignment in valid_assignments:
            self.queue_assignments[queue_number] = assignment
            print(f"[MarchManager] Updated queue {queue_number} to {assignment}")
            return True
        return False
    
    def get_queue_assignment(self, queue_number: int) -> str:
        """Get assignment for a specific queue"""
        if queue_number <= self.unlocked_queues:
            return self.queue_assignments.get(queue_number, "AutoGather")
        return "Locked"
    
    def get_available_gather_queues(self) -> List[int]:
        """Get list of queues available for gathering"""
        available = []
        for queue_num in range(1, self.unlocked_queues + 1):
            if self.queue_assignments.get(queue_num) == "AutoGather":
                available.append(queue_num)
        return available
    
    def get_available_rally_queues(self) -> List[int]:
        """Get list of queues available for rallies"""
        available = []
        for queue_num in range(1, self.unlocked_queues + 1):
            assignment = self.queue_assignments.get(queue_num)
            if assignment in ["Rally/Manual", "Manual Only"]:
                available.append(queue_num)
        return available
    
    def get_manual_only_queues(self) -> List[int]:
        """Get list of queues that are manual only"""
        manual = []
        for queue_num in range(1, self.unlocked_queues + 1):
            if self.queue_assignments.get(queue_num) == "Manual Only":
                manual.append(queue_num)
        return manual
    
    def get_queue_summary(self) -> Dict:
        """Get summary of queue configuration"""
        summary = {
            "instance_name": self.instance_name,
            "total_queues": 6,
            "unlocked_queues": self.unlocked_queues,
            "queue_assignments": {},
            "available_for_gather": len(self.get_available_gather_queues()),
            "available_for_rally": len(self.get_available_rally_queues()),
            "manual_only": len(self.get_manual_only_queues())
        }
        
        # Add individual queue info
        for queue_num in range(1, 7):
            if queue_num <= self.unlocked_queues:
                assignment = self.queue_assignments.get(queue_num, "AutoGather")
                summary["queue_assignments"][f"queue_{queue_num}"] = {
                    "assignment": assignment,
                    "available": True
                }
            else:
                summary["queue_assignments"][f"queue_{queue_num}"] = {
                    "assignment": "Locked",
                    "available": False
                }
        
        return summary
    
    def reset_to_defaults(self):
        """Reset queue configuration to defaults"""
        self.unlocked_queues = 2
        self.queue_assignments = {
            1: "AutoGather",
            2: "AutoGather", 
            3: "Rally/Manual",
            4: "Rally/Manual",
            5: "Manual Only",
            6: "Manual Only"
        }
        print(f"[MarchManager] Reset {self.instance_name} to default configuration")
    
    def apply_preset(self, preset_name: str):
        """Apply a preset configuration"""
        presets = {
            "gathering_focused": {
                "unlocked": 4,
                "assignments": {1: "AutoGather", 2: "AutoGather", 3: "AutoGather", 4: "Rally/Manual"}
            },
            "rally_focused": {
                "unlocked": 4, 
                "assignments": {1: "AutoGather", 2: "Rally/Manual", 3: "Rally/Manual", 4: "Rally/Manual"}
            },
            "balanced": {
                "unlocked": 4,
                "assignments": {1: "AutoGather", 2: "AutoGather", 3: "Rally/Manual", 4: "Manual Only"}
            },
            "manual_control": {
                "unlocked": 2,
                "assignments": {1: "Manual Only", 2: "Manual Only"}
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.unlocked_queues = preset["unlocked"]
            
            for queue_num, assignment in preset["assignments"].items():
                self.queue_assignments[queue_num] = assignment
            
            print(f"[MarchManager] Applied preset '{preset_name}' to {self.instance_name}")
            return True
        
        return False
    
    def validate_configuration(self) -> Dict:
        """Validate current configuration and return any issues"""
        issues = []
        warnings = []
        
        # Check if at least one queue is available for gathering
        gather_queues = self.get_available_gather_queues()
        if not gather_queues:
            warnings.append("No queues assigned for AutoGather - resource gathering will be disabled")
        
        # Check if rally queues are available for high-level players
        rally_queues = self.get_available_rally_queues()
        if self.unlocked_queues >= 3 and not rally_queues:
            warnings.append("No queues available for rallies - consider assigning some for rally participation")
        
        # Check for reasonable distribution
        if len(gather_queues) == self.unlocked_queues and self.unlocked_queues > 2:
            warnings.append("All queues assigned to gathering - consider reserving some for rallies/manual use")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "gather_queues": len(gather_queues),
            "rally_queues": len(rally_queues),
            "total_unlocked": self.unlocked_queues
        }


# Utility functions
def get_march_manager(instance_name: str) -> SimplifiedMarchManager:
    """Get or create march manager for an instance"""
    return SimplifiedMarchManager(instance_name)


def update_march_settings_from_dialog(instance_name: str, settings: Dict) -> bool:
    """Update march settings from the settings dialog"""
    try:
        manager = get_march_manager(instance_name)
        
        # Update unlocked queue count
        unlocked_count = settings.get("unlocked_queues", 2)
        manager.update_unlocked_queues(unlocked_count)
        
        # Update individual queue assignments
        queue_assignments = settings.get("queue_assignments", {})
        for queue_str, assignment in queue_assignments.items():
            queue_num = int(queue_str)
            manager.update_queue_assignment(queue_num, assignment)
        
        # Save configuration
        manager.save_configuration()
        
        # Validate configuration
        validation = manager.validate_configuration()
        if validation["warnings"]:
            print(f"[MarchManager] Configuration warnings for {instance_name}:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
        
        return True
        
    except Exception as e:
        print(f"[MarchManager] Error updating march settings: {e}")
        return False


def get_march_configuration_for_dialog(instance_name: str) -> Dict:
    """Get march configuration formatted for the settings dialog"""
    try:
        manager = get_march_manager(instance_name)
        
        config = {
            "unlocked_queues": manager.unlocked_queues,
            "queue_assignments": {}
        }
        
        # Format assignments for dialog
        for queue_num in range(1, manager.unlocked_queues + 1):
            assignment = manager.get_queue_assignment(queue_num)
            config["queue_assignments"][str(queue_num)] = assignment
        
        return config
        
    except Exception as e:
        print(f"[MarchManager] Error getting configuration: {e}")
        return {"unlocked_queues": 2, "queue_assignments": {"1": "AutoGather", "2": "AutoGather"}}


# Export functions
__all__ = [
    'SimplifiedMarchManager',
    'get_march_manager',
    'update_march_settings_from_dialog',
    'get_march_configuration_for_dialog'
]