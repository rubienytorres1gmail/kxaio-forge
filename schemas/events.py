from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class KxaioEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    source_event_id: Optional[str] = None
    event_type: str
    subject_id: Optional[str] = None
    customer_email: Optional[str] = None
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str = "forge.dispatch"

class KxaioResult(BaseModel):
    accepted: bool
    event_id: str
    status: str
    message: str
