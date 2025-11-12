from fastapi import FastAPI
import redis.asyncio as redis
from contextlib import asynccontextmanager

REDIS_URL = "redis://127.0.0.1:6379"
REDIS_KEY_PREFIX = "User:"

@asynccontextmanager
async def startup(app: FastAPI):
    try:
        app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        pong = await app.state.redis.ping()
        print("Redis connected successfully! PING →", pong)
    except:
        print("Failed to connect to Redis:", e)
        raise

    yield

    await app.state.redis.close()
    print("Redis connection closed.")

app = FastAPI(lifespan=startup)

@app.get("/health")
async def health():
    try:
        await app.state.redis.ping()
        return {"status": "healthy", "redis": "connected"}
    except:
        return {"status": "unhealthy", "redis": "disconnected"}
