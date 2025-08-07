#!/usr/bin/env python3
"""
Simple test and demonstration of the Housekeep Wrapper API

This script demonstrates the core functionality without requiring
the full Housekeep environment to be set up.
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_preference_management():
    """Test preference management functionality"""
    print("=== Testing Preference Management ===")
    
    from wrapper_api import PreferenceManager
    from wrapper_api.preference_manager import ObjectPreference, RoomPreference, SafetyConstraint
    from wrapper_api.preference_manager import ObjectPriority, RoomType
    
    # Create preference manager
    pm = PreferenceManager()
    
    # Add object preferences
    pm.add_object_preference(ObjectPreference(
        object_type="coffee_mug",
        priority=ObjectPriority.HIGH,
        preferred_room=RoomType.KITCHEN,
        preferred_receptacle="kitchen_counter"
    ))
    
    pm.add_object_preference(ObjectPreference(
        object_type="laptop",
        priority=ObjectPriority.CRITICAL,
        preferred_room=RoomType.OFFICE,
        preferred_receptacle="desk"
    ))
    
    # Add room preferences
    pm.add_room_preference(RoomPreference(
        room_type=RoomType.KITCHEN,
        priority=ObjectPriority.HIGH,
        max_objects=6,
        forbidden_objects=["dirty_clothes", "toys"]
    ))
    
    # Set safety constraints
    pm.set_safety_constraints(SafetyConstraint(
        max_distance_from_start=5.0,
        forbidden_actions=["DELETE", "BREAK"],
        require_confirmation=["MOVE_EXPENSIVE"]
    ))
    
    # Set global preferences
    pm.set_global_preference('exploration_aggressiveness', 0.4)
    pm.set_global_preference('user_intervention_frequency', 0.1)
    
    print(f"✓ Created {len(pm.object_preferences)} object preferences")
    print(f"✓ Created {len(pm.room_preferences)} room preferences")
    print(f"✓ Set safety constraints: {pm.safety_constraints.max_distance_from_start}m max distance")
    
    # Test preference queries
    mug_priority = pm.get_object_priority("coffee_mug")
    laptop_room = pm.get_preferred_room("laptop")
    
    print(f"✓ Coffee mug priority: {mug_priority}")
    print(f"✓ Laptop preferred room: {laptop_room}")
    
    return pm


def test_action_controller(preference_manager):
    """Test action controller functionality"""
    print("\n=== Testing Action Controller ===")
    
    from wrapper_api import ActionController
    from wrapper_api.action_controller import ActionStatus
    
    ac = ActionController(preference_manager)
    
    # Test various actions
    test_actions = [
        ("MOVE_FORWARD", {"distance": 1.0}),
        ("GRAB_RELEASE", {"object": "coffee_mug"}),
        ("MOVE_EXPENSIVE", {"object": "laptop"}),  # Should require confirmation
        ("DELETE", {"object": "file"}),  # Should be forbidden
    ]
    
    print("Processing test actions:")
    for action, context in test_actions:
        processed_action, status = ac.process_action(action, context, timeout=2.0)
        print(f"  {action}: {status}")
        
        # Handle any pending interventions automatically for demo
        pending = ac.get_pending_interventions()
        for intervention in pending:
            if action == "MOVE_EXPENSIVE":
                # Approve but modify
                safer_action = {"type": "MOVE_CAREFUL", "object": context["object"]}
                ac.submit_user_response(intervention.action_id, False, safer_action, "Use careful handling")
            elif action == "DELETE":
                # Reject dangerous action
                ac.submit_user_response(intervention.action_id, False, None, "Forbidden action")
            else:
                # Approve normal actions
                ac.submit_user_response(intervention.action_id, True, None, "Approved")
    
    # Show statistics
    stats = ac.get_action_statistics()
    print(f"✓ Action statistics: {stats['total_actions']} total, {stats['intervention_rate']:.1%} intervention rate")
    
    return ac


def test_configuration_override(preference_manager):
    """Test configuration override functionality"""
    print("\n=== Testing Configuration Override ===")
    
    from wrapper_api import ConfigOverride
    
    co = ConfigOverride()
    
    # Set some manual overrides
    co.set_override('ENVIRONMENT.MAX_EPISODE_STEPS', 1500)
    co.set_override('RL.PPO.lr', 0.0002)
    
    # Apply preferences to create configuration
    config = co.apply_preferences(preference_manager)
    
    print("✓ Configuration generated with preferences applied")
    print(f"✓ Manual overrides: {len(co.overrides)}")
    
    # Show some config values
    if 'ENVIRONMENT' in config:
        print(f"✓ Episode steps: {config.get('ENVIRONMENT', {}).get('MAX_EPISODE_STEPS', 'default')}")
    
    return co


def test_save_load_preferences(preference_manager):
    """Test saving and loading preferences"""
    print("\n=== Testing Save/Load Preferences ===")
    
    import tempfile
    
    # Create temp file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Save preferences
        preference_manager.save_to_file(temp_file)
        print(f"✓ Preferences saved to {temp_file}")
        
        # Load into new preference manager
        from wrapper_api import PreferenceManager
        pm2 = PreferenceManager()
        pm2.load_from_file(temp_file)
        
        print(f"✓ Preferences loaded: {len(pm2.object_preferences)} objects, {len(pm2.room_preferences)} rooms")
        
        # Verify they match
        original_dict = preference_manager.to_dict()
        loaded_dict = pm2.to_dict()
        
        match = (len(original_dict['object_preferences']) == len(loaded_dict['object_preferences']) and
                len(original_dict['room_preferences']) == len(loaded_dict['room_preferences']))
        
        print(f"✓ Preferences match after save/load: {match}")
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_advanced_features():
    """Test advanced wrapper features"""
    print("\n=== Testing Advanced Features ===")
    
    from wrapper_api import PreferenceManager
    from wrapper_api.preference_manager import ObjectPriority
    
    pm = PreferenceManager()
    pm.create_example_preferences()
    
    # Test priority queries
    priorities = []
    for obj_type in ["mug", "book", "clothes", "unknown_object"]:
        priority = pm.get_object_priority(obj_type)
        priorities.append(f"{obj_type}: {priority}")
    
    print("✓ Object priority queries:")
    for p in priorities:
        print(f"  {p}")
    
    # Test action permissions
    test_actions = ["MOVE_FORWARD", "GRAB_FRAGILE_ITEMS", "DELETE", "TURN_LEFT"]
    permissions = []
    for action in test_actions:
        allowed = pm.is_action_allowed(action)
        requires_confirm = pm.requires_confirmation(action)
        permissions.append(f"{action}: allowed={allowed}, confirm={requires_confirm}")
    
    print("✓ Action permission checks:")
    for p in permissions:
        print(f"  {p}")


def main():
    """Run all tests"""
    print("Housekeep Wrapper API Test Suite")
    print("=" * 50)
    
    try:
        # Test preference management
        pm = test_preference_management()
        
        # Test action controller
        ac = test_action_controller(pm)
        
        # Test configuration override
        co = test_configuration_override(pm)
        
        # Test save/load
        test_save_load_preferences(pm)
        
        # Test advanced features
        test_advanced_features()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        
        print("\nSummary:")
        print(f"  Preference Manager: {len(pm.object_preferences)} objects, {len(pm.room_preferences)} rooms")
        print(f"  Action Controller: {ac.get_action_statistics()['total_actions']} actions processed")
        print(f"  Config Override: {len(co.overrides)} manual overrides")
        print(f"  Global Preferences: {len(pm.global_preferences)} settings")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())