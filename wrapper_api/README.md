# Housekeep Wrapper API

A high-level wrapper API for the Housekeep agent that enables user preference integration and real-time control over agent behavior in household rearrangement tasks.

## Overview

The Housekeep Wrapper API provides a user-friendly interface to:
- Define and manage user preferences for object placement and agent behavior
- Control agent actions with real-time intervention capabilities
- Apply safety constraints and custom configurations
- Monitor agent performance and decision-making processes

## Key Components

### 1. PreferenceManager
Manages user preferences for:
- **Object Preferences**: Priority levels, preferred rooms, and receptacles for different object types
- **Room Preferences**: Room-specific constraints and object limits
- **Safety Constraints**: Distance limits, forbidden actions, confirmation requirements
- **Global Preferences**: Exploration aggressiveness, safety vs efficiency balance, intervention frequency

### 2. PolicyWrapper
Integrates user preferences into the agent's decision-making process by:
- Wrapping the hierarchical policy (HiePolicy) with preference-aware components
- Modifying object ranking and scoring based on user priorities
- Adjusting exploration behavior according to user preferences
- Implementing safety constraint enforcement

### 3. ConfigOverride
Provides dynamic configuration management:
- Applies user preferences to base configuration files
- Supports runtime configuration modifications
- Generates custom configuration files for different scenarios

### 4. ActionController
Handles real-time action intervention:
- Intercepts agent actions before execution
- Requests user approval for critical actions
- Applies safety constraints and filters forbidden actions
- Maintains action history and statistics

### 5. HousekeepWrapper
Main interface that ties all components together:
- Simplifies setup and configuration
- Provides high-level methods for common operations
- Manages episode execution with preference integration

## Installation and Setup

1. Ensure you have the base Housekeep repository set up with all dependencies
2. The wrapper API is located in the `wrapper_api/` directory
3. No additional dependencies are required beyond the base Housekeep requirements

## Quick Start

```python
from wrapper_api import HousekeepWrapper

# Create wrapper with example preferences
wrapper = HousekeepWrapper.create_with_example_setup()

# Add custom object preferences
wrapper.add_object_preference('mug', 'high', 'kitchen', 'kitchen_counter')
wrapper.add_object_preference('book', 'medium', 'living_room', 'bookshelf')

# Set global preferences
wrapper.set_global_preference('exploration_aggressiveness', 0.4)
wrapper.set_global_preference('user_intervention_frequency', 0.1)

# Initialize the agent
wrapper.initialize_agent()

# Run an episode
results = wrapper.run_episode('scene_name', max_steps=1000)
```

## User Preference Types

### Object Preferences
```python
wrapper.add_object_preference(
    object_type='wine_glass',
    priority='critical',           # critical, high, medium, low, ignore
    preferred_room='kitchen',      # kitchen, living_room, bedroom, etc.
    preferred_receptacle='cabinet' # specific receptacle name
)
```

### Global Preferences
```python
# Exploration behavior (0.0 = conservative, 1.0 = aggressive)
wrapper.set_global_preference('exploration_aggressiveness', 0.6)

# Safety vs efficiency (0.0 = maximum safety, 1.0 = maximum efficiency)
wrapper.set_global_preference('efficiency_vs_safety', 0.3)

# User intervention frequency (0.0 = never, 1.0 = every action)
wrapper.set_global_preference('user_intervention_frequency', 0.15)
```

### Safety Constraints
```python
from wrapper_api.preference_manager import SafetyConstraint

safety = SafetyConstraint(
    max_distance_from_start=8.0,
    forbidden_actions=['DELETE_PERMANENT', 'MOVE_FURNITURE'],
    require_confirmation=['MOVE_EXPENSIVE', 'HANDLE_FRAGILE']
)
wrapper.preference_manager.set_safety_constraints(safety)
```

## Real-time Intervention

The wrapper API supports real-time intervention in agent actions:

```python
# Get pending intervention requests
interventions = wrapper.get_intervention_requests()

for intervention in interventions:
    print(f"Action: {intervention.action_type}")
    print(f"Context: {intervention.context}")
    
    # Respond to intervention
    if intervention.action_type == 'GRAB_FRAGILE':
        # Reject risky action
        wrapper.respond_to_intervention(
            intervention.action_id, 
            approved=False, 
            reason="Too risky"
        )
    else:
        # Approve action
        wrapper.respond_to_intervention(
            intervention.action_id, 
            approved=True
        )
```

## Configuration Management

### Dynamic Configuration Override
```python
from wrapper_api import ConfigOverride

config_override = ConfigOverride('base_config.yaml')

# Set manual overrides
config_override.set_override('ENVIRONMENT.MAX_EPISODE_STEPS', 2000)
config_override.set_override('RL.PPO.lr', 0.0001)

# Apply preferences
final_config = config_override.apply_preferences(preference_manager)

# Save custom configuration
config_override.save_config('custom_config.yaml', final_config)
```

## Monitoring and Statistics

```python
# Get agent status
status = wrapper.get_agent_status()
print(f"Running: {status['is_running']}")
print(f"Episodes: {status['current_episode']}")
print(f"Interventions: {status['pending_interventions']}")

# Get preference summary
prefs = wrapper.get_preference_summary()
print(f"Object preferences: {prefs['object_preferences']}")
print(f"Room preferences: {prefs['room_preferences']}")

# Get action statistics
action_controller = wrapper.action_controller
stats = action_controller.get_action_statistics()
print(f"Total actions: {stats['total_actions']}")
print(f"Intervention rate: {stats['intervention_rate']:.2%}")
```

## Saving and Loading Preferences

```python
# Save preferences to file
wrapper.save_preferences('my_preferences.json')

# Load preferences from file
wrapper.load_preferences('my_preferences.json')

# Export complete episode data
wrapper.export_episode_data('output_directory/')
```

## Integration Points with Original Housekeep

The wrapper API integrates with the original Housekeep system at these key points:

1. **Policy Level**: `cos_eor/policy/hie_policy.py` - Hierarchical policy wrapper
2. **Ranking System**: `cos_eor/policy/rank.py` - Object scoring modification
3. **Environment**: `cos_eor/env/env.py` - Action interception
4. **Configuration**: `cos_eor/configs/` - Dynamic config generation
5. **Trainer**: `cos_eor/trainer/hie_policy_runner.py` - Episode execution

## Architecture Overview

```
HousekeepWrapper
├── PreferenceManager
│   ├── Object Preferences
│   ├── Room Preferences
│   ├── Safety Constraints
│   └── Global Preferences
├── PolicyWrapper
│   ├── PreferenceAwareRankModule
│   ├── Action Selection Override
│   └── Exploration Control
├── ConfigOverride
│   ├── Preference Application
│   ├── Manual Overrides
│   └── Config Generation
└── ActionController
    ├── Action Interception
    ├── User Intervention
    ├── Safety Enforcement
    └── Action History
```

## Examples

See the `examples/` directory for comprehensive usage examples:
- `basic_usage.py` - Complete walkthrough of all features
- Advanced preference setups
- Intervention handling
- Configuration management
- Saving/loading preferences

## API Reference

### HousekeepWrapper Methods

- `add_object_preference(object_type, priority, preferred_room, preferred_receptacle)`
- `set_global_preference(key, value)`
- `initialize_agent(config_overrides=None)`
- `run_episode(scene_name, max_steps=None)`
- `get_intervention_requests()`
- `respond_to_intervention(action_id, approved, modified_action, reason)`
- `get_agent_status()`
- `save_preferences(filepath)`
- `load_preferences(filepath)`

### PreferenceManager Methods

- `add_object_preference(preference)`
- `add_room_preference(preference)`
- `set_safety_constraints(constraints)`
- `get_object_priority(object_type)`
- `is_action_allowed(action)`
- `requires_confirmation(action)`

### ActionController Methods

- `process_action(action, context, timeout)`
- `submit_user_response(action_id, approved, modified_action, reason)`
- `get_action_statistics()`
- `get_pending_interventions()`

## Best Practices

1. **Start Simple**: Begin with basic object preferences and gradually add complexity
2. **Safety First**: Always define safety constraints before running episodes
3. **Monitor Interventions**: Check intervention statistics to optimize frequency settings
4. **Save Configurations**: Save working preference sets for reuse
5. **Test Thoroughly**: Use the examples to understand behavior before deployment

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Configuration Conflicts**: Check for conflicting preference settings
3. **Intervention Timeouts**: Adjust timeout values for slower response times
4. **Missing Dependencies**: Verify all Housekeep dependencies are installed

### Debug Mode

Enable detailed logging by setting debug preferences:
```python
wrapper.set_global_preference('debug_mode', True)
wrapper.set_global_preference('log_interventions', True)
```

## Contributing

To extend the wrapper API:
1. Follow the existing pattern for new preference types
2. Add corresponding configuration mappings
3. Update the HousekeepWrapper interface
4. Add examples and documentation
5. Include appropriate error handling

## License

This wrapper API follows the same license as the base Housekeep repository.