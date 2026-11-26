from fastapi import FastAPI

from routers.ask import router as ask_router
from routers.chat import router as chat_router
from routers.compare import router as compare_router
from routers.health import router as health_router
from routers.models import router as models_router
from routers.tokens import router as tokens_router

app = FastAPI(
    title="ai4dev-wiki",
    description="Q&A assistant over the AI for Developers course material",
    version="0.1.0",
)

# Route order matters: FastAPI matches in the order routes are declared, so a
# fixed path must always be registered before a path that captures a parameter.
for router in (
    health_router,
    ask_router,
    chat_router,
    compare_router,
    models_router,
    tokens_router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["health"], summary="Liveness ping")
async def root():
    return {"message": "Hello, ai4dev-wiki!"}
