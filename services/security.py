import hmac
from fastapi import Header, HTTPException
from app.config import settings

def require_api_key(x_kxaio_key: str = Header(default="")):
    if not hmac.compare_digest(x_kxaio_key, settings.kxaio_api_key):
        raise HTTPException(status_code=401, detail="Invalid KXAIO API key")
    return True

def require_n8n_secret(x_n8n_secret: str = Header(default="")):
    if not hmac.compare_digest(x_n8n_secret, settings.n8n_shared_secret):
        raise HTTPException(status_code=401, detail="Invalid n8n shared secret")
    return True
