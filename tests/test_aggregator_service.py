import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.database import Base
from src.db.models import Event, CameraConfig
from src.services.aggregator import EventAggregatorService

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_aggregator_7_cameras_calculation(db_session):
    event = Event(name="Music Concert", max_capacity=5000)
    db_session.add(event)
    db_session.commit()

    entry_1 = CameraConfig(event_id=event.id, name="Entry 1", role="entry")
    entry_2 = CameraConfig(event_id=event.id, name="Entry 2", role="entry")
    exits = [CameraConfig(event_id=event.id, name=f"Exit {i}", role="exit") for i in range(1, 6)]
    db_session.add_all([entry_1, entry_2] + exits)
    db_session.commit()

    service = EventAggregatorService(db_session, event.id)
    service.record_crossing(camera_id=entry_1.id, count=25)
    service.record_crossing(camera_id=entry_2.id, count=15)
    service.record_crossing(camera_id=exits[0].id, count=8)

    summary = service.get_summary()
    assert summary["total_in"] == 40
    assert summary["total_out"] == 8
    assert summary["current_inside"] == 32
