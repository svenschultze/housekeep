"""
Core Move objects and API for the "Swipe to Approve" interface.

Implements the lightweight Move-based system for mobile robot control.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid


class MoveState(Enum):
    """State of a Move in the approval workflow."""
    PENDING = "PENDING"      # Needs user swipe
    DECIDED = "DECIDED"      # User has swiped
    EXECUTED = "EXECUTED"    # Robot has completed action
    UNDONE = "UNDONE"        # Action was reversed


class MoveDecision(Enum):
    """User decision on a Move."""
    APPROVE = "APPROVE"      # Yes, that belongs there
    REJECT = "REJECT"        # No, undo or learn that I dislike this
    DEFER = "DEFER"          # Ask me later


@dataclass
class Move:
    """
    Core Move object representing a robot tidying action.
    
    The robot thinks of every tidying action as a Move: "put object from A to B".
    """
    move_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    object_label: str = ""           # Plain-language name ("coffee mug")
    from_location: str = ""          # Where object currently is
    to_location: str = ""            # Where robot plans to move it
    confidence_score: float = 0.0    # How sure the robot feels (0.0-1.0)
    state: MoveState = MoveState.PENDING
    decision: Optional[MoveDecision] = None
    
    # Optional fields
    snapshot_urls: Dict[str, str] = field(default_factory=dict)  # before/after images
    timestamp: datetime = field(default_factory=datetime.now)
    decision_timestamp: Optional[datetime] = None
    
    # Internal housekeeping data (hidden from mobile app)
    _internal_data: Dict[str, Any] = field(default_factory=dict)


class MoveAPI:
    """
    Minimal API for "Swipe to Approve" robot control.
    
    Only two operations needed:
    1. List Moves - get cards to show user
    2. Send Feedback - record user swipe decisions
    """
    
    def __init__(self, move_store):
        """Initialize with a move store backend."""
        self.move_store = move_store
        self.undo_window = timedelta(seconds=15)  # 15s window for undo
    
    def list_moves(self, include_recent_decided: bool = True) -> List[Move]:
        """
        Get moves for the card stack.
        
        Returns:
        - All PENDING moves (need swipes)
        - Optionally, decided moves from last day (for context)
        """
        moves = []
        
        # All pending moves
        moves.extend(self.move_store.get_moves_by_state(MoveState.PENDING))
        
        # Recent decided moves if requested
        if include_recent_decided:
            cutoff = datetime.now() - timedelta(days=1)
            recent_decided = self.move_store.get_moves_decided_after(cutoff)
            moves.extend(recent_decided)
        
        # Sort by timestamp, newest first
        moves.sort(key=lambda m: m.timestamp, reverse=True)
        return moves
    
    def send_feedback(self, feedback: Dict[str, MoveDecision]) -> Dict[str, bool]:
        """
        Record user swipe decisions.
        
        Args:
            feedback: Dict mapping move_id -> decision
            
        Returns:
            Dict mapping move_id -> success boolean
        """
        results = {}
        
        for move_id, decision in feedback.items():
            try:
                move = self.move_store.get_move(move_id)
                if not move:
                    results[move_id] = False
                    continue
                
                # Update move with decision
                move.decision = decision
                move.decision_timestamp = datetime.now()
                move.state = MoveState.DECIDED
                
                # Handle immediate undo for rejections within window
                if (decision == MoveDecision.REJECT and 
                    move.state in [MoveState.EXECUTED] and
                    datetime.now() - move.timestamp <= self.undo_window):
                    
                    self._trigger_undo(move)
                
                self.move_store.update_move(move)
                results[move_id] = True
                
            except Exception as e:
                print(f"Error processing feedback for {move_id}: {e}")
                results[move_id] = False
        
        return results
    
    def _trigger_undo(self, move: Move):
        """Trigger robot to undo a rejected move."""
        # This would integrate with the robot control system
        # For now, just mark as undone
        move.state = MoveState.UNDONE
        print(f"Triggering undo for move {move.move_id}: {move.object_label} from {move.to_location} back to {move.from_location}")
    
    def get_move_details(self, move_id: str) -> Optional[Move]:
        """Get full details for a specific move (for inspection)."""
        return self.move_store.get_move(move_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics about move approval patterns."""
        return {
            'pending_count': len(self.move_store.get_moves_by_state(MoveState.PENDING)),
            'total_moves': self.move_store.get_total_count(),
            'approval_rate': self.move_store.get_approval_rate(),
            'recent_activity': len(self.list_moves(include_recent_decided=True))
        }


def create_move(object_label: str, from_location: str, to_location: str, 
               confidence_score: float = 1.0, snapshot_urls: Optional[Dict[str, str]] = None) -> Move:
    """
    Convenience function to create a new Move.
    
    This is what the robot control system would call when planning/executing actions.
    """
    return Move(
        object_label=object_label,
        from_location=from_location,
        to_location=to_location,
        confidence_score=confidence_score,
        snapshot_urls=snapshot_urls or {}
    )