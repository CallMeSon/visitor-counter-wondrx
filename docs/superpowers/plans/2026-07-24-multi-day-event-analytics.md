# Multi-Day Event Daily Recording & Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automatic per-day visitor recording in SQLite/SQLAlchemy, scoped live counter (resets to 0 daily), and a professional multi-day Analytics Page (`analytics.html`) consistent with [DESIGN.md](file:///c:/visitor-counter/DESIGN.md) without emojis.

**Architecture:** 
- Add `DailyRecord` table to persist per-day visitor totals (`total_in`, `total_out`, `peak_inside`).
- Update `EventAggregatorService` to upsert daily records on every crossing, scope live dashboard metrics to current date logs, and calculate overall multi-day analytics (total visitors across all days, peak hour overall, busiest day).
- Add FastAPI endpoint `GET /api/events/{event_id}/analytics`.
- Build `analytics.html` and `analytics.js` following the warm, editorial design system of `DESIGN.md` using clean SVG indicators / badges (no emojis).

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy 2.0, Chart.js, HTML5, Vanilla CSS, Pytest.

## Global Constraints

- **Design System:** Follow [DESIGN.md](file:///c:/visitor-counter/DESIGN.md) palette (`#FBF8F3` bg, `#FFFFFF` card, `#020002` text, `#FF7200` lime accent, `#017187` purple accent).
- **No Emojis:** Strictly DO NOT use emojis in UI headings, card titles, badges, or labels. Use clean text labels and subtle SVG dot status indicators.
- **TDD:** Write unit tests first for backend service and API endpoint before implementation code.

---

### Task 1: Database Schema & Migration for `DailyRecord`

**Files:**
- Modify: `src/db/models.py`
- Modify: `src/api/app.py`
- Test: `tests/test_daily_records_schema.py`

**Interfaces:**
- Produces: `DailyRecord` SQLAlchemy model class in `src.db.models`.

- [ ] **Step 1: Write failing test for `DailyRecord` model**

Create `tests/test_daily_records_schema.py`:
```python
from datetime import datetime
from src.db.database import Base, engine, SessionLocal
from src.db.models import Event, DailyRecord, utc_now

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

        assert record.id is not null or record.id > 0
        assert record.date == "2026-07-24"
        assert record.day_number == 1
        assert record.total_in == 150
        assert record.peak_inside == 60
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_daily_records_schema.py`
Expected: FAIL with `ImportError: cannot import name 'DailyRecord' from 'src.db.models'`.

- [ ] **Step 3: Implement `DailyRecord` model in `src/db/models.py`**

In `src/db/models.py`:
```python
class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    date = Column(String, nullable=False, index=True)      # Format: "YYYY-MM-DD"
    day_number = Column(Integer, nullable=False)           # Day 1, 2, 3...
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    peak_inside = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utc_now)

    event = relationship("Event", back_populates="daily_records")
```
Also add `daily_records` relationship to `Event`:
```python
    daily_records = relationship("DailyRecord", back_populates="event", cascade="all, delete-orphan")
```

In `src/api/app.py`, update `run_migrations()` if needed:
```python
def run_migrations():
    """Tambahkan migration / create table jika belum ada."""
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_daily_records_schema.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/db/models.py src/api/app.py tests/test_daily_records_schema.py
git commit -m "feat(db): add DailyRecord model and schema migration"
```

---

### Task 2: Aggregator Service Auto-Reset & Analytics Calculation

**Files:**
- Modify: `src/services/aggregator.py`
- Test: `tests/test_aggregator_multiday.py`

**Interfaces:**
- Consumes: `DailyRecord`, `CountingLog` from `src.db.models`
- Produces: `EventAggregatorService.get_analytics_summary() -> dict`, updated `record_crossing()` and `get_summary()`.

- [ ] **Step 1: Write failing tests for multi-day aggregator logic**

Create `tests/test_aggregator_multiday.py`:
```python
from datetime import datetime, timezone, timedelta
from src.db.database import Base, engine, SessionLocal
from src.db.models import Event, CameraConfig, CountingLog, utc_now
from src.services.aggregator import EventAggregatorService

def test_daily_upsert_and_scoped_summary():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        event = Event(name="Multi-Day Test Event", max_capacity=5000)
        db.add(event)
        db.commit()
        
        cam = CameraConfig(event_id=event.id, name="Entry 1", role="entry")
        db.add(cam)
        db.commit()

        service = EventAggregatorService(db, event.id)

        # Record crossings today
        service.record_crossing(cam.id, count=10)
        
        summary = service.get_summary()
        assert summary["total_in"] == 10

        analytics = service.get_analytics_summary()
        assert analytics["overall_stats"]["total_visitors_all_days"] == 10
        assert len(analytics["daily_breakdown"]) >= 1
        assert analytics["daily_breakdown"][0]["total_in"] == 10
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_aggregator_multiday.py`
Expected: FAIL with `AttributeError: 'EventAggregatorService' object has no attribute 'get_analytics_summary'`.

- [ ] **Step 3: Implement multi-day aggregator logic**

In `src/services/aggregator.py`:
1. In `record_crossing()`:
   - Extract today's date string `today_str = utc_now().strftime("%Y-%m-%d")`.
   - Find or create `DailyRecord` for `(self.event_id, today_str)`.
   - Update `total_in` / `total_out` and calculate `peak_inside`.
2. Implement `get_analytics_summary()`:
   - Calculate total visitors across all days from `DailyRecord`.
   - Find peak hour overall by grouping `CountingLog` entries (where `role == 'entry'`) by hour (`strftime("%H:00")`).
   - Find busiest day.
   - Return dictionary containing `overall_stats`, `daily_breakdown`, and `hourly_distribution`.
3. Update `get_summary()`:
   - Filter `CountingLog` entries to current date (`YYYY-MM-DD`) for today's live total count.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_aggregator_multiday.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/aggregator.py tests/test_aggregator_multiday.py
git commit -m "feat(services): implement daily upsert and multi-day analytics calculation"
```

---

### Task 3: Analytics API Endpoint

**Files:**
- Modify: `src/api/app.py`
- Test: `tests/test_analytics_api.py`

**Interfaces:**
- Produces: `GET /api/events/{event_id}/analytics` endpoint returning analytics payload.

- [ ] **Step 1: Write failing test for Analytics API endpoint**

Create `tests/test_analytics_api.py`:
```python
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_get_event_analytics():
    response = client.get("/api/events/1/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "overall_stats" in data
    assert "daily_breakdown" in data
    assert "hourly_distribution" in data
    assert "total_visitors_all_days" in data["overall_stats"]
    assert "peak_hour_overall" in data["overall_stats"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_analytics_api.py`
Expected: FAIL with HTTP 404.

- [ ] **Step 3: Implement `GET /api/events/{event_id}/analytics` in `src/api/app.py`**

In `src/api/app.py`:
```python
@app.get("/api/events/{event_id}/analytics")
def get_analytics(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    service = EventAggregatorService(db, event_id)
    return service.get_analytics_summary()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_analytics_api.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/app.py tests/test_analytics_api.py
git commit -m "feat(api): add GET /api/events/{event_id}/analytics endpoint"
```

---

### Task 4: UI Navigation & Analytics Page (`index.html` & `analytics.html`)

**Files:**
- Modify: `src/static/index.html`
- Create: `src/static/analytics.html`
- Create: `src/static/analytics.js`
- Modify: `src/static/styles.css`

**Design Requirements (Strict adherence to [DESIGN.md](file:///c:/visitor-counter/DESIGN.md)):**
- Palette: `#FBF8F3` body, `#FFFFFF` card, `#020002` text, `#FF7200` accent, `#017187` secondary.
- **NO EMOJIS**. Use text titles, uppercase category labels, and dot indicators (`.dot-status`).
- Clean navigation button in `navbar-pill`: "Analytics & Histori".

- [ ] **Step 1: Update `index.html` with navbar navigation link**

In `src/static/index.html`:
Add navigation link inside `.navbar-right`:
```html
<a href="analytics.html" class="nav-link-btn">Analytics & Histori</a>
```

- [ ] **Step 2: Create `analytics.html` page structure (No Emojis)**

Create `src/static/analytics.html`:
- Navbar pill matching `index.html`.
- Top metrics grid:
  - Card 1: TOTAL PENGUNJUNG (SEMUA HARI)
  - Card 2: JAM PALING RAMAI (AKUMULASI)
  - Card 3: HARI TERAMAI
- Table Section: Data Histori Per Hari (`Hari`, `Tanggal`, `Total Masuk`, `Total Keluar`, `Puncak Pengunjung`).
- Chart Section: Perbandingan Pengunjung Harian (Bar Chart) & Distribusi Kedatangan Per Jam (Line Chart).

- [ ] **Step 3: Create `analytics.js` for data fetching & rendering**

Create `src/static/analytics.js`:
- Fetch data from `/api/events/1/analytics`.
- Render summary cards text values.
- Render table rows dynamically.
- Initialize Chart.js bar chart for daily comparison & line chart for hourly arrival distribution.

- [ ] **Step 4: Update `styles.css` with table & nav button styles**

In `src/static/styles.css`:
- Add `.nav-link-btn`, `.analytics-table`, `.table-card`, `.nav-back` styles matching `DESIGN.md`.

- [ ] **Step 5: Run full test suite and manual verification**

Run: `pytest`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/static/index.html src/static/analytics.html src/static/analytics.js src/static/styles.css
git commit -m "feat(ui): add professional multi-day analytics page without emojis"
```
