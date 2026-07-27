import subprocess

def test_camera_runner_device_options():
    result = subprocess.run(
        ["python", "camera_runner.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "--device" in result.stdout
