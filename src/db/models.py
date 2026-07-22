from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.db.database import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    max_capacity = Column(Integer, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=utc_now)

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
    last_active_at = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="cameras")

class CountingLog(Base):
    __tablename__ = "counting_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    camera_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # "entry" or "exit"
    count_delta = Column(Integer, default=1)
    timestamp = Column(DateTime, default=utc_now)

    event = relationship("Event", back_populates="logs")

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    current_inside = Column(Integer, default=0)
    timestamp = Column(DateTime, default=utc_now)

    event = relationship("Event", back_populates="snapshots")

