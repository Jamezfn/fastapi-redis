from fastapi import FastAPI
from pydantic import BaseModel
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

REDIS_URL = "redis://localhost:6379"
NAMESPACE = "app_v1"

def key(*parts: str) -> str:
    return ":".join([NAMESPACE, *map(str, parts)])

class User(BaseModel):
    id: int
    name: str
    email: str
    country: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    await app.state.redis.ping()
    yield
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

async def cache_with_fixed_ttl(key: str, value, ttl: int = 30):
    return await app.state.redis.setex(key, ttl, value)

async def write_user(user: User, ttl: int = 300):
    cache_key = key("user", user.id)
    await app.state.redis.setex(cache_key, ttl, user.model_dump_json())

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    cache_key = key("user", user_id)

    cached_user = await app.state.redis.get(cache_key)
    if cached_user:
        return {"source": "cache", "user": User.model_validate_json(cached_user)}
    user = User(id=user_id, name="John Doe", email="john.doe@example.com", country="USA")
    await cache_with_fixed_ttl(cache_key, user.model_dump_json())
    return {"source": "database", "user": user}

@app.get("/users/{user_id}/sliding")
async def get_user_sliding(user_id: int):
    cache_key = key("user", user_id)
    cached_user = await app.state.redis.get(cache_key)
    if cached_user:
        await app.state.redis.expire(cache_key, 30)
        return {"source": "cache", "user": User.model_validate_json(cached_user)}
    user = User(id=user_id, name="John Doe", email="john.doe@example.com", country="USA")
    await cache_with_fixed_ttl(cache_key, user.model_dump_json())
    return {"source": "database", "user": user}

@app.post("/users")
async def create_or_update_user(u: User, ttl: int = 300):
    saved = await write_user(u, ttl=ttl)
    return {"status": "user saved", "user": u}

@app.post("/persist/{user_id}")
async def persist_user(user_id: int):
    cache_key = key("user", user_id)
    result = await app.state.redis.persist(cache_key)
    if result:
        return {"status": "user cache persisted"}
    return {"status": "user cache not found or already persistent"}