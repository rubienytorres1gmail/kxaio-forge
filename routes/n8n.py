from fastapi import APIRouter, Depends
from app.schemas.events import KxaioEvent, KxaioResult
from app.services.security import require_n8n_secret
from app.services.store import save_event
from app.services.kxaio_orchestrator import dispatch_to_kxaio

router = APIRouter()

@router.post("/n8n/kxaio-trigger", response_model=KxaioResult)
def n8n_trigger(event: KxaioEvent, _: bool = Depends(require_n8n_secret)):
    event.source = event.source or "n8n"
    inserted, event_id = save_event(event)
    if inserted:
        dispatch_to_kxaio(event)
    return KxaioResult(accepted=True, event_id=event_id, status="accepted" if inserted else "duplicate", message="n8n event received")
