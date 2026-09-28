from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.query import router as query_router
from app.api.routes.auth import router as auth_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="DocAI",
    description="Production-grade document intelligence and RAG platform",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(query_router)
app.include_router(auth_router)