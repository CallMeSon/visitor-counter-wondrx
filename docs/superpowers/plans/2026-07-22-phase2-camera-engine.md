# Phase 2: AI & Camera Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core line-crossing detection algorithm and video stream counter module capable of detecting direction vector crossing for 7 cameras (2 entry, 5 exit).

**Architecture:** Pure geometric cross-product line-crossing counter tracking bounding-box centroids across video frames, yielding directional crossing events (`forward` vs `backward`).

**Tech Stack:** Python 3.10+, NumPy, Pytest.

## Global Constraints

- Pure Python/NumPy geometric detection without external GPU or custom training requirements for MVP.
- Supports directional crossing detection (`forward` vs `backward`).
- Memory footprint: tracks active object IDs and clears dead tracks.

---

### Task 1: Geometric Line-Crossing Detector

**Files:**
- Create: `src/engine/__init__.py`
- Create: `src/engine/counter.py`
- Test: `tests/test_counter_engine.py`

**Interfaces:**
- Consumes: None
- Produces: `LineCrossCounter`, `Point`, `update_position()`, `reset_track()`

- [ ] **Step 1: Write the failing test for LineCrossCounter**

Create `tests/test_counter_engine.py`:
```python
import pytest
from src.engine.counter import LineCrossCounter

def test_entry_direction_crossing():
    # Line defined at y = 100 from x=0 to x=200
    counter = LineCrossCounter(line_p1=(0, 100), line_p2=(200, 100), direction_vector=(0, 1))

    # Object 1 moves downward across line y=100 (from 80 to 120)
    events_1 = counter.update_position(obj_id=1, pos=(100, 80))
    assert len(events_1) == 0

    events_2 = counter.update_position(obj_id=1, pos=(100, 120))
    assert len(events_2) == 1
    assert events_2[0]["obj_id"] == 1
    assert events_2[0]["direction"] == "forward"

def test_exit_direction_crossing():
    counter = LineCrossCounter(line_p1=(0, 100), line_p2=(200, 100), direction_vector=(0, 1))

    # Object 2 moves upward across line y=100 (from 120 to 80)
    counter.update_position(obj_id=2, pos=(100, 120))
    events = counter.update_position(obj_id=2, pos=(100, 80))
    assert len(events) == 1
    assert events[0]["obj_id"] == 2
    assert events[0]["direction"] == "backward"

def test_reset_object_track():
    counter = LineCrossCounter(line_p1=(0, 100), line_p2=(200, 100))
    counter.update_position(obj_id=1, pos=(100, 80))
    counter.reset_track(obj_id=1)
    assert 1 not in counter.history
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_counter_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.engine'`

- [ ] **Step 3: Write minimal LineCrossCounter implementation**

Create empty file `src/engine/__init__.py`.

Create `src/engine/counter.py`:
```python
from typing import Tuple, Dict, List, Optional

Point = Tuple[int, int]

class LineCrossCounter:
    def __init__(self, line_p1: Point, line_p2: Point, direction_vector: Point = (0, 1)):
        self.line_p1 = line_p1
        self.line_p2 = line_p2
        self.direction_vector = direction_vector
        self.history: Dict[int, List[Point]] = {}
        self.crossed_ids: set = set()

    def _cross_product(self, p1: Point, p2: Point, p3: Point) -> float:
        return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])

    def update_position(self, obj_id: int, pos: Point) -> List[Dict]:
        events = []
        if obj_id not in self.history:
            self.history[obj_id] = [pos]
            return events

        prev_pos = self.history[obj_id][-1]
        self.history[obj_id].append(pos)

        cp1 = self._cross_product(self.line_p1, self.line_p2, prev_pos)
        cp2 = self._cross_product(self.line_p1, self.line_p2, pos)

        if cp1 * cp2 < 0 and obj_id not in self.crossed_ids:
            self.crossed_ids.add(obj_id)
            direction = "forward" if cp2 > cp1 else "backward"
            events.append({
                "obj_id": obj_id,
                "direction": direction,
                "prev_pos": prev_pos,
                "curr_pos": pos
            })

        return events

    def reset_track(self, obj_id: int):
        self.history.pop(obj_id, None)
        self.crossed_ids.discard(obj_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_counter_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/engine/__init__.py src/engine/counter.py tests/test_counter_engine.py
git commit -m "feat(engine): implement geometric line-crossing detector module"
```
