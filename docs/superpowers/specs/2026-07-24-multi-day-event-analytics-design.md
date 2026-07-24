# Multi-Day Event Daily Recording & Analytics Design Spec

**Date:** 2026-07-24  
**Status:** Approved  
**Scope:** Database Schema, Aggregator Service, Analytics API, and Frontend Analytics Page  

---

## 1. Overview & Business Intent

For multi-day events (e.g., a 3-day concert/bazar/seminar), the visitor counting system needs to:
1. Automatically group and persist visitor records on a **per-day basis** (based on calendar date).
2. Start the **live counter from 0 at the beginning of each new day** (assuming the venue is cleared at night).
3. Provide a dedicated **Analytics & Histori Page** (`analytics.html`) allowing event organizers to review:
   - Total visitors across all days (accumulated).
   - Peak hour overall (jam paling ramai akumulasi).
   - Busiest day.
   - Per-day breakdown (Total In, Total Out, Peak Occupancy).
   - Hourly visitor arrival distribution.

---

## 2. Database Design Changes

### New Table: `daily_records`
Location: [src/db/models.py](file:///c:/visitor-counter/src/db/models.py)

```python
class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    date = Column(String, nullable=False, index=True)      # ISO Format: "YYYY-MM-DD"
    day_number = Column(Integer, nullable=False)           # Relative day index: 1, 2, 3...
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    peak_inside = Column(Integer, default=0)              # Maximum concurrent visitors inside on this date
    updated_at = Column(DateTime, default=utc_now)
```

Relationship:
- `Event` has `daily_records = relationship("DailyRecord", back_populates="event", cascade="all, delete-orphan")`

---

## 3. Service Layer Specifications

Location: [src/services/aggregator.py](file:///c:/visitor-counter/src/services/aggregator.py)

### 3.1 Automatic Daily Upsert & Live Counter Scoping
- When `record_crossing(camera_id, count)` is called:
  1. Determine current UTC/local date string `date_str` (`YYYY-MM-DD`).
  2. Compute `day_number` based on the event's creation date or first log date.
  3. Upsert the `DailyRecord` entry for `(event_id, date_str)`:
     - Increment `total_in` or `total_out`.
     - Calculate current day's inside count: `today_inside = max(0, total_in - total_out)`.
     - Update `peak_inside = max(peak_inside, today_inside)`.
  4. Scope `get_summary()` live counter to **today's logs** (`timestamp >= today_start`):
     - `today_total_in` = sum of `count_delta` where `role == 'entry'` and `date == today`.
     - `today_total_out` = sum of `count_delta` where `role == 'exit'` and `date == today`.
     - `current_inside` = `max(0, today_total_in - today_total_out)`.

### 3.2 Analytics Calculation Method
- `get_analytics_summary()`:
  1. **Overall Total Visitors:** Sum of `total_in` across all `daily_records` for the event.
  2. **Peak Hour Overall:** Group all `CountingLog` entries (with `role == 'entry'`) by hour of day `HH:00` (e.g. 14:00 - 15:00) to find the hour with the highest total arrivals across all days.
  3. **Busiest Day:** Filter `daily_records` for max `total_in`.
  4. **Daily Breakdown List:** Array of all `DailyRecord` entries ordered by `date ASC`.
  5. **Hourly Distribution:** Array of `{ hour: "HH:00", count: N }` for chart plotting.

---

## 4. API Endpoints Specification

Location: [src/api/app.py](file:///c:/visitor-counter/src/api/app.py)

### 1. `GET /api/events/{event_id}/summary`
- Response updated to include current date stats:
  - `total_in` (today), `total_out` (today), `current_inside` (today).
  - `event_total_in_all_days` (total overall).

### 2. `GET /api/events/{event_id}/analytics`
- Response Payload:
```json
{
  "event_id": 1,
  "overall_stats": {
    "total_visitors_all_days": 12450,
    "peak_hour_overall": "15:00 - 16:00",
    "busiest_day": "Hari 2 (2026-07-25)",
    "total_days_active": 3
  },
  "daily_breakdown": [
    {
      "day_number": 1,
      "date": "2026-07-24",
      "total_in": 3800,
      "total_out": 3750,
      "peak_inside": 450
    },
    ...
  ],
  "hourly_distribution": [
    { "hour": "08:00", "count": 120 },
    { "hour": "09:00", "count": 450 },
    ...
  ]
}
```

---

## 5. Frontend & UI Design

### 5.1 Main Dashboard Navigation ([src/static/index.html](file:///c:/visitor-counter/src/static/index.html))
- Add navigation link in the top bar: **"📊 Analytics & Histori"** pointing to `/analytics.html`.

### 5.2 Analytics Page ([src/static/analytics.html](file:///c:/visitor-counter/src/static/analytics.html)) & Logic ([src/static/analytics.js](file:///c:/visitor-counter/src/static/analytics.js))
- **Header:** Back to Dashboard link + Event Title + Date range badge.
- **Top Metric Cards:**
  1. 🏆 **Total Pengunjung (Semua Hari)**
  2. ⏰ **Jam Paling Ramai (Akumulasi)**
  3. 📈 **Hari Teramai**
- **Daily Summary Table:** Table showing Day #, Date, Total Entry, Total Exit, Peak Occupancy.
- **Visual Charts:**
  - Bar chart comparing total visitors per day.
  - Line chart showing visitor entry pattern per hour.

---

## 6. Verification & Automated Test Plan

1. **Unit Tests (`tests/test_daily_records.py`):**
   - Test automatic creation & update of `DailyRecord` on log insertion across multiple dates.
   - Test daily counter scoping (`get_summary()` returns today's counts only).
   - Test calculation of `total_visitors_all_days` and `peak_hour_overall`.
2. **API Integration Tests (`tests/test_analytics_api.py`):**
   - Verify `GET /api/events/{event_id}/analytics` returns expected JSON structure.
3. **Frontend Integration Check:**
   - Verify `index.html` header links to `analytics.html`.
   - Verify `analytics.html` fetches `/api/events/1/analytics` and renders cards, table, and charts cleanly.
