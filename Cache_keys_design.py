from fastapi import FastAPI
from pydantic import BaseModel
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

REDIS_URL = "redis://localhost:6379"
NAMESPACE = "app_v1"

def make_cache_key(*parts: str) -> str:
    return ":".join([NAMESPACE, *parts])

class User(BaseModel):
    id: int
    name: str
    email: str
    country: str

def get_user_cache_key(user_id: int) -> str:
    return make_cache_key("user", str(user_id))

def get_user_post_cache_key(user_id: int, page: int = 1) -> str:
    return make_cache_key("user", str(user_id), "posts", str(page))

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    await app.state.redis.ping()
    yield
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    cache_key = get_user_cache_key(user_id)
    cached_user = await app.state.redis.get(cache_key)
    if cached_user:
        return {"source": "cache", "user": User.model_validate_json(cached_user)}

    user = User(id=user_id, name="John Doe", email="john.doe@example.com", country="USA")
    await app.state.redis.set(cache_key, user.model_dump_json())
    return {"source": "database", "user": user}

@app.get("/users/{user_id}/posts")
async def get_user_posts(user_id: int, page: int = 1):
    cache_key = get_user_post_cache_key(user_id, page)
    cached_posts = await app.state.redis.get(cache_key)
    if cached_posts:
        return {"source": "cache", "posts": json.loads(cached_posts)}

    posts = [{"post_id": i, "content": f"Post {i} content"} for i in range((page-1)*10, page*10)]
    await app.state.redis.set(cache_key, json.dumps(posts))
    return {"source": "database", "posts": posts}