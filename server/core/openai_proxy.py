import json, httpx, asyncio, tiktoken
from fastapi import HTTPException
from core.settings import settings
from core.logging_config import logger

enc = tiktoken.encoding_for_model(settings.openai_model)


async def stream_chat(prompt: str):
    """Yields SSE‑formatted chunks (`str`) exactly like OpenAI."""

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream("POST", f"{settings.openai_base}/chat/completions", headers=headers, json=body) as resp:
                status = resp.status_code
                logger.info(f"OpenAI status {status}")

                if status != 200:
                    detail = await resp.aread()
                    payload = json.dumps({"error": detail.decode()})
                    yield f"data: {payload}\n\n"
                    return

                async for line in resp.aiter_lines():
                    if line.strip() == "" or line.startswith(":"):
                        continue

                    if line.strip() == "data: [DONE]":
                        yield "data: [DONE]\n\n"
                        break

                    if not line.startswith("data: "):
                        line = f"data: {line}"

                    yield f"{line}\n\n"

        except httpx.RequestError as exc:
            payload = json.dumps({"error": str(exc)})
            print(f"RequestError: {exc}")
            yield f"data: {payload}\n\n"
        except Exception as exc:
            payload = json.dumps({"error": str(exc)})
            print(f"Unexpected: {exc}")
            yield f"data: {payload}\n\n"
