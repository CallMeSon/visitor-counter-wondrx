import subprocess

def test_camera_runner_help_options():
    result = subprocess.run(
        ["python", "camera_runner.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "--model-name" in result.stdout
    assert "--tracker" in result.stdout
