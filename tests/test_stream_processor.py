import pytest
from src.engine.stream_processor import calculate_line_points

def test_calculate_line_points_horizontal():
    p1, p2 = calculate_line_points(width=640, height=480, orientation="horizontal", position=0.5)
    assert p1 == (0, 240)
    assert p2 == (640, 240)

def test_calculate_line_points_vertical():
    p1, p2 = calculate_line_points(width=640, height=480, orientation="vertical", position=0.5)
    assert p1 == (320, 0)
    assert p2 == (320, 480)

def test_calculate_line_points_custom():
    p1, p2 = calculate_line_points(width=640, height=480, orientation="custom", custom_coords="100,50,500,400")
    assert p1 == (100, 50)
    assert p2 == (500, 400)
