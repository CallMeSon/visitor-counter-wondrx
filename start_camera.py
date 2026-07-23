import os
import sys

def main():
    print("==================================================")
    print(" Visitor Counter - Interactive Camera Launcher ")
    print("==================================================")
    
    # 1. IP Host
    host_input = input("Masukkan IP Server Mini PC [Default: 127.0.0.1]: ").strip()
    host = host_input if host_input else "127.0.0.1"

    # 2. Camera ID
    cam_id_input = input("Masukkan Camera ID (1 & 2 = Entry, 3-7 = Exit) [Default: 1]: ").strip()
    camera_id = cam_id_input if cam_id_input else "1"

    # 3. Source
    source_input = input("Masukkan Source Kamera (0 = Webcam, atau nama file video) [Default: 0]: ").strip()
    source = source_input if source_input else "0"

    print("\n--------------------------------------------------")
    print(f"Menjalankan Kamera ID {camera_id} mengarah ke Server http://{host}:8000 ...")
    print("--------------------------------------------------\n")

    cmd = [sys.executable, "camera_runner.py", "--host", host, "--camera-id", camera_id, "--source", source]
    import subprocess
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
