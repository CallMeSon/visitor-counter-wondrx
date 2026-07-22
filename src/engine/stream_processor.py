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
        model_name="yolov8n.pt",
        show_window=True
    ):
        self.camera_id = camera_id
        self.event_id = event_id
        self.source = source
        self.orientation = orientation
        self.position = position
        self.custom_coords = custom_coords
        self.api_url = api_url
        self.show_window = show_window

        self.model = YOLO(model_name)
        self.line_p1 = (0, 240)
        self.line_p2 = (640, 240)
        self.line_counter = None
        self.dragging_point = None
        self.window_name = f"AI Visitor Counter - Camera #{self.camera_id}"

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if clicked near p1 or p2 (within 25px radius)
            dist_p1 = ((x - self.line_p1[0]) ** 2 + (y - self.line_p1[1]) ** 2) ** 0.5
            dist_p2 = ((x - self.line_p2[0]) ** 2 + (y - self.line_p2[1]) ** 2) ** 0.5
            if dist_p1 < 25:
                self.dragging_point = 1
            elif dist_p2 < 25:
                self.dragging_point = 2
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging_point:
            if self.dragging_point == 1:
                self.line_p1 = (x, y)
            elif self.dragging_point == 2:
                self.line_p2 = (x, y)
            if self.line_counter:
                self.line_counter.line_p1 = self.line_p1
                self.line_counter.line_p2 = self.line_p2
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_point = None

    def send_count_to_api(self, count: int = 1):
        payload = {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "count": count
        }
        try:
            res = requests.post(self.api_url, json=payload, timeout=2.0)
            if res.status_code == 200:
                summary = res.json().get("summary", {})
                print(f"✅ [Kamera #{self.camera_id}] Count Pushed! "
                      f"Current Inside: {summary.get('current_inside', 0)}")
            else:
                print(f"❌ API Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"⚠️ Failed sending count to API: {e}")

    def run(self):
        print(f"🎥 Starting Camera Processor #{self.camera_id} (Source: {self.source})...")
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print(f"❌ Cannot open camera source: {self.source}")
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

        if self.show_window:
            cv2.namedWindow(self.window_name)
            cv2.setMouseCallback(self.window_name, self._mouse_callback)

        print(f"📍 Initial Line Coordinates: {self.line_p1} -> {self.line_p2}")
        print("💡 Tip: Click and drag yellow endpoints with mouse to adjust line in real time!")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("End of video stream.")
                break

            # Run YOLOv8 Tracking specifically for 'person' (class 0)
            results = self.model.track(frame, persist=True, classes=[0], verbose=False)

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
            cv2.circle(frame, self.line_p1, 10, (0, 165, 255), -1)
            cv2.circle(frame, self.line_p2, 10, (0, 165, 255), -1)

            cv2.putText(
                frame,
                f"Line #{self.camera_id} (Drag Endpoints)",
                (min(self.line_p1[0], self.line_p2[0]) + 10, min(self.line_p1[1], self.line_p2[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            if self.show_window:
                cv2.imshow(self.window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("User stopped stream.")
                    break

        cap.release()
        if self.show_window:
            cv2.destroyAllWindows()
