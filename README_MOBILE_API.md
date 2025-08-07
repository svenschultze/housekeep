# Mobile "Swipe to Approve" API for Housekeeping Robot

A lightweight, mobile-first API that enables users to control a tidying robot through a simple Tinder-like swipe interface.

## Concept-Level Brief

**Feature:** "Swipe to Approve" review loop for a home-tidying robot
**Purpose:** Enable real-time user control over robot actions through a simple mobile interface

### Core Idea

The robot thinks of every tidying action as a **Move** ("put *object* from *A* to *B*").
The phone shows these Moves as Tinder-like cards. The user swipes:

- **Approve** → "Yes, that belongs there"
- **Reject** → "No, undo or learn that I dislike this"
- **Defer** → "Ask me later"

### Key Objects

| Concept | Why it matters to the user |
|---------|---------------------------|
| **Move ID** | Lets the app refer unambiguously to a card |
| **Object label** | Plain-language name ("coffee mug") |
| **From / To locations** | So the user knows what the robot plans or has done |
| **Confidence score** | Quick cue on how sure the robot feels (helps decide when to inspect images) |
| **State** | `PENDING` (needs swipe) → `DECIDED` (after swipe) → optionally `EXECUTED` / `UNDONE` |
| **Snapshot URLs (optional)** | Before/after images the user can tap to inspect |

### Minimal Interactions

1. **List Moves** - *Client gets a page of all `PENDING` Moves plus any decided in the last day*
2. **Send Feedback** - *Client posts a decision for one or many Move IDs*

That's it. If you can list cards and send swipes, the loop works.

### Move Life-Cycle

```
Robot proposes/executes Move → Backend stores as PENDING
                                   │
                                   ▼
                             Phone fetches PENDING
                                   │
                       User swipes APPROVE / REJECT / DEFER
                                   │
                                   ▼
                          Backend marks DECIDED
                                   │
              (optional) Robot receives update → may undo or learn
```

**Timing constraints:**
- The phone should see new Moves quickly enough that a swipe-to-undo can still stop or reverse the action (≲ 15s ideal)
- A feedback round-trip should finish before the robot has walked away from the object

## Quick Start

```python
from mobile_api import MoveDecision
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

# User swipes to approve/reject
feedback = {move_id: MoveDecision.APPROVE}
results = api.send_feedback(feedback)

# Robot executes approved moves
if results[move_id]:
    integration.execute_move(move_id)
```

## Files

- `mobile_api/` - Complete API implementation
- `mobile_api_demo.py` - Working demonstration
- `test_mobile_api.py` - Comprehensive test suite

## Demo

Run the demo to see the API in action:

```bash
python mobile_api_demo.py
```

## Tests

Run the test suite to validate functionality:

```bash
python test_mobile_api.py
```

---

**In one sentence:** Expose a lightweight *Move* resource that the phone can list and annotate—nothing more is needed to let users steer a tidying robot with a simple swipe interface, while leaving room to add richer features later.