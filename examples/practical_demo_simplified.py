#!/usr/bin/env python3
"""
Practical Usage Demonstration of Housekeep Wrapper API (Simplified)

This script shows realistic scenarios without requiring full Housekeep dependencies.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def scenario_family_home():
    """
    Scenario: Family home with specific preferences
    """
    print("🏠 Family Home Customization Scenario")
    print("=" * 50)
    
    from wrapper_api import PreferenceManager, ActionController, ConfigOverride
    from wrapper_api.preference_manager import ObjectPreference, RoomPreference, SafetyConstraint
    from wrapper_api.preference_manager import ObjectPriority, RoomType
    
    # Create preference manager
    pm = PreferenceManager()
    
    print("Setting family-specific preferences...")
    
    # Kitchen items - high priority, safety first
    pm.add_object_preference(ObjectPreference('knife', ObjectPriority.CRITICAL, RoomType.KITCHEN, 'knife_block'))
    pm.add_object_preference(ObjectPreference('glass', ObjectPriority.HIGH, RoomType.KITCHEN, 'cabinet'))
    pm.add_object_preference(ObjectPreference('plate', ObjectPriority.HIGH, RoomType.KITCHEN, 'dishwasher'))
    
    # Living room items
    pm.add_object_preference(ObjectPreference('remote_control', ObjectPriority.MEDIUM, RoomType.LIVING_ROOM, 'coffee_table'))
    pm.add_object_preference(ObjectPreference('book', ObjectPriority.MEDIUM, RoomType.LIVING_ROOM, 'bookshelf'))
    
    # Children's items - lower priority
    pm.add_object_preference(ObjectPreference('toy', ObjectPriority.LOW, RoomType.LIVING_ROOM, 'toy_box'))
    pm.add_object_preference(ObjectPreference('stuffed_animal', ObjectPriority.LOW, RoomType.BEDROOM, 'toy_chest'))
    
    # Valuable items - critical handling
    pm.add_object_preference(ObjectPreference('vase', ObjectPriority.CRITICAL, RoomType.LIVING_ROOM, 'display_cabinet'))
    pm.add_object_preference(ObjectPreference('laptop', ObjectPriority.CRITICAL, RoomType.OFFICE, 'desk'))
    
    # Safety constraints for family home
    pm.set_safety_constraints(SafetyConstraint(
        max_distance_from_start=5.0,
        forbidden_actions=['DELETE_FILES', 'MOVE_FURNITURE'],
        require_confirmation=['MOVE_EXPENSIVE', 'HANDLE_SHARP']
    ))
    
    # Family-friendly global settings
    pm.set_global_preference('exploration_aggressiveness', 0.3)  # Conservative
    pm.set_global_preference('efficiency_vs_safety', 0.2)        # Safety first
    pm.set_global_preference('user_intervention_frequency', 0.15)  # Regular check-ins
    
    print(f"✓ Family preferences configured: {len(pm.object_preferences)} objects")
    
    return pm


def scenario_office_space():
    """
    Scenario: Professional office space
    """
    print("\n💼 Professional Office Customization Scenario")
    print("=" * 50)
    
    from wrapper_api import PreferenceManager
    from wrapper_api.preference_manager import ObjectPreference, SafetyConstraint
    from wrapper_api.preference_manager import ObjectPriority, RoomType
    
    pm = PreferenceManager()
    
    print("Setting professional office preferences...")
    
    # Office equipment - critical priority
    pm.add_object_preference(ObjectPreference('computer', ObjectPriority.CRITICAL, RoomType.OFFICE, 'desk'))
    pm.add_object_preference(ObjectPreference('monitor', ObjectPriority.CRITICAL, RoomType.OFFICE, 'monitor_stand'))
    pm.add_object_preference(ObjectPreference('hard_drive', ObjectPriority.CRITICAL, RoomType.OFFICE, 'secure_drawer'))
    
    # Office supplies
    pm.add_object_preference(ObjectPreference('pen', ObjectPriority.MEDIUM, RoomType.OFFICE, 'pen_holder'))
    pm.add_object_preference(ObjectPreference('folder', ObjectPriority.HIGH, RoomType.OFFICE, 'filing_cabinet'))
    pm.add_object_preference(ObjectPreference('projector_remote', ObjectPriority.HIGH, RoomType.OFFICE, 'projector_table'))
    
    # Break area
    pm.add_object_preference(ObjectPreference('coffee_cup', ObjectPriority.LOW, RoomType.KITCHEN, 'dishwasher'))
    
    # Professional constraints
    pm.set_safety_constraints(SafetyConstraint(
        max_distance_from_start=10.0,
        forbidden_actions=['ACCESS_PERSONAL_FILES'],
        require_confirmation=['MOVE_EXPENSIVE', 'SHUTDOWN_COMPUTER']
    ))
    
    # Professional efficiency settings
    pm.set_global_preference('exploration_aggressiveness', 0.7)  # Efficient
    pm.set_global_preference('efficiency_vs_safety', 0.8)        # Efficiency focused
    pm.set_global_preference('user_intervention_frequency', 0.05)  # Minimal interruption
    
    print(f"✓ Office preferences configured: {len(pm.object_preferences)} objects")
    
    return pm


def demonstrate_intervention_handling(preference_manager, scenario_name):
    """Demonstrate how interventions work in practice"""
    print(f"\n🤖 Agent Intervention Demo - {scenario_name}")
    print("=" * 50)
    
    from wrapper_api import ActionController
    from wrapper_api.action_controller import ActionStatus
    
    action_controller = ActionController(preference_manager)
    
    # Simulate realistic agent actions
    test_scenarios = [
        {
            'action': {'type': 'GRAB_RELEASE', 'object': 'knife'},
            'context': {'current_room': 'kitchen', 'object_type': 'knife'},
            'description': 'Agent wants to move a kitchen knife'
        },
        {
            'action': {'type': 'MOVE_FORWARD', 'distance': 2.0},
            'context': {'current_room': 'living_room', 'distance': 2.0},
            'description': 'Agent wants to move across living room'
        },
        {
            'action': {'type': 'MOVE_EXPENSIVE', 'object': 'laptop'},
            'context': {'current_room': 'office', 'object_type': 'laptop'},
            'description': 'Agent wants to move expensive laptop'
        },
        {
            'action': {'type': 'GRAB_RELEASE', 'object': 'toy'},
            'context': {'current_room': 'living_room', 'object_type': 'toy'},
            'description': 'Agent wants to move a toy'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario['description']}")
        
        # Process the action
        processed_action, status = action_controller.process_action(
            scenario['action'], 
            scenario['context'], 
            timeout=2.0
        )
        
        print(f"  Action: {scenario['action']['type']}")
        print(f"  Status: {status}")
        
        # Handle any interventions
        pending = action_controller.get_pending_interventions()
        for intervention in pending:
            print(f"  → Intervention requested: {intervention.action_type}")
            
            # Simulate intelligent user responses
            object_type = scenario['context'].get('object_type', '')
            action_type = scenario['action']['type']
            
            if object_type in ['knife', 'laptop', 'vase'] or action_type == 'MOVE_EXPENSIVE':
                # Critical items - require careful handling
                modified_action = {'type': 'CAREFUL_' + action_type, 'object': object_type}
                action_controller.submit_user_response(
                    intervention.action_id, 
                    False,  # Don't approve as-is
                    modified_action,
                    f"Use careful handling for {object_type}"
                )
                print(f"  → Modified to use careful handling")
            else:
                # Normal actions - approve
                action_controller.submit_user_response(
                    intervention.action_id, 
                    True, 
                    None, 
                    "Action approved"
                )
                print(f"  → Approved action")
    
    # Show final statistics
    stats = action_controller.get_action_statistics()
    print(f"\n📊 Statistics for {scenario_name}:")
    print(f"  Total actions: {stats['total_actions']}")
    print(f"  Interventions: {stats['intercepted_actions']}")
    print(f"  Intervention rate: {stats['intervention_rate']:.1%}")
    print(f"  Modifications: {stats['modified_actions']}")
    
    return stats


def demonstrate_configuration_override(preference_manager, scenario_name):
    """Show how preferences translate to configuration"""
    print(f"\n⚙️ Configuration Override Demo - {scenario_name}")
    print("=" * 50)
    
    from wrapper_api import ConfigOverride
    
    co = ConfigOverride()
    
    # Add some manual overrides for this scenario
    if "Family" in scenario_name:
        co.set_override('ENVIRONMENT.MAX_EPISODE_STEPS', 1200)  # Longer episodes for family
        co.set_override('RL.COLLISION_REWARD', -0.15)  # Higher collision penalty
    else:
        co.set_override('ENVIRONMENT.MAX_EPISODE_STEPS', 800)   # Shorter episodes for office
        co.set_override('RL.COLLISION_REWARD', -0.05)  # Lower collision penalty
    
    # Apply preferences to generate configuration
    config = co.apply_preferences(preference_manager)
    
    print(f"Configuration generated for {scenario_name}:")
    
    # Show key configuration values
    if 'ENVIRONMENT' in config:
        env_config = config['ENVIRONMENT']
        print(f"  Max episode steps: {env_config.get('MAX_EPISODE_STEPS', 'default')}")
    
    if 'RL' in config:
        rl_config = config['RL']
        print(f"  Collision reward: {rl_config.get('COLLISION_REWARD', 'default')}")
        
        if 'POLICY' in rl_config:
            policy_config = rl_config['POLICY']
            print(f"  Exploration max steps: {policy_config.get('explore', {}).get('max_steps', 'default')}")
            print(f"  Intervention frequency: {policy_config.get('intervention_frequency', 'default')}")
    
    print(f"  Manual overrides: {len(co.overrides)}")
    
    # Save configuration for reuse
    config_dir = '/tmp/housekeep_demo'
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, f"{scenario_name.lower().replace(' ', '_')}_config.yaml")
    co.save_config(config_file, config)
    print(f"  Saved to: {config_file}")
    
    return config_file


def demonstrate_preference_analysis(preference_manager, scenario_name):
    """Analyze and display preference patterns"""
    print(f"\n📊 Preference Analysis - {scenario_name}")
    print("=" * 50)
    
    # Analyze object priorities
    priority_counts = {}
    room_assignments = {}
    
    for obj_type, pref in preference_manager.object_preferences.items():
        priority = pref.priority.name
        room = pref.preferred_room.value if pref.preferred_room else 'any'
        
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        room_assignments[room] = room_assignments.get(room, 0) + 1
    
    print("Object Priority Distribution:")
    for priority, count in sorted(priority_counts.items()):
        print(f"  {priority}: {count} objects")
    
    print("\nRoom Assignment Distribution:")
    for room, count in sorted(room_assignments.items()):
        print(f"  {room}: {count} objects")
    
    # Show safety settings
    safety = preference_manager.safety_constraints
    print(f"\nSafety Configuration:")
    print(f"  Max distance: {safety.max_distance_from_start}m")
    print(f"  Forbidden actions: {len(safety.forbidden_actions or [])}")
    print(f"  Require confirmation: {len(safety.require_confirmation or [])}")
    
    # Show global preferences
    global_prefs = preference_manager.global_preferences
    print(f"\nGlobal Preferences:")
    for key, value in global_prefs.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1%}" if value <= 1.0 else f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")


def main():
    """Run the practical demonstration"""
    print("Housekeep Wrapper API - Practical Usage Demonstration")
    print("=" * 70)
    print("Demonstrating real-world scenarios for customizing agent behavior")
    print()
    
    try:
        # Scenario 1: Family home
        family_prefs = scenario_family_home()
        family_stats = demonstrate_intervention_handling(family_prefs, "Family Home")
        family_config = demonstrate_configuration_override(family_prefs, "Family Home")
        demonstrate_preference_analysis(family_prefs, "Family Home")
        
        # Scenario 2: Office space
        office_prefs = scenario_office_space()
        office_stats = demonstrate_intervention_handling(office_prefs, "Office Space")
        office_config = demonstrate_configuration_override(office_prefs, "Office Space")
        demonstrate_preference_analysis(office_prefs, "Office Space")
        
        # Comparison
        print(f"\n🔄 Scenario Comparison")
        print("=" * 50)
        print(f"Family Home vs Office Space:")
        print(f"  Objects configured: {len(family_prefs.object_preferences)} vs {len(office_prefs.object_preferences)}")
        print(f"  Intervention rates: {family_stats['intervention_rate']:.1%} vs {office_stats['intervention_rate']:.1%}")
        print(f"  Safety focus: High vs Medium")
        print(f"  Exploration: Conservative vs Aggressive")
        
        # Save preference profiles
        pref_dir = '/tmp/housekeep_demo'
        os.makedirs(pref_dir, exist_ok=True)
        
        family_pref_file = os.path.join(pref_dir, 'family_preferences.json')
        office_pref_file = os.path.join(pref_dir, 'office_preferences.json')
        
        family_prefs.save_to_file(family_pref_file)
        office_prefs.save_to_file(office_pref_file)
        
        print(f"\n🎉 Demonstration Complete!")
        print("=" * 50)
        print("Key Features Demonstrated:")
        print("✓ Scenario-specific object and room preferences")
        print("✓ Safety constraints and intervention handling")
        print("✓ Dynamic configuration generation")
        print("✓ Real-time action processing and modification")
        print("✓ Preference analysis and comparison")
        print("✓ Persistent preference profiles")
        
        print(f"\nGenerated Files:")
        print(f"• Family preferences: {family_pref_file}")
        print(f"• Office preferences: {office_pref_file}")
        print(f"• Family config: {family_config}")
        print(f"• Office config: {office_config}")
        
        print(f"\nNext Steps:")
        print("• Load these preference files in your Housekeep setup")
        print("• Customize further based on specific needs")
        print("• Use the configurations to run episodes with preferred behavior")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())