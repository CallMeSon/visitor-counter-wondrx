from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.db.models import Event, CameraConfig, CountingLog, Snapshot, DailyRecord, utc_now

class EventAggregatorService:
    def __init__(self, db: Session, event_id: int):
        self.db = db
        self.event_id = event_id

    def _upsert_daily_record(self, role: str, count: int):
        now = utc_now()
        today_str = now.strftime("%Y-%m-%d")

        existing_records = (
            self.db.query(DailyRecord)
            .filter_by(event_id=self.event_id)
            .order_by(DailyRecord.date.asc())
            .all()
        )
        record_map = {r.date: r for r in existing_records}

        if today_str in record_map:
            daily_rec = record_map[today_str]
        else:
            day_number = len(existing_records) + 1
            daily_rec = DailyRecord(
                event_id=self.event_id,
                date=today_str,
                day_number=day_number,
                total_in=0,
                total_out=0,
                peak_inside=0
            )
            self.db.add(daily_rec)
            self.db.commit()
            self.db.refresh(daily_rec)

        if role == "entry":
            daily_rec.total_in += count
        elif role == "exit":
            daily_rec.total_out += count

        today_inside = max(0, daily_rec.total_in - daily_rec.total_out)
        if today_inside > daily_rec.peak_inside:
            daily_rec.peak_inside = today_inside

        daily_rec.updated_at = now
        self.db.commit()

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

        self._upsert_daily_record(camera.role, count)

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
        now = utc_now()
        today_str = now.strftime("%Y-%m-%d")

        all_logs = self.db.query(CountingLog).filter_by(event_id=self.event_id).all()
        today_logs = [l for l in all_logs if l.timestamp and l.timestamp.strftime("%Y-%m-%d") == today_str]

        cameras = self.db.query(CameraConfig).filter_by(event_id=self.event_id).order_by(CameraConfig.id.asc()).all()

        total_in = sum(l.count_delta for l in today_logs if l.role == "entry")
        total_out = sum(l.count_delta for l in today_logs if l.role == "exit")
        current_inside = max(0, total_in - total_out)

        cameras_list = []
        active_camera_count = 0

        for cam in cameras:
            cam_today_logs = [l for l in today_logs if l.camera_id == cam.id]
            cam_count = sum(l.count_delta for l in cam_today_logs)

            is_connected = False
            if cam.last_active_at:
                delta_sec = (now - cam.last_active_at).total_seconds()
                is_connected = delta_sec < 30

            if is_connected:
                active_camera_count += 1

            cameras_list.append({
                "id": cam.id,
                "name": cam.name,
                "role": cam.role,
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

    def get_analytics_summary(self) -> dict:
        daily_records = (
            self.db.query(DailyRecord)
            .filter_by(event_id=self.event_id)
            .order_by(DailyRecord.day_number.asc())
            .all()
        )

        all_logs = self.db.query(CountingLog).filter_by(event_id=self.event_id).all()
        entry_logs = [l for l in all_logs if l.role == "entry"]

        total_visitors = sum(r.total_in for r in daily_records)

        hour_counts = {}
        for l in entry_logs:
            if l.timestamp:
                hour_str = l.timestamp.strftime("%H:00")
                hour_counts[hour_str] = hour_counts.get(hour_str, 0) + l.count_delta

        peak_hour_str = "-"
        if hour_counts:
            busiest_h = max(hour_counts, key=hour_counts.get)
            h_int = int(busiest_h.split(":")[0])
            next_h_str = f"{(h_int + 1) % 24:02d}:00"
            peak_hour_str = f"{busiest_h} - {next_h_str}"

        busiest_day_str = "-"
        if daily_records:
            busiest_rec = max(daily_records, key=lambda r: r.total_in)
            busiest_day_str = f"Hari {busiest_rec.day_number} ({busiest_rec.date})"

        daily_breakdown = [
            {
                "day_number": r.day_number,
                "date": r.date,
                "total_in": r.total_in,
                "total_out": r.total_out,
                "peak_inside": r.peak_inside
            }
            for r in daily_records
        ]

        hourly_distribution = [
            {"hour": f"{h:02d}:00", "count": hour_counts.get(f"{h:02d}:00", 0)}
            for h in range(24)
        ]

        return {
            "event_id": self.event_id,
            "overall_stats": {
                "total_visitors_all_days": total_visitors,
                "peak_hour_overall": peak_hour_str,
                "busiest_day": busiest_day_str,
                "total_days_active": len(daily_records)
            },
            "daily_breakdown": daily_breakdown,
            "hourly_distribution": hourly_distribution
        }

    def reset_counter(self) -> dict:
        self.db.query(CountingLog).filter_by(event_id=self.event_id).delete()
        self.db.query(Snapshot).filter_by(event_id=self.event_id).delete()
        self.db.query(DailyRecord).filter_by(event_id=self.event_id).delete()
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

