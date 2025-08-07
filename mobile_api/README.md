# Mobile "Swipe to Approve" API for Housekeeping Robot

A lightweight, mobile-first API that enables users to control a tidying robot through a simple Tinder-like swipe interface.

## Core Concept

The robot thinks of every tidying action as a **Move** ("put *object* from *A* to *B*").
The mobile app shows these Moves as swipeable cards where users can:

- **Approve** → "Yes, that belongs there"
- **Reject** → "No, undo or learn that I dislike this"  
- **Defer** → "Ask me later"

## Key Objects

| Concept | Description |
|---------|-------------|
| **Move ID** | Unique identifier for each card |
| **Object label** | Plain-language name ("coffee mug") |
| **From / To locations** | Where the object is/will be moved |
| **Confidence score** | How sure the robot feels (0.0-1.0) |
| **State** | `PENDING` → `DECIDED` → `EXECUTED`/`UNDONE` |
| **Snapshot URLs** | Optional before/after images |

## Minimal API

Just two operations needed:

### 1. List Moves
```python
api.list_moves()  # Get all pending moves + recent decided ones
```

### 2. Send Feedback  
```python
api.send_feedback({
    "move_123": MoveDecision.APPROVE,
    "move_456": MoveDecision.REJECT
})
```

## Quick Start

```python
from mobile_api import MoveAPI, MoveStore, MoveDecision
from mobile_api.integration import HousekeepMobileIntegration

# Initialize the system
integration = HousekeepMobileIntegration()
api = integration.get_api()

# Robot proposes a move
move_id = integration.propose_move(
    object_label="coffee mug",
    from_location="kitchen counter", 
    to_location="dishwasher",
    confidence_score=0.9
)

# Mobile app gets pending moves
moves = api.list_moves()
print(f"Found {len(moves)} moves to review")

# User swipes to approve/reject
feedback = {move_id: MoveDecision.APPROVE}
results = api.send_feedback(feedback)

# Robot executes approved moves
if results[move_id]:
    integration.execute_move(move_id)
```

## Move Life-Cycle

```
Robot proposes Move → Backend stores as PENDING
                         ↓
                   Phone fetches PENDING  
                         ↓
           User swipes APPROVE/REJECT/DEFER
                         ↓
                Backend marks DECIDED
                         ↓
         Robot receives update → may undo or learn
```

## Timing Constraints

- New moves appear in mobile app within ≲15 seconds
- Feedback round-trip completes before robot moves away from object
- Reject decisions within 15s window can trigger immediate undo

## Files

- `move_api.py` - Core Move objects and API
- `move_store.py` - Simple in-memory storage  
- `integration.py` - Bridge to existing robot system
- `README.md` - This documentation

## Future Extensions

While the V1 API is minimal, it can easily grow to support:
- Batch approval rules ("always approve cups → dishwasher")
- Priority tags and room preferences
- Real-time push notifications
- Confidence thresholds for auto-approval