import pytest
import requests
from unittest.mock import MagicMock
from src.engine.stream_processor import CameraStreamProcessor

def test_stream_processor_retry_queue_enqueue(monkeypatch):
    processor = CameraStreamProcessor(camera_id=1, show_window=False, api_key="secret123")
    
    def mock_post_fail(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Network disconnected")
    
    monkeypatch.setattr(requests, "post", mock_post_fail)
    
    processor.send_count_to_api(count=1)
    processor._telemetry_queue.join()
    assert len(processor.failed_queue) == 1
    assert processor.failed_queue[0]["count"] == 1
    assert processor.api_status == "offline"

def test_stream_processor_retry_queue_flush(monkeypatch):
    processor = CameraStreamProcessor(camera_id=1, show_window=False, api_key="secret123")
    processor.failed_queue.append({"event_id": 1, "camera_id": 1, "count": 2})
    
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"summary": {"current_inside": 10}}
    
    calls = []
    def mock_post_success(url, json=None, headers=None, timeout=None):
        calls.append(json)
        return mock_res
    
    monkeypatch.setattr(requests, "post", mock_post_success)
    
    processor.send_count_to_api(count=1)
    processor._telemetry_queue.join()
    assert len(calls) == 2
    assert len(processor.failed_queue) == 0
    assert processor.api_status == "ok"
