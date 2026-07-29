import os
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
    parser.add_argument("--api-key", type=str, default=os.environ.get("API_KEY"),
                        help="API Key for Cloud Server authentication (optional for local dev)")
    
    parser.add_argument("--no-window", action="store_true", help="Disable OpenCV video window GUI")
    parser.add_argument("--model-name", type=str, default="yolov8s.onnx",
                        help="Model name or path (e.g. yolov8s.onnx, yolov8n.pt)")
    parser.add_argument("--tracker", type=str, default="bytetrack.yaml",
                        help="Tracker config name (bytetrack.yaml or botsort.yaml)")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to run inference (cpu, gpu, or GPU index e.g. 0)")
    
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

        host_in = input("3. Masukkan IP Host / Domain Backend (contoh: 192.168.1.100 atau api.eventku.com, press Enter jika localhost): ").strip()
        if host_in:
            args.host = host_in

        print("4. Pilih Format Engine Model:")
        print("   [1] OpenVINO (Disarankan untuk Laptop Intel / Intel Iris Xe GPU - Paling Cepat & Dingin) [Default]")
        print("   [2] ONNX (Disarankan untuk Mini PC AMD Ryzen / Radeon iGPU / CPU Universal)")
        print("   [3] PyTorch .pt (Disarankan untuk NVIDIA GPU CUDA / Standar)")
        model_choice = input("   Pilih [1-3, Default 1]: ").strip()
        if model_choice == "2":
            args.model_name = "yolov8s.onnx"
        elif model_choice == "3":
            args.model_name = "yolov8s.pt"
        elif model_choice == "1" or not model_choice:
            if os.path.exists("yolov8s_openvino_model"):
                args.model_name = "yolov8s_openvino_model"
            else:
                args.model_name = "yolov8s.onnx"
        else:
            args.model_name = model_choice

        print("\n5. Pilih Algoritma Pelacak (Tracker):")
        print("   [1] ByteTrack (Sangat Cepat & Ringan - Cocok untuk FPS Tinggi & Real-time) [Default]")
        print("   [2] BoT-SORT (Akurasi Ekstra - Memperhitungkan Pergerakan Kamera)")
        tracker_choice = input("   Pilih [1-2, Default 1]: ").strip()
        if tracker_choice == "2":
            args.tracker = "botsort.yaml"
        else:
            args.tracker = "bytetrack.yaml"

        print("\n6. Pilih Hardware Device Pemrosesan:")
        print("   [1] GPU (Akselerasi GPU Iris Xe / Dedicated GPU)")
        print("   [2] CPU (Pemrosesan Utama Prosesor) [Default]")
        device_choice = input("   Pilih [1-2, Default 2]: ").strip()
        if device_choice == "1":
            args.device = "gpu"
        else:
            args.device = "cpu"

        api_key_in = input("\n7. Masukkan API Key Server (Opsional, press Enter jika dev lokal): ").strip()
        if api_key_in:
            args.api_key = api_key_in

    # Tentukan API URL berdasarkan --api-url, --host, atau default 127.0.0.1
    if args.api_url:
        api_url = args.api_url
    elif args.host:
        host_str = args.host.strip()
        if host_str.startswith(("http://", "https://")):
            if "/api/count" in host_str:
                api_url = host_str
            else:
                api_url = f"{host_str.rstrip('/')}/api/count"
        else:
            api_url = f"http://{host_str}:{args.port}/api/count"
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
        api_key=args.api_key,
        model_name=args.model_name,
        tracker=args.tracker,
        device=args.device,
        show_window=not args.no_window
    )

    processor.run()

if __name__ == "__main__":
    main()
