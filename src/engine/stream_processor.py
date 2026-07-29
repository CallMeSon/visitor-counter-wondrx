import os
import time
import queue
import threading
import cv2
import requests
from ultralytics import YOLO
from src.engine.counter import LineCrossCounter

def calculate_line_points(
    width: int,
    height: int,
    orientation: str = "horizontal",
    position: float = 0.5,
    custom_coords: str = None
):
    if custom_coords:
        try:
            parts = list(map(int, custom_coords.split(",")))
            if len(parts) == 4:
                return (parts[0], parts[1]), (parts[2], parts[3])
        except Exception:
            pass

    position = max(0.05, min(0.95, position))

    if orientation == "vertical":
        x = int(width * position)
        return (x, 0), (x, height)
    else:  # default horizontal
        y = int(height * position)
        return (0, y), (width, y)


class CameraStreamProcessor:
    def __init__(
        self,
        camera_id: int,
        event_id: int = 1,
        source=0,
        orientation: str = "horizontal",
        position: float = 0.5,
        custom_coords: str = None,
        api_url="http://127.0.0.1:8000/api/count",
        api_key: str = None,
        model_name="yolov8s.onnx",
        tracker="bytetrack.yaml",
        device="cpu",
        show_window=True
    ):
        self.camera_id = camera_id
        self.event_id = event_id
        self.source = source
        self.orientation = orientation
        self.position = position
        self.custom_coords = custom_coords
        self.api_url = api_url
        self.api_key = api_key
        self.show_window = show_window
        self.model_name = model_name
        self.tracker = tracker
        self.device = device

        self.failed_queue = []
        self.max_queue_size = 1000
        self.api_status = "ok"  # "ok", "offline", or "unauthorized"

        # Threading queue for non-blocking telemetry I/O
        self._telemetry_queue = queue.Queue()
        self._stop_worker_flag = False
        self._worker_thread = threading.Thread(target=self._telemetry_worker, daemon=True)
        self._worker_thread.start()

        self.model = YOLO(model_name)
        self.line_p1 = (0, 240)
        self.line_p2 = (640, 240)
        self.line_counter = None
        self.dragging_point = None
        self.window_name = f"AI Visitor Counter - Camera #{self.camera_id}"

    def _mouse_callback(self, event, x, y, flags, param):
        DRAG_RADIUS = 35  # px radius untuk klik endpoint

        if event == cv2.EVENT_LBUTTONDOWN:
            dist_p1 = ((x - self.line_p1[0]) ** 2 + (y - self.line_p1[1]) ** 2) ** 0.5
            dist_p2 = ((x - self.line_p2[0]) ** 2 + (y - self.line_p2[1]) ** 2) ** 0.5
            if dist_p1 < DRAG_RADIUS:
                self.dragging_point = 1
            elif dist_p2 < DRAG_RADIUS:
                self.dragging_point = 2
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging_point == 1:
                self.line_p1 = (x, y)
                if self.line_counter:
                    self.line_counter.line_p1 = self.line_p1
            elif self.dragging_point == 2:
                self.line_p2 = (x, y)
                if self.line_counter:
                    self.line_counter.line_p2 = self.line_p2
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_point = None

    def send_count_to_api(self, count: int = 1):
        payload = {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "count": count
        }
        self._telemetry_queue.put({"type": "count", "payload": payload})

    def send_heartbeat_to_api(self):
        payload = {
            "event_id": self.event_id,
            "camera_id": self.camera_id
        }
        self._telemetry_queue.put({"type": "heartbeat", "payload": payload})

    def stop_worker(self):
        self._stop_worker_flag = True
        self._telemetry_queue.put(None)

    def _telemetry_worker(self):
        while not self._stop_worker_flag:
            try:
                task = self._telemetry_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if task is None:
                break

            task_type = task.get("type")
            payload = task.get("payload")
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            if task_type == "count":
                # Flush pending retry queue first if possible
                to_remove = []
                for item in list(self.failed_queue):
                    try:
                        res = requests.post(self.api_url, json=item, headers=headers, timeout=2.0)
                        if res.status_code == 200:
                            to_remove.append(item)
                        elif res.status_code == 401:
                            self.api_status = "unauthorized"
                            break
                    except requests.exceptions.RequestException:
                        break
                for item in to_remove:
                    self.failed_queue.remove(item)

                try:
                    res = requests.post(self.api_url, json=payload, headers=headers, timeout=2.0)
                    if res.status_code == 200:
                        self.api_status = "ok"
                        summary = res.json().get("summary", {})
                        print(f"✅ [Kamera #{self.camera_id}] Count Pushed! "
                              f"Current Inside: {summary.get('current_inside', 0)}")
                    elif res.status_code == 401:
                        self.api_status = "unauthorized"
                        print(f"❌ [Kamera #{self.camera_id}] API Key Rejected (401 Unauthorized)!")
                    else:
                        self.api_status = "offline"
                        if len(self.failed_queue) < self.max_queue_size:
                            self.failed_queue.append(payload)
                        print(f"❌ API Error: {res.status_code} - {res.text}")
                except requests.exceptions.RequestException as e:
                    self.api_status = "offline"
                    if len(self.failed_queue) < self.max_queue_size:
                        self.failed_queue.append(payload)
                    print(f"⚠️ Failed sending count to API: {e}. Saved to retry queue (Queued: {len(self.failed_queue)})")

            elif task_type == "heartbeat":
                heartbeat_url = self.api_url.replace("/api/count", "/api/heartbeat")
                try:
                    res = requests.post(heartbeat_url, json=payload, headers=headers, timeout=2.0)
                    if res.status_code == 200:
                        if self.api_status == "offline":
                            self.api_status = "ok"
                    elif res.status_code == 401:
                        self.api_status = "unauthorized"
                except requests.exceptions.RequestException:
                    self.api_status = "offline"

            self._telemetry_queue.task_done()

    def run(self):
        print(f"🎥 Starting Camera Processor #{self.camera_id} (Source: {self.source})...")

        if isinstance(self.source, int):
            cap = cv2.VideoCapture(self.source)
            if not cap.isOpened() and os.name == 'nt':
                cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        elif isinstance(self.source, str) and self.source.startswith(("rtsp://", "rtmp://", "http://")):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;5000000"
            cap = cv2.VideoCapture(self.source)
        else:
            cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print(f"\n❌ Gagal membuka sumber kamera: {self.source}")
            if isinstance(self.source, int):
                print("💡 PETUNJUK TROUBLESHOOTING WEBCAM:")
                print("   1. Pastikan webcam/kamera USB tidak sedang dipakai oleh aplikasi lain (Zoom, Teams, Browser, dll).")
                print("   2. Coba ganti index kamera (misal --source 0 atau --source 1).")
                print("   3. Jika tidak ada webcam fisik, Anda bisa menggunakan simulasi lalu lintas data tanpa kamera:")
                print("      python sim_test.py\n")
            elif isinstance(self.source, str) and self.source.startswith("rtsp://"):
                print("💡 PETUNJUK TROUBLESHOOTING RTSP:")
                print("   1. URL 'rtsp://admin:password@192.168.1.50:554/stream' adalah contoh tempat penampung (placeholder).")
                print("      Ganti dengan IP address, username, password, dan path RTSP asli dari IP Camera Anda.")
                print("   2. Pastikan PC Anda dan IP Camera berada dalam jaringan lokal yang sama (LAN/WiFi/VPN).")
                print("   3. Untuk pengujian cepat tanpa IP Camera fisik, gunakan webcam USB/laptop:")
                print(f"      python camera_runner.py --camera-id {self.camera_id} --source 0")
                print("   4. Atau jalankan skrip simulasi tanpa kamera sama sekali:")
                print("      python sim_test.py\n")
            else:
                print("💡 PETUNJUK TROUBLESHOOTING FILE VIDEO:")
                print("   1. Pastikan nama/path file video yang Anda masukkan benar dan file tersedia.")
                print("   2. Atau jalankan skrip simulasi tanpa kamera sama sekali: python sim_test.py\n")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

        # Calculate initial line points
        self.line_p1, self.line_p2 = calculate_line_points(
            width=frame_width,
            height=frame_height,
            orientation=self.orientation,
            position=self.position,
            custom_coords=self.custom_coords
        )
        self.line_counter = LineCrossCounter(line_p1=self.line_p1, line_p2=self.line_p2)
        current_orientation = self.orientation  # track active orientation for HUD

        if self.show_window:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        print(f"📍 Initial Line Coordinates: {self.line_p1} -> {self.line_p2}")
        print("💡 Tombol: [H] Horizontal | [V] Vertikal | [R] Reset Tengah | [Q] Keluar")

        last_heartbeat_time = 0
        self.send_heartbeat_to_api()
        mouse_callback_registered = False

        while cap.isOpened():
            now = time.time()
            if now - last_heartbeat_time >= 5.0:
                self.send_heartbeat_to_api()
                last_heartbeat_time = now

            success, frame = cap.read()
            if not success:
                print("End of video stream.")
                break

            # Run YOLOv8 Tracking specifically for 'person' (class 0)
            results = self.model.track(frame, persist=True, classes=[0], tracker=self.tracker, device=self.device, verbose=False)

            if results and results[0].boxes and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().numpy()

                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = map(int, box)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    crossing_events = self.line_counter.update_position(obj_id=int(track_id), pos=(cx, cy))

                    for event in crossing_events:
                        print(f"🚨 LINE CROSS DETECTED: Object #{event['obj_id']} ({event['direction']})")
                        self.send_count_to_api(count=1)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    cv2.putText(
                        frame,
                        f"Person #{track_id}",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2
                    )

            # Draw Virtual Line and Interactive Endpoint Handles
            cv2.line(frame, self.line_p1, self.line_p2, (0, 255, 255), 3)
            # Larger circles (radius 15) for easier mouse hit
            cv2.circle(frame, self.line_p1, 15, (0, 165, 255), -1)
            cv2.circle(frame, self.line_p2, 15, (0, 165, 255), -1)
            cv2.circle(frame, self.line_p1, 15, (255, 255, 255), 2)
            cv2.circle(frame, self.line_p2, 15, (255, 255, 255), 2)

            cv2.putText(
                frame,
                f"Line #{self.camera_id} | Drag orange dots to adjust",
                (min(self.line_p1[0], self.line_p2[0]) + 10, min(self.line_p1[1], self.line_p2[1]) - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2
            )

            # Render API Connection Badge (top right)
            if self.api_status == "ok":
                status_text = "API: OK"
                status_color = (0, 255, 0)
            elif self.api_status == "unauthorized":
                status_text = "API: 401 Unauthorized"
                status_color = (0, 0, 255)
            else:
                status_text = f"API: Offline (Queued: {len(self.failed_queue)})"
                status_color = (0, 215, 255)

            cv2.putText(frame, status_text, (frame_width - 260, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
            cv2.putText(frame, status_text, (frame_width - 260, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)

            # Keyboard shortcut hint overlay (bottom-left)
            hint_lines = [
                f"Mode: {'HORIZONTAL' if current_orientation == 'horizontal' else 'VERTICAL'}",
                "[H] Horizontal  [V] Vertikal",
                "[R] Reset Tengah  [Q] Keluar",
            ]
            for i, hint in enumerate(hint_lines):
                y_pos = frame_height - 15 - (len(hint_lines) - 1 - i) * 22
                cv2.putText(frame, hint, (10, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(frame, hint, (10, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if self.show_window:
                cv2.imshow(self.window_name, frame)

                # Register mouse callback AFTER first imshow so window is fully active
                if not mouse_callback_registered:
                    cv2.setMouseCallback(self.window_name, self._mouse_callback)
                    mouse_callback_registered = True

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("User stopped stream.")
                    break
                elif key == ord('h') or key == ord('H'):
                    # Snap line to horizontal center
                    self.line_p1, self.line_p2 = calculate_line_points(
                        frame_width, frame_height, orientation="horizontal", position=0.5)
                    self.line_counter.line_p1 = self.line_p1
                    self.line_counter.line_p2 = self.line_p2
                    current_orientation = "horizontal"
                    print(f"[H] Line diset ke HORIZONTAL tengah: {self.line_p1} -> {self.line_p2}")
                elif key == ord('v') or key == ord('V'):
                    # Snap line to vertical center
                    self.line_p1, self.line_p2 = calculate_line_points(
                        frame_width, frame_height, orientation="vertical", position=0.5)
                    self.line_counter.line_p1 = self.line_p1
                    self.line_counter.line_p2 = self.line_p2
                    current_orientation = "vertical"
                    print(f"[V] Line diset ke VERTIKAL tengah: {self.line_p1} -> {self.line_p2}")
                elif key == ord('r') or key == ord('R'):
                    # Reset line to center with current orientation
                    self.line_p1, self.line_p2 = calculate_line_points(
                        frame_width, frame_height, orientation=current_orientation, position=0.5)
                    self.line_counter.line_p1 = self.line_p1
                    self.line_counter.line_p2 = self.line_p2
                    print(f"[R] Line direset ke tengah ({current_orientation}): {self.line_p1} -> {self.line_p2}")

        cap.release()
        self.stop_worker()
        if self.show_window:
            cv2.destroyAllWindows()

