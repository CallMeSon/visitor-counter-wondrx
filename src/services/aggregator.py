from sqlalchemy.orm import Session
from src.db.models import Event, CameraConfig, CountingLog, Snapshot

class EventAggregatorService:
    def __init__(self, db: Session, event_id: int):
        self.db = db
        self.event_id = event_id

    def record_crossing(self, camera_id: int, count: int = 1) -> CountingLog:
        camera = self.db.query(CameraConfig).filter_by(id=camera_id, event_id=self.event_id).first()
        if not camera:
            raise ValueError(f"Camera ID {camera_id} not found for Event {self.event_id}")

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

    def get_summary(self) -> dict:
        logs = self.db.query(CountingLog).filter_by(event_id=self.event_id).all()
        total_in = sum(l.count_delta for l in logs if l.role == "entry")
        total_out = sum(l.count_delta for l in logs if l.role == "exit")
        current_inside = max(0, total_in - total_out)

        return {
            "event_id": self.event_id,
            "total_in": total_in,
            "total_out": total_out,
            "current_inside": current_inside,
            "camera_counts": {
                "entry": total_in,
                "exit": total_out
            }
        }

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
