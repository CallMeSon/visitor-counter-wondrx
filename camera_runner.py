import argparse
from src.engine.stream_processor import CameraStreamProcessor

def main():
    parser = argparse.ArgumentParser(description="Live AI Body Detection & Visitor Counter Camera Runner")
    parser.add_argument("--camera-id", type=int, default=1, help="Camera ID in DB (1 or 2 = Entry, 3-7 = Exit)")
    parser.add_argument("--source", type=str, default="0", help="Camera source: 0 for Webcam, video file path, or RTSP URL")
    parser.add_argument("--event-id", type=int, default=1, help="Event ID")
    
    # Line Adjustment Arguments
    parser.add_argument("--line-orientation", type=str, choices=["horizontal", "vertical", "custom"], default="horizontal",
                        help="Line orientation: 'horizontal', 'vertical', or 'custom'")
    parser.add_argument("--line-position", type=float, default=0.5,
                        help="Relative position of line on screen (0.1 to 0.9, default 0.5 = middle)")
    parser.add_argument("--line-coords", type=str, default=None,
                        help="Custom line coordinates in format 'x1,y1,x2,y2' (e.g. '100,200,500,200')")
    
    parser.add_argument("--no-window", action="store_true", help="Disable OpenCV video window GUI")
    
    args = parser.parse_args()

    # Convert string "0" to integer 0 for webcam
    source = 0 if args.source == "0" else args.source

    processor = CameraStreamProcessor(
        camera_id=args.camera_id,
        event_id=args.event_id,
        source=source,
        orientation=args.line_orientation,
        position=args.line_position,
        custom_coords=args.line_coords,
        show_window=not args.no_window
    )

    processor.run()

if __name__ == "__main__":
    main()
