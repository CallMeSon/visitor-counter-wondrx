# Event Visitor Counter MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time event visitor counter MVP for single-day events (concerts, seminars, bazaars) tracking 7 AI camera feeds (2 entry, 5 exit) with live counter metrics, trend graphs, and historical event logs in a user-friendly dashboard.

**Architecture:** A FastAPI backend coupled with SQLite/SQLAlchemy for persistent storage and an in-memory event state aggregator for high-throughput stream counting. OpenCV and a line-crossing counter module process RTSP/video feeds to update camera line crossings, broadcasting real-time metrics over WebSocket to a single-page frontend styled according to `DESIGN.md`.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pytest, OpenCV, NumPy, HTML5/CSS3/Vanilla JS (Chart.js for trend graphs).

## Global Constraints

- Must support 7 camera roles: 2 `entry` cameras and 5 `exit` cameras.
- Live metric formula: `Current Visitors = Total In - Total Out` (clamped to min 0).
- Visual Design System: Cream background (`#FBF8F3`), Near Black text (`#020002`), Lime accent (`#FF7200` highlight), Deep Purple (`#017187`), and rounded pill navbar & cards as specified in `DESIGN.md`.
- Simple setup: standard Python dependencies without custom AI model training requirements.

---

### Task 1: Database Setup and Data Models

**Files:**
- Create: `src/db/database.py`
- Create: `src/db/models.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: None (Foundation task)
- Produces: `get_db()`, `Base`, `Event`, `CameraConfig`, `CountingLog`, `Snapshot`

- [ ] **Step 1: Write the failing test for Database and Models**

Create `tests/test_db.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base, get_db
from src.db.models import Event, CameraConfig, CountingLog, Snapshot

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_event_and_cameras(db_session):
    event = Event(name="Music Fest 2026", max_capacity=5000)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.name == "Music Fest 2026"

    cam_entry1 = CameraConfig(event_id=event.id, name="Gate A Entry", role="entry", rtsp_url="rtsp://fake/1")
    cam_exit1 = CameraConfig(event_id=event.id, name="Gate B Exit", role="exit", rtsp_url="rtsp://fake/2")
    db_session.add_all([cam_entry1, cam_exit1])
    db_session.commit()

    cameras = db_session.query(CameraConfig).filter_by(event_id=event.id).all()
    assert len(cameras) == 2
    assert cameras[0].role in ["entry", "exit"]

def test_log_and_snapshot(db_session):
    event = Event(name="Tech Expo", max_capacity=1000)
    db_session.add(event)
    db_session.commit()

    log_entry = CountingLog(event_id=event.id, camera_id=1, count_delta=1, role="entry")
    snapshot = Snapshot(event_id=event.id, total_in=10, total_out=4, current_inside=6)
    db_session.add_all([log_entry, snapshot])
    db_session.commit()

    saved_log = db_session.query(CountingLog).first()
    assert saved_log.count_delta == 1
    saved_snapshot = db_session.query(Snapshot).first()
    assert saved_snapshot.current_inside == 6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 3: Write minimal database setup and models**

Create `src/__init__.py` and `src/db/__init__.py` (empty files).

Create `src/db/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./visitor_counter.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Create `src/db/models.py`:
```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    max_capacity = Column(Integer, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    cameras = relationship("CameraConfig", back_populates="event", cascade="all, delete-orphan")
    logs = relationship("CountingLog", back_populates="event", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="event", cascade="all, delete-orphan")

class CameraConfig(Base):
    __tablename__ = "camera_configs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=True)

    event = relationship("Event", back_populates="cameras")

class CountingLog(Base):
    __tablename__ = "counting_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    camera_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    count_delta = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="logs")

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    current_inside = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="snapshots")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/db/database.py src/db/models.py tests/test_db.py
git commit -m "feat: setup database schema and models for events and camera counts"
```

---

### Task 2: Core Camera Counting Engine & Line Crossing Logic

**Files:**
- Create: `src/engine/counter.py`
- Test: `tests/test_counter.py`

**Interfaces:**
- Consumes: None (pure domain logic)
- Produces: `LineCrossCounter`, `Point`

- [ ] **Step 1: Write the failing test for line-crossing counter**

Create `tests/test_counter.py`:
```python
import pytest
from src.engine.counter import LineCrossCounter

def test_line_cross_entry():
    counter = LineCrossCounter(line_p1=(0, 100), line_p2=(200, 100), direction_vector=(0, 1))

    obj_id = 1
    events_1 = counter.update_position(obj_id=obj_id, pos=(100, 80))
    assert len(events_1) == 0

    events_2 = counter.update_position(obj_id=obj_id, pos=(100, 120))
    assert len(events_2) == 1
    assert events_2[0]["obj_id"] == 1
    assert events_2[0]["direction"] == "forward"

def test_line_cross_exit():
    counter = LineCrossCounter(line_p1=(0, 100), line_p2=(200, 100), direction_vector=(0, 1))

    obj_id = 2
    counter.update_position(obj_id=obj_id, pos=(100, 120))
    events = counter.update_position(obj_id=obj_id, pos=(100, 80))
    assert len(events) == 1
    assert events[0]["obj_id"] == 2
    assert events[0]["direction"] == "backward"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_counter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.engine'`

- [ ] **Step 3: Write minimal LineCrossCounter implementation**

Create `src/engine/__init__.py`.
Create `src/engine/counter.py`:
```python
from typing import Tuple, Dict, List, Optional

Point = Tuple[int, int]

class LineCrossCounter:
    def __init__(self, line_p1: Point, line_p2: Point, direction_vector: Point = (0, 1)):
        self.line_p1 = line_p1
        self.line_p2 = line_p2
        self.direction_vector = direction_vector
        self.history: Dict[int, List[Point]] = {}
        self.crossed_ids: set = set()

    def _cross_product(self, p1: Point, p2: Point, p3: Point) -> float:
        return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])

    def update_position(self, obj_id: int, pos: Point) -> List[Dict]:
        events = []
        if obj_id not in self.history:
            self.history[obj_id] = [pos]
            return events

        prev_pos = self.history[obj_id][-1]
        self.history[obj_id].append(pos)

        cp1 = self._cross_product(self.line_p1, self.line_p2, prev_pos)
        cp2 = self._cross_product(self.line_p1, self.line_p2, pos)

        if cp1 * cp2 < 0 and obj_id not in self.crossed_ids:
            self.crossed_ids.add(obj_id)
            direction = "forward" if cp2 > cp1 else "backward"
            events.append({
                "obj_id": obj_id,
                "direction": direction,
                "prev_pos": prev_pos,
                "curr_pos": pos
            })

        return events

    def reset_track(self, obj_id: int):
        self.history.pop(obj_id, None)
        self.crossed_ids.discard(obj_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_counter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/engine/counter.py tests/test_counter.py
git commit -m "feat: implement line-crossing detection logic for camera counter engine"
```

---

### Task 3: Event Visitor Aggregator Service

**Files:**
- Create: `src/services/aggregator.py`
- Test: `tests/test_aggregator.py`

**Interfaces:**
- Consumes: `src.db.models.Event`, `src.db.models.CameraConfig`, `src.db.models.CountingLog`
- Produces: `EventAggregatorService`, `get_summary()`, `record_crossing()`, `get_trend_history()`

- [ ] **Step 1: Write the failing test for Aggregator Service**

Create `tests/test_aggregator.py`:
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
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_aggregator_7_cameras(db_session):
    event = Event(name="Main Concert", max_capacity=2000)
    db_session.add(event)
    db_session.commit()

    cams = []
    for i in range(1, 3):
        cams.append(CameraConfig(event_id=event.id, name=f"Entry Cam {i}", role="entry"))
    for i in range(1, 6):
        cams.append(CameraConfig(event_id=event.id, name=f"Exit Cam {i}", role="exit"))
    db_session.add_all(cams)
    db_session.commit()

    service = EventAggregatorService(db_session, event.id)

    service.record_crossing(camera_id=cams[0].id, count=10)
    service.record_crossing(camera_id=cams[1].id, count=5)
    service.record_crossing(camera_id=cams[2].id, count=3)
    service.record_crossing(camera_id=cams[3].id, count=1)

    summary = service.get_summary()
    assert summary["total_in"] == 15
    assert summary["total_out"] == 4
    assert summary["current_inside"] == 11
    assert summary["camera_counts"]["entry"] == 15
    assert summary["camera_counts"]["exit"] == 4

def test_aggregator_no_negative_inside(db_session):
    event = Event(name="Small Workshop", max_capacity=100)
    db_session.add(event)
    db_session.commit()
    cam_exit = CameraConfig(event_id=event.id, name="Exit 1", role="exit")
    db_session.add(cam_exit)
    db_session.commit()

    service = EventAggregatorService(db_session, event.id)
    service.record_crossing(camera_id=cam_exit.id, count=5)

    summary = service.get_summary()
    assert summary["total_in"] == 0
    assert summary["total_out"] == 5
    assert summary["current_inside"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_aggregator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.services'`

- [ ] **Step 3: Write minimal EventAggregatorService implementation**

Create `src/services/__init__.py`.
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
        self.db.refresh(log)

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_aggregator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/services/aggregator.py tests/test_aggregator.py
git commit -m "feat: implement visitor aggregator service for 7-camera tracking and metrics"
```

---

### Task 4: FastAPI Web Server & API Endpoints + WebSocket Broadcast

**Files:**
- Create: `src/api/app.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `src.services.aggregator.EventAggregatorService`, `src.db.database.get_db`
- Produces: FastAPI REST endpoints (`/api/events`, `/api/events/{id}/summary`, `/api/events/{id}/trend`, `/api/count`) and WebSocket (`/ws/events/{id}`)

- [ ] **Step 1: Write the failing test for API endpoints**

Create `tests/test_api.py`:
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
    event = Event(id=1, name="Standard Event MVP", max_capacity=3000)
    db.add(event)
    db.commit()
    for i in range(1, 3):
        db.add(CameraConfig(id=i, event_id=1, name=f"Entry {i}", role="entry"))
    for i in range(3, 8):
        db.add(CameraConfig(id=i, event_id=1, name=f"Exit {i-2}", role="exit"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_get_event_summary():
    response = client.get("/api/events/1/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_in"] == 0
    assert data["total_out"] == 0
    assert data["current_inside"] == 0

def test_post_camera_count():
    response = client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 5})
    assert response.status_code == 200

    summary_resp = client.get("/api/events/1/summary")
    assert summary_resp.json()["current_inside"] == 5
    assert summary_resp.json()["total_in"] == 5

def test_get_trend_data():
    client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 2})
    response = client.get("/api/events/1/trend")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["current_inside"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.api'`

- [ ] **Step 3: Write minimal FastAPI Application**

Create `src/api/__init__.py`.
Create `src/api/app.py`:
```python
from typing import List, Dict
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db, engine, Base
from src.db.models import Event
from src.services.aggregator import EventAggregatorService

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Visitor Counter MVP API")

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
    events = db.query(Event).all()
    return events

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

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/app.py tests/test_api.py
git commit -m "feat: implement FastAPI endpoints and WebSocket live broadcast manager"
```

---

### Task 5: Web Dashboard Frontend Implementation

**Files:**
- Create: `src/static/index.html`
- Create: `src/static/styles.css`
- Create: `src/static/app.js`
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: `/api/events/1/summary`, `/api/events/1/trend`, `/ws/events/1`
- Produces: Responsive Dashboard with large numbers, Chart.js trends, Pill navbar, and Design Tokens (`#FBF8F3` background, `#020002` text, `#FF7200` & `#017187` accents).

- [ ] **Step 1: Write test for Static Frontend Integration**

Create `tests/test_frontend.py`:
```python
import os

def test_static_files_exist():
    assert os.path.exists("src/static/index.html")
    assert os.path.exists("src/static/styles.css")
    assert os.path.exists("src/static/app.js")

def test_css_design_tokens():
    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        content = f.read()
    assert "#FBF8F3" in content
    assert "#020002" in content
    assert "--radius-pill" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend.py -v`
Expected: FAIL with `AssertionError: assert False`

- [ ] **Step 3: Write Frontend Files (`index.html`, `styles.css`, `app.js`)**

Create directory `src/static`.

Create `src/static/index.html`:
```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Event Visitor Counter Dashboard</title>
  <link rel="stylesheet" href="styles.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <div class="container">
    <nav class="navbar-pill">
      <div class="brand">
        <span class="dot"></span> Event Counter MVP
      </div>
      <div class="event-badge">
        <span id="event-name">Konser/Seminar Live</span>
      </div>
    </nav>

    <header class="hero-section">
      <div class="badge-status">
        <span class="live-indicator"></span> LIVE UPDATING (7 CAMERAS)
      </div>
      <h1 class="headline">Jumlah Pengunjung Real-Time</h1>
    </header>

    <section class="metrics-grid">
      <div class="card card-primary">
        <div class="card-label">PENGUNJUNG SAAT INI</div>
        <div class="card-value" id="val-inside">0</div>
        <div class="card-sub">Di dalam area venue</div>
      </div>
      <div class="card">
        <div class="card-label">TOTAL MASUK</div>
        <div class="card-value accent-lime" id="val-total-in">0</div>
        <div class="card-sub">Pintu Masuk (2 Kamera)</div>
      </div>
      <div class="card">
        <div class="card-label">TOTAL KELUAR</div>
        <div class="card-value accent-purple" id="val-total-out">0</div>
        <div class="card-sub">Pintu Keluar (5 Kamera)</div>
      </div>
    </section>

    <section class="chart-section">
      <div class="card chart-card">
        <h2>Grafik Tren Pengunjung</h2>
        <div class="chart-container">
          <canvas id="trendChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <script src="app.js"></script>
</body>
</html>
```

Create `src/static/styles.css`:
```css
:root {
  --color-bg: #FBF8F3;
  --color-surface: #FFFFFF;
  --color-text: #020002;
  --color-accent-lime: #FF7200;
  --color-accent-purple: #017187;
  --color-accent-orange: #F59121;

  --radius-pill: 999px;
  --radius-card: 20px;
  --font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-family);
  padding: 24px;
}

.container {
  max-width: 1100px;
  margin: 0 auto;
}

.navbar-pill {
  background: var(--color-surface);
  border-radius: var(--radius-pill);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  margin-bottom: 40px;
}

.brand {
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  background-color: var(--color-accent-lime);
  border-radius: 50%;
  display: inline-block;
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
}

.badge-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  padding: 6px 16px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 16px;
  border: 1px solid #E5E0D8;
}

.live-indicator {
  width: 8px;
  height: 8px;
  background-color: #10B981;
  border-radius: 50%;
}

.headline {
  font-size: 48px;
  font-weight: 900;
  letter-spacing: -1px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
}

.card-primary {
  border: 2px solid var(--color-text);
}

.card-label {
  font-size: 13px;
  font-weight: 700;
  color: #666;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.card-value {
  font-size: 64px;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 8px;
}

.accent-lime { color: var(--color-accent-lime); }
.accent-purple { color: var(--color-accent-purple); }

.card-sub {
  font-size: 14px;
  color: #777;
}

.chart-card h2 {
  font-size: 20px;
  margin-bottom: 20px;
}

.chart-container {
  position: relative;
  height: 320px;
}
```

Create `src/static/app.js`:
```javascript
const EVENT_ID = 1;

let trendChart = null;

function initChart() {
  const ctx = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Pengunjung di Dalam',
          data: [],
          borderColor: '#FF7200',
          backgroundColor: 'rgba(255, 114, 0, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

async function fetchSummary() {
  try {
    const res = await fetch(`/api/events/${EVENT_ID}/summary`);
    const data = await res.json();
    updateMetrics(data);
  } catch (err) {
    console.error("Failed fetching summary:", err);
  }
}

async function fetchTrend() {
  try {
    const res = await fetch(`/api/events/${EVENT_ID}/trend`);
    const history = await res.json();
    if (trendChart) {
      trendChart.data.labels = history.map(h => new Date(h.timestamp).toLocaleTimeString());
      trendChart.data.datasets[0].data = history.map(h => h.current_inside);
      trendChart.update();
    }
  } catch (err) {
    console.error("Failed fetching trend:", err);
  }
}

function updateMetrics(summary) {
  document.getElementById('val-inside').innerText = summary.current_inside;
  document.getElementById('val-total-in').innerText = summary.total_in;
  document.getElementById('val-total-out').innerText = summary.total_out;
}

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/events/${EVENT_ID}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateMetrics(data);
    fetchTrend();
  };

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  initChart();
  fetchSummary();
  fetchTrend();
  initWebSocket();
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css src/static/app.js tests/test_frontend.py
git commit -m "feat: implement web dashboard UI with DESIGN.md styling and live Chart.js integration"
```

---

### Task 6: End-to-End Simulation & Verification Test

**Files:**
- Create: `tests/test_e2e_simulation.py`

**Interfaces:**
- Consumes: All modules (`src.api.app`, `src.services.aggregator`, `src.db.models`)
- Produces: Simulated 7-camera stream inputs to verify system stability and DoD criteria.

- [ ] **Step 1: Write E2E Simulation Test**

Create `tests/test_e2e_simulation.py`:
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
client = TestClient(app)

def test_full_7_camera_event_flow():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    event = Event(id=1, name="Full Concert Test", max_capacity=1000)
    db.add(event)
    db.commit()

    entry_cams = [CameraConfig(id=1, event_id=1, name="Entry 1", role="entry"), CameraConfig(id=2, event_id=1, name="Entry 2", role="entry")]
    exit_cams = [CameraConfig(id=i, event_id=1, name=f"Exit {i-2}", role="exit") for i in range(3, 8)]
    db.add_all(entry_cams + exit_cams)
    db.commit()

    client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 100})
    client.post("/api/count", json={"event_id": 1, "camera_id": 2, "count": 50})

    for exit_cam in exit_cams:
        client.post("/api/count", json={"event_id": 1, "camera_id": exit_cam.id, "count": 6})

    res = client.get("/api/events/1/summary")
    data = res.json()
    assert data["total_in"] == 150
    assert data["total_out"] == 30
    assert data["current_inside"] == 120

    trend_res = client.get("/api/events/1/trend")
    assert len(trend_res.json()) == 7

    Base.metadata.drop_all(bind=engine)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_e2e_simulation.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_simulation.py
git commit -m "test: add E2E simulation test verifying 7-camera visitor count pipeline"
```
