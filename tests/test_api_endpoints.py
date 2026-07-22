import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.db.database import Base, get_db
from src.db.models import Event, CameraConfig

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    event = Event(id=1, name="Seminar Utama", max_capacity=2000)
    db.add(event)
    db.commit()
    db.add(CameraConfig(id=1, event_id=1, name="Pintu 1", role="entry"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_api_summary_and_count():
    res_init = client.get("/api/events/1/summary")
    assert res_init.status_code == 200
    assert res_init.json()["current_inside"] == 0

    res_post = client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 5})
    assert res_post.status_code == 200

    res_updated = client.get("/api/events/1/summary")
    assert res_updated.json()["current_inside"] == 5

    res_reset = client.post("/api/events/1/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["summary"]["current_inside"] == 0

