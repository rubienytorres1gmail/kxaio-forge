from fastapi import APIRouter, Depends
from app.schemas.events import KxaioEvent, KxaioResult
from app.services.security import require_api_key
from app.services.store import save_event
from app.services.kxaio_orchestrator import dispatch_to_kxaio

router = APIRouter()

@router.post("/forge/manual", response_model=KxaioResult)
def manual_forge(event: KxaioEvent, _: bool = Depends(require_api_key)):
    event.source = "manual"
    inserted, event_id = save_event(event)
    if inserted:
        dispatch_to_kxaio(event)
    return KxaioResult(accepted=True, event_id=event_id, status="accepted" if inserted else "duplicate", message="Manual event received")
