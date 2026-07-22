import cv2
import requests
from ultralytics import YOLO
from src.engine.counter import LineCrossCounter

class CameraStreamProcessor:
    def __init__(
        self,
        camera_id: int,
        event_id: int = 1,
        source=0,  # 0 for webcam, "rtsp://..." for RTSP camera stream, or "video.mp4"
        line_p1=(0, 240),
        line_p2=(640, 240),
        api_url="http://127.0.0.1:8000/api/count",
        model_name="yolov8n.pt",
        show_window=True
    ):
        self.camera_id = camera_id
        self.event_id = event_id
        self.source = source
        self.api_url = api_url
        self.show_window = show_window

        # Initialize YOLOv8 Model (Pretrained COCO dataset)
        self.model = YOLO(model_name)
        # Initialize Line Crossing Counter
        self.line_counter = LineCrossCounter(line_p1=line_p1, line_p2=line_p2)
        self.line_p1 = line_p1
        self.line_p2 = line_p2

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
                print(f"✅ [Kamera #{self.camera_id}] Person Detected & Counted! "
                      f"Live Inside: {summary.get('current_inside', 0)}")
            else:
                print(f"❌ API Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"⚠️ Failed to send count to API: {e}")

    def run(self):
        print(f"🎥 Starting Camera Processor for Camera ID {self.camera_id} (Source: {self.source})...")
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print(f"❌ Error: Cannot open camera source {self.source}")
            return

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("End of video stream or cannot fetch frame.")
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

                    # Update position in Line Cross Counter
                    crossing_events = self.line_counter.update_position(obj_id=int(track_id), pos=(cx, cy))

                    for event in crossing_events:
                        print(f"🚨 LINE CROSS DETECTED: Object {event['obj_id']} ({event['direction']})")
                        self.send_count_to_api(count=1)

                    # Draw Bounding Box and Centroid
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

            # Draw Counting Line (Yellow virtual line)
            cv2.line(frame, self.line_p1, self.line_p2, (0, 255, 255), 3)
            cv2.putText(
                frame,
                f"Camera #{self.camera_id} Line",
                (self.line_p1[0] + 10, self.line_p1[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            if self.show_window:
                cv2.imshow(f"AI Visitor Counter - Camera #{self.camera_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("User stopped video stream.")
                    break

        cap.release()
        if self.show_window:
            cv2.destroyAllWindows()
