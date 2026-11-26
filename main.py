from fastapi import FastAPI

from routers.ask import router as ask_router
from routers.chat import router as chat_router
from routers.compare import router as compare_router
from routers.models import router as models_router
from routers.tokens import router as tokens_router

app = FastAPI(
    title="ai4dev-wiki",
    description="Q&A assistant over the AI for Developers course material",
    version="0.1.0",
)

for router in (ask_router, chat_router, compare_router, models_router, tokens_router):
    app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["health"], summary="Health check")
async def root():
    return {"message": "Hello, ai4dev-wiki!"}
