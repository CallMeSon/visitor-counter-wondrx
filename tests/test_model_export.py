import os
import subprocess

def test_model_export_cli():
    # Pastikan file target tidak ada sebelum pengujian
    if os.path.exists("yolov8s.onnx"):
        os.remove("yolov8s.onnx")
    
    # Jalankan skrip ekspor
    result = subprocess.run(
        ["python", "export_model.py", "--model", "yolov8s.pt"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert os.path.exists("yolov8s.onnx")
