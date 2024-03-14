from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


from create_and_add_data import get_dtos_mapp_with_relationship, select_resumes_with_all_relationships


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.get("/workers")
@cache(expire=60)
async def get_worker():
    workers = await get_dtos_mapp_with_relationship()
    return workers


@app.get("/resumes")
@cache(expire=60)
async def get_resumes():
    resumes = await select_resumes_with_all_relationships()
    return resumes
