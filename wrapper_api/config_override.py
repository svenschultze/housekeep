"""
Configuration Override System

Provides dynamic configuration management that allows user preferences
to override default configuration values at runtime.
"""

from typing import Dict, Any, Optional
import yaml
import copy
from pathlib import Path

from .preference_manager import PreferenceManager, ObjectPriority, RoomType


class ConfigOverride:
    """
    Manages configuration overrides based on user preferences.
    
    This class takes a base configuration and applies user preferences
    to create a modified configuration that reflects user choices.
    """
    
    def __init__(self, base_config_path: Optional[str] = None):
        self.base_config = {}
        self.overrides = {}
        
        if base_config_path:
            self.load_base_config(base_config_path)
    
    def load_base_config(self, config_path: str) -> None:
        """Load base configuration from YAML file"""
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def apply_preferences(self, preference_manager: PreferenceManager) -> Dict[str, Any]:
        """
        Apply user preferences to create modified configuration.
        
        Args:
            preference_manager: PreferenceManager instance with user preferences
            
        Returns:
            Modified configuration dictionary
        """
        # Start with base configuration
        config = copy.deepcopy(self.base_config)
        
        # Apply global preference overrides
        self._apply_global_preferences(config, preference_manager)
        
        # Apply exploration preferences
        self._apply_exploration_preferences(config, preference_manager)
        
        # Apply safety constraint overrides
        self._apply_safety_constraints(config, preference_manager)
        
        # Apply object/room specific overrides
        self._apply_object_preferences(config, preference_manager)
        
        # Apply any manual overrides
        self._apply_manual_overrides(config)
        
        return config
    
    def _apply_global_preferences(self, config: Dict[str, Any], preference_manager: PreferenceManager) -> None:
        """Apply global preference overrides to configuration"""
        global_prefs = preference_manager.global_preferences
        
        # Adjust efficiency vs safety
        efficiency_vs_safety = global_prefs.get('efficiency_vs_safety', 0.7)
        
        if efficiency_vs_safety > 0.8:
            # High efficiency mode
            self._set_nested_value(config, 'ENVIRONMENT.MAX_EPISODE_STEPS', 1500)
            self._set_nested_value(config, 'RL.PPO.num_steps', 1200)
            self._set_nested_value(config, 'RL.COLLISION_REWARD', -0.05)  # Less penalty for collisions
        elif efficiency_vs_safety < 0.3:
            # High safety mode
            self._set_nested_value(config, 'ENVIRONMENT.MAX_EPISODE_STEPS', 800)
            self._set_nested_value(config, 'RL.PPO.num_steps', 600)
            self._set_nested_value(config, 'RL.COLLISION_REWARD', -0.2)  # Higher penalty for collisions
        
        # Adjust intervention frequency
        intervention_freq = global_prefs.get('user_intervention_frequency', 0.2)
        self._set_nested_value(config, 'RL.POLICY.intervention_frequency', intervention_freq)
    
    def _apply_exploration_preferences(self, config: Dict[str, Any], preference_manager: PreferenceManager) -> None:
        """Apply exploration preference overrides"""
        exploration_aggressiveness = preference_manager.global_preferences.get('exploration_aggressiveness', 0.5)
        
        # Adjust exploration parameters based on aggressiveness
        if exploration_aggressiveness > 0.7:
            # Aggressive exploration
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps', 200)
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps_since_new_area', 15000)
            self._set_nested_value(config, 'RL.POLICY.explore.type', 'frontier')  # Use frontier exploration
        elif exploration_aggressiveness < 0.3:
            # Conservative exploration
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps', 64)
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps_since_new_area', 5000)
            self._set_nested_value(config, 'RL.POLICY.explore.type', 'oracle')  # Use oracle if available
        else:
            # Moderate exploration (default)
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps', 128)
            self._set_nested_value(config, 'RL.POLICY.explore.max_steps_since_new_area', 10000)
    
    def _apply_safety_constraints(self, config: Dict[str, Any], preference_manager: PreferenceManager) -> None:
        """Apply safety constraint overrides"""
        safety_constraints = preference_manager.safety_constraints
        
        # Apply distance constraints
        if safety_constraints.max_distance_from_start:
            self._set_nested_value(config, 'RL.POLICY.max_distance_from_start', 
                                 safety_constraints.max_distance_from_start)
        
        # Apply forbidden actions
        if safety_constraints.forbidden_actions:
            # Remove forbidden actions from possible actions
            possible_actions = self._get_nested_value(config, 'TASK.POSSIBLE_ACTIONS', [])
            filtered_actions = [action for action in possible_actions 
                              if action not in safety_constraints.forbidden_actions]
            self._set_nested_value(config, 'TASK.POSSIBLE_ACTIONS', filtered_actions)
        
        # Apply confirmation requirements
        if safety_constraints.require_confirmation:
            self._set_nested_value(config, 'RL.POLICY.require_confirmation', 
                                 safety_constraints.require_confirmation)
    
    def _apply_object_preferences(self, config: Dict[str, Any], preference_manager: PreferenceManager) -> None:
        """Apply object and room specific preferences"""
        # Create preference-based scoring weights
        object_weights = {}
        for obj_type, pref in preference_manager.object_preferences.items():
            weight = self._priority_to_weight(pref.priority)
            object_weights[obj_type] = weight
        
        if object_weights:
            self._set_nested_value(config, 'RL.POLICY.rank.object_weights', object_weights)
        
        # Apply room preferences
        room_weights = {}
        for room_type, pref in preference_manager.room_preferences.items():
            weight = self._priority_to_weight(pref.priority)
            room_weights[room_type.value] = weight
        
        if room_weights:
            self._set_nested_value(config, 'RL.POLICY.rank.room_weights', room_weights)
    
    def _apply_manual_overrides(self, config: Dict[str, Any]) -> None:
        """Apply any manually set configuration overrides"""
        for key_path, value in self.overrides.items():
            self._set_nested_value(config, key_path, value)
    
    def set_override(self, key_path: str, value: Any) -> None:
        """
        Manually set a configuration override.
        
        Args:
            key_path: Dot-separated path to configuration value (e.g., 'RL.PPO.lr')
            value: New value to set
        """
        self.overrides[key_path] = value
    
    def remove_override(self, key_path: str) -> None:
        """Remove a manual configuration override"""
        if key_path in self.overrides:
            del self.overrides[key_path]
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get a nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def _priority_to_weight(self, priority: ObjectPriority) -> float:
        """Convert priority enum to numerical weight"""
        weights = {
            ObjectPriority.CRITICAL: 2.0,
            ObjectPriority.HIGH: 1.5,
            ObjectPriority.MEDIUM: 1.0,
            ObjectPriority.LOW: 0.5,
            ObjectPriority.IGNORE: 0.1
        }
        return weights.get(priority, 1.0)
    
    def save_config(self, output_path: str, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            output_path: Path to save configuration file
            config: Configuration to save (if None, uses base config with current overrides)
        """
        if config is None:
            config = copy.deepcopy(self.base_config)
            self._apply_manual_overrides(config)
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def get_override_summary(self) -> Dict[str, Any]:
        """Get summary of active configuration overrides"""
        return {
            'manual_overrides_count': len(self.overrides),
            'manual_overrides': dict(self.overrides),
            'has_base_config': bool(self.base_config)
        }
    
    def create_preference_based_config(self, preference_manager: PreferenceManager, 
                                     output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a complete configuration based on user preferences.
        
        Args:
            preference_manager: PreferenceManager with user preferences
            output_path: Optional path to save the configuration
            
        Returns:
            Complete configuration dictionary
        """
        config = self.apply_preferences(preference_manager)
        
        if output_path:
            self.save_config(output_path, config)
        
        return config
    
    @classmethod
    def from_preference_file(cls, preference_file: str, base_config_path: str) -> 'ConfigOverride':
        """
        Create ConfigOverride instance from a preference file.
        
        Args:
            preference_file: Path to JSON file with user preferences
            base_config_path: Path to base configuration YAML file
            
        Returns:
            ConfigOverride instance with preferences applied
        """
        config_override = cls(base_config_path)
        
        # Load preferences
        preference_manager = PreferenceManager()
        preference_manager.load_from_file(preference_file)
        
        # Apply preferences as overrides
        preference_config = config_override.apply_preferences(preference_manager)
        
        return config_override