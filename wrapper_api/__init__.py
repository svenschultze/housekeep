"""
Wrapper API for Housekeep Agent Control with User Preferences

This module provides a high-level API for controlling the Housekeep agent
with user-defined preferences and constraints.
"""

# Use lazy imports to avoid heavy dependencies when not needed
from .preference_manager import PreferenceManager
from .config_override import ConfigOverride
from .action_controller import ActionController

# These will be imported only when explicitly used
def __getattr__(name):
    if name == 'PolicyWrapper':
        from .policy_wrapper import PolicyWrapper
        return PolicyWrapper
    elif name == 'HousekeepWrapper':
        from .housekeep_wrapper import HousekeepWrapper
        return HousekeepWrapper
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'PreferenceManager',
    'PolicyWrapper', 
    'ConfigOverride',
    'ActionController',
    'HousekeepWrapper'
]