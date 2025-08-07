"""
Integration layer between the housekeeping robot and the mobile API.

This connects the existing Housekeep system to the new Move-based API.
"""

from typing import Any, Dict, Optional
from .move_api import MoveAPI, Move, MoveState, MoveDecision, create_move
from .move_store import MoveStore


class HousekeepMobileIntegration:
    """
    Integration layer that connects the Housekeep robot system to the mobile API.
    
    This would be integrated into the main robot control loop to:
    1. Convert robot actions into Move objects
    2. Check for user feedback before/after actions
    3. Handle approvals, rejections, and undos
    """
    
    def __init__(self):
        self.move_store = MoveStore()
        self.move_api = MoveAPI(self.move_store)
    
    def propose_move(self, object_label: str, from_location: str, 
                    to_location: str, confidence_score: float = 1.0,
                    snapshot_urls: Optional[Dict[str, str]] = None) -> str:
        """
        Robot proposes a new move.
        
        Returns the move_id for tracking.
        """
        move = create_move(
            object_label=object_label,
            from_location=from_location,
            to_location=to_location,
            confidence_score=confidence_score,
            snapshot_urls=snapshot_urls
        )
        
        self.move_store.add_move(move)
        return move.move_id
    
    def execute_move(self, move_id: str) -> bool:
        """
        Mark a move as executed by the robot.
        
        Returns True if successful.
        """
        move = self.move_store.get_move(move_id)
        if not move:
            return False
        
        move.state = MoveState.EXECUTED
        self.move_store.update_move(move)
        return True
    
    def check_pending_decisions(self) -> Dict[str, MoveDecision]:
        """
        Check for any user decisions on pending moves.
        
        Returns dict of move_id -> decision for newly decided moves.
        """
        decisions = {}
        decided_moves = self.move_store.get_moves_by_state(MoveState.DECIDED)
        
        for move in decided_moves:
            if move.decision:
                decisions[move.move_id] = move.decision
        
        return decisions
    
    def get_api(self) -> MoveAPI:
        """Get the MoveAPI for use by mobile app."""
        return self.move_api
    
    def should_execute_move(self, move_id: str, require_approval: bool = False) -> bool:
        """
        Check if a move should be executed based on user preferences.
        
        Args:
            move_id: ID of the move to check
            require_approval: If True, require explicit approval before execution
        
        Returns:
            True if move should be executed
        """
        move = self.move_store.get_move(move_id)
        if not move:
            return False
        
        if require_approval:
            # Require explicit approval
            return move.decision == MoveDecision.APPROVE
        else:
            # Execute unless explicitly rejected
            return move.decision != MoveDecision.REJECT
    
    def handle_rejection(self, move_id: str) -> bool:
        """
        Handle a rejected move (undo if already executed).
        
        Returns True if handled successfully.
        """
        move = self.move_store.get_move(move_id)
        if not move or move.decision != MoveDecision.REJECT:
            return False
        
        if move.state == MoveState.EXECUTED:
            # Trigger undo
            move.state = MoveState.UNDONE
            self.move_store.update_move(move)
            print(f"Undoing move: {move.object_label} from {move.to_location} back to {move.from_location}")
        
        return True