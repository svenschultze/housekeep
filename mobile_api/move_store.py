"""
Simple in-memory storage for Move objects.

In production, this would be replaced with a proper database backend.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .move_api import Move, MoveState, MoveDecision


class MoveStore:
    """
    Simple in-memory store for Move objects.
    
    Provides basic CRUD operations needed by the MoveAPI.
    """
    
    def __init__(self):
        self._moves: Dict[str, Move] = {}
    
    def add_move(self, move: Move) -> None:
        """Add a new move to the store."""
        self._moves[move.move_id] = move
    
    def get_move(self, move_id: str) -> Optional[Move]:
        """Get a move by ID."""
        return self._moves.get(move_id)
    
    def update_move(self, move: Move) -> None:
        """Update an existing move."""
        self._moves[move.move_id] = move
    
    def get_moves_by_state(self, state: MoveState) -> List[Move]:
        """Get all moves with a specific state."""
        return [move for move in self._moves.values() if move.state == state]
    
    def get_moves_decided_after(self, cutoff: datetime) -> List[Move]:
        """Get moves that were decided after a certain time."""
        return [
            move for move in self._moves.values() 
            if (move.decision_timestamp and 
                move.decision_timestamp >= cutoff and 
                move.state == MoveState.DECIDED)
        ]
    
    def get_total_count(self) -> int:
        """Get total number of moves."""
        return len(self._moves)
    
    def get_approval_rate(self) -> float:
        """Calculate approval rate from decided moves."""
        decided_moves = [
            move for move in self._moves.values() 
            if move.decision is not None
        ]
        
        if not decided_moves:
            return 0.0
        
        approved = sum(1 for move in decided_moves if move.decision == MoveDecision.APPROVE)
        return approved / len(decided_moves)
    
    def clear(self) -> None:
        """Clear all moves (for testing)."""
        self._moves.clear()
    
    def get_all_moves(self) -> List[Move]:
        """Get all moves."""
        return list(self._moves.values())