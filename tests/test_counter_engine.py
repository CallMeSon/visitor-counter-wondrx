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
