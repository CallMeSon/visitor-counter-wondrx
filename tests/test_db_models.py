import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.database import Base
from src.db.models import Event, CameraConfig, CountingLog, Snapshot

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

def test_event_and_camera_relationship(db_session):
    event = Event(name="Grand Concert", max_capacity=5000)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    cam1 = CameraConfig(event_id=event.id, name="Gate 1 Entry", role="entry")
    cam2 = CameraConfig(event_id=event.id, name="Gate 2 Exit", role="exit")
    db_session.add_all([cam1, cam2])
    db_session.commit()

    assert len(event.cameras) == 2
    assert event.cameras[0].role in ["entry", "exit"]

def test_log_and_snapshot_creation(db_session):
    event = Event(name="Tech Expo", max_capacity=1000)
    db_session.add(event)
    db_session.commit()

    log = CountingLog(event_id=event.id, camera_id=1, role="entry", count_delta=1)
    snapshot = Snapshot(event_id=event.id, total_in=10, total_out=3, current_inside=7)
    db_session.add_all([log, snapshot])
    db_session.commit()

    assert log.id is not None
    assert snapshot.current_inside == 7
