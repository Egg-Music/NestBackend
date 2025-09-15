import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from ..deps import auth_dependency
from ..config import settings
from ..daw.schema import execute_actions_tool
from ..daw.action_bus import ActionBus

router = APIRouter(prefix="/v1", tags=["assistant"])
logger = logging.getLogger(__name__)

SYSTEM = (
    "You are an assistant for a DAW. "
    "Return the smallest valid plan that achieves the user's intent. "
    "Use only IDs provided in the project summary. Never delete data."
)

def _map_conversation(conversation: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    if not conversation:
        return []
    mapped: List[Dict[str, str]] = []
    for m in conversation:
        role = str(m.get("role", "")).lower()
        text = str(m.get("text", ""))
        if not text:
            continue
        if role == "egg":
            role = "assistant"
        elif role not in ("user", "assistant", "system"):
            continue
        mapped.append({"role": role, "content": text})
    return mapped

def make_messages(project_summary: Dict[str, Any], user_prompt: str, conversation: Optional[List[Dict[str, Any]]] = None):
    msgs: List[Dict[str, str]] = [
        {"role":"system","content": SYSTEM},
        {"role":"system","content": f"PROJECT SUMMARY: {json.dumps(project_summary)[:6000]}"},
    ]
    msgs.extend(_map_conversation(conversation))
    if not msgs or not (msgs[-1].get("role") == "user" and msgs[-1].get("content") == user_prompt):
        msgs.append({"role":"user",  "content": user_prompt})
    return msgs

def summarize_plan(plan: list[dict]) -> str:
    parts: list[str] = []
    for a in plan:
        t = a.get("type")
        if t == "project.setTitle":
            parts.append(f"set project title to '{a.get('title')}'")
        elif t == "transport.play":
            parts.append("start playback")
        elif t == "transport.stop":
            parts.append("stop playback")
        elif t == "loop.set":
            parts.append(f"set loop to startBeat={a.get('startBeat')} lengthBeats={a.get('lengthBeats')}")
        elif t == "track.add":
            parts.append(f"add track '{a.get('name')}'")
        elif t == "track.rename":
            parts.append(f"rename track {a.get('trackId')} to '{a.get('name')}'")
        elif t == "track.setGain":
            parts.append(f"set gain of track {a.get('trackId')} to {a.get('gainDb')} dB")
        elif t == "track.toggleMute":
            parts.append(f"toggle mute on track {a.get('trackId')}")
        elif t == "clip.addAudio":
            parts.append(f"add audio clip to track {a.get('trackId')} at beat {a.get('startBeat')} from '{a.get('path')}'")
        elif t == "clip.move":
            parts.append(f"move clip {a.get('clipId')} to beat {a.get('startBeat')}")
    if not parts:
        return "No changes."
    if len(parts) == 1:
        return f"I will {parts[0]}."
    return "I will " + ", then ".join(parts) + "."

@router.post("/assistant")
async def assistant(
    prompt: str = Body(...),
    project_summary: Dict[str, Any] = Body(...),
    conversation: Optional[List[Dict[str, Any]]] = Body(default=None),
    mode: str = Body("dryRun"),
    _: None = Depends(auth_dependency),
):
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_s)
    model = settings.openai_model

    chat = await client.chat.completions.create(
        model=model,
        tools=[{"type":"function","function": execute_actions_tool}],
        tool_choice="auto",
        messages= make_messages(project_summary, prompt, conversation)
    )

    msg = chat.choices[0].message
    tool_calls = msg.tool_calls or []

    if not tool_calls:
        return {"type":"text","content": msg.content or ""}

    try:
        raw_args = tool_calls[0].function.arguments or "{}"
        logger.info("assistant.tool_call.raw_args=%s", raw_args)
        args = json.loads(raw_args)
        plan = args.get("plan", [])
        logger.info("assistant.tool_call.plan=%s", plan)
        if not isinstance(plan, list) or len(plan)==0:
            return {"type":"error","error":"empty plan"}
    except Exception as e:
        return {"type":"error","error":f"bad tool args: {e}"}

    bus = ActionBus(
        project_root=project_summary.get("projectRoot",""),
        bpm=float(project_summary.get("bpm", 120)),
        beat_unit=int(project_summary.get("timeSig",{}).get("denominator", 4))
    )

    results_preview, diffs_preview = bus.execute_plan(plan, "dryRun")

    SAFE = {"transport.play","transport.stop","loop.set","track.rename","track.toggleMute","track.setGain","project.setTitle"}
    is_small_safe = len(plan) <= 3 and all(isinstance(a, dict) and a.get("type") in SAFE for a in plan)
    if mode == "apply" and is_small_safe:
        results_apply, diffs_apply = bus.execute_plan(plan, "apply")
        return {"type":"applied","preview":{"mods":diffs_preview},"results":results_apply}

    return {"type":"plan","preview":{"mods":diffs_preview},"plan":plan}

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

@router.post("/assistant/stream")
async def assistant_stream(
    request: Request,
    prompt: str = Body(...),
    project_summary: Dict[str, Any] = Body(...),
    conversation: Optional[List[Dict[str, Any]]] = Body(default=None),
    mode: str = Body("dryRun"),
    _: None = Depends(auth_dependency),
):
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_s)
    model = settings.openai_model

    async def gen():
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages= make_messages(project_summary, prompt, conversation),
                tools=[{"type":"function","function": execute_actions_tool}],
                tool_choice="auto",
                stream=True,
            )

            saw_tool = False
            tool_name = None
            tool_args_buf = ""
            streamed_any_text = False

            async for chunk in stream:
                if await request.is_disconnected():
                    break
                if not chunk.choices:
                    continue
                d = chunk.choices[0].delta
                if not d:
                    continue

                # Accumulate tool call arguments if present
                if getattr(d, "tool_calls", None):
                    saw_tool = True
                    for tc in d.tool_calls:
                        if getattr(tc, "function", None):
                            if getattr(tc.function, "name", None):
                                tool_name = tc.function.name
                            if getattr(tc.function, "arguments", None):
                                tool_args_buf += tc.function.arguments
                    # skip sending text when tool engaged
                    continue

                # Stream text deltas only if no tool call detected
                if not saw_tool:
                    delta = d.content
                    if delta:
                        streamed_any_text = True
                        yield _sse({"delta": delta})

            # End of stream
            if not saw_tool:
                # pure text path
                yield _sse({"done": True})
                return

            # tool path: parse args and emit plan frame
            try:
                logger.info("assistant.stream.tool_call.raw_args=%s", tool_args_buf)
                args = json.loads(tool_args_buf or "{}")
                plan = args.get("plan", [])
                logger.info("assistant.stream.tool_call.plan=%s", plan)
                if not isinstance(plan, list) or len(plan)==0:
                    yield _sse({"error":"empty plan"})
                    return
            except Exception as e:
                yield _sse({"error": f"bad tool args: {e}"})
                return

            bus = ActionBus(
                project_root=project_summary.get("projectRoot",""),
                bpm=float(project_summary.get("bpm", 120)),
                beat_unit=int(project_summary.get("timeSig",{}).get("denominator", 4))
            )
            _, diffs_preview = bus.execute_plan(plan, "dryRun")
            yield _sse({"type":"plan", "preview": {"mods": diffs_preview}, "plan": plan})
        except Exception as e:
            yield _sse({"error": str(e)})

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)



@router.post("/apply")
async def apply_plan(
    plan: List[Dict[str, Any]] = Body(...),
    project_summary: Dict[str, Any] = Body(default_factory=dict),
    mode: str = Body("apply"),
    _: None = Depends(auth_dependency),
):
    logger.info("assistant.apply.plan=%s", plan)
    bus = ActionBus(
        project_root=project_summary.get("projectRoot",""),
        bpm=float(project_summary.get("bpm", 120)),
        beat_unit=int(project_summary.get("timeSig",{}).get("denominator", 4))
    )
    results, diffs = bus.execute_plan(plan, "apply" if mode == "apply" else "dryRun")
    if mode == "apply":
        return {"type":"applied", "preview": {"mods": diffs}, "results": results}
    return {"type":"plan", "preview": {"mods": diffs}, "plan": plan}

