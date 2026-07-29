import time
import pytest
import requests
from unittest.mock import MagicMock
from src.engine.stream_processor import CameraStreamProcessor

def test_async_telemetry_non_blocking_when_offline(monkeypatch):
    processor = CameraStreamProcessor(camera_id=1, show_window=False, api_key="secret123")
    
    # Mock requests.post to simulate a slow 3-second network timeout
    def mock_slow_failing_post(*args, **kwargs):
        time.sleep(1.0)
        raise requests.exceptions.ConnectionError("Backend unreachable")
    
    monkeypatch.setattr(requests, "post", mock_slow_failing_post)
    
    # Measure execution time of send_count_to_api from main thread perspective
    start_time = time.time()
    processor.send_count_to_api(count=1)
    elapsed = time.time() - start_time
    
    # Main thread execution should be instantaneous (< 0.1s), NOT blocking for 1+ seconds
    assert elapsed < 0.1
    
    # Clean up worker thread
    if hasattr(processor, "stop_worker"):
        processor.stop_worker()
