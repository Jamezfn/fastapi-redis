from fastapi import FastAPI
from pydantic import BaseModel
import redis.asyncio as redis
from contextlib import asynccontextmanager
import logging
import json
from typing import Any, Dict

REDIS_URL = "redis://127.0.0.1:6379"
STREAM_NAME = "event:stream"

class EventIn(BaseModel):
    event_type: str
    payload: Dict[str, Any]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await app.state.redis.ping()
        logger.info("  Connected to Redis successfully.")
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e)
        raise
    yield

    await app.state.redis.close()
    logger.info("Redis connection closed.")

app = FastAPI(lifespan=lifespan)

@app.post("/events/publish")
async def publish_event(event_data: EventIn):
    payload = {
        "event_type": event_data.event_type,
        "payload": json.dumps(event_data.payload)
    }
    event_id = await app.state.redis.xadd(STREAM_NAME, payload)
    return {"event_id": event_id, "status": "published"}