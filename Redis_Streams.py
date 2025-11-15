from fastapi import FastAPI
from pydantic import BaseModel
import redis.asyncio as redis
from redis.exceptions import ResponseError
from contextlib import asynccontextmanager
import logging
import json
from typing import Any, Dict
import asyncio

REDIS_URL = "redis://127.0.0.1:6379"
STREAM_NAME = "event:stream"
GROUP_NAME = "events_group"
CONSUMER_NAME = "worker-1"

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

@app.get("/events")
async def get_events(count: int = 10):
    events_raw = await app.state.redis.xrevrange(STREAM_NAME, max="+", min="-", count=count)
    events = []
    for event_id, fields in events_raw:
        event = {
            "event_id": event_id,
            "event_type": fields.get("event_type"),
            "payload": json.loads(fields.get("payload", "{}"))
        }
        events.append(event)  
    return {"events": events}

@app.post("/events/group/create")
async def create_consumer_group(mkstream: bool = False):
    try:
        await app.state.redis.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=mkstream)
        return {"status": "consumer group created"}
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            return {"status": "consumer group already exists"}
        else:
            raise

@app.delete("/events/{id}")
async def clear_events(id: str):
    event_with_id = await app.state.redis.xrange(STREAM_NAME, min=id, max=id, count=1)
    if not event_with_id:
        return {"status": "not found"}
    deleted = await app.state.redis.xdel(STREAM_NAME, id)
    return {"status": "cleared"}

@app.delete("/events/clear")
async def clear_all_events():
    deleted = await app.state.redis.delete(STREAM_NAME)
    return {"status": "all cleared", "deleted_count": deleted}