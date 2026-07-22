import time
import random
import requests

API_URL = "http://127.0.0.1:8000/api/count"
EVENT_ID = 1

# Camera IDs mapping (from seed data):
# Camera 1 & 2 = Entry
# Camera 3, 4, 5, 6, 7 = Exit
ENTRY_CAMS = [1, 2]
EXIT_CAMS = [3, 4, 5, 6, 7]

def simulate_visitor_flow(duration_seconds=60, delay=1.5):
    print("=" * 60)
    print("🚀 MEMULAI SIMULASI HITUNGAN PENGUNJUNG REAL-TIME")
    print("Buka Dashboard di browser: http://localhost:8000/")
    print("=" * 60)

    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        # 70% chance of visitor entry, 30% exit
        is_entry = random.random() < 0.7

        if is_entry:
            cam_id = random.choice(ENTRY_CAMS)
            count = random.randint(1, 3)
            role_desc = "MASUK (Entry)"
        else:
            cam_id = random.choice(EXIT_CAMS)
            count = random.randint(1, 2)
            role_desc = "KELUAR (Exit)"

        payload = {
            "event_id": EVENT_ID,
            "camera_id": cam_id,
            "count": count
        }

        try:
            res = requests.post(API_URL, json=payload)
            if res.status_code == 200:
                data = res.json()["summary"]
                print(f"[{role_desc}] Kamera #{cam_id} (+{count}) | "
                      f"Masuk: {data['total_in']} | Keluar: {data['total_out']} | "
                      f"👉 DI DALAM: {data['current_inside']}")
            else:
                print(f"❌ Error API: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"⚠️ Gagal terhubung ke API server (Pastikan server Uvicorn berjalan): {e}")

        time.sleep(delay)

    print("\n✅ Simulasi Selesai!")

if __name__ == "__main__":
    simulate_visitor_flow(duration_seconds=120, delay=2.0)
