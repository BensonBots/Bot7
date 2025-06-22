"""
BENSON v2.0 - Corrected March Queue Management System
March queues are for gathering and rallies only, not training
Training happens at buildings and doesn't use march slots
"""

import json
import threading
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


class MarchAssignment(Enum):
    """March queue assignment types"""
    AUTO_GATHER = "auto_gather"      # Used by AutoGather module
    RALLY_RESERVED = "rally_reserved"  # Reserved for rally participation
    MANUAL_ONLY = "manual_only"      # Completely manual control
    LOCKED = "locked"                # Queue not unlocked yet


class MarchStatus(Enum):
    """March queue status"""
    IDLE = "idle"                    # Available for new tasks
    GATHERING = "gathering"          # Currently gathering resources
    RALLY = "rally"                  # Participating in rally
    MANUAL_USE = "manual_use"        # Being used manually
    LOCKED = "locked"                # Queue not unlocked
    UNKNOWN = "unknown"              # Status unclear


class MarchQueue:
    """Represents a single march queue"""
    
    def __init__(self, queue_number: int, is_unlocked: bool = True, 
                 assignment: MarchAssignment = MarchAssignment.AUTO_GATHER):
        self.queue_number = queue_number
        self.is_unlocked = is_unlocked
        self.assignment = assignment if is_unlocked else MarchAssignment.LOCKED
        self.status = MarchStatus.IDLE if is_unlocked else MarchStatus.LOCKED
        
        # Current operation tracking
        self.current_task = None
        self.resource_type = None
        self.target_location = None
        self.estimated_return = None
        self.march_capacity = 0
        self.last_updated = datetime.now()
        
        # Statistics
        self.usage_count = 0
        self.total_duration = timedelta()
        self.resources_gathered = {"food": 0, "wood": 0, "iron": 0, "stone": 0}
    
    def start_gathering(self, resource_type: str, estimated_duration: timedelta, 
                       capacity: int = 0, location: str = None):
        """Start a gathering operation on this queue"""
        if not self.is_available_for_gathering():
            return False
        
        self.current_task = f"gather_{resource_type}"
        self.resource_type = resource_type
        self.target_location = location
        self.march_capacity = capacity
        self.status = MarchStatus.GATHERING
        self.estimated_return = datetime.now() + estimated_duration
        self.last_updated = datetime.now()
        self.usage_count += 1
        
        return True
    
    def start_rally(self, rally_target: str, estimated_duration: timedelta):
        """Start rally participation on this queue"""
        if not self.is_available_for_rally():
            return False
        
        self.current_task = f"rally_{rally_target}"
        self.target_location = rally_target
        self.status = MarchStatus.RALLY
        self.estimated_return = datetime.now() + estimated_duration
        self.last_updated = datetime.now()
        self.usage_count += 1
        
        return True
    
    def complete_operation(self, resources_gained: Dict[str, int] = None):
        """Complete current operation and return to idle"""
        if self.current_task and self.estimated_return:
            # Calculate actual duration
            start_time = self.estimated_return - (self.estimated_return - self.last_updated)
            actual_duration = datetime.now() - start_time
            self.total_duration += actual_duration
        
        # Record resources if gathering
        if resources_gained and self.status == MarchStatus.GATHERING:
            for resource, amount in resources_gained.items():
                if resource in self.resources_gathered:
                    self.resources_gathered[resource] += amount
        
        # Reset to idle
        self.current_task = None
        self.resource_type = None
        self.target_location = None
        self.estimated_return = None
        self.march_capacity = 0
        self.status = MarchStatus.IDLE if self.is_unlocked else MarchStatus.LOCKED
        self.last_updated = datetime.now()
    
    def is_available_for_gathering(self) -> bool:
        """Check if queue is available for gathering"""
        if not self.is_unlocked or self.assignment == MarchAssignment.LOCKED:
            return False
        
        if self.assignment == MarchAssignment.MANUAL_ONLY:
            return False
        
        if self.status == MarchStatus.IDLE:
            return True
        
        # Check if operation should be completed by now
        if self.estimated_return and datetime.now() >= self.estimated_return:
            self.complete_operation()
            return True
        
        return False
    
    def is_available_for_rally(self) -> bool:
        """Check if queue is available for rally participation"""
        if not self.is_unlocked or self.assignment == MarchAssignment.LOCKED:
            return False
        
        # Rally reserved and manual queues can be used for rallies
        if self.assignment in [MarchAssignment.RALLY_RESERVED, MarchAssignment.MANUAL_ONLY]:
            return self.status == MarchStatus.IDLE or (
                self.estimated_return and datetime.now() >= self.estimated_return
            )
        
        return False
    
    def unlock_queue(self):
        """Unlock this march queue"""
        if not self.is_unlocked:
            self.is_unlocked = True
            self.assignment = MarchAssignment.AUTO_GATHER  # Default assignment
            self.status = MarchStatus.IDLE
            return True
        return False
    
    def lock_queue(self):
        """Lock this march queue (if player loses VIP or downgrades)"""
        if self.is_unlocked:
            # Complete any current operation first
            if self.status in [MarchStatus.GATHERING, MarchStatus.RALLY]:
                self.complete_operation()
            
            self.is_unlocked = False
            self.assignment = MarchAssignment.LOCKED
            self.status = MarchStatus.LOCKED
            return True
        return False
    
    def get_info(self) -> Dict:
        """Get comprehensive queue information"""
        return {
            "queue_number": self.queue_number,
            "is_unlocked": self.is_unlocked,
            "assignment": self.assignment.value,
            "status": self.status.value,
            "current_task": self.current_task,
            "resource_type": self.resource_type,
            "target_location": self.target_location,
            "march_capacity": self.march_capacity,
            "estimated_return": self.estimated_return.isoformat() if self.estimated_return else None,
            "is_available_for_gathering": self.is_available_for_gathering(),
            "is_available_for_rally": self.is_available_for_rally(),
            "usage_count": self.usage_count,
            "total_duration_hours": self.total_duration.total_seconds() / 3600,
            "resources_gathered": self.resources_gathered.copy(),
            "last_updated": self.last_updated.isoformat()
        }


class MarchQueueManager:
    """Manages all march queues for an instance"""
    
    def __init__(self, instance_name: str, console_callback=None):
        self.instance_name = instance_name
        self.console_callback = console_callback or print
        
        # Initialize march queues (6 maximum)
        self.march_queues = {}
        self._initialize_queues()
        
        # Load configuration
        self.settings_file = f"march_config_{instance_name}.json"
        self._load_march_configuration()
        
        # Statistics
        self.total_gathers_sent = 0
        self.total_rallies_joined = 0
        self.operation_history = []
        
        # Thread safety
        self.lock = threading.Lock()
    
    def _initialize_queues(self):
        """Initialize march queues with default unlock status"""
        # Most players start with 2-3 queues unlocked
        # Queue 1-2: Usually unlocked by default
        # Queue 3-4: Unlocked through VIP or research
        # Queue 5-6: Higher VIP levels or advanced research
        
        default_unlock_status = {
            1: True,   # Always unlocked
            2: True,   # Usually unlocked
            3: False,  # VIP/Research required
            4: False,  # Higher VIP/Research
            5: False,  # High VIP
            6: False   # Maximum VIP
        }
        
        for queue_num in range(1, 7):
            is_unlocked = default_unlock_status.get(queue_num, False)
            self.march_queues[queue_num] = MarchQueue(queue_num, is_unlocked)
    
    def _load_march_configuration(self):
        """Load march queue configuration from file"""
        try:
            with open(self.settings_file, 'r') as f:
                config = json.load(f)
            
            # Load unlock status
            unlock_status = config.get("unlocked_queues", {})
            for queue_num, is_unlocked in unlock_status.items():
                queue_number = int(queue_num)
                if queue_number in self.march_queues:
                    if is_unlocked and not self.march_queues[queue_number].is_unlocked:
                        self.march_queues[queue_number].unlock_queue()
                    elif not is_unlocked and self.march_queues[queue_number].is_unlocked:
                        self.march_queues[queue_number].lock_queue()
            
            # Load assignments
            assignments = config.get("queue_assignments", {})
            assignment_mapping = {
                "AutoGather": MarchAssignment.AUTO_GATHER,
                "Rally/Manual": MarchAssignment.RALLY_RESERVED,
                "Manual Only": MarchAssignment.MANUAL_ONLY
            }
            
            for queue_num, assignment_name in assignments.items():
                queue_number = int(queue_num)
                if queue_number in self.march_queues and self.march_queues[queue_number].is_unlocked:
                    assignment = assignment_mapping.get(assignment_name, MarchAssignment.AUTO_GATHER)
                    self.march_queues[queue_number].assignment = assignment
            
            self.log_message(f"📋 Loaded march queue configuration")
            self._log_queue_summary()
            
        except FileNotFoundError:
            self.log_message(f"📋 No march configuration found, using defaults")
            self._apply_default_configuration()
        except Exception as e:
            self.log_message(f"❌ Error loading march configuration: {e}")
            self._apply_default_configuration()
    
    def _apply_default_configuration(self):
        """Apply default march queue configuration"""
        # Default assignments for unlocked queues
        for queue in self.march_queues.values():
            if queue.is_unlocked:
                if queue.queue_number <= 2:
                    queue.assignment = MarchAssignment.AUTO_GATHER
                elif queue.queue_number <= 4:
                    queue.assignment = MarchAssignment.AUTO_GATHER  
                else:
                    queue.assignment = MarchAssignment.RALLY_RESERVED
        
        self._log_queue_summary()
    
    def _log_queue_summary(self):
        """Log current march queue status"""
        unlocked_count = len([q for q in self.march_queues.values() if q.is_unlocked])
        assignment_summary = {}
        
        for queue in self.march_queues.values():
            if queue.is_unlocked:
                assignment = queue.assignment.value
                assignment_summary[assignment] = assignment_summary.get(assignment, 0) + 1
        
        self.log_message(f"📊 March Queues: {unlocked_count}/6 unlocked")
        if assignment_summary:
            summary_text = ", ".join([f"{count} {assignment.replace('_', ' ')}" 
                                    for assignment, count in assignment_summary.items()])
            self.log_message(f"📊 Assignments: {summary_text}")
    
    def log_message(self, message: str):
        """Log message with queue manager context"""
        formatted_message = f"[MarchQueue-{self.instance_name}] {message}"
        if self.console_callback:
            self.console_callback(formatted_message)
        print(formatted_message)
    
    def update_unlocked_queues(self, unlocked_queues: List[int]):
        """Update which queues are unlocked"""
        with self.lock:
            changes_made = False
            
            for queue_num in range(1, 7):
                should_be_unlocked = queue_num in unlocked_queues
                queue = self.march_queues[queue_num]
                
                if should_be_unlocked and not queue.is_unlocked:
                    queue.unlock_queue()
                    self.log_message(f"🔓 Unlocked march queue #{queue_num}")
                    changes_made = True
                elif not should_be_unlocked and queue.is_unlocked:
                    queue.lock_queue()
                    self.log_message(f"🔒 Locked march queue #{queue_num}")
                    changes_made = True
            
            if changes_made:
                self._save_configuration()
                self._log_queue_summary()
            
            return changes_made
    
    def request_queue_for_gathering(self, resource_type: str, 
                                  estimated_duration: timedelta = None,
                                  capacity: int = 0) -> Optional[int]:
        """Request a march queue for resource gathering"""
        with self.lock:
            # Find available AUTO_GATHER queues
            available_queues = [
                queue for queue in self.march_queues.values()
                if queue.assignment == MarchAssignment.AUTO_GATHER and queue.is_available_for_gathering()
            ]
            
            if not available_queues:
                self.log_message(f"❌ No available gathering queues for {resource_type}")
                return None
            
            # Select the lowest numbered available queue
            selected_queue = min(available_queues, key=lambda q: q.queue_number)
            
            # Start the gathering operation
            duration = estimated_duration or timedelta(hours=2)  # Default 2 hours
            location = f"{resource_type}_tile_{int(time.time())}"  # Placeholder location
            
            success = selected_queue.start_gathering(resource_type, duration, capacity, location)
            
            if success:
                self.total_gathers_sent += 1
                self.operation_history.append({
                    "type": "gather",
                    "queue": selected_queue.queue_number,
                    "resource": resource_type,
                    "timestamp": datetime.now().isoformat(),
                    "estimated_duration": duration.total_seconds() / 3600,
                    "capacity": capacity
                })
                
                self.log_message(f"✅ Queue #{selected_queue.queue_number} gathering {resource_type}")
                return selected_queue.queue_number
            
            return None
    
    def request_queue_for_rally(self, rally_target: str, 
                              estimated_duration: timedelta = None) -> Optional[int]:
        """Request a march queue for rally participation"""
        with self.lock:
            # Find available rally queues
            available_queues = [
                queue for queue in self.march_queues.values()
                if queue.is_available_for_rally()
            ]
            
            if not available_queues:
                self.log_message(f"❌ No available rally queues for {rally_target}")
                return None
            
            # Prefer rally-reserved queues, then manual queues
            rally_reserved = [q for q in available_queues if q.assignment == MarchAssignment.RALLY_RESERVED]
            selected_queue = (rally_reserved[0] if rally_reserved else available_queues[0])
            
            # Start the rally operation
            duration = estimated_duration or timedelta(minutes=30)  # Default 30 minutes
            
            success = selected_queue.start_rally(rally_target, duration)
            
            if success:
                self.total_rallies_joined += 1
                self.operation_history.append({
                    "type": "rally",
                    "queue": selected_queue.queue_number,
                    "target": rally_target,
                    "timestamp": datetime.now().isoformat(),
                    "estimated_duration": duration.total_seconds() / 3600
                })
                
                self.log_message(f"⚔️ Queue #{selected_queue.queue_number} joining rally: {rally_target}")
                return selected_queue.queue_number
            
            return None
    
    def complete_operation(self, queue_number: int, resources_gained: Dict[str, int] = None):
        """Mark an operation as completed"""
        with self.lock:
            if queue_number not in self.march_queues:
                return False
            
            queue = self.march_queues[queue_number]
            operation_type = "rally" if queue.status == MarchStatus.RALLY else "gathering"
            target = queue.target_location or queue.resource_type
            
            queue.complete_operation(resources_gained)
            
            if target:
                self.log_message(f"✅ Queue #{queue_number} completed {operation_type}: {target}")
                if resources_gained:
                    resource_text = ", ".join([f"{amount:,} {res}" for res, amount in resources_gained.items() if amount > 0])
                    if resource_text:
                        self.log_message(f"📦 Gained: {resource_text}")
            
            return True
    
    def get_available_gathering_queues(self) -> int:
        """Get number of available queues for gathering"""
        with self.lock:
            return len([
                queue for queue in self.march_queues.values()
                if queue.assignment == MarchAssignment.AUTO_GATHER and queue.is_available_for_gathering()
            ])
    
    def get_available_rally_queues(self) -> int:
        """Get number of available queues for rallies"""
        with self.lock:
            return len([
                queue for queue in self.march_queues.values()
                if queue.is_available_for_rally()
            ])
    
    def get_gathering_capacity(self) -> int:
        """Get total gathering capacity (assigned gathering queues)"""
        return len([
            queue for queue in self.march_queues.values()
            if queue.assignment == MarchAssignment.AUTO_GATHER and queue.is_unlocked
        ])
    
    def get_active_operations(self) -> Dict[str, List[Dict]]:
        """Get information about active operations"""
        active_gathers = []
        active_rallies = []
        
        for queue in self.march_queues.values():
            if queue.status == MarchStatus.GATHERING:
                active_gathers.append({
                    "queue_number": queue.queue_number,
                    "resource_type": queue.resource_type,
                    "capacity": queue.march_capacity,
                    "location": queue.target_location,
                    "estimated_return": queue.estimated_return.isoformat() if queue.estimated_return else None
                })
            elif queue.status == MarchStatus.RALLY:
                active_rallies.append({
                    "queue_number": queue.queue_number,
                    "target": queue.target_location,
                    "estimated_return": queue.estimated_return.isoformat() if queue.estimated_return else None
                })
        
        return {
            "gathers": active_gathers,
            "rallies": active_rallies
        }
    
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive march queue manager status"""
        with self.lock:
            unlocked_queues = [q.queue_number for q in self.march_queues.values() if q.is_unlocked]
            active_ops = self.get_active_operations()
            
            status = {
                "instance_name": self.instance_name,
                "total_queues": 6,
                "unlocked_queues": len(unlocked_queues),
                "unlocked_queue_numbers": unlocked_queues,
                "available_gathering_queues": self.get_available_gathering_queues(),
                "available_rally_queues": self.get_available_rally_queues(),
                "gathering_capacity": self.get_gathering_capacity(),
                "total_gathers_sent": self.total_gathers_sent,
                "total_rallies_joined": self.total_rallies_joined,
                "active_gathers": len(active_ops["gathers"]),
                "active_rallies": len(active_ops["rallies"]),
                "queues": {
                    queue_num: queue.get_info() 
                    for queue_num, queue in self.march_queues.items()
                },
                "active_operations": active_ops,
                "recent_operations": self.operation_history[-10:]  # Last 10 operations
            }
            
            return status
    
    def update_queue_assignments(self, new_assignments: Dict[int, str]):
        """Update march queue assignments"""
        with self.lock:
            assignment_mapping = {
                "AutoGather": MarchAssignment.AUTO_GATHER,
                "Rally/Manual": MarchAssignment.RALLY_RESERVED,
                "Manual Only": MarchAssignment.MANUAL_ONLY
            }
            
            changes_made = False
            
            for queue_num, assignment_name in new_assignments.items():
                if queue_num in self.march_queues and self.march_queues[queue_num].is_unlocked:
                    new_assignment = assignment_mapping.get(assignment_name, MarchAssignment.AUTO_GATHER)
                    old_assignment = self.march_queues[queue_num].assignment
                    
                    if old_assignment != new_assignment:
                        # If queue is currently busy and being changed to manual, warn
                        queue = self.march_queues[queue_num]
                        if (not queue.is_available_for_gathering() and 
                            new_assignment == MarchAssignment.MANUAL_ONLY):
                            self.log_message(f"⚠️ Queue #{queue_num} changed to manual but currently busy")
                        
                        self.march_queues[queue_num].assignment = new_assignment
                        changes_made = True
                        self.log_message(f"🔄 Queue #{queue_num}: {old_assignment.value} → {new_assignment.value}")
            
            if changes_made:
                self._save_configuration()
                self._log_queue_summary()
            
            return changes_made
    
    def _save_configuration(self):
        """Save current march configuration to file"""
        try:
            config = {
                "unlocked_queues": {
                    str(queue_num): queue.is_unlocked
                    for queue_num, queue in self.march_queues.items()
                },
                "queue_assignments": {},
                "last_updated": datetime.now().isoformat()
            }
            
            assignment_mapping = {
                MarchAssignment.AUTO_GATHER: "AutoGather",
                MarchAssignment.RALLY_RESERVED: "Rally/Manual",
                MarchAssignment.MANUAL_ONLY: "Manual Only"
            }
            
            for queue_num, queue in self.march_queues.items():
                if queue.is_unlocked:
                    config["queue_assignments"][str(queue_num)] = assignment_mapping[queue.assignment]
            
            with open(self.settings_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_message("💾 Saved march queue configuration")
            
        except Exception as e:
            self.log_message(f"❌ Error saving configuration: {e}")
    
    def force_return_queue(self, queue_number: int, reason: str = "Manual override"):
        """Force a march queue to return (emergency)"""
        with self.lock:
            if queue_number not in self.march_queues:
                return False
            
            queue = self.march_queues[queue_number]
            if queue.status in [MarchStatus.GATHERING, MarchStatus.RALLY]:
                operation_type = "rally" if queue.status == MarchStatus.RALLY else "gathering"
                self.log_message(f"🛑 Force returning queue #{queue_number} from {operation_type}: {reason}")
                queue.complete_operation()
                return True
            
            return False