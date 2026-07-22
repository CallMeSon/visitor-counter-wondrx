# Phase 4: Web Dashboard Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a single-page web dashboard implementing `DESIGN.md` visual tokens (`#FBF8F3` cream background, bold typography, pill navbar) displaying large real-time numbers, 7-camera status, and live updating Chart.js trend lines over WebSockets.

**Architecture:** Vanilla HTML5/CSS3/JavaScript single page application mounted as static files on the FastAPI backend. Real-time updates push live data to DOM and Chart.js without manual page refreshes.

**Tech Stack:** HTML5, Vanilla CSS3 (Custom Properties), Vanilla JS (ES6+), Chart.js CDN, FastAPI StaticFiles.

## Global Constraints

- Must implement visual design tokens from `DESIGN.md`: Background `#FBF8F3`, Text `#020002`, Lime highlight `#FF7200`, Deep Purple `#017187`, pill navbar (`border-radius: 999px`), card radius (`20px`).
- Displays live metric numbers clearly for event organizers without technical training.
- Live WebSocket auto-reconnect on disconnect.

---

### Task 1: Single-Page Dashboard UI HTML/CSS Layout

**Files:**
- Create: `src/static/index.html`
- Create: `src/static/styles.css`
- Test: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: `DESIGN.md` token specifications
- Produces: `index.html`, `styles.css`

- [ ] **Step 1: Write test for Static Frontend Assets**

Create `tests/test_frontend_assets.py`:
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

Run: `pytest tests/test_frontend_assets.py -v`
Expected: FAIL with `AssertionError: assert False`

- [ ] **Step 3: Write HTML and CSS files**

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

- [ ] **Step 4: Run test to verify it passes partially (app.js needed in next step)**

Write minimal `src/static/app.js`:
```javascript
console.log("Visitor counter frontend app initialized.");
```

Run: `pytest tests/test_frontend_assets.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css src/static/app.js tests/test_frontend_assets.py
git commit -m "feat(frontend): add responsive dashboard UI with DESIGN.md tokens"
```

---

### Task 2: Live WebSocket Client & Chart.js Integration

**Files:**
- Modify: `src/static/app.js`
- Modify: `src/api/app.py:90` (Mount static files)
- Test: `tests/test_frontend_ws.py`

**Interfaces:**
- Consumes: `/api/events/1/summary`, `/ws/events/1`
- Produces: Live metric DOM binding & Chart updates

- [ ] **Step 1: Write test for Static Mount in FastAPI**

Create `tests/test_frontend_ws.py`:
```python
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_static_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "Event Visitor Counter Dashboard" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_ws.py -v`
Expected: FAIL with 404 Not Found (static files not mounted yet)

- [ ] **Step 3: Mount StaticFiles in FastAPI & Complete `app.js`**

Update `src/api/app.py` to add:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
```

Update `src/static/app.js`:
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

Run: `pytest tests/test_frontend_ws.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/static/app.js src/api/app.py tests/test_frontend_ws.py
git commit -m "feat(frontend): bind real-time WebSocket events to DOM metrics and Chart.js"
```
