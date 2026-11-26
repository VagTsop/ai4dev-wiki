from fastapi import FastAPI

from routers.ask import router as ask_router

app = FastAPI(
    title="ai4dev-wiki",
    description="Βοηθός Q&A πάνω στο υλικό του σεμιναρίου AI for Developers",
    version="0.1.0",
)

app.include_router(ask_router, prefix="/api/v1")


@app.get("/", tags=["health"], summary="Έλεγχος λειτουργίας")
async def root():
    return {"message": "Hello, ai4dev-wiki!"}
