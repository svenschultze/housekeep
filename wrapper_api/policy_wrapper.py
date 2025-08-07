"""
Policy Wrapper for User Preference Integration

Wraps the existing HiePolicy to inject user preferences into the decision-making process.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from collections import defaultdict

from cos_eor.policy.hie_policy import HiePolicy
from cos_eor.policy.rank import RankModule
from .preference_manager import PreferenceManager, ObjectPriority, RoomType


class PreferenceAwareRankModule:
    """
    Wraps the original rank module to incorporate user preferences into scoring.
    """
    
    def __init__(self, original_rank_module: RankModule, preference_manager: PreferenceManager):
        self.original_rank_module = original_rank_module
        self.preference_manager = preference_manager
    
    def __getattr__(self, name):
        """Delegate attribute access to the original rank module"""
        return getattr(self.original_rank_module, name)
    
    def score_objects(self, objects: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, float]:
        """
        Score objects incorporating user preferences.
        
        Args:
            objects: List of object information dictionaries
            context: Context information (room, current state, etc.)
            
        Returns:
            Dictionary mapping object IDs to preference-adjusted scores
        """
        # Get original scores
        original_scores = self.original_rank_module.score_objects(objects, context)
        
        # Apply user preference adjustments
        adjusted_scores = {}
        for obj_id, original_score in original_scores.items():
            obj_info = next((obj for obj in objects if obj.get('id') == obj_id), None)
            if not obj_info:
                adjusted_scores[obj_id] = original_score
                continue
            
            # Get user preference priority
            object_type = obj_info.get('type', obj_info.get('category', 'unknown'))
            priority = self.preference_manager.get_object_priority(object_type)
            
            # Adjust score based on priority
            priority_multiplier = self._get_priority_multiplier(priority)
            
            # Apply room preference bonus/penalty
            room_bonus = self._get_room_preference_bonus(obj_info, context)
            
            # Apply receptacle preference bonus
            receptacle_bonus = self._get_receptacle_preference_bonus(obj_info, context)
            
            # Calculate final adjusted score
            adjusted_score = original_score * priority_multiplier + room_bonus + receptacle_bonus
            adjusted_scores[obj_id] = max(0.0, adjusted_score)  # Ensure non-negative
        
        return adjusted_scores
    
    def _get_priority_multiplier(self, priority: ObjectPriority) -> float:
        """Get score multiplier based on object priority"""
        multipliers = {
            ObjectPriority.CRITICAL: 2.0,
            ObjectPriority.HIGH: 1.5,
            ObjectPriority.MEDIUM: 1.0,
            ObjectPriority.LOW: 0.5,
            ObjectPriority.IGNORE: 0.1
        }
        return multipliers.get(priority, 1.0)
    
    def _get_room_preference_bonus(self, obj_info: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Get bonus/penalty based on room preferences"""
        object_type = obj_info.get('type', obj_info.get('category', 'unknown'))
        preferred_room = self.preference_manager.get_preferred_room(object_type)
        
        if not preferred_room:
            return 0.0
        
        current_room = context.get('current_room', context.get('room'))
        if current_room and current_room.lower() == preferred_room.value:
            return 0.2  # Bonus for objects in their preferred room
        
        return 0.0
    
    def _get_receptacle_preference_bonus(self, obj_info: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Get bonus based on receptacle preferences"""
        object_type = obj_info.get('type', obj_info.get('category', 'unknown'))
        preferred_receptacle = self.preference_manager.get_preferred_receptacle(object_type)
        
        if not preferred_receptacle:
            return 0.0
        
        # Check if there's a matching receptacle available in context
        available_receptacles = context.get('available_receptacles', [])
        if preferred_receptacle in available_receptacles:
            return 0.15  # Bonus for having preferred receptacle available
        
        return 0.0


class PolicyWrapper:
    """
    Wraps the HiePolicy to integrate user preferences into agent decision-making.
    
    This wrapper intercepts key decision points and applies user preferences
    while maintaining compatibility with the existing policy interface.
    """
    
    def __init__(self, original_policy: HiePolicy, preference_manager: PreferenceManager):
        self.original_policy = original_policy
        self.preference_manager = preference_manager
        
        # Wrap the rank module with preference-aware version
        if hasattr(original_policy, 'rank_module'):
            self.original_policy.rank_module = PreferenceAwareRankModule(
                original_policy.rank_module, preference_manager
            )
        
        # Track user intervention state
        self.intervention_count = 0
        self.total_decisions = 0
        self.pending_confirmations = []
    
    def __getattr__(self, name):
        """Delegate attribute access to the original policy"""
        return getattr__(self.original_policy, name)
    
    def act(self, observations, rnn_hidden_states, prev_actions, masks, deterministic=False):
        """
        Main action selection method with user preference integration.
        """
        self.total_decisions += 1
        
        # Check if user intervention is needed
        if self._should_request_intervention():
            # Request user input (in a real implementation, this would be async)
            user_override = self._request_user_intervention(observations)
            if user_override:
                return user_override
        
        # Get original policy action
        original_action = self.original_policy.act(
            observations, rnn_hidden_states, prev_actions, masks, deterministic
        )
        
        # Apply safety constraints
        if self._is_action_safe(original_action, observations):
            return original_action
        else:
            # Find safer alternative or request user input
            return self._find_safe_alternative(original_action, observations)
    
    def select_next_object(self, observations, object_list: List[Dict[str, Any]]) -> Optional[str]:
        """
        Select next object to rearrange based on user preferences.
        
        Args:
            observations: Current environment observations
            object_list: List of available objects to rearrange
            
        Returns:
            Object ID of selected object or None
        """
        if not object_list:
            return None
        
        # Filter objects based on user preferences
        allowed_objects = []
        for obj in object_list:
            object_type = obj.get('type', obj.get('category', 'unknown'))
            priority = self.preference_manager.get_object_priority(object_type)
            
            # Skip objects marked as ignore
            if priority != ObjectPriority.IGNORE:
                allowed_objects.append(obj)
        
        if not allowed_objects:
            return None
        
        # Use the preference-aware ranking to select best object
        context = self._extract_context(observations)
        scores = self.original_policy.rank_module.score_objects(allowed_objects, context)
        
        # Select highest scoring allowed object
        best_object_id = max(scores.keys(), key=lambda k: scores[k])
        return best_object_id
    
    def should_explore(self, observations) -> bool:
        """
        Determine if agent should explore based on user preferences.
        """
        # Get original exploration decision
        original_decision = self.original_policy.explore_module.should_explore(observations)
        
        # Adjust based on user's exploration aggressiveness preference
        exploration_pref = self.preference_manager.global_preferences.get('exploration_aggressiveness', 0.5)
        
        # If exploration preference is low, be more conservative
        if exploration_pref < 0.3 and original_decision:
            # Check if exploration is really necessary
            return self._is_exploration_necessary(observations)
        
        # If exploration preference is high, be more aggressive
        elif exploration_pref > 0.7 and not original_decision:
            return self._should_explore_more(observations)
        
        return original_decision
    
    def _should_request_intervention(self) -> bool:
        """Determine if user intervention should be requested"""
        intervention_freq = self.preference_manager.global_preferences.get('user_intervention_frequency', 0.2)
        
        if intervention_freq == 0.0:
            return False
        
        # Request intervention based on frequency and decision importance
        return (self.total_decisions % int(1.0 / intervention_freq)) == 0
    
    def _request_user_intervention(self, observations) -> Optional[Any]:
        """
        Request user intervention (placeholder for actual implementation).
        
        In a real implementation, this would:
        1. Present current state to user
        2. Show available options
        3. Wait for user input
        4. Return user's choice
        """
        # Placeholder: return None to continue with original policy
        self.intervention_count += 1
        return None
    
    def _is_action_safe(self, action, observations) -> bool:
        """Check if action meets safety constraints"""
        # Extract action type from action tensor/dict
        action_name = self._extract_action_name(action)
        
        # Check forbidden actions
        if not self.preference_manager.is_action_allowed(action_name):
            return False
        
        # Check distance constraints
        max_distance = self.preference_manager.safety_constraints.max_distance_from_start
        if max_distance and self._get_distance_from_start(observations) > max_distance:
            return False
        
        return True
    
    def _find_safe_alternative(self, unsafe_action, observations):
        """Find a safe alternative to an unsafe action"""
        # For now, return STOP action as safe default
        # In a full implementation, this would find the closest safe action
        stop_action_id = 0  # Assuming STOP is action 0
        return stop_action_id
    
    def _extract_context(self, observations) -> Dict[str, Any]:
        """Extract context information from observations"""
        context = {}
        
        # Extract room information if available
        if 'room' in observations:
            context['current_room'] = observations['room']
        elif 'semantic' in observations:
            # Try to infer room from semantic segmentation
            context['current_room'] = self._infer_room_from_semantic(observations['semantic'])
        
        # Extract available receptacles
        if 'receptacles' in observations:
            context['available_receptacles'] = observations['receptacles']
        
        return context
    
    def _extract_action_name(self, action) -> str:
        """Extract action name from action tensor/dict"""
        # This is a simplified extraction - actual implementation would
        # depend on the action representation used by the environment
        if hasattr(action, 'item'):
            action_id = action.item()
        else:
            action_id = action
        
        action_names = ["STOP", "MOVE_FORWARD", "TURN_LEFT", "TURN_RIGHT", 
                       "LOOK_UP", "LOOK_DOWN", "GRAB_RELEASE"]
        
        if 0 <= action_id < len(action_names):
            return action_names[action_id]
        
        return "UNKNOWN"
    
    def _get_distance_from_start(self, observations) -> float:
        """Calculate distance from starting position"""
        # Placeholder implementation
        # Real implementation would track starting position and calculate distance
        return 0.0
    
    def _infer_room_from_semantic(self, semantic_obs) -> Optional[str]:
        """Infer current room from semantic observations"""
        # Placeholder - real implementation would analyze semantic segmentation
        return None
    
    def _is_exploration_necessary(self, observations) -> bool:
        """Check if exploration is necessary given current state"""
        # Conservative exploration check
        # Real implementation would check coverage, known objects, etc.
        return False
    
    def _should_explore_more(self, observations) -> bool:
        """Check if more aggressive exploration is warranted"""
        # Aggressive exploration check
        # Real implementation would check for unexplored areas, missing objects, etc.
        return True
    
    def get_preference_summary(self) -> Dict[str, Any]:
        """Get summary of preference application"""
        return {
            'total_decisions': self.total_decisions,
            'intervention_count': self.intervention_count,
            'intervention_rate': self.intervention_count / max(1, self.total_decisions),
            'object_preferences_count': len(self.preference_manager.object_preferences),
            'room_preferences_count': len(self.preference_manager.room_preferences),
            'active_constraints': bool(self.preference_manager.safety_constraints.forbidden_actions or 
                                     self.preference_manager.safety_constraints.require_confirmation)
        }