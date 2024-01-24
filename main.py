from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from create_and_add_data import get_dtos_mapp_with_relationship, select_resumes_with_all_relationships

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get("/workers")
async def get_worker():
    workers = await get_dtos_mapp_with_relationship()
    return workers


@app.get("/resumes")
async def get_resumes():
    resumes = await select_resumes_with_all_relationships()
    return resumes
