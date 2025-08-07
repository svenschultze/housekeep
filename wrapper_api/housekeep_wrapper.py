"""
Main Housekeep Wrapper API

Provides a high-level interface for controlling the Housekeep agent with user preferences.
This is the main entry point for the wrapper API.
"""

from typing import Dict, List, Optional, Any, Callable
import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cos_eor.trainer.hie_policy_runner import HiePolicyRunner
from cos_eor.policy.hie_policy import HiePolicy
from habitat_baselines.config.default import get_config

from .preference_manager import PreferenceManager, ObjectPreference, RoomPreference, SafetyConstraint
from .policy_wrapper import PolicyWrapper
from .config_override import ConfigOverride
from .action_controller import ActionController, ActionIntervention, ActionStatus


class HousekeepWrapper:
    """
    Main wrapper class for the Housekeep agent with user preference integration.
    
    This class provides a high-level interface to:
    1. Configure the agent with user preferences
    2. Control agent behavior in real-time
    3. Monitor and intervene in agent actions
    4. Collect feedback and adapt behavior
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 preference_file: Optional[str] = None):
        """
        Initialize the Housekeep wrapper.
        
        Args:
            config_path: Path to base configuration file
            preference_file: Path to user preferences JSON file
        """
        self.preference_manager = PreferenceManager()
        self.config_override = ConfigOverride(config_path)
        self.action_controller = ActionController(self.preference_manager)
        
        # Core components (initialized later)
        self.policy_runner: Optional[HiePolicyRunner] = None
        self.wrapped_policy: Optional[PolicyWrapper] = None
        self.current_config: Optional[Dict[str, Any]] = None
        
        # State tracking
        self.is_running = False
        self.current_episode = 0
        self.episode_history = []
        
        # Load preferences if provided
        if preference_file and os.path.exists(preference_file):
            self.preference_manager.load_from_file(preference_file)
        else:
            # Create example preferences for demonstration
            self.preference_manager.create_example_preferences()
    
    def configure_preferences(self, preferences: Optional[Dict[str, Any]] = None) -> None:
        """
        Configure user preferences.
        
        Args:
            preferences: Dictionary of preferences or None to use interactive setup
        """
        if preferences:
            self.preference_manager.from_dict(preferences)
        else:
            # Interactive preference setup (placeholder)
            print("Interactive preference setup not yet implemented")
            print("Using example preferences for now")
            self.preference_manager.create_example_preferences()
    
    def add_object_preference(self, object_type: str, priority: str, 
                            preferred_room: Optional[str] = None,
                            preferred_receptacle: Optional[str] = None) -> None:
        """
        Add preference for a specific object type.
        
        Args:
            object_type: Type of object (e.g., 'mug', 'book', 'clothes')
            priority: Priority level ('critical', 'high', 'medium', 'low', 'ignore')
            preferred_room: Optional preferred room
            preferred_receptacle: Optional preferred receptacle
        """
        from .preference_manager import ObjectPriority, RoomType
        
        # Convert string priority to enum
        priority_map = {
            'critical': ObjectPriority.CRITICAL,
            'high': ObjectPriority.HIGH,
            'medium': ObjectPriority.MEDIUM,
            'low': ObjectPriority.LOW,
            'ignore': ObjectPriority.IGNORE
        }
        
        priority_enum = priority_map.get(priority.lower(), ObjectPriority.MEDIUM)
        
        # Convert room string to enum if provided
        room_enum = None
        if preferred_room:
            room_map = {room.value: room for room in RoomType}
            room_enum = room_map.get(preferred_room.lower())
        
        # Create and add preference
        preference = ObjectPreference(
            object_type=object_type,
            priority=priority_enum,
            preferred_room=room_enum,
            preferred_receptacle=preferred_receptacle
        )
        
        self.preference_manager.add_object_preference(preference)
    
    def set_global_preference(self, key: str, value: Any) -> None:
        """Set a global preference parameter"""
        self.preference_manager.set_global_preference(key, value)
    
    def initialize_agent(self, config_overrides: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the agent with current preferences.
        
        Args:
            config_overrides: Optional manual configuration overrides
        """
        # Apply preferences to create configuration
        self.current_config = self.config_override.apply_preferences(self.preference_manager)
        
        # Apply any manual overrides
        if config_overrides:
            for key, value in config_overrides.items():
                self.config_override.set_override(key, value)
            self.current_config = self.config_override.apply_preferences(self.preference_manager)
        
        # Create habitat config from our processed config
        habitat_config = get_config(None, opts=[])
        
        # Update habitat config with our processed config
        self._update_habitat_config(habitat_config, self.current_config)
        
        # Initialize policy runner
        self.policy_runner = HiePolicyRunner(habitat_config)
        
        # Wrap the policy with preference awareness
        if hasattr(self.policy_runner, 'policy') and self.policy_runner.policy:
            self.wrapped_policy = PolicyWrapper(
                self.policy_runner.policy, 
                self.preference_manager
            )
            # Replace the original policy with our wrapper
            self.policy_runner.policy = self.wrapped_policy
        
        # Set up action controller callbacks
        self.action_controller.add_intervention_callback(self._handle_intervention_request)
        self.action_controller.add_action_callback(self._handle_action_event)
    
    def run_episode(self, scene_name: str, max_steps: Optional[int] = None) -> Dict[str, Any]:
        """
        Run a single episode with user preference integration.
        
        Args:
            scene_name: Name of the scene to run
            max_steps: Optional maximum number of steps
            
        Returns:
            Episode results and statistics
        """
        if not self.policy_runner:
            raise RuntimeError("Agent not initialized. Call initialize_agent() first.")
        
        self.is_running = True
        self.current_episode += 1
        
        # Prepare episode configuration
        episode_config = self.current_config.copy() if self.current_config else {}
        if max_steps:
            episode_config['ENVIRONMENT'] = episode_config.get('ENVIRONMENT', {})
            episode_config['ENVIRONMENT']['MAX_EPISODE_STEPS'] = max_steps
        
        try:
            # Run episode with intervention
            results = self._run_episode_with_intervention(scene_name, episode_config)
            
            # Store episode history
            episode_info = {
                'episode_number': self.current_episode,
                'scene_name': scene_name,
                'results': results,
                'preferences_applied': self.preference_manager.to_dict(),
                'interventions': self.action_controller.get_action_statistics()
            }
            self.episode_history.append(episode_info)
            
            return results
            
        finally:
            self.is_running = False
    
    def get_intervention_requests(self) -> List[ActionIntervention]:
        """Get pending intervention requests"""
        return self.action_controller.get_pending_interventions()
    
    def respond_to_intervention(self, action_id: str, approved: bool, 
                               modified_action: Optional[Any] = None,
                               reason: Optional[str] = None) -> bool:
        """
        Respond to an intervention request.
        
        Args:
            action_id: ID of the action intervention
            approved: Whether to approve the action
            modified_action: Optional modified action
            reason: Optional reason for the decision
            
        Returns:
            True if response was successfully submitted
        """
        return self.action_controller.submit_user_response(
            action_id, approved, modified_action, reason
        )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of the agent and wrapper system"""
        status = {
            'is_running': self.is_running,
            'current_episode': self.current_episode,
            'total_episodes': len(self.episode_history),
            'agent_initialized': self.policy_runner is not None,
            'preferences_loaded': bool(self.preference_manager.object_preferences),
            'pending_interventions': len(self.action_controller.get_pending_interventions())
        }
        
        if self.wrapped_policy:
            status.update(self.wrapped_policy.get_preference_summary())
        
        if self.action_controller:
            status.update(self.action_controller.get_action_statistics())
        
        return status
    
    def get_preference_summary(self) -> Dict[str, Any]:
        """Get summary of current preferences"""
        return {
            'object_preferences': len(self.preference_manager.object_preferences),
            'room_preferences': len(self.preference_manager.room_preferences),
            'safety_constraints': self.preference_manager.safety_constraints.__dict__,
            'global_preferences': self.preference_manager.global_preferences,
            'preferences_dict': self.preference_manager.to_dict()
        }
    
    def save_preferences(self, filepath: str) -> None:
        """Save current preferences to file"""
        self.preference_manager.save_to_file(filepath)
    
    def load_preferences(self, filepath: str) -> None:
        """Load preferences from file"""
        self.preference_manager.load_from_file(filepath)
        
        # Reinitialize agent if it was already initialized
        if self.policy_runner:
            self.initialize_agent()
    
    def export_episode_data(self, output_dir: str) -> None:
        """Export episode history and statistics"""
        import json
        os.makedirs(output_dir, exist_ok=True)
        
        # Export episode history
        with open(os.path.join(output_dir, 'episode_history.json'), 'w') as f:
            json.dump(self.episode_history, f, indent=2, default=str)
        
        # Export current preferences
        self.save_preferences(os.path.join(output_dir, 'preferences.json'))
        
        # Export agent status
        with open(os.path.join(output_dir, 'agent_status.json'), 'w') as f:
            json.dump(self.get_agent_status(), f, indent=2, default=str)
        
        # Export configuration
        if self.current_config:
            self.config_override.save_config(
                os.path.join(output_dir, 'final_config.yaml'),
                self.current_config
            )
    
    def _update_habitat_config(self, habitat_config, processed_config: Dict[str, Any]) -> None:
        """Update habitat configuration with processed config"""
        # This is a simplified update - full implementation would need to properly
        # map our configuration structure to habitat's expected structure
        
        # Update key configuration values
        if 'ENVIRONMENT' in processed_config:
            for key, value in processed_config['ENVIRONMENT'].items():
                if hasattr(habitat_config, key):
                    setattr(habitat_config, key, value)
        
        if 'RL' in processed_config:
            rl_config = processed_config['RL']
            if hasattr(habitat_config, 'RL'):
                for key, value in rl_config.items():
                    if hasattr(habitat_config.RL, key):
                        setattr(habitat_config.RL, key, value)
    
    def _run_episode_with_intervention(self, scene_name: str, 
                                     episode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run episode with action intervention capability"""
        # This is a placeholder for the actual episode running logic
        # In a full implementation, this would:
        # 1. Set up the environment with the scene
        # 2. Run the policy step by step
        # 3. Intercept actions through action_controller
        # 4. Apply user interventions
        # 5. Collect and return results
        
        results = {
            'scene_name': scene_name,
            'steps_taken': 0,
            'objects_rearranged': 0,
            'success_rate': 0.0,
            'interventions_applied': 0,
            'preference_compliance': 0.0
        }
        
        return results
    
    def _handle_intervention_request(self, intervention: ActionIntervention) -> None:
        """Handle intervention request callback"""
        # In a real implementation, this would:
        # 1. Display intervention request to user interface
        # 2. Provide options for approval/modification/rejection
        # 3. Wait for user input
        
        print(f"Intervention requested for action: {intervention.action_type}")
        print(f"Action ID: {intervention.action_id}")
        print(f"Context: {intervention.context}")
    
    def _handle_action_event(self, action_id: str, action_info: Dict[str, Any]) -> None:
        """Handle action event callback"""
        # Log or process action events
        pass
    
    @classmethod
    def create_with_example_setup(cls, config_path: Optional[str] = None) -> 'HousekeepWrapper':
        """
        Create a HousekeepWrapper with example preferences for demonstration.
        
        Args:
            config_path: Optional path to base configuration file
            
        Returns:
            Configured HousekeepWrapper instance
        """
        wrapper = cls(config_path)
        
        # Set up example preferences
        wrapper.add_object_preference('mug', 'high', 'kitchen', 'kitchen_counter')
        wrapper.add_object_preference('book', 'medium', 'living_room', 'bookshelf')
        wrapper.add_object_preference('clothes', 'high', 'bedroom', 'wardrobe')
        wrapper.add_object_preference('toy', 'low', 'living_room', 'toy_box')
        
        # Set global preferences
        wrapper.set_global_preference('exploration_aggressiveness', 0.4)
        wrapper.set_global_preference('efficiency_vs_safety', 0.8)
        wrapper.set_global_preference('user_intervention_frequency', 0.1)
        
        return wrapper