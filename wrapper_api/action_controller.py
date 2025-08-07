"""
Action Controller for User Intervention

Provides mechanisms for intercepting, modifying, and controlling agent actions
based on user preferences and real-time input.
"""

from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import time
from collections import deque
import threading
import queue

from .preference_manager import PreferenceManager


class ActionStatus(Enum):
    """Status of action processing"""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    PENDING = "pending"
    TIMEOUT = "timeout"


class ActionIntervention:
    """Represents a user intervention request"""
    
    def __init__(self, action_id: str, action_type: str, context: Dict[str, Any], 
                 timestamp: float, timeout: float = 30.0):
        self.action_id = action_id
        self.action_type = action_type
        self.context = context
        self.timestamp = timestamp
        self.timeout = timeout
        self.status = ActionStatus.PENDING
        self.user_response = None
        self.modified_action = None


class ActionController:
    """
    Controls agent actions with user intervention capabilities.
    
    This class provides mechanisms to:
    1. Intercept actions before execution
    2. Request user approval/modification
    3. Apply safety constraints
    4. Log action decisions
    """
    
    def __init__(self, preference_manager: PreferenceManager):
        self.preference_manager = preference_manager
        self.action_history = deque(maxlen=1000)
        self.pending_interventions = {}
        self.user_input_queue = queue.Queue()
        
        # Statistics
        self.total_actions = 0
        self.intercepted_actions = 0
        self.approved_actions = 0
        self.rejected_actions = 0
        self.modified_actions = 0
        
        # Callbacks for external integration
        self.intervention_callbacks: List[Callable[[ActionIntervention], None]] = []
        self.action_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
    
    def process_action(self, action: Union[str, int, Dict[str, Any]], 
                      context: Dict[str, Any], 
                      timeout: float = 30.0) -> tuple[Any, ActionStatus]:
        """
        Process an action with potential user intervention.
        
        Args:
            action: The action to process (can be string, int, or dict)
            context: Context information (observations, state, etc.)
            timeout: Timeout for user intervention in seconds
            
        Returns:
            Tuple of (processed_action, status)
        """
        self.total_actions += 1
        action_id = f"action_{self.total_actions}_{time.time()}"
        
        # Normalize action to standard format
        normalized_action = self._normalize_action(action)
        action_type = normalized_action.get('type', 'unknown')
        
        # Log action
        self.action_history.append({
            'action_id': action_id,
            'action': normalized_action,
            'context': context,
            'timestamp': time.time()
        })
        
        # Check if action requires intervention
        intervention_needed = self._should_intervene(normalized_action, context)
        
        if not intervention_needed:
            # Action approved automatically
            self.approved_actions += 1
            self._notify_action_callbacks(action_id, {'status': 'auto_approved', 'action': action})
            return action, ActionStatus.APPROVED
        
        # Create intervention request
        intervention = ActionIntervention(
            action_id=action_id,
            action_type=action_type,
            context=context,
            timestamp=time.time(),
            timeout=timeout
        )
        
        self.pending_interventions[action_id] = intervention
        self.intercepted_actions += 1
        
        # Notify intervention callbacks
        self._notify_intervention_callbacks(intervention)
        
        # Wait for user response or timeout
        final_action, status = self._wait_for_intervention_response(intervention, action)
        
        # Update statistics
        if status == ActionStatus.APPROVED:
            self.approved_actions += 1
        elif status == ActionStatus.REJECTED:
            self.rejected_actions += 1
        elif status == ActionStatus.MODIFIED:
            self.modified_actions += 1
        
        # Clean up
        if action_id in self.pending_interventions:
            del self.pending_interventions[action_id]
        
        return final_action, status
    
    def submit_user_response(self, action_id: str, approved: bool, 
                           modified_action: Optional[Any] = None, 
                           reason: Optional[str] = None) -> bool:
        """
        Submit user response to an intervention request.
        
        Args:
            action_id: ID of the action intervention
            approved: Whether the action is approved
            modified_action: Optional modified action if not approved as-is
            reason: Optional reason for the decision
            
        Returns:
            True if response was successfully submitted
        """
        if action_id not in self.pending_interventions:
            return False
        
        intervention = self.pending_interventions[action_id]
        
        if approved:
            intervention.status = ActionStatus.APPROVED
        elif modified_action is not None:
            intervention.status = ActionStatus.MODIFIED
            intervention.modified_action = modified_action
        else:
            intervention.status = ActionStatus.REJECTED
        
        intervention.user_response = {
            'approved': approved,
            'modified_action': modified_action,
            'reason': reason,
            'response_time': time.time() - intervention.timestamp
        }
        
        # Put response in queue
        self.user_input_queue.put(intervention)
        
        return True
    
    def add_intervention_callback(self, callback: Callable[[ActionIntervention], None]) -> None:
        """Add callback for intervention requests"""
        self.intervention_callbacks.append(callback)
    
    def add_action_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for action processing"""
        self.action_callbacks.append(callback)
    
    def get_pending_interventions(self) -> List[ActionIntervention]:
        """Get list of pending intervention requests"""
        return list(self.pending_interventions.values())
    
    def get_action_statistics(self) -> Dict[str, Any]:
        """Get action processing statistics"""
        return {
            'total_actions': self.total_actions,
            'intercepted_actions': self.intercepted_actions,
            'approved_actions': self.approved_actions,
            'rejected_actions': self.rejected_actions,
            'modified_actions': self.modified_actions,
            'intervention_rate': self.intercepted_actions / max(1, self.total_actions),
            'approval_rate': self.approved_actions / max(1, self.intercepted_actions),
            'modification_rate': self.modified_actions / max(1, self.intercepted_actions)
        }
    
    def get_recent_actions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent action history"""
        return list(self.action_history)[-count:]
    
    def _should_intervene(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Determine if an action requires user intervention"""
        action_type = action.get('type', 'unknown')
        
        # Check if action requires confirmation
        if self.preference_manager.requires_confirmation(action_type):
            return True
        
        # Check if action is forbidden
        if not self.preference_manager.is_action_allowed(action_type):
            return True
        
        # Check intervention frequency preference
        intervention_freq = self.preference_manager.global_preferences.get('user_intervention_frequency', 0.2)
        if intervention_freq > 0 and (self.total_actions % int(1.0 / intervention_freq)) == 0:
            return True
        
        # Check safety constraints
        if self._violates_safety_constraints(action, context):
            return True
        
        # Check for high-risk actions
        if self._is_high_risk_action(action, context):
            return True
        
        return False
    
    def _violates_safety_constraints(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if action violates safety constraints"""
        safety_constraints = self.preference_manager.safety_constraints
        
        # Check distance constraints
        if safety_constraints.max_distance_from_start:
            current_distance = context.get('distance_from_start', 0.0)
            if current_distance > safety_constraints.max_distance_from_start:
                return True
        
        # Add other safety checks here
        
        return False
    
    def _is_high_risk_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if action is considered high-risk"""
        action_type = action.get('type', 'unknown')
        
        # Define high-risk actions
        high_risk_actions = ['GRAB_FRAGILE', 'MOVE_EXPENSIVE', 'DELETE', 'IRREVERSIBLE_ACTION']
        
        return action_type in high_risk_actions
    
    def _normalize_action(self, action: Union[str, int, Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize action to dictionary format"""
        if isinstance(action, dict):
            return action
        elif isinstance(action, str):
            return {'type': action}
        elif isinstance(action, int):
            # Map action ID to action name
            action_names = ["STOP", "MOVE_FORWARD", "TURN_LEFT", "TURN_RIGHT", 
                           "LOOK_UP", "LOOK_DOWN", "GRAB_RELEASE"]
            action_type = action_names[action] if 0 <= action < len(action_names) else "UNKNOWN"
            return {'type': action_type, 'id': action}
        else:
            return {'type': 'unknown', 'raw': str(action)}
    
    def _wait_for_intervention_response(self, intervention: ActionIntervention, 
                                      original_action: Any) -> tuple[Any, ActionStatus]:
        """Wait for user response to intervention request"""
        start_time = time.time()
        
        while time.time() - start_time < intervention.timeout:
            try:
                # Check for user response
                response_intervention = self.user_input_queue.get(timeout=1.0)
                
                if response_intervention.action_id == intervention.action_id:
                    if response_intervention.status == ActionStatus.APPROVED:
                        return original_action, ActionStatus.APPROVED
                    elif response_intervention.status == ActionStatus.MODIFIED:
                        return response_intervention.modified_action, ActionStatus.MODIFIED
                    else:
                        return None, ActionStatus.REJECTED
                else:
                    # Put back response for different action
                    self.user_input_queue.put(response_intervention)
                    
            except queue.Empty:
                continue
        
        # Timeout - apply default behavior
        return self._handle_intervention_timeout(intervention, original_action)
    
    def _handle_intervention_timeout(self, intervention: ActionIntervention, 
                                   original_action: Any) -> tuple[Any, ActionStatus]:
        """Handle intervention request timeout"""
        # Default behavior on timeout - can be configured
        default_on_timeout = self.preference_manager.global_preferences.get('default_on_timeout', 'reject')
        
        if default_on_timeout == 'approve':
            return original_action, ActionStatus.APPROVED
        else:
            return None, ActionStatus.TIMEOUT
    
    def _notify_intervention_callbacks(self, intervention: ActionIntervention) -> None:
        """Notify all intervention callbacks"""
        for callback in self.intervention_callbacks:
            try:
                callback(intervention)
            except Exception as e:
                # Log error but don't break the flow
                print(f"Error in intervention callback: {e}")
    
    def _notify_action_callbacks(self, action_id: str, action_info: Dict[str, Any]) -> None:
        """Notify all action callbacks"""
        for callback in self.action_callbacks:
            try:
                callback(action_id, action_info)
            except Exception as e:
                # Log error but don't break the flow
                print(f"Error in action callback: {e}")
    
    def create_intervention_summary(self) -> Dict[str, Any]:
        """Create summary of intervention system status"""
        pending_count = len(self.pending_interventions)
        stats = self.get_action_statistics()
        
        return {
            'pending_interventions': pending_count,
            'statistics': stats,
            'recent_actions': self.get_recent_actions(5),
            'active_callbacks': {
                'intervention_callbacks': len(self.intervention_callbacks),
                'action_callbacks': len(self.action_callbacks)
            }
        }