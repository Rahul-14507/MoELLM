# backend/main.py

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from scraper import scrape_products
from conflict_engine import parse_constraints, parse_preferences, evaluate_products
from llm_client import build_resolution_prompt, stream_resolution, stream_chat

app = FastAPI(title="MOELLM Conflict Resolver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResolveRequest(BaseModel):
    preference: str = Field(..., min_length=5)
    constraints: str = Field(..., min_length=5)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/resolve")
async def resolve(req: ResolveRequest):
    """
    Main endpoint. Streams SSE events:
      {type: "step",       step: "scraping"|"conflicts"|"resolving", message: str}
      {type: "products",   data: [...]}
      {type: "conflicts",  data: [...]}
      {type: "token",      content: str}
      {type: "done"}
      {type: "error",      message: str}
    """

    async def event_stream():
        try:
            # ── Step 1: Scrape ────────────────────────────────────
            yield f"data: {json.dumps({'type': 'step', 'step': 'scraping', 'message': 'Searching live market data via Bright Data…'})}\n\n"

            products = await scrape_products(req.preference)

            yield f"data: {json.dumps({'type': 'products', 'data': products})}\n\n"

            # ── Step 2: Detect conflicts ──────────────────────────
            yield f"data: {json.dumps({'type': 'step', 'step': 'conflicts', 'message': f'Found {len(products)} products. Detecting conflicts…'})}\n\n"

            preferences = parse_preferences(req.preference)
            constraints = parse_constraints(req.constraints)
            evaluations = evaluate_products(products, preferences, constraints)

            # Serialize conflicts for frontend
            conflicts_payload = []
            for ev in evaluations:
                conflicts_payload.append({
                    "product_title": ev.product["title"][:60],
                    "product_price": ev.product["price"],
                    "product_url": ev.product.get("url", "#"),
                    "passes": ev.passes_hard_constraints,
                    "match_score": ev.match_score,
                    "conflicts": [
                        {
                            "constraint": c.constraint,
                            "severity": c.severity,
                            "expected": c.expected,
                            "actual": c.actual,
                            "description": c.description,
                        }
                        for c in ev.conflicts
                    ],
                })

            yield f"data: {json.dumps({'type': 'conflicts', 'data': conflicts_payload})}\n\n"

            # ── Step 3: LLM Resolution ────────────────────────────
            yield f"data: {json.dumps({'type': 'step', 'step': 'resolving', 'message': 'Sending to Qwen for conflict resolution…'})}\n\n"

            prompt = build_resolution_prompt(
                req.preference,
                req.constraints,
                constraints,
                evaluations,
            )

            async for token in stream_resolution(prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/chat")
async def chat(req: ChatRequest):
    """Endpoint for follow-up chatbot."""
    async def event_stream():
        try:
            # Convert ChatMessage models to dicts for the LLM client
            messages = [{"role": m.role, "content": m.content} for m in req.messages]
            
            async for token in stream_chat(messages, req.context):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

