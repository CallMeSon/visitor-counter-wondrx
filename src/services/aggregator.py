from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.db.models import Event, CameraConfig, CountingLog, Snapshot, utc_now

class EventAggregatorService:
    def __init__(self, db: Session, event_id: int):
        self.db = db
        self.event_id = event_id

    def record_crossing(self, camera_id: int, count: int = 1) -> CountingLog:
        camera = self.db.query(CameraConfig).filter_by(id=camera_id, event_id=self.event_id).first()
        if not camera:
            raise ValueError(f"Camera ID {camera_id} not found for Event {self.event_id}")

        camera.last_active_at = utc_now()
        log = CountingLog(
            event_id=self.event_id,
            camera_id=camera_id,
            role=camera.role,
            count_delta=count
        )
        self.db.add(log)
        self.db.commit()

        summary = self.get_summary()
        snapshot = Snapshot(
            event_id=self.event_id,
            total_in=summary["total_in"],
            total_out=summary["total_out"],
            current_inside=summary["current_inside"]
        )
        self.db.add(snapshot)
        self.db.commit()

        return log

    def record_heartbeat(self, camera_id: int):
        camera = self.db.query(CameraConfig).filter_by(id=camera_id, event_id=self.event_id).first()
        if camera:
            camera.last_active_at = utc_now()
            self.db.commit()
        return self.get_summary()

    def get_summary(self) -> dict:
        logs = self.db.query(CountingLog).filter_by(event_id=self.event_id).all()
        cameras = self.db.query(CameraConfig).filter_by(event_id=self.event_id).order_by(CameraConfig.id.asc()).all()

        total_in = sum(l.count_delta for l in logs if l.role == "entry")
        total_out = sum(l.count_delta for l in logs if l.role == "exit")
        current_inside = max(0, total_in - total_out)

        now = utc_now()
        cameras_list = []
        active_camera_count = 0

        for cam in cameras:
            cam_logs = [l for l in logs if l.camera_id == cam.id]
            cam_count = sum(l.count_delta for l in cam_logs)
            
            is_connected = False
            if cam.last_active_at:
                delta_sec = (now - cam.last_active_at).total_seconds()
                is_connected = delta_sec < 30  # Active in last 30s

            if is_connected:
                active_camera_count += 1

            cameras_list.append({
                "id": cam.id,
                "name": cam.name,
                "role": cam.role,  # "entry" or "exit"
                "role_label": "Masuk (Entry)" if cam.role == "entry" else "Keluar (Exit)",
                "count": cam_count,
                "is_connected": is_connected,
                "status": "Connected" if is_connected else "Standby",
                "last_active": cam.last_active_at.isoformat() if cam.last_active_at else None
            })

        return {
            "event_id": self.event_id,
            "total_in": total_in,
            "total_out": total_out,
            "current_inside": current_inside,
            "total_cameras": len(cameras),
            "connected_cameras": active_camera_count,
            "cameras": cameras_list,
            "camera_counts": {
                "entry": total_in,
                "exit": total_out
            }
        }

    def reset_counter(self) -> dict:
        self.db.query(CountingLog).filter_by(event_id=self.event_id).delete()
        self.db.query(Snapshot).filter_by(event_id=self.event_id).delete()
        initial_snapshot = Snapshot(
            event_id=self.event_id,
            total_in=0,
            total_out=0,
            current_inside=0
        )
        self.db.add(initial_snapshot)
        self.db.commit()
        return self.get_summary()

    def get_trend_history(self, limit: int = 50) -> list:
        snapshots = (
            self.db.query(Snapshot)
            .filter_by(event_id=self.event_id)
            .order_by(Snapshot.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "total_in": s.total_in,
                "total_out": s.total_out,
                "current_inside": s.current_inside
            }
            for s in snapshots
        ]
