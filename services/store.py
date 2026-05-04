from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import json
from app.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)
Base = declarative_base()

class EventRecord(Base):
    __tablename__ = "kxaio_events"
    event_id = Column(String, primary_key=True)
    source = Column(String, index=True)
    source_event_id = Column(String, index=True, nullable=True)
    event_type = Column(String, index=True)
    status = Column(String, default="accepted")
    payload_json = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)

def save_event(event):
    with SessionLocal() as db:
        if event.source_event_id:
            existing = db.query(EventRecord).filter_by(source=event.source, source_event_id=event.source_event_id).first()
            if existing:
                return False, existing.event_id
        rec = EventRecord(
            event_id=event.event_id,
            source=event.source,
            source_event_id=event.source_event_id,
            event_type=event.event_type,
            status="accepted",
            payload_json=json.dumps(event.model_dump(mode="json")),
        )
        db.add(rec)
        db.commit()
        return True, event.event_id
