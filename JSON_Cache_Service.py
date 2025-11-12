from fastapi import FastAPI, Response, status, HTTPException
import redis.asyncio as redis
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import json

REDIS_URL = "redis://127.0.0.1:6379"
REDIS_KEY_PREFIX = "User:"

class User(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    email: Optional[str] = None

def _user_key(user_id: str) -> str:
    return f"{REDIS_KEY_PREFIX}{user_id}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await app.state.redis.ping()
    except Exception as e:
        print("Failed to connect to Redis:", e)
        raise
    yield

    await app.state.redis.close()
    print("Redis connection closed.")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    try:
        await app.state.redis.ping()
        return {"status": "healthy", "redis": "connected"}
    except:
        return {"status": "unhealthy", "redis": "disconnected"}
    

    
@app.get("/get/{user_id}")
async def get_user_data(user_id: str):
    key = _user_key(user_id)
    data = await app.state.redis.get(key)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "User not found"})
    return {"user_id": user_id, "data": data}

@app.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    key = _user_key(user.id)
    value = json.dumps(user.model_dump())
    await app.state.redis.set(key, value)
    return {"stored": True, "key": key}