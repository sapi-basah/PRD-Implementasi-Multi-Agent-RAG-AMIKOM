"""Main FastAPI Application: Multi-Agent RAG AMIKOM Yogyakarta."""

import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import evaluation, health, query, sources
from app.observability import logger

app = FastAPI(
    title="Multi-Agent RAG AMIKOM Yogyakarta",
    description="Sistem Layanan Akademik Terpadu S1 Informatika Universitas AMIKOM Yogyakarta (PRD V1.1)",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware for request ID and latency logging (no PII logged)
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-MS"] = f"{latency_ms:.2f}"

    # Log route, method, status, latency — NO raw query logged to protect PII
    logger.info(
        f"Method={request.method} Path={request.url.path} "
        f"RequestID={request_id} Latency={latency_ms:.2f}ms Status={response.status_code}"
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(query.router)
app.include_router(evaluation.router)
app.include_router(sources.router)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {
        "service": "Multi-Agent RAG AMIKOM",
        "version": "1.1.0",
        "status": "RUNNING",
        "docs_url": "/docs",
        "ui_url": "/ui",
        "health_url": "/api/v1/health",
        "readiness_url": "/api/v1/readiness",
    }


@app.get("/ui")
def read_ui():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return read_root()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
