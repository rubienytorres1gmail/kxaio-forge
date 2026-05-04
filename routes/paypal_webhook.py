import httpx
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.schemas.events import KxaioEvent, KxaioResult
from app.services.store import save_event
from app.services.kxaio_orchestrator import dispatch_to_kxaio

router = APIRouter()

def paypal_base_url():
    return "https://api-m.paypal.com" if settings.paypal_env == "live" else "https://api-m.sandbox.paypal.com"

async def get_paypal_access_token():
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            f"{paypal_base_url()}/v1/oauth2/token",
            auth=(settings.paypal_client_id, settings.paypal_client_secret),
            data={"grant_type": "client_credentials"},
        )
        res.raise_for_status()
        return res.json()["access_token"]

async def verify_paypal_webhook(headers: dict, body: dict):
    token = await get_paypal_access_token()
    verification_payload = {
        "auth_algo": headers.get("paypal-auth-algo"),
        "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": settings.paypal_webhook_id,
        "webhook_event": body,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            f"{paypal_base_url()}/v1/notifications/verify-webhook-signature",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=verification_payload,
        )
        res.raise_for_status()
        return res.json().get("verification_status") == "SUCCESS"

@router.post("/paypal", response_model=KxaioResult)
async def paypal_webhook(request: Request):
    body = await request.json()
    ok = await verify_paypal_webhook(dict(request.headers), body)
    if not ok:
        raise HTTPException(status_code=400, detail="PayPal webhook verification failed")

    resource = body.get("resource", {})
    amount = resource.get("amount", {}) or resource.get("seller_receivable_breakdown", {}).get("gross_amount", {})

    event = KxaioEvent(
        source="paypal",
        source_event_id=body.get("id"),
        event_type=body.get("event_type", "paypal.unknown"),
        subject_id=resource.get("id"),
        customer_email=resource.get("payer", {}).get("email_address"),
        amount_total=int(float(amount.get("value", "0")) * 100) if amount.get("value") else None,
        currency=amount.get("currency_code"),
        raw=body
    )

    inserted, event_id = save_event(event)
    if inserted:
        dispatch_to_kxaio(event)

    return KxaioResult(accepted=True, event_id=event_id, status="accepted" if inserted else "duplicate", message="PayPal event received")
