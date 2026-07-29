# Cloud API Authentication & Edge Retry Queue Design

**Date**: 2026-07-29  
**Status**: Approved  
**Topic**: Remote Cloud Deployment Security & Network Resilience for Edge Cameras  

---

## 1. Overview & Context

When deploying the **Event Visitor Counter** system in production for live events:
- The **Backend API & Dashboard** (`src/api/app.py`) may be hosted on a Cloud VPS / Remote Server (e.g. AWS, DigitalOcean).
- The **Camera Runners** (`camera_runner.py`) run on Edge Devices (laptops / NUCs) located at physical event gates connected to local cameras.
- Telemetry count data is transmitted over the public internet from Edge Cameras to the Cloud API via HTTP POST requests (`/api/count`).

This design introduces:
1. **Lightweight API Key Authentication** to secure Cloud API ingestion endpoints (`POST /api/count`, `POST /api/reset`).
2. **In-Memory Retry Queue & Network Resilience** in `CameraStreamProcessor` to prevent count data loss when venue Wi-Fi/cellular connection drops or experiences packet loss.
3. **Connection Status Indicators** on the OpenCV video stream overlay.

---

## 2. Proposed Changes & Architecture

### Component 1: Backend API Security (`src/api/app.py`)

- **Environment Variable**: `API_KEY` (Optional).
- **Authentication Middleware / Dependency**:
  - Creates a FastAPI dependency `verify_api_key(x_api_key: str = Header(None))`.
  - If the server process has `API_KEY` set (e.g., `API_KEY="secret-event-key"`):
    - Rejects any requests to protected endpoints (`POST /api/count`, `POST /api/reset`) missing or possessing an invalid `X-API-Key` header with HTTP `401 Unauthorized`.
  - If `API_KEY` is not configured on the server (Local Development / Testing), authentication verification is bypassed.
- **Unrestricted Public Endpoints**:
  - Read-only endpoints (`GET /api/events/{id}/summary`, WebSocket feeds `/ws/events/{id}`, static files) remain public to allow uninhibited dashboard presentation.

---

### Component 2: Edge Camera CLI & Config (`camera_runner.py`)

- **CLI Argument & Environment Variable**:
  - Adds `--api-key` string parameter (default `None`).
  - Falls back to `os.environ.get("API_KEY")` if `--api-key` is not explicitly passed.
- **Interactive Setup Prompt**:
  - Prompts for API Key during interactive execution (`len(sys.argv) == 1`):
    `7. Masukkan API Key Server (Opsional, press Enter untuk local dev):`
- **StreamProcessor Initialization**:
  - Passes `api_key` argument into `CameraStreamProcessor`.

---

### Component 3: Network Resilience & Retry Queue (`src/engine/stream_processor.py`)

- **In-Memory Queue**:
  - Initializes `self.failed_queue = []` (capped at `max_queue_size = 1000`).
- **Telemetry Ingestion Logic**:
  - On line crossing event (`send_count_to_api(count)`):
    1. Prepares payload `{"event_id": self.event_id, "camera_id": self.camera_id, "count": count}`.
    2. Includes header `{"X-API-Key": self.api_key}` if `api_key` is present.
    3. Attempts HTTP POST `requests.post(self.api_url, json=payload, headers=headers, timeout=2.0)`.
    4. **If Request Fails** (`RequestException`, Connection Error, Timeout, 5xx Error):
       - Appends payload to `self.failed_queue`.
       - Logs warning to console and updates status overlay.
    5. **If Request Succeeds**:
       - If `self.failed_queue` has items, flushes pending items sequentially up to a batch limit.
- **Visual Overlay Status**:
  - Renders connection badge on OpenCV frame:
    - 🟢 `API: OK`
    - 🟡 `API: Retry Queue (N)`
    - 🔴 `API: 401 Unauthorized`

---

## 3. Verification Plan

### Automated Tests
1. **`tests/test_api_auth.py`**:
   - Tests `POST /api/count` with `API_KEY` set in env:
     - Valid key -> `200 OK`.
     - Missing / Invalid key -> `401 Unauthorized`.
   - Tests `POST /api/count` without `API_KEY` in env:
     - Missing key -> `200 OK` (Dev mode compatibility).
2. **`tests/test_retry_queue.py`**:
   - Tests `CameraStreamProcessor.send_count_to_api` with mocked network failures.
   - Asserts failed count payloads are enqueued into `failed_queue`.
   - Mocks network recovery and asserts queued items are successfully flushed.

### Manual Verification
1. Run server with `API_KEY="testkey123" uvicorn src.api.app:app`.
2. Run camera runner with `python camera_runner.py --api-key testkey123`.
3. Disconnect network / stop server to verify retry queue counter in terminal & OpenCV window.
4. Restart server to verify auto-flush behavior.
