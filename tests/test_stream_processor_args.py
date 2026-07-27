from unittest.mock import MagicMock, patch
from src.engine.stream_processor import CameraStreamProcessor

@patch("src.engine.stream_processor.YOLO")
@patch("src.engine.stream_processor.cv2.VideoCapture")
def test_stream_processor_custom_model_and_tracker(mock_video_capture, mock_yolo):
    # Set up VideoCapture mock to return False on open so processor.run() exits immediately
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_video_capture.return_value = mock_cap

    # Initialize processor
    processor = CameraStreamProcessor(
        camera_id=1,
        model_name="custom_model.onnx",
        tracker="custom_tracker.yaml",
        show_window=False
    )

    assert processor.model_name == "custom_model.onnx"
    assert processor.tracker == "custom_tracker.yaml"
    
    # Verify YOLO is initialized with the correct model path
    mock_yolo.assert_called_with("custom_model.onnx")
