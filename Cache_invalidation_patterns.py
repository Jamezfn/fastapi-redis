from fastapi import FastAPI
from pydantic import BaseModel
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json
import asyncio
from typing import Optional

REDIS_URL = "redis://localhost:6379"
NAMESPACE = "app_v1"
DEFAULT_TTL = 300

def key(*parts: str) -> str:
    return ":".join([NAMESPACE, *map(str, parts)])

class User(BaseModel):
    id: int
    name: str
    email: str
    country: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None

_db: dict[int, dict] = {}
_db_lock = asyncio.Lock()

async def db_get(user_id: int) -> Optional[dict]:
    async with _db_lock:
        return _db.get(user_id)

async def db_set(user: dict):
    async with _db_lock:
        _db[user["id"]] = user.copy()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    await app.state.redis.ping()
    yield
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

@app.get("/cache-aside/users/{user_id}")
async def cache_aside_get(user_id: int):
    cache_key = key("user", user_id)
    cached_user = await app.state.redis.get(cache_key)
    if cached_user:
        return {"source": "cache", "user": User.model_validate_json(cached_user)}
    
    await db_set({"id": user_id, "name": "John Doe", "email": "john.doe@example.com", "country": "USA"})
    row = await db_get(user_id)
    if not row:
        return {"error": "User not found"}, 404
    
    user = User.model_validate(row)
    await app.state.redis.setex(cache_key, DEFAULT_TTL, user.model_dump_json())
    return {"source": "database", "user": user}

@app.post("/write-through/users/{user_id}")
@app.put("/write-through/users/{user_id}")
async def write_through_get(user_id: int, payload: UserUpdate):
    await db_set({"id": user_id, **payload.model_dump(exclude_unset=True)})
    user = await db_get(user_id)
    user_json = json.dumps(user)
    cache_key = key("user", user_id)
    await app.state.redis.setex(cache_key, DEFAULT_TTL, user_json)
    return {"source": "write-through", "user": user}

@app.get("/db/debug/{user_id}")
async def db_debug(user_id: int):
    row = await db_get(user_id)
    return {"db_row": row}