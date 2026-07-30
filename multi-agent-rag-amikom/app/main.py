import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import health, query, evaluation
from app.observability.logging import logger

app = FastAPI(
    title="Multi-Agent RAG AMIKOM Yogyakarta",
    description="Sistem Layanan Akademik Terpadu S1 Informatika Universitas AMIKOM Yogyakarta",
    version="1.0.0"
)

# Middleware for request ID and latency logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-MS"] = f"{latency_ms:.2f}"
    logger.info(f"Method={request.method} Path={request.url.path} RequestID={request_id} Latency={latency_ms:.2f}ms Status={response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.responses import FileResponse

app.include_router(health.router)        # router already has prefix /api/v1
app.include_router(query.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {
        "service": "Multi-Agent RAG AMIKOM",
        "status": "RUNNING",
        "docs_url": "/docs"
    }

@app.get("/ui")
def read_ui():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return read_root()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
