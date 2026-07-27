import argparse
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Export YOLOv8 PyTorch model to ONNX or OpenVINO format")
    parser.add_argument("--model", type=str, default="yolov8s.pt",
                        help="Nama file model PyTorch (.pt)")
    parser.add_argument("--format", type=str, choices=["onnx", "openvino"], default="onnx",
                        help="Format ekspor model (onnx atau openvino)")
    args = parser.parse_args()

    print(f"📥 Memuat model PyTorch: {args.model}")
    model = YOLO(args.model)
    
    print(f"⚡ Mengekspor model ke format {args.format}...")
    export_path = model.export(format=args.format, imgsz=640)
    print(f"✅ Ekspor selesai! Hasil tersimpan di: {export_path}")

if __name__ == "__main__":
    main()
