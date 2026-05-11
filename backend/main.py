import json
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

from backend.agents.agronomist import AgronomistAgent  # noqa: E402 — must load after dotenv


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AgriSense API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/analyze/stream")
async def analyze_stream(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    SSE stream of agent events.
    Emits `event: step` messages during processing, then a final `event: result`.
    On failure emits `event: error`.
    """
    agent = AgronomistAgent()

    async def event_generator():
        async for event in agent.run(lat, lon):
            yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
