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
    
    parser.add_argument("--host", type=str, default=None, help="Server IP / Host (e.g. 192.168.1.150)")
    parser.add_argument("--port", type=int, default=8000, help="Server Port (default 8000)")
    parser.add_argument("--api-url", type=str, default=None,
                        help="Backend Server API URL (override custom host/port if specified)")
    
    parser.add_argument("--no-window", action="store_true", help="Disable OpenCV video window GUI")
    
    args = parser.parse_args()

    # If executed without command line arguments, offer interactive input prompts
    import sys
    if len(sys.argv) == 1:
        print("\n=======================================================")
        print("   Event Visitor Counter - Interactive Camera Setup    ")
        print("=======================================================\n")
        
        cam_id_in = input("1. Masukkan Camera ID (1-2 = Entry, 3-7 = Exit) [Default 1]: ").strip()
        if cam_id_in.isdigit():
            args.camera_id = int(cam_id_in)

        src_in = input("2. Masukkan Source Kamera (0 untuk Webcam, file video, atau URL RTSP) [Default 0]: ").strip()
        if src_in:
            args.source = src_in

        host_in = input("3. Masukkan IP Host Backend (contoh: 192.168.1.100, press Enter jika localhost): ").strip()
        if host_in:
            args.host = host_in

    # Tentukan API URL berdasarkan --api-url, --host, atau default 127.0.0.1
    if args.api_url:
        api_url = args.api_url
    elif args.host:
        api_url = f"http://{args.host}:{args.port}/api/count"
    else:
        api_url = f"http://127.0.0.1:{args.port}/api/count"

    # Convert string numeric camera index (e.g. "0", "1") to integer for OpenCV webcam
    if str(args.source).isdigit():
        source = int(args.source)
    else:
        source = args.source

    print(f"\n[INFO] Menjalankan Kamera #{args.camera_id} dengan Source '{source}' -> API: {api_url}\n")

    processor = CameraStreamProcessor(
        camera_id=args.camera_id,
        event_id=args.event_id,
        source=source,
        orientation=args.line_orientation,
        position=args.line_position,
        custom_coords=args.line_coords,
        api_url=api_url,
        show_window=not args.no_window
    )

    processor.run()

if __name__ == "__main__":
    main()
