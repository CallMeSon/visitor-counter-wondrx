import sys
import os
import pytest

def test_camera_runner_api_key_argument(monkeypatch):
    from camera_runner import main
    test_args = ["camera_runner.py", "--no-window", "--api-key", "mysecret"]
    monkeypatch.setattr(sys, "argv", test_args)
    
    captured_kwargs = {}
    def mock_processor_init(self, **kwargs):
        captured_kwargs.update(kwargs)
        self.api_key = kwargs.get("api_key")
        self.show_window = False
    
    def mock_run(self):
        pass

    from src.engine.stream_processor import CameraStreamProcessor
    monkeypatch.setattr(CameraStreamProcessor, "__init__", mock_processor_init)
    monkeypatch.setattr(CameraStreamProcessor, "run", mock_run)

    main()
    assert captured_kwargs.get("api_key") == "mysecret"
