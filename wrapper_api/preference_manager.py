"""
User Preference Management System

Handles capturing, storing, and managing user preferences for agent behavior.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json
from dataclasses import dataclass, asdict


class ObjectPriority(Enum):
    """Object priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    IGNORE = 5


class RoomType(Enum):
    """Room types for room-specific preferences"""
    KITCHEN = "kitchen"
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    OFFICE = "office"
    DINING_ROOM = "dining_room"
    ANY = "any"


@dataclass
class ObjectPreference:
    """Preference for a specific object or object category"""
    object_type: str
    priority: ObjectPriority
    preferred_room: Optional[RoomType] = None
    preferred_receptacle: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class RoomPreference:
    """Preferences for a specific room"""
    room_type: RoomType
    priority: ObjectPriority
    max_objects: Optional[int] = None
    forbidden_objects: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class SafetyConstraint:
    """Safety constraints for agent behavior"""
    max_distance_from_start: Optional[float] = None
    forbidden_actions: Optional[List[str]] = None
    require_confirmation: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None


class PreferenceManager:
    """
    Manages user preferences for agent behavior in the housekeeping task.
    
    This class provides methods to define, store, and retrieve user preferences
    that can influence the agent's decision-making process.
    """
    
    def __init__(self):
        self.object_preferences: Dict[str, ObjectPreference] = {}
        self.room_preferences: Dict[RoomType, RoomPreference] = {}
        self.safety_constraints: SafetyConstraint = SafetyConstraint()
        self.global_preferences: Dict[str, Any] = {
            'exploration_aggressiveness': 0.5,  # 0.0 to 1.0
            'efficiency_vs_safety': 0.7,  # 0.0 (safety) to 1.0 (efficiency)
            'user_intervention_frequency': 0.2,  # 0.0 (none) to 1.0 (always)
        }
    
    def add_object_preference(self, object_preference: ObjectPreference) -> None:
        """Add or update preference for a specific object type"""
        self.object_preferences[object_preference.object_type] = object_preference
    
    def add_room_preference(self, room_preference: RoomPreference) -> None:
        """Add or update preference for a specific room"""
        self.room_preferences[room_preference.room_type] = room_preference
    
    def set_safety_constraints(self, safety_constraints: SafetyConstraint) -> None:
        """Set safety constraints for agent behavior"""
        self.safety_constraints = safety_constraints
    
    def set_global_preference(self, key: str, value: Any) -> None:
        """Set a global preference parameter"""
        self.global_preferences[key] = value
    
    def get_object_priority(self, object_type: str) -> ObjectPriority:
        """Get priority for a specific object type"""
        if object_type in self.object_preferences:
            return self.object_preferences[object_type].priority
        return ObjectPriority.MEDIUM  # default
    
    def get_preferred_room(self, object_type: str) -> Optional[RoomType]:
        """Get preferred room for a specific object type"""
        if object_type in self.object_preferences:
            return self.object_preferences[object_type].preferred_room
        return None
    
    def get_preferred_receptacle(self, object_type: str) -> Optional[str]:
        """Get preferred receptacle for a specific object type"""
        if object_type in self.object_preferences:
            return self.object_preferences[object_type].preferred_receptacle
        return None
    
    def is_action_allowed(self, action: str) -> bool:
        """Check if an action is allowed based on safety constraints"""
        forbidden = self.safety_constraints.forbidden_actions or []
        return action not in forbidden
    
    def requires_confirmation(self, action: str) -> bool:
        """Check if an action requires user confirmation"""
        require_confirm = self.safety_constraints.require_confirmation or []
        return action in require_confirm
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary for serialization"""
        object_prefs = {}
        for k, v in self.object_preferences.items():
            obj_dict = asdict(v)
            # Convert enums to their values for serialization
            obj_dict['priority'] = obj_dict['priority'].value if hasattr(obj_dict['priority'], 'value') else obj_dict['priority']
            if obj_dict.get('preferred_room') and hasattr(obj_dict['preferred_room'], 'value'):
                obj_dict['preferred_room'] = obj_dict['preferred_room'].value
            object_prefs[k] = obj_dict
        
        room_prefs = {}
        for k, v in self.room_preferences.items():
            room_dict = asdict(v)
            room_dict['priority'] = room_dict['priority'].value if hasattr(room_dict['priority'], 'value') else room_dict['priority']
            room_dict['room_type'] = room_dict['room_type'].value if hasattr(room_dict['room_type'], 'value') else room_dict['room_type']
            room_prefs[k.value] = room_dict
        
        return {
            'object_preferences': object_prefs,
            'room_preferences': room_prefs,
            'safety_constraints': asdict(self.safety_constraints),
            'global_preferences': self.global_preferences
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load preferences from dictionary"""
        # Load object preferences
        if 'object_preferences' in data:
            for obj_type, pref_data in data['object_preferences'].items():
                # Handle priority enum conversion
                priority_val = pref_data['priority']
                if isinstance(priority_val, int):
                    pref_data['priority'] = ObjectPriority(priority_val)
                elif isinstance(priority_val, str):
                    # Handle string representation like "ObjectPriority.HIGH"
                    if '.' in priority_val:
                        priority_val = priority_val.split('.')[-1]
                    pref_data['priority'] = ObjectPriority[priority_val]
                else:
                    pref_data['priority'] = ObjectPriority(priority_val)
                
                # Handle room enum conversion
                if pref_data.get('preferred_room'):
                    room_val = pref_data['preferred_room']
                    if isinstance(room_val, str):
                        if '.' in room_val:
                            room_val = room_val.split('.')[-1]
                        pref_data['preferred_room'] = RoomType[room_val] if room_val in RoomType.__members__ else RoomType(room_val)
                    else:
                        pref_data['preferred_room'] = RoomType(room_val) if room_val else None
                
                self.object_preferences[obj_type] = ObjectPreference(**pref_data)
        
        # Load room preferences
        if 'room_preferences' in data:
            for room_name, pref_data in data['room_preferences'].items():
                # Handle room type enum conversion
                room_type_val = pref_data['room_type']
                if isinstance(room_type_val, str):
                    if '.' in room_type_val:
                        room_type_val = room_type_val.split('.')[-1]
                    pref_data['room_type'] = RoomType[room_type_val] if room_type_val in RoomType.__members__ else RoomType(room_type_val)
                else:
                    pref_data['room_type'] = RoomType(room_type_val)
                
                # Handle priority enum conversion
                priority_val = pref_data['priority']
                if isinstance(priority_val, int):
                    pref_data['priority'] = ObjectPriority(priority_val)
                elif isinstance(priority_val, str):
                    if '.' in priority_val:
                        priority_val = priority_val.split('.')[-1]
                    pref_data['priority'] = ObjectPriority[priority_val]
                else:
                    pref_data['priority'] = ObjectPriority(priority_val)
                
                room_type = pref_data['room_type']
                self.room_preferences[room_type] = RoomPreference(**pref_data)
        
        # Load safety constraints
        if 'safety_constraints' in data:
            self.safety_constraints = SafetyConstraint(**data['safety_constraints'])
        
        # Load global preferences
        if 'global_preferences' in data:
            self.global_preferences.update(data['global_preferences'])
    
    def save_to_file(self, filepath: str) -> None:
        """Save preferences to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def load_from_file(self, filepath: str) -> None:
        """Load preferences from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.from_dict(data)
    
    def create_example_preferences(self) -> None:
        """Create example preferences for demonstration"""
        # Object preferences
        self.add_object_preference(ObjectPreference(
            object_type="mug",
            priority=ObjectPriority.HIGH,
            preferred_room=RoomType.KITCHEN,
            preferred_receptacle="kitchen_counter"
        ))
        
        self.add_object_preference(ObjectPreference(
            object_type="book",
            priority=ObjectPriority.MEDIUM,
            preferred_room=RoomType.LIVING_ROOM,
            preferred_receptacle="bookshelf"
        ))
        
        self.add_object_preference(ObjectPreference(
            object_type="clothes",
            priority=ObjectPriority.HIGH,
            preferred_room=RoomType.BEDROOM,
            preferred_receptacle="wardrobe"
        ))
        
        # Room preferences
        self.add_room_preference(RoomPreference(
            room_type=RoomType.KITCHEN,
            priority=ObjectPriority.HIGH,
            max_objects=5,
            forbidden_objects=["dirty_clothes", "toys"]
        ))
        
        # Safety constraints
        self.set_safety_constraints(SafetyConstraint(
            max_distance_from_start=10.0,
            forbidden_actions=["GRAB_FRAGILE_ITEMS"],
            require_confirmation=["DELETE", "MOVE_EXPENSIVE_ITEMS"]
        ))
        
        # Global preferences
        self.set_global_preference('exploration_aggressiveness', 0.3)
        self.set_global_preference('efficiency_vs_safety', 0.8)
        self.set_global_preference('user_intervention_frequency', 0.1)