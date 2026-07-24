import pytest
from datetime import datetime, timezone, timedelta
from src.db.database import Base, engine, SessionLocal
from src.db.models import Event, CameraConfig, CountingLog, DailyRecord, utc_now
from src.services.aggregator import EventAggregatorService

def test_daily_upsert_and_analytics_calculation():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        event = Event(name="Multi-Day Test Event", max_capacity=5000)
        db.add(event)
        db.commit()
        db.refresh(event)

        entry_cam = CameraConfig(event_id=event.id, name="Pintu Masuk", role="entry")
        exit_cam = CameraConfig(event_id=event.id, name="Pintu Keluar", role="exit")
        db.add_all([entry_cam, exit_cam])
        db.commit()
        db.refresh(entry_cam)
        db.refresh(exit_cam)

        service = EventAggregatorService(db, event.id)

        # 1. Record crossing today
        service.record_crossing(entry_cam.id, count=15)
        service.record_crossing(exit_cam.id, count=5)

        today_str = utc_now().strftime("%Y-%m-%d")
        daily_rec = db.query(DailyRecord).filter_by(event_id=event.id, date=today_str).first()
        assert daily_rec is not None
        assert daily_rec.total_in == 15
        assert daily_rec.total_out == 5
        assert daily_rec.peak_inside == 15

        # 2. Verify summary is scoped to today
        summary = service.get_summary()
        assert summary["total_in"] == 15
        assert summary["total_out"] == 5
        assert summary["current_inside"] == 10

        # 3. Test get_analytics_summary()
        analytics = service.get_analytics_summary()
        assert "overall_stats" in analytics
        assert "daily_breakdown" in analytics
        assert "hourly_distribution" in analytics
        assert analytics["overall_stats"]["total_visitors_all_days"] == 15
        assert len(analytics["daily_breakdown"]) >= 1
        assert analytics["daily_breakdown"][0]["date"] == today_str
        assert analytics["daily_breakdown"][0]["total_in"] == 15
    finally:
        db.close()
