# Phase 1: Database & Data Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the foundational SQLite database configuration, SQLAlchemy ORM models, and CRUD helper utilities for managing events, camera roles, count logs, and trend snapshots.

**Architecture:** A lightweight SQLite database initialized via SQLAlchemy ORM with model relationships linking Events to CameraConfigs (entry/exit roles), CountingLogs, and Snapshots.

**Tech Stack:** Python 3.10+, SQLAlchemy 2.0+, SQLite3, Pytest.

## Global Constraints

- Must support 7 camera configurations per event (2 entry, 5 exit roles).
- SQLite file location: `./visitor_counter.db` for runtime, `sqlite:///:memory:` for unit testing.
- Explicit cascade rules (`all, delete-orphan`) on event relationship models.

---

### Task 1: Database Connection Setup

**Files:**
- Create: `src/__init__.py`
- Create: `src/db/__init__.py`
- Create: `src/db/database.py`
- Test: `tests/test_database_init.py`

**Interfaces:**
- Consumes: None
- Produces: `DATABASE_URL`, `engine`, `SessionLocal`, `Base`, `get_db()`

- [x] **Step 1: Write the failing test for Database Connection**

Create `tests/test_database_init.py`:
```python
import pytest
from sqlalchemy import text
from src.db.database import Base, engine, SessionLocal, get_db

def test_database_engine_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_get_db_generator():
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    try:
        next(db_gen)
    except StopIteration:
        pass
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_database_init.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src'`

- [x] **Step 3: Write minimal database setup implementation**

Create empty files `src/__init__.py` and `src/db/__init__.py`.

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

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_database_init.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/__init__.py src/db/__init__.py src/db/database.py tests/test_database_init.py
git commit -m "feat(db): initialize SQLAlchemy engine and session dependency"
```

---

### Task 2: Data Models (Event, CameraConfig, CountingLog, Snapshot)

**Files:**
- Create: `src/db/models.py`
- Test: `tests/test_db_models.py`

**Interfaces:**
- Consumes: `src.db.database.Base`
- Produces: `Event`, `CameraConfig`, `CountingLog`, `Snapshot`

- [x] **Step 1: Write the failing test for ORM models**

Create `tests/test_db_models.py`:
```python
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Event' from 'src.db.models'`

- [x] **Step 3: Write minimal models implementation**

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
    role = Column(String, nullable=False)  # "entry" or "exit"
    rtsp_url = Column(String, nullable=True)

    event = relationship("Event", back_populates="cameras")

class CountingLog(Base):
    __tablename__ = "counting_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    camera_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # "entry" or "exit"
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

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db_models.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/db/models.py tests/test_db_models.py
git commit -m "feat(db): define Event, CameraConfig, CountingLog, and Snapshot ORM models"
```
