from fastapi import FastAPI

from app.api.routes.health import router as health_router


app = FastAPI(
    title="DocAI",
    description="Production-grade document intelligence and RAG platform",
    version="0.1.0",
)

@app.get('/')
def Home():
    return {
        "title": "DocAI",
        "description": "Production-grade document intelligence and RAG platform",
        "version": "0.1.0"
    }


app.include_router(health_router)