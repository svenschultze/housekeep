"""
Tests for the Mobile "Swipe to Approve" API.

Validates core functionality of the lightweight Move-based system.
"""

import unittest
from datetime import datetime, timedelta
from mobile_api import MoveAPI, Move, MoveState, MoveDecision, MoveStore, create_move


class TestMoveAPI(unittest.TestCase):
    """Test the core MoveAPI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = MoveStore()
        self.api = MoveAPI(self.store)
    
    def test_create_move(self):
        """Test creating a new Move object."""
        move = create_move(
            object_label="test mug",
            from_location="table", 
            to_location="dishwasher",
            confidence_score=0.8
        )
        
        self.assertEqual(move.object_label, "test mug")
        self.assertEqual(move.from_location, "table")
        self.assertEqual(move.to_location, "dishwasher")
        self.assertEqual(move.confidence_score, 0.8)
        self.assertEqual(move.state, MoveState.PENDING)
        self.assertIsNone(move.decision)
        self.assertIsNotNone(move.move_id)
    
    def test_list_moves_empty(self):
        """Test listing moves when store is empty."""
        moves = self.api.list_moves()
        self.assertEqual(len(moves), 0)
    
    def test_list_moves_with_pending(self):
        """Test listing moves with pending items."""
        # Add some pending moves
        move1 = create_move("mug", "table", "dishwasher")
        move2 = create_move("book", "couch", "shelf") 
        
        self.store.add_move(move1)
        self.store.add_move(move2)
        
        moves = self.api.list_moves()
        self.assertEqual(len(moves), 2)
        
        # Should be sorted by timestamp (newest first)
        self.assertIn(move1, moves)
        self.assertIn(move2, moves)
    
    def test_send_feedback_approve(self):
        """Test sending approval feedback."""
        move = create_move("mug", "table", "dishwasher")
        self.store.add_move(move)
        
        feedback = {move.move_id: MoveDecision.APPROVE}
        results = self.api.send_feedback(feedback)
        
        self.assertTrue(results[move.move_id])
        
        # Check move was updated
        updated_move = self.store.get_move(move.move_id)
        self.assertEqual(updated_move.decision, MoveDecision.APPROVE)
        self.assertEqual(updated_move.state, MoveState.DECIDED)
        self.assertIsNotNone(updated_move.decision_timestamp)
    
    def test_send_feedback_reject(self):
        """Test sending rejection feedback."""
        move = create_move("knife", "counter", "drawer")
        self.store.add_move(move)
        
        feedback = {move.move_id: MoveDecision.REJECT}
        results = self.api.send_feedback(feedback)
        
        self.assertTrue(results[move.move_id])
        
        # Check move was updated
        updated_move = self.store.get_move(move.move_id)
        self.assertEqual(updated_move.decision, MoveDecision.REJECT)
        self.assertEqual(updated_move.state, MoveState.DECIDED)
    
    def test_send_feedback_nonexistent_move(self):
        """Test sending feedback for non-existent move."""
        feedback = {"fake_id": MoveDecision.APPROVE}
        results = self.api.send_feedback(feedback)
        
        self.assertFalse(results["fake_id"])
    
    def test_send_feedback_batch(self):
        """Test sending feedback for multiple moves."""
        move1 = create_move("mug", "table", "dishwasher")
        move2 = create_move("book", "couch", "shelf")
        
        self.store.add_move(move1)
        self.store.add_move(move2)
        
        feedback = {
            move1.move_id: MoveDecision.APPROVE,
            move2.move_id: MoveDecision.REJECT
        }
        results = self.api.send_feedback(feedback)
        
        self.assertTrue(all(results.values()))
        
        # Check both moves were updated
        updated1 = self.store.get_move(move1.move_id)
        updated2 = self.store.get_move(move2.move_id)
        
        self.assertEqual(updated1.decision, MoveDecision.APPROVE)
        self.assertEqual(updated2.decision, MoveDecision.REJECT)
    
    def test_get_stats(self):
        """Test getting API statistics."""
        stats = self.api.get_stats()
        
        self.assertEqual(stats['pending_count'], 0)
        self.assertEqual(stats['total_moves'], 0)
        self.assertEqual(stats['approval_rate'], 0.0)
        
        # Add some moves and decisions
        move1 = create_move("mug", "table", "dishwasher")
        move2 = create_move("book", "couch", "shelf")
        
        self.store.add_move(move1)
        self.store.add_move(move2)
        
        # Decide on one
        feedback = {move1.move_id: MoveDecision.APPROVE}
        self.api.send_feedback(feedback)
        
        stats = self.api.get_stats()
        self.assertEqual(stats['pending_count'], 1)  # move2 still pending
        self.assertEqual(stats['total_moves'], 2)
        self.assertEqual(stats['approval_rate'], 1.0)  # 100% of decided moves approved


class TestMoveStore(unittest.TestCase):
    """Test the MoveStore functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = MoveStore()
    
    def test_add_and_get_move(self):
        """Test adding and retrieving moves."""
        move = create_move("test", "here", "there")
        self.store.add_move(move)
        
        retrieved = self.store.get_move(move.move_id)
        self.assertEqual(retrieved, move)
    
    def test_get_nonexistent_move(self):
        """Test retrieving non-existent move."""
        result = self.store.get_move("fake_id")
        self.assertIsNone(result)
    
    def test_get_moves_by_state(self):
        """Test filtering moves by state."""
        move1 = create_move("mug", "table", "dishwasher")
        move2 = create_move("book", "couch", "shelf")
        move2.state = MoveState.EXECUTED
        
        self.store.add_move(move1)
        self.store.add_move(move2)
        
        pending = self.store.get_moves_by_state(MoveState.PENDING)
        executed = self.store.get_moves_by_state(MoveState.EXECUTED)
        
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(executed), 1)
        self.assertEqual(pending[0], move1)
        self.assertEqual(executed[0], move2)
    
    def test_approval_rate_calculation(self):
        """Test approval rate calculation."""
        # No decided moves
        self.assertEqual(self.store.get_approval_rate(), 0.0)
        
        # Add moves with decisions
        move1 = create_move("mug", "table", "dishwasher")
        move1.decision = MoveDecision.APPROVE
        
        move2 = create_move("book", "couch", "shelf")
        move2.decision = MoveDecision.REJECT
        
        move3 = create_move("phone", "desk", "charger")
        move3.decision = MoveDecision.APPROVE
        
        self.store.add_move(move1)
        self.store.add_move(move2)
        self.store.add_move(move3)
        
        # 2 approved out of 3 decided = 66.67%
        self.assertAlmostEqual(self.store.get_approval_rate(), 2/3, places=2)


class TestMoveLifecycle(unittest.TestCase):
    """Test the complete move lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = MoveStore()
        self.api = MoveAPI(self.store)
    
    def test_complete_lifecycle(self):
        """Test complete move from creation to decision."""
        # 1. Create and add move
        move = create_move("mug", "table", "dishwasher", confidence_score=0.9)
        self.store.add_move(move)
        self.assertEqual(move.state, MoveState.PENDING)
        
        # 2. List moves (mobile app fetches)
        moves = self.api.list_moves()
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].move_id, move.move_id)
        
        # 3. User swipes to approve
        feedback = {move.move_id: MoveDecision.APPROVE}
        results = self.api.send_feedback(feedback)
        self.assertTrue(results[move.move_id])
        
        # 4. Verify state change
        updated = self.store.get_move(move.move_id)
        self.assertEqual(updated.state, MoveState.DECIDED)
        self.assertEqual(updated.decision, MoveDecision.APPROVE)
        self.assertIsNotNone(updated.decision_timestamp)
        
        # 5. Move should now appear in decided list
        decided_moves = self.store.get_moves_by_state(MoveState.DECIDED)
        self.assertEqual(len(decided_moves), 1)
        
        # 6. Should still appear in list_moves (recent decided)
        moves = self.api.list_moves(include_recent_decided=True)
        self.assertEqual(len(moves), 1)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)