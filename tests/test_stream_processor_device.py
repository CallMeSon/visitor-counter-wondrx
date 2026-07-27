from unittest.mock import MagicMock, patch
from src.engine.stream_processor import CameraStreamProcessor

@patch("src.engine.stream_processor.YOLO")
@patch("src.engine.stream_processor.cv2.VideoCapture")
def test_stream_processor_device_integration(mock_video_capture, mock_yolo):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_video_capture.return_value = mock_cap

    # Initialize with device="gpu"
    processor = CameraStreamProcessor(
        camera_id=1,
        model_name="yolov8s.onnx",
        tracker="bytetrack.yaml",
        device="gpu",
        show_window=False
    )

    assert processor.device == "gpu"
