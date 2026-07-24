import pytest
from datetime import datetime
from src.db.database import Base, engine, SessionLocal
from src.db.models import Event, DailyRecord

def test_create_daily_record():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        event = Event(name="Test 3-Day Event", max_capacity=1000)
        db.add(event)
        db.commit()
        db.refresh(event)

        record = DailyRecord(
            event_id=event.id,
            date="2026-07-24",
            day_number=1,
            total_in=150,
            total_out=100,
            peak_inside=60
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        assert record.id is not None and record.id > 0
        assert record.date == "2026-07-24"
        assert record.day_number == 1
        assert record.total_in == 150
        assert record.total_out == 100
        assert record.peak_inside == 60
    finally:
        db.close()
