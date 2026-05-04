import stripe
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.schemas.events import KxaioEvent, KxaioResult
from app.services.store import save_event
from app.services.kxaio_orchestrator import dispatch_to_kxaio

router = APIRouter()

@router.post("/stripe", response_model=KxaioResult)
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        stripe_event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Stripe signature verification failed: {exc}")

    data_object = stripe_event.get("data", {}).get("object", {})
    event = KxaioEvent(
        source="stripe",
        source_event_id=stripe_event.get("id"),
        event_type=stripe_event.get("type", "stripe.unknown"),
        subject_id=data_object.get("id"),
        customer_email=data_object.get("customer_details", {}).get("email") or data_object.get("receipt_email"),
        amount_total=data_object.get("amount_total") or data_object.get("amount"),
        currency=data_object.get("currency"),
        raw=stripe_event
    )

    inserted, event_id = save_event(event)
    if inserted:
        dispatch_to_kxaio(event)

    return KxaioResult(accepted=True, event_id=event_id, status="accepted" if inserted else "duplicate", message="Stripe event received")
