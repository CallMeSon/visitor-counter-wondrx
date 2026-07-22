import sys
import argparse
from src.engine.stream_processor import CameraStreamProcessor

def main():
    parser = argparse.ArgumentParser(description="Live AI Body Detection & Visitor Counter Camera Runner")
    parser.add_argument("--camera-id", type=int, default=1, help="Camera ID in DB (1 or 2 = Entry, 3-7 = Exit)")
    parser.add_argument("--source", type=str, default="0", help="Camera source: 0 for Webcam, or video file path / RTSP URL")
    parser.add_argument("--event-id", type=int, default=1, help="Event ID")
    parser.add_argument("--no-window", action="store_true", help="Disable OpenCV video window GUI")
    
    args = parser.parse_args()

    # Convert string "0" to integer 0 for webcam
    source = 0 if args.source == "0" else args.source

    processor = CameraStreamProcessor(
        camera_id=args.camera_id,
        event_id=args.event_id,
        source=source,
        line_p1=(0, 240),
        line_p2=(640, 240),
        show_window=not args.no_window
    )

    processor.run()

if __name__ == "__main__":
    main()
