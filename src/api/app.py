from contextlib import asynccontextmanager
from typing import List, Dict
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db, SessionLocal, engine, Base
from src.db.models import Event, CameraConfig, CountingLog, Snapshot
from src.services.aggregator import EventAggregatorService


def run_migrations():
    """Tambahkan kolom baru ke tabel yang sudah ada agar DB lama tetap kompatibel."""
    migrations = [
        ("camera_configs", "last_active_at", "DATETIME"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                result = conn.execute(
                    __import__("sqlalchemy").text(f"SELECT {column} FROM {table} LIMIT 1")
                )
                result.fetchone()
            except Exception:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                    )
                )
                conn.commit()


def seed_default_event():
    db = SessionLocal()
    try:
        event = db.query(Event).filter_by(id=1).first()
        if not event:
            event = Event(id=1, name="Konser/Seminar Live MVP", max_capacity=5000)
            db.add(event)
            db.commit()

            cams = [
                CameraConfig(id=1, event_id=1, name="Pintu Masuk A (Kamera 1)", role="entry"),
                CameraConfig(id=2, event_id=1, name="Pintu Masuk B (Kamera 2)", role="entry"),
                CameraConfig(id=3, event_id=1, name="Pintu Keluar 1 (Kamera 3)", role="exit"),
                CameraConfig(id=4, event_id=1, name="Pintu Keluar 2 (Kamera 4)", role="exit"),
                CameraConfig(id=5, event_id=1, name="Pintu Keluar 3 (Kamera 5)", role="exit"),
                CameraConfig(id=6, event_id=1, name="Pintu Keluar 4 (Kamera 6)", role="exit"),
                CameraConfig(id=7, event_id=1, name="Pintu Keluar 5 (Kamera 7)", role="exit"),
            ]
            db.add_all(cams)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations()
    seed_default_event()
    yield


app = FastAPI(title="Event Visitor Counter API", lifespan=lifespan)

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
            disconnected = []
            for connection in list(self.active_connections[event_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(event_id, conn)

manager = ConnectionManager()

class CountPayload(BaseModel):
    event_id: int
    camera_id: int
    count: int = 1

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

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

class HeartbeatPayload(BaseModel):
    event_id: int
    camera_id: int

@app.post("/api/heartbeat")
async def record_heartbeat(payload: HeartbeatPayload, db: Session = Depends(get_db)):
    service = EventAggregatorService(db, payload.event_id)
    summary = service.record_heartbeat(payload.camera_id)
    await manager.broadcast(payload.event_id, summary)
    return {"status": "heartbeat_received", "summary": summary}

@app.post("/api/events/{event_id}/reset")
async def reset_counter(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    service = EventAggregatorService(db, event_id)
    summary = service.reset_counter()
    await manager.broadcast(event_id, summary)
    return {"status": "success", "summary": summary}


@app.websocket("/ws/events/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: int):
    await manager.connect(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        manager.disconnect(event_id, websocket)

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")


