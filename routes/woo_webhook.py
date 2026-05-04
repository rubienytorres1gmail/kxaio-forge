import base64, hashlib, hmac
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.schemas.events import KxaioEvent, KxaioResult
from app.services.store import save_event
from app.services.kxaio_orchestrator import dispatch_to_kxaio

router = APIRouter()

def verify_woo_signature(raw_body: bytes, signature: str) -> bool:
    digest = hmac.new(
        settings.woocommerce_webhook_secret.encode(),
        raw_body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature or "")

@router.post("/woocommerce", response_model=KxaioResult)
async def woocommerce_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("x-wc-webhook-signature", "")

    if not verify_woo_signature(raw, signature):
        raise HTTPException(status_code=400, detail="WooCommerce webhook signature verification failed")

    body = await request.json()
    event_type = request.headers.get("x-wc-webhook-topic", "woocommerce.unknown")

    billing = body.get("billing", {})
    event = KxaioEvent(
        source="woocommerce",
        source_event_id=request.headers.get("x-wc-delivery-id") or str(body.get("id")),
        event_type=event_type,
        subject_id=str(body.get("id")),
        customer_email=billing.get("email"),
        amount_total=int(float(body.get("total", "0")) * 100) if body.get("total") else None,
        currency=body.get("currency"),
        raw=body
    )

    inserted, event_id = save_event(event)
    if inserted:
        dispatch_to_kxaio(event)

    return KxaioResult(accepted=True, event_id=event_id, status="accepted" if inserted else "duplicate", message="WooCommerce event received")
