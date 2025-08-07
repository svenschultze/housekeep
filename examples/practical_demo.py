#!/usr/bin/env python3
"""
Practical Usage Demonstration of Housekeep Wrapper API

This script shows a realistic scenario of how someone would use the wrapper API
to customize the Housekeep agent behavior for their specific needs.
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
    - Kitchen safety is paramount
    - Children's toys have lower priority
    - Valuable items need careful handling
    - Conservative exploration to avoid accidents
    """
    print("🏠 Family Home Customization Scenario")
    print("=" * 50)
    
    from wrapper_api import HousekeepWrapper
    
    # Create wrapper
    wrapper = HousekeepWrapper()
    
    # Family-specific object preferences
    print("Setting family-specific preferences...")
    
    # Kitchen items - high priority, safety first
    wrapper.add_object_preference('knife', 'critical', 'kitchen', 'knife_block')
    wrapper.add_object_preference('glass', 'high', 'kitchen', 'cabinet')
    wrapper.add_object_preference('plate', 'high', 'kitchen', 'dishwasher')
    wrapper.add_object_preference('mug', 'medium', 'kitchen', 'mug_rack')
    
    # Living room items
    wrapper.add_object_preference('remote_control', 'medium', 'living_room', 'coffee_table')
    wrapper.add_object_preference('book', 'medium', 'living_room', 'bookshelf')
    wrapper.add_object_preference('magazine', 'low', 'living_room', 'magazine_rack')
    
    # Children's items - lower priority but specific places
    wrapper.add_object_preference('toy', 'low', 'living_room', 'toy_box')
    wrapper.add_object_preference('stuffed_animal', 'low', 'bedroom', 'toy_chest')
    wrapper.add_object_preference('crayon', 'low', 'office', 'art_supplies_drawer')
    
    # Valuable/fragile items - critical handling
    wrapper.add_object_preference('vase', 'critical', 'living_room', 'display_cabinet')
    wrapper.add_object_preference('laptop', 'critical', 'office', 'desk')
    wrapper.add_object_preference('tablet', 'high', 'living_room', 'charging_station')
    
    # Global family-friendly settings
    wrapper.set_global_preference('exploration_aggressiveness', 0.3)  # Conservative
    wrapper.set_global_preference('efficiency_vs_safety', 0.2)        # Safety first
    wrapper.set_global_preference('user_intervention_frequency', 0.15)  # Regular check-ins
    
    print("✓ Family preferences configured")
    return wrapper


def scenario_office_space():
    """
    Scenario: Professional office space
    - Efficiency is important
    - Expensive equipment needs care
    - Organized workspace priority
    """
    print("\n💼 Professional Office Customization Scenario")
    print("=" * 50)
    
    from wrapper_api import HousekeepWrapper
    
    wrapper = HousekeepWrapper()
    
    print("Setting professional office preferences...")
    
    # Office equipment - critical priority
    wrapper.add_object_preference('computer', 'critical', 'office', 'desk')
    wrapper.add_object_preference('monitor', 'critical', 'office', 'monitor_stand')
    wrapper.add_object_preference('printer', 'high', 'office', 'printer_table')
    wrapper.add_object_preference('hard_drive', 'critical', 'office', 'secure_drawer')
    
    # Office supplies - organized placement
    wrapper.add_object_preference('pen', 'medium', 'office', 'pen_holder')
    wrapper.add_object_preference('paper', 'medium', 'office', 'paper_tray')
    wrapper.add_object_preference('stapler', 'medium', 'office', 'desk_organizer')
    wrapper.add_object_preference('folder', 'high', 'office', 'filing_cabinet')
    
    # Meeting room items
    wrapper.add_object_preference('whiteboard_marker', 'medium', 'office', 'marker_tray')
    wrapper.add_object_preference('projector_remote', 'high', 'office', 'projector_table')
    
    # Break area
    wrapper.add_object_preference('coffee_cup', 'low', 'kitchen', 'dishwasher')
    wrapper.add_object_preference('water_bottle', 'low', 'kitchen', 'counter')
    
    # Professional efficiency settings
    wrapper.set_global_preference('exploration_aggressiveness', 0.7)  # Efficient
    wrapper.set_global_preference('efficiency_vs_safety', 0.8)        # Efficiency focused
    wrapper.set_global_preference('user_intervention_frequency', 0.05)  # Minimal interruption
    
    print("✓ Office preferences configured")
    return wrapper


def demonstrate_intervention_handling(wrapper, scenario_name):
    """Demonstrate how interventions work in practice"""
    print(f"\n🤖 Agent Intervention Demo - {scenario_name}")
    print("=" * 50)
    
    # Simulate some realistic actions the agent might take
    test_scenarios = [
        {
            'action': 'GRAB_RELEASE',
            'context': {'object_type': 'knife', 'current_room': 'kitchen'},
            'description': 'Agent wants to move a kitchen knife'
        },
        {
            'action': 'MOVE_FORWARD', 
            'context': {'distance': 2.0, 'current_room': 'living_room'},
            'description': 'Agent wants to move across living room'
        },
        {
            'action': 'GRAB_RELEASE',
            'context': {'object_type': 'laptop', 'current_room': 'office'},
            'description': 'Agent wants to move expensive laptop'
        },
        {
            'action': 'GRAB_RELEASE',
            'context': {'object_type': 'toy', 'current_room': 'living_room'},
            'description': 'Agent wants to move a toy'
        }
    ]
    
    action_controller = wrapper.action_controller
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario['description']}")
        
        # Process the action
        processed_action, status = action_controller.process_action(
            scenario['action'], 
            scenario['context'], 
            timeout=3.0
        )
        
        print(f"  Action: {scenario['action']}")
        print(f"  Status: {status}")
        
        # Handle any interventions
        pending = action_controller.get_pending_interventions()
        for intervention in pending:
            print(f"  → Intervention requested: {intervention.action_type}")
            
            # Simulate intelligent user responses based on context
            object_type = scenario['context'].get('object_type', '')
            
            if object_type in ['knife', 'laptop', 'vase']:
                # Critical items - require careful handling
                action_controller.submit_user_response(
                    intervention.action_id, 
                    False,  # Don't approve as-is
                    {'type': 'CAREFUL_GRAB_RELEASE', 'object': object_type},
                    f"Use careful handling for {object_type}"
                )
                print(f"  → Modified to use careful handling")
            elif scenario['action'] == 'MOVE_FORWARD':
                # Normal movement - approve
                action_controller.submit_user_response(
                    intervention.action_id, 
                    True, 
                    None, 
                    "Movement approved"
                )
                print(f"  → Approved movement")
            else:
                # Other actions - approve
                action_controller.submit_user_response(
                    intervention.action_id, 
                    True, 
                    None, 
                    "Action approved"
                )
                print(f"  → Approved action")
    
    # Show final statistics
    stats = action_controller.get_action_statistics()
    print(f"\n📊 Final Statistics:")
    print(f"  Total actions processed: {stats['total_actions']}")
    print(f"  Intervention rate: {stats['intervention_rate']:.1%}")
    print(f"  Approval rate: {stats['approval_rate']:.1%}")
    print(f"  Modification rate: {stats['modification_rate']:.1%}")


def demonstrate_preference_persistence():
    """Show how to save and reuse preference configurations"""
    print(f"\n💾 Preference Persistence Demo")
    print("=" * 50)
    
    # Create some custom preferences
    from wrapper_api import HousekeepWrapper
    wrapper = HousekeepWrapper()
    
    # Add some unique preferences
    wrapper.add_object_preference('wine_glass', 'critical', 'kitchen', 'wine_cabinet')
    wrapper.add_object_preference('artwork', 'critical', 'living_room', 'wall_mount')
    wrapper.add_object_preference('tool', 'medium', 'office', 'toolbox')
    
    wrapper.set_global_preference('exploration_aggressiveness', 0.25)
    wrapper.set_global_preference('user_intervention_frequency', 0.2)
    
    # Save to files
    os.makedirs('/tmp/housekeep_demo', exist_ok=True)
    
    family_prefs = '/tmp/housekeep_demo/family_preferences.json'
    wrapper.save_preferences(family_prefs)
    print(f"✓ Saved preferences to {family_prefs}")
    
    # Load into new wrapper to verify
    new_wrapper = HousekeepWrapper()
    new_wrapper.load_preferences(family_prefs)
    
    loaded_summary = new_wrapper.get_preference_summary()
    print(f"✓ Loaded preferences: {loaded_summary['object_preferences']} objects")
    
    # Show they can be reused
    print("✓ Preferences can be saved and reused across sessions")
    
    return family_prefs


def main():
    """Run the practical demonstration"""
    print("Housekeep Wrapper API - Practical Usage Demonstration")
    print("=" * 70)
    print("This demo shows real-world scenarios for customizing agent behavior")
    print()
    
    try:
        # Scenario 1: Family home
        family_wrapper = scenario_family_home()
        demonstrate_intervention_handling(family_wrapper, "Family Home")
        
        # Scenario 2: Office space
        office_wrapper = scenario_office_space()
        demonstrate_intervention_handling(office_wrapper, "Office Space")
        
        # Persistence demo
        pref_file = demonstrate_preference_persistence()
        
        print(f"\n🎉 Demonstration Complete!")
        print("=" * 50)
        print("Key takeaways:")
        print("• Different environments need different agent behaviors")
        print("• User preferences can be fine-tuned for specific needs")
        print("• Real-time intervention provides safety and control")
        print("• Preferences can be saved and reused")
        print("• The wrapper API makes customization simple and powerful")
        
        print(f"\nFiles created:")
        print(f"• {pref_file}")
        print("\nYou can now use these preference files to configure the agent!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())