"""
Example usage of the Housekeep Wrapper API

This script demonstrates how to use the wrapper API to control
the Housekeep agent with user preferences.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from wrapper_api import HousekeepWrapper, PreferenceManager, ObjectPreference, RoomPreference
from wrapper_api.preference_manager import ObjectPriority, RoomType, SafetyConstraint


def basic_usage_example():
    """Basic usage example with simple preferences"""
    print("=== Basic Usage Example ===")
    
    # Create wrapper with example setup
    wrapper = HousekeepWrapper.create_with_example_setup()
    
    # Display current preferences
    print("Current preferences:")
    pref_summary = wrapper.get_preference_summary()
    print(json.dumps(pref_summary, indent=2, default=str))
    
    # Add additional preferences
    wrapper.add_object_preference('plate', 'high', 'kitchen', 'dishwasher')
    wrapper.add_object_preference('remote', 'medium', 'living_room', 'coffee_table')
    
    # Set global preferences
    wrapper.set_global_preference('exploration_aggressiveness', 0.3)  # Conservative
    wrapper.set_global_preference('user_intervention_frequency', 0.2)  # 20% of actions
    
    print("\nAgent status before initialization:")
    print(json.dumps(wrapper.get_agent_status(), indent=2, default=str))
    
    return wrapper


def advanced_preference_setup():
    """Advanced preference setup with detailed constraints"""
    print("\n=== Advanced Preference Setup ===")
    
    # Create preference manager
    pref_manager = PreferenceManager()
    
    # Define object preferences
    object_prefs = [
        ObjectPreference(
            object_type="valuable_vase",
            priority=ObjectPriority.CRITICAL,
            preferred_room=RoomType.LIVING_ROOM,
            preferred_receptacle="display_cabinet",
            constraints={"handle_with_care": True, "requires_confirmation": True}
        ),
        ObjectPreference(
            object_type="kitchen_knife",
            priority=ObjectPriority.HIGH,
            preferred_room=RoomType.KITCHEN,
            preferred_receptacle="knife_block",
            constraints={"safety_critical": True}
        ),
        ObjectPreference(
            object_type="laptop",
            priority=ObjectPriority.HIGH,
            preferred_room=RoomType.OFFICE,
            preferred_receptacle="desk",
            constraints={"avoid_water": True, "handle_carefully": True}
        )
    ]
    
    for pref in object_prefs:
        pref_manager.add_object_preference(pref)
    
    # Define room preferences
    room_prefs = [
        RoomPreference(
            room_type=RoomType.KITCHEN,
            priority=ObjectPriority.HIGH,
            max_objects=8,
            forbidden_objects=["clothes", "toys", "books"],
            constraints={"maintain_hygiene": True}
        ),
        RoomPreference(
            room_type=RoomType.BEDROOM,
            priority=ObjectPriority.MEDIUM,
            max_objects=15,
            forbidden_objects=["food_items", "dirty_dishes"],
            constraints={"privacy_zone": True}
        )
    ]
    
    for pref in room_prefs:
        pref_manager.add_room_preference(pref)
    
    # Set safety constraints
    safety_constraints = SafetyConstraint(
        max_distance_from_start=8.0,
        forbidden_actions=["DELETE_PERMANENT", "MOVE_FIXED_FURNITURE"],
        require_confirmation=["MOVE_EXPENSIVE", "HANDLE_FRAGILE"],
        constraints={"emergency_stop_enabled": True}
    )
    pref_manager.set_safety_constraints(safety_constraints)
    
    # Global preferences for fine-tuned control
    pref_manager.set_global_preference('exploration_aggressiveness', 0.6)
    pref_manager.set_global_preference('efficiency_vs_safety', 0.3)  # Prioritize safety
    pref_manager.set_global_preference('user_intervention_frequency', 0.15)
    
    # Create wrapper with advanced preferences
    wrapper = HousekeepWrapper()
    wrapper.preference_manager = pref_manager
    
    print("Advanced preferences configured:")
    print(f"Object preferences: {len(pref_manager.object_preferences)}")
    print(f"Room preferences: {len(pref_manager.room_preferences)}")
    print(f"Safety constraints: {pref_manager.safety_constraints}")
    
    return wrapper


def intervention_handling_example(wrapper):
    """Example of handling user interventions"""
    print("\n=== Intervention Handling Example ===")
    
    # Simulate some intervention requests
    from wrapper_api.action_controller import ActionIntervention
    import time
    
    # Get action controller
    action_controller = wrapper.action_controller
    
    # Simulate processing actions that might need intervention
    test_actions = [
        {'type': 'GRAB_FRAGILE', 'object': 'valuable_vase'},
        {'type': 'MOVE_FORWARD', 'distance': 2.0},
        {'type': 'MOVE_EXPENSIVE', 'object': 'laptop'},
        {'type': 'GRAB_RELEASE', 'object': 'kitchen_knife'}
    ]
    
    context = {
        'current_room': 'living_room',
        'agent_position': [1.0, 0.0, 2.0],
        'available_objects': ['vase', 'laptop', 'remote'],
        'distance_from_start': 3.5
    }
    
    print("Processing test actions...")
    for i, action in enumerate(test_actions):
        print(f"\nProcessing action {i+1}: {action['type']}")
        
        # Process action through controller
        processed_action, status = action_controller.process_action(action, context, timeout=5.0)
        
        print(f"Action status: {status}")
        
        # If intervention was requested, simulate user response
        pending = action_controller.get_pending_interventions()
        for intervention in pending:
            if intervention.action_id.endswith(str(time.time())):  # Current intervention
                print(f"Intervention requested for: {intervention.action_type}")
                
                # Simulate user decision
                if action['type'] == 'GRAB_FRAGILE':
                    # Reject dangerous action
                    action_controller.submit_user_response(
                        intervention.action_id, False, None, "Too risky for valuable item"
                    )
                elif action['type'] == 'MOVE_EXPENSIVE':
                    # Modify action to be safer
                    safer_action = {'type': 'MOVE_CAREFUL', 'object': action['object']}
                    action_controller.submit_user_response(
                        intervention.action_id, False, safer_action, "Use careful handling"
                    )
                else:
                    # Approve other actions
                    action_controller.submit_user_response(
                        intervention.action_id, True, None, "Action approved"
                    )
    
    # Show final statistics
    print("\nIntervention statistics:")
    stats = action_controller.get_action_statistics()
    print(json.dumps(stats, indent=2))


def configuration_override_example():
    """Example of dynamic configuration override"""
    print("\n=== Configuration Override Example ===")
    
    from wrapper_api import ConfigOverride
    
    # Create config override manager
    config_override = ConfigOverride()
    
    # Set manual overrides
    config_override.set_override('ENVIRONMENT.MAX_EPISODE_STEPS', 2000)
    config_override.set_override('RL.PPO.lr', 0.0001)
    config_override.set_override('RL.COLLISION_REWARD', -0.1)
    
    # Create preference manager
    pref_manager = PreferenceManager()
    pref_manager.create_example_preferences()
    pref_manager.set_global_preference('efficiency_vs_safety', 0.2)  # Very safe
    
    # Apply preferences to configuration
    final_config = config_override.apply_preferences(pref_manager)
    
    print("Configuration overrides applied:")
    print(f"Manual overrides: {config_override.get_override_summary()}")
    
    # Save configuration
    output_dir = "/tmp/housekeep_configs"
    os.makedirs(output_dir, exist_ok=True)
    config_override.save_config(os.path.join(output_dir, "custom_config.yaml"), final_config)
    print(f"Configuration saved to: {output_dir}/custom_config.yaml")


def save_and_load_preferences():
    """Example of saving and loading preferences"""
    print("\n=== Save and Load Preferences Example ===")
    
    # Create wrapper with preferences
    wrapper = HousekeepWrapper.create_with_example_setup()
    
    # Add more preferences
    wrapper.add_object_preference('wine_glass', 'critical', 'kitchen', 'wine_cabinet')
    wrapper.set_global_preference('user_intervention_frequency', 0.05)
    
    # Save preferences
    output_dir = "/tmp/housekeep_preferences"
    os.makedirs(output_dir, exist_ok=True)
    pref_file = os.path.join(output_dir, "my_preferences.json")
    wrapper.save_preferences(pref_file)
    print(f"Preferences saved to: {pref_file}")
    
    # Create new wrapper and load preferences
    new_wrapper = HousekeepWrapper()
    new_wrapper.load_preferences(pref_file)
    
    print("Preferences loaded successfully!")
    print(f"Loaded object preferences: {len(new_wrapper.preference_manager.object_preferences)}")
    
    # Verify preferences match
    original_prefs = wrapper.get_preference_summary()
    loaded_prefs = new_wrapper.get_preference_summary()
    
    print(f"Preferences match: {original_prefs == loaded_prefs}")


def main():
    """Run all examples"""
    print("Housekeep Wrapper API Examples")
    print("=" * 50)
    
    try:
        # Basic usage
        wrapper = basic_usage_example()
        
        # Advanced setup
        advanced_wrapper = advanced_preference_setup()
        
        # Intervention handling
        intervention_handling_example(wrapper)
        
        # Configuration override
        configuration_override_example()
        
        # Save/load preferences
        save_and_load_preferences()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
        # Final status
        print("\nFinal wrapper status:")
        print(json.dumps(wrapper.get_agent_status(), indent=2, default=str))
        
    except Exception as e:
        print(f"\nError during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()