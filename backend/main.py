# backend/main.py

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from resolver import resolve, TASK_LABELS
from models_config import MODELS
from qwen_client import stream_completion

app = FastAPI(title="MELLM Conflict Resolver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ResolveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    task: str = "rag"
    user_preferred_model: str = "qwen-plus"
    max_latency_tier: int = Field(3, ge=1, le=5)
    max_cost_tier: int = Field(3, ge=1, le=5)
    privacy_required: bool = False
    weight_accuracy: float = Field(8.0, ge=0, le=10)
    weight_speed: float = Field(6.0, ge=0, le=10)
    weight_cost: float = Field(5.0, ge=0, le=10)
    weight_privacy: float = Field(4.0, ge=0, le=10)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/models")
def list_models():
    return {
        mid: {
            "display_name": m["display_name"],
            "best_tasks": m["best_tasks"],
            "latency_tier": m["latency_tier"],
        }
        for mid, m in MODELS.items()
    }

@app.get("/tasks")
def list_tasks():
    return TASK_LABELS


@app.post("/resolve")
def resolve_conflicts(req: ResolveRequest):
    result = resolve(
        task=req.task,
        user_preferred_model=req.user_preferred_model,
        max_latency_tier=req.max_latency_tier,
        max_cost_tier=req.max_cost_tier,
        privacy_required=req.privacy_required,
        weight_accuracy=req.weight_accuracy,
        weight_speed=req.weight_speed,
        weight_cost=req.weight_cost,
        weight_privacy=req.weight_privacy,
    )
    return {
        "winner_id": result.winner_id,
        "winner_name": result.winner_name,
        "confidence": result.confidence,
        "preference_honoured": result.preference_honoured,
        "user_preferred_id": result.user_preferred_id,
        "conflicts": [
            {
                "severity": c.severity,
                "dimension": c.dimension,
                "description": c.description,
                "penalty": c.penalty,
            }
            for c in result.conflicts
        ],
        "dimension_scores": [
            {
                "name": d.name,
                "raw_score": d.raw_score,
                "weight": d.weight,
                "weighted_score": d.weighted_score,
                "color": d.color,
            }
            for d in result.dimension_scores
        ],
        "verdict": result.verdict,
        "all_scores": result.all_scores,
    }


@app.post("/run")
async def run_query(req: ResolveRequest):
    """Resolve conflicts then stream the response from the winning model."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = resolve(
        task=req.task,
        user_preferred_model=req.user_preferred_model,
        max_latency_tier=req.max_latency_tier,
        max_cost_tier=req.max_cost_tier,
        privacy_required=req.privacy_required,
        weight_accuracy=req.weight_accuracy,
        weight_speed=req.weight_speed,
        weight_cost=req.weight_cost,
        weight_privacy=req.weight_privacy,
    )

    winner_model_id = MODELS[result.winner_id]["qwen_model_id"]

    async def event_stream():
        # First, emit the resolution metadata as a JSON event
        import json
        meta = {
            "type": "resolution",
            "winner_id": result.winner_id,
            "winner_name": result.winner_name,
            "confidence": result.confidence,
            "preference_honoured": result.preference_honoured,
            "conflicts": [
                {"severity": c.severity, "dimension": c.dimension, "description": c.description}
                for c in result.conflicts
            ],
            "dimension_scores": [
                {"name": d.name, "weighted_score": d.weighted_score, "color": d.color}
                for d in result.dimension_scores
            ],
            "verdict": result.verdict,
            "all_scores": result.all_scores,
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Then stream the actual LLM response
        async for token in stream_completion(winner_model_id, req.query, req.task):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok", "models": list(MODELS.keys())}
