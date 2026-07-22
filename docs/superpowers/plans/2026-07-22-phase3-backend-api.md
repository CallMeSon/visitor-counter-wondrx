# Phase 3: Core Aggregator & Backend API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the multi-camera visitor state aggregator service and FastAPI REST/WebSocket endpoints to record line crossings, calculate live visitor counts, and broadcast real-time metrics.

**Architecture:** An `EventAggregatorService` consuming database models (`Event`, `CameraConfig`, `CountingLog`, `Snapshot`) and computing `current_inside = max(0, total_in - total_out)`. FastAPI exposes HTTP REST routes and WebSocket channels via an active `ConnectionManager`.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pytest, FastAPI TestClient.

## Global Constraints

- Aggregates up to 7 cameras per event (2 entry, 5 exit roles).
- Real-time updates pushed over WebSocket (`/ws/events/{id}`).
- Metric formula: `current_inside = max(0, total_in - total_out)`.

---

### Task 1: Visitor Aggregator Service

**Files:**
- Create: `src/services/__init__.py`
- Create: `src/services/aggregator.py`
- Test: `tests/test_aggregator_service.py`

**Interfaces:**
- Consumes: `src.db.models.Event`, `src.db.models.CameraConfig`
- Produces: `EventAggregatorService`, `record_crossing()`, `get_summary()`, `get_trend_history()`

- [x] **Step 1: Write the failing test for Aggregator Service**

Create `tests/test_aggregator_service.py`:
```python
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

    # Add 2 Entry and 5 Exit cameras
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_aggregator_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.services'`

- [x] **Step 3: Write minimal EventAggregatorService implementation**

Create empty file `src/services/__init__.py`.

Create `src/services/aggregator.py`:
```python
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
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_aggregator_service.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/services/__init__.py src/services/aggregator.py tests/test_aggregator_service.py
git commit -m "feat(service): implement EventAggregatorService for metric calculation"
```

---

### Task 2: FastAPI Endpoints & WebSocket Manager

**Files:**
- Create: `src/api/__init__.py`
- Create: `src/api/app.py`
- Test: `tests/test_api_endpoints.py`

**Interfaces:**
- Consumes: `src.services.aggregator.EventAggregatorService`, `src.db.database.get_db`
- Produces: FastAPI REST routes and WebSocket Broadcast endpoint `/ws/events/{id}`

- [x] **Step 1: Write the failing test for API endpoints**

Create `tests/test_api_endpoints.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.app import app
from src.db.database import Base, get_db
from src.db.models import Event, CameraConfig

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_endpoints.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.api'`

- [x] **Step 3: Write minimal FastAPI application**

Create empty file `src/api/__init__.py`.

Create `src/api/app.py`:
```python
from typing import List, Dict
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db, engine, Base
from src.db.models import Event
from src.services.aggregator import EventAggregatorService

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Visitor Counter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, event_id: int, websocket: WebSocket):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, event_id: int, websocket: WebSocket):
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)

    async def broadcast(self, event_id: int, message: dict):
        if event_id in self.active_connections:
            for connection in self.active_connections[event_id]:
                await connection.send_json(message)

manager = ConnectionManager()

class CountPayload(BaseModel):
    event_id: int
    camera_id: int
    count: int = 1

@app.get("/api/events")
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()

@app.get("/api/events/{event_id}/summary")
def get_summary(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    service = EventAggregatorService(db, event_id)
    return service.get_summary()

@app.get("/api/events/{event_id}/trend")
def get_trend(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    service = EventAggregatorService(db, event_id)
    return service.get_trend_history()

@app.post("/api/count")
async def record_count(payload: CountPayload, db: Session = Depends(get_db)):
    service = EventAggregatorService(db, payload.event_id)
    try:
        service.record_crossing(payload.camera_id, payload.count)
        summary = service.get_summary()
        await manager.broadcast(payload.event_id, summary)
        return {"status": "success", "summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/events/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: int):
    await manager.connect(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(event_id, websocket)
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_endpoints.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/api/__init__.py src/api/app.py tests/test_api_endpoints.py
git commit -m "feat(api): implement FastAPI endpoints and WebSocket broadcaster"
```
