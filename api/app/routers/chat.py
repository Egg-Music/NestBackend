from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import json
from ..models import ChatRequest, ChatChunk
from ..deps import auth_dependency
from ..config import settings

router = APIRouter(prefix="/v1", tags=["chat"])

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

@router.post("/chat", response_model=dict)
async def chat(body: ChatRequest, _: None = Depends(auth_dependency)):
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_s)
    model = body.model or settings.openai_model

    resp = await client.chat.completions.create(
        model=model,
        messages=[m.model_dump() for m in body.messages],
        temperature=body.temperature,
        stream=False,
    )
    text = resp.choices[0].message.content or ""
    return {"text": text}

@router.post("/chat/stream")
async def chat_stream(request: Request, _: None = Depends(auth_dependency)):
    """
    SSE stream. Returns `text/event-stream` with frames like:
      data: {"delta":"..."}
      data: {"done":true}
    """
    async def gen():
        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_s)
        payload = await request.json()
        body = ChatRequest(**payload)
        model = body.model or settings.openai_model

        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[m.model_dump() for m in body.messages],
                temperature=body.temperature,
                stream=True,
            )

            async for chunk in stream:
                if await request.is_disconnected():
                    break
                delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
                if delta:
                    yield _sse(ChatChunk(delta=delta).model_dump())
            yield _sse(ChatChunk(done=True).model_dump())
        except Exception as e:
            yield _sse(ChatChunk(error=str(e)).model_dump())

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # tip: if using server-wide compression, disable it for this route at proxy layer
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)


