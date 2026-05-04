from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import requests
import os
import json
import uuid
from datetime import datetime

# ═════════════════════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="KXAIO Forge API",
    description="MetaBantrix OMEGA Level — AI Product Generation & Swarm Orchestration",
    version="vΩ♾️",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — Allow n8n, Render, Vercel, and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5678",      # n8n local
        "https://app.n8n.cloud",     # n8n cloud
        "https://metabantrix-api.onrender.com",
        "https://mymiracle.io",
        "https://rubienytorres.com",
        "*"  # Remove in production if you want strict security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic) — Request/Response Schemas
# ═════════════════════════════════════════════════════════════════════════════

class ForgeRequest(BaseModel):
    """Incoming request from n8n to trigger a forge operation."""
    prompt: str = Field(..., description="The user prompt or event type to process")
    task_type: str = Field(default="forge_full", description="Type of forge operation")
    event_id: Optional[str] = Field(default=None, description="Optional event tracking ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Extra context data")

class SwarmAgent(BaseModel):
    """Individual swarm agent output."""
    role: str
    output: str

class ForgeScore(BaseModel):
    """Quality/trust scoring for the forge output."""
    quality: float = Field(ge=0.0, le=1.0, default=0.94)
    trust: float = Field(ge=0.0, le=1.0, default=0.96)
    success: float = Field(ge=0.0, le=1.0, default=1.0)
    reuse: float = Field(ge=0.0, le=1.0, default=0.89)
    utility: float = Field(ge=0.0, le=1.0, default=0.93)

class ForgeResponse(BaseModel):
    """Structured response back to n8n."""
    status: str = "success"
    event_id: str
    route: str = "alpha_infinity_v1"
    prompt: str
    task_type: str
    output: str
    swarm: Dict[str, Any]
    score: ForgeScore
    timestamp: str
    canon_lock: bool = True

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    uptime: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standardized error response."""
    status: str = "error"
    error_type: str
    message: str
    timestamp: str
    event_id: Optional[str] = None

# ═════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def generate_event_id() -> str:
    """Generate a unique event ID for tracking across n8n → FastAPI → Supabase."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """ISO 8601 timestamp for all logging."""
    return datetime.utcnow().isoformat() + "Z"

def build_swarm_result(prompt: str, task_type: str) -> Dict[str, Any]:
    """
    Build the swarm agent outputs.
    In production, this would call actual AI models (OpenAI, Claude, etc.).
    For now, returns structured stubs that n8n can score and log.
    """
    return {
        "agents": [
            {
                "role": "planner",
                "output": f"Planning full canon forge for: {prompt}",
                "confidence": 0.95
            },
            {
                "role": "critic",
                "output": "Canon alignment verified — safety boundaries respected",
                "confidence": 0.98
            },
            {
                "role": "synthesizer",
                "output": f"Compounded output ready for distribution. Task: {task_type}",
                "confidence": 0.96
            }
        ],
        "final_output": f"KXAIO Forge completed — {task_type} executed for: {prompt}",
        "canon_version": "vΩ♾️",
        "execution_time_ms": 42  # Stub — measure real execution in production
    }

def build_score(swarm_result: Dict[str, Any]) -> ForgeScore:
    """
    Calculate quality scores based on swarm outputs.
    In production, this would use actual ML-based scoring.
    """
    # Simple heuristic: average confidence of agents
    confidences = [a["confidence"] for a in swarm_result["agents"]]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.9

    return ForgeScore(
        quality=round(avg_conf, 2),
        trust=0.96,
        success=1.0,
        reuse=0.89,
        utility=0.93
    )

# ═════════════════════════════════════════════════════════════════════════════
# CORE ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", response_model=HealthResponse, tags=["Health"])
def root():
    """
    Root health check — used by UptimeRobot, n8n cron monitoring, etc.
    """
    return HealthResponse(
        status="FastAPI is running — KXAIO Forge vΩ♾️",
        version="vΩ♾️",
        timestamp=get_timestamp(),
        uptime="active"
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Dedicated health endpoint for external monitoring (UptimeRobot, Better Stack).
    """
    return HealthResponse(
        status="healthy",
        version="vΩ♾️",
        timestamp=get_timestamp()
    )


@app.post("/kxaio/forge", response_model=ForgeResponse, tags=["Forge"])
def kxaio_forge(request: ForgeRequest):
    """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  KXAIO FORGE — OMEGA Level Endpoint                                   ║
    ║  Receives: n8n HTTP Request with prompt + task_type                   ║
    ║  Returns: Structured forge result with swarm + score                  ║
    ║  Logs to: Supabase (via n8n downstream node)                          ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    This is the core of the MetaBantrix engine. n8n calls this endpoint,
    receives the forge output, then logs to Supabase and notifies Viktor.
    """
    try:
        # Generate or use provided event ID
        event_id = request.event_id or generate_event_id()

        # Build swarm result
        swarm = build_swarm_result(request.prompt, request.task_type)

        # Calculate scores
        score = build_score(swarm)

        # Build response
        response = ForgeResponse(
            status="success",
            event_id=event_id,
            route="alpha_infinity_v1",
            prompt=request.prompt,
            task_type=request.task_type,
            output=swarm["final_output"],
            swarm=swarm,
            score=score,
            timestamp=get_timestamp(),
            canon_lock=True
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status="error",
                error_type="forge_execution_error",
                message=str(e),
                timestamp=get_timestamp(),
                event_id=request.event_id or generate_event_id()
            ).dict()
        )


@app.post("/trigger", tags=["Legacy / n8n Bridge"])
def trigger(data: dict):
    """
    LEGACY ENDPOINT — Forwards to n8n webhook.
    Kept for backward compatibility with existing workflows.

    In the vΩ♾️ architecture, n8n should call /kxaio/forge directly
    instead of using this forwarding pattern.
    """
    try:
        response = requests.post(
            "http://localhost:5678/webhook-test/trigger",
            json=data,
            timeout=5
        )
        return {
            "status": "forwarded_to_n8n",
            "n8n_status_code": response.status_code,
            "n8n_response": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ═════════════════════════════════════════════════════════════════════════════
# EXPANSION ENDPOINTS (Future-Proofing)
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/kxaio/forge/product", tags=["Forge — Product Generation"])
def forge_product(request: ForgeRequest):
    """
    Dedicated endpoint for product generation (Gumroad, digital assets).
    Returns product-ready output with pricing, description, and tags.
    """
    event_id = request.event_id or generate_event_id()

    return {
        "status": "success",
        "event_id": event_id,
        "product": {
            "title": f"MetaBantrix: {request.prompt[:50]}",
            "description": f"AI-generated product based on: {request.prompt}",
            "price": 27.00,
            "currency": "USD",
            "tags": ["AI", "MetaBantrix", "vΩ♾️", request.task_type],
            "canon_locked": True
        },
        "score": ForgeScore().dict(),
        "timestamp": get_timestamp()
    }


@app.post("/kxaio/forge/deed", tags=["Forge — NFT Deed"])
def forge_deed(request: ForgeRequest):
    """
    Dedicated endpoint for IndustryDeed NFT generation.
    Returns deed metadata ready for blockchain minting.
    """
    event_id = request.event_id or generate_event_id()

    return {
        "status": "success",
        "event_id": event_id,
        "deed": {
            "type": "IndustryDeed",
            "title": f"Deed: {request.prompt[:40]}",
            "owner": "MetaBantrix Canon",
            "blockchain": "Polygon",
            "metadata_uri": f"https://mymiracle.io/deeds/{event_id}",
            "canonical": True
        },
        "score": ForgeScore().dict(),
        "timestamp": get_timestamp()
    }


# ═════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS (vΩ♾️ Style — Never Fail Silently)
# ═════════════════════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Catch all HTTP errors and return structured JSON.
    n8n can parse this and route to the Error Handler workflow.
    """
    return {
        "status": "error",
        "error_type": "http_error",
        "status_code": exc.status_code,
        "message": exc.detail,
        "timestamp": get_timestamp(),
        "path": str(request.url),
        "level": "OMEGA"
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Catch-all for unexpected errors.
    Logs to console AND returns structured error for n8n Supabase logging.
    """
    error_id = generate_event_id()
    print(f"🚨 CRITICAL ERROR [{error_id}]: {str(exc)}")

    return {
        "status": "error",
        "error_type": "critical_unexpected",
        "error_id": error_id,
        "message": str(exc),
        "timestamp": get_timestamp(),
        "path": str(request.url),
        "level": "OMEGA",
        "action": "Check Supabase errors table for stack trace"
    }


# ═════════════════════════════════════════════════════════════════════════════
# RUN (Local Development Only — Render uses uvicorn directly)
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
