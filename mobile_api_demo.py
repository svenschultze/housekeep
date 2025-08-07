"""
Example demonstrating the "Swipe to Approve" mobile API.

Shows how the robot and mobile app would interact through the lightweight Move API.
"""

from mobile_api import MoveDecision
from mobile_api.integration import HousekeepMobileIntegration
import time


def demo_swipe_to_approve():
    """
    Demonstrate the complete workflow:
    1. Robot proposes moves
    2. Mobile app fetches pending moves  
    3. User swipes to approve/reject
    4. Robot receives feedback and acts accordingly
    """
    print("=== Mobile 'Swipe to Approve' API Demo ===\n")
    
    # Initialize the system
    integration = HousekeepMobileIntegration()
    api = integration.get_api()
    
    print("1. Robot proposes several tidying moves...")
    
    # Robot proposes multiple moves
    moves = [
        {
            'object': 'coffee mug',
            'from': 'kitchen counter',
            'to': 'dishwasher',
            'confidence': 0.9
        },
        {
            'object': 'laptop',
            'from': 'dining table', 
            'to': 'office desk',
            'confidence': 0.7
        },
        {
            'object': 'toy car',
            'from': 'living room floor',
            'to': 'toy box',
            'confidence': 0.95
        },
        {
            'object': 'kitchen knife',
            'from': 'counter',
            'to': 'knife block', 
            'confidence': 0.6
        }
    ]
    
    move_ids = []
    for move_data in moves:
        move_id = integration.propose_move(
            object_label=move_data['object'],
            from_location=move_data['from'],
            to_location=move_data['to'],
            confidence_score=move_data['confidence']
        )
        move_ids.append(move_id)
        print(f"  - Proposed: {move_data['object']} from '{move_data['from']}' to '{move_data['to']}' (confidence: {move_data['confidence']})")
    
    print(f"\n2. Mobile app fetches {len(move_ids)} pending moves...")
    
    # Mobile app gets moves for card stack
    pending_moves = api.list_moves()
    print(f"Found {len(pending_moves)} moves to show in card stack:")
    
    for move in pending_moves:
        print(f"  - {move.object_label}: {move.from_location} → {move.to_location} (confidence: {move.confidence_score:.1f})")
    
    print("\n3. User swipes on cards...")
    
    # Simulate user swipe decisions
    swipe_decisions = {
        move_ids[0]: MoveDecision.APPROVE,  # coffee mug - approve
        move_ids[1]: MoveDecision.APPROVE,  # laptop - approve  
        move_ids[2]: MoveDecision.APPROVE,  # toy car - approve
        move_ids[3]: MoveDecision.REJECT,   # knife - reject (safety concern)
    }
    
    for move_id, decision in swipe_decisions.items():
        move = api.get_move_details(move_id)
        action = decision.value.lower()
        print(f"  - {action.upper()}: {move.object_label} → {move.to_location}")
    
    # Send feedback to API
    results = api.send_feedback(swipe_decisions)
    print(f"\nFeedback submitted successfully: {all(results.values())}")
    
    print("\n4. Robot receives feedback and acts...")
    
    # Robot checks for decisions and executes approved moves
    for move_id in move_ids:
        move = api.get_move_details(move_id)
        
        if move.decision == MoveDecision.APPROVE:
            # Execute the move
            integration.execute_move(move_id)
            print(f"  ✓ EXECUTED: {move.object_label} moved to {move.to_location}")
            
        elif move.decision == MoveDecision.REJECT:
            # Learn from rejection, don't execute
            print(f"  ✗ REJECTED: {move.object_label} - learning user prefers it not in {move.to_location}")
            
        elif move.decision == MoveDecision.DEFER:
            # Ask again later
            print(f"  ⏸ DEFERRED: {move.object_label} - will ask again later")
    
    print("\n5. API statistics:")
    stats = api.get_stats()
    print(f"  - Total moves processed: {stats['total_moves']}")
    print(f"  - Approval rate: {stats['approval_rate']:.1%}")
    print(f"  - Pending moves: {stats['pending_count']}")
    
    print("\n=== Demo Complete ===")
    print("\nThis demonstrates the core 'Swipe to Approve' workflow:")
    print("✓ Robot proposes lightweight Move objects") 
    print("✓ Mobile app fetches moves with minimal API calls")
    print("✓ User swipes to approve/reject/defer")
    print("✓ Robot receives feedback and learns preferences")
    print("✓ ≲15s round-trip time for real-time control")


if __name__ == "__main__":
    demo_swipe_to_approve()