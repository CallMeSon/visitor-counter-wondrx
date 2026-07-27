import os
import shutil
import subprocess

def test_openvino_model_export_cli():
    target_dir = "yolov8n_openvino_model"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        
    result = subprocess.run(
        ["python", "export_model.py", "--model", "yolov8n.pt", "--format", "openvino"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert os.path.exists(target_dir)
