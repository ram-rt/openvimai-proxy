import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from core.logging_config import logger
from models import request as R
from core import openai_proxy, cache
from core.settings import settings
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel
from telemetry import db as tdb
from datetime import datetime
from core.security import get_current_user


class TelemetryEvent(BaseModel):
    ts: Optional[datetime] = None
    event_type: str
    payload: Dict[str, Any] = {}

router = APIRouter()

@router.post("/completion")
async def completion(req: R.CompletionRequest, _user=Depends(get_current_user)):
    # Try to return cached response
    cached = cache.get(req.prompt)
    if cached:
        resp_text, _tok = cached
        tdb.record("cache_hit", {"mode": req.mode})

        async def cached_stream(text: str):
            # Format cached text as fake SSE
            chunk = json.dumps({"choices": [{"delta": {"content": text}}]})
            yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(cached_stream(resp_text), media_type="text/event-stream")

    # Stream response from OpenAI
    async def event_stream():
        prompt_tokens = len(openai_proxy.enc.encode(req.prompt))
        buffer, n_tokens = [], 0

        async for chunk in openai_proxy.stream_chat(req.prompt):
            # Remove SSE prefix
            if chunk.startswith("data:"):
                payload = chunk[len("data:"):].strip()
            else:
                payload = chunk.strip()

            # Check end-of-stream
            if payload == "[DONE]":
                yield "data: [DONE]\n\n"
                break

            # Parse streamed chunk for token counting and caching
            try:
                parsed = json.loads(payload)
                delta = parsed["choices"][0].get("delta", {})
                if (content := delta.get("content")):
                    buffer.append(content)
                    n_tokens += len(openai_proxy.enc.encode(content))
            except json.JSONDecodeError as exc:
                logger.error(f"stream decode error: {exc}: {payload!r}")

            # Check token cutoff threshold
            if prompt_tokens + n_tokens >= int(settings.ctx_tokens * settings.cutoff_ratio):
                logger.warning("⏹  stream_interrupt @%.0f%% ctx", settings.cutoff_ratio * 100)
                tdb.record("stream_interrupt", {"at_tokens": prompt_tokens + n_tokens})
                yield "data: [DONE]\n\n"
                break

            # Forward original chunk to client
            yield chunk

        # Persist response to cache and telemetry
        if buffer:
            full_text = "".join(buffer)
            total = prompt_tokens + n_tokens
            cache.put(req.prompt, full_text, total)
            tdb.record("completion", {"tokens": total})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/telemetry")
async def telemetry_ingest(
    events: Union[TelemetryEvent, List[TelemetryEvent]],
    _user=Depends(get_current_user)
):
    # Normalize to list
    if not isinstance(events, list):
        events = [events]

    # Record events to database
    for ev in events:
        tdb.record(ev.event_type, ev.payload, ev.ts)

    return {"status": "ok", "count": len(events)}
