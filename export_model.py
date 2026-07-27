import argparse
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Export YOLOv8 PyTorch model to ONNX format")
    parser.add_argument("--model", type=str, default="yolov8s.pt",
                        help="Nama file model PyTorch (.pt)")
    args = parser.parse_args()

    print(f"📥 Memuat model PyTorch: {args.model}")
    model = YOLO(args.model)
    
    print("⚡ Mengekspor model ke format ONNX...")
    onnx_path = model.export(format="onnx", imgsz=640)
    print(f"✅ Ekspor selesai! File ONNX tersimpan di: {onnx_path}")

if __name__ == "__main__":
    main()
